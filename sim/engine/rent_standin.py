"""The rent the opening carries until the economy supplies its own (Complaints/507).

The cost calculator charges rent it is handed (`rent_hours_per_kg_by_material`: hours per unit of an extracted
good, and per hectare of land). This module is the stand-in a caller uses when it has none, and only then.
Both rents are Ricardian margins that need a quantity demanded; the stand-in fixes that quantity from the
opening's own physical figures and no price, which is why it is a temporary heuristic: the economy's land
rent per hectare and a mine's own marginal cost replace it (ONE_PRICE_OWNER_PLAN.md stage 5).
"""
import json

from sim.constants import declare
from sim.engine.default_civilisation import default_civilisation_id
from sim.engine.solve_prices_core import recipe_cost_and_allocation
from sim.world import deposits
from sim.world import land

STAND_IN_ORE_DEMAND_SHARE_OF_OPENING_OUTPUT = declare(
    "STAND_IN_ORE_DEMAND_SHARE_OF_OPENING_OUTPUT", 1.0, kind="temporary_heuristic",
    unit="share of the opening's recorded yearly output of a metal",
    source=None, confidence="D", retire="Complaints/507 stage 5: ore rent is the mine's own marginal cost",
    why="Ore rent needs a quantity demanded to find the marginal deposit. The stand-in takes the opening's "
        "recorded output of the metal, whatever the price, so rent does not answer the price the solver "
        "computes. The land stand-in (`land_rent_hours_per_hectare`) is sized the same way, to the "
        "population's grain or the farmed area, and is retired with it.")

# The ore-to-metal links come from the catalogue (deposits.rent_bearing_ore_materials). Where an ore has several
# smelting recipes (iron: blast furnace, bloomery) the first one present in this solve's gated entries is the
# dominant one, so a gated era falls back to a recipe it can run.


