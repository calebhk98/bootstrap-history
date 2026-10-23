"""Bonded hours leave the labour market (Complaint 538): a bonded cohort's owed hours are worked in its creditor's
works, off its offers and off the works' bids, and come off the debt."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import bondage, bondage_hours
from sim.economy.accounts import Book
from sim.economy.types import LabourBid, LabourOffer, Transfer

BONDED = "household:t:0"
FREE = "household:t:1"
CREDITOR = "household:t:2"
WORKS = "producer:creditor_farm"
OTHER_WORKS = "producer:other_farm"
OWNER = {WORKS: CREDITOR, OTHER_WORKS: "household:t:1"}
WAGE = 0.5


def offers(hours=1000.0):
    return [LabourOffer(BONDED, "hand", "area", hours, WAGE), LabourOffer(FREE, "hand", "area", hours, WAGE)]


def bonds(debt=10000.0):
    return {BONDED: {"creditor": CREDITOR, "debt": debt, "years_left": 5.0}}


def place(bids, debt=10000.0, share=0.75, offered=None):
    return bondage_hours.place(bonds(debt), offered or offers(), bids, lambda employer: OWNER.get(employer), share)


class PlacementTests(unittest.TestCase):
    def test_the_owed_share_of_the_hours_is_worked_in_the_creditors_works_not_sold(self):
        placement = place([LabourBid(WORKS, "hand", "area", 2000.0, 1.0)])
        self.assertEqual(placement.hired, {WORKS: {"hand": 750.0}})
        self.assertAlmostEqual(next(offer.hours for offer in placement.offers if offer.worker == BONDED), 250.0)
        self.assertAlmostEqual(placement.bids[0].hours, 1250.0)                 # the works hires that much less on the market
        self.assertAlmostEqual(next(offer.hours for offer in placement.offers if offer.worker == FREE), 1000.0)

    def test_the_hours_come_off_the_debt_at_the_cohorts_reservation_wage(self):
        placement = place([LabourBid(WORKS, "hand", "area", 2000.0, 1.0)])
        self.assertAlmostEqual(placement.value_placed[BONDED], 750.0 * WAGE)

    def test_works_that_are_not_the_creditors_get_none(self):
        placement = place([LabourBid(OTHER_WORKS, "hand", "area", 2000.0, 1.0)])
        self.assertEqual(placement.hired, {})
        self.assertAlmostEqual(next(offer.hours for offer in placement.offers if offer.worker == BONDED), 1000.0)

    def test_works_that_want_fewer_hours_take_what_they_want_and_the_rest_stay_in_the_market(self):
        placement = place([LabourBid(WORKS, "hand", "area", 300.0, 1.0)])
        self.assertEqual(placement.hired, {WORKS: {"hand": 300.0}})
        self.assertAlmostEqual(next(offer.hours for offer in placement.offers if offer.worker == BONDED), 700.0)
        # 750 hours were owed, 300 worked: the creditor takes cash on the other 450 of the 700 sold
        self.assertAlmostEqual(placement.cash_share[BONDED], 450.0 / 700.0)

    def test_no_works_means_the_old_rule_a_cash_share_of_the_wages(self):
        placement = place([])
        self.assertEqual(placement.hired, {})
        self.assertAlmostEqual(placement.cash_share[BONDED], 0.75)

    def test_no_more_hours_than_the_debt_is_worth(self):
        placement = place([LabourBid(WORKS, "hand", "area", 2000.0, 1.0)], debt=100.0)
        self.assertAlmostEqual(placement.hired[WORKS]["hand"], 100.0 / WAGE)
        self.assertAlmostEqual(placement.value_placed[BONDED], 100.0)

    def test_a_trade_or_area_the_works_do_not_bid_for_takes_none(self):
        self.assertEqual(place([LabourBid(WORKS, "smith", "area", 2000.0, 1.0)]).hired, {})
        self.assertEqual(place([LabourBid(WORKS, "hand", "elsewhere", 2000.0, 1.0)]).hired, {})

    def test_hired_hours_are_booked_as_the_creditors_works_hired_hours(self):
        placement = place([LabourBid(WORKS, "hand", "area", 2000.0, 1.0)])
        hired = {WORKS: {"hand": 100.0}}
        bondage_hours.deliver(hired, placement)
        self.assertAlmostEqual(hired[WORKS]["hand"], 850.0)


class ServiceTests(unittest.TestCase):
    def record(self, debt=1000.0):
        record = types.SimpleNamespace(bondage=bonds(debt), credit_losses={CREDITOR: debt}, book=Book())
        record.book.transfer(Transfer("edge:legacy", BONDED, "coin", 10000.0, "opening"))
        return record

    def test_hours_worked_for_the_creditor_come_off_the_debt_and_its_loss_without_any_cash(self):
        record = self.record()
        payments = bondage.service(record, "coin", {BONDED: 0.0}, worked_value={BONDED: 400.0}, cash_share={BONDED: 0.0})
        self.assertEqual(payments, [])
        self.assertAlmostEqual(record.bondage[BONDED]["debt"], 600.0)
        self.assertAlmostEqual(record.credit_losses[CREDITOR], 600.0)

    def test_cash_is_taken_only_on_the_hours_that_stayed_in_the_market(self):
        record = self.record()
        payments = bondage.service(record, "coin", {BONDED: 100.0}, worked_value={BONDED: 400.0}, cash_share={BONDED: 0.5})
        self.assertAlmostEqual(sum(payment.amount for payment in payments), 50.0)
        self.assertAlmostEqual(record.bondage[BONDED]["debt"], 1000.0 - 400.0 - 50.0)

    def test_hours_that_work_off_the_whole_debt_end_the_bond(self):
        record = self.record(debt=300.0)
        bondage.service(record, "coin", {BONDED: 0.0}, worked_value={BONDED: 900.0}, cash_share={BONDED: 0.0})
        self.assertEqual(record.bondage, {})


if __name__ == "__main__":
    unittest.main()
