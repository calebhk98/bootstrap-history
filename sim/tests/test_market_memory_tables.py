"""The market memory's stores as views of the market tables: each behaves as the dict it replaced, in the dict's order, and the
numbering of the markets survives a save."""
QUICK_TOPIC = True

import copy
import random
import unittest

from sim.economy.market_memory import STORE_NAMES, MarketMemory, written_stamp
from sim.economy.market_memory_follow import follow_goods_markets
from sim.economy.market_areas_follow import _moved

GOODS = ("grain", "iron", "salt")
AREAS = ("a", "b", "c")
COUNT_STORES = ("trade_age", "years_without_bids", "years_without_offers")
KEYS = [good + "|" + area for good in GOODS for area in AREAS]


def memory_and_dicts(**stores):
    """A memory built from the dicts and an independent copy of each dict, the oracle."""
    return MarketMemory(**copy.deepcopy(stores)), copy.deepcopy(stores)


class StoreActsAsDictTests(unittest.TestCase):
    def test_the_stores_list_markets_in_the_order_they_entered(self):
        memory, _ = memory_and_dicts(prices={"iron|a": 2.0, "grain|a": 1.0})
        memory.prices["salt|a"] = 3.0
        self.assertEqual(list(memory.prices), ["iron|a", "grain|a", "salt|a"])

    def test_a_market_that_left_and_came_back_is_last_and_one_overwritten_keeps_its_place(self):
        memory, _ = memory_and_dicts(prices={"iron|a": 2.0, "grain|a": 1.0, "salt|a": 3.0})
        memory.prices.pop("iron|a")
        memory.prices["iron|a"] = 4.0
        memory.prices["grain|a"] = 5.0
        self.assertEqual(list(memory.prices.items()), [("grain|a", 5.0), ("salt|a", 3.0), ("iron|a", 4.0)])

    def test_random_operations_agree_with_a_dict_in_content_and_order(self):
        rng = random.Random(4)
        memory, _ = memory_and_dicts()
        oracles = {name: {} for name in STORE_NAMES}
        for _ in range(600):
            name = rng.choice(STORE_NAMES)
            key = rng.choice(KEYS if name != "wages" else ["smith|l1", "farmer|l1", "farmer|l2"])
            store, oracle = getattr(memory, name), oracles[name]
            figure = ("asking" if rng.random() < 0.5 else "bid") if name == "quote_kinds" else (rng.randrange(5) if name in COUNT_STORES else round(rng.random(), 3))
            action = rng.choice(("set", "set", "pop", "get", "del"))
            if action == "set":
                store[key] = oracle[key] = figure
            elif action == "pop":
                self.assertEqual(store.pop(key, None), oracle.pop(key, None))
            elif action == "get":
                self.assertEqual(store.get(key, -1), oracle.get(key, -1))
            elif key in oracle:
                del store[key]
                del oracle[key]
            self.assertEqual((list(store), len(store)), (list(oracle), len(oracle)), (name, action, key))
        for name in STORE_NAMES:
            self.assertEqual((list(getattr(memory, name).items()), list(getattr(memory, name).values())),
                             (list(oracles[name].items()), list(oracles[name].values())))

    def test_a_store_equals_the_dict_with_its_content(self):
        memory, _ = memory_and_dicts(trade_age={"grain|a": 0})
        self.assertTrue(memory.trade_age == {"grain|a": 0} and memory.trade_age != {"grain|a": 1})

    def test_a_key_without_the_separator_is_a_market_of_the_empty_area(self):
        memory, _ = memory_and_dicts(prices={"k": 1.0})
        self.assertEqual(memory.prices.get("k"), 1.0)

    def test_a_nan_is_refused_not_stored_as_none(self):
        memory, _ = memory_and_dicts()
        with self.assertRaises(ValueError):
            memory.prices["grain|a"] = float("nan")

    def test_a_missing_market_is_a_key_error_and_get_gives_the_default(self):
        memory, _ = memory_and_dicts(prices={"grain|a": 1.0})
        with self.assertRaises(KeyError):
            memory.prices["iron|a"]
        self.assertEqual((memory.prices.get("iron|a"), memory.prices.get("iron|a", 7.0)), (None, 7.0))

    def test_whole_assignment_replaces_the_content_and_marks_the_memory_written(self):
        memory, _ = memory_and_dicts(trade_age={"grain|a": 0, "iron|a": 1})
        before = written_stamp()
        memory.trade_age = {"salt|b": 2}
        self.assertEqual((dict(memory.trade_age), written_stamp() > before), ({"salt|b": 2}, True))

    def test_quote_kinds_read_back_as_text(self):
        memory, _ = memory_and_dicts(quote_kinds={"grain|a": "asking"})
        memory.quote_kinds["iron|a"] = "bid"
        self.assertEqual(list(memory.quote_kinds.items()), [("grain|a", "asking"), ("iron|a", "bid")])

    def test_values_come_back_as_plain_python_numbers(self):
        memory, _ = memory_and_dicts(prices={"grain|a": 1.5}, trade_age={"grain|a": 2})
        self.assertEqual((type(memory.prices["grain|a"]), type(memory.trade_age["grain|a"]), type(memory.prices.values()[0])),
                         (float, int, float))


