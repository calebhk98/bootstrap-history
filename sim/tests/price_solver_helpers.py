"""Shared construction of a civilization-gated price-solver context."""

from sim import simulator
from sim.prices import solve_prices_core, rent_standin, engine_seam


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
