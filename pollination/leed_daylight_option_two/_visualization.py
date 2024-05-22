from dataclasses import dataclass
from pollination_dsl.dag import Inputs, GroupedDAG, task, Outputs
from pollination.honeybee_display.translate import ModelToVis
from pollination.path.copy import CopyFolder
from pollination.honeybee_radiance.post_process import LeedDaylightOptionTwoVisMetadata


@dataclass
class LeedDaylightOptionTwoVisualization(GroupedDAG):
    """Create visualization."""

    # inputs
    model = Inputs.file(
        description='Input Honeybee model.',
        extensions=['json', 'hbjson', 'pkl', 'hbpkl', 'zip']
    )

    illuminance_9am = Inputs.folder(
        description='Illuminance results for 9 AM',
        path='simulation/9AM/results'
    )

    illuminance_3pm = Inputs.folder(
        description='Illuminance results for 3 PM',
        path='simulation/3PM/results'
    )

    pass_fail_9am = Inputs.folder(
        description='Pass/fail results for 9 AM',
        path='results/9AM'
    )

    pass_fail_3pm = Inputs.folder(
        description='Pass/fail results for 3 PM',
        path='results/3PM'
    )

    pass_fail_combined = Inputs.folder(
        description='Pass/fail results for combined.',
        path='results/combined'
    )

    @task(template=CopyFolder)
    def copy_illuminance_9am(self, src=illuminance_9am):
        return [
            {
                'from': CopyFolder()._outputs.dst,
                'to': 'visualization/illuminance-9am'
            }
        ]

    @task(template=CopyFolder)
    def copy_illuminance_3pm(self, src=illuminance_3pm):
        return [
            {
                'from': CopyFolder()._outputs.dst,
                'to': 'visualization/illuminance-3pm'
            }
        ]

    @task(template=CopyFolder)
    def copy_pass_fail_9am(self, src=pass_fail_9am):
        return [
            {
                'from': CopyFolder()._outputs.dst,
                'to': 'visualization/pass-fail-9am'
            }
        ]

    @task(template=CopyFolder)
    def copy_pass_fail_3pm(self, src=pass_fail_3pm):
        return [
            {
                'from': CopyFolder()._outputs.dst,
                'to': 'visualization/pass-fail-3pm'
            }
        ]

    @task(template=CopyFolder)
    def copy_pass_fail_combined(self, src=pass_fail_combined):
        return [
            {
                'from': CopyFolder()._outputs.dst,
                'to': 'visualization/pass-fail-combined'
            }
        ]

    @task(
        template=LeedDaylightOptionTwoVisMetadata,
    )
    def create_vis_metadata(self):
        return [
            {
                'from': LeedDaylightOptionTwoVisMetadata()._outputs.vis_metadata_folder,
                'to': 'visualization'
            }
        ]

    @task(
        template=ModelToVis,
        needs=[copy_illuminance_9am, copy_illuminance_3pm , copy_pass_fail_9am,
               copy_pass_fail_3pm, copy_pass_fail_combined, create_vis_metadata]
    )
    def create_vsf(
        self, model=model, grid_data='visualization',
        active_grid_data='pass-fail-combined', output_format='vsf'
    ):
        return [
            {
                'from': ModelToVis()._outputs.output_file,
                'to': 'visualization.vsf'
            }
        ]
    
    visualization = Outputs.file(
        source='visualization.vsf',
        description='Visualization in VisualizationSet format.'
    )
