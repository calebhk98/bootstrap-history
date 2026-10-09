"""What people need, priced: the one household need-and-floor model every actor reads.

A need has a physical floor per person per year, a weight in surplus spending, and goods that serve it
with an effectiveness each. Goods inside a need share spending by a constant-elasticity mix on cost per
need unit; the need's price index is what one need unit costs at that mix (need units add one for one: a
calorie is a calorie, so adding a good that delivers the same calories at the same price changes
nothing). Everything here is pure: prices come in as a function of the good, climate floors as plain
numbers, and no actor, market or tile is named. The economy, the aggregate demand model and the strata
read this module; they add what only they know (cash, durables, income bins, a purse).
"""
import dataclasses
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
                            "supply_per_year": attributes.get("supply_per_year"),
                            "bought_by_households": attributes.get("bought_by_households", True)}
    for entry in production.values():
        if not entry.get("outputs") or not (entry.get("satisfies") or entry.get("supply_per_year")):
            continue
        material = demand._dominant_output_key(entry)
        record = merged.setdefault(material, {"satisfies": {}, "supply_per_year": None})
        record["satisfies"].update(entry.get("satisfies") or {})
        if entry.get("supply_per_year"):
            record["supply_per_year"] = entry["supply_per_year"]
    return merged


def need_floor(data: Mapping[str, Any]) -> float:
    """A need's floor per person per year from its data: a named constant, a stated figure, or a held
    stock that wears out (`held_stock_per_capita` over `service_life_years`, as for any durable)."""
    if data.get("subsistence_constant"):
        return float(getattr(demand, data["subsistence_constant"]))
    if data.get("held_stock_per_capita") and data.get("service_life_years"):
        return float(data["held_stock_per_capita"]) / float(data["service_life_years"])
    return float(data.get("subsistence_per_capita_per_year", 0.0))


def civ_scale(data: Mapping[str, Any], civ_values: Mapping[str, Any]) -> float:
    """What share of the population a need applies to: a need that names `scales_with_civ_field` (writing
    follows literacy) is scaled by that field of the civilisation; one that names none applies to all."""
    field = data.get("scales_with_civ_field")
    return 1.0 if not field else max(0.0, min(1.0, float(civ_values.get(field, 0.0))))


def make_basket(need_data: Mapping[str, Any], production: Mapping[str, Any],
                substitution_elasticity: Optional[float] = None,
                civ_values: Optional[Mapping[str, Any]] = None) -> Basket:
    """The household basket. A good households do not buy themselves (`bought_by_households` false, such as
    the coin the mint keeps struck) serves no need in it. `civ_values` are the civilisation fields a need may
    scale with; a need that scales with a field not given applies to nobody."""
    attributes = goods_attributes(need_data, production)
    civ_values = civ_values or {}
    serving: Dict[str, List[Tuple[str, float]]] = {}
    for good in sorted(attributes):
        if attributes[good].get("bought_by_households") is False:
            continue
        for need_id, effect in sorted(attributes[good]["satisfies"].items()):
            serving.setdefault(need_id, []).append((good, effect))
    specs = []
    for need_id in sorted(need_data["needs"]):
        data = need_data["needs"][need_id]
        scale = civ_scale(data, civ_values)
        specs.append(NeedSpec(need_id, need_floor(data) * scale, float(data["surplus_budget_share"]) * scale,
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


def need_units(priced: Sequence[PricedNeed], basket: Basket, people: float, surplus: float,
               satiate: bool = True):
    """(floor units, total units) per need id: floors plus weighted surplus, limited by satiation
    (unless `satiate` is off, for a caller that limits the sum over several groups itself)."""
    floors = {need.spec.need_id: need.spec.subsistence_per_person * people for need in priced}
    weight_total = math.fsum(need.spec.budget_weight for need in priced)
    totals = dict(floors)
    if surplus > 0.0 and weight_total > 0.0:
        for need in priced:
            totals[need.spec.need_id] += (surplus * need.spec.budget_weight / weight_total
                                          / need.price_index)
        if satiate:
            limit_satiation(totals, priced, basket, people)
    return floors, totals


def limit_satiation(totals: Dict[str, float], priced: Sequence[PricedNeed], basket: Basket, people: float) -> None:
    """Cap each satiable need's units at its per-head limit and move the freed spending, in place."""
    limits = {need.spec.need_id: {"surplus_budget_share": need.spec.budget_weight,
                                  "satiation_per_capita_per_year": satiation_limit(basket, need.spec.need_id)}
              for need in priced}
    apply_satiation(totals, {need.spec.need_id: need.price_index for need in priced}, limits, people)


def climate_floor_fields(basket: Basket) -> Dict[str, str]:
    """{need id: the climate floor name (`sim/world/climate_needs.py`) that sets its floor}, for the needs
    whose data names one in `subsistence_from_climate`."""
    return {need_id: spec["subsistence_from_climate"] for need_id, spec in basket.need_data.items()
            if spec.get("subsistence_from_climate")}


def basket_with_floors(basket: Basket, climate_floors: Mapping[str, float]) -> Basket:
    """The basket with each climate need's floor replaced by the named entry of `climate_floors`
    (floors per person per year, as `climate_needs.floors_for_tile` returns them)."""
    fields = climate_floor_fields(basket)
    needs = tuple(dataclasses.replace(need, subsistence_per_person=float(climate_floors[fields[need.need_id]]))
                  if need.need_id in fields else need for need in basket.needs)
    return dataclasses.replace(basket, needs=needs)


def mean_climate_basket(basket: Basket, tile_records_with_people: Sequence[Tuple[Mapping[str, Any], float]]) -> Basket:
    """The basket for a civilisation: each climate floor is the people-weighted mean of its tiles' floors
    (floors are nonlinear in temperature, so the mean is over floors, not over climates)."""
    if not climate_floor_fields(basket):
        return basket
    from sim.world import climate_needs
    total = math.fsum(people for _record, people in tile_records_with_people)
    if total <= 0.0:
        return basket
    by_tile = [(climate_needs.floors_for_tile(record), people) for record, people in tile_records_with_people]
    names = sorted(set(climate_floor_fields(basket).values()))
    return basket_with_floors(basket, {name: math.fsum(floors[name] * people for floors, people in by_tile) / total
                                       for name in names})


def climate_basket(basket: Basket, tile_record: Mapping[str, Any]) -> Basket:
    """The basket for a place with this climate (`lat`, `koppen_class`, optional `koppen_sample_mix`):
    warmth, clothing and shelter floors follow from heat balance."""
    from sim.world import climate_needs
    if not climate_floor_fields(basket):
        return basket
    return basket_with_floors(basket, climate_needs.floors_for_tile(tile_record))
