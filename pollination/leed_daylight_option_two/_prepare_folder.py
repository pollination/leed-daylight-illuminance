from pollination_dsl.dag import Inputs, GroupedDAG, task, Outputs
from dataclasses import dataclass
from pollination.honeybee_radiance.sky import CreateLeedSkies
from pollination.honeybee_radiance.translate import CreateRadianceFolderGrid
from pollination.path.copy import Copy

# input/output alias
from pollination.alias.inputs.model import hbjson_model_input
from pollination.alias.inputs.wea import wea_input
from pollination.alias.inputs.north import north_input
from pollination.alias.inputs.grid import grid_filter_input


@dataclass
class LeedDaylightOptionTwoPrepareFolder(GroupedDAG):
    """Prepare folder for leed-daylight-option-two."""

    # inputs
    model = Inputs.file(
        description='A Honeybee model in HBJSON file format.',
        extensions=['json', 'hbjson'],
        alias=hbjson_model_input
    )

    wea = Inputs.file(
        description='A Typical Meteorological Year (TMY) .wea file. The file '
        'must be annual with a timestep of 1 for a non-leap year.',
        extensions=['wea', 'epw'], alias=wea_input
    )

    north = Inputs.float(
        default=0,
        description='A number for rotation from north.',
        spec={'type': 'number', 'minimum': 0, 'maximum': 360},
        alias=north_input
    )

    grid_filter = Inputs.str(
        description='Text for a grid identifier or a pattern to filter the sensor grids '
        'of the model that are simulated. For instance, first_floor_* will simulate '
        'only the sensor grids that have an identifier that starts with '
        'first_floor_. By default, all grids in the model will be simulated.',
        default='*',
        alias=grid_filter_input
    )

    @task(template=Copy)
    def copy_model(self, src=model):
        return [
            {
                'from': Copy()._outputs.dst,
                'to': 'simulation/model.hbjson'
            }
        ]

    @task(template=CreateRadianceFolderGrid, annotations={'main_task': True})
    def create_rad_folder(self, input_model=model, grid_filter=grid_filter):
        """Translate the input model to a radiance folder."""
        return [
            {
                'from': CreateRadianceFolderGrid()._outputs.model_folder,
                'to': 'model'
            },
            {
                'from': CreateRadianceFolderGrid()._outputs.sensor_grids_file,
                'to': 'resources/grids_info.json'
            }
        ]

    @task(template=CreateLeedSkies)
    def create_skies(self, wea=wea, north=north):
        return [
            {
                'from': CreateLeedSkies()._outputs.output_folder,
                'to': 'resources/skies'
            }
        ]

    sky_list = Outputs.list(
        source='resources/skies/sky_info.json',
        description='A JSON array containing the information about the two '
        'generated sky files.'
    )

    model_folder = Outputs.folder(
        source='model', description='Input model folder folder.'
    )

    resources = Outputs.folder(
        source='resources', description='Resources folder.'
    )

    simulation = Outputs.folder(
        source='simulation', description='Simulation folder.'
    )
