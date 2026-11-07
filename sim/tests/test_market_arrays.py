"""The market memory's stores are arrays by (good, area) id that answer like the dictionaries they replace."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.economy.market_arrays import FLOAT, INTEGER, TEXT, MarketIds, MarketStore, split_key
from sim.economy.market_memory import PRICE_REMEMBERED, PRICE_SMOOTHED_TRADE, MarketMemory
from sim.economy.types import QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE


class SplitKeyTests(unittest.TestCase):
    def test_a_key_splits_at_its_first_separator(self):
        self.assertEqual(split_key("grain|a|b"), ("grain", "a|b"))


class MarketStoreTests(unittest.TestCase):
    def test_set_get_pop_and_contains_answer_like_a_dictionary(self):
        store = MarketStore(MarketIds())
        store["grain|a"] = 2.5
        self.assertEqual((store.get("grain|a"), store.get("grain|b"), store.get("grain|b", 7.0), "grain|a" in store, len(store)),
                         (2.5, None, 7.0, True, 1))
        self.assertEqual((store.pop("grain|a"), store.pop("grain|a", None), len(store)), (2.5, None, 0))

    def test_a_store_grows_past_its_first_capacity_and_keeps_every_figure(self):
        store = MarketStore(MarketIds())
        expected = {f"good{good}|area{area}": float(good * 100 + area) for good in range(30) for area in range(25)}
        store.update(expected)
        self.assertEqual(dict(store.items()), expected)

    def test_iteration_is_in_sorted_key_order_whatever_order_they_came_in(self):
        keys = [f"g{number}|a" for number in range(12)]
        random.Random(3).shuffle(keys)
        store = MarketStore(MarketIds(), INTEGER, {key: 1 for key in keys})
        self.assertEqual(list(store), sorted(keys))

    def test_a_text_store_holds_strings_and_an_integer_store_integers(self):
        text = MarketStore(MarketIds(), TEXT, {"a|x": "bid", "b|x": "ask"})
        count = MarketStore(MarketIds(), INTEGER, {"a|x": 0})
        self.assertEqual((text.get("b|x"), text.get("c|x"), count.get("a|x"), type(count.get("a|x"))), ("ask", None, 0, int))

    def test_gather_lays_the_store_over_another_order_of_names(self):
        ids = MarketIds()
        store = MarketStore(ids, FLOAT, {"grain|north": 1.0, "wine|south": 2.0})
        block = store.gather(ids.rows_of(["wine", "salt", "grain"]), ids.columns_of(["south", "north", "east"]))
        expected = np.full((3, 3), np.nan)
        expected[0, 0] = 2.0
        expected[2, 1] = 1.0
        np.testing.assert_array_equal(np.nan_to_num(block, nan=-1.0), np.nan_to_num(expected, nan=-1.0))

    def test_add_to_all_moves_only_present_figures(self):
        store = MarketStore(MarketIds(), INTEGER, {"a|x": 0, "b|x": 3})
        store.add_to_all(1)
        self.assertEqual(dict(store.items()), {"a|x": 1, "b|x": 4})


class MemoryOverArraysTests(unittest.TestCase):
    def test_price_kinds_by_good_agree_with_the_kind_of_each_market(self):
        rng = random.Random(5)
        memory = MarketMemory()
        for good in ("a", "b", "c", "d_e", "d"):
            for area in ("x", "y", "z"):
                key = f"{good}|{area}"
                if rng.random() < 0.8:
                    memory.prices[key] = rng.random() + 0.1
                if rng.random() < 0.5:
                    memory.trade_age[key] = rng.randrange(3)
                if rng.random() < 0.4:
                    memory.quote_kinds[key] = rng.choice([QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE])
        expected = {}
        for key in sorted(memory.prices):
            good, kind = key.split("|")[0], memory.price_kind(key)
            if expected.get(good) != PRICE_SMOOTHED_TRADE and (kind == PRICE_SMOOTHED_TRADE or good not in expected):
                expected[good] = kind
        self.assertEqual(memory.price_kinds_by_good(), expected)

    def test_a_market_that_never_cleared_has_no_age_and_the_years_go_by_for_the_rest(self):
        memory = MarketMemory(prices={"a|x": 1.0, "b|x": 1.0}, trade_age={"a|x": 0})
        memory.note_trading(["b|x"])
        self.assertEqual((memory.trade_age.get("a|x"), memory.trade_age.get("b|x"), memory.price_kind("a|x")),
                         (1, 0, PRICE_REMEMBERED))

    def test_the_record_round_trips_with_plain_numbers(self):
        memory = MarketMemory(prices={"a|x": 1.5}, trade_age={"a|x": 2}, quote_kinds={"a|x": QUOTE_OPENING_ESTIMATE},
                              wages={"smith|x": 0.2})
        record = memory.to_record()
        self.assertEqual((type(record["trade_age"]["a|x"]), record["prices"], record["wages"]), (int, {"a|x": 1.5}, {"smith|x": 0.2}))
        self.assertEqual(MarketMemory.from_record(record), memory)

    def test_a_trade_is_held_when_any_area_pays_it(self):
        memory = MarketMemory(wages={"smith|x": 0.2})
        self.assertEqual((memory.holds_wage_for("smith"), memory.holds_wage_for("baker")), (True, False))
        memory.wages.clear()
        self.assertFalse(memory.holds_wage_for("smith"))


if __name__ == "__main__":
    unittest.main()
