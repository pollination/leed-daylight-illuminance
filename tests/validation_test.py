from pollination.leed_daylight_illuminance.entry import LeedDaylightIlluminanceEntryPoint
from queenbee.recipe.dag import DAG


def test_leed_daylight_illuminance():
    recipe = LeedDaylightIlluminanceEntryPoint().queenbee
    assert recipe.name == 'leed-daylight-illuminance-entry-point'
    assert isinstance(recipe, DAG)
