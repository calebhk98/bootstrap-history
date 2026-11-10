"""What merchants learn from a year (`merchants_news`) on the merchants' columns gives, bit for bit, what the dictionaries gave
(`merchants_news_plain`), and a merchant's column (`merchant_figures.MarketFigures`) answers as the dict it replaced."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.economy import merchants_news
from sim.economy.market_tables import MarketTables
from sim.economy.merchant_figures import MarketFigures
from sim.economy.merchants import Merchant, bind_markets
from sim.tests import merchants_news_plain

GOODS = ("grain", "salt", "wool")
AREAS = tuple("a%d" % number for number in range(7))
KEYS = [(good, area) for good in GOODS for area in AREAS]
SPEED = 0.7


def random_figures(rng, share):
    return {key: rng.uniform(0.5, 30.0) for key in KEYS if rng.random() < share}


def random_year(rng):
    prices = {key: rng.uniform(0.5, 30.0) for key in KEYS if rng.random() < 0.8}
    volumes = {key: rng.uniform(1.0, 90.0) for key in KEYS if rng.random() < 0.8}
    return prices, volumes


def random_merchant(rng, name):
    merchant = Merchant(name, "t", "owner", 100.0, random_figures(rng, 0.6), random_figures(rng, 0.5))
    for key in KEYS:
        if rng.random() < 0.2:
            merchant.price_history[key] = [rng.uniform(1.0, 9.0) for _ in range(rng.randrange(1, 3))]
    return merchant


def same_state(merchant, reference):
    return (dict(merchant.expected_prices) == reference.expected_prices and dict(merchant.expected_volumes) == reference.expected_volumes
            and merchant.price_history == reference.price_history)


class Reference:
    """A merchant's state as the dictionaries held it."""

    def __init__(self, merchant):
        self.expected_prices = dict(merchant.expected_prices)
        self.expected_volumes = dict(merchant.expected_volumes)
        self.price_history = {key: list(value) for key, value in merchant.price_history.items()}


class MoveTowardTests(unittest.TestCase):
    def test_it_moves_a_share_of_the_gap_and_takes_the_value_where_there_was_none(self):
        old = np.array([[2.0, np.nan, 10.0], [np.nan, 4.0, 1.0]])
        values = np.array([6.0, 5.0, 2.0])
        moved = merchants_news.move_toward(old, values, 0.5)
        self.assertEqual(moved.tolist(), [[4.0, 5.0, 6.0], [6.0, 4.5, 1.5]])


class LearnAllTests(unittest.TestCase):
    def test_every_merchant_moves_as_the_dictionaries_moved_it(self):
        for seed in range(25):
            rng = random.Random(seed)
            news = merchants_news.YearNews(*random_year(rng))
            merchants = [random_merchant(rng, "m%d" % number) for number in range(1 + seed % 4)]
            lags = [np.array([rng.choice((0, 0, 1, 2, merchants_news.NOT_HEARD)) for _ in news.price_keys], np.int64)
                    for _ in merchants]
            references = [Reference(merchant) for merchant in merchants]
            for reference, merchant_lags in zip(references, lags):
                merchants_news_plain.learn(reference, news, merchant_lags, SPEED)
            merchants_news.learn_all(merchants, news, lags, SPEED)
            for merchant, reference in zip(merchants, references):
                self.assertTrue(same_state(merchant, reference), seed)

    def test_merchants_indexed_by_one_numbering_and_by_their_own_are_moved_alike(self):
        rng = random.Random(5)
        news = merchants_news.YearNews(*random_year(rng))
        shared = MarketTables()
        first, second, alone = (random_merchant(random.Random(1), name) for name in ("a", "b", "c"))
        for merchant in (first, second):
            bind_markets(merchant, shared)
        lags = [np.zeros(len(news.price_keys), np.int64)] * 3
        merchants_news.learn_all([first, alone, second], news, lags, SPEED)
        self.assertEqual(dict(first.expected_prices), dict(alone.expected_prices))
        self.assertEqual(dict(second.expected_volumes), dict(alone.expected_volumes))


