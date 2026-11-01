"""An ask that employers do not buy at rests at the wage floor (what an hour is worth to the household in other uses),
however many years the hours stay unsold; the floor, not the cut, is what holds it."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import asks
from sim.labour.market.records import MarketState

RESERVATION = 1.0
FLOOR = 0.6


class AskRestsAtTheFloor(unittest.TestCase):
    def test_the_ask_stops_at_the_floor_when_almost_every_hour_stays_unsold(self):
        state = MarketState()
        scales = []
        for _ in range(40):
            asks.record(state, "vale", "digger", 1000.0, 10.0, 0.7, RESERVATION, lowest=FLOOR)
            scales.append(asks.scale_of(state, "vale", "digger"))
        self.assertAlmostEqual(scales[-1], FLOOR / RESERVATION)
        self.assertEqual(scales[-1], scales[-10])

    def test_a_floor_that_rises_lifts_a_resting_ask_with_it(self):
        state = MarketState()
        for _ in range(40):
            asks.record(state, "vale", "digger", 1000.0, 10.0, 0.7, RESERVATION, lowest=FLOOR)
        asks.record(state, "vale", "digger", 1000.0, 10.0, 0.7, RESERVATION, lowest=2.0 * FLOOR)
        self.assertAlmostEqual(asks.scale_of(state, "vale", "digger"), 2.0 * FLOOR / RESERVATION)


if __name__ == "__main__":
    unittest.main()
