"""A workforce seat's fractional housing places and its school seats by trade survive a save and a load."""

QUICK_TOPIC = True

import unittest

from sim.engine.state import deserialize_state, serialize_state
from sim.workforce.state import WorkforceSeat


class SeatRoundTrip(unittest.TestCase):

    def test_fractional_worker_housing_places_keep_their_fraction(self):
        seat = WorkforceSeat(worker_housing_places=2.5)
        self.assertEqual(deserialize_state(serialize_state(seat), WorkforceSeat).worker_housing_places, 2.5)

    def test_trade_schools_keep_their_trades_and_seats(self):
        seat = WorkforceSeat(trade_schools={"mason": 3.5})
        self.assertEqual(deserialize_state(serialize_state(seat), WorkforceSeat).trade_schools, {"mason": 3.5})


if __name__ == "__main__":
    unittest.main()
