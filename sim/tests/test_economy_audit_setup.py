"""Content ids the economy reads come from the setup, and what a risky trade and a zero yield do."""
import dataclasses
import unittest

from sim.economy import labour
from sim.economy.setup import EconomySetup, TradeSpec


class SetupContentIdTests(unittest.TestCase):
    def test_hunger_need_and_unskilled_trade_are_setup_fields(self):
        defaults = {field.name: field.default for field in dataclasses.fields(EconomySetup)}
        self.assertEqual(defaults["unskilled_trade"], "labourer")
        self.assertEqual(defaults["hunger_need"], "food")


class HungerNeedTests(unittest.TestCase):
    def test_hunger_counts_the_need_the_setup_names(self):
        from sim.tests import economy_fixture
        basket = economy_fixture.basket()
        famine = dataclasses.replace(basket, needs=tuple(  # a floor no harvest can meet
            dataclasses.replace(need, subsistence_per_person=100.0 * need.subsistence_per_person) for need in basket.needs))
        _economy, named_food = economy_fixture.run(economy_fixture.small_setup(basket=famine), years=3)
        _economy, named_other = economy_fixture.run(
            economy_fixture.small_setup(basket=famine, hunger_need=economy_fixture.ORNAMENT), years=3)
        self.assertGreater(sum(named_food[-1].hunger_by_tile.values()), 0.0)
        self.assertEqual(sum(named_other[-1].hunger_by_tile.values()), 0.0)


class DangerPayTests(unittest.TestCase):
    def test_trade_spec_carries_a_fatality_risk_that_defaults_to_none(self):
        self.assertEqual(TradeSpec("miner").fatality_risk_per_year, 0.0)

    def test_a_risky_trade_has_a_higher_reservation_wage(self):
        safe = labour.reservation_wage(100.0, 2000.0, TradeSpec("clerk").fatality_risk_per_year, 20.0)
        risky = labour.reservation_wage(100.0, 2000.0, TradeSpec("miner", 0.0, 0.01).fatality_risk_per_year, 20.0)
        self.assertGreater(risky, safe)


if __name__ == "__main__":
    unittest.main()
