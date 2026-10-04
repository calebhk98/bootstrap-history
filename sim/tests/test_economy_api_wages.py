"""api.wages_by_trade_weighted weights each trade's remembered wages by last year's hours hired."""
import unittest

from sim.economy import api
from sim.economy.api import Economy, EconomyRecord
from sim.tests import economy_fixture


class WeightedWageTests(unittest.TestCase):
    def setUp(self):
        self.economy, self.outcomes = economy_fixture.run(years=3)

    def test_weighted_wage_lies_within_the_trades_tile_wages(self):
        weighted = api.wages_by_trade_weighted(self.economy)
        tile_wages = api.wages_by_trade(self.economy)
        self.assertTrue(weighted)
        for trade, wage in weighted.items():
            self.assertGreaterEqual(wage, min(tile_wages[trade]) - 1e-9, trade)
            self.assertLessEqual(wage, max(tile_wages[trade]) + 1e-9, trade)

    def test_weighted_wage_equals_the_years_outcome_for_trades_that_hired(self):
        weighted = api.wages_by_trade_weighted(self.economy)
        checked = 0
        for trade, wage in self.outcomes[-1].wages.items():
            hired = sum(hours for key, hours in self.economy.record.hours_hired.items()
                        if key.split("|", 1)[0] == trade)
            if hired > 0.0:
                checked += 1
                self.assertAlmostEqual(weighted[trade], wage, places=9, msg=trade)
        self.assertGreater(checked, 0)

    def test_weighted_wage_survives_a_record_round_trip(self):
        resumed = Economy(self.economy.setup, EconomyRecord.from_record(self.economy.record.to_record()))
        self.assertEqual(resumed.record.hours_hired, self.economy.record.hours_hired)
        self.assertEqual(api.wages_by_trade_weighted(resumed), api.wages_by_trade_weighted(self.economy))


if __name__ == "__main__":
    unittest.main()
