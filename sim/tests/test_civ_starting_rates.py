"""Interest and tax rates are each civilisation's own starting state: each civ declares them, and the rules that read them
(the market rate before the economy opens, the arrears rate, the tax in the living cost) are called on the finance module over plain values."""
QUICK_TOPIC = True


import copy
import json
import os
import tempfile
import unittest
from sim.tests import workforce_stand_in
from unittest import mock

from sim.engine import data
from sim.tests import finance_host

BASE_CIVS = ["rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"]
MOD_CIV = "sample_egypt_100bc_e7k2:egypt"
FIELDS = ("starting_interest_rate", "starting_tax_share")


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


def module(civ_fields, **views):
    """The finance module over the civ's fields, with no agent market yet, no standing, no debt and a revenue of a thousand."""
    return finance_host.build(civilisation=dict(civ_fields), revenue_estimate=1000.0, **views)


class EngineUsesCivRatesTests(unittest.TestCase):
    def test_before_the_economy_opens_the_market_rate_is_the_civs_starting_rate(self):
        for name in BASE_CIVS + [MOD_CIV]:
            civ = data.load_civ(name)
            self.assertEqual(module(civ).market_rate(), civ["starting_interest_rate"], name)

    def test_a_civs_base_rate_shifts_the_arrears_rate_one_for_one(self):
        before = module({"starting_interest_rate": 0.05}).debt_interest_rate()
        after = module({"starting_interest_rate": 0.15}).debt_interest_rate()
        self.assertAlmostEqual(after - before, 0.1)

    def test_a_dearer_starting_rate_makes_arrears_dearer(self):
        rates = [module({"starting_interest_rate": value}).debt_interest_rate() for value in (0.05, 0.40)]
        self.assertLess(rates[0], rates[1])

    def test_tax_bite_follows_the_civs_tax_share(self):
        costs = {share: module({"starting_tax_share": share}).living_cost()
                 for share in (0.0, 0.3)}
        self.assertEqual(costs[0.0], 0.0)
        self.assertAlmostEqual(costs[0.3], 0.3 * 1000.0)


if __name__ == "__main__":
    unittest.main()
