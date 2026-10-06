"""Complaints/355: a civilisation that exists only in memory (a derived mod civ,
a test variant, a player-made country) runs the whole game, and its own fields
are what the engine uses, not a file's with the same id."""
import copy
import random
import unittest

from .harness import *  # noqa: F401,F403
from sim.engine.prices import band_farmed_hectares
from sim.ui.protocol import _agent_dispatch, KNOWN_COMMANDS

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

    @classmethod
    def setUpClass(cls):
        cls.variant = _variant(keep_file_id=True)
        cls.variant_sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=False, civ=cls.variant)

    def test_variant_with_a_files_id_is_priced_as_itself(self):
        variant, sim = self.variant, self.variant_sim
        original = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=False,
                         civ=S.load_civ("rome_100ad"))
        held = frozenset(sim.state.projects.done)
        own_hours, _basis = S.calculated_goods_table(
            held, civilization_id=variant["id"], civilization=variant,
            farmed_hectares=band_farmed_hectares(sim.farm_land.hectares))
        own = {material: price * sim.labour.money_per_labour_hour() for material, price in own_hours.items()}
        self.assertTrue(sim._material_prices() == own)
        self.assertTrue(sim._material_prices() != original._material_prices())
        self.assertNotAlmostEqual(
            sim._material_prices()["hectare_land"] / sim.labour.money_per_labour_hour(),
            original._material_prices()["hectare_land"] / original.labour.money_per_labour_hour())

    def test_divergence_start_values_are_the_variants_own(self):
        territory = _agent_dispatch(self.variant_sim, NODES, {"cmd": "divergence"})["territory"]
        self.assertEqual(territory["start"], ["scandinavia"])
        self.assertFalse(territory["changed"])