class ManyAtOnceTests(unittest.TestCase):
    def test_get_many_is_get_for_each_key_for_every_kind_of_store(self):
        memory, _ = memory_and_dicts(prices={"grain|a": 1.5, "iron|a": 2.5}, trade_age={"iron|a": 3}, quote_kinds={"grain|a": "asking"},
                                     wages={"smith|l": 4.0})
        keys = ["iron|a", "unknown|a", "grain|a", "salt|a"]
        for store, default in ((memory.prices, None), (memory.trade_age, 9), (memory.quote_kinds, "none")):
            self.assertEqual(store.get_many(keys, default), [store.get(key, default) for key in keys])
        self.assertEqual(memory.wages.get_many(["smith|l", "smith|m"], 0.0), [4.0, 0.0])

    def test_get_many_of_no_keys_is_empty(self):
        memory, _ = memory_and_dicts()
        self.assertEqual(memory.prices.get_many([], None), [])

    def test_figures_for_reads_a_plain_dict_too(self):
        from sim.economy.market_store import figures_for
        self.assertEqual(figures_for({"a|x": 1.0}, ["a|x", "b|x"], 0.0), [1.0, 0.0])


class NoteTradingTests(unittest.TestCase):
    def test_note_trading_matches_the_dict_rule(self):
        memory, oracle = memory_and_dicts(trade_age={"grain|a": 0, "iron|a": 3})
        memory.note_trading(["salt|a", "iron|a"])
        for key in list(oracle["trade_age"]):
            oracle["trade_age"][key] += 1
        for key in ["salt|a", "iron|a"]:
            oracle["trade_age"][key] = 0
        self.assertEqual(list(memory.trade_age.items()), list(oracle["trade_age"].items()))

    def test_the_trade_age_stamp_moves(self):
        from sim.economy.market_memory import age_and_kind_stamp
        memory, _ = memory_and_dicts()
        before = age_and_kind_stamp()
        memory.note_trading([])
        self.assertGreater(age_and_kind_stamp(), before)


