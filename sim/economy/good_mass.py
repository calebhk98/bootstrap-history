"""The mass of one unit of a good, for freight, from what the data and the physical models state.

Order of evidence: a mass unit in the good's id; a `unit_mass_kg` stated in the good's production
entry; a live weight in the animal table; a unit that is
not a mass at all (ground area, energy), which cannot be carried; a volume unit at a stated bulk
density; the mass of what a one-item recipe consumes; and last, a labelled default. Each answer
names its source so an audit can count how much of the freight base is still a guess.

Standalone: `sim.constants`, `sim.unit_conversions`, `sim.world`.
"""
import math
from typing import Any, Mapping, Optional, Tuple

from sim.constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.geography.api import transport
from sim.world import demand

# Units written into an id the way demand reads `_kg`, `_g`, `_t`; the tonne spelled out is one more.
EXTRA_MASS_UNIT_SUFFIXES = {"_tons": KILOGRAMS_PER_TONNE}
# Unit tokens naming a quantity with no mass: a flow of energy, or a piece of ground. Not carried.
IMMOBILE_UNIT_SUFFIXES = ("_mj",)
IMMOBILE_UNIT_PREFIXES = ("hectare_",)
VOLUME_UNIT_SUFFIX = "_m3"

IMMOBILE_MASS_KG = math.inf    # carriage per unit is infinite, value per tonne is nil: no area beyond its tile

BULK_DENSITY_KG_PER_M3 = declare(
    "BULK_DENSITY_KG_PER_M3", 1000.0, kind="temporary_heuristic", unit="kg per cubic metre",
    source=None, confidence="D",
    why="A good counted by volume states no material density; water's is the scale seasoned timber, "
        "earth and loose stone sit around, within a factor of about two. Replace with a density "
        "per material when data names one.")
PRODUCT_MASS_SHARE_OF_CONSUMED_MASS = declare(
    "PRODUCT_MASS_SHARE_OF_CONSUMED_MASS", 1.0, kind="temporary_heuristic",
    unit="kg of product per kg of mass-denominated inputs", source=None, confidence="D",
    why="A one-item recipe's product cannot weigh more than what it consumed, and shaping or "
        "firing loses part of it (waste stone, driven-off water, burnt fuel); the loss is not "
        "stated per recipe, so the product is taken as heavy as its inputs, an upper bound.")
UNKNOWN_UNIT_MASS_KG = declare(
    "UNKNOWN_UNIT_MASS_KG", 1.0, kind="temporary_heuristic", unit="kg per unit", source=None,
    confidence="D",
    why="The good's unit is not a mass, no animal weight, bulk density or consumed mass says what a "
        "unit weighs; one kilogram keeps it carriable until the data states a mass.")

SOURCE_MASS_UNIT = "mass unit"
SOURCE_STATED = "stated in production data"
SOURCE_ANIMAL = "animal live weight"
SOURCE_IMMOBILE = "immobile unit"
SOURCE_VOLUME = "volume at bulk density"
SOURCE_RECIPE = "mass of consumed inputs"
SOURCE_DEFAULT = "default"


def _living_masses() -> Mapping[str, float]:
    return {animal.name: animal.body_mass_kg for animal in vars(transport).values()
            if isinstance(animal, transport.Animal)}


def _mass_unit_kg(good: str) -> Optional[float]:
    for suffix, multiplier in EXTRA_MASS_UNIT_SUFFIXES.items():
        if good.endswith(suffix):
            return multiplier
    return demand.mass_in_kg_or_none(good, 1.0)


def _consumed_mass_kg(good: str, production: Mapping[str, Any]) -> Optional[float]:
    """Mass of the mass-denominated inputs of a recipe that makes one unit of `good` per run."""
    entry = production.get(good)
    if not isinstance(entry, Mapping) or (entry.get("outputs") or {}).get(good) != 1.0:
        return None
    total = sum(quantity * (_mass_unit_kg(input_good) or 0.0)
                for input_good, quantity in (entry.get("inputs") or {}).items())
    return total * PRODUCT_MASS_SHARE_OF_CONSUMED_MASS if total > 0.0 else None


def _stated_unit_mass_kg(good: str, production: Optional[Mapping[str, Any]]) -> Optional[float]:
    entry = (production if production is not None else demand.production_data()).get(good)
    stated = entry.get("unit_mass_kg") if isinstance(entry, Mapping) else None
    return float(stated) if stated is not None else None


def unit_mass_and_source(good: str, production: Optional[Mapping[str, Any]] = None) -> Tuple[float, str]:
    """(kg of one unit, where the figure came from); `production` defaults to the shared data."""
    mass = _mass_unit_kg(good)
    if mass is not None:
        return mass, SOURCE_MASS_UNIT
    stated = _stated_unit_mass_kg(good, production)
    if stated is not None:
        return stated, SOURCE_STATED
    living = _living_masses()
    if good in living:
        return living[good], SOURCE_ANIMAL
    if good.endswith(IMMOBILE_UNIT_SUFFIXES) or good.startswith(IMMOBILE_UNIT_PREFIXES):
        return IMMOBILE_MASS_KG, SOURCE_IMMOBILE
    if good.endswith(VOLUME_UNIT_SUFFIX):
        return BULK_DENSITY_KG_PER_M3, SOURCE_VOLUME
    consumed = _consumed_mass_kg(good, production if production is not None else demand.production_data())
    if consumed is not None:
        return consumed, SOURCE_RECIPE
    return UNKNOWN_UNIT_MASS_KG, SOURCE_DEFAULT
