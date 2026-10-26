"""The materials module's rules as plain functions of plain values: what a year's work draws, what supplies it, how far
the supply goes and what the stock accounting leaves."""
import collections
from typing import Any, Callable, Dict, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, Tuple

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from .constants import (COKE_PER_CHARCOAL, FIREWOOD_PER_CHARCOAL_MASS_RATIO, GENERIC_ELECTRIC_LOAD_KW, HOURS_PER_YEAR,
                        LAB_SCALE_SUFFIX, MARKET_STANDING_SHARE_CEILING, SALTPETRE_TRADE_ROUTE_TONNES_PER_YR,
                        STANDING_MATERIAL_DRAW_SHARE)

COKE_REPLACES = ("charcoal_kg", "firewood_kg")


def build_span(node: Mapping[str, Any]) -> float:
    """Years a node's build takes, at least one."""
    return max(1.0, float(node.get("build_yrs") or node.get("yrs") or 1.0))


def normalized(material: Any, minable: Iterable[str], price_keys: Mapping[str, Any], is_commodity: Callable[[str], bool]) -> str:
    """The key a name means: the short curated name a mine has always used, or the exact material key the tree uses."""
    material = str(material or "").strip().lower()
    if not material or material in minable:
        return material
    if material in price_keys or is_commodity(material):
        return material
    for suffix in ("_kg", "_g"):
        candidate = material + suffix
        if candidate in price_keys:
            return candidate
    return material


def tag_of(material: str, checks: Mapping[str, Tuple[str, str]], commodity_of: Mapping[str, str]) -> Tuple[str, str]:
    """(commodity, supply-pool tag) a material key draws on: the tracked pair, else its curated commodity, else itself."""
    pair = checks.get(material)
    if pair:
        return pair
    commodity = commodity_of.get(material, material)
    return (commodity, "mine:" + commodity)


def fuel_choice(requirement_groups: Optional[Sequence[Mapping[str, Any]]], is_held: Callable[[str], bool]) -> str:
    """Which fuel a node burns: coke when the best fuel option held is coke or coal, else charcoal."""
    for group in (requirement_groups or []):
        if "fuel" not in str(group.get("group", "")).lower():
            continue
        best, pick = 0.0, None
        for option, quality in sorted((group.get("options") or {}).items()):
            if is_held(option) and float(quality) > best:
                best, pick = float(quality), option
        if pick and ("coke" in pick or "coal" in pick):
            return "coke"
    return "charcoal"


def annual_demand(active_keys: Iterable[str], nodes: Mapping[str, Any], uses_coke: Callable[[str], bool],
                  standing_terms: Iterable[Tuple[str, float]]) -> collections.Counter:
    """Tonnes a year of every material the active projects draw over their build, plus what the finished installations
    keep drawing."""
    demand: collections.Counter = collections.Counter()
    for node_id in active_keys:
        node = nodes[node_id]
        span = build_span(node)
        coke = uses_coke(node_id)
        for material, quantity in sorted(node["mat"].items()):
            if coke and material in COKE_REPLACES:
                demand["coal_kg"] += float(quantity) * COKE_PER_CHARCOAL / span / KILOGRAMS_PER_TONNE
                continue
            demand[material] += float(quantity) / span / KILOGRAMS_PER_TONNE
    for material, amount in standing_terms:
        demand[material] += amount
    return demand


def standing_terms(done_in_order: Iterable[str], nodes: Mapping[str, Any],
                   uses_coke: Callable[[str], bool]) -> List[Tuple[str, float]]:
    """(material, tonnes a year) for every finished installation that keeps drawing material, in done order."""
    terms: List[Tuple[str, float]] = []
    for node_id in done_in_order:
        node = nodes[node_id]
        if node["up"] <= 0 or not node["mat"]:
            continue
        span = build_span(node)
        coke = uses_coke(node_id)
        for material, quantity in sorted(node["mat"].items()):
            if coke and material in COKE_REPLACES:
                terms.append(("coal_kg", (STANDING_MATERIAL_DRAW_SHARE * float(quantity)
                                          * COKE_PER_CHARCOAL / span / KILOGRAMS_PER_TONNE)))
                continue
            terms.append((material, STANDING_MATERIAL_DRAW_SHARE * float(quantity) / span / KILOGRAMS_PER_TONNE))
    return terms


