"""The merchant table's year kernels give what the per-merchant functions gave: the credit requests of every merchant at once
(`merchants_credit_batch.credit_requests` against `merchants_credit.credit_request`), the settlement of every merchant
(`merchants.close_all` against `merchants.close_year`), the news every merchant hears (`merchant_year_kernels.hear_all`
against the dictionary loop of `merchants_transit.heard`) and the table's rows against the merchants made alone."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.book import Book
from sim.economy import merchant_year_kernels, merchants, merchants_book, merchants_credit, merchants_credit_batch, merchants_transit
from sim.economy.market_tables import MarketTables
from sim.economy.merchant_table import MerchantTable
from sim.economy.merchants import Merchant
from sim.economy.types import EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Transfer
from sim.tests.test_year_speed_merchants import SPECS, random_world

SEEDS = 25


def funded_book(held, cash, agent="m1"):
    book = Book()
    if cash > 0.0:
        book.transfer(Transfer(EDGE_MINT, agent, "coin", cash, "opening coin"))
    for (good, tile), quantity in held.items():
        book.move(GoodsMove(EDGE_PRODUCTION, agent, good, tile, quantity, "stock"))
    return book


class CreditBatchTests(unittest.TestCase):
    def test_every_merchants_request_is_the_request_it_asks_alone(self):
        asked = 0
        for seed in range(SEEDS):
            who, view, carriage, area_map, held, _shares = random_world(seed)
            cash = random.Random(seed).choice((0.0, 50.0, 3000.0))
            tables = MarketTables()
            merchants.put_merchant({}, who, tables)
            book = funded_book(held, cash)
            route = merchants_book.route_pass(view, carriage, area_map, SPECS)
            debts = {"m1": random.Random(seed).choice((0.0, 10.0, 500.0))}
            alone = merchants_credit.credit_request(who, view, carriage, area_map, cash, held, SPECS, 0.05, debts["m1"], "coin", route)
            batch = merchants_credit_batch.credit_requests(MerchantTable.of(tables), route, book, debts, "coin", 0.05)
            self.assertEqual(batch, [] if alone is None else [alone], seed)
            asked += alone is not None
        self.assertGreater(asked, 3)


class SettlementTests(unittest.TestCase):
    def test_close_all_settles_as_close_year_did(self):
        paid = 0
        for seed in range(SEEDS):
            who, _view, _carriage, area_map, held, _shares = random_world(seed)
            rng = random.Random(seed)
            who.capital_base = rng.choice((10.0, 500.0, 3000.0))
            cash = rng.choice((0.0, 100.0, 2000.0))
            twin = Merchant("m1", who.home_tile, "owner", who.capital_base)
            twin.expected_prices, twin.expected_volumes = dict(who.expected_prices), dict(who.expected_volumes)
            twin.in_transit = list(who.in_transit)
            tables = MarketTables()
            merchants.put_merchant({}, who, tables)
            book = funded_book(held, cash)
            expected = merchants.close_year(twin, {}, {}, cash, held, area_map.area_of, "coin", 0.05, learned=True)
            got = merchants.close_all(tables, book, area_map, "coin", 0.05)
            self.assertEqual(tuple(got), expected, seed)
            self.assertEqual(who.capital_base, twin.capital_base, seed)
            paid += bool(expected)
        self.assertGreater(paid, 3)


class HearingTests(unittest.TestCase):
    def test_hear_all_keeps_the_history_the_dictionary_loop_kept(self):
        rng = random.Random(5)
        crowd = [Merchant("m%d" % number, "t0", "owner", 1.0) for number in range(3)]
        tables = MarketTables()
        for each in crowd:
            merchants.put_merchant({}, each, tables)
        keys = [("g%d" % number, "area") for number in range(4)]
        tables.admit_goods_markets(["%s|%s" % key for key in keys])
        store = MerchantTable.of(tables)
        reference = {each.agent_id: {} for each in crowd}
        for _year in range(6):
            prices = numpy.array([rng.uniform(1.0, 9.0) for _key in keys])
            lags = numpy.array([[rng.choice((-1, 0, 1, 2, 3)) for _key in keys] for _each in crowd], numpy.int64)
            market_rows = numpy.array([tables.goods_numbers["%s|%s" % key] for key in keys], numpy.int64)
            heard, kept, store.history_key, store.history_starts, store.history_price = merchant_year_kernels.hear_all(
                store.rank_order(), market_rows, prices, lags, store.history_key, store.history_starts, store.history_price)
            for place, each in enumerate(sorted(crowd, key=lambda found: found.agent_id)):
                history = reference[each.agent_id]
                for column, key in enumerate(keys):
                    lag = int(lags[place, column])
                    if lag <= 0:
                        self.assertEqual((bool(kept[place, column]), heard[place, column]), (True, prices[column]))
                        continue
                    past = history.setdefault(key, [])
                    past.append(float(prices[column]))
                    del past[:-(lag + 1)]
                    self.assertEqual(bool(kept[place, column]), len(past) > lag)
                    if len(past) > lag:
                        self.assertEqual(heard[place, column], past[0])
            for each in crowd:
                self.assertEqual(each.price_history, reference[each.agent_id])


class TableRowTests(unittest.TestCase):
    def test_a_merchant_in_a_table_reads_and_writes_what_it_held_alone(self):
        alone = Merchant("m1", "t0", "owner", 7.0, {("g", "a"): 2.0}, {("g", "a"): 3.0})
        alone.in_transit = [merchants_transit.Shipment("g", 4.0, "t1", 2)]
        alone.price_history = {("g", "a"): [1.0, 2.0]}
        tables = MarketTables()
        merchants.put_merchant({}, alone, tables)
        self.assertEqual((alone.capital_base, dict(alone.expected_prices), dict(alone.expected_volumes), alone.price_history),
                         (7.0, {("g", "a"): 2.0}, {("g", "a"): 3.0}, {("g", "a"): [1.0, 2.0]}))
        self.assertEqual([(each.good, each.quantity, each.destination_tile, each.years_left) for each in alone.in_transit],
                         [("g", 4.0, "t1", 2)])
        self.assertEqual(float(MerchantTable.of(tables).capital_base[0]), 7.0)


if __name__ == "__main__":
    unittest.main()
