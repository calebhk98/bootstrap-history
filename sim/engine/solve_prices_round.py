"""One round of the price solve, with everything that does not change between rounds worked out once.

`recipe_cost_and_allocation` re-reads a recipe's static fields on every call. A solve costs the same recipes
every round against new prices, so `RecipePlan` holds what depends only on the recipe (labour bill, rent,
capital charge per build, output quantities, capability floor test) and `plan_cost` does the same arithmetic
in the same order using only the price lookups that move. The results are identical to
`recipe_cost_and_allocation` called with the round's disposal costs.
"""
import collections

from sim.engine import solve_prices_core as core
from sim.world.capital_market import stand_yearly_share


class RecipePlan:
    """The round-independent part of costing one recipe."""
    __slots__ = ("recipe_id", "entry", "inputs", "outputs", "single_output", "single_quantity",
                 "batch_output_quantity", "labour_cost_hours", "rent_hours", "land_hectare_years",
                 "capital_goods", "energy", "holding_years", "output_meets_floor")

    def __init__(self, recipe_id, entry, wage_by_trade, rent_by_kg, interest_rate, floor_by_carrier):
        self.recipe_id = recipe_id
        self.entry = entry
        self.inputs = tuple((entry.get("inputs") or {}).items())
        outputs = entry.get("outputs") or {}
        self.outputs = outputs
        self.single_output = next(iter(outputs)) if len(outputs) == 1 else None
        self.single_quantity = outputs[self.single_output] if len(outputs) == 1 else None
        self.batch_output_quantity = max(outputs.values()) if outputs else 1.0
        self.labour_cost_hours = core._labour_cost_hours(entry.get("labour_hours") or {}, wage_by_trade)
        self.rent_hours = core._extraction_rent_cost_hours(outputs, rent_by_kg)
        self.land_hectare_years = entry.get("land_hectare_years") or 0.0
        self.capital_goods = tuple(
            (tuple((capital_good.get("build_materials") or {}).items()),
             tuple(hours * wage_by_trade[trade]
                   for trade, hours in (capital_good.get("build_labour_hours") or {}).items()),
             stand_yearly_share(
                interest_rate, capital_good["service_life_years"], capital_good.get("establishment_years") or 0.0),
             capital_good["annual_output_at_basis"])
            for capital_good in (entry.get("capital") or []))
        self.energy = tuple(
            (energy_key, entry.get(energy_key)) for energy_key in core.ENERGY_CARRIER_FIELDS
            if entry.get(energy_key) or 0.0)
        self.holding_years = float(entry.get("holding_years") or 0.0)
        self.output_meets_floor = {
            material: core._meets_capability_floor(material, entry, floor_by_carrier) for material in outputs}


def plan_cost(plan, prices, wage_by_trade, band_price_by_carrier, interest_rate, disposal_costs,
              reference_price_by_material=None):
    """(total_process_cost_hours, {output: price}) or None, as `recipe_cost_and_allocation` with the round's
    disposal costs."""
    waste_input_costs = disposal_costs
    material_cost_hours = 0.0
    for input_material, quantity_per_batch in plan.inputs:
        input_price = prices.get(input_material)
        if input_price is None:
            return None
        if input_price < 0.0:
            input_price = max(input_price, -(waste_input_costs or {}).get(input_material, 0.0))
        material_cost_hours += quantity_per_batch * input_price

    if plan.land_hectare_years:
        land_price = prices.get("hectare_land")
        if land_price is None:
            return None
        land_cost_hours = plan.land_hectare_years * land_price
    else:
        land_cost_hours = 0.0

    capital_cost_hours = 0.0
    for build_materials, build_labour_costs, yearly_share, annual_output in plan.capital_goods:
        build_cost_hours = 0.0
        for build_material, quantity_per_build in build_materials:
            build_material_price = prices.get(build_material)
            if build_material_price is None:
                return None
            build_cost_hours += quantity_per_build * build_material_price
        for labour_cost in build_labour_costs:
            build_cost_hours += labour_cost
        capital_cost_hours += build_cost_hours * yearly_share / annual_output

    energy_cost_hours = 0.0
    for energy_key, energy_quantity_per_batch in plan.energy:
        energy_price = core._capability_graded_price(
            energy_key, plan.entry, prices, band_price_by_carrier)
        if energy_price is None:
            return None
        energy_cost_hours += energy_quantity_per_batch * energy_price

    inventory_cost_hours = material_cost_hours * interest_rate * plan.holding_years
    total_process_cost_hours = max(
        0.0, material_cost_hours + plan.labour_cost_hours + plan.rent_hours + land_cost_hours
        + capital_cost_hours * plan.batch_output_quantity + energy_cost_hours + inventory_cost_hours)

    if plan.single_output is not None:
        return total_process_cost_hours, {plan.single_output: total_process_cost_hours / plan.single_quantity}
    output_prices = core._allocate_output_prices(
        plan.outputs, prices, total_process_cost_hours, reference_price_by_material, interest_rate,
        disposal_costs)
    return total_process_cost_hours, output_prices


