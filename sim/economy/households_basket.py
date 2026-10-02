"""What households need, as data: the needs, their floors and weights, and the goods that serve them.

`make_basket` is built once from data/world/needs.json and the production data (the same inputs as
sim/world/need_demand.py). `need_prices` prices it at a tile from the market view; build one per tile
and share it across that tile's classes.
"""
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from sim.world import demand, need_demand
from sim.world.need_satiation import SATIATION_FIELD

from .protocols import MarketView
from .types import TileId


@dataclass(frozen=True)
class NeedSpec:
    need_id: str
    subsistence_per_person: float          # need units a person needs a year whatever the price
    budget_weight: float                   # weight of the need in surplus spending
    goods: Tuple[Tuple[str, float], ...]   # (good, need units one unit of the good gives)


@dataclass(frozen=True)
class Basket:
    needs: Tuple[NeedSpec, ...]
    substitution: float                    # elasticity of substitution between goods of one need
    need_data: Mapping[str, Any]           # kept for the satiation limits


@dataclass(frozen=True)
class PricedNeed:
    spec: NeedSpec
    price_index: float                     # money per need unit at the cheapest mix
    goods: Tuple[Tuple[str, float, float, float], ...]   # (good, price, effectiveness, share of spending)


def make_basket(need_data: Mapping[str, Any], production: Mapping[str, Any],
                substitution_elasticity: Optional[float] = None) -> Basket:
    attributes = need_demand.goods_attributes(need_data, production)
    serving: Dict[str, List[Tuple[str, float]]] = {}
    for good in sorted(attributes):
        for need_id, effect in sorted(attributes[good]["satisfies"].items()):
            serving.setdefault(need_id, []).append((good, effect))
    specs = []
    for need_id in sorted(need_data["needs"]):
        data = need_data["needs"][need_id]
        subsistence = (float(getattr(demand, data["subsistence_constant"]))
                       if data.get("subsistence_constant")
                       else float(data.get("subsistence_per_capita_per_year", 0.0)))
        specs.append(NeedSpec(need_id, subsistence, float(data["surplus_budget_share"]),
                              tuple(serving.get(need_id, ()))))
    substitution = (need_demand.NEED_SUBSTITUTION_ELASTICITY if substitution_elasticity is None
                    else substitution_elasticity)
    if substitution == 1.0:
        raise ValueError("the constant-elasticity mix is undefined at a substitution elasticity of one")
    return Basket(tuple(specs), substitution, need_data["needs"])


def satiation_limit(basket: Basket, need_id: str) -> Optional[float]:
    return basket.need_data[need_id].get(SATIATION_FIELD)


def need_prices(basket: Basket, view: MarketView, tile: TileId) -> List[PricedNeed]:
    """Each need that has a priced good on this tile, with its price index and the spending shares of
    its goods (a constant-elasticity mix: cheaper per need unit takes more)."""
    exponent = 1.0 - basket.substitution
    priced = []
    for spec in basket.needs:
        rows = []
        for good, effect in spec.goods:
            price = view.price(good, view.area_of(good, tile))
            if price is not None and price > 0.0 and effect > 0.0:
                rows.append((good, price, effect, (price / effect) ** exponent))
        if not rows:
            continue
        power = math.fsum(row[3] for row in rows)
        priced.append(PricedNeed(spec, power ** (1.0 / exponent),
                                 tuple((good, price, effect, weight / power)
                                       for good, price, effect, weight in rows)))
    return priced


def subsistence_cost_per_person(priced: List[PricedNeed]) -> float:
    """What one person's floors cost a year at these prices."""
    return math.fsum(need.price_index * need.spec.subsistence_per_person for need in priced)
