"""The opening's basket: what households are seeded to want, as far as the opening's producers supply it.

Final demand sizes the producers, but a deposit's limit, a chain held to its ore (opening_runs.fit_to_supply) or
an input the placed producers use up leaves some goods short of it. A good's weight in the price level index and
its depth of market are read from the basket, so a quantity the opening cannot make would carry the index once the
good trades and its price rises to ration it. The basket therefore holds the part of each good's demand the
producers' expected sales leave over after their own inputs and plant wear; a good with none left is absent.
"""
import math
from typing import Dict, Mapping

from .types import GoodId


def left_for_households(setup, record) -> Dict[GoodId, float]:
    """Each good's quantity the producers expect to make a year, less what their expected runs use of it as an
    input or as plant wear."""
    left: Dict[GoodId, float] = {}
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        for good, quantity in recipe.outputs.items():
            left[good] = left.get(good, 0.0) + producer.expected_sales * producer.yield_factor * quantity
        for good, quantity in recipe.inputs.items():
            left[good] = left.get(good, 0.0) - producer.expected_sales * quantity
        if recipe.plant_life_years > 0.0:
            for good, quantity in recipe.plant_goods.items():
                left[good] = left.get(good, 0.0) - producer.expected_sales * quantity / recipe.plant_life_years
    return left


def supplied_part(setup, record, demand: Mapping[GoodId, float]) -> Dict[GoodId, float]:
    """`demand` held to what the producers leave for households, a good with none left dropped."""
    left = left_for_households(setup, record)
    basket = {good: min(wanted, left.get(good, 0.0)) for good, wanted in demand.items()}
    return {good: quantity for good, quantity in basket.items() if quantity > 0.0 and math.isfinite(quantity)}
