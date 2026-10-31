"""Hands that walked into a trade needing no training since the clearing lower what the next one expects to earn
there: the wage slides down the employers' bids as the hands arrive."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import aptitude, expectations, trades
from sim.labour.market.records import Clearing, MarketState, YearInputs

AREA = "plain"
HOURS = 1000.0
SUBSISTENCE = 500.0


def _inputs():
    specs = trades.trade_specs({"digger": {"family": "earth", "training_years": 0, "difficulty": -3.0, "fallback": True}})
    return YearInputs(trades=specs, bids=[], subsistence_per_worker_year={AREA: SUBSISTENCE},
                      hours_per_worker_year=HOURS, discount_rate=0.03, career_years=40.0)


def _clearing():
    """One digger sold his hours at the dearest of four bids of one worker's hours each."""
    return {(AREA, "digger"): Clearing(
        trade="digger", area=AREA, wage=40.0, hours_offered=HOURS, hours_wanted=4 * HOURS, hours_hired=HOURS,
        hired_by_employer={}, paid_by_employer={}, average_wage=40.0, target_wage=40.0, hours_held=HOURS,
        demand=((40.0, HOURS), (30.0, HOURS), (20.0, HOURS), (10.0, HOURS)))}


def _state(diggers):
    bands = aptitude.band_count()
    return MarketState(workers={AREA: {"digger": [diggers / bands] * bands}})


class ArrivalsGraduationIncomeTests(unittest.TestCase):
    def _income(self, diggers):
        return expectations.income_at_graduation(_state(diggers), _inputs(), _clearing(), AREA, "digger", [1.0])

    def test_no_arrivals_leaves_the_wage_the_market_cleared_at(self):
        self.assertGreater(self._income(1.0), 30.0 * HOURS)

    def test_two_arrivals_move_the_wage_down_the_bids_and_fill_part_of_the_shortage(self):
        # three diggers meet the bids at (10 + 20) / 2 = 15 an hour; a third of the shortage is left
        reservation = SUBSISTENCE / HOURS
        expected = SUBSISTENCE + (15.0 - reservation) * HOURS / 3.0
        self.assertAlmostEqual(self._income(3.0), expected)


if __name__ == "__main__":
    unittest.main()