class SaveTests(unittest.TestCase):
    def test_a_saved_memory_loads_with_the_same_stores_order_and_market_numbers(self):
        memory, _ = memory_and_dicts(prices={"salt|b": 1.0, "grain|a": 2.0}, quote_kinds={"grain|a": "asking"}, wages={"smith|l": 3.0})
        memory.prices["iron|c"] = 4.0
        loaded = MarketMemory.from_plain(memory.to_plain())
        self.assertEqual((list(loaded.prices.items()), loaded.quote_kinds, loaded.wages, loaded.tables.state()),
                         (list(memory.prices.items()), memory.quote_kinds, memory.wages, memory.tables.state()))

    def test_the_saved_numbering_is_the_one_the_live_game_had_not_a_re_sort(self):
        memory, _ = memory_and_dicts(prices={"salt|a": 1.0})
        memory.prices["grain|a"] = 2.0
        loaded = MarketMemory.from_plain(memory.to_plain())
        self.assertEqual(loaded.tables.goods_markets.names, ("salt|a", "grain|a"))

    def test_the_plain_form_is_dicts_in_store_order_plus_the_numbering(self):
        memory, _ = memory_and_dicts(prices={"salt|a": 1.0, "grain|a": 2.0})
        plain = memory.to_plain()
        self.assertEqual((list(plain["prices"]), plain["market_ids"]["goods_markets"]), (["salt|a", "grain|a"], ["grain|a", "salt|a"]))

    def test_a_copy_is_independent(self):
        memory, _ = memory_and_dicts(prices={"salt|a": 1.0})
        clone = copy.deepcopy(memory)
        clone.prices["salt|a"] = 9.0
        self.assertEqual((memory.prices["salt|a"], clone.prices["salt|a"]), (1.0, 9.0))


class FollowTests(unittest.TestCase):
    """follow_goods_markets against the dict rule it replaces (`market_areas_follow._moved`)."""

    def moved_both_ways(self, stores, follows, old_ids):
        memory, oracle = memory_and_dicts(**stores)
        follow_goods_markets(memory, follows, old_ids)
        return memory, {name: _moved(figures, follows, old_ids) for name, figures in oracle.items()}

    def test_new_areas_take_the_figures_of_the_old_area_holding_their_anchor_in_the_dicts_order(self):
        stores = {"prices": {"grain|old1": 1.0, "salt|old1": 2.0, "grain|old2": 3.0, "iron|x": 9.0},
                  "trade_age": {"grain|old2": 0, "grain|old1": 4},
                  "quote_kinds": {"grain|old2": "asking"}, "cleared_prices": {"grain|old1": 1.5},
                  "years_without_bids": {"grain|old1": 2}, "usual_prices": {"grain|old1": 1.1, "grain|old2": 3.1}}
        follows = {"grain": {"new1": "old2", "new2": "old1", "new3": "old1"}}
        memory, expected = self.moved_both_ways(stores, follows, {"grain": frozenset(("old1", "old2"))})
        for name, figures in expected.items():
            self.assertEqual(list(getattr(memory, name).items()), list(figures.items()), name)

    def test_a_key_that_is_no_market_of_the_old_areas_stays(self):
        stores = {"prices": {"grain|old1": 1.0, "grain|elsewhere": 5.0}}
        memory, expected = self.moved_both_ways(stores, {"grain": {"new": "old1"}}, {"grain": frozenset(("old1",))})
        self.assertEqual(list(memory.prices.items()), list(expected["prices"].items()))

    def test_an_area_that_keeps_its_id_moves_to_the_end_as_the_dicts_did(self):
        stores = {"prices": {"grain|a": 1.0, "grain|b": 2.0, "salt|a": 3.0}}
        memory, expected = self.moved_both_ways(stores, {"grain": {"a": "a", "b": "b"}}, {"grain": frozenset(("a", "b"))})
        self.assertEqual(list(memory.prices.items()), list(expected["prices"].items()))

    def test_wages_and_markets_of_goods_that_did_not_change_are_untouched(self):
        stores = {"prices": {"salt|a": 1.0}, "wages": {"smith|l": 3.0}}
        memory, _ = self.moved_both_ways(stores, {"grain": {"new": "old"}}, {"grain": frozenset(("old",))})
        self.assertEqual((dict(memory.prices), dict(memory.wages)), ({"salt|a": 1.0}, {"smith|l": 3.0}))

    def test_every_new_market_is_numbered_and_the_member_counts_follow(self):
        stores = {"prices": {"grain|old": 1.0}, "trade_age": {"grain|old": 1}}
        memory, _ = self.moved_both_ways(stores, {"grain": {"n1": "old", "n2": "old"}}, {"grain": frozenset(("old",))})
        self.assertEqual((memory.tables.goods_markets.names, len(memory.prices), len(memory.trade_age)), (("grain|n1", "grain|n2"), 2, 2))


if __name__ == "__main__":
    unittest.main()
