"""A producer that keeps losing leaves; capacity with no plant follows use; plant already built is sunk."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.contracts import TERM_LOAN
from sim.economy import entry, producer_exit, producers, producers_close
from sim.economy.types import Loan, Transfer
from sim.tests.economy_fixture import HILLS, ORE
from sim.tests.test_economy_producers import FARM, SMELT, View, farm_view, farmer


def smelter_view(**changes):
    return View({"metal": 0.1, "silver": 0.1, "ore": 1.0, "stone": 1.0}, {"smith": 1.0}, **changes)


class IdleCapacityTests(unittest.TestCase):
    def test_plantless_capacity_whose_runs_would_not_pay_is_shed_at_the_pace_workplaces_change(self):
        # some workplaces still cover their cost, so the producer stays; the rest close no faster than workplaces open
        producer = farmer(capacity_runs=10.0)
        for _year in range(10):
            before = producer.capacity_runs
            result = producers_close.close_year(producer, FARM, 100.0, 50.0, farm_view(0.5), 4.0)
            producer = result.producer
            self.assertFalse(result.exited)
            self.assertLess(producer.capacity_runs, before)
            self.assertGreaterEqual(producer.capacity_runs, (1.0 - producers.OUTPUT_CHANGE_SHARE_PER_YEAR) * before - 1e-9)

    def test_plantless_capacity_whose_runs_would_pay_is_kept_while_it_waits(self):
        # idle for want of inputs or buyers, not of a margin: the hands are kept
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 100.0, 50.0, farm_view(2.0), 4.0)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_plantless_capacity_that_was_all_worked_is_unchanged(self):
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 100.0, 50.0, farm_view(2.0), 10.0)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_idle_sunk_plant_is_not_charged_in_the_loss_test(self):
        view = smelter_view()
        producer = farmer(recipe_id="smelt", capacity_runs=10.0)
        # revenue covers costs and the charge on one run worked, but not on all ten
        self.assertEqual(producers_close.close_year(producer, SMELT, 55.0, 50.0, view, 10.0).producer.years_of_loss, 1)
        self.assertEqual(producers_close.close_year(producer, SMELT, 55.0, 50.0, view, 1.0).producer.years_of_loss, 0)


class ExitTests(unittest.TestCase):
    def test_a_plantless_producer_no_workplace_of_which_pays_exits_in_the_first_year_its_sales_do_not_cover_cost(self):
        view = farm_view(0.001, cash=20.0)
        producer = farmer()
        result = producers_close.close_year(producer, FARM, 3.0, 70.0, view, 1.0)
        producer = result.producer
        self.assertTrue(result.exited)
        self.assertEqual(producer.capacity_runs, 0.0)
        self.assertAlmostEqual(sum(transfer.amount for transfer in result.transfers), 20.0)

    def test_workplaces_that_do_not_pay_close_no_faster_than_workplaces_open(self):
        # the price covers the cost of some workplaces: the producer keeps them and sheds the rest by a
        # quarter of its capacity a year, as the market loses makers without losing the market
        view = farm_view(0.5, cash=20.0)
        producer = farmer(capacity_runs=10.0)
        capacities = []
        for _year in range(producers_close.LOSS_YEARS_BEFORE_EXIT + 3):
            result = producers_close.close_year(producer, FARM, 3.0, 70.0, view, 1.0)
            self.assertFalse(result.exited)
            producer = result.producer
            capacities.append(producer.capacity_runs)
        shed = [after for before, after in zip(capacities, capacities[1:]) if after < before]
        self.assertTrue(shed)
        for before, after in zip(capacities, capacities[1:]):
            self.assertGreaterEqual(after, (1.0 - producers.OUTPUT_CHANGE_SHARE_PER_YEAR) * before - 1e-9)
        self.assertGreater(capacities[-1], 0.0)

    def test_a_loser_whose_runs_still_cover_variable_cost_does_not_exit(self):
        view = farm_view(2.0)
        producer = farmer()
        for _year in range(producers_close.LOSS_YEARS_BEFORE_EXIT + 3):
            result = producers_close.close_year(producer, FARM, 10.0, 100.0, view, 5.0)
            producer = result.producer
            self.assertFalse(result.exited)
        self.assertGreater(producer.capacity_runs, 0.0)

    def test_plant_with_a_positive_variable_margin_is_mothballed_and_wears_by_its_life(self):
        view = View({"metal": 20.0, "silver": 5.0, "ore": 1.0, "stone": 1.0}, {"smith": 1.0})
        producer = farmer(recipe_id="smelt", capacity_runs=10.0, years_of_loss=producers_close.LOSS_YEARS_BEFORE_EXIT)
        result = producers_close.close_year(producer, SMELT, 0.0, 500.0, view, 1.0)
        self.assertFalse(result.exited)
        self.assertAlmostEqual(result.producer.capacity_runs, 9.0)
        self.assertGreater(result.producer.years_of_loss, producers_close.LOSS_YEARS_BEFORE_EXIT)

    def test_a_profitable_producer_is_unaffected(self):
        result = producers_close.close_year(farmer(), FARM, 300.0, 100.0, farm_view(2.0), 10.0)
        self.assertFalse(result.exited)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)
        self.assertEqual(result.producer.years_of_loss, 0)

    def test_a_sliver_of_past_scale_closes_and_a_working_producer_does_not(self):
        sliver = farmer(agent_id="sliver", capacity_runs=0.001, last_runs=10.0)
        working = farmer(agent_id="working", capacity_runs=5.0, last_runs=5.0)
        newcomer = farmer(agent_id="new", capacity_runs=0.0)
        closing = entry.producers_to_close({"sliver": sliver, "working": working, "new": newcomer}, set(), set())
        self.assertEqual(closing, ["new", "sliver"])


class StubBook:
    """The book an exiting producer is settled in: its cash and goods, and a record of what was paid and moved."""

    def __init__(self, cash, goods):
        self.cash, self.goods, self.transfers, self.moves = cash, goods, [], []

    def balance(self, agent, currency):
        return self.cash

    def holdings(self, agent):
        return {"goods": self.goods}

    def transfer_many(self, transfers):
        self.transfers.extend(transfers)

    def move_many(self, moves):
        self.moves.extend(moves)


def exiting(cash, loans, goods=None):
    """A record holding one producer (owned by "owner") with `cash` and `goods`, owing `loans`; ownership.spread is the identity."""
    defaulted = []
    record = types.SimpleNamespace(
        book=StubBook(cash, goods or {}), producers={"producer": types.SimpleNamespace(owner="owner")}, loans=loans,
        credit_losses={}, remembered_defaults={}, worn_runs={}, expansion_runs={}, shares={}, last_dividends={},
        contracts=types.SimpleNamespace(default=lambda borrower, kind: defaulted.append((borrower, kind))))
    return record, defaulted


def exit_with(record, payout):
    spread = []
    with mock.patch.object(producer_exit.ownership, "spread", lambda _record, payments: spread.extend(payments) or payments):
        producer_exit.exit_producer(record, "producer", payout)
    return spread


class ExitBooksTests(unittest.TestCase):
    def test_cash_goods_and_debt_of_an_exiting_producer(self):
        loan = Loan("loan-1", "lender", "producer", "coin", 100.0, 0.05, 5.0, 0.0, arrears=10.0)
        record, defaulted = exiting(40.0, [loan], {ORE: {HILLS: 7.0}})
        spread = exit_with(record, [Transfer("producer", "owner", "coin", 40.0, "dividend")])
        self.assertEqual(spread, [])      # the cash all went to the lender
        self.assertEqual([(each.payee, each.amount) for each in record.book.transfers], [("lender", 40.0)])
        self.assertEqual([(move.receiver, move.quantity) for move in record.book.moves],
                         [("owner", 7.0)])
        self.assertNotIn("producer", record.producers)
        self.assertEqual(defaulted, [("producer", TERM_LOAN)])
        self.assertAlmostEqual(record.credit_losses["lender"], 110.0 - 40.0)
        self.assertAlmostEqual(record.remembered_defaults["producer"], 110.0 - 40.0)

    def test_lenders_are_repaid_before_the_owner(self):
        loan = Loan("loan-1", "lender", "producer", "coin", 50.0, 0.05, 5.0, 0.0)
        record, _defaulted = exiting(100.0, [loan])
        spread = exit_with(record, [Transfer("producer", "owner", "coin", 100.0, "dividend")])
        self.assertEqual([(each.payee, each.amount) for each in record.book.transfers[:1]], [("lender", 50.0)])
        self.assertEqual([(each.payee, each.amount) for each in spread], [("owner", 50.0)])
        self.assertEqual(record.credit_losses, {})


if __name__ == "__main__":
    unittest.main()