class MarketFiguresTests(unittest.TestCase):
    def test_it_answers_as_the_dict_of_the_same_keys(self):
        figures = MarketFigures(items={("grain", "a1"): 2.0, ("salt", "a0"): 3.5})
        self.assertEqual(figures, {("grain", "a1"): 2.0, ("salt", "a0"): 3.5})
        self.assertEqual(figures.get(("grain", "a1")), 2.0)
        self.assertIsNone(figures.get(("grain", "a0")))
        self.assertEqual(figures.get(("grain", "a0"), 9.0), 9.0)
        self.assertIn(("salt", "a0"), figures)
        self.assertNotIn(("salt", "a1"), figures)
        self.assertEqual(len(figures), 2)
        with self.assertRaises(KeyError):
            figures[("wool", "a0")]

    def test_a_removed_figure_and_a_none_are_both_absent(self):
        figures = MarketFigures(items={("grain", "a1"): 2.0, ("salt", "a0"): 3.5})
        del figures[("grain", "a1")]
        figures[("salt", "a0")] = None
        self.assertEqual(dict(figures), {})

    def test_a_nan_cannot_be_stored(self):
        with self.assertRaises(ValueError):
            MarketFigures()[("grain", "a1")] = float("nan")

    def test_take_gives_nan_for_a_row_with_no_figure_or_no_market(self):
        tables = MarketTables()
        figures = MarketFigures(tables, {("grain", "a1"): 2.0})
        row = tables.goods_numbers["grain|a1"]
        taken = figures.take(np.array([row, -1], np.int64))
        self.assertEqual(taken[0], 2.0)
        self.assertTrue(np.isnan(taken[1]))

    def test_a_merchant_made_with_dicts_keeps_them_as_columns_and_assigning_a_dict_replaces_them(self):
        merchant = Merchant("m", "t", "owner", 1.0, {("grain", "a1"): 2.0}, {("grain", "a1"): 7.0})
        self.assertIsInstance(merchant.expected_prices, MarketFigures)
        merchant.expected_prices = {("salt", "a2"): 1.5}
        self.assertEqual(dict(merchant.expected_prices), {("salt", "a2"): 1.5})
        self.assertEqual(dict(merchant.expected_volumes), {("grain", "a1"): 7.0})

    def test_binding_to_a_record_numbering_keeps_the_figures(self):
        merchant = Merchant("m", "t", "owner", 1.0, {("grain", "a1"): 2.0}, {("salt", "a2"): 7.0})
        record_tables = MarketTables()
        bind_markets(merchant, record_tables)
        self.assertIs(merchant.expected_prices.tables, record_tables)
        self.assertEqual(dict(merchant.expected_prices), {("grain", "a1"): 2.0})
        self.assertIn("salt|a2", record_tables.goods_numbers)

    def test_a_renumbered_column_is_refused_until_it_follows(self):
        tables = MarketTables()
        figures = MarketFigures(tables, {("grain", "a1"): 2.0})
        numbering = tables.goods_markets.compacted(np.ones(len(tables.goods_markets), np.bool_))[0]
        tables.install_goods_markets(numbering, tables.goods_table)
        with self.assertRaises(RuntimeError):
            figures.values

    def test_following_a_renumbering_keeps_survivors_and_copies_to_the_new_markets(self):
        tables = MarketTables()
        figures = MarketFigures(tables, {("grain", "a0"): 1.0, ("grain", "a1"): 2.0, ("salt", "a0"): 3.0})
        old = tables.goods_markets
        keep = np.array([name != "grain|a1" for name in old.names], np.bool_)
        numbering, old_to_new = old.compacted(keep)
        numbering.admit(["grain|b0", "grain|b1"])
        new_rows = np.array([numbering.number("grain|b0"), numbering.number("grain|b1")], np.int64)
        old_rows = np.array([old.number("grain|a1"), old.number("grain|a1")], np.int64)
        tables.install_goods_markets(numbering, tables.blank_goods_table(numbering))
        figures.follow(old_to_new, new_rows, old_rows)
        self.assertEqual(dict(figures), {("grain", "a0"): 1.0, ("salt", "a0"): 3.0, ("grain", "b0"): 2.0, ("grain", "b1"): 2.0})


if __name__ == "__main__":
    unittest.main()
