"""The stationary quantities of an opening: what one year of the recipes yields when it repeats itself.

A plain function over built inputs (Caiani et al. 2016 solve the stationary state first and spread it over the
agents; Complaints 473 and 526). Recipes have fixed coefficients, so the runs of every recipe follow from final
demand by the input-output solve x = A x + d (`opening_runs.choose_recipes`), and the prices that pay for them
are the cost-price dual (`unit_cost`). From the runs come the flows that a year that repeats itself must show:

- value added equals the value of final demand (wages plus profit are the income that buys it);
- hours demanded by each trade, to be set against the hours offered;
- the wage the labour market clears at when more hours are offered than demanded (the survival wage, which
  `labour_ask_floor` sets), against the wage the cost table states.

Nothing here reads a game; the opening calls it with its own final demand, and a test calls it with the small
fixture's. The opening does not yet seed its producers from it (Complaint 473).
"""
import math
from dataclasses import dataclass
from typing import Dict, Mapping, Optional

from . import opening_income, opening_runs, unit_cost
from .types import GoodId, Recipe, TileId


@dataclass(frozen=True)
class StationaryFlows:
    runs: Mapping[str, float]                 # runs a year of each recipe that meet final demand
    hours_by_trade: Mapping[str, float]       # hours a year those runs hire, by trade
    wage_bill: float                          # what the runs pay their workers at the stated wages
    input_cost: float                         # what the runs pay each other for inputs and plant wear
    sales_value: float                        # value of everything the runs make
    final_value: float                        # value of final demand at the prices given

    @property
    def profit(self) -> float:
        """What the producers keep after wages and inputs: the part of income that is not wages."""
        return self.sales_value - self.wage_bill - self.input_cost

    @property
    def income(self) -> float:
        """Wages plus profit: the value added, which a repeating year pays to households."""
        return self.wage_bill + self.profit


def solve(final_by_tile: Mapping[TileId, Mapping[GoodId, float]], recipes: Mapping[str, Recipe],
          prices: Mapping[GoodId, float], wages: Mapping[str, float], rate: float,
          yields: Optional[Mapping[str, float]] = None,
          ceilings: Optional[Mapping[str, float]] = None) -> StationaryFlows:
    """The runs that meet `final_by_tile`, and the money and hours they move at these prices and wages."""
    _ranked, runs = opening_runs.choose_recipes(final_by_tile, recipes, prices, wages, rate, ceilings, yields)
    yields = yields or {}
    hours: Dict[str, float] = {}
    for recipe_id, count in runs.items():
        for trade, per_run in recipes[recipe_id].labour_hours.items():
            hours[trade] = hours.get(trade, 0.0) + count * per_run
    wage_bill = math.fsum(hours[trade] * wages.get(trade, 0.0) for trade in hours)
    input_cost = math.fsum(count * (unit_cost.input_cost_per_run(recipes[recipe_id], prices)
                                    + _plant_wear_cost(recipes[recipe_id], prices))
                           for recipe_id, count in runs.items())
    sales_value = math.fsum(count * yields.get(recipe_id, 1.0) * unit_cost.revenue_per_run(recipes[recipe_id], prices)
                            for recipe_id, count in runs.items())
    final_value = opening_income.value_of(final_by_tile, prices)
    return StationaryFlows(dict(sorted(runs.items())), dict(sorted(hours.items())), wage_bill, input_cost,
                           sales_value, final_value)


def _plant_wear_cost(recipe: Recipe, prices: Mapping[GoodId, float]) -> float:
    if recipe.plant_life_years <= 0.0:
        return 0.0
    return math.fsum(quantity * prices.get(good, 0.0) for good, quantity in recipe.plant_goods.items()) / recipe.plant_life_years


def hours_offered_over_demanded(hours_by_trade: Mapping[str, float], hours_offered: float,
                                trade: str) -> Optional[float]:
    """How many times the hours offered cover the hours the stationary runs hire in `trade`; None where
    nothing hires it. Above one the labour market clears at the workers' ask floor, not at the stated wage."""
    demanded = hours_by_trade.get(trade, 0.0)
    return hours_offered / demanded if demanded > 0.0 else None


def survival_wage_per_hour(floor_cost_per_person: float, people_per_worker: float, hours_per_worker_year: float) -> float:
    """The least wage a worker's year of hours is sold for when the plot grows nothing: what his people's floors
    cost, spread over the hours (the survival side of `labour_ask_floor.wage_floor_per_worker_year`)."""
    if hours_per_worker_year <= 0.0:
        return math.inf
    return floor_cost_per_person * people_per_worker / hours_per_worker_year


def hours_that_clear_at(demanded_hours: float, workers: float, slack_share: float) -> float:
    """Hours a worker offers a year so that the hours offered exceed the hours demanded by `slack_share`."""
    if workers <= 0.0:
        return 0.0
    return demanded_hours * (1.0 + slack_share) / workers
