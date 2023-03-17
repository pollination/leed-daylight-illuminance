from pollination_dsl.dag import Inputs, DAG, task
from dataclasses import dataclass
from pollination.honeybee_radiance.octree import CreateOctreeWithSkyStatic
from pollination.honeybee_radiance.grid import SplitGridFolder, MergeFolderData
from pollination.honeybee_radiance.raytrace import RayTracingPointInTime
from pollination.path.copy import Copy


@dataclass
class PointInTimeGridEntryPoint(DAG):
    """Point-in-time grid-based entry point."""

    # inputs
    model_folder = Inputs.folder(
        description='A Honeybee Radiance Model folder.'
    )

    sky = Inputs.file(
        description='Radiance Sky file for simulation.',
        extensions=['sky']
    )

    sensor_grids_file = Inputs.file(
        description='JSON file with information about the sensor grids to simulate.',
        extensions=['json']
    )

    cpu_count = Inputs.int(
        default=50,
        description='The maximum number of CPUs for parallel execution. This will be '
        'used to determine the number of sensors run by each worker.',
        spec={'type': 'integer', 'minimum': 1}
    )

    min_sensor_count = Inputs.int(
        description='The minimum number of sensors in each sensor grid after '
        'redistributing the sensors based on cpu_count.', default=1,
        spec={'type': 'integer', 'minimum': 1}
    )

    radiance_parameters = Inputs.str(
        description='The radiance parameters for ray tracing',
        default='-ab 2 -aa 0.1 -ad 2048 -ar 64'
    )

    bsdfs = Inputs.folder(
        description='Folder containing any BSDF files needed for ray tracing.',
        optional=True
    )

    @task(template=Copy)
    def copy_sensor_grid_info(self, src=sensor_grids_file):
        return [
            {
                'from': Copy()._outputs.dst,
                'to': 'results/grids_info.json'
            }
        ]

    @task(template=CreateOctreeWithSkyStatic)
    def create_octree(self, model=model_folder, sky=sky):
        """Create octree from radiance folder and sky."""
        return [
            {
                'from': CreateOctreeWithSkyStatic()._outputs.scene_file,
                'to': 'resources/scene.oct'
            }
        ]

    @task(
        template=SplitGridFolder,
        sub_paths={'input_folder': 'grid'}
    )
    def split_grid_folder(
        self, input_folder=model_folder,
        cpu_count=cpu_count, cpus_per_grid=2, min_sensor_count=min_sensor_count
    ):
        """Split sensor grid folder based on the number of CPUs"""
        return [
            {
                'from': SplitGridFolder()._outputs.output_folder,
                'to': 'resources/grid'
            },
            {
                'from': SplitGridFolder()._outputs.dist_info,
                'to': 'initial_results/_redist_info.json'
            },
            {
                'from': SplitGridFolder()._outputs.sensor_grids,
                'description': 'Sensor grids information.'
            }
        ]

    @task(
        template=RayTracingPointInTime,
        needs=[create_octree, split_grid_folder],
        loop=split_grid_folder._outputs.sensor_grids,
        sub_folder='initial_results/{{item.full_id}}',  # subfolder for each grid
        sub_paths={'grid': '{{item.full_id}}.pts'}  # subpath for sensor_grid
    )
    def point_in_time_grid_ray_tracing(
        self,
        radiance_parameters=radiance_parameters,
        metric='illuminance',
        scene_file=create_octree._outputs.scene_file,
        grid=split_grid_folder._outputs.output_folder,
        bsdf_folder=bsdfs
    ):
        return [
            {
                'from': RayTracingPointInTime()._outputs.result,
                'to': '../{{item.name}}.res'
            }
        ]

    @task(
        template=MergeFolderData,
        needs=[point_in_time_grid_ray_tracing]
    )
    def restructure_results(
        self, input_folder='initial_results',
        extension='res'
    ):
        return [
            {
                'from': MergeFolderData()._outputs.output_folder,
                'to': 'results'
            }
        ]
