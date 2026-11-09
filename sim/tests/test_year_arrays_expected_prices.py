"""`year_arrays_producers._expected_prices`: each producer's expected price at its recipe's good slots, NaN where it holds none."""
import unittest
from types import SimpleNamespace

import numpy as np

from sim.economy import year_arrays_producers
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer

QUICK_TOPIC = True


def _matrices():
    """Two recipes: `bake` has slots (flour, bread, bran); `mill` has slots (wheat, flour, none). The year's goods lack `salt`."""
    goods = SimpleNamespace(row={"bran": 0, "bread": 1, "flour": 2, "wheat": 3})
    slot_goods = np.array([[2, 1, 0], [3, 2, -1]], dtype=np.int64)
    return SimpleNamespace(goods=goods, good_slots=3, slot_goods=slot_goods)


class ExpectedPricesBySlot(unittest.TestCase):
    def test_a_held_price_lands_in_the_slot_of_its_good_and_the_rest_are_nan(self):
        store = ProducerStore({
            "a": Producer("a", "o", "bake", "t", 1.0, expected_prices={"bread": 4.0, "salt": 9.0, "flour": 1.5}),
            "b": Producer("b", "o", "mill", "t", 1.0, expected_prices={"flour": 2.5}),
            "c": Producer("c", "o", "mill", "t", 1.0),
        })
        rows = store.order()
        recipe_row = np.array([0, 1, 1], dtype=np.int64)
        prices = year_arrays_producers._expected_prices(store, rows, recipe_row, _matrices())
        self.assertEqual(prices[0, :2].tolist(), [1.5, 4.0])
        self.assertTrue(np.isnan(prices[0, 2]))
        self.assertTrue(np.isnan(prices[1, 0]))
        self.assertEqual(prices[1, 1], 2.5)
        self.assertTrue(np.isnan(prices[1, 2]))
        self.assertTrue(np.isnan(prices[2]).all())

    def test_a_good_in_two_slots_fills_both_and_a_padded_slot_stays_nan(self):
        store = ProducerStore({"a": Producer("a", "o", "twice", "t", 1.0, expected_prices={"bran": 7.0, "flour": 1.5})})
        matrices = SimpleNamespace(goods=_matrices().goods, good_slots=4, slot_goods=np.array([[2, 0, 2, -1]], dtype=np.int64))
        prices = year_arrays_producers._expected_prices(store, store.order(), np.array([0], dtype=np.int64), matrices)
        self.assertEqual(prices[0, :3].tolist(), [1.5, 7.0, 1.5])
        self.assertTrue(np.isnan(prices[0, 3]))

    def test_no_prices_held_is_all_nan(self):
        store = ProducerStore({"a": Producer("a", "o", "bake", "t", 1.0)})
        prices = year_arrays_producers._expected_prices(store, store.order(), np.array([0], dtype=np.int64), _matrices())
        self.assertTrue(np.isnan(prices).all())


if __name__ == "__main__":
    unittest.main()
