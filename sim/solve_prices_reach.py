"""Solving to a price vector in which every material has a technique that makes it (Complaints/420)."""


def solve_priced_materials(production_entries, producers_of, resolvable_materials, wage_by_trade, **solve_arguments):
    """(prices, iterations_run, residual, chosen_recipe_by_material, resolvable_materials).

    A material no technique in the solve can cost (a heat nothing reaches) would keep the solver's
    starting guess as its price, and so would everything priced through it. Such a material has no
    price: it leaves the resolvable set and the solve repeats until every remaining material is made."""
    from sim import solve_prices  # through the module, so a caller that wraps the solver sees every solve
    resolvable_materials = set(resolvable_materials)
    while True:
        prices, iterations_run, residual, chosen = solve_prices.solve(
            production_entries, producers_of, resolvable_materials, wage_by_trade, **solve_arguments)
        unmade = resolvable_materials - set(chosen)
        if not unmade:
            return prices, iterations_run, residual, chosen, resolvable_materials
        resolvable_materials -= unmade
