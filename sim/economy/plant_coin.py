"""The coin a producer has for the year's runs, once the plant it means to rebuild is paid for (the clearing rule set).

The close reserves the coin for the plant a producer rebuilds itself (close_kernel: it is not paid out), and the
producer bids for that plant's goods beside its inputs (`Economy._rebuild_worn_plant`). Under the clearing set the
runs a producer staffs and the inputs it orders follow its hired hours and can take all the coin it has; the plant's
coin is therefore set aside first, so a producer does not let its plant wear to run a few more runs this year."""
import math

from . import unit_cost
from .producers import live_input_prices, live_wages


def coin_left_for_runs(coin: float, plant_runs_to_rebuild: float, plant_value_per_run: float) -> float:
    """The coin left for inputs and hours: what the producer holds less the cost of the plant it means to rebuild;
    never under nothing, and all of it where there is no plant to rebuild or its cost cannot be worked out."""
    held = max(0.0, coin)
    if not plant_runs_to_rebuild > 0.0 or not math.isfinite(plant_value_per_run) or plant_value_per_run <= 0.0:
        return held
    return max(0.0, held - plant_runs_to_rebuild * plant_value_per_run)


def coin_for_runs(setup, record, view, producer, coin: float) -> float:
    """`coin_left_for_runs` of `producer`: the plant it means to rebuild is the record's (`credit.worn_runs`, noted at
    last year's close), priced at this year's prices and wages on its tile."""
    rebuilds = getattr(getattr(record, "credit", None), "worn_runs", None)
    runs = rebuilds.get(producer.agent_id, 0.0) if rebuilds else 0.0
    if not runs > 0.0:
        return max(0.0, coin)
    recipe = setup.recipes[producer.recipe_id]
    value = unit_cost.plant_value_per_run(recipe, live_input_prices(producer, recipe, view), live_wages(producer, recipe, view))
    return coin_left_for_runs(coin, runs, value)
