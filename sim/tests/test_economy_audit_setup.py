"""Content ids the economy reads come from the setup, and what a risky trade and a zero yield do."""

QUICK_TOPIC = True

import dataclasses
import types
import unittest

from sim.economy import diagnostics, labour
from sim.economy.households_basket import NeedSpec
from sim.economy.setup import EconomySetup, TradeSpec


class SetupContentIdTests(unittest.TestCase):
    def test_hunger_need_and_unskilled_trade_are_setup_fields(self):
        defaults = {field.name: field.default for field in dataclasses.fields(EconomySetup)}
        self.assertEqual(defaults["unskilled_trade"], "labourer")
        self.assertEqual(defaults["hunger_need"], "food")


class HungerNeedTests(unittest.TestCase):
    def test_hunger_share_counts_the_floor_of_the_need_the_setup_names(self):
        needs = (NeedSpec("food", 250.0, 0.6, (("grain_kg", 1.0),)), NeedSpec("ornament", 10.0, 0.05, (("metal_kg", 1.0),)))
        outcome = types.SimpleNamespace(hunger_by_tile={"farms": 500.0, "town": 500.0})
        names_food = types.SimpleNamespace(basket=types.SimpleNamespace(needs=needs), hunger_need="food")
        names_ornament = types.SimpleNamespace(basket=types.SimpleNamespace(needs=needs), hunger_need="ornament")
        self.assertAlmostEqual(diagnostics.hunger_share(outcome, names_food, 10.0), 1000.0 / 2500.0)
        self.assertAlmostEqual(diagnostics.hunger_share(outcome, names_ornament, 10.0), 1000.0 / 100.0)


class DangerPayTests(unittest.TestCase):
    def test_trade_spec_carries_a_fatality_risk_that_defaults_to_none(self):
        self.assertEqual(TradeSpec("miner").fatality_risk_per_year, 0.0)

    def test_a_risky_trade_has_a_higher_reservation_wage(self):
        safe = labour.reservation_wage(100.0, 2000.0, TradeSpec("clerk").fatality_risk_per_year, 20.0)
        risky = labour.reservation_wage(100.0, 2000.0, TradeSpec("miner", 0.0, 0.01).fatality_risk_per_year, 20.0)
        self.assertGreater(risky, safe)


if __name__ == "__main__":
    unittest.main()
