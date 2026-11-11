"""The data living stock reads: its rates file, and the production entry that raises each stock material."""
import functools
import json
import os

from sim.world.demand import production_data

LIVING_STOCK_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                 "data", "world", "living_stock.json")


@functools.lru_cache(maxsize=None)
def stock_rates():
    """{material: {natural_increase, annual_loss, breeding_minimum_units, basis}} from the data file."""
    with open(LIVING_STOCK_PATH, encoding="utf-8") as handle:
        return json.load(handle)["materials"]


def stock_entry(material, production=None):
    """The production entry (of `production`, else the repository's) that makes a stock material, which states the labour
    and land of raising more of it, or None when the data has no such entry."""
    for _key, entry in sorted((production_data() if production is None else production).items()):
        if (entry.get("outputs") or {}).get(material, 0.0) > 0.0:
            return entry
    return None

