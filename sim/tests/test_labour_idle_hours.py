"""`labour_idle_hours.note_idle_hours` leaves the record as the market-by-market loop it replaced did: idle hours by market key in the
markets' order, and the expected sold share moved only in markets with hours offered. Called on written-out markets; no game."""
QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy import households_work
from sim.economy.labour_idle_hours import market_keys, note_idle_hours, sold_shares


def plain_close(expected, trades, areas, hired, idle):
    """The loop `year_labour.clear_labour` ran over the cleared markets."""
    hours_idle = {}
    for trade, area, hired_hours, idle_hours in zip(trades, areas, hired.tolist(), idle.tolist()):
        key = trade + "|" + area
        hours_idle[key] = idle_hours
        if hired_hours + idle_hours > 0.0:
            expected[key] = households_work.smoothed_sold_share(expected.get(key, 1.0), households_work.sold_share(hired_hours, idle_hours))
    return hours_idle


class NoteIdleHours(unittest.TestCase):
    def test_written_out_markets(self):
        trades, areas = ["smith", "smith", "miller", "weaver"], ["work@a", "work@b", "work@a", "work@a"]
        hired, idle = np.array([30.0, 0.0, 0.0, 10.0]), np.array([10.0, 0.0, 0.0, 0.1])
        expected = {"smith|work@a": 0.6, "weaver|work@a": 0.9, "miller|work@a": 0.3}
        before = dict(expected)
        found = note_idle_hours(expected, trades, areas, hired, idle)
        self.assertEqual(found, {"smith|work@a": 10.0, "smith|work@b": 0.0, "miller|work@a": 0.0, "weaver|work@a": 0.1})
        self.assertEqual(expected["smith|work@a"], before["smith|work@a"] + 0.5 * (0.75 - before["smith|work@a"]))
        self.assertEqual(expected["miller|work@a"], 0.3)          # nothing offered: untouched
        self.assertNotIn("smith|work@b", expected)

    def test_random_markets_equal_the_loop(self):
        rng = np.random.default_rng(3)
        for _round in range(50):
            count = int(rng.integers(0, 12))
            trades = ["t%d" % number for number in rng.integers(0, 4, count)]
            areas = ["work@%d" % number for number in range(count)]
            hired = np.where(rng.random(count) < 0.3, 0.0, rng.random(count) * 900.0)
            idle = np.where(rng.random(count) < 0.3, 0.0, rng.random(count) * 300.0)
            history = {"%s|%s" % (trade, area): float(rng.random()) for trade, area in zip(trades, areas) if rng.random() < 0.5}
            plain_history = dict(history)
            self.assertEqual(note_idle_hours(history, trades, areas, hired, idle), plain_close(plain_history, trades, areas, hired, idle))
            self.assertEqual(list(history.items()), list(plain_history.items()))

    def test_sold_shares_is_one_where_nothing_was_offered(self):
        self.assertEqual(sold_shares(np.array([0.0, 5.0, 0.0]), np.array([0.0, 5.0, 4.0])).tolist(), [1.0, 0.5, 0.0])

    def test_market_keys_join_trade_and_area(self):
        self.assertEqual(market_keys(["smith"], ["work@a"]), ["smith|work@a"])
        self.assertEqual(market_keys([], []), [])


if __name__ == "__main__":
    unittest.main()
