from pollination.leed_daylight_option_one.entry import LeedDaylightOptionTwoEntryPoint
from queenbee.recipe.dag import DAG


def test_leed_daylight_illuminance():
    recipe = LeedDaylightOptionTwoEntryPoint().queenbee
    assert recipe.name == 'leed-daylight-option-two-entry-point'
    assert isinstance(recipe, DAG)