def rent_hours_per_kg_by_ore_material(production_entries, wage_by_trade):
    """{ore_material_key: hours of rent per kg of that ore's own output},
    for every ore the catalogue's `ore_goods` names whose ore and dominant
    smelting recipe both survive this era's gate - see RENT ON EXTRACTED
    MATERIALS in the `solve_prices` module docstring for the mechanism this implements and
    why it is only approximate for a metal with more than one ore-consuming
    recipe.

    THE ALGEBRA. `sim/world/deposits.py`'s `find_marginal_deposit` gives
    `price_at_margin_labour_hours_per_kg` - the Ricardian, rent-inclusive
    price of one kilogram of CONTAINED METAL, at the fixed quantity demanded
    this function reads from `data/world/resources.json`'s own
    `empire_output_100ad` (see the `solve_prices` module docstring's own TEMPORARY
    HEURISTIC paragraph on why that quantity is fixed rather than derived
    from price). Call that `metal_price`.

    The dominant recipe's own `inputs[ore] / outputs[metal]` ratio
    (`ore_per_metal`, kg of ore per kg of metal) is what turns a kilogram of
    metal into a kilogram of ore in `data/production/`'s own accounting.
    The ore's own recipe carries no inputs, so its RENT-FREE price
    (`ore_base_price`, labour only) is fixed and does not depend on the
    solve's iteration at all - this function is therefore called once,
    before the iteration starts, not once per round.

    Setting `existing_extraction_proxy = ore_base_price * ore_per_metal`
    (what the dominant recipe already implies a kilogram of metal's
    extraction costs, with no rent), the rent this function attributes to
    the metal is `max(0, metal_price - existing_extraction_proxy)` - the
    Ricardian gap between the marginal deposit's true price and what the
    zero-rent recipe already charges - and dividing that back by
    `ore_per_metal` gives `rent_per_kg_ore`, the number this function
    returns for that ore. Added onto `ore_base_price` inside
    `recipe_cost_and_allocation` and multiplied back through the dominant
    recipe's own `ore_per_metal`, it reproduces `metal_price` on that
    recipe's output EXACTLY (the division and the later multiplication use
    the same ratio); every OTHER recipe that consumes the same ore at a
    DIFFERENT ratio gets an approximation instead, by design - see the
    `solve_prices` module docstring.

    A metal whose marginal deposit is cheap enough that the existing
    zero-rent recipe already prices above it (which can happen: the two
    numbers come from unrelated sources, `data/production/`'s own generic
    grade assumption and `sim/world/deposits.py`'s specific named
    deposits) gets exactly 0.0 rent here, not a negative one - rent is a
    surplus over cost of production, never a discount below it.
    """
    with open(deposits.RESOURCES_FILE) as handle:
        resources_json = json.load(handle)

    rent_by_ore_material = {}
    for ore_material, (metal, candidate_recipe_ids) in deposits.rent_bearing_ore_materials().items():
        ore_entry = production_entries.get(ore_material)
        if ore_entry is None:
            # Gated out of this era (--civ), or (should not happen for a
            # base material the tree already validates) simply absent -
            # either way there is nothing to attach a rent to, so this ore
            # keeps the RENT_IS_ZERO default rather than a guess.
            continue
        dominant_entry = next(
            (production_entries[recipe_id] for recipe_id in candidate_recipe_ids
             if recipe_id in production_entries),
            None)
        if dominant_entry is None:
            # Every candidate recipe is gated out of this era too - iron
            # under an ungated future-tech solve missing BOTH blast furnace
            # and bloomery would land here, which should not happen for
            # this project's own civilizations but is handled the same way
            # as any other missing recipe: zero rent, not a guess.
            continue
        dominant_inputs = dominant_entry.get("inputs") or {}
        dominant_outputs = dominant_entry.get("outputs") or {}
        if ore_material not in dominant_inputs or not dominant_outputs:
            continue
        ore_per_metal = dominant_inputs[ore_material] / max(dominant_outputs.values())
        if ore_per_metal <= 0:
            continue

        ore_outputs = ore_entry.get("outputs") or {}
        if ore_material not in ore_outputs:
            continue
        ore_output_quantity = ore_outputs[ore_material]
        base_cost = recipe_cost_and_allocation(ore_material, ore_entry, {}, wage_by_trade)
        if base_cost is None:
            continue
        ore_base_total_hours, _ = base_cost
        ore_base_price_per_kg = ore_base_total_hours / ore_output_quantity
        existing_extraction_proxy_per_kg_metal = ore_base_price_per_kg * ore_per_metal

        deposits_for_metal = deposits.load_deposits(metal)
        quantity_demanded_tonnes_per_year = (
            STAND_IN_ORE_DEMAND_SHARE_OF_OPENING_OUTPUT
            * deposits.empire_output_net_of_byproducts_tonnes_per_year(metal, resources_json))
        outcome = deposits.find_marginal_deposit(
            deposits_for_metal, quantity_demanded_tonnes_per_year)
        metal_price_per_kg = outcome.price_at_margin_labour_hours_per_kg

        rent_per_kg_metal = max(
            0.0, metal_price_per_kg - existing_extraction_proxy_per_kg_metal)
        rent_by_ore_material[ore_material] = rent_per_kg_metal / ore_per_metal

    return rent_by_ore_material


# See sim/world/land.py's own `solve_prices` module docstring for the mechanism (the
# margin of cultivation over a civilization's own regions, not an ore
# deposit's grade) and for why this defaults to Rome's own territory when
# no --civ is given: mirroring rent_hours_per_kg_by_ore_material's own
# Rome-anchored default (data/world/resources.json's empire_output_100ad
# has no per-civilization breakdown either), even though land's OWN
# mechanism, unlike ore's, is genuinely per-civilization the moment --civ
# names one.
DEFAULT_LAND_CIVILIZATION = default_civilisation_id()


