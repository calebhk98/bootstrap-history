"""A starting labour market places each area's people in the trades its work needs: hard trades from
the able bands, the rest in the fallback trade, nobody lost, and a short run from there settles."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import aptitude, opening, records, trades, year

REGISTRY = {
    "digger": {"family": "toil", "training_years": 0},
    "carver": {"family": "craft", "training_years": 3},
    "healer": {"family": "lore", "training_years": 6, "difficulty": 1.2},
}
HOURS = 2000.0


class OpeningTests(unittest.TestCase):
    def setUp(self):
        self.specs = trades.trade_specs(REGISTRY)
        self.state = opening.opening_state(self.specs, {"vale": 1000.0},
                                           {"vale": {"carver": 100 * HOURS, "healer": 20 * HOURS}}, HOURS)

    def test_everyone_is_placed(self):
        self.assertAlmostEqual(records.people_in(self.state), 1000.0)

    def test_needed_trades_are_staffed(self):
        self.assertAlmostEqual(aptitude.band_total(self.state.workers["vale"]["carver"]), 100.0)
        self.assertAlmostEqual(aptitude.band_total(self.state.workers["vale"]["healer"]), 20.0)

    def test_a_hard_trade_is_staffed_from_the_able(self):
        healers = self.state.workers["vale"]["healer"]
        self.assertGreater(healers[-1], 5 * healers[0])

    def test_need_beyond_those_able_is_capped(self):
        state = opening.opening_state(self.specs, {"vale": 100.0}, {"vale": {"healer": 90 * HOURS}}, HOURS)
        self.assertLess(aptitude.band_total(state.workers["vale"]["healer"]), 90.0)
        self.assertAlmostEqual(records.people_in(state), 100.0)

    def test_a_year_runs_from_the_opening(self):
        inputs = records.YearInputs(
            trades=self.specs, bids=[records.Bid("yard", "carver", "vale", 100 * HOURS, 5.0)],
            subsistence_per_worker_year={"vale": HOURS}, hours_per_worker_year=HOURS,
            discount_rate=0.05, career_years=30.0)
        state, report = year.run_year(self.state, inputs)
        self.assertGreater(report.clearing("carver", "vale").hours_hired, 0.0)
        self.assertAlmostEqual(records.people_in(state), 1000.0)


if __name__ == "__main__":
    unittest.main()
