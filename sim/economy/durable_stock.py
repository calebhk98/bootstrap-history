"""The stock of a durable a household wants in use, and how much of its holding is that stock.
Pure functions. The wanted stock is the expected flow it serves times the good's service life; the
flow is smoothed because a service life multiplies a one-year swing in spending many times over."""
from typing import Dict, Mapping

from sim.constants import declare

from .types import GoodId, GoodSpec

EXPECTED_SPENDING_ADJUSTMENT = declare(
    "EXPECTED_SPENDING_ADJUSTMENT", 0.3, kind="temporary_heuristic",
    unit="share of the gap closed a year", source=None, confidence="D",
    why="A household sizes the durables it wants in use on the spending it expects, which moves toward "
        "each year's actual spending by this share of the gap. Real households form expectations from "
        "income history and habit, which are not modelled; the share is an assumption.")


def update_expected_spending(expected: float, spent: float) -> float:
    """Expected yearly spending after a year in which `spent` was spent (the first year seeds it)."""
    if expected <= 0.0:
        return spent
    return expected + EXPECTED_SPENDING_ADJUSTMENT * (spent - expected)


def expected_flow_scale(expected_spending: float, spending: float) -> float:
    """What share of a planned flow a durable's stock is sized on: expected spending over this year's."""
    if expected_spending <= 0.0 or spending <= 0.0:
        return 1.0
    return expected_spending / spending


def in_use_stock(flow_by_good: Mapping[GoodId, float], specs: Mapping[GoodId, GoodSpec],
                 scale: float, band: float) -> Dict[GoodId, float]:
    """Stock of each durable the flow keeps in use (flow times service life, `band` added); the store
    does not count it as savings."""
    stock = {}
    for good, flow in flow_by_good.items():
        spec = specs.get(good)
        if spec is not None and spec.service_life_years > 0.0 and flow > 0.0:
            stock[good] = flow * scale * spec.service_life_years * (1.0 + band)
    return stock
