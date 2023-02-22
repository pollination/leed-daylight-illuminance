from pollination.leed_daylight_option_two.entry import LeedDaylightOptionTwoEntryPoint
from queenbee.recipe.dag import DAG


def test_leed_daylight_daylight_option_two():
    recipe = LeedDaylightOptionTwoEntryPoint().queenbee
    assert recipe.name == 'leed-daylight-option-two-entry-point'
    assert isinstance(recipe, DAG)