def project_needs(node: Mapping[str, Any], uses_coke: bool) -> collections.Counter:
    """{material key: units} a project physically consumes, with the fuel substitution the throttle applies."""
    needs: collections.Counter = collections.Counter()
    for material, quantity in sorted(node["mat"].items()):
        if uses_coke and material in COKE_REPLACES:
            needs["coal_kg"] += float(quantity) * COKE_PER_CHARCOAL
        else:
            needs[material] += float(quantity)
    return needs


def market_tonnes(national_tonnes: float, share: float, is_charcoal: bool, standing_factor: Optional[float],
                  output_scale: float, sea_routes: int, import_tonnes: float) -> float:
    """Tonnes a year of a commodity the market sells the seat: the national output's share, widened by standing (not for
    charcoal, which no standing makes travel), scaled to the territory held, plus a sea route's tonnage and what a
    trading partner brings."""
    if not is_charcoal:
        if standing_factor is not None:
            share *= standing_factor
        share = min(share, MARKET_STANDING_SHARE_CEILING)
    market = national_tonnes * share * output_scale
    for _route in range(sea_routes):
        market += SALTPETRE_TRADE_ROUTE_TONNES_PER_YR
    return market + import_tonnes


def demand_by_tag(demand: Mapping[str, float], tag_of_material: Callable[[str], Tuple[str, str]]) -> collections.Counter:
    """Demand grouped by the (commodity, supply tag) it draws on, so materials that share a pool add up."""
    by_tag: collections.Counter = collections.Counter()
    for material, amount in sorted(demand.items()):
        if amount:
            by_tag[tag_of_material(material)] += amount
    return by_tag


def demand_and_own_supply(by_tag: Mapping[Tuple[str, str], float], own_supply_of: Callable[[str], float]
                          ) -> Dict[str, Tuple[float, float]]:
    """{commodity: (demand, own supply)} with tags that share one land base expressed in the units of the reference tag,
    so the demands add and the own supply is the largest of them."""
    demand_scale = {"forest4": 1.0 / FIREWOOD_PER_CHARCOAL_MASS_RATIO}
    totals: Dict[str, Tuple[float, float]] = {}
    for (commodity, tag), need in sorted(by_tag.items()):
        scale = demand_scale.get(tag, 1.0)
        demand, own = totals.get(commodity, (0.0, 0.0))
        own = max(own, own_supply_of(tag) * scale)
        totals[commodity] = (demand + need * scale, own)
    return totals


def throttle_demand_split(demand: Mapping[str, float], tag_of_material: Callable[[str], Tuple[str, str]]
                          ) -> Tuple[collections.Counter, collections.Counter]:
    """`demand` as (industrial, laboratory) tonnes a year by (commodity, tag): a key in grams is a bench quantity."""
    industrial: collections.Counter = collections.Counter()
    lab: collections.Counter = collections.Counter()
    for material, amount in sorted(demand.items()):
        if not amount:
            continue
        pair = tag_of_material(material)
        if material.endswith(LAB_SCALE_SUFFIX) and not material.endswith("_kg"):
            lab[pair] += amount / KILOGRAMS_PER_TONNE
        else:
            industrial[pair] += amount
    return industrial, lab


def shortfall(need: float, own: float, market: float) -> float:
    """Tonnes a year of demand neither the seat's own supply nor the market covers."""
    if need <= 0.0:
        return 0.0
    return max(0.0, need - own - market)


def scarcity_factor(needs_and_own_supplies: Iterable[Tuple[float, float]], market_tonnes_: float, share_cap: float,
                    pressure_scale: float) -> float:
    """The dearest pressure among a material's demands. Each demand is (need, own supply) in tonnes; its share of the
    supply (own plus market) is capped, and the price rises by the pressure scale times the share squared. One when
    nothing is needed."""
    worst = 1.0
    for need, own_supply_ in needs_and_own_supplies:
        if need <= 0:
            continue
        supply = max(1e-9, own_supply_ + market_tonnes_)
        share = min(share_cap, need / supply)
        worst = max(worst, 1.0 + pressure_scale * share * share)
    return worst


def premium_sentence(rows: Sequence[Tuple[str, float]]) -> Optional[str]:
    """The line on materials trading above book price because the seat's own demand leans on the market; None when none."""
    if not rows:
        return None
    ordered = sorted(rows, key=lambda entry: -entry[1])
    worst = ordered[0]
    return ("%d material%s trading above book price because your own "
            "demand is leaning on what the market will sell: worst is "
            "%s at %d%% of book. Sinking your own mine or production "
            "capacity in it brings this back down, the same way it "
            "does for iron - 'quote mine %s' shows the price"
            % (len(ordered), "" if len(ordered) == 1 else "s", worst[0], round(worst[1] * 100), worst[0]))


