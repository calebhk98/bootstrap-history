"""The merchants' share of household funds reads the capital market's last meeting and nothing else, so pricing a
landed good before the market first meets cannot loop back through society output to the landed price."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine.foreign_traders import ForeignTradersMixin


class FundsBeforeTheMarketMeets(unittest.TestCase):

    def test_no_meeting_means_no_pooled_funds_and_no_call_into_output(self):
        def output_must_not_be_read():
            raise AssertionError("household saving read before the capital market met")
        world = types.SimpleNamespace(_market_record=lambda: None, household_saving=output_must_not_be_read)
        self.assertEqual(ForeignTradersMixin._households_loanable_funds(world), 0.0)

    def test_after_a_meeting_the_households_supply_is_read(self):
        record = types.SimpleNamespace(supply=10.0, supply_by_source={"households": 7.0})
        world = types.SimpleNamespace(_market_record=lambda: record)
        self.assertEqual(ForeignTradersMixin._households_loanable_funds(world), 7.0)


if __name__ == "__main__":
    unittest.main()
