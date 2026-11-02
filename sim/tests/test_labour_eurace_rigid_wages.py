"""The wage the market clears at, one function each: every hour of a trade in an area is paid the one wage
(Complaints 473, 608, 964; Eurace Firm_update_wage_offer, Household_receive_wage, Household_read_application_rejection_update_wage_reservation)."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing
from sim.labour.market.records import Bid

RESERVATION = 1.0
OFFERED = 1000.0


class NewHireWage(unittest.TestCase):
    def test_a_surplus_of_workers_lowers_the_wage_new_hires_clear_at(self):
        bids = [Bid("farm", "digger", "vale", 100.0, 6.0)]
        self.assertLess(clearing.market_wage(5.0, RESERVATION, OFFERED, bids), 5.0 - 0.3 * 4.0 * 0.9)

    def test_a_surplus_does_not_take_new_hires_below_the_ask(self):
        bids = [Bid("farm", "digger", "vale", 100.0, 6.0)]
        self.assertGreaterEqual(clearing.market_wage(5.0, RESERVATION, OFFERED, bids), RESERVATION)

    def test_scarcity_still_raises_the_wage_by_a_share_of_the_gap(self):
        bids = [Bid("farm", "digger", "vale", 2000.0, 6.0)]
        self.assertGreater(clearing.market_wage(2.0, RESERVATION, OFFERED, bids), 2.0)


class EligibleBids(unittest.TestCase):
    def test_a_bid_under_the_market_wage_is_not_wanted_even_for_hours_held(self):
        bids = [Bid("mill", "digger", "vale", 100.0, 3.5)]
        self.assertEqual(clearing.eligible_bids(bids, 4.0), ({}, {}, {}))


if __name__ == "__main__":
    unittest.main()
