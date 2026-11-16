"""The stationary quantities of an opening: what one year of the recipes yields when it repeats itself.

A plain function over built inputs (Caiani et al. 2016 solve the stationary state first and spread it over the
agents; Complaints 473 and 526). Recipes have fixed coefficients, so the runs of every recipe follow from final
demand by the input-output solve x = A x + d (`opening_runs.choose_recipes`), and the prices that pay for them
are the cost-price dual (`unit_cost`). From the runs come the flows that a year that repeats itself must show:

- value added equals the value of final demand (wages plus profit are the income that buys it);
- hours demanded by each trade, to be set against the hours offered;
- the wage the labour market clears at when more hours are offered than demanded (the survival wage, which
  `labour_ask_floor` sets), against the wage the cost table states.

Nothing here reads a game; the fixture setups (fixture_setups.py) call it with their final demand. The opening does
not seed its producers or its wage from it (Complaint 473).
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
    unpaid = sorted(trade for trade in hours if trade not in wages)
    if unpaid:
        raise ValueError(f"the stationary flows need a wage for every trade the runs use; none for {unpaid}")
    wage_bill = math.fsum(hours[trade] * wages[trade] for trade in hours)
    input_cost = math.fsum(count * (unit_cost.bought_input_cost_per_run(recipes[recipe_id], prices)
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
    return math.fsum(quantity * prices[good] for good, quantity in recipe.plant_goods.items()
                     if prices.get(good) is not None) / recipe.plant_life_years


def hours_that_clear_at(demanded_hours: float, workers: float, slack_share: float,
                        kept_per_worker: float = 0.0) -> float:
    """Hours a worker has a year so that the hours he offers exceed the hours demanded by `slack_share`, after the
    hours `kept_per_worker` that he keeps for his plot at the wage (`households_hours_offered.plot_hours_kept`)."""
    if workers <= 0.0:
        return 0.0
    return demanded_hours * (1.0 + slack_share) / workers + max(0.0, kept_per_worker)
