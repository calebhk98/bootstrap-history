"""What a trade is expected to pay on graduation counts the chance of finding work in it."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import expectations, trades
from sim.labour.market.records import Clearing, MarketState, YearInputs

AREA = "plain"
HOURS = 1000.0
SUBSISTENCE = 500.0
WHOLE_BAND = [1.0]


def _inputs():
    specs = trades.trade_specs({"carver": {"family": "craft", "training_years": 2, "difficulty": 0.0}})
    return YearInputs(trades=specs, bids=[], subsistence_per_worker_year={AREA: SUBSISTENCE},
                      hours_per_worker_year=HOURS, discount_rate=0.03, career_years=40.0)


def _clearing(wanted_hours, offered_hours=HOURS, wage=1.0):
    return {(AREA, "carver"): Clearing(
        trade="carver", area=AREA, wage=wage, hours_offered=offered_hours, hours_wanted=wanted_hours,
        hours_hired=min(offered_hours, wanted_hours), hired_by_employer={}, paid_by_employer={},
        average_wage=wage, target_wage=wage)}


class GraduationIncomeTests(unittest.TestCase):
    def _income(self, wanted_hours):
        return expectations.income_at_graduation(MarketState(), _inputs(), _clearing(wanted_hours), AREA, "carver",
                                                 WHOLE_BAND)

    def test_a_glut_that_still_pays_the_wage_is_worth_the_share_of_hands_it_employs(self):
        full = self._income(HOURS)
        half = self._income(0.5 * HOURS)
        self.assertAlmostEqual(half, SUBSISTENCE + 0.5 * (full - SUBSISTENCE))

    def test_no_glut_changes_nothing(self):
        self.assertAlmostEqual(self._income(HOURS), 1.0 * HOURS)


if __name__ == "__main__":
    unittest.main()