def land_rent_hours_per_hectare(production_entries, wage_by_trade,
                                civilization_id=None, civilizations=None, farmed_hectares=None):
    """{"hectare_land": hours of rent per hectare}, or {} if there is no
    reference crop price or no priceable land to convert into one this
    round - see sim/world/land.py's own `solve_prices` module docstring for the mechanism
    (the Ricardian margin of cultivation over a civilization's own held
    regions) and for why a civilization holding only one region prices
    land at exactly zero (a real finding, not a bug: no differential rent
    without at least two regions of different quality to compare).

    THE ALGEBRA. sim/world/land.py's own `margin_outcome_for_civilization`
    returns a supply-weighted average rent in kilograms of grain-equivalent
    per hectare - a PHYSICAL quantity, not a price (see that module's own
    WHY THE HOURS CONVERSION LIVES IN sim/engine/solve_prices.py, NOT HERE
    section for why the conversion happens here rather than there).
    Multiplying by wheat_kg's own ZERO-LAND-RENT price (labour only, exactly
    like rent_hours_per_kg_by_ore_material's own `ore_base_price_per_kg`)
    turns that physical surplus into the labour-hour unit this file prices
    everything else in. `hectare_land` itself has no `inputs` and no
    `labour_hours` of its own (data/production/40_organics.json's own
    entry says so directly), so this rent figure becomes its WHOLE solved
    price with nothing else added - see recipe_cost_and_allocation's own
    rent_hours term.

    THE ZERO-LAND-RENT REFERENCE PRICE, AND WHY IT STAYS ZERO-RENT EVEN NOW
    THAT wheat_kg CONSUMES LAND (Complaints/48). Before this round wheat_kg
    truly had no `inputs` at all, so calling `recipe_cost_and_allocation`
    with an empty price dict gave its labour-only price by construction.
    wheat_kg now also states a `land_hectare_years` (see RENT ON GROWN AND
    LAND-LIMITED MATERIALS above), so the SAME call would otherwise return
    None the moment it tries to look up a price for `hectare_land` that this
    empty dict does not have. The fix is to seed exactly that one price at
    0.0 rather than leave it absent - `{"hectare_land": 0.0}` - which
    reproduces the pre-Complaints/48 answer exactly (0.0 hours/hectare times
    any `land_hectare_years` is 0.0, so the land term drops out and only
    labour remains) rather than changing what this reference price MEANS.
    This is deliberately NOT circular: the reference price answers "what
    would wheat cost if land were free", which this function needs as a
    pure UNIT CONVERSION for land.py's physical rent, and it is computed
    once, outside the main iteration, the same way it always was - wheat's
    ACTUAL solved price (what every other recipe that consumes wheat_kg
    pays, and what bread is costed from) is computed by the ordinary
    Jacobi iteration in `solve()` below, WITH land_hectare_years priced in,
    using `hectare_land`'s price that THIS function's own return value
    fixes beforehand. See WHY NO NEW CYCLE in the `solve_prices` module docstring.
    """
    civilization_id = civilization_id or DEFAULT_LAND_CIVILIZATION
    wheat_entry = production_entries.get("wheat_kg")
    if wheat_entry is None:
        # Gated out of this era, or (should not happen - wheat_kg carries
        # requires_node: null, admitted to every era) simply absent. Either
        # way there is no reference crop price to convert the physical rent
        # into hours with, so land keeps the old RENT_IS_ZERO answer.
        return {}
    # the reference is wheat's labour alone: the plough team's capital is priced by the main solve, and
    # needs the land rent this function is still to fix
    labour_only = {key: value for key, value in wheat_entry.items() if key != "capital"}
    wheat_cost = recipe_cost_and_allocation(
        "wheat_kg", labour_only, {"hectare_land": 0.0}, wage_by_trade)
    if wheat_cost is None:
        return {}
    _wheat_total_hours, wheat_output_prices = wheat_cost
    wheat_price_per_kg = wheat_output_prices.get("wheat_kg")
    if not wheat_price_per_kg:
        return {}

    try:
        outcome = land.margin_outcome_for_civilization(
            civilization_id, civilizations=civilizations, farmed_hectares=farmed_hectares)
    except (FileNotFoundError, KeyError):
        # An unknown civilization id, or one missing a population field -
        # should not happen for this project's own data/civilizations/
        # files, handled the same way a missing ore recipe is: no rent
        # guessed, the old zero-rent answer stands.
        return {}
    rent_kg_per_hectare = outcome.price_kg_grain_equivalent_per_hectare
    if rent_kg_per_hectare <= 0.0:
        return {}
    rent_hours = rent_kg_per_hectare * wheat_price_per_kg
    return {"hectare_land": rent_hours}


def stand_in_rent(production_entries, wage_by_trade, civilization_id=None, civilizations=None, farmed_hectares=None):
    """{good: hours of rent per unit} the opening carries when the caller supplies none: the ore rents and the
    land rent."""
    rent = rent_hours_per_kg_by_ore_material(production_entries, wage_by_trade)
    rent.update(land_rent_hours_per_hectare(
        production_entries, wage_by_trade, civilization_id=civilization_id, civilizations=civilizations,
        farmed_hectares=farmed_hectares))
    return rent
