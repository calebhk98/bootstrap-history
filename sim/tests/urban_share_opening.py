"""Command: each civilisation's computed urban share at its opening against its validation band.

    python3 -m sim.tests.urban_share_opening [civilisation_id ...]

Prints the typed `urban_fraction` (the opening's initial condition), the share the regions give (`Sim.urban_fraction`),
the most the regions' towns could feed, and the band with its source (data/world/urban_share_bands.json).
"""
import json
import os
import sys

from sim.tests.harness import unopened_sim
from sim.world import urban_share

BANDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "world", "urban_share_bands.json")


def bands():
    with open(BANDS_PATH, encoding="utf-8") as handle:
        return json.load(handle)["bands"]


def opening_report(civilisation_id):
    game = unopened_sim(civilisation_id)
    people = game.people_by_tile() or game._people_for_urban_share()
    ceilings = game.urban_ceilings()
    band = urban_share.band_for(civilisation_id, bands())
    computed = game.urban_fraction()
    return {"civilisation": civilisation_id, "typed_initial_condition": float(game.civ.get("urban_fraction", 0.0)),
            "computed": computed,
            "most_the_towns_could_feed": sum(min(ceilings[tile], people[tile]) for tile in people) / game.population.total,
            "band": band, "inside_band": urban_share.within_band(computed, band)}


if __name__ == "__main__":
    from sim.engine.ui_port import civilization_ids
    for civilisation in sys.argv[1:] or civilization_ids():
        print(json.dumps(opening_report(civilisation), sort_keys=True))