# ---- the throttle -----------------------------------------------------------------------------------------------

class MaterialDraw(NamedTuple):
    """What one material's year did: how much of each need it met, the pace it allows, and the stock it leaves."""
    lab_drawn: float
    industrial_drawn: float
    pace: Optional[float]      # the fraction of planned work this material supports; None when it covers the need
    banked: float              # own production and prior stock left undrawn
    net_draw: float            # drawn beyond what was owned, which is what the market was asked for


def draw_one_material(opening_stock: float, own_supply_: float, market_tonnes_: float, lab_need: float,
                      industrial_need: float, pace_floor: float) -> MaterialDraw:
    """One material's year. `opening_stock` plus `own_supply_` is physically owned and can bank; `market_tonnes_` is a
    standing offer that can be drawn but is never kept. Laboratory-scale need is met first and never sets the pace; an
    industrial need the owned and offered tonnes cannot cover slows work to their share of it, never below `pace_floor`."""
    owned = opening_stock + own_supply_
    have = owned + market_tonnes_
    lab_drawn = min(lab_need, have)
    have -= lab_drawn
    industrial_drawn, pace = 0.0, None
    if industrial_need > 1e-12:
        if have < industrial_need:
            pace = max(pace_floor, have / industrial_need)
            industrial_drawn = have
        else:
            industrial_drawn = industrial_need
    banked = max(0.0, owned - lab_drawn - industrial_drawn)
    return MaterialDraw(lab_drawn, industrial_drawn, pace, banked, lab_drawn + industrial_drawn - owned)


class ThrottleReading(NamedTuple):
    """The year's material pace, the pool that binds it and what banking it leaves in the tonnes ledger."""
    pace: float
    binding: Optional[str]
    banked: Tuple[Tuple[str, float], ...]     # (commodity, tonnes) in the order they are set; a later set of one commodity wins
    draws: Tuple[Tuple[str, float], ...]      # (commodity, tonnes drawn beyond what was owned) in the same order


def throttle_reading(industrial: Mapping[Tuple[str, str], float], lab: Mapping[Tuple[str, str], float],
                     own_tags: Iterable[Tuple[str, str]], electricity_need: float, electricity_have: float,
                     opening_stock: Mapping[str, float], own_supply_of: Callable[[str], float],
                     market_tonnes_of: Callable[[str], float], pace_floor: float) -> ThrottleReading:
    """How much of the year's planned work the materials and electricity support: the worst of electricity and each
    tracked pool, the unused owned part of every pool banked again. Changes nothing."""
    worst, who = 1.0, None
    if electricity_need > 1e-9 and electricity_have < electricity_need:
        fraction = max(pace_floor, electricity_have / electricity_need)
        if fraction < worst:
            worst, who = fraction, "electricity"
    all_tags = set(industrial) | set(lab) | set(own_tags)
    banked: List[Tuple[str, float]] = []
    draws: List[Tuple[str, float]] = []
    for commodity, tag in sorted(all_tags):
        draw = draw_one_material(opening_stock.get(commodity, 0.0), own_supply_of(tag), market_tonnes_of(commodity),
                                 lab.get((commodity, tag), 0.0), industrial.get((commodity, tag), 0.0), pace_floor)
        if draw.pace is not None and draw.pace < worst:
            worst, who = draw.pace, commodity
        banked.append((commodity, draw.banked))
        draws.append((commodity, draw.net_draw))
    return ThrottleReading(worst, who, tuple(banked), tuple(draws))


def input_pools(materials: Iterable[str], uses_coke: bool, pool_of: Callable[[str], str], lab_scale_suffix: str,
                kilogram_suffix: str = "_kg") -> Set[str]:
    """The pools a project's material inputs draw on. A project on coke draws coal where it names charcoal or firewood;
    gram-scale purchases never take part in the flow throttle."""
    pools = set()
    for material in materials:
        effective = "coal_kg" if uses_coke and material in COKE_REPLACES else material
        if effective.endswith(lab_scale_suffix) and not effective.endswith(kilogram_suffix):
            continue
        pools.add(pool_of(effective))
    return pools


