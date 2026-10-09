"""Splits one joint process's cost across its outputs using demand.

A joint recipe (one smelt, several products) has one cost and several
prices, so cost alone cannot separate them. Outputs with a demand anchor
(a market-clearing price from `sim/world/demand.py`) take a share of the
cost proportional to anchor price times quantity. Outputs without one are
valued at the batch's standalone unit cost, which does not depend on any
solved output price, so the split cannot feed back into itself.
"""
import json
import os
import warnings

from sim.constants import declare
from sim.engine.default_civilisation import default_civilisation_id
from sim.engine.joint_floor import bound_to_disposal_cost, is_glutted
from sim.world import demand, deposits

DEFAULT_CIVILIZATION = default_civilisation_id()
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR = declare(
    "MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR", 550.0,
    kind="temporary_heuristic",
    unit="labour-hours/person/year",
    source=None,
    confidence="D",
    why="Household income scale for the demand anchors: hours worked per "
        "worker-year times a working share of the whole population. Should "
        "come from the labour market once it is wired; until then it is one "
        "number for every civilisation.")


def allocate_joint_cost(outputs, current_prices, total_cost,
                        anchor_price_by_material=None,
                        disposal_value_by_material=None,
                        disposal_cost_by_material=None):
    """{material: price per unit} splitting `total_cost` over `outputs`.

    Outputs only have to recover the batch together; a bulk waste may carry
    far less than its mass share. Without an anchor an output is valued by
    its mass in kg. An output whose unit is not a mass is warned about,
    left out of the split and priced at zero.

    An anchored output whose demand-clearing price is at or below its
    disposal value (default zero) is in surplus: it prices at the disposal
    value and the other outputs carry the rest of the batch.

    An anchored output in glut (its demand clears at next to nothing) prices at minus its disposal cost
    per unit, `disposal_cost_by_material`, and the other outputs carry the batch plus that cost.
    No output is priced below minus its disposal cost.
    """
    if len(outputs) == 1:
        (name, quantity), = outputs.items()
        return {name: total_cost / quantity}
    anchors = anchor_price_by_material or {}
    disposal = disposal_value_by_material or {}
    disposal_costs = disposal_cost_by_material or {}
    surplus = {name: disposal.get(name, 0.0) for name in outputs
               if name in anchors and anchors[name] <= disposal.get(name, 0.0)}
    surplus.update({name: -disposal_costs[name] for name in outputs
                    if name not in surplus and name in anchors and name in disposal_costs
                    and is_glutted(anchors[name], disposal_costs[name])})
    if surplus and len(surplus) < len(outputs):
        # Disposal revenue cannot exceed the batch, so the rest never goes negative; a disposal cost
        # (negative value) is added to what the rest carry.
        surplus_total = sum(outputs[name] * value for name, value in surplus.items())
        surplus_revenue = min(total_cost, surplus_total)
        scale = surplus_revenue / (surplus_total or 1.0)
        prices = {name: value * scale for name, value in surplus.items()}
        remaining = {name: quantity for name, quantity in outputs.items()
                     if name not in surplus}
        prices.update(allocate_joint_cost(
            remaining, current_prices, total_cost - surplus_revenue,
            {name: price for name, price in anchors.items() if name in remaining},
            disposal_cost_by_material={name: cost for name, cost in disposal_costs.items()
                                       if name in remaining}))
        return prices
    mass = {name: demand.mass_in_kg_or_none(name, quantity)
            for name, quantity in outputs.items()}
    unconvertible = sorted(name for name, kilograms in mass.items() if kilograms is None)
    if unconvertible:
        warnings.warn("joint outputs with no mass unit are left out of the cost split: %s"
                      % ", ".join(unconvertible))
    split_outputs = {name: quantity for name, quantity in outputs.items()
                     if mass[name] is not None}
    prices = dict.fromkeys(unconvertible, 0.0)
    if not split_outputs:
        return prices
    anchored = {name for name in split_outputs if name in anchors}
    kilograms_per_unit = {name: mass[name] / quantity for name, quantity in split_outputs.items()}
    # TEMPORARY HEURISTIC: an unanchored output is valued at the batch's
    # standalone cost per kg, which does not depend on any solved output price.
    standalone_cost_per_kg = total_cost / (sum(mass[name] for name in split_outputs) or 1.0)
    reference_prices = {
        name: anchors[name] if name in anchored
        else standalone_cost_per_kg * kilograms_per_unit[name]
        for name in split_outputs}
    split = _split_by_value(split_outputs, reference_prices, total_cost)
    prices.update(bound_to_disposal_cost(split, split_outputs, disposal_costs))
    return prices


