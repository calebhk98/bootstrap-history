"""Figures that say whether a run of the economy behaves plausibly, from its yearly outcomes.

Pure functions over `economy.YearOutcome`s and the setup; nothing here changes the economy. Which goods
count as the staple or as metals is the caller's choice (from data), so nothing here names a good.
Checks are distributions and directions, never dated events (CLAUDE.md 4.2):

    volatility          standard deviation of the yearly log change of a price
    hired_share         hours hired over hours offered (hired plus idle)
    hunger_share        food floor units short over the floor units the population needs
    price_over_labour   a good's price over the labour cost of its cheapest recipe at the year's wages
    ratio               median over the years of one good's price over another's
"""
import math
import statistics
from typing import Dict, Iterable, Mapping, Optional, Sequence


def volatility(series: Sequence[float]) -> float:
    changes = [math.log(after / before) for before, after in zip(series, series[1:])
               if before and after and before > 0.0 and after > 0.0
               and math.isfinite(before) and math.isfinite(after)]
    return statistics.pstdev(changes) if len(changes) > 1 else math.nan


def price_series(outcomes: Iterable, good: str) -> list:
    return [outcome.prices.get(good, math.nan) for outcome in outcomes]


def median_volatility(outcomes: Sequence, goods: Iterable[str]) -> float:
    values = [volatility(price_series(outcomes, good)) for good in goods]
    values = [value for value in values if not math.isnan(value)]
    return statistics.median(values) if values else math.nan


def hired_share(outcome) -> float:
    offered = outcome.hired_hours + outcome.idle_hours
    return outcome.hired_hours / offered if offered > 0.0 else math.nan


def hunger_share(outcome, setup, people: float) -> float:
    need = next((spec for spec in setup.basket.needs if spec.need_id == setup.hunger_need), None)
    floor = people * need.subsistence_per_person if need is not None else 0.0
    return math.fsum(outcome.hunger_by_tile.values()) / floor if floor > 0.0 else math.nan


def labour_cost_per_unit(setup, wages: Mapping[str, float], good: str) -> Optional[float]:
    """The cheapest labour bill per unit of `good` over the recipes that make it, at `wages`; None when
    no recipe makes it or a trade has no wage."""
    costs = []
    for recipe in setup.recipes.values():
        made = recipe.outputs.get(good, 0.0)
        if made <= 0.0 or any(trade not in wages for trade in recipe.labour_hours):
            continue
        costs.append(math.fsum(hours * wages[trade] for trade, hours in recipe.labour_hours.items()) / made)
    return min(costs) if costs else None


def price_over_labour(outcome, setup, good: str) -> float:
    cost = labour_cost_per_unit(setup, outcome.wages, good)
    price = outcome.prices.get(good)
    return price / cost if cost and price else math.nan


def ratio(outcomes: Sequence, top: str, bottom: str) -> float:
    values = [outcome.prices[top] / outcome.prices[bottom] for outcome in outcomes
              if outcome.prices.get(top) and outcome.prices.get(bottom)]
    return statistics.median(values) if values else math.nan


def summary(outcomes: Sequence, setup, staple: str, metals: Iterable[str]) -> Dict[str, float]:
    """The headline figures of a run: staple and metal volatility, the hired share and the staple's
    price over its labour cost (medians over the years), and the mean hunger share."""
    people = math.fsum(setup.opening_population_by_tile.values())
    return {
        "staple_volatility": volatility(price_series(outcomes, staple)),
        "metal_volatility": median_volatility(outcomes, metals),
        "hired_share": _median(hired_share(outcome) for outcome in outcomes),
        "hunger_share": _mean(hunger_share(outcome, setup, people) for outcome in outcomes),
        "staple_over_labour": _median(price_over_labour(outcome, setup, staple) for outcome in outcomes),
    }


def _median(values) -> float:
    values = [value for value in values if not math.isnan(value)]
    return statistics.median(values) if values else math.nan


def _mean(values) -> float:
    values = [value for value in values if not math.isnan(value)]
    return statistics.fmean(values) if values else math.nan