def shared_throttle(factor: float, binding: Optional[str], project_pools: Set[str]) -> float:
    """The portfolio's throttle `factor` for a project that draws on the `binding` pool; full pace for any other, and for
    a throttle too slight to matter."""
    if factor >= 0.999 or not binding:
        return 1.0
    return factor if binding in project_pools else 1.0


# ---- electricity ------------------------------------------------------------------------------------------------

def electricity_demand_kw(curated: Mapping[str, Tuple[str, float]], annual_tonnes: Callable[[str, str], float],
                          load_ids: Set[str], nodes: Mapping[str, Any], active: Mapping[str, Any], done: Set[str],
                          operating: Set[str]) -> float:
    """Average continuous kW drawn by work in hand: the curated heavy processes by their specific energy, every other
    node gated on generated electricity by one flat figure while it is being built, half of it while it stands and runs."""
    total = 0.0
    for node_id, (material, kwh_per_kg) in sorted(curated.items()):
        tonnes = annual_tonnes(node_id, material)
        if tonnes <= 0:
            continue
        total += (tonnes * KILOGRAMS_PER_TONNE * kwh_per_kg) / HOURS_PER_YEAR
    for node_id in sorted(load_ids - set(curated)):
        node = nodes.get(node_id)
        if node is None:
            continue
        if node_id in active:
            total += GENERIC_ELECTRIC_LOAD_KW
        elif node_id in done and float(node.get("up") or 0) > 0 and node_id in operating:
            total += STANDING_MATERIAL_DRAW_SHARE * GENERIC_ELECTRIC_LOAD_KW
    return total


def node_annual_tonnes(node: Optional[Mapping[str, Any]], material: str, is_active: bool, is_done: bool) -> float:
    """Tonnes a year ONE node draws of `material`: its build-time rate while it is built, the standing share of that rate
    while it stands and costs upkeep."""
    if node is None:
        return 0.0
    quantity = float((node.get("mat") or {}).get(material, 0.0))
    if quantity <= 0:
        return 0.0
    span = build_span(node)
    if is_active:
        return quantity / span / KILOGRAMS_PER_TONNE
    if is_done and float(node.get("up") or 0) > 0:
        return STANDING_MATERIAL_DRAW_SHARE * quantity / span / KILOGRAMS_PER_TONNE
    return 0.0


def generation_breakdown(done: Set[str], tree: Mapping[str, Any], generation_nodes: Mapping[str, Mapping[str, Any]],
                         prime_mover_nodes: Mapping[str, Mapping[str, Any]], anchor_kw_of: Callable[[str], float]
                         ) -> Dict[str, Any]:
    """What the seat can generate and transmit in kilowatts: local and grid generation, transmission, the best mechanical
    prime mover of each family (informational) and the generation data of built nodes by source."""
    def generation_kw(role: str) -> float:
        return sum(anchor_kw_of(generation_nodes[node_id]["tier"]) for node_id in generation_nodes
                   if generation_nodes[node_id]["role"] == role and node_id in done)
    local_kw = generation_kw("local")
    grid_kw = generation_kw("grid")
    transmission_kw = generation_kw("transmission")
    mechanical_kw: Dict[str, float] = {}
    families: Dict[str, Tuple[str, List[str]]] = {}
    for node_id in prime_mover_nodes:
        spec = prime_mover_nodes[node_id]
        families.setdefault(spec["family"], (spec["tier"], []))[1].append(node_id)
    for family, (tier, chain) in sorted(families.items()):
        mechanical_kw[family] = anchor_kw_of(tier) if any(node_id in done for node_id in chain) else 0.0
    sources_kw: Dict[str, float] = {}
    for node_id in sorted(done):
        generator = tree.get(node_id, {}).get("electricity_generation") or {}
        if generator:
            source = generator.get("source")
            capacity_kw = float(generator.get("capacity_kw", 0.0))
            if not source or capacity_kw < 0:
                raise ValueError("%s has invalid electricity_generation data" % node_id)
            sources_kw[source] = sources_kw.get(source, 0.0) + capacity_kw
    mod_generation_kw = sum(sources_kw.values())
    return {"local_kw": local_kw, "grid_kw": grid_kw, "transmission_kw": transmission_kw, "mechanical_kw": mechanical_kw,
            "sources_kw": sources_kw, "total_kw": local_kw + grid_kw + mod_generation_kw}


