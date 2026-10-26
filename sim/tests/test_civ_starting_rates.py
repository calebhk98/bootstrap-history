"""Interest and tax rates are each civilisation's own starting state: each civ declares them, and the rules that read them
(the market rate before the economy opens, the arrears rate, the tax in the living cost) are called on a stub game."""
QUICK_TOPIC = True


import copy
import json
import os
import types
import tempfile
import unittest
from unittest import mock

from sim.engine import data
from sim.engine.economy_capital_market import CapitalMarketMixin
from sim.engine.economy_credit import CreditMixin

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


def stub_game(civ_fields, **overrides):
    """What the rate rules read: the civ's fields, no agent market yet, a household with no standing, no debt."""
    household = types.SimpleNamespace(capital=0.0)
    game = types.SimpleNamespace(
        reputation=0.0, civ=dict(civ_fields), economy=types.SimpleNamespace(agent_rate=lambda: None), price_index=1.0,
        state=types.SimpleNamespace(household=household), effect_values=lambda _effect: [],
        revenue=lambda: 1000.0, upkeep=lambda: 0.0, labour=types.SimpleNamespace(wage_bill=lambda: 0.0),
        household_bill_per_person=lambda: 0.0, dependants_cost=lambda: 0.0,
        DEBT_RATE_REPUTATION_DISCOUNT_CAP=CreditMixin.DEBT_RATE_REPUTATION_DISCOUNT_CAP,
        DEBT_RATE_REPUTATION_SCALE=CreditMixin.DEBT_RATE_REPUTATION_SCALE,
        LIVING_COST_STATUS_PER_CAPITAL=CreditMixin.LIVING_COST_STATUS_PER_CAPITAL,
        LIVING_COST_APPEARANCES_SHARE_OF_ROOM=CreditMixin.LIVING_COST_APPEARANCES_SHARE_OF_ROOM)
    game.market_rate = lambda: CapitalMarketMixin.market_rate(game)
    for name, value in overrides.items():
        setattr(game, name, value)
    return game


class EngineUsesCivRatesTests(unittest.TestCase):
    def test_before_the_economy_opens_the_market_rate_is_the_civs_starting_rate(self):
        for name in BASE_CIVS + [MOD_CIV]:
            civ = data.load_civ(name)
            self.assertEqual(CapitalMarketMixin.market_rate(stub_game(civ)), civ["starting_interest_rate"], name)

    def test_a_civs_base_rate_shifts_the_arrears_rate_one_for_one(self):
        before = CreditMixin.debt_interest_rate(stub_game({"starting_interest_rate": 0.05}))
        after = CreditMixin.debt_interest_rate(stub_game({"starting_interest_rate": 0.15}))
        self.assertAlmostEqual(after - before, 0.1)

    def test_a_dearer_starting_rate_makes_arrears_dearer(self):
        rates = [CreditMixin.debt_interest_rate(stub_game({"starting_interest_rate": value})) for value in (0.05, 0.40)]
        self.assertLess(rates[0], rates[1])

    def test_tax_bite_follows_the_civs_tax_share(self):
        costs = {share: CreditMixin.living_cost(stub_game({"starting_tax_share": share}))
                 for share in (0.0, 0.3)}
        self.assertEqual(costs[0.0], 0.0)
        self.assertAlmostEqual(costs[0.3], 0.3 * 1000.0)


if __name__ == "__main__":
    unittest.main()
