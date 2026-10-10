"""Quantities typed in a unit: `n` with a `unit` (or "10 acre" as the text of `n`) converts to the unit the engine takes.

The unit is any registry unit of the quantity's dimension, or `shown` for the
one the player chose to display. Without a unit the quantity is the engine's
own, as the usage lines say, so a script never depends on a display choice.
"""
import re

from sim.engine.ui_port import units
from .buy_targets import TARGET_QUANTITY, canonical_target
from .util import _qty

_NUMBER_AND_UNIT = re.compile(r"\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*([A-Za-z][A-Za-z0-9_ ]*?)\s*")
SHOWN_WORDS = ("shown", "chosen", "display", "displayed")


def read_quantity(cmd, key, default, dimension, native_unit, sim):
    """(quantity in the engine's `native_unit`, error) for a quantity of `dimension`, reading a `unit` the player may have given."""
    value = cmd.get(key, default)
    unit_text = cmd.get("unit")
    if isinstance(value, str):
        match = _NUMBER_AND_UNIT.fullmatch(value)
        if match:
            value, unit_text = match.group(1), match.group(2)
    quantity, error = _qty({key: value}, key, default)
    if error or unit_text in (None, ""):
        return quantity, error
    registry = units.registry()
    civ_id = getattr(sim, "civ_id", None) or (getattr(sim, "civ", None) or {}).get("id")
    if str(unit_text).strip().lower() in SHOWN_WORDS:
        unit_id = units.chosen_units().get(dimension) or native_unit
    else:
        unit_id = units.find_unit(registry, unit_text, dimension, civ_id)
    if unit_id is None:
        options = ", ".join(units.available_units(registry, dimension, civ_id))
        return None, "%r is not a unit of %s here; use one of: %s, or shown" % (unit_text, dimension, options)
    if unit_id == native_unit:
        return quantity, None
    return units.convert_between(registry, quantity, unit_id, native_unit, units.unit_context(sim)), None


def read_target_quantity(cmd, key, default, target, sim):
    """`read_quantity` for a buy target that has a dimension; the plain reader for the others, which take no unit."""
    dimension_and_unit = TARGET_QUANTITY.get(canonical_target(target) or "")
    if dimension_and_unit is None:
        return _qty(cmd, key, default)
    return read_quantity(cmd, key, default, dimension_and_unit[0], dimension_and_unit[1], sim)
