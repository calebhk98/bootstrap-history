"""What one run of a recipe costs and earns at live prices: never opening prices, never a book.

Prices and wages come in as mappings (good -> price, trade -> wage per hour). A good or trade a
run needs that is missing from its mapping makes the cost infinite: a run that cannot be priced is
not run. The plant is charged per run through the capital recovery factor at the live interest rate:
the yearly share that repays the plant's value over its life.
"""
import math
from typing import Mapping, Optional

from sim.world import capital_market

from .types import GoodId, Recipe, TradeId

Prices = Mapping[GoodId, float]
Wages = Mapping[TradeId, float]


def _bill(quantities: Mapping[str, float], rates: Mapping[str, float]) -> float:
    total = 0.0
    for key, quantity in quantities.items():
        if quantity <= 0.0:
            continue
        if key not in rates:
            return math.inf
        total += quantity * rates[key]
    return total


def input_cost_per_run(recipe: Recipe, input_prices: Prices) -> float:
    return _bill(recipe.inputs, input_prices)


def labour_cost_per_run(recipe: Recipe, wages: Wages) -> float:
    return _bill(recipe.labour_hours, wages)


def variable_cost_per_run(recipe: Recipe, input_prices: Prices, wages: Wages, rent: float = 0.0) -> float:
    """Inputs and labour, plus the rent on the land a run works (zero where land is not charged for)."""
    return input_cost_per_run(recipe, input_prices) + labour_cost_per_run(recipe, wages) + rent


def plant_value_per_run(recipe: Recipe, input_prices: Prices, wages: Wages) -> float:
    """What the plant for one run of yearly capacity costs to build at these prices and wages."""
    return _bill(recipe.plant_goods, input_prices) + _bill(recipe.plant_labour_hours, wages)


def capital_charge_per_run(recipe: Recipe, input_prices: Prices, wages: Wages, interest_rate: float) -> float:
    value = plant_value_per_run(recipe, input_prices, wages)
    if value == 0.0:
        return 0.0
    if recipe.plant_life_years <= 0.0:
        return value  # a plant used up within the run is repaid by that run
    return value * capital_market.capital_recovery_factor(interest_rate, recipe.plant_life_years)


def revenue_per_run(recipe: Recipe, expected_output_prices: Prices) -> float:
    """Every output at its expected price; an output with no expected price is left out of the sum."""
    return math.fsum(quantity * expected_output_prices[good] for good, quantity in recipe.outputs.items()
                     if expected_output_prices.get(good) is not None)


def return_on_capital(recipe: Recipe, expected_output_prices: Prices, input_prices: Prices,
                      wages: Wages, rent: float = 0.0) -> Optional[float]:
    """Yearly operating surplus (revenue less variable cost) per run, over the capital a run of yearly
    capacity employs: its plant plus a year's variable cost paid before the sales come in. Compare
    with the live interest rate; None if nothing is employed or it cannot be priced (a caller treats that
    as no return, not as a return of zero). It is gross of the plant's wear: the ceiling a loan for the plant can
    be priced at (`credit.earnable_rate`) and the yield the plant's worth is discounted from
    (`economy.plant_worth_ratio`, which counts the life). Whether to build is `return_after_recovery` against the rate."""
    variable = variable_cost_per_run(recipe, input_prices, wages, rent)
    employed = plant_value_per_run(recipe, input_prices, wages) + variable
    if not math.isfinite(employed) or employed <= 0.0:
        return None
    return (revenue_per_run(recipe, expected_output_prices) - variable) / employed


def return_after_recovery(recipe: Recipe, expected_output_prices: Prices, input_prices: Prices,
                          wages: Wages, interest_rate: float, rent: float = 0.0) -> Optional[float]:
    """`return_on_capital` after the plant's wear: the surplus less the part of the capital charge that repays the plant
    itself (the charge less the interest on it), over the same capital employed. It exceeds `interest_rate` exactly when
    the run's margin (revenue less variable cost and the capital charge) covers interest on its working capital, so a newcomer or an expansion is judged
    by the charge that `close_year` later makes. None where `return_on_capital` is."""
    gross = return_on_capital(recipe, expected_output_prices, input_prices, wages, rent)
    if gross is None:
        return None
    plant = plant_value_per_run(recipe, input_prices, wages)
    employed = plant + variable_cost_per_run(recipe, input_prices, wages, rent)
    wear = capital_charge_per_run(recipe, input_prices, wages, interest_rate) - interest_rate * plant
    return gross - wear / employed


def full_cost_per_unit(recipe: Recipe, good: GoodId, output_prices: Prices, input_prices: Prices, wages: Wages,
                       interest_rate: float, rent: float = 0.0, yield_factor: float = 1.0) -> float:
    """The one definition of what a unit of `good` costs to make: variable cost (inputs, labour, the rent on the land a
    run works) plus the plant's capital charge at the LIVE `interest_rate`, per unit made at `yield_factor`. Callers
    differ only in whose yield and rent they pass: a named producer's (`seller_offers.unit_cost`), a site's for a
    newcomer (`entry_trial.recipes_by_cost`), or none, yield 1 and no rent, where no maker or site is named
    (`notional.cheapest_cost`).

    A joint run's cost is shared among its outputs: by value at `output_prices` among the outputs that have a price (an
    unpriced co-product takes no share); when `good` itself has no price, by its share of the run's physical output
    quantities. Infinite when a cost cannot be priced or the recipe does not make `good`."""
    made = recipe.outputs.get(good, 0.0) * yield_factor
    if made <= 0.0:
        return math.inf
    run_cost = (variable_cost_per_run(recipe, input_prices, wages, rent)
                + capital_charge_per_run(recipe, input_prices, wages, interest_rate))
    if not math.isfinite(run_cost):
        return math.inf
    revenue = revenue_per_run(recipe, output_prices)
    own_price = output_prices.get(good)
    own_value = recipe.outputs[good] * own_price if own_price is not None else 0.0
    if revenue > 0.0 and own_value > 0.0:
        share = own_value / revenue
    else:
        share = recipe.outputs[good] / math.fsum(recipe.outputs.values())
    return run_cost * share / made
