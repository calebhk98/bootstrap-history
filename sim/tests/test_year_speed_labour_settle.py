"""Labour settlement on tables: the pairing kernels give `settlement_limits.pair_fills` bit for bit, and a year's markets settled
from fill columns (`labour_settle_year.settle_year`) leave the book, the ledger and the results as the per-market path did
(`year_labour._result`, `settlement.settle_labour`, `YearLedger.note_settlement`, `note_labour_settled`), on random small years
with short purses, an edge employer and workers who also hire. No game."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.book import Book
from sim.economy import settlement, year_labour
from sim.economy.labour_fills import fills_of, rows_from_objects
from sim.economy.labour_results_table import LabourResults, bought_value, hours_totals
from sim.economy.labour_settle_year import interleave, settle_year
from sim.economy.labour_walk_kernel import fill_slots, grouped_python_sums, market_agents, walk_pairs
from sim.economy.settlement_limits import pair_fills
from sim.economy.types import EDGE_EXTERNAL, EDGE_MINT, Fill, LabourOffer, Transfer
from sim.economy.year_ledger import YearLedger
from sim.labour.api import LabourClearing


def fills_of_quantities(quantities):
    return [Fill("agent", "good", "area", "", quantity, 1.0, "buy") for quantity in quantities]


class WalkPairsTests(unittest.TestCase):
    def test_written_out_markets_pair_as_pair_fills_does(self):
        markets = [([5.0, 4.0, 8.0], [10.0, 3.0, 4.0]), ([1.0], [0.5, 0.25, 0.25, 7.0]), ([2.5, 2.5], [5.0]), ([3.0], []),
                   ([], [2.0]), ([0.1, 0.2, 0.3], [0.3, 0.3])]
        buy_start, sell_start, buys, sells = [0], [0], [], []
        for buy, sell in markets:
            buys.extend(buy)
            sells.extend(sell)
            buy_start.append(len(buys))
            sell_start.append(len(sells))
        pair_start, pair_buy, pair_sell, pair_quantity = walk_pairs(
            numpy.array(buy_start, dtype=numpy.int64), numpy.array(buys), numpy.array(sell_start, dtype=numpy.int64), numpy.array(sells))
        for market, (buy, sell) in enumerate(markets):
            expected = pair_fills(fills_of_quantities(buy), fills_of_quantities(sell))
            first, last = pair_start[market], pair_start[market + 1]
            self.assertEqual([each - buy_start[market] for each in pair_buy[first:last].tolist()], expected[0])
            self.assertEqual([each - sell_start[market] for each in pair_sell[first:last].tolist()], expected[1])
            self.assertEqual(pair_quantity[first:last].tolist(), expected[2])

    def test_random_markets_pair_as_pair_fills_does(self):
        rng = random.Random(5)
        for _round in range(200):
            markets = [([rng.uniform(0.001, 50.0) for _ in range(rng.randint(0, 6))], [rng.uniform(0.001, 50.0) for _ in range(rng.randint(0, 6))])
                       for _ in range(rng.randint(1, 5))]
            buy_start, sell_start, buys, sells = [0], [0], [], []
            for buy, sell in markets:
                buys.extend(buy)
                sells.extend(sell)
                buy_start.append(len(buys))
                sell_start.append(len(sells))
            pair_start, pair_buy, pair_sell, pair_quantity = walk_pairs(
                numpy.array(buy_start, dtype=numpy.int64), numpy.array(buys), numpy.array(sell_start, dtype=numpy.int64), numpy.array(sells))
            for market, (buy, sell) in enumerate(markets):
                expected = pair_fills(fills_of_quantities(buy), fills_of_quantities(sell))
                first, last = pair_start[market], pair_start[market + 1]
                self.assertEqual(pair_quantity[first:last].tolist(), expected[2])
                self.assertEqual([each - buy_start[market] for each in pair_buy[first:last].tolist()], expected[0])
                self.assertEqual([each - sell_start[market] for each in pair_sell[first:last].tolist()], expected[1])


class SmallKernelTests(unittest.TestCase):
    def test_grouped_python_sums_are_sum(self):
        rng = random.Random(6)
        values = [rng.uniform(-1e6, 1e6) * 10 ** rng.randint(-8, 3) for _ in range(40)]
        cuts = [0, 7, 7, 19, 40]
        totals = grouped_python_sums(numpy.array(cuts, dtype=numpy.int64), numpy.array(values))
        self.assertEqual(totals.tolist(), [sum(values[first:last]) for first, last in zip(cuts, cuts[1:])])

    def test_market_agents_list_buyers_then_new_sellers(self):
        # market 0: buyers refs 3, 1; sellers refs 1, 0, 2 (1 is a buyer too); pairs use buyers 0..1 and sellers 0..1
        pair_start = numpy.array([0, 3], dtype=numpy.int64)
        pair_buy, pair_sell = numpy.array([0, 1, 1], dtype=numpy.int64), numpy.array([0, 0, 1], dtype=numpy.int64)
        agent_start, agent_ref, buyer_agent, seller_agent = market_agents(
            pair_start, pair_buy, pair_sell, numpy.array([0, 2], dtype=numpy.int64), numpy.array([3, 1], dtype=numpy.int64),
            numpy.array([0, 3], dtype=numpy.int64), numpy.array([1, 0, 2], dtype=numpy.int64), 4)
        self.assertEqual(agent_ref.tolist(), [3, 1, 0])
        self.assertEqual(agent_start.tolist(), [0, 3])
        self.assertEqual(buyer_agent.tolist(), [0, 1, 1])
        self.assertEqual(seller_agent.tolist(), [1, 1, 2])

    def test_fill_slots_share_a_slot_between_a_market_s_buy_and_sell_of_one_agent(self):
        buy_slot, sell_slot, slot_market, slot_ref = fill_slots(
            numpy.array([0, 2, 3], dtype=numpy.int64), numpy.array([4, 2, 4], dtype=numpy.int64),
            numpy.array([0, 2, 3], dtype=numpy.int64), numpy.array([2, 7, 9], dtype=numpy.int64), 10)
        self.assertEqual(buy_slot.tolist(), [0, 1, 3])
        self.assertEqual(sell_slot.tolist(), [1, 2, 4])
        self.assertEqual(slot_market.tolist(), [0, 0, 0, 1, 1])
        self.assertEqual(slot_ref.tolist(), [4, 2, 7, 4, 9])

    def test_interleave_puts_each_market_s_buys_before_its_sells(self):
        merged = interleave(numpy.array([0, 2, 2, 3], dtype=numpy.int64), numpy.array([1, 2, 3]),
                            numpy.array([0, 1, 3, 3], dtype=numpy.int64), numpy.array([10, 20, 30]))
        self.assertEqual(merged.tolist(), [1, 2, 10, 20, 30, 3])


EMPLOYERS = ["e%d" % number for number in range(7)] + [EDGE_MINT, EDGE_EXTERNAL + ":far"]
WORKERS = ["w%d" % number for number in range(9)]
TRADES = ["plough", "smith"]
AREAS = ["a1", "a2", "a3"]


def random_year(rng):
    """(book, clearings, offers): money for the employers (short for some), a clearing for most (trade, area), offers for most
    markets; some workers also hire."""
    book = Book()
    for name in EMPLOYERS[:-2] + WORKERS:
        book.transfer(Transfer(EDGE_MINT, name, "coin", rng.choice([0.0, rng.uniform(1, 80), rng.uniform(500, 90000)]), "start"))
    clearings, offers = [], []
    for trade in TRADES:
        for area in AREAS:
            if rng.random() < 0.15:
                continue
            hirers = rng.sample(EMPLOYERS + WORKERS[:2], rng.randint(0, 5))
            hired_by = {name: rng.uniform(0.0, 400.0) if rng.random() < 0.9 else 0.0 for name in hirers}
            hired = sum(hired_by.values())
            wage = rng.uniform(0.2, 9.0)
            sellers = rng.sample(WORKERS, rng.randint(0, 6))
            for name in sellers:
                for _repeat in range(2 if rng.random() < 0.1 else 1):
                    offers.append(LabourOffer(name, trade, area, rng.choice([0.0, rng.uniform(10.0, 900.0)]), 1.0))
            clearings.append(LabourClearing(trade=trade, area=area, wage=wage, hours_offered=hired * rng.uniform(0.9, 1.5),
                                            hours_wanted=hired * rng.uniform(0.9, 1.4), hours_hired=hired, hired_by_employer=hired_by))
    rng.shuffle(offers)
    return book, clearings, offers


def old_path(book, ledger, clearings, offers):
    """The per-market path `clear_labour` took before the year was on tables, from the clearings of the core."""
    by_market = {}
    for offer in offers:
        by_market.setdefault((offer.trade, offer.area), []).append(offer)
    for clearing in sorted(clearings, key=lambda each: (each.trade, each.area)):
        result = year_labour._result(clearing, "coin", by_market.get((clearing.trade, clearing.area), ()))
        done = settlement.settle_labour(book, result)
        ledger.note_settlement(done, "wages")
        ledger.note_labour_settled(result, done)


def new_path(book, ledger, clearings, offers):
    fills = fills_of(*rows_from_objects(clearings), offers)
    settle_year(book, ledger, fills, "coin")
    ledger.labour_results = LabourResults(fills, "coin", ledger.labour_results)


def book_state(book):
    record = book.to_record()
    return {name: record[name] for name in ("money", "goods", "gross_money", "gross_goods", "edge_money_volume", "edge_money_net")}


class WholeYearTests(unittest.TestCase):
    def test_random_years_settle_as_the_per_market_path_did(self):
        for seed in range(60):
            old_book, clearings, offers = random_year(random.Random(seed))
            new_book, _clearings, _offers = random_year(random.Random(seed))
            old_ledger = YearLedger()
            new_ledger = YearLedger(book=new_book) if seed % 2 else YearLedger()     # in the game the ledger shares the book
            old_path(old_book, old_ledger, clearings, offers)
            new_path(new_book, new_ledger, clearings, offers)
            self.assertEqual(book_state(old_book), book_state(new_book), seed)
            for name in ("money_out", "wages_in", "hours_sold", "hours_hired", "hours_hired_by_market"):
                self.assertEqual(self.items(getattr(old_ledger, name)), self.items(getattr(new_ledger, name)), (seed, name))
            self.assertEqual(list(old_ledger.labour_results), list(new_ledger.labour_results), seed)
            self.assertEqual(hours_totals(old_ledger.labour_results), hours_totals(new_ledger.labour_results))
            self.assertEqual(bought_value(old_ledger.labour_results, "e1"), bought_value(new_ledger.labour_results, "e1"))

    @staticmethod
    def items(view):
        return [(key, dict(value) if hasattr(value, "items") else value) for key, value in view.items()]


if __name__ == "__main__":
    unittest.main()
