"""Interest and tax rates are each civilisation's own starting state."""
import contextlib
import copy
import json
import os
import random
import tempfile
import unittest
from unittest import mock

from sim.engine import data
from sim.engine.core import Sim

BASE_CIVS = ["rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"]
MOD_CIV = "sample_egypt_100bc_e7k2:egypt"
FIELDS = ("starting_interest_rate", "starting_tax_share")


_GAMES = {}


def game(name):
    """One shared game per civilisation, built once with the economy unopened (the engine's own base rate, as it
    stands before the economy opens). A test varies a rate on the game's own civ for the length of a block: the
    engine reads the civ's field when it answers, so no second game (and no second price solve) is needed."""
    if name not in _GAMES:
        from sim.tests import harness
        _GAMES[name] = harness.build_unopened(lambda: Sim(
            harness.NODES, harness.ORDER, random.Random(1), events=False, manual=True, civ=data.load_civ(name)))
    return _GAMES[name]


@contextlib.contextmanager
def civ_field(sim, field, value):
    held = sim.civ[field]
    sim.civ[field] = value
    try:
        yield
    finally:
        sim.civ[field] = held


class CivRateFieldTests(unittest.TestCase):
    def test_every_civ_declares_both_rates_with_a_sourced_note(self):
        for name in BASE_CIVS + [MOD_CIV]:
            civ = data.load_civ(name)
            for field in FIELDS:
                self.assertIn(field, civ, (name, field))
                self.assertGreaterEqual(civ[field], 0.0)
                self.assertLess(civ[field], 1.0)
                note = civ["_internal"][field]
                self.assertTrue(note["source"] and note["confidence"], (name, field))

    def test_civs_do_not_all_share_one_rate(self):
        for field in FIELDS:
            values = {data.load_civ(name)[field] for name in BASE_CIVS}
            self.assertGreater(len(values), 1, field)

    def test_missing_field_is_a_clear_load_error(self):
        for field in FIELDS:
            with tempfile.TemporaryDirectory() as directory:
                civ = copy.deepcopy(data.load_civ("rome_100ad"))
                civ.pop(field)
                with open(os.path.join(directory, "rome_100ad.json"), "w") as handle:
                    json.dump(civ, handle)
                with mock.patch.object(data, "CIVDIR", directory):
                    with self.assertRaises(ValueError) as caught:
                        data.load_civ("rome_100ad")
                self.assertIn(field, str(caught.exception))


class EngineUsesCivRatesTests(unittest.TestCase):
    def test_each_civ_base_rate_shifts_its_interest_one_for_one(self):
        for name in BASE_CIVS + [MOD_CIV]:
            sim = game(name)
            base = sim.civ["starting_interest_rate"]
            before = sim.debt_interest_rate()
            with civ_field(sim, "starting_interest_rate", base + 0.1):
                self.assertAlmostEqual(sim.debt_interest_rate() - before, 0.1, msg=name)

    def test_tax_bite_follows_the_civs_tax_share(self):
        sim = game("rome_100ad")
        costs = {}
        for share in (0.0, 0.3):
            with civ_field(sim, "starting_tax_share", share):
                costs[share] = sim.living_cost(_rev=1000.0, _upkeep=0.0)
        self.assertGreater(costs[0.3], costs[0.0])

    def test_interest_follows_civ_value(self):
        sim = game("rome_100ad")
        rates = []
        for value in (0.05, 0.40):
            with civ_field(sim, "starting_interest_rate", value):
                reputation, operating = sim.state.household.reputation, set(sim.operating)
                sim.state.household.reputation = 0.0
                sim.operating.clear()
                try:
                    rates.append(sim.debt_interest_rate())
                finally:
                    sim.state.household.reputation = reputation
                    sim.operating.update(operating)
        self.assertLess(rates[0], rates[1])


if __name__ == "__main__":
    unittest.main()