def installed_by_tier(done: Set[str], generation_nodes: Mapping[str, Mapping[str, Any]],
                      anchor_kw_of: Callable[[str], float]) -> Dict[str, float]:
    """{tier node id: kW of built generating plant filed under that tier}; transmission is not generation."""
    by_tier: Dict[str, float] = {}
    for node_id in generation_nodes:
        spec = generation_nodes[node_id]
        if node_id in done and spec["role"] != "transmission":
            by_tier[spec["tier"]] = by_tier.get(spec["tier"], 0.0) + anchor_kw_of(spec["tier"])
    return by_tier


# ---- a project's material bill ------------------------------------------------------------------------------------

def material_bill(needs: Mapping[str, float], span: float, tonnes_per_unit: Callable[[str], float],
                  tag_of_material: Callable[[str], Tuple[str, str]], stock_of: Callable[[str], float],
                  unclaimed_own_of: Callable[[str], float], purchase_cost: Callable[..., Any],
                  market_tonnes_of: Callable[[str], float], own_supply_of: Callable[[str], float]) -> Dict[str, Any]:
    """The rows of a project's material bill and the cost of what is missing. `needs` is {material key: units}; `span`
    the years the build takes. Each need is met from the stock, then the seat's own unclaimed output over the build, then
    bought; what the market can deliver this year is paid at the start and the rest at today's quote."""
    stock_left: Dict[str, float] = {}
    own_left: Dict[str, float] = {}
    headroom_left: Dict[str, float] = {}
    bought: collections.Counter = collections.Counter()
    rows: List[Dict[str, Any]] = []
    total = 0.0
    for material, units in sorted(needs.items()):
        commodity, tag = tag_of_material(material)
        needed = units * tonnes_per_unit(material)
        stock_left.setdefault(commodity, stock_of(commodity))
        own_left.setdefault(tag, unclaimed_own_of(tag) * span)
        from_stock = min(needed, stock_left[commodity])
        stock_left[commodity] -= from_stock
        from_own = min(needed - from_stock, own_left[tag])
        own_left[tag] -= from_own
        missing = needed - from_stock - from_own
        quoted = purchase_cost(material, missing, bought[commodity, tag])
        cost, mean_price = quoted if quoted else (0.0, 0.0)
        bought[commodity, tag] += missing
        deliverable_cost = cost
        lab_scale = material.endswith(LAB_SCALE_SUFFIX) and not material.endswith("_kg")
        headroom_left.setdefault(commodity, market_tonnes_of(commodity))
        deliverable = missing if lab_scale else min(missing, headroom_left[commodity])
        if not lab_scale:
            headroom_left[commodity] -= deliverable
        if quoted and missing > deliverable:
            # past a year's market supply the rest is bought over the following years at today's quote
            spot = purchase_cost(material, 0.0)
            deliverable_cost = (purchase_cost(material, deliverable, bought[commodity, tag] - missing)[0]
                                if deliverable > 0 else 0.0)
            cost = deliverable_cost + (missing - deliverable) * spot[1]
            mean_price = cost / missing
        total += cost
        rows.append({"material": material, "needed_tonnes": needed,
                     "held_tonnes": from_stock + from_own,
                     "held_from_stock_tonnes": from_stock,
                     "held_from_own_output_tonnes": from_own,
                     "missing_tonnes": missing,
                     "price_per_tonne": mean_price, "cost_of_missing": cost,
                     "cost_of_deliverable": deliverable_cost,
                     "deliverable_now_tonnes": deliverable,
                     "own_supply_tonnes_per_year": own_supply_of(tag),
                     "years_of_supply_it_takes": (
                         None if lab_scale or missing <= 0 else missing / max(
                             1e-9, market_tonnes_of(commodity) + own_supply_of(tag))),
                     "priced": quoted is not None})
    return {"rows": rows, "cost_of_missing": total}


def unclaimed(own_tonnes: float, claimed: float) -> float:
    """Yearly own output of a supply pool that no other running project has claimed."""
    return max(0.0, own_tonnes - claimed)


def bill_parts(bill: Mapping[str, Any]) -> Tuple[float, float]:
    """(cost of the missing materials, of which paid for at the start), before the geography and opposition factors."""
    up_front = 0.0
    for row in bill["rows"]:
        if row["missing_tonnes"] > 0 and row["priced"]:
            up_front += row["cost_of_deliverable"]
    return bill["cost_of_missing"], up_front


# ---- reach -------------------------------------------------------------------------------------------------------

ROUTE_HELD = "held"
ROUTE_MARKET = "market"
ROUTE_IMPORTED = "imported"
ROUTE_MAKEABLE = "makeable"
ROUTE_UNAVAILABLE = "unavailable"


