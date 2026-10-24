"""A state with a bigger stated real programme prints more money to pay for it than one with a smaller programme, and one
with no programme prints none. `state_budget.plan_year` is called on a book, a policy and a view built here, no year is run;
what the extra money does to prices is measured by `python3 sim/simulator.py economy-check` (Complaint 389)."""
QUICK_TOPIC = True
import unittest
from types import SimpleNamespace

from sim.economy import state_budget
from sim.economy.accounts import Book
from sim.economy.state_policy import StatePolicy
from sim.economy.types import CurrencySpec, EDGE_MINT, Transfer

COIN = "coin"
STATE = "state:test"
OPENING_SUPPLY = 10000.0
REVENUE = 1000.0


def planned_by(real_spending_target):
    """The state's budget and the money supply after it plans a year with the given real programme."""
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "holder", COIN, OPENING_SUPPLY, "opening"))
    book.transfer(Transfer(EDGE_MINT, STATE, COIN, REVENUE, "opening"))
    record = SimpleNamespace(book=book, currency=CurrencySpec(COIN, "fiat", None, 0.0, STATE, 0.0), cohorts={}, loans=[],
                             loan_requests=[], state_budget=state_budget.StateBudget(revenue=REVENUE))
    setup = SimpleNamespace(currency_id=COIN, state_agent=STATE, trades=(), unskilled_trade="labour",
                            state_policy=StatePolicy(financing_order=("issue",), real_spending_target=real_spending_target))
    view = SimpleNamespace(chained_price_level=lambda money: 1.0, interest_rate=lambda money: 0.05)
    state_budget.plan_year(setup, record, view, [])
    return record.state_budget, book.money_supply(COIN)


class PrintingScaleTests(unittest.TestCase):
    def test_a_bigger_programme_prints_more_and_leaves_more_money(self):
        smaller_budget, smaller_supply = planned_by(0.5 * OPENING_SUPPLY)
        bigger_budget, bigger_supply = planned_by(2.0 * OPENING_SUPPLY)
        self.assertGreater(bigger_budget.issued_total, smaller_budget.issued_total)
        self.assertGreater(bigger_supply, smaller_supply)

    def test_a_programme_of_either_size_prints_something_and_none_prints_nothing(self):
        self.assertEqual(planned_by(0.0)[0].issued_total, 0.0)
        for scale in (0.5, 2.0):
            self.assertGreater(planned_by(scale * OPENING_SUPPLY)[0].issued_total, 0.0)

    def test_the_money_printed_is_the_money_added_to_the_supply(self):
        budget, supply = planned_by(2.0 * OPENING_SUPPLY)
        self.assertAlmostEqual(supply - OPENING_SUPPLY - REVENUE, budget.issued_total)


if __name__ == "__main__":
    unittest.main()
