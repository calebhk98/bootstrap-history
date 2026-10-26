"""Reads data/world/world_hazards.json: the base-rate hazards, the famine recording threshold, the log length."""
import functools
import json
import os

FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "world", "world_hazards.json")


@functools.lru_cache(maxsize=1)
def _document():
    with open(FILE, encoding="utf-8") as handle:
        return json.load(handle)


def hazards():
    return [dict(entry) for entry in _document()["hazards"]]


def famine_food_shortfall():
    return float(_document()["famine_food_shortfall"]["value"])


def years_kept():
    return int(_document()["event_log_years_kept"])
