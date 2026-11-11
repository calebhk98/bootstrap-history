"""The state's take off a harvest, netted from what a grower expects to get (Complaint 657).

`share_by_good` is the share of the harvest of each good that the state's forms on the harvest take from growers (agents'
`tax_burden.harvest_share_taken`, handed in by the port each year, so the farmer's rule and the producers' rules read one figure).
A grower keeps the rest, so what a harvest fetches him is the price times the share he keeps. Plain functions."""
from typing import Dict, Mapping

from . import unit_cost
from .types import GoodId


def kept_share(good: GoodId, share_by_good: Mapping[GoodId, float]) -> float:
    """Share of the harvest of `good` a grower keeps; all of it where the state takes nothing of that good."""
    return 1.0 - min(1.0, max(0.0, share_by_good.get(good, 0.0)))


def kept_share_of_outputs(outputs: Mapping[GoodId, float], share_by_good: Mapping[GoodId, float]) -> float:
    """Share of a recipe's harvest a grower keeps: each output's kept share weighted by the quantity made; all of it for a
    recipe that makes nothing."""
    total = sum(outputs.values())
    if total <= 0.0:
        return 1.0
    return sum(quantity * kept_share(good, share_by_good) for good, quantity in outputs.items()) / total


def net_output_prices(prices: Mapping[GoodId, float], share_by_good: Mapping[GoodId, float]) -> Dict[GoodId, float]:
    """The prices a grower gets for his outputs once the state has taken its share of each harvest."""
    return {good: price * kept_share(good, share_by_good) for good, price in prices.items()}


def net_revenue_per_run(recipe, expected_output_prices: Mapping[GoodId, float], share_by_good: Mapping[GoodId, float]) -> float:
    """What a run's outputs fetch at the expected prices (`unit_cost.revenue_per_run`) once the state has taken its share of each harvest."""
    return unit_cost.revenue_per_run(recipe, net_output_prices(expected_output_prices, share_by_good))
