"""What a material's count measures (mass, area, volume, ...), so a screen can label it in its own unit."""

from sim.constants import declare
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import demand, good_dimension

NEVER_PRODUCED_YEARS = declare(
    "NEVER_PRODUCED_YEARS", 1000.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="A shortfall that market and own output would take longer than this to supply is shown as "
        "something nobody produces, not as a number of years.")

UNIT_WORDS = {good_dimension.MASS: "tonnes", good_dimension.AREA: "hectares",
              good_dimension.VOLUME: "cubic metres", good_dimension.ENERGY: "MJ",
              good_dimension.LENGTH: "metres", good_dimension.COUNT: "pieces"}


def material_dimension(material):
    """The dimension of one unit of a material: its production entry's `unit_dimension`, else what its id spells, else mass."""
    entry = demand.production_data().get(material)
    stated = entry.get("unit_dimension") if isinstance(entry, dict) else None
    return stated or good_dimension.dimension_from_id(material) or good_dimension.MASS


def own_unit_quantities(material, needed_tonnes, held_tonnes, missing_tonnes):
    """The quantities of a non-mass material in its own unit (the bill counts a thousand units to the tonne), or None for a mass."""
    dimension = material_dimension(material)
    if dimension == good_dimension.MASS:
        return None
    return {"dimension": dimension, "unit": UNIT_WORDS.get(dimension, "units"),
            "needed": round(needed_tonnes * KILOGRAMS_PER_TONNE, 2),
            "held": round(held_tonnes * KILOGRAMS_PER_TONNE, 2),
            "missing": round(missing_tonnes * KILOGRAMS_PER_TONNE, 2)}
