"""Demand from what goods do, not from a list of goods.

Households spend on needs (food, shelter, health, ...). A good declares which
needs it satisfies and how well per unit. Inside a need, goods compete on
effectiveness per unit cost. Everything a wanted good consumes is demanded in
turn through the recipes that make it, and so is what technologies under
development consume. Where supply is limited, the price that clears the
market is the scarcity price.

Needs and goods come from data/world/needs.json and mods (see
sim/engine/need_data.py); recipes from data/production/. This module takes
them as arguments.
"""
import collections
import math
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

from sim.constants import declare
from sim.world import demand, need_basket
from sim.world.need_basket import NEED_SUBSTITUTION_ELASTICITY, goods_attributes

def load_needs(root: str) -> Dict[str, Any]:
    """The base-and-enabled-mod needs and goods under `root` (sim/engine/need_data.py)."""
    from sim.engine import need_data
    return need_data.load_needs(root)


DERIVED_DEMAND_PRICE_ELASTICITY = declare(
    "DERIVED_DEMAND_PRICE_ELASTICITY", 1.0,
    kind="temporary_heuristic",
    unit="dimensionless (elasticity of an input's derived demand to its own price)",
    source=None,
    confidence="D",
    why="A recipe's input demand falls as the input gets dearer, because "
        "producers switch technique or cut output. The recipe graph here "
        "has fixed coefficients, so this stands in for the substitution "
        "that choice of technique would do; without it an input whose "
        "derived demand exceeds its supply has no finite clearing price.")

TECHNOLOGY_LOOKAHEAD_DEPTH = declare(
    "TECHNOLOGY_LOOKAHEAD_DEPTH", 1,
    kind="temporary_heuristic",
    unit="technology nodes (unreached prerequisite steps still counted as pursued)",
    source=None,
    confidence="D",
    why="A technology's build materials are demanded while it is being "
        "pursued, and only a technology whose prerequisites are held can "
        "be pursued now. One counts exactly those; a larger depth also "
        "counts what is one prerequisite further, on the view that "
        "people stockpile ahead of an obvious next step. Every pursued "
        "technology is assumed to be pursued at once, which overstates "
        "demand for materials many nodes share.")

DERIVED_DEMAND_MAX_SWEEPS = declare(
    "DERIVED_DEMAND_MAX_SWEEPS", 200,
    kind="temporary_heuristic",
    unit="sweeps",
    source=None,
    confidence="D",
    why="Cap on repeated passes over the recipe graph when a chain of "
        "recipes loops back on itself. Demand through a loop converges "
        "when each turn of the loop consumes less than it yields; the cap "
        "only stops a data error from spinning.")

DEMAND_CONVERGENCE_TOLERANCE = 1e-12
CLEARING_BISECTION_STEPS = 8
CLEARING_PASSES = 2
REUSE_RELATIVE_TOLERANCE = 1e-12
POLISH_MAX_STEPS = 60
POLISH_LOG_TOLERANCE = 1e-14
CLEARING_SEARCH_SPAN_DECADES = 9


def technology_material_demand(nodes: Iterable[Mapping[str, Any]], held: Set[str],
                               lookahead_depth: Optional[int] = None) -> Dict[str, float]:
    """{material: per-year quantity} consumed by technologies being pursued.

    A node is pursued when it is not held and every prerequisite is held, or,
    with a larger `lookahead_depth`, when at most that many unheld steps stand
    between it and what is held. Its build materials are spread over its
    build years.
    """
    depth_limit = TECHNOLOGY_LOOKAHEAD_DEPTH if lookahead_depth is None else lookahead_depth
    by_id = {node["id"]: node for node in nodes}
    depth: Dict[str, float] = {}

    def steps_needed(node_id: str) -> float:
        if node_id in held:
            return 0
        if node_id in depth:
            return depth[node_id]
        depth[node_id] = float("inf")   # a prerequisite cycle stays unreachable
        node = by_id.get(node_id)
        if node is not None:
            depth[node_id] = 1 + max(
                (steps_needed(prerequisite) for prerequisite in node.get("pre") or ()),
                default=0)
        return depth[node_id]

    totals: Dict[str, float] = collections.defaultdict(float)
    for node_id in sorted(by_id):
        if steps_needed(node_id) > depth_limit or node_id in held:
            continue
        node = by_id[node_id]
        years = node.get("build_yrs") or 1.0
        for material, quantity in (node.get("mat") or {}).items():
            totals[material] += quantity / years
    return dict(totals)


