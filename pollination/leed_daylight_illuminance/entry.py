from pollination_dsl.dag import Inputs, DAG, task, Outputs
from dataclasses import dataclass
from pollination.honeybee_radiance.sky import CreateLeedSkies
from pollination.honeybee_radiance.translate import CreateRadianceFolderGrid
from pollination.honeybee_radiance.post_process import LeedIlluminanceCredits
from pollination.path.copy import Copy

from ._illuminance import PointInTimeGridEntryPoint

# input/output alias
from pollination.alias.inputs.model import hbjson_model_input
from pollination.alias.inputs.wea import wea_input
from pollination.alias.inputs.north import north_input
from pollination.alias.inputs.grid import sensor_count_input, grid_filter_input
from pollination.alias.inputs.bool_options import glare_control_devices_input
from pollination.alias.inputs.radiancepar import rad_par_leed_illuminance_input
from pollination.alias.outputs.daylight import illuminance_9am_results, \
    illuminance_3pm_results, pass_fail_9am_results, pass_fail_3pm_results, \
    pass_fail_comb_results, leed_ill_credit_summary_results


@dataclass
class LeedDaylightIlluminanceEntryPoint(DAG):
    """LEED Daylight Illuminance entry point."""

    # inputs
    model = Inputs.file(
        description='A Honeybee model in HBJSON file format.',
        extensions=['json', 'hbjson'],
        alias=hbjson_model_input
    )

    wea = Inputs.file(
        description='A Typical Meteorological Year (TMY) .wea file. The file '
        'must be annual with a timestep of 1 for a non-leap year.',
        extensions=['wea'], alias=wea_input
    )

    glare_control_devices = Inputs.str(
        description='A switch to note whether the model has "view-preserving automatic '
        '(with manual override) glare-control devices," which means that illuminance '
        'only needs to be above 300 lux and not between 300 and 3000 lux.',
        default='glare-control',
        spec={'type': 'string', 'enum': ['glare-control', 'no-glare-control']},
        alias=glare_control_devices_input
    )

    north = Inputs.float(
        default=0,
        description='A number for rotation from north.',
        spec={'type': 'number', 'minimum': 0, 'maximum': 360},
        alias=north_input
    )

    grid_filter = Inputs.str(
        description='Text for a grid identifer or a pattern to filter the sensor grids '
        'of the model that are simulated. For instance, first_floor_* will simulate '
        'only the sensor grids that have an identifier that starts with '
        'first_floor_. By default, all grids in the model will be simulated.',
        default='*',
        alias=grid_filter_input
    )

    sensor_count = Inputs.int(
        default=100,
        description='The maximum number of grid points per parallel execution.',
        spec={'type': 'integer', 'minimum': 1},
        alias=sensor_count_input
    )

    radiance_parameters = Inputs.str(
        description='The radiance parameters for ray tracing',
        default='-ab 5 -aa 0.1 -ad 2048 -ar 64',
        alias=rad_par_leed_illuminance_input
    )

    @task(template=Copy)
    def copy_model(self, src=model):
        return [
            {
                'from': Copy()._outputs.dst,
                'to': 'simulation/model.hbjson'
            }
        ]

    @task(template=CreateRadianceFolderGrid)
    def create_rad_folder(self, input_model=model, grid_filter=grid_filter):
        """Translate the input model to a radiance folder."""
        return [
            {'from': CreateRadianceFolderGrid()._outputs.model_folder, 'to': 'model'},
            {
                'from': CreateRadianceFolderGrid()._outputs.model_sensor_grids_file,
                'to': 'grids_info.json'
            },
            {
                'from': CreateRadianceFolderGrid()._outputs.sensor_grids_file,
                'to': '_grids_info.json'
            }
        ]

    @task(template=CreateLeedSkies)
    def create_skies(self, wea=wea, north=north):
        return [
            {'from': CreateLeedSkies()._outputs.sky_list},
            {'from': CreateLeedSkies()._outputs.output_folder, 'to': 'skies'}
        ]

    @task(
        template=PointInTimeGridEntryPoint,
        needs=[create_rad_folder, create_skies],
        loop=create_skies._outputs.sky_list,
        sub_folder='simulation/{{item.id}}',
        sub_paths={'sky': '{{item.path}}'}
    )
    def illuminance_simulation(
        self,
        model_folder=create_rad_folder._outputs.model_folder,
        sky=create_skies._outputs.output_folder,
        sensor_grids_file=create_rad_folder._outputs.sensor_grids_file,
        model_sensor_grids_file=create_rad_folder._outputs.model_sensor_grids_file,
        grid_filter=grid_filter,
        sensor_count=sensor_count,
        radiance_parameters=radiance_parameters
    ):
        # this task doesn't return a folder for each loop.
        # instead we access the results folder as a separate task
        pass

    @task(
        template=LeedIlluminanceCredits, needs=[copy_model, illuminance_simulation]
    )
    def evaluate_credits(
        self, folder='simulation', glare_control_devices=glare_control_devices
    ):
        return [
            {
                'from': LeedIlluminanceCredits()._outputs.pass_fail_results,
                'to': 'results'
            },
            {
                'from': LeedIlluminanceCredits()._outputs.credit_summary,
                'to': 'credit_summary.json'
            }
        ]

    illuminance_9am = Outputs.folder(
        source='simulation/9AM/results',
        description='Illuminance results for the 9AM simulation in lux.',
        alias=illuminance_9am_results
    )

    illuminance_3pm = Outputs.folder(
        source='simulation/3PM/results',
        description='Illuminance results for the 3PM simulation in lux.',
        alias=illuminance_3pm_results
    )

    pass_fail_9am = Outputs.folder(
        description='Pass/Fail results for the 9AM simulation as one/zero values.',
        source='results/9AM',
        alias=pass_fail_9am_results
    )

    pass_fail_3pm = Outputs.folder(
        description='Pass/Fail results for the 3PM simulation as one/zero values.',
        source='results/3PM',
        alias=pass_fail_3pm_results
    )

    pass_fail_combined = Outputs.folder(
        description='Pass/Fail results for the combined simulation as one/zero values.',
        source='results/combined',
        alias=pass_fail_comb_results
    )

    credit_summary = Outputs.folder(
        description='JSON file containing the number of LEED credits achieved and '
        'a summary of the percentage of the sensor grid area that meets the criteria.',
        source='credit_summary.json',
        alias=leed_ill_credit_summary_results
    )
