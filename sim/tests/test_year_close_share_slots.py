"""`year_close_shares.asked_slots`: the output slots a producer's growth is priced for are those before the recipe row's first
empty slot, as the row-by-row pricer read them (it stopped at the first empty slot): a good after a gap is not asked about."""
QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy import year_close_shares


def plain_asked(slot_goods, slot_is_output, added):
    """The (row, slot) pairs the old row-by-row loop priced."""
    asked = []
    for row in range(len(slot_goods)):
        for slot, column in enumerate(slot_goods[row]):
            if column < 0:
                break
            if slot_is_output[row, slot] and added[row, slot] > 0.0:
                asked.append((row, slot))
    return asked


class AskedSlotsTest(unittest.TestCase):
    def test_slots_after_a_gap_are_not_asked(self):
        slot_goods = np.array([[3, 5, -1, 7], [2, -1, -1, -1], [4, 6, 8, 9]])
        slot_is_output = np.array([[True, True, False, True], [True, False, False, False], [False, True, True, True]])
        added = np.array([[1.0, 2.0, 0.0, 3.0], [1.0, 0.0, 0.0, 0.0], [5.0, 0.0, 1.0, 2.0]])
        rows, slots = year_close_shares.asked_slots(slot_goods, slot_is_output, added)
        self.assertEqual(list(zip(rows.tolist(), slots.tolist())), plain_asked(slot_goods, slot_is_output, added))
        self.assertNotIn((0, 3), list(zip(rows.tolist(), slots.tolist())))

    def test_random_rows_match_the_row_by_row_loop(self):
        generator = np.random.default_rng(5)
        for _case in range(200):
            slot_goods = generator.integers(-1, 9, size=(generator.integers(1, 6), generator.integers(1, 6)))
            slot_is_output = generator.random(slot_goods.shape) < 0.6
            added = np.where(generator.random(slot_goods.shape) < 0.7, generator.random(slot_goods.shape), 0.0)
            rows, slots = year_close_shares.asked_slots(slot_goods, slot_is_output, added)
            self.assertEqual(list(zip(rows.tolist(), slots.tolist())), plain_asked(slot_goods, slot_is_output, added))


if __name__ == "__main__":
    unittest.main()