def declared_supply(need_data: Mapping[str, Any],
                    production: Mapping[str, Any]) -> Dict[str, float]:
    """{material: annual supply in its own unit} for goods that declare one."""
    return {material: attributes["supply_per_year"]
            for material, attributes in goods_attributes(need_data, production).items()
            if attributes.get("supply_per_year")}


def budget_weights_by_good(need_data: Mapping[str, Any], production: Mapping[str, Any],
                           available_materials: Set[str],
                           cost_per_unit: Optional[Mapping[str, float]] = None) -> Dict[str, float]:
    """{good: share of household spending} with no prices: each need's budget weight, normalised over
    needs an available good serves, split among those goods. `cost_per_unit` is what a unit of a good costs
    in any one currency (labour value when prices are unknown); the goods of a need then take spending as
    the household mix does (constant elasticity on cost per need unit, sim/world/need_basket.py). A good
    without a positive cost takes the mean weight of its need's priced goods; with no costs at all the
    split inside a need is equal."""
    attributes = goods_attributes(need_data, production)
    servers: Dict[str, List[str]] = collections.defaultdict(list)
    for material in sorted(available_materials):
        for need_id in attributes.get(material, {}).get("satisfies", {}):
            servers[need_id].append(material)
    weight_total = sum(need_data["needs"][need_id]["surplus_budget_share"]
                       for need_id in servers)
    weights: Dict[str, float] = collections.defaultdict(float)
    for need_id, materials in servers.items():
        share = need_data["needs"][need_id]["surplus_budget_share"] / weight_total
        inside = _mix_inside_need(need_id, materials, attributes, cost_per_unit or {})
        for material in materials:
            weights[material] += share * inside[material]
    return dict(weights)


def _mix_inside_need(need_id: str, materials: List[str], attributes: Mapping[str, Any],
                     cost_per_unit: Mapping[str, float]) -> Dict[str, float]:
    """Each good's share of its need's spending: cost per need unit to the power of one minus the substitution
    elasticity, normalised; equal where no cost is known."""
    exponent = 1.0 - NEED_SUBSTITUTION_ELASTICITY
    raw = {material: (cost_per_unit[material] / attributes[material]["satisfies"][need_id]) ** exponent
           for material in materials if cost_per_unit.get(material, 0.0) > 0.0}
    if not raw:
        return {material: 1.0 / len(materials) for material in materials}
    mean_raw = sum(raw.values()) / len(raw)
    filled = {material: raw.get(material, mean_raw) for material in materials}
    total = sum(filled.values())
    return {material: weight / total for material, weight in filled.items()}


def _polish_root(function, low: float, high: float) -> float:
    """Root of a decreasing function in [low, high] to full precision (Illinois
    false position on log price), so anchors vary smoothly with prices."""
    log_low, log_high = math.log(low), math.log(high)
    value_low, value_high = function(low), function(high)
    side = 0
    for _step in range(POLISH_MAX_STEPS):
        if value_low == value_high:
            break
        log_mid = (log_low * value_high - log_high * value_low) / (value_high - value_low)
        log_mid = min(max(log_mid, min(log_low, log_high)), max(log_low, log_high))
        value_mid = function(math.exp(log_mid))
        if value_mid > 0.0:
            log_low, value_low = log_mid, value_mid
            if side == 1:
                value_high *= 0.5
            side = 1
        else:
            log_high, value_high = log_mid, value_mid
            if side == -1:
                value_low *= 0.5
            side = -1
        if abs(log_high - log_low) < POLISH_LOG_TOLERANCE:
            break
    return math.exp(0.5 * (log_low + log_high))


