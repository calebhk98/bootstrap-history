"""Interest and tax rates are each civilisation's own starting state."""
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


def build(civ):
    from sim.tests import harness
    return Sim(harness.NODES, harness.ORDER, random.Random(1), events=False,
               manual=True, civ=civ)


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
            base = data.load_civ(name)
            raised = data.load_civ(name)
            raised["starting_interest_rate"] = base["starting_interest_rate"] + 0.1
            self.assertAlmostEqual(build(raised).debt_interest_rate()
                                   - build(base).debt_interest_rate(), 0.1, msg=name)

    def test_tax_bite_follows_the_civs_tax_share(self):
        costs = {}
        for share in (0.0, 0.3):
            civ = data.load_civ("rome_100ad")
            civ["starting_tax_share"] = share
            costs[share] = build(civ).living_cost(_rev=1000.0, _upkeep=0.0)
        self.assertGreater(costs[0.3], costs[0.0])

    def test_interest_follows_civ_value(self):
        rates = []
        for value in (0.05, 0.40):
            civ = data.load_civ("rome_100ad")
            civ["starting_interest_rate"] = value
            sim = build(civ)
            sim.state.household.reputation = 0.0
            sim.operating.clear()
            rates.append(sim.debt_interest_rate())
        self.assertLess(rates[0], rates[1])


if __name__ == "__main__":
    unittest.main()
