"""Seed rate and fold return of Roman wheat, built from data/world/grain_yield.json.

Pure: reads the data files; imports nothing else from sim/ besides farm_labour (the iugerum)."""
import json
import os
from functools import lru_cache
from typing import Any, Dict

from .farm_labour import load_farm_labour

GRAIN_YIELD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "data", "world", "grain_yield.json")


@lru_cache(maxsize=1)
def load_grain_yield() -> Dict[str, Any]:
    with open(GRAIN_YIELD_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def seed_kg_per_hectare(data: Dict[str, Any], iugerum_hectares: float) -> float:
    """Kilograms of seed a hectare takes: modii to the iugerum, each modius weighing so many Roman pounds."""
    seed = data["seed"]
    kg_per_iugerum = (float(seed["modii_per_iugerum"]) * float(seed["pounds_per_modius"])
                      * float(seed["kg_per_roman_pound"]))
    return kg_per_iugerum / iugerum_hectares


def fold_return(data: Dict[str, Any]) -> float:
    return float(data["fold_return"]["value"])


def net_yield_kg_per_hectare(seed_kg: float, fold: float) -> float:
    """Grain left after the seed is held back; the fold return counts the seed inside the harvest."""
    return seed_kg * (fold - 1.0)


SEED_KG_PER_HECTARE = seed_kg_per_hectare(load_grain_yield(), float(load_farm_labour()["iugerum_hectares"]["value"]))
FOLD_RETURN = fold_return(load_grain_yield())