def supply_route(stock_tonnes: float, own_tonnes: float, market_tonnes_: float, import_tonnes: float,
                 can_be_bought: bool) -> str:
    """How the seat gets a material today: held, from the market, imported, makeable (priced but no producer runs it) or
    unavailable."""
    if stock_tonnes > 0.0 or own_tonnes > 0.0:
        return ROUTE_HELD
    if market_tonnes_ - import_tonnes > 0.0:
        return ROUTE_MARKET
    if import_tonnes > 0.0:
        return ROUTE_IMPORTED
    if can_be_bought:
        return ROUTE_MAKEABLE
    return ROUTE_UNAVAILABLE


def unsupplied_sentence(material: str, route: str, makers: Sequence[str], held_makers: Sequence[str]) -> str:
    """One sentence on why nothing of `material` reaches the seat, or "" when something does. `makers` are the visible
    concerns that would make it, `held_makers` those among them already built."""
    if route == ROUTE_MAKEABLE:
        if held_makers:
            return ("No producer runs %s yet, though %s can make it: open it, or wait for a producer to "
                    "start." % (material, ", ".join(held_makers[:3])))
        if makers:
            return ("No producer runs %s yet; %s would make it." % (material, ", ".join(makers[:3])))
        return ("No producer runs %s yet: a technique you hold makes it, but nothing is set up to, so "
                "the work waits for a producer to start." % material)
    if route == ROUTE_UNAVAILABLE:
        return ("No one in reach makes or sells %s: it cannot be bought until a technique that makes it "
                "is reached, a route opens to a partner that does, or a partner gains it." % material)
    return ""


# ---- a standing shortage ------------------------------------------------------------------------------------------

# Change in the share of planned work that still runs, from the last reported figure, that counts as new
# (presentation threshold, not a mechanism).
MATERIAL_THROUGHPUT_CHANGE = 0.10
STEADY_BAND = 0.02     # smaller moves than this between years read as steady


def material_words(material: Any) -> str:
    """A material key in player words: "alum_kg" is "alum", "saltpetre" stays as it is."""
    words = str(material)
    for suffix in ("_kg", "_g", "_t"):
        words = words.removesuffix(suffix)
    return words.replace("_", " ")


def noted_shortage(condition: Optional[Dict[str, Any]], material: str, throughput: float, year: int
                   ) -> Tuple[Dict[str, Any], bool]:
    """(the standing condition after this year's shortage, whether it deserves a fresh event): news is a new material, or
    a throughput that has moved materially since the last time it was reported. The condition given is updated in place."""
    if not condition or condition["material"] != material:
        return ({"material": material, "since": year, "reported": throughput, "previous": throughput,
                 "latest": throughput}, True)
    condition["previous"] = condition["latest"]
    condition["latest"] = throughput
    if abs(throughput - condition["reported"]) >= MATERIAL_THROUGHPUT_CHANGE:
        condition["reported"] = throughput
        return condition, True
    return condition, False


def condition_row(condition: Optional[Mapping[str, Any]], year: int, deficit_tonnes: Optional[float]) -> List[Dict[str, Any]]:
    """The standing shortage as rows for the state screen, empty when none. `deficit_tonnes` is the shortfall of the
    material, or None when the caller did not ask for it."""
    if not condition:
        return []
    change = condition["latest"] - condition["previous"]
    trend = "improving" if change > STEADY_BAND else "worsening" if change < -STEADY_BAND else "steady"
    row = {"material": condition["material"], "throughput": condition["latest"],
           "years": max(1, year - condition["since"] + 1), "trend": trend}
    if deficit_tonnes is not None and deficit_tonnes > 0.0:
        row["deficit_tonnes_per_year"] = round(deficit_tonnes, 1)
    return [row]


def condition_line(row: Mapping[str, Any], mass_rate_label: str = "t/year") -> str:
    """One readable line for a standing condition; a text screen passes the label of the unit it shows the deficit in."""
    parts = ["%s CONSTRAINED: work at %d%% of plan" % (material_words(row["material"]).upper(), round(100 * row["throughput"]))]
    if row.get("deficit_tonnes_per_year"):
        parts.append("short %s %s" % ("{:,.1f}".format(row["deficit_tonnes_per_year"]), mass_rate_label))
    parts.append("year %d, %s" % (row["years"], row["trend"]))
    return ", ".join(parts)
