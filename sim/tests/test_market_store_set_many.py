"""`FloatStore.set_many` leaves a store as the same writes one at a time do: the figures, the order the markets entered, the count."""
QUICK_TOPIC = True

import unittest

from sim.economy.market_memory import MarketMemory


def _memory(**stores):
    return MarketMemory(**stores)


class SetManyIsTheSequenceOfSets(unittest.TestCase):
    def check(self, before, keys, figures, store_name="prices"):
        sequential, block = _memory(**{store_name: dict(before)}), _memory(**{store_name: dict(before)})
        for key, figure in zip(keys, figures):
            getattr(sequential, store_name)[key] = figure
        getattr(block, store_name).set_many(keys, figures)
        one, many = getattr(sequential, store_name), getattr(block, store_name)
        self.assertEqual(list(many.items()), list(one.items()))
        self.assertEqual(len(many), len(one))

    def test_new_markets_enter_in_the_order_given(self):
        self.check({}, ["salt|a", "grain|a", "iron|b"], [3.0, 1.0, 2.0])

    def test_markets_already_held_keep_their_place_and_take_the_new_figure(self):
        self.check({"iron|a": 2.0, "grain|a": 1.0}, ["grain|a", "salt|a", "iron|a"], [5.0, 3.0, 4.0])

    def test_a_key_given_twice_enters_once_with_the_last_figure(self):
        self.check({}, ["salt|a", "grain|a", "salt|a"], [3.0, 1.0, 7.0])

    def test_a_labour_store_numbers_its_markets_too(self):
        self.check({"smith|town": 1.0}, ["farmer|town", "smith|town", "smith|port"], [2.0, 3.0, 4.0], store_name="wages")

    def test_no_keys_changes_nothing(self):
        self.check({"iron|a": 2.0}, [], [])

    def test_a_nan_is_refused(self):
        memory = _memory(prices={})
        with self.assertRaises(ValueError):
            memory.prices.set_many(["salt|a"], [float("nan")])
        self.assertEqual(len(memory.prices), 0)


if __name__ == "__main__":
    unittest.main()