def cap_anchors(anchor_price_by_material, direct_price_by_material):
    """Anchors, each held at or below the cheapest sole-output route's price.

    A joint recipe cannot value a byproduct above what making it directly
    costs. Sole-output routes never depend on an anchor, so the cap cannot
    feed back into the price it is capped by.
    """
    if anchor_price_by_material is None:
        return None
    return {name: min(price, direct_price_by_material.get(name, price))
            for name, price in anchor_price_by_material.items()}


def _split_by_value(outputs, reference_prices, total_cost):
    values = {name: quantity * max(reference_prices.get(name, 1.0), 0.0)
              for name, quantity in outputs.items()}
    total_value = sum(values.values())
    if total_value <= 0:
        # Nothing has a value yet; split by quantity until prices exist.
        values = dict(outputs)
        total_value = sum(values.values())
    return {name: total_cost * values[name] / total_value / quantity
            for name, quantity in outputs.items()}


def _annual_supply(material, resources):
    """Annual supply in the material's own unit, from the first table naming it."""
    for table in resources:
        output = table.get(material.rsplit("_", 1)[0])
        if output:
            kilograms = output["t_per_yr"] * 1000.0
            per_unit = demand.mass_in_kg_or_none(material, 1.0)
            return kilograms / per_unit if per_unit else None
    return None


def _civilisation(civilization_id):
    path = os.path.join(_ROOT, "data", "civilizations", "%s.json" % civilization_id)
    if not civilization_id or not os.path.exists(path):
        path = os.path.join(
            _ROOT, "data", "civilizations", "%s.json" % DEFAULT_CIVILIZATION)
    with open(path) as handle:
        return json.load(handle)


def build_demand_anchors(civilization_id=None, supply_by_material=None, civilization=None):
    """NeedDemandAnchors for a civilisation, or None when nothing is anchorable.

    Demand comes from the needs data (data/world/needs.json and mods), the
    recipe graph, and the technologies the civilisation could pursue next.
    Supply, in each good's own unit, comes from a good's declared
    `supply_per_year`, else from the resource tables.
    """
    from sim.engine import catalog, need_data
    from sim.world import need_demand
    production = demand.production_data()
    needs = need_data.load_needs(_ROOT)
    declared = need_demand.declared_supply(needs, production)
    if supply_by_material is None:
        with open(deposits.RESOURCES_FILE) as handle:
            resources = json.load(handle)
        tables = [resources["empire_output_100ad"],
                  resources.get("placer_metal_output_reference", {})]
        outputs = {material for entry in production.values() for material in entry["outputs"]}
        supply_by_material = {}
        for material in sorted(outputs):
            supply = _annual_supply(material, tables)
            if supply:
                supply_by_material[material] = supply
    table_supply = set(supply_by_material) - set(declared)
    supply_by_material = dict(supply_by_material, **declared)
    if not supply_by_material:
        return None
    civilisation = civilization if civilization is not None else _civilisation(civilization_id)
    bins = demand.income_bins(
        float(civilisation["population"]), MEAN_INCOME_LABOUR_HOURS_PER_CAPITA_PER_YEAR)
    technology_demand = need_demand.technology_material_demand(
        catalog.load_mod_tree_nodes(_ROOT), set(civilisation.get("starting_techs") or ()))
    model = need_demand.NeedDemandModel(needs, production, bins, technology_demand)
    return need_demand.NeedDemandAnchors(model, supply_by_material, table_supply)
