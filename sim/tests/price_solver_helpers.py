"""Shared construction of a civilization-gated price-solver context."""

import warnings

from sim import simulator
from sim.prices import disposal_cost, solve_prices_core, rent_standin, engine_seam
from sim.prices.joint_allocation import outputs_split_by_mass


def solver_context(civilization_id):
    production_entries, _duplicates = engine_seam.load_production()
    reached = engine_seam.load_civ(civilization_id)["starting_techs"]
    available, _unreached, _unclassified = solve_prices_core.techniques_available_to(
        production_entries, reached)
    _tree, prices_json, _nodes, _wages, _goods = simulator.load()
    wage_by_trade = solve_prices_core.wage_ratios_by_trade(prices_json)
    producers_of = solve_prices_core.build_producers_index(available)
    rent = rent_standin.rent_hours_per_kg_by_ore_material(
        available, wage_by_trade)
    return available, wage_by_trade, producers_of, rent


def engine_solve_converges(civilization_id=None):
    """Whether the engine's own solve converges: with every technique (no civilisation) or with
    the techniques the civilisation starts with."""
    from sim.prices import prices as engine_prices
    _tree, prices_json, _nodes, _wages, _goods = simulator.load()
    held = (engine_seam.load_civ(civilization_id)["starting_techs"] if civilization_id
            else engine_prices.all_gate_nodes())
    return engine_prices.solved_prices(held, prices_json, civilization_id=civilization_id).converged


def minor_joint_byproducts_split_by_mass(production_entries, chosen_recipe_by_material,
                                         prices, wage_by_trade, share_threshold=0.5,
                                         rent_hours_per_kg_by_material=None, interest_rate=0.0,
                                         reference_price_by_material=None):
    """{material: value_share} for every material whose CONVERGED, CHOSEN
    recipe is a joint-production recipe in which this material holds under
    `share_threshold` of the batch's value and was split by mass.

    A joint output is valued at a reference price when the caller gave one or when a sole-output route
    makes it (what making it alone costs); a recorded waste with neither is worth nothing; any other is
    valued by mass (the labelled fallback of sim/prices/joint_allocation.py). Those prices are a real lower bound on cost, not a real relative
    price, and every caller that prints one must be able to say so next to it.
    """
    direct = {material for entry in production_entries.values()
              if len(entry.get("outputs") or {}) == 1 for material in entry["outputs"]}
    references = set(reference_price_by_material or ()) | direct
    flagged = {}
    for material, recipe_id in chosen_recipe_by_material.items():
        entry = production_entries[recipe_id]
        outputs = entry.get("outputs") or {}
        if material not in outputs_split_by_mass(outputs, references, disposal_cost.waste_materials()):
            continue
        result = solve_prices_core.recipe_cost_and_allocation(
            recipe_id, entry, prices, wage_by_trade,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material, interest_rate=interest_rate)
        if result is None:
            continue
        total_process_cost, _output_prices = result
        if total_process_cost <= 0:
            continue
        value_share = (outputs[material] * prices[material]) / total_process_cost
        if value_share < share_threshold:
            flagged[material] = value_share
    if flagged:
        warnings.warn("joint byproducts priced by mass, with no reference price: %s"
                      % ", ".join(sorted(flagged)))
    return flagged
