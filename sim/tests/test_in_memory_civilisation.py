"""Complaints/690: a civilisation that exists only in memory (a derived mod civ,
a test variant, a player-made country) runs the whole game, and its own fields
are what the engine uses, not a file's with the same id."""
import copy
import random
import unittest

from .harness import *  # noqa: F401,F403
from sim.engine.protocol import _agent_dispatch, KNOWN_COMMANDS

_SKIP = ("quit", "save", "load")


def _variant(keep_file_id=False):
    civ = copy.deepcopy(S.load_civ("rome_100ad"))
    if not keep_file_id:
        civ["id"] = "variant_with_no_file"
    civ["home_regions"] = ["scandinavia"]
    civ["starting_interest_rate"] = 0.31
    return civ


class InMemoryCivilisation(unittest.TestCase):
    def test_game_runs_every_screen(self):
        sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=False, civ=_variant())
        for _ in range(4):
            sim.step()
        self.assertEqual(sim.civ["id"], "variant_with_no_file")
        failures = []
        for command in sorted(KNOWN_COMMANDS):
            if command in _SKIP:
                continue
            try:
                response = _agent_dispatch(sim, NODES, {"cmd": command})
            except Exception as error:  # a screen must answer, never raise
                failures.append((command, repr(error)))
                continue
            text = str(response.get("error", "")) if isinstance(response, dict) else ""
            if "unknown civili" in text.lower():
                failures.append((command, text))
        self.assertEqual(failures, [])

    def test_variant_with_a_files_id_is_priced_as_itself(self):
        variant = _variant(keep_file_id=True)
        sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=False, civ=variant)
        original = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=False,
                         civ=S.load_civ("rome_100ad"))
        held = frozenset(sim.state.projects.done)
        own = S.calculated_goods_prices(held, civilization_id=variant["id"], civilization=variant,
                                        money_per_labour_hour=sim.money_per_labour_hour())
        self.assertTrue(sim._material_prices() == own)
        self.assertTrue(sim._material_prices() != original._material_prices())
        self.assertNotAlmostEqual(
            sim._material_prices()["hectare_land"] / sim.money_per_labour_hour(),
            original._material_prices()["hectare_land"] / original.money_per_labour_hour())

    def test_divergence_start_values_are_the_variants_own(self):
        sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=False,
                    civ=_variant(keep_file_id=True))
        territory = _agent_dispatch(sim, NODES, {"cmd": "divergence"})["territory"]
        self.assertEqual(territory["start"], ["scandinavia"])
        self.assertFalse(territory["changed"])
