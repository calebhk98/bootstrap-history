"""How far prices stand from what goods cost to make. For each good, revenue over full cost per run
(inputs, labour and the plant's yearly charge at the live rate) for the known recipe that makes it
most cheaply: for a single output that is price over unit cost, and for joint outputs the same ratio
with the cost shared by value. One means the price pays the cost of making it, capital included."""
import math
import statistics
from typing import Dict, Mapping

from . import unit_cost
from .types import GoodId, Recipe


def price_to_cost(recipes: Mapping[str, Recipe], prices: Mapping[GoodId, float],
                  wages: Mapping[str, float], interest_rate: float) -> Dict[GoodId, float]:
    """Each good some recipe can price, against the cheapest such recipe's full cost."""
    ratios: Dict[GoodId, float] = {}
    for recipe_id in sorted(recipes):
        recipe = recipes[recipe_id]
        cost = (unit_cost.variable_cost_per_run(recipe, prices, wages)
                + unit_cost.capital_charge_per_run(recipe, prices, wages, interest_rate))
        if not math.isfinite(cost) or cost <= 0.0 or any(good not in prices for good in recipe.outputs):
            continue
        ratio = unit_cost.revenue_per_run(recipe, prices) / cost
        for good in recipe.outputs:
            ratios[good] = max(ratios.get(good, 0.0), ratio)
    return ratios


def summary(ratios: Mapping[GoodId, float]) -> Dict[str, object]:
    """The median ratio and the good farthest from one, above or below."""
    if not ratios:
        return dict(median=float("nan"), worst=float("nan"), worst_good="")
    worst_good = max(sorted(ratios), key=lambda good: abs(math.log(ratios[good])) if ratios[good] > 0.0 else math.inf)
    return dict(median=statistics.median(ratios.values()), worst=ratios[worst_good], worst_good=worst_good)
