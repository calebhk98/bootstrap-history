"""Speed: the reads the market memory keeps between calls (the trade ages and quote kinds of the price keys) are
dropped when what they read is written, and kept when it is not. Each test calls one method on inputs
written out in the test; no game."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory import MarketMemory
from sim.economy.types import QUOTE_LOWEST_UNFILLED_ASK


def counting(value):
    calls = []

    def compute():
        calls.append(1)
        return value
    return compute, calls


KEYS = ("grain|a", "salt|a")


class AgesAndKinds(unittest.TestCase):
    def memory(self):
        return MarketMemory(prices={"grain|a": 1.0, "salt|a": 2.0}, trade_age={"grain|a": 0})

    def test_the_same_answer_is_kept_and_a_price_written_meanwhile_does_not_drop_it(self):
        memory = self.memory()
        compute, calls = counting("answer")
        self.assertEqual(memory.kept_for_ages_and_kinds("bits", KEYS, compute), "answer")
        memory.set_price("grain|a", 3.0)
        self.assertEqual(memory.kept_for_ages_and_kinds("bits", KEYS, compute), "answer")
        self.assertEqual(len(calls), 1)

    def test_a_year_ending_drops_it(self):
        memory = self.memory()
        compute, calls = counting("answer")
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        memory.note_trading(["salt|a"])
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        self.assertEqual(len(calls), 2)

    def test_a_quote_kind_set_or_dropped_drops_it(self):
        memory = self.memory()
        compute, calls = counting("answer")
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        memory.set_quote_kind("salt|a", QUOTE_LOWEST_UNFILLED_ASK)
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        memory.drop_quote_kind("salt|a")
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        self.assertEqual(len(calls), 3)

    def test_a_replaced_store_or_other_keys_drop_it(self):
        memory = self.memory()
        compute, calls = counting("answer")
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        memory.trade_age = dict(memory.trade_age)
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        memory.kept_for_ages_and_kinds("bits", ("grain|a",), compute)
        self.assertEqual(len(calls), 3)

    def test_equal_keys_in_a_new_tuple_keep_it(self):
        memory = self.memory()
        compute, calls = counting("answer")
        memory.kept_for_ages_and_kinds("bits", KEYS, compute)
        memory.kept_for_ages_and_kinds("bits", tuple(list(KEYS)), compute)
        self.assertEqual(len(calls), 1)




if __name__ == "__main__":
    unittest.main()