class NeedDemandModel:
    """Household final demand by need, plus the demand recipes derive from it."""

    def __init__(self, need_data: Mapping[str, Any], production: Mapping[str, Any],
                 bins: Sequence[Any], technology_demand: Optional[Mapping[str, float]] = None,
                 substitution_elasticity: Optional[float] = None,
                 derived_price_elasticity: Optional[float] = None,
                 satiate: bool = False):
        # `satiate` limits a need that declares a per-head limit to it. The price solver leaves it
        # off (a limit would make the clearing price of a glutted metal collapse); the quantities
        # households actually buy turn it on.
        self.satiate = satiate
        self.needs = dict(need_data["needs"])
        self.production = production
        self.bins = list(bins)
        self.technology_demand = dict(technology_demand or {})
        self.substitution = (NEED_SUBSTITUTION_ELASTICITY if substitution_elasticity is None
                             else substitution_elasticity)
        self.derived_elasticity = (DERIVED_DEMAND_PRICE_ELASTICITY
                                   if derived_price_elasticity is None
                                   else derived_price_elasticity)
        self.effectiveness: Dict[str, Dict[str, float]] = collections.defaultdict(dict)
        for material, attributes in goods_attributes(need_data, production).items():
            for need_id, effect in attributes["satisfies"].items():
                self.effectiveness[need_id][material] = effect
        self._need_goods = {need_id: sorted(self.effectiveness.get(need_id, ()))
                            for need_id in sorted(self.needs)}
        self.basket = need_basket.make_basket(need_data, production, self.substitution)
        self.subsistence = {need.need_id: need.subsistence_per_person for need in self.basket.needs}
        self._input_per_unit_output = self._recipe_coefficients()
        self._influence_cache: Dict[str, Dict[str, float]] = {}

    def _recipe_coefficients(self) -> Dict[str, Dict[str, float]]:
        """{output: {input: quantity per unit output}}, averaged over the recipes
        whose dominant output it is (equal split; a stand-in for choice of technique).
        """
        # TEMPORARY HEURISTIC: recipes making one good are used in equal shares.
        producers: Dict[str, List[Dict[str, float]]] = collections.defaultdict(list)
        for recipe_key in sorted(self.production):
            entry = self.production[recipe_key]
            if not entry.get("outputs"):
                continue
            try:
                coefficients = demand.input_coefficients_per_unit_output(
                    recipe_key, self.production)
            except (KeyError, ValueError):
                continue
            producers[demand._dominant_output_key(entry)].append(coefficients)
        table: Dict[str, Dict[str, float]] = {}
        for material, recipes in producers.items():
            averaged: Dict[str, float] = collections.defaultdict(float)
            for coefficients in recipes:
                for input_material, quantity in coefficients.items():
                    averaged[input_material] += quantity / len(recipes)
            if averaged:
                table[material] = dict(averaged)
        return table

    def final_demand(self, prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: units households want per year} at `prices`: floors, price index and the
        surplus split come from the need-basket kernel; below the committed cost of every floor the
        protected-floor rule of sim/world/demand.py applies per income bin."""
        priced = need_basket.need_prices(self.basket, prices.get)
        if not priced:
            return {}
        weight_total = sum(need.spec.budget_weight for need in priced)
        price_index = {need.spec.need_id: need.price_index for need in priced}
        goods = tuple(demand.Good(need.spec.need_id, need.spec.subsistence_per_person,
                                  need.spec.budget_weight / weight_total) for need in priced)
        need_units = {need.spec.need_id: 0.0 for need in priced}
        committed = need_basket.subsistence_cost_per_person(priced)
        covered_population = 0.0
        covered_surplus = 0.0
        for income_bin in self.bins:
            surplus = income_bin.income_per_capita_per_year - committed
            if surplus >= 0.0:
                covered_population += income_bin.population
                covered_surplus += income_bin.population * surplus
                continue
            for good in goods:
                need_units[good.name] += (
                    income_bin.population * demand.household_quantity_demanded_per_capita(
                        good, price_index, income_bin.income_per_capita_per_year, goods))
        _floors, covered_units = need_basket.need_units(
            priced, self.basket, covered_population, covered_surplus, satiate=False)
        for need_id, units in covered_units.items():
            need_units[need_id] += units
        if self.satiate:
            need_basket.limit_satiation(need_units, priced, self.basket,
                                        sum(income_bin.population for income_bin in self.bins))
        quantities: Dict[str, float] = collections.defaultdict(float)
        for need in priced:
            spending = need.price_index * need_units[need.spec.need_id]
            for material, price, _effect, share in need.goods:
                quantities[material] += spending * share / price
        return dict(quantities)

    def _demand_from(self, sources: Mapping[str, float]) -> Dict[str, float]:
        """Total demand once every source's inputs are demanded through the recipes."""
        totals = dict(sources)
        for _sweep in range(DERIVED_DEMAND_MAX_SWEEPS):
            updated = dict(sources)
            for material in sorted(totals):
                for input_material, coefficient in self._input_per_unit_output.get(
                        material, {}).items():
                    updated[input_material] = (updated.get(input_material, 0.0)
                                               + totals[material] * coefficient)
            change = max((abs(updated.get(material, 0.0) - totals.get(material, 0.0))
                          for material in set(updated) | set(totals)), default=0.0)
            totals = updated
            if change <= DEMAND_CONVERGENCE_TOLERANCE * max(totals.values(), default=1.0):
                break
        return totals

    def _sources(self, prices: Mapping[str, float]) -> Dict[str, float]:
        sources = dict(self.final_demand(prices))
        for material, quantity in self.technology_demand.items():
            sources[material] = sources.get(material, 0.0) + quantity
        return sources

    def total_demand(self, prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: units demanded per year}: households, recipes, technologies."""
        return self._demand_from(self._sources(prices))

    def _influence(self, target: str) -> Dict[str, float]:
        """{source: units of `target` demanded per unit of that source}."""
        if target not in self._influence_cache:
            weights = {target: 1.0}
            materials = sorted(self._input_per_unit_output)
            for _sweep in range(DERIVED_DEMAND_MAX_SWEEPS):
                change = 0.0
                for material in materials:
                    value = (1.0 if material == target else 0.0) + sum(
                        coefficient * weights.get(input_material, 0.0)
                        for input_material, coefficient
                        in self._input_per_unit_output[material].items())
                    change = max(change, abs(value - weights.get(material, 0.0)))
                    weights[material] = value
                if change <= DEMAND_CONVERGENCE_TOLERANCE:
                    break
            self._influence_cache[target] = weights
        return self._influence_cache[target]

    def demand_for(self, material: str, prices: Mapping[str, float]) -> float:
        """Total demand for one material without sweeping the whole graph."""
        weights = self._influence(material)
        return sum(weights.get(source, 0.0) * quantity
                   for source, quantity in self._sources(prices).items())

    def byproduct_supply(self, prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: units per year} a joint by-product is made in, fixed by
        how much of its recipe's dominant output is being made to meet demand."""
        # TEMPORARY HEURISTIC: the dominant output is made to exactly meet its demand.
        supply: Dict[str, float] = collections.defaultdict(float)
        for recipe_key in sorted(self.production):
            entry = self.production[recipe_key]
            outputs = entry.get("outputs") or {}
            if len(outputs) < 2:
                continue
            dominant = demand._dominant_output_key(entry)
            batches = self.demand_for(dominant, prices) / outputs[dominant]
            for material, quantity in outputs.items():
                if material != dominant:
                    supply[material] += batches * quantity
        return dict(supply)

    def clearing_prices(self, prices: Mapping[str, float],
                        supply_by_material: Mapping[str, float],
                        report: Optional[Iterable[str]] = None) -> Dict[str, float]:
        """{material: price at which demand equals its supply}, other prices held.

        Materials nobody demands at all are left out.
        """
        return self.clearing_with_glut(prices, supply_by_material, report)[0]

    def clearing_with_glut(self, prices: Mapping[str, float],
                           supply_by_material: Mapping[str, float],
                           report: Optional[Iterable[str]] = None):
        """(clearing prices, materials in glut): the glut is where the first pass of the search found supply
        above demand at every price down to the span's floor, so no price clears the market."""
        wanted = set(supply_by_material if report is None else report)
        # Only goods sharing a need with a reported good can move its price.
        rival_needs = {need_id for need_id, goods in self._need_goods.items()
                       if wanted & set(goods)}
        rivals = {material for need_id in rival_needs for material in self._need_goods[need_id]}
        targets = []
        for material in sorted(supply_by_material):
            current = prices.get(material)
            if (material in wanted or material in rivals) and supply_by_material[material] \
                    and current and current > 0.0 and self.demand_for(material, prices) > 0.0:
                targets.append(material)
        # Supply-limited goods compete inside a need at their clearing prices,
        # not their costs, so each is re-cleared against the others' latest.
        working = dict(prices)
        clearing: Dict[str, float] = {}
        glutted: Set[str] = set()
        for _pass in range(CLEARING_PASSES):
            for material in targets:
                clearing[material], is_glut = self._clear(
                    material, supply_by_material[material], working, prices[material])
                working[material] = clearing[material]
                # Only the first pass searches the full span below the good's own price.
                if is_glut and _pass == 0:
                    glutted.add(material)
        return ({material: price for material, price in clearing.items() if material in wanted},
                {material for material in glutted if material in wanted})

    def _clear(self, material: str, supply: float, prices: Dict[str, float],
               reference: float):
        """(clearing price, whether supply exceeds demand at every price searched)."""
        current = reference
        weights = self._influence(material)

        technology_weighted = sum(weights.get(source, 0.0) * quantity
                                  for source, quantity in self.technology_demand.items())

        def excess_demand(price: float) -> float:
            price = max(price, sys.float_info.min)
            trial = dict(prices)
            trial[material] = price
            final = self.final_demand(trial)
            own_final = final.get(material, 0.0)
            total = technology_weighted + sum(
                weights.get(source, 0.0) * quantity for source, quantity in final.items())
            derived = total - own_final
            elastic_derived = derived * (price / current) ** (-self.derived_elasticity)
            return own_final + elastic_derived - supply

        centre = prices[material]
        if not centre > 0.0:
            return centre, False
        low = max(centre * 10.0 ** (-CLEARING_SEARCH_SPAN_DECADES), sys.float_info.min)
        high = centre * 10.0 ** CLEARING_SEARCH_SPAN_DECADES
        if excess_demand(high) > 0.0:
            return high, False
        if excess_demand(low) < 0.0:
            return low, True
        for _step in range(CLEARING_BISECTION_STEPS):
            # Geometric midpoint in log space, so tiny prices cannot underflow to zero.
            middle = math.exp((math.log(low) + math.log(high)) / 2.0)
            if excess_demand(middle) > 0.0:
                low = middle
            else:
                high = middle
        return _polish_root(excess_demand, low, high), False


