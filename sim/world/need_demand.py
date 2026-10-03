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
from sim.world import demand
from sim.world.need_satiation import apply_satiation

def load_needs(root: str) -> Dict[str, Any]:
    """The base-and-enabled-mod needs and goods under `root` (sim/engine/need_data.py)."""
    from sim.engine import need_data
    return need_data.load_needs(root)


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


def declared_supply(need_data: Mapping[str, Any],
                    production: Mapping[str, Any]) -> Dict[str, float]:
    """{material: annual supply in its own unit} for goods that declare one."""
    return {material: attributes["supply_per_year"]
            for material, attributes in goods_attributes(need_data, production).items()
            if attributes.get("supply_per_year")}


def budget_weights_by_good(need_data: Mapping[str, Any], production: Mapping[str, Any],
                           available_materials: Set[str]) -> Dict[str, float]:
    """{good: share of household spending} with no prices: each need's budget
    weight, normalised over needs an available good serves, split equally
    among those goods."""
    # TEMPORARY HEURISTIC: equal split inside a need, since no prices are known here.
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
        for material in materials:
            weights[material] += share / len(materials)
    return dict(weights)


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
        self.subsistence = {need_id: self._subsistence(spec)
                            for need_id, spec in self.needs.items()}
        self._input_per_unit_output = self._recipe_coefficients()
        self._influence_cache: Dict[str, Dict[str, float]] = {}

    @staticmethod
    def _subsistence(spec: Mapping[str, Any]) -> float:
        if spec.get("subsistence_constant"):
            return float(getattr(demand, spec["subsistence_constant"]))
        return float(spec.get("subsistence_per_capita_per_year", 0.0))

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

    def _active_needs(self, prices: Mapping[str, float]) -> Dict[str, List[str]]:
        """{need: its priced goods} for needs with at least one."""
        active = {}
        for need_id, goods in self._need_goods.items():
            priced = [material for material in goods if prices.get(material, 0.0) > 0.0]
            if priced:
                active[need_id] = priced
        return active

    def final_demand(self, prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: units households want per year} at `prices`."""
        active = self._active_needs(prices)
        if not active:
            return {}
        exponent = 1.0 - self.substitution
        weight_total = sum(self.needs[need_id]["surplus_budget_share"] for need_id in active)
        cost_per_effect: Dict[str, Dict[str, float]] = {}
        price_index: Dict[str, float] = {}
        for need_id, materials in active.items():
            costs = {material: prices[material] / self.effectiveness[need_id][material]
                     for material in materials}
            cost_per_effect[need_id] = costs
            index_power = sum(cost ** exponent for cost in costs.values())
            price_index[need_id] = index_power ** (1.0 / exponent)
        basket = tuple(
            demand.Good(need_id, self.subsistence[need_id],
                        self.needs[need_id]["surplus_budget_share"] / weight_total)
            for need_id in active)
        need_units = {need_id: 0.0 for need_id in active}
        committed = sum(price_index[good.name] * good.subsistence_quantity_per_capita_per_year
                        for good in basket)
        covered_population = 0.0
        covered_surplus = 0.0
        for income_bin in self.bins:
            surplus = income_bin.income_per_capita_per_year - committed
            if surplus >= 0.0:
                covered_population += income_bin.population
                covered_surplus += income_bin.population * surplus
                continue
            for good in basket:
                need_units[good.name] += (
                    income_bin.population * demand.household_quantity_demanded_per_capita(
                        good, price_index, income_bin.income_per_capita_per_year, basket))
        for good in basket:
            need_units[good.name] += (
                good.subsistence_quantity_per_capita_per_year * covered_population
                + good.marginal_budget_share / price_index[good.name] * covered_surplus)
        if self.satiate:
            apply_satiation(need_units, price_index, self.needs,
                            sum(income_bin.population for income_bin in self.bins))
        quantities: Dict[str, float] = collections.defaultdict(float)
        for need_id, materials in active.items():
            spending = price_index[need_id] * need_units[need_id]
            index_power = price_index[need_id] ** exponent
            for material in materials:
                share = cost_per_effect[need_id][material] ** exponent / index_power
                quantities[material] += spending * share / prices[material]
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
        for _pass in range(CLEARING_PASSES):
            for material in targets:
                clearing[material] = self._clear(
                    material, supply_by_material[material], working, prices[material])
                working[material] = clearing[material]
        return {material: price for material, price in clearing.items() if material in wanted}

    def _clear(self, material: str, supply: float, prices: Dict[str, float],
               reference: float) -> float:
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
            return centre
        low = max(centre * 10.0 ** (-CLEARING_SEARCH_SPAN_DECADES), sys.float_info.min)
        high = centre * 10.0 ** CLEARING_SEARCH_SPAN_DECADES
        if excess_demand(high) > 0.0:
            return high
        if excess_demand(low) < 0.0:
            return low
        for _step in range(CLEARING_BISECTION_STEPS):
            # Geometric midpoint in log space, so tiny prices cannot underflow to zero.
            middle = math.exp((math.log(low) + math.log(high)) / 2.0)
            if excess_demand(middle) > 0.0:
                low = middle
            else:
                high = middle
        return _polish_root(excess_demand, low, high)


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
        result = self.model.clearing_prices(current_prices, supply, report=materials)
        self._last[key] = (inputs, result)
        return result

    def prices(self, current_prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: clearing price} for anchorable goods at this round's prices.

        A good supplied from a resource table whose demand falls short of
        that supply is left unanchored (valued by cost), since the recipe
        graph and final needs do not yet cover every use of such a good.
        """
        # TEMPORARY HEURISTIC: an anchor below the current price is dropped, not used as a glut.
        clearing = self._clearing(current_prices, self.anchor_materials)
        return {material: price for material, price in clearing.items()
                if material not in self.table_supply_materials
                or price >= current_prices[material]}

    def scarcity_floor_prices(self, current_prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: lowest price its limited supply allows}."""
        if not self.scarcity_materials:
            return {}
        return self._clearing(current_prices, self.scarcity_materials)
