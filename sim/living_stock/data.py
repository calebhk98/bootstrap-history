"""The data living stock reads: its rates file, and the production entry that raises each stock material."""
import functools
import json
import os

from sim.labour.api import production_data
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world.material_units import tonnes_per_unit

LIVING_STOCK_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                 "data", "world", "living_stock.json")


@functools.lru_cache(maxsize=None)
def stock_rates():
    """{material: {natural_increase, annual_loss, breeding_minimum_units, basis}} from the data file."""
    with open(LIVING_STOCK_PATH, encoding="utf-8") as handle:
        return json.load(handle)["materials"]


@functools.lru_cache(maxsize=None)
def stock_entry(material):
    """The production entry that makes a stock material, which states the labour and land of raising more
    of it, or None when the data has no such entry."""
    for _key, entry in sorted(production_data().items()):
        if (entry.get("outputs") or {}).get(material, 0.0) > 0.0:
            return entry
    return None


def kilograms_per_unit(material):
    return tonnes_per_unit(material) * KILOGRAMS_PER_TONNE
