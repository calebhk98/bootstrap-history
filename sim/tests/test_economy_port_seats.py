"""Complaints/668: the seat's year in the clearing is kept per material and read back as an outlook. The functions are
called on a stand-in economy that holds what the clearing left in the seat's account; no game is built."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import concern_sales
from sim.markets import port_seats


def stand_in(unsold, price=50.0):
    area_map = types.SimpleNamespace(area_of=lambda good, tile: "area", goods=lambda: ["acid", "salt"])
    view = types.SimpleNamespace(price=lambda good, area: price)
    economy = types.SimpleNamespace(area_map=area_map, view=lambda: view)
    holdings = {"goods": {good: {"tile": units} for good, units in unsold.items()}}
    return economy, mock.patch.object(port_seats.economy_api, "account_holdings", lambda eco, seat: holdings)


class RecordYearTests(unittest.TestCase):
    def test_a_seat_that_offered_far_more_than_buyers_took_is_recorded_as_paid_for_what_cleared(self):
        economy, patched = stand_in({"acid": 990.0})
        with patched:
            kept = port_seats.record_year(economy, {"seat": ("tile", {"acid": 1000.0})}, {"seat": 10.0}, 2.0)
        offered, sold, proceeds = kept["seat"]["acid"]
        self.assertEqual((offered, sold), (1000.0, 10.0))
        self.assertAlmostEqual(proceeds, 20.0)   # the units of money the account held, in coin

    def test_nothing_taken_records_no_sale_and_no_money(self):
        economy, patched = stand_in({"acid": 1000.0})
        with patched:
            kept = port_seats.record_year(economy, {"seat": ("tile", {"acid": 1000.0})}, {}, 2.0)
        self.assertEqual(kept["seat"]["acid"], [1000.0, 0.0, 0.0])


class OutlookTests(unittest.TestCase):
    def test_the_seats_record_answers_before_the_markets(self):
        economy, _ = stand_in({})
        taken = port_seats.outlook(economy, {"seat": {"acid": [1000.0, 10.0, 500.0]}}, "seat", "acid", 1000.0)
        self.assertEqual(taken.basis, concern_sales.CLEARED_LAST_YEAR)
        self.assertAlmostEqual(taken.share, 0.01)

    def test_a_seat_with_no_record_is_bound_by_what_buyers_took_and_still_wanted(self):
        economy, _ = stand_in({})
        record = {"sold": 15.0, "unsold": 900.0, "unmet": 5.0}
        with mock.patch.object(port_seats.economy_api, "market_record", lambda eco, good: record):
            taken = port_seats.outlook(economy, {}, "seat", "acid", 1000.0)
        self.assertEqual(taken.basis, concern_sales.BUYERS_LAST_YEAR)
        self.assertAlmostEqual(taken.share, 0.02)

    def test_a_good_the_economy_does_not_trade_has_no_outlook(self):
        economy, _ = stand_in({})
        self.assertIsNone(port_seats.outlook(economy, {}, "seat", "mithril", 1000.0))


if __name__ == "__main__":
    unittest.main()
