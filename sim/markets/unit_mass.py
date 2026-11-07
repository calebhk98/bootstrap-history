"""Mass of one unit of a good, read from the economy's one rule for it (sim/economy/good_mass.py, through its goods specs)."""
import math

from sim.economy.api import goods_specs
from sim.world.demand import production_data
from sim.unit_conversions import KILOGRAMS_PER_TONNE

_kept = {"data": None, "kilograms": {}}     # the production data the masses were read under, and the mass of each good met


def unit_mass_kg(material):
    """Kilograms in one unit of a material, as the freight model reads it (infinite for a unit that cannot be carried).
    Kept while the production data stays the same object."""
    data = production_data()
    if _kept["data"] is not data:
        _kept["data"], _kept["kilograms"] = data, {}
    kilograms = _kept["kilograms"]
    if material not in kilograms:
        kilograms[material] = goods_specs({material: ""}, {})[material].unit_mass_kg
    return kilograms[material]


def tonnes_per_unit(material):
    """Tonnes in one unit of a material, or None when a unit has no finite mass (an area, a flow of energy), which no
    tonnes make."""
    per_unit = unit_mass_kg(material) / KILOGRAMS_PER_TONNE
    return per_unit if 0.0 < per_unit < math.inf else None
