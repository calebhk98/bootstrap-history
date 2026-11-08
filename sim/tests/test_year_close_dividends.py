"""The close's dividends as posting rows (year_close_dividends.py, year_close_dividend_kernels.py) against `shares.split_dividend` and
`ownership.spread`, the per-producer Python they replace: the same payments, in the same order, to the last bit."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

import numpy as np

from sim.book import Book, InsufficientFunds
from sim.economy import ownership
from sim.economy.types import Transfer
from sim.economy.year_close_sums import python_sum
from sim.economy.year_close_dividends import add_property_income, as_transfers, dividend_plan, post_dividends
from sim.economy.year_close_owners import Participants


def cohort(agent_id, tile, share):
    return SimpleNamespace(agent_id=agent_id, tile=tile, ownership_share=share)


def producer(agent_id, owner):
    return SimpleNamespace(agent_id=agent_id, owner=owner)


def world(shares):
    """Three tiles: A has three cohorts, B has cohorts that own nothing, C has one; and the share register given."""
    cohorts = [cohort("cohort:A:2", "A", 0.2), cohort("cohort:A:0", "A", 0.1), cohort("cohort:A:1", "A", 0.7),
               cohort("cohort:B:0", "B", 0.0), cohort("cohort:B:1", "B", 0.0), cohort("cohort:C:0", "C", 1.0)]
    producers = [producer("farm", "cohort:A:2"), producer("mill", "cohort:B:0"), producer("smithy", "cohort:C:0"),
                 producer("shop", "somebody"), producer("estate", "cohort:A:0"), producer("quarry", "cohort:A:1")]
    record = SimpleNamespace(
        cohorts={each.agent_id: each for each in cohorts}, producers={each.agent_id: each for each in producers},
        capital_markets=SimpleNamespace(shares=shares, capital=SimpleNamespace(funds={"fund:one": object()})))
    columns = SimpleNamespace(ids=tuple(sorted(record.producers)), row={}, owners=lambda: [record.producers[each].owner for each in columns.ids])
    columns.row = {each: position for position, each in enumerate(columns.ids)}
    return record, columns


def old_payments(record, columns, dividend, currency="money"):
    paid = []
    for row, producer_id in enumerate(columns.ids):
        if dividend[row] > 0.0:
            paid.extend(ownership.spread(record, [Transfer(producer_id, columns.owners()[row], currency, dividend[row], "dividend")]))
    return paid


class DividendRowsTests(unittest.TestCase):
    def check(self, shares, dividend):
        record, columns = world(shares)
        dividend = np.array(dividend)
        participants = Participants()
        pay_rows = np.nonzero(dividend > 0.0)[0]
        plan = dividend_plan(record, columns, dividend, pay_rows, participants)
        new = as_transfers(plan, [columns.ids[row] for row in plan.row.tolist()], participants, "money")
        self.assertEqual(new, old_payments(record, columns, dividend.tolist()))
        return new

    def test_an_owner_cohort_dividend_is_shared_by_ownership_share_over_its_tile(self):
        paid = self.check({}, [10.0, 7.0, 3.0, 5.0, 1.0, 2.0])
        self.assertEqual([each.payee for each in paid if each.payer == "estate"], ["cohort:A:0", "cohort:A:1", "cohort:A:2"])

    def test_a_tile_whose_cohorts_own_nothing_and_an_owner_that_is_no_cohort_keep_the_payment_whole(self):
        paid = self.check({}, [0.0, 0.0, 4.0, 0.0, 6.0, 0.0])
        self.assertEqual([(each.payer, each.payee, each.amount) for each in paid],
                         [("mill", "cohort:B:0", 4.0), ("shop", "somebody", 6.0)])

    def test_holders_of_shares_are_paid_their_part_first_and_the_rest_goes_to_the_owner_tile(self):
        shares = {"farm": {"cohort:C:0": 0.25, "fund:one": 0.125, "stranger": 0.3, "cohort:B:1": 1e-12},
                  "mill": {"cohort:A:0": 0.999999999999}}
        paid = self.check(shares, [0.0, 10.0, 0.7, 0.0, 0.0, 0.0])
        self.assertEqual([each.purpose for each in paid if each.payer == "farm"][:2], ["dividend on shares"] * 2)

    def test_a_dividend_wholly_owned_by_holders_leaves_nothing_for_the_owner(self):
        paid = self.check({"farm": {"cohort:C:0": 0.6, "cohort:B:1": 0.4}}, [0.0, 3.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual([each.payee for each in paid], ["cohort:B:1", "cohort:C:0"])

    def test_a_producer_with_a_register_of_holders_none_eligible_pays_its_owner_the_whole_dividend(self):
        paid = self.check({"smithy": {"stranger": 0.5}}, [0.0, 0.0, 0.0, 0.0, 0.0, 8.0])
        self.assertEqual([(each.payee, each.amount) for each in paid], [("cohort:C:0", 8.0)])

    def test_a_dividend_of_dust_with_holders_is_dropped_as_the_python_drops_it(self):
        paid = self.check({"smithy": {"stranger": 0.5, "cohort:A:0": 0.5}}, [0.0, 0.0, 0.0, 0.0, 0.0, 1e-12])
        self.assertEqual(len(paid), 1)


def funded_book(money_of):
    book = Book()
    for agent, amount in money_of.items():
        book.transfer(Transfer("edge:mint", agent, "money", amount, "seed"))
    return book


class PostDividendsTests(unittest.TestCase):
    def posted(self, money_of, shares):
        record, columns = world(shares)
        dividend = np.array([0.0, 10.0, 0.0, 0.0, 0.0, 4.0])
        participants = Participants()
        plan = dividend_plan(record, columns, dividend, np.nonzero(dividend > 0.0)[0], participants)
        by_rows = funded_book(money_of)
        by_objects = funded_book(money_of)
        post_dividends(by_rows, "money", plan, columns.ids, participants)
        by_objects.transfer_many(old_payments(record, columns, dividend.tolist()))
        return by_rows, by_objects

    def test_the_batch_leaves_the_book_as_the_objects_would_with_the_same_numbering(self):
        by_rows, by_objects = self.posted({"farm": 10.0, "smithy": 4.0}, {"farm": {"cohort:C:0": 0.25}})
        self.assertEqual(by_rows.numbering_state(), by_objects.numbering_state())
        for agent in by_objects.agents():
            self.assertEqual(by_rows.holdings(agent), by_objects.holdings(agent))
        self.assertEqual(by_rows.gross_money(), by_objects.gross_money())

    def test_a_batch_that_overdraws_a_payer_is_refused_whole_with_the_books_own_error(self):
        record, columns = world({})
        dividend = np.array([0.0, 10.0, 0.0, 0.0, 0.0, 4.0])
        participants = Participants()
        plan = dividend_plan(record, columns, dividend, np.nonzero(dividend > 0.0)[0], participants)
        book = funded_book({"farm": 10.0, "smithy": 1.0})
        with self.assertRaises(InsufficientFunds):
            post_dividends(book, "money", plan, columns.ids, participants)
        self.assertEqual(book.balance("farm", "money"), 10.0)


class PythonSumTests(unittest.TestCase):
    def test_it_adds_floats_as_the_builtin_sum_does_on_values_that_cancel(self):
        rng = np.random.default_rng(4)
        for size in (0, 1, 2, 3, 7, 40):
            values = np.concatenate([rng.normal(size=size) * 10.0 ** rng.integers(-8, 16, size=size)])
            self.assertEqual(python_sum(values, size), sum(values.tolist()))
        shares = np.array([0.1, 0.2, 0.3, 1e16, -1e16])
        self.assertEqual(python_sum(shares, 5), sum(shares.tolist()))


class PropertyIncomeTests(unittest.TestCase):
    def test_each_payee_is_added_to_in_the_order_of_the_rows_and_new_payees_enter_in_that_order(self):
        participants = Participants()
        names = ["b", "a", "c"]
        numbers = [participants.of(each) for each in names]
        rows = np.array([5, 1, 3, 1, 5])
        payees = np.array([numbers[0], numbers[1], numbers[0], numbers[2], numbers[1]])
        amounts = np.array([1e16, 1.0, -1e16, 0.25, 1.0])
        income = {"a": 0.1, "z": 2.0}
        expected = dict(income)
        for row, payee, amount in sorted(zip(rows.tolist(), payees.tolist(), amounts.tolist()), key=lambda each: each[0]):
            expected[participants.names[payee]] = expected.get(participants.names[payee], 0.0) + amount
        add_property_income(income, participants, rows, payees, amounts)
        self.assertEqual(list(income.items()), list(expected.items()))


if __name__ == "__main__":
    unittest.main()
