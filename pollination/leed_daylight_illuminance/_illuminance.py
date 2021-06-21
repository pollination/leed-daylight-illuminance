from pollination_dsl.dag import Inputs, DAG, task, Outputs
from dataclasses import dataclass
from pollination.honeybee_radiance.octree import CreateOctreeWithSky
from pollination.honeybee_radiance.translate import CreateRadianceFolderGrid
from pollination.path.copy import Copy
from pollination.path.read import ReadJSONList

from ._raytracing import PointInTimeGridRayTracing


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

    model_sensor_grids_file = Inputs.file(
        description='JSON file with information about the sensor grids to simulate.',
        extensions=['json']
    )

    sensor_count = Inputs.int(
        default=200,
        description='The maximum number of grid points per parallel execution',
        spec={'type': 'integer', 'minimum': 1}
    )

    radiance_parameters = Inputs.str(
        description='The radiance parameters for ray tracing',
        default='-ab 2 -aa 0.1 -ad 2048 -ar 64'
    )

    @task(template=Copy)
    def copy_sensor_grid_info(self, src=model_sensor_grids_file):
        return [
            {
                'from': Copy()._outputs.dst,
                'to': 'results/grids_info.json'
            }
        ]

    @task(template=ReadJSONList)
    def read_sensor_grid_info(self, src=sensor_grids_file):
        return [
            {
                'from': ReadJSONList()._outputs.data,
                'description': 'Sensor grids information.'
            }
        ]

    @task(template=CreateOctreeWithSky)
    def create_octree(self, model=model_folder, sky=sky):
        """Create octree from radiance folder and sky."""
        return [
            {
                'from': CreateOctreeWithSky()._outputs.scene_file,
                'to': 'resources/scene.oct'
            }
        ]

    @task(
        template=PointInTimeGridRayTracing,
        needs=[read_sensor_grid_info, create_octree],
        loop=read_sensor_grid_info._outputs.data,
        sub_folder='initial_results/{{item.name}}',  # create a subfolder for each grid
        sub_paths={'sensor_grid': 'grid/{{item.full_id}}.pts'}  # subpath for sensor_grid
    )
    def point_in_time_grid_ray_tracing(
        self,
        sensor_count=sensor_count,
        radiance_parameters=radiance_parameters,
        metric='illuminance',
        octree_file=create_octree._outputs.scene_file,
        grid_name='{{item.full_id}}',
        sensor_grid=model_folder
    ):
        # this task doesn't return a file for each loop.
        # instead we access the results folder as a separate task
        pass
