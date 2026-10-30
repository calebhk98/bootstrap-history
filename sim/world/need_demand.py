"""Demand from what goods do, not from a list of goods.

Households spend on needs (food, shelter, health, ...). A good declares which
needs it satisfies and how well per unit. Inside a need, goods compete on
effectiveness per unit cost. Everything a wanted good consumes is demanded in
turn through the recipes that make it.

Needs and goods come from data/world/needs.json and mods (see
sim/content/need_data.py); recipes from data/production/. This module takes
them as arguments.
"""
import collections
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from sim.constants import declare
from sim.world import demand, need_basket, need_final_demand
from sim.world.need_basket import NEED_SUBSTITUTION_ELASTICITY, goods_attributes

def load_needs(root: str) -> Dict[str, Any]:
    """The base-and-enabled-mod needs and goods under `root` (sim/content/need_data.py)."""
    from sim.content.api import load_needs
    return load_needs(root)


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


def budget_weights_by_good(need_data: Mapping[str, Any], production: Mapping[str, Any],
                           available_materials: Set[str],
                           cost_per_unit: Optional[Mapping[str, float]] = None,
                           civ_values: Optional[Mapping[str, Any]] = None) -> Dict[str, float]:
    """{good: share of household spending} with no prices: each need's budget weight, normalised over
    needs an available good serves, split among those goods. `cost_per_unit` is what a unit of a good costs
    in any one currency (labour value when prices are unknown); the goods of a need then take spending as
    the household mix does (constant elasticity on cost per need unit, sim/world/need_basket.py). A good
    without a positive cost takes the mean weight of its need's priced goods; with no costs at all the
    split inside a need is equal. A need that scales with a civilisation field (`civ_values`) weighs by it."""
    attributes = goods_attributes(need_data, production)
    servers: Dict[str, List[str]] = collections.defaultdict(list)
    for material in sorted(available_materials):
        for need_id in attributes.get(material, {}).get("satisfies", {}):
            servers[need_id].append(material)
    civ_values = civ_values or {}
    need_weight = {need_id: need_data["needs"][need_id]["surplus_budget_share"]
                   * need_basket.civ_scale(need_data["needs"][need_id], civ_values) for need_id in servers}
    weight_total = sum(need_weight.values())
    weights: Dict[str, float] = collections.defaultdict(float)
    for need_id, materials in servers.items():
        share = need_weight[need_id] / weight_total if weight_total > 0.0 else 0.0
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


class NeedDemandModel:
    """Household final demand by need, plus the demand recipes derive from it."""

    def __init__(self, need_data: Mapping[str, Any], production: Mapping[str, Any],
                 bins: Sequence[Any], substitution_elasticity: Optional[float] = None,
                 satiate: bool = False):
        # `satiate` limits a need that declares a per-head limit to it; the quantities households
        # actually buy turn it on.
        self.satiate = satiate
        self.needs = dict(need_data["needs"])
        self.production = production
        self.bins = list(bins)
        self.substitution = (NEED_SUBSTITUTION_ELASTICITY if substitution_elasticity is None
                             else substitution_elasticity)
        self.basket = need_basket.make_basket(need_data, production, self.substitution)
        self.subsistence = {need.need_id: need.subsistence_per_person for need in self.basket.needs}
        self._input_per_unit_output = self._recipe_coefficients()

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
        return need_final_demand.quantities_from_priced(
            self, need_basket.need_prices(self.basket, prices.get))

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

    def total_demand(self, prices: Mapping[str, float]) -> Dict[str, float]:
        """{material: units demanded per year}: households and the recipes that supply them."""
        return self._demand_from(self.final_demand(prices))
