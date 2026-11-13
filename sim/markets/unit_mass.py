"""Mass of one unit of a good, read from the economy's one rule for it (sim/economy/good_mass.py, through its goods specs)."""
import math

from sim.economy.api import goods_specs
from sim.world.demand import production_data
from sim.unit_conversions import KILOGRAMS_PER_TONNE

_kept = {}     # id of a production table -> (the table, the mass of each good met under it); a hit is confirmed with `is`


def unit_mass_kg(material, production=None):
    """Kilograms in one unit of a material, as the freight model reads it (infinite for a unit that cannot be carried), under
    `production` (the repository's mods' when none is given). Kept while the production data stays the same object."""
    data = production_data() if production is None else production
    held = _kept.get(id(data))
    if held is None or held[0] is not data:
        held = _kept[id(data)] = (data, {})
    kilograms = held[1]
    if material not in kilograms:
        kilograms[material] = goods_specs({material: ""}, {}, production=data)[material].unit_mass_kg
    return kilograms[material]


def tonnes_per_unit(material, production=None):
    """Tonnes in one unit of a material, or None when a unit has no finite mass (an area, a flow of energy), which no
    tonnes make."""
    per_unit = unit_mass_kg(material, production) / KILOGRAMS_PER_TONNE
    return per_unit if 0.0 < per_unit < math.inf else None
