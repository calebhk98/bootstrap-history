"""What one run of a recipe costs and earns at live prices: never opening prices, never a book.

Prices and wages come in as mappings (good -> price, trade -> wage per hour). A good or trade a
run needs that is missing from its mapping makes the cost infinite: a run that cannot be priced is
not run. The plant is charged per run through the capital recovery factor at the live interest rate:
the yearly share that repays the plant's value over its life.
"""
import math
from typing import Mapping

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


def variable_cost_per_run(recipe: Recipe, input_prices: Prices, wages: Wages) -> float:
    return input_cost_per_run(recipe, input_prices) + labour_cost_per_run(recipe, wages)


def capital_recovery_factor(interest_rate: float, life_years: float) -> float:
    """The yearly payment, per unit borrowed, that repays it with interest over the life; one over the
    life at a nil or negative rate."""
    if life_years <= 0.0:
        return 1.0
    if interest_rate <= 0.0:
        return 1.0 / life_years
    return interest_rate / (1.0 - (1.0 + interest_rate) ** -life_years)


def plant_value_per_run(recipe: Recipe, input_prices: Prices, wages: Wages) -> float:
    """What the plant for one run of yearly capacity costs to build at these prices and wages."""
    return _bill(recipe.plant_goods, input_prices) + _bill(recipe.plant_labour_hours, wages)


def capital_charge_per_run(recipe: Recipe, input_prices: Prices, wages: Wages, interest_rate: float) -> float:
    value = plant_value_per_run(recipe, input_prices, wages)
    if value == 0.0:
        return 0.0
    return value * capital_recovery_factor(interest_rate, recipe.plant_life_years)


def revenue_per_run(recipe: Recipe, expected_output_prices: Prices) -> float:
    """Every output at its expected price; an output with no expected price is counted at nothing."""
    return sum(quantity * expected_output_prices.get(good, 0.0) for good, quantity in recipe.outputs.items())


def expected_margin(recipe: Recipe, expected_output_prices: Prices, input_prices: Prices,
                    wages: Wages, interest_rate: float) -> float:
    """Revenue over every output, less variable cost and the capital charge, per run."""
    return (revenue_per_run(recipe, expected_output_prices)
            - variable_cost_per_run(recipe, input_prices, wages)
            - capital_charge_per_run(recipe, input_prices, wages, interest_rate))


def return_on_capital(recipe: Recipe, expected_output_prices: Prices, input_prices: Prices,
                      wages: Wages) -> float:
    """Yearly operating surplus (revenue less variable cost) per run, over the capital a run of yearly
    capacity employs: its plant plus a year's variable cost paid before the sales come in. Compare
    with the live interest rate; zero if nothing is employed or it cannot be priced."""
    variable = variable_cost_per_run(recipe, input_prices, wages)
    employed = plant_value_per_run(recipe, input_prices, wages) + variable
    if not math.isfinite(employed) or employed <= 0.0:
        return 0.0
    return (revenue_per_run(recipe, expected_output_prices) - variable) / employed
