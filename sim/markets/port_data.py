"""The data files the port reads beside the mod-applied registries: the goods' service lives and spoilage rates. Part of the port."""
import os

from sim.default_civilisation import REPOSITORY_ROOT
from sim.json_files import read_json

WORLD_DATA = os.path.join(REPOSITORY_ROOT, "data", "world")


def service_life_years():
    """{good: service life in years} of the goods that wear out."""
    return {good: float(entry["years"])
            for good, entry in read_json(os.path.join(WORLD_DATA, "service_lives.json")).get("years", {}).items()}


def spoilage_rates():
    """{good: {"rate": continuous spoilage a year}} of the goods that spoil."""
    return read_json(os.path.join(WORLD_DATA, "spoilage.json")).get("rates_per_year", {})
