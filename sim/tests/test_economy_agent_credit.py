"""The agent economy's loanable-funds rate: savings with no borrowers pull it down toward lenders' asks,
more funds lower it, more borrowing raises it, and money lent is money moved, not made (Complaint 389).
Engine-free fixture; each test states a direction, not a figure."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import api as economy_api, credit, credit_idle_rate
from sim.economy.types import FundsOffer, Loan, LoanRequest
from sim.world import capital_market

COIN = "coin"
START_RATE = 0.10


def offer(amount=1000.0, minimum_rate=0.02, lender="lender:a"):
    return FundsOffer(lender, COIN, amount, minimum_rate)


def request(amount=100.0, maximum_rate=0.5, borrower="borrower:a"):
    return LoanRequest(borrower, COIN, amount, maximum_rate, 4.0, 10 * amount, "test")


class SavingsWithNoBorrowersTests(unittest.TestCase):
    def rate(self, funds, last_rate=START_RATE):
        return credit_idle_rate.rate_with_no_borrowers(last_rate, funds)

    def test_the_rate_falls_toward_the_lowest_ask(self):
        rate = self.rate([offer(minimum_rate=0.02)])
        self.assertLess(rate, START_RATE)
        self.assertGreaterEqual(rate, 0.02)

    def test_it_falls_further_each_year_and_never_below_the_ask(self):
        rates = [START_RATE]
        for _year in range(8):
            rates.append(self.rate([offer(minimum_rate=0.02)], rates[-1]))
        self.assertTrue(all(later <= earlier for earlier, later in zip(rates, rates[1:])))
        self.assertGreaterEqual(min(rates), 0.02 - 1e-12)
        self.assertLess(rates[-1], rates[1])

    def test_a_lender_who_asks_more_holds_the_rate_higher(self):
        self.assertLess(self.rate([offer(minimum_rate=0.02)]), self.rate([offer(minimum_rate=0.08)]))

    def test_the_lowest_ask_among_lenders_sets_the_floor(self):
        mixed = self.rate([offer(minimum_rate=0.08, lender="lender:b"), offer(minimum_rate=0.02)])
        self.assertAlmostEqual(mixed, self.rate([offer(minimum_rate=0.02)]))

    def test_no_funds_and_no_borrowers_leave_the_rate_alone(self):
        self.assertEqual(self.rate([]), START_RATE)


class BorrowersAgainstFundsTests(unittest.TestCase):
    def test_borrowers_with_no_savings_are_no_price_so_the_rate_stays(self):
        clearing = credit.clear_with_cause([request()], [], COIN, START_RATE, {})
        self.assertEqual(clearing.rate, START_RATE)
        self.assertEqual(clearing.loans, [])
        self.assertIsNotNone(clearing.cause)

    def test_borrowers_with_a_sky_high_ceiling_and_almost_no_funds_do_not_lift_the_rate_past_the_lenders_ask(self):
        ceiling = 0.2
        clearing = credit.clear_with_cause([request(amount=1000.0, maximum_rate=50.0 * ceiling)],
                                           [offer(amount=1.0, minimum_rate=0.02)], COIN, START_RATE, {}, rate_ceiling=ceiling)
        self.assertLessEqual(clearing.rate, ceiling + 1e-12)
        self.assertLess(clearing.rate, START_RATE)      # the queue is rationed by quantity: the rate moves to the lender's ask, not up
        self.assertGreaterEqual(clearing.rate, 0.02)

    def test_a_glut_of_funds_does_not_hold_the_rate_above_the_lowest_ask(self):
        funds = [offer(amount=1_000_000.0, minimum_rate=0.02)]
        borrowing = [request(amount=100.0, maximum_rate=0.5)]
        _loans, rate, _unmet = credit.clear(borrowing, funds, COIN, 0.45, {})
        self.assertAlmostEqual(rate, 0.02)

    def test_a_rate_held_high_does_not_turn_away_a_borrower_who_would_pay_the_clearing_rate(self):
        funds = [offer(amount=1_000_000.0, minimum_rate=0.02)]
        borrowing = [request(amount=100.0, maximum_rate=0.5), request(amount=100.0, maximum_rate=0.1, borrower="borrower:b")]
        loans, rate, unmet = credit.clear(borrowing, funds, COIN, 0.45, {})
        self.assertEqual(unmet, [])
        self.assertAlmostEqual(sum(loan.principal for loan in loans), 200.0)
        self.assertLess(rate, 0.1)

    def test_scarce_funds_still_let_the_rate_fall_only_by_a_share_of_the_gap(self):
        funds = [offer(amount=50.0, minimum_rate=0.02)]
        borrowing = [request(amount=100.0, maximum_rate=0.5)]
        _loans, rate, _unmet = credit.clear(borrowing, funds, COIN, 0.45, {})
        self.assertGreater(rate, 0.1)

    def test_more_funds_against_the_same_borrowing_clear_at_a_lower_rate(self):
        borrowing = [request(amount=500.0)]
        scarce_funds = [offer(amount=100.0, minimum_rate=0.03)]
        plenty_funds = scarce_funds + [offer(amount=2000.0, minimum_rate=0.01, lender="lender:b")]
        scarce, scarce_rate, _unmet = credit.clear(borrowing, scarce_funds, COIN, None, {})
        plenty, plenty_rate, _unmet = credit.clear(borrowing, plenty_funds, COIN, None, {})
        self.assertLess(plenty_rate, scarce_rate)
        self.assertGreater(sum(loan.principal for loan in plenty), sum(loan.principal for loan in scarce))

    def test_more_borrowing_against_the_same_funds_clears_at_a_higher_rate(self):
        funds = [offer(amount=300.0, minimum_rate=0.01), offer(amount=300.0, minimum_rate=0.05, lender="lender:b")]
        few = credit.clear([request(amount=100.0)], funds, COIN, None, {})[1]
        many = credit.clear([request(amount=100.0), request(amount=500.0, borrower="borrower:b")],
                            funds, COIN, None, {})[1]
        self.assertGreater(many, few)

    def test_a_borrower_pays_the_base_rate_plus_a_premium_never_less(self):
        loans, rate, _unmet = credit.clear([request()], [offer()], COIN, None, {})
        self.assertTrue(loans)
        for loan in loans:
            self.assertGreaterEqual(loan.rate, rate)

    def test_a_borrower_who_cannot_pay_the_rate_is_rationed_not_served(self):
        loans, _rate, unmet = credit.clear([request(maximum_rate=0.001)], [offer(minimum_rate=0.05)], COIN, None, {})
        self.assertEqual(loans, [])
        self.assertEqual(len(unmet), 1)


class CreditRoomTests(unittest.TestCase):
    """What lenders will still advance comes from the funds offered and what the clearing granted or lent."""

    FUNDS = 1000.0

    def met(self, **changes):
        record = dict(funds_offered=self.FUNDS, credit_granted={}, lent_by_borrower={"borrower:a": 100.0})
        record.update(changes)
        return types.SimpleNamespace(record=types.SimpleNamespace(**record))

    def test_there_is_no_room_figure_before_lenders_have_met(self):
        self.assertIsNone(economy_api.credit_room(self.met(funds_offered=0.0), "borrower:a"))

    def test_room_is_what_lenders_will_lend_less_what_others_took_this_year(self):
        self.assertAlmostEqual(economy_api.credit_room(self.met(), "borrower:b"),
                               capital_market.lendable_capacity(self.FUNDS) - 100.0)

    def test_a_borrowers_own_loan_does_not_count_against_its_room(self):
        self.assertAlmostEqual(economy_api.credit_room(self.met(), "borrower:a"), capital_market.lendable_capacity(self.FUNDS))

    def test_a_credit_line_borrower_has_what_the_clearing_granted_it(self):
        self.assertEqual(economy_api.credit_room(self.met(credit_granted={"borrower:l": 42.0}), "borrower:l"), 42.0)


class LoansMoveMoneyTests(unittest.TestCase):
    def test_a_loan_moves_money_from_lender_to_borrower_and_makes_none(self):
        loan = Loan("loan-1", "lender:a", "borrower:a", COIN, 50.0, rate=0.05, years_left=4.0, issued_year=0)
        moved = credit.disbursements([loan])
        self.assertEqual([(each.payer, each.payee, each.currency, each.amount) for each in moved],
                         [("lender:a", "borrower:a", COIN, 50.0)])


if __name__ == "__main__":
    unittest.main()
