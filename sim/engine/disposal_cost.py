"""What it costs to get rid of a unit of waste: handling, haulage to a dump, and the ground its heap holds.

A by-product nobody wants prices no lower than minus this cost, since dumping it is always an option.
The work is the disposal sink in data/production/99_waste_disposal.json (handling, haulage and dump
ground, each a service priced by the cost routine like any recipe); this module turns the solved prices
of those services into a cost per unit of one material, using the material's own heap
(data/world/waste_heaps.json). A solve holding no sink services finds disposal free. The state's minimum
dump distance (Complaints/309) lengthens the haul when it is longer than the walk to free land.
Figures behind the design: Complaints/reports/negative-byproduct-value-research.md.
"""
import functools
import json
import os
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable

from sim.constants import declare
from sim.world import demand

HANDLING_SERVICE = "waste_handling_job"
HAULAGE_SERVICE = "waste_haulage_tkm"
GROUND_SERVICE = "dump_ground_m2"
KILOGRAMS_PER_TONNE = 1000.0
WASTE_HEAPS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "data", "world", "waste_heaps.json")

DISPOSAL_FREE_LAND_DISTANCE_KILOMETRES = declare(
    "DISPOSAL_FREE_LAND_DISTANCE_KILOMETRES", 2.0, kind="temporary_heuristic", unit="km", source=None,
    confidence="D",
    why="Distance from the works to the nearest free land where waste may be tipped. Should come from the "
        "map around the works; the solve holds no map.")
DISPOSAL_HEAP_BULK_DENSITY_KILOGRAMS_PER_CUBIC_METRE = declare(
    "DISPOSAL_HEAP_BULK_DENSITY_KILOGRAMS_PER_CUBIC_METRE", 1000.0, kind="temporary_heuristic",
    unit="kg per cubic metre",
    source="Loose bulk solids run from a few hundred to a couple of thousand kg per cubic metre.",
    confidence="D",
    why="Density of a heap of a waste with no entry in data/world/waste_heaps.json. Give the material an "
        "entry there.")
DISPOSAL_HEAP_HEIGHT_METRES = declare(
    "DISPOSAL_HEAP_HEIGHT_METRES", 3.0, kind="temporary_heuristic", unit="m", source=None,
    confidence="D",
    why="Height of a hand-tipped heap of a waste with no entry in data/world/waste_heaps.json. Give the "
        "material an entry there.")
DISPOSAL_HEAP_OCCUPATION_YEARS_AT_ZERO_INTEREST = declare(
    "DISPOSAL_HEAP_OCCUPATION_YEARS_AT_ZERO_INTEREST", 100.0, kind="temporary_heuristic", unit="years",
    source=None, confidence="D",
    why="A heap holds its ground for good, so its rent is capitalised at the interest rate; with no "
        "interest rate the capitalised rent is unbounded, so this many years of rent stand in.")


@dataclass(frozen=True)
class Disposal:
    """What a solve round knows about waste: cost per unit by material, and the materials in glut."""
    costs: Dict[str, float] = field(default_factory=dict)
    glutted: FrozenSet[str] = frozenset()


def default_heap():
    return (DISPOSAL_HEAP_BULK_DENSITY_KILOGRAMS_PER_CUBIC_METRE, DISPOSAL_HEAP_HEIGHT_METRES)


@functools.lru_cache(maxsize=1)
def _heap_table():
    with open(WASTE_HEAPS_FILE) as handle:
        return json.load(handle)["materials"]


def heap_of(material):
    """(bulk density in kg per cubic metre, heap height in metres) of a heap of `material`."""
    record = _heap_table().get(material)
    if record is None:
        return default_heap()
    return record["bulk_density_kg_per_m3"], record["heap_height_m"]


def heap_area_square_metres_per_kilogram(bulk_density, heap_height):
    return 1.0 / (bulk_density * heap_height)


def disposal_cost_hours_per_kilogram(
        handling_hours_per_tonne, haul_hours_per_tonne_kilometre, ground_hours_per_square_metre_year,
        interest_rate=0.0, distance_kilometres=DISPOSAL_FREE_LAND_DISTANCE_KILOMETRES,
        bulk_density=DISPOSAL_HEAP_BULK_DENSITY_KILOGRAMS_PER_CUBIC_METRE,
        heap_height=DISPOSAL_HEAP_HEIGHT_METRES):
    """Labour hours to load, haul and tip one kilogram and to hold the ground its heap covers for good."""
    occupation_years = (1.0 / interest_rate if interest_rate > 0.0
                        else DISPOSAL_HEAP_OCCUPATION_YEARS_AT_ZERO_INTEREST)
    ground_hours = (ground_hours_per_square_metre_year * occupation_years
                    * heap_area_square_metres_per_kilogram(bulk_density, heap_height))
    return (handling_hours_per_tonne + haul_hours_per_tonne_kilometre * distance_kilometres) \
        / KILOGRAMS_PER_TONNE + ground_hours


def disposal_cost_by_material(materials: Iterable[str], prices, interest_rate=0.0,
                              minimum_dump_distance_kilometres=0.0) -> Dict[str, float]:
    """{material: disposal cost in hours per unit of that material}, for each material that has a mass.

    Empty when the solve prices none of the sink services: with no way to dispose of waste there is no cost
    to charge for it."""
    if not all(service in prices for service in (HANDLING_SERVICE, HAULAGE_SERVICE, GROUND_SERVICE)):
        return {}
    distance = max(DISPOSAL_FREE_LAND_DISTANCE_KILOMETRES, minimum_dump_distance_kilometres)
    costs = {}
    for material in materials:
        kilograms = demand.mass_in_kg_or_none(material, 1.0)
        if kilograms is None:
            continue
        bulk_density, heap_height = heap_of(material)
        costs[material] = kilograms * disposal_cost_hours_per_kilogram(
            max(prices[HANDLING_SERVICE], 0.0), max(prices[HAULAGE_SERVICE], 0.0),
            max(prices[GROUND_SERVICE], 0.0), interest_rate, distance, bulk_density, heap_height)
    return costs


def joint_output_materials(production_entries):
    """Materials some joint recipe makes alongside another output: the ones that can be a waste."""
    return sorted({material for entry in production_entries.values()
                   if len(entry.get("outputs") or {}) > 1 for material in entry["outputs"]})


def disposal_price_floor(materials, prices, interest_rate=0.0, minimum_dump_distance_kilometres=0.0):
    """{material: lowest price the solve may give it}, minus its disposal cost."""
    return {material: -cost for material, cost in disposal_cost_by_material(
        materials, prices, interest_rate, minimum_dump_distance_kilometres).items()}