class NeedDemandAnchors:
    """Clearing prices from need-derived demand, for the price solver.

    `prices` gives the anchors joint allocation splits a shared cost by.
    `scarcity_floor_prices` gives a price floor for goods whose limited supply
    is declared with the good; a good whose supply comes from a resource
    table (`table_supply_materials`) already carries deposit rent, so it is
    anchored but not floored.
    """

    def __init__(self, model: NeedDemandModel, supply_by_material: Mapping[str, float],
                 table_supply_materials: Iterable[str] = ()):
        self.model = model
        self.supply_by_material = dict(supply_by_material)
        table = set(table_supply_materials)
        self.table_supply_materials = table
        self.scarcity_materials = sorted(set(self.supply_by_material) - table)
        joint_outputs = {material for entry in model.production.values()
                         if len(entry.get("outputs") or {}) > 1 for material in entry["outputs"]}
        self._last: Dict[Any, Any] = {}
        self._relevant_materials = sorted(
            {material for goods in model.effectiveness.values() for material in goods}
            | set(self.supply_by_material))
        self.anchor_materials = sorted(
            (set(self.supply_by_material) | joint_outputs) | set(self.scarcity_materials))

    def _clearing(self, current_prices: Mapping[str, float], materials: Sequence[str]):
        inputs = [current_prices.get(material, 0.0) for material in self._relevant_materials]
        key = tuple(materials)
        cached = self._last.get(key)
        # Prices that moved less than the solver can see reuse the last answer.
        if cached is not None and all(
                abs(new - old) <= REUSE_RELATIVE_TOLERANCE * abs(old)
                for new, old in zip(inputs, cached[0])):
            return cached[1]
        supply = self.model.byproduct_supply(current_prices)
        supply.update(self.supply_by_material)
        result = self.model.clearing_with_glut(current_prices, supply, report=materials)
        self._last[key] = (inputs, result)
        return result

    def prices(self, current_prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: clearing price} for anchorable goods at this round's prices.

        A good supplied from a resource table whose demand falls short of
        that supply is left unanchored (valued by cost), since the recipe
        graph and final needs do not yet cover every use of such a good.
        """
        # TEMPORARY HEURISTIC: an anchor below the current price is dropped, not used as a glut.
        clearing = self._clearing(current_prices, self.anchor_materials)[0]
        return {material: price for material, price in clearing.items()
                if material not in self.table_supply_materials
                or price >= current_prices[material]}

    def scarcity_floor_prices(self, current_prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: lowest price its limited supply allows}."""
        if not self.scarcity_materials:
            return {}
        return self._clearing(current_prices, self.scarcity_materials)[0]

    def glutted_materials(self, current_prices: Mapping[str, float],
                          disposal_cost_by_material: Optional[Mapping[str, float]] = None) -> Set[str]:
        """Materials nobody pays for: supply exceeds demand at every price the clearing search tried, or the
        market clears below what it costs to dispose of a unit (buyers then take it for less than dumping it
        costs, so it is a waste, not a product).

        The search for a waste is centred at no less than its disposal cost, so a price that has decayed
        towards zero cannot hide a market that clears well above it. A good supplied from a resource table
        is left out: the recipe graph does not yet cover every use of it, so a shortfall of demand there is
        not a glut."""
        costs = {material: cost for material, cost in (disposal_cost_by_material or {}).items()
                 if cost > 0.0 and material in self.anchor_materials}
        centred = dict(current_prices)
        for material, cost in costs.items():
            centred[material] = max(centred.get(material, 0.0), cost)
        clearing, glut = self._clearing(centred, self.anchor_materials)
        glut = set(glut) | {material for material, cost in costs.items()
                            if material in clearing and clearing[material] < cost}
        return {material for material in glut if material not in self.table_supply_materials}
