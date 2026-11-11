"""The price solver as it was before the undamped opening rounds: damped Jacobi from the first round, kept as plain
reference code so a test can set the solver's answer against it."""
import math

from sim.prices import disposal_cost
from sim.prices import solve_prices_core as core
from sim.prices.price_change import relative_price_change


def reference_round_update_prices(resolvable_materials, prices, candidates_by_material,
                               damping, chosen_recipe_by_material,
                               disposal_floor=None):
    new_prices = {}
    max_relative_change = 0.0
    disposal_costs_floor = disposal_floor or {}
    for material in resolvable_materials:
        candidates = candidates_by_material.get(material)
        if not candidates:
            new_prices[material] = prices[material]
            continue
        # A candidate cannot go below minus the material's disposal cost; bound before choosing.
        lowest = disposal_costs_floor.get(material, -math.inf)
        best_price, best_recipe = None, None
        for price, recipe in candidates:
            bounded_price = max(price, lowest)
            if best_price is None or bounded_price < best_price:
                best_price, best_recipe = bounded_price, recipe
        chosen_recipe_by_material[material] = best_recipe
        damped_price = (1.0 - damping) * prices[material] + damping * best_price
        new_prices[material] = damped_price
        max_relative_change = max(
            max_relative_change, relative_price_change(prices[material], damped_price))
    return new_prices, max_relative_change


def reference_solve(production_entries, producers_of, resolvable_materials, wage_by_trade,
         damping=core.DAMPING_FACTOR, max_iterations=core.MAXIMUM_ITERATIONS,
         tolerance=core.CONVERGENCE_TOLERANCE, rent_hours_per_kg_by_material=None,
         reference_price_by_material=None, interest_rate=0.0, dump_minimum_distance_kilometres=0.0,
         initial_prices=None):
    # A caller may start the iteration from the prices of a nearby solve; a material it lacks starts at the guess.
    start = initial_prices or {}
    prices = {material: start.get(material, core.INITIAL_PRICE_GUESS_HOURS) for material in resolvable_materials}
    chosen_recipe_by_material = {}
    recipe_ids_in_order = sorted(production_entries)  # stable order; see above
    floor_by_carrier = core.capability_floor_by_carrier()
    required_grades_by_carrier = core.capability_required_grades(production_entries)

    final_residual = float("inf")
    iterations_run = 0
    joint_materials = disposal_cost.joint_output_materials(production_entries)
    from sim.prices import solve_prices_round  # imports this module, so only once it is loaded
    plans = solve_prices_round.build_plans(
        production_entries, recipe_ids_in_order, resolvable_materials, wage_by_trade,
        rent_hours_per_kg_by_material or {}, interest_rate, floor_by_carrier)
    suppliers_by_carrier = solve_prices_round.band_suppliers(required_grades_by_carrier, production_entries)
    for iteration in range(1, max_iterations + 1):
        iterations_run = iteration

        band_price_by_carrier = solve_prices_round.band_prices(
            required_grades_by_carrier, suppliers_by_carrier, prices, wage_by_trade,
            rent_hours_per_kg_by_material, interest_rate, dump_minimum_distance_kilometres)

        # What waste costs to dispose of this round: no output is priced below minus it.
        disposal_costs = disposal_cost.disposal_cost_by_material(
            joint_materials, prices, interest_rate, dump_minimum_distance_kilometres)

        candidates_by_material = solve_prices_round.round_candidates(
            plans, prices, wage_by_trade, band_price_by_carrier, interest_rate, disposal_costs,
            reference_price_by_material)

        prices, final_residual = reference_round_update_prices(
            resolvable_materials, prices, candidates_by_material, damping, chosen_recipe_by_material,
            {material: -cost for material, cost in disposal_costs.items()})
        if final_residual < tolerance:
            break

    return prices, iterations_run, final_residual, chosen_recipe_by_material
