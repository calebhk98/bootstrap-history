"""Downward-rigid wages, one function each: a held hour keeps its contracted wage, only new hires clear at the market
(Complaints 473, 608; Eurace Firm_update_wage_offer, Household_receive_wage, Household_read_application_rejection_update_wage_reservation)."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing
from sim.labour.market.records import Bid

RESERVATION = 1.0
OFFERED = 1000.0


class ContractedWage(unittest.TestCase):
    def test_a_held_hour_keeps_its_contract_when_the_market_wage_is_lower(self):
        self.assertEqual(clearing.contracted_wage(contract=5.0, market=2.0, best_maximum=9.0), 5.0)

    def test_a_held_hour_keeps_its_contract_when_the_market_wage_is_higher(self):
        self.assertEqual(clearing.contracted_wage(contract=3.0, market=4.0, best_maximum=9.0), 3.0)

    def test_the_contract_is_paid_only_up_to_the_employers_best_maximum(self):
        self.assertEqual(clearing.contracted_wage(contract=5.0, market=2.0, best_maximum=4.0), 4.0)

    def test_an_employer_without_a_contract_pays_the_market_wage(self):
        self.assertEqual(clearing.contracted_wage(contract=None, market=2.0, best_maximum=9.0), 2.0)


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


class RaisedMarketWage(unittest.TestCase):
    def test_a_bid_under_the_new_market_wage_but_over_its_contract_is_still_wanted_for_the_hours_held(self):
        bids = [Bid("mill", "digger", "vale", 100.0, 3.5)]
        wanted, _paid, _ranks, wanted_to_keep = clearing.eligible_bids(bids, 4.0, {"mill": 3.0})
        self.assertEqual((wanted, wanted_to_keep), ({}, {"mill": 100.0}))

    def test_a_bid_under_its_contract_and_under_the_market_wage_is_not_wanted(self):
        bids = [Bid("mill", "digger", "vale", 100.0, 2.5)]
        _wanted, _paid, _ranks, wanted_to_keep = clearing.eligible_bids(bids, 4.0, {"mill": 3.0})
        self.assertEqual(wanted_to_keep, {})


class PayByEmployer(unittest.TestCase):
    def test_hours_kept_are_paid_the_contract_and_hours_hired_new_the_market_wage(self):
        paid, reported = clearing.pay_by_employer(
            kept={"mill": 60.0}, hired={"mill": 100.0}, contracts={"mill": 5.0}, new_paid={"mill": 2.0}, market=2.0,
            best_maximum={"mill": 9.0})
        self.assertAlmostEqual(paid["mill"], (60.0 * 5.0 + 40.0 * 2.0) / 100.0)
        self.assertAlmostEqual(reported, paid["mill"])

    def test_the_reported_wage_is_the_hours_weighted_mean_over_employers(self):
        _paid, reported = clearing.pay_by_employer(
            kept={"mill": 100.0, "farm": 0.0}, hired={"mill": 100.0, "farm": 100.0}, contracts={"mill": 4.0},
            new_paid={"farm": 2.0}, market=2.0, best_maximum={"mill": 9.0, "farm": 9.0})
        self.assertAlmostEqual(reported, 3.0)

    def test_with_nobody_hired_the_reported_wage_is_the_market_wage(self):
        self.assertEqual(clearing.pay_by_employer({}, {}, {}, {}, 2.0, {})[1], 2.0)


if __name__ == "__main__":
    unittest.main()
