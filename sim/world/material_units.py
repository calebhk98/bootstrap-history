"""Mass per counted unit of a material key. A leaf module, so any engine module or package can import it.

Not the freight mass: the economy's rule (sim/economy/good_mass.py, the markets module's `unit_mass_kg` view) is the owner, and
the markets package reads only that. This stand-in remains for sim/actors/delivered_goods.py, sim/actors/world_trade.py,
sim/materials/availability.py, sim/materials/project_bill.py, sim/living_stock/data.py and sim/engine/material_units.py, which are to
read the view and then delete this file."""
from sim.unit_conversions import KILOGRAMS_PER_TONNE

_GRAMS_PER_TONNE = 1.0e6


def tonnes_per_unit(material):
    """Tonnes in one unit of a material key: the tree's gram keys are grams,
    every other key is counted in thousands of units to the tonne."""
    if material.endswith("_g") and not material.endswith("_kg"):
        return 1.0 / _GRAMS_PER_TONNE
    return 1.0 / KILOGRAMS_PER_TONNE
