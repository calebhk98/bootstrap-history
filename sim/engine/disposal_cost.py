"""What it costs to get rid of a kilogram of waste: handling, haulage to a dump, and the heap's land.

A by-product nobody wants prices no lower than minus this cost, since dumping it is always an option.
Every term is a physical quantity or a labelled heuristic; the result is in labour hours per kilogram.
Source strength for the design (Complaints/reports/negative-byproduct-value-research.md): read through
search summaries only, so the figures below are labelled D and the structure, not the numbers, is the claim.
"""
from sim.constants import declare
from sim.world import demand

SQUARE_METRES_PER_HECTARE = declare(
    "SQUARE_METRES_PER_HECTARE", 10000.0, kind="physical_constant", unit="square metres per hectare",
    source="Definition of the hectare.", confidence="A",
    why="Turns the heap's footprint into the unit land is priced in.")
DISPOSAL_HANDLING_LABOUR_HOURS_PER_KILOGRAM = declare(
    "DISPOSAL_HANDLING_LABOUR_HOURS_PER_KILOGRAM", 0.002, kind="temporary_heuristic",
    unit="labour-hours per kg (loading plus tipping)", source=None, confidence="D",
    why="Twice the loading rate of the porter carriage mode (handling_hours_per_tonne in "
        "data/world/geography/route_modes/modes.json), one for loading and one for tipping. Should come "
        "from the carriage mode the dump haul uses.")
DISPOSAL_HAUL_LABOUR_HOURS_PER_KILOGRAM_KILOMETRE = declare(
    "DISPOSAL_HAUL_LABOUR_HOURS_PER_KILOGRAM_KILOMETRE", 0.001, kind="temporary_heuristic",
    unit="labour-hours per kg per km", source=None, confidence="D",
    why="One driver and an ox cart carrying about half a tonne at about 20 km a day, empty on the way "
        "back. Should come from the cheapest carriage mode's crew_hours_per_tonne_km "
        "(sim/geography/routes_carriage.py); not read here because the solve holds no map.")
DISPOSAL_DUMP_DISTANCE_KILOMETRES = declare(
    "DISPOSAL_DUMP_DISTANCE_KILOMETRES", 2.0, kind="temporary_heuristic", unit="km", source=None,
    confidence="D",
    why="Distance from the works to free land where waste may be tipped. Should be the larger of the "
        "distance to the nearest free land and a state rule's minimum distance from settlement and water.")
DISPOSAL_HEAP_BULK_DENSITY_KILOGRAMS_PER_CUBIC_METRE = declare(
    "DISPOSAL_HEAP_BULK_DENSITY_KILOGRAMS_PER_CUBIC_METRE", 1000.0, kind="temporary_heuristic",
    unit="kg per cubic metre",
    source="Loose bulk solids run from a few hundred to a couple of thousand kg per cubic metre "
           "(recalled from handbooks, not checked).", confidence="D",
    why="One density for every waste. Should be a property of the material.")
DISPOSAL_HEAP_HEIGHT_METRES = declare(
    "DISPOSAL_HEAP_HEIGHT_METRES", 3.0, kind="temporary_heuristic", unit="m", source=None,
    confidence="D",
    why="Height a hand-tipped heap of loose waste stands at before it slumps. Should come from the "
        "material's angle of repose and the tipping method.")
DISPOSAL_HEAP_OCCUPATION_YEARS_AT_ZERO_INTEREST = declare(
    "DISPOSAL_HEAP_OCCUPATION_YEARS_AT_ZERO_INTEREST", 100.0, kind="temporary_heuristic", unit="years",
    source=None, confidence="D",
    why="A heap holds its land for good, so its rent is capitalised at the interest rate; with no "
        "interest rate the capitalised rent is unbounded, so this many years of rent stand in.")
LAND_PRICE_MATERIAL = "hectare_land"


def heap_area_square_metres_per_kilogram(bulk_density, heap_height):
    return 1.0 / (bulk_density * heap_height)


def disposal_cost_hours_per_kilogram(
        land_rent_hours_per_hectare_year=0.0, interest_rate=0.0,
        distance_kilometres=DISPOSAL_DUMP_DISTANCE_KILOMETRES,
        bulk_density=DISPOSAL_HEAP_BULK_DENSITY_KILOGRAMS_PER_CUBIC_METRE,
        heap_height=DISPOSAL_HEAP_HEIGHT_METRES,
        handling_hours=DISPOSAL_HANDLING_LABOUR_HOURS_PER_KILOGRAM,
        haul_hours_per_kilometre=DISPOSAL_HAUL_LABOUR_HOURS_PER_KILOGRAM_KILOMETRE):
    """Labour hours to load, haul and tip one kilogram and to hold the land its heap covers for good."""
    occupation_years = (1.0 / interest_rate if interest_rate > 0.0
                        else DISPOSAL_HEAP_OCCUPATION_YEARS_AT_ZERO_INTEREST)
    land_hours = (land_rent_hours_per_hectare_year * occupation_years
                  * heap_area_square_metres_per_kilogram(bulk_density, heap_height)
                  / SQUARE_METRES_PER_HECTARE)
    return handling_hours + haul_hours_per_kilometre * distance_kilometres + land_hours


def disposal_cost_by_material(materials, prices, interest_rate=0.0):
    """{material: disposal cost in hours per unit of that material}, for each material that has a mass."""
    cost_per_kilogram = disposal_cost_hours_per_kilogram(
        max(prices.get(LAND_PRICE_MATERIAL, 0.0), 0.0), interest_rate)
    costs = {}
    for material in materials:
        kilograms = demand.mass_in_kg_or_none(material, 1.0)
        if kilograms is not None:
            costs[material] = cost_per_kilogram * kilograms
    return costs


def joint_output_materials(production_entries):
    """Materials some joint recipe makes alongside another output: the ones that can be a waste."""
    return sorted({material for entry in production_entries.values()
                   if len(entry.get("outputs") or {}) > 1 for material in entry["outputs"]})


def disposal_price_floor(materials, prices, interest_rate=0.0):
    """{material: lowest price the solve may give it}, minus its disposal cost."""
    return {material: -cost for material, cost in
            disposal_cost_by_material(materials, prices, interest_rate).items()}
