"""Complaint 665: a seat's credit line is a request in the same clearing as every borrower's, and the lenders'
reserve is held out of every offer alike.

Rules called on built inputs: credit_lines.hold_reserve, line_request, split_lines, credit.clear, api.credit_room."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import api, credit, credit_lines
from sim.economy.types import FundsOffer, LoanRequest
from sim.world import capital_market


def plant(borrower, amount, ceiling):
    return LoanRequest(borrower, "coin", amount, ceiling, 80.0, amount, "expand")


def granted_by(loans):
    totals = {}
    for loan in loans:
        totals[loan.borrower] = totals.get(loan.borrower, 0.0) + loan.principal
    return totals


class ReserveTests(unittest.TestCase):
    def test_the_reserve_is_held_out_of_each_offer(self):
        held = credit_lines.hold_reserve([FundsOffer("saver", "coin", 100.0, 0.0)])
        self.assertAlmostEqual(held[0].amount, capital_market.lendable_capacity(100.0))

    def test_a_lender_that_kept_its_reserve_already_is_not_cut_twice(self):
        held = credit_lines.hold_reserve([FundsOffer("bank", "coin", 100.0, 0.0), FundsOffer("saver", "coin", 100.0, 0.0)],
                                         already_reserved=["bank"])
        self.assertEqual(held[0].amount, 100.0)
        self.assertLess(held[1].amount, 100.0)

    def test_total_lent_never_passes_the_lendable_capacity_when_demand_is_greater(self):
        offers = credit_lines.hold_reserve([FundsOffer("saver", "coin", 100.0, 0.0)])
        loans, _rate, _unmet = credit.clear([plant("producer:a", 1000.0, 5.0)], offers, "coin", 0.1, {})
        self.assertLessEqual(sum(loan.principal for loan in loans), capital_market.lendable_capacity(100.0) + 1e-9)


class SeatRequestsAmongOthersTests(unittest.TestCase):
    def clear(self, line_ceiling_rate):
        offers = credit_lines.hold_reserve([FundsOffer("saver", "coin", 100.0, 0.0)])
        seat = credit_lines.line_request("seat", "coin", 30.0, line_ceiling_rate)
        requests = [plant("producer:a", 1000.0, 0.9), plant("producer:b", 1000.0, 0.3), seat]
        return credit.clear(requests, offers, "coin", 0.1, {})

    def test_a_rationed_market_rations_the_seat_by_its_ceiling_like_the_others(self):
        loans, _rate, unmet = self.clear(0.05)
        granted = granted_by(loans)
        self.assertGreater(granted["producer:a"], 0.0)                        # the highest ceiling is served first
        self.assertAlmostEqual(granted.get("seat", 0.0), 0.0)                  # the seat's ceiling is below the rationing point
        self.assertIn("seat", {request.borrower for request in unmet})

    def test_a_seat_that_outbids_a_plant_is_served_ahead_of_it(self):
        offers = credit_lines.hold_reserve([FundsOffer("saver", "coin", 100.0, 0.0)])
        seat = LoanRequest("seat", "coin", 30.0, 2.0, 1.0, 30.0, credit_lines.LINE_PURPOSE)
        loans, _rate, _unmet = credit.clear([plant("producer:a", 1000.0, 0.9), seat], offers, "coin", 0.1, {})
        self.assertAlmostEqual(granted_by(loans)["seat"], 30.0)

    def test_the_request_names_a_ceiling_above_the_market_rate_and_asks_what_the_line_is(self):
        request = credit_lines.line_request("seat", "coin", 30.0, 0.1)
        self.assertEqual(request.amount, 30.0)
        self.assertGreater(request.maximum_rate, 0.1)


class RoomTests(unittest.TestCase):
    def economy(self, **record):
        fields = dict(funds_offered=100.0, lent_by_borrower={}, credit_granted={})
        fields.update(record)
        return types.SimpleNamespace(record=types.SimpleNamespace(**fields))

    def test_the_lines_grants_are_not_booked_as_loans(self):
        offers = credit_lines.hold_reserve([FundsOffer("saver", "coin", 100.0, 0.0)])
        seat = LoanRequest("seat", "coin", 30.0, 2.0, 1.0, 30.0, credit_lines.LINE_PURPOSE)
        loans, _rate, _unmet = credit.clear([seat, plant("producer:a", 1000.0, 0.9)], offers, "coin", 0.1, {})
        booked, granted = credit_lines.split_lines(loans, ["seat"])
        self.assertTrue(all(loan.borrower != "seat" for loan in booked))
        self.assertAlmostEqual(granted["seat"], 30.0)

    def test_a_seat_with_a_line_in_the_clearing_has_the_room_it_was_granted(self):
        economy = self.economy(credit_granted={"seat": 12.0}, lent_by_borrower={"seat": 12.0, "producer:a": 68.0})
        self.assertEqual(api.credit_room(economy, "seat"), 12.0)

    def test_a_seat_granted_nothing_has_no_room_whatever_is_left_to_others(self):
        economy = self.economy(credit_granted={"seat": 0.0}, lent_by_borrower={"producer:a": 10.0})
        self.assertEqual(api.credit_room(economy, "seat"), 0.0)

    def test_a_borrower_with_no_line_request_has_what_the_others_left_of_the_lendable_capacity(self):
        economy = self.economy(lent_by_borrower={"producer:a": 30.0})
        self.assertAlmostEqual(api.credit_room(economy, "other"), capital_market.lendable_capacity(100.0) - 30.0)


if __name__ == "__main__":
    unittest.main()
