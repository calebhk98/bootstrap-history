"""Shared construction of a civilization-gated price-solver context."""

from sim import simulator, solve_prices


def solver_context(civilization_id):
    production_entries, _duplicates = solve_prices.load_production()
    reached = solve_prices.load_starting_technologies(civilization_id)
    available, _unreached, _unclassified = solve_prices.techniques_available_to(
        production_entries, reached)
    _tree, prices_json, _nodes, _wages, _goods = simulator.load()
    wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
    producers_of = solve_prices.build_producers_index(available)
    rent = solve_prices.rent_hours_per_kg_by_ore_material(
        available, wage_by_trade)
    return available, wage_by_trade, producers_of, rent
