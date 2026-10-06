"""What people need, priced: the one household need-and-floor model every actor reads.

A need has a physical floor per person per year, a weight in surplus spending, and goods that serve it
with an effectiveness each. Goods inside a need share spending by a constant-elasticity mix on cost per
need unit; the need's price index is what one need unit costs at that mix (need units add one for one: a
calorie is a calorie, so adding a good that delivers the same calories at the same price changes
nothing). Everything here is pure: prices come in as a function of the good, climate floors as plain
numbers, and no actor, market or tile is named. The economy, the aggregate demand model and the strata
read this module; they add what only they know (cash, durables, income bins, a purse).
"""
import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare
from sim.world import demand
from sim.world.need_satiation import SATIATION_FIELD, apply_satiation

NEED_SUBSTITUTION_ELASTICITY = declare(
    "NEED_SUBSTITUTION_ELASTICITY", 2.0,
    kind="temporary_heuristic",
    unit="dimensionless (constant elasticity of substitution between goods "
         "serving one need)",
    source=None,
    confidence="D",
    why="How sharply households move spending toward whichever good gives "
        "more of a need per unit cost. Above one, a good that is twice as "
        "effective per cost takes more than twice the share; one would "
        "spend a fixed share per good whatever it costs. A measured "
        "cross-price elasticity between close substitutes (metals for "
        "tools, fabrics for clothing) would replace it.")


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
    price_index: float                     # money per need unit of the mix the household buys
    goods: Tuple[Tuple[str, float, float, float], ...]   # (good, price, effectiveness, share of spending)
    ceilings: Tuple[float, ...] = ()       # per good: the price a buyer stops buying it above (inf if none)


def goods_attributes(need_data: Mapping[str, Any],
                     production: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Per good: `satisfies` {need: effectiveness per unit} and `supply_per_year`.

    Read from the needs file's goods table and from production entries, where
    an entry's attributes belong to its dominant output.
    """
    merged: Dict[str, Dict[str, Any]] = {}
    for material, attributes in (need_data.get("goods") or {}).items():
        merged[material] = {"satisfies": dict(attributes.get("satisfies") or {}),
                            "supply_per_year": attributes.get("supply_per_year")}
    for entry in production.values():
        if not entry.get("outputs") or not (entry.get("satisfies") or entry.get("supply_per_year")):
            continue
        material = demand._dominant_output_key(entry)
        record = merged.setdefault(material, {"satisfies": {}, "supply_per_year": None})
        record["satisfies"].update(entry.get("satisfies") or {})
        if entry.get("supply_per_year"):
            record["supply_per_year"] = entry["supply_per_year"]
    return merged


def make_basket(need_data: Mapping[str, Any], production: Mapping[str, Any],
                substitution_elasticity: Optional[float] = None) -> Basket:
    attributes = goods_attributes(need_data, production)
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
    substitution = (NEED_SUBSTITUTION_ELASTICITY if substitution_elasticity is None
                    else substitution_elasticity)
    if substitution == 1.0:
        raise ValueError("the constant-elasticity mix is undefined at a substitution elasticity of one")
    return Basket(tuple(specs), substitution, need_data["needs"])


def satiation_limit(basket: Basket, need_id: str) -> Optional[float]:
    return basket.need_data[need_id].get(SATIATION_FIELD)


def need_prices(basket: Basket, price_of: Callable[[str], Optional[float]]) -> List[PricedNeed]:
    """Each need that has a priced good, with its price index and the spending shares of its goods
    (a constant-elasticity mix: cheaper per need unit takes more). `price_of(good)` is None for a
    good with no price."""
    exponent = 1.0 - basket.substitution
    priced = []
    for spec in basket.needs:
        rows = []
        for good, effect in spec.goods:
            price = price_of(good)
            if price is not None and price > 0.0 and effect > 0.0:
                rows.append((good, price, effect, (price / effect) ** exponent))
        if not rows:
            continue
        power = math.fsum(row[3] for row in rows)
        shares = [(good, price, effect, weight / power) for good, price, effect, weight in rows]
        # need units add up one for one (a calorie is a calorie): a unit costs what the chosen mix pays
        # per unit, between the cheapest and dearest good; substitution shapes only the mix
        units_per_money = math.fsum(share * effect / price for _good, price, effect, share in shares)
        priced.append(PricedNeed(spec, 1.0 / units_per_money, tuple(shares), price_ceilings(shares)))
    return priced


def price_ceilings(shares) -> Tuple[float, ...]:
    """The cheapest way to meet a need is bought up to the cost of the next cheapest: past that,
    people switch. A dearer good has no ceiling (it is bought for variety)."""
    costs = [price / effect for _good, price, effect, _share in shares]
    ceilings = []
    for index, (_good, price, effect, _share) in enumerate(shares):
        others = costs[:index] + costs[index + 1:]
        parity = min(others) * effect if others else math.inf
        ceilings.append(parity if parity >= price else math.inf)
    return tuple(ceilings)


def subsistence_cost_per_person(priced: Sequence[PricedNeed]) -> float:
    """What one person's floors cost a year at these prices."""
    return math.fsum(need.price_index * need.spec.subsistence_per_person for need in priced)


def need_units(priced: Sequence[PricedNeed], basket: Basket, people: float, surplus: float):
    """(floor units, total units) per need id: floors plus weighted surplus, limited by satiation."""
    floors = {need.spec.need_id: need.spec.subsistence_per_person * people for need in priced}
    weight_total = math.fsum(need.spec.budget_weight for need in priced)
    totals = dict(floors)
    if surplus > 0.0 and weight_total > 0.0:
        for need in priced:
            totals[need.spec.need_id] += (surplus * need.spec.budget_weight / weight_total
                                          / need.price_index)
        limits = {need.spec.need_id: {"surplus_budget_share": need.spec.budget_weight,
                                      "satiation_per_capita_per_year": satiation_limit(basket, need.spec.need_id)}
                  for need in priced}
        apply_satiation(totals, {need.spec.need_id: need.price_index for need in priced}, limits, people)
    return floors, totals
