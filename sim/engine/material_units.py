"""Mass per counted unit of a material key. A leaf module, so any engine module can import it."""
from sim.unit_conversions import KILOGRAMS_PER_TONNE

_GRAMS_PER_TONNE = 1.0e6


def tonnes_per_unit(material):
    """Tonnes in one unit of a material key: the tree's gram keys are grams,
    every other key is counted in thousands of units to the tonne."""
    if material.endswith("_g") and not material.endswith("_kg"):
        return 1.0 / _GRAMS_PER_TONNE
    return 1.0 / KILOGRAMS_PER_TONNE