def build_plans(production_entries, recipe_ids_in_order, resolvable_materials, wage_by_trade,
                rent_by_kg, interest_rate, floor_by_carrier):
    """RecipePlans, in solve order, for every recipe whose outputs are all resolvable."""
    return [RecipePlan(recipe_id, production_entries[recipe_id], wage_by_trade, rent_by_kg,
                       interest_rate, floor_by_carrier)
            for recipe_id in recipe_ids_in_order
            if (production_entries[recipe_id].get("outputs") or {})
            and all(material in resolvable_materials for material in production_entries[recipe_id]["outputs"])]


def round_candidates(plans, prices, wage_by_trade, band_price_by_carrier, interest_rate, disposal_costs,
                     reference_price_by_material=None):
    """{material: [(price, recipe_id)]} for this round: sole-output recipes first, whose cheapest price per
    material is what a joint recipe's output is worth when made alone, and so its reference price for the
    split unless the caller gave one."""
    result_by_recipe = {}
    direct_price_by_material = {}
    for plan in plans:
        if plan.single_output is None:
            continue
        result = plan_cost(plan, prices, wage_by_trade, band_price_by_carrier, interest_rate, disposal_costs)
        result_by_recipe[plan.recipe_id] = result
        if result is None:
            continue
        for material, price in result[1].items():
            if plan.output_meets_floor[material]:
                direct_price_by_material[material] = min(
                    price, direct_price_by_material.get(material, price))
    references = dict(direct_price_by_material, **(reference_price_by_material or {}))
    for plan in plans:
        if plan.recipe_id not in result_by_recipe:
            result_by_recipe[plan.recipe_id] = plan_cost(
                plan, prices, wage_by_trade, band_price_by_carrier, interest_rate, disposal_costs, references)

    candidates_by_material = collections.defaultdict(list)
    for plan in plans:
        result = result_by_recipe[plan.recipe_id]
        if result is None:
            continue
        for material, price in result[1].items():
            if plan.output_meets_floor[material]:
                candidates_by_material[material].append((price, plan.recipe_id))
    return candidates_by_material


def band_suppliers(required_grades_by_carrier, production_entries):
    """{carrier: [(recipe_id, entry, reached_value)]} for the recipes that output each graded carrier."""
    suppliers = {}
    for carrier in required_grades_by_carrier:
        reached_field = core.CAPABILITY_CAP_FIELDS[carrier][0]
        suppliers[carrier] = [
            (recipe_id, entry, entry.get(reached_field)) for recipe_id, entry in production_entries.items()
            if carrier in (entry.get("outputs") or {})]
    return suppliers


def band_prices(required_grades_by_carrier, suppliers_by_carrier, prices, wage_by_trade,
                rent_hours_per_kg_by_material, interest_rate):
    """{carrier: {required_value: (price, recipe_id) or None}}: as `capability_price_for_requirement` for each
    required value, costing each supplying recipe once per round however many requirements it can clear."""
    bands = {}
    for carrier, required_values in required_grades_by_carrier.items():
        price_by_recipe = {}
        band = {}
        for required_value in required_values:
            best = None
            for recipe_id, entry, reached in suppliers_by_carrier[carrier]:
                if reached is not None and reached < required_value:
                    continue
                if recipe_id not in price_by_recipe:
                    result = core.recipe_cost_and_allocation(
                        recipe_id, entry, prices, wage_by_trade,
                        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
                        interest_rate=interest_rate)
                    price_by_recipe[recipe_id] = None if result is None else result[1][carrier]
                price = price_by_recipe[recipe_id]
                if price is None:
                    continue
                if best is None or price < best[0]:
                    best = (price, recipe_id)
            band[required_value] = best
        bands[carrier] = band
    return bands
