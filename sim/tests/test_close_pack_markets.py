"""The close pack's market figures read by array (`close_pack_markets`) against the per-(good, area) dict loops they replace, bit for bit."""
QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy.close_pack_markets import clearing_and_unmet, columns_of_markets

GOOD_NAMES = ["bread", "iron", "salt", "wool"]       # the market memory's good numbers 0..3; wool has no column
AREA_NAMES = ["north", "south", "west"]               # area numbers 0..2; west has no column
GOOD_ROW = {"iron": 0, "bread": 1, "salt": 2}
AREA_ROW = {"south": 0, "north": 1}


def old_figures(markets, delivered, priced, unmet, unmet_order, shape):
    """The old loops: markets are (good name, area name); delivered, priced and unmet by market number."""
    clearing, wanted = np.full(shape, np.nan), np.zeros(shape)
    for number, (good, area) in enumerate(markets):
        column, good_column = AREA_ROW.get(area), GOOD_ROW.get(good)
        price = None if priced[number] != priced[number] else priced[number]
        if column is not None and good_column is not None and delivered[number] > 0.0 and price is not None:
            clearing[good_column, column] = price
        if column is not None and good_column is not None and unmet_order[number] != 0:
            wanted[good_column, column] = unmet[number]
    return clearing, wanted


class MarketColumnsTests(unittest.TestCase):
    def test_a_market_has_the_columns_of_its_good_and_area_and_minus_one_where_there_is_none(self):
        first = np.array([0, 3, 1, 2], dtype=np.int64)
        area = np.array([0, 0, 2, 1], dtype=np.int64)
        good_column, area_column = columns_of_markets(first, area, GOOD_NAMES, AREA_NAMES, GOOD_ROW, AREA_ROW)
        self.assertEqual(good_column.tolist(), [1, -1, 0, 2])
        self.assertEqual(area_column.tolist(), [1, 1, -1, 0])

    def test_no_markets_give_empty_columns(self):
        empty = np.zeros(0, dtype=np.int64)
        good_column, area_column = columns_of_markets(empty, empty, GOOD_NAMES, AREA_NAMES, GOOD_ROW, AREA_ROW)
        self.assertEqual((len(good_column), len(area_column)), (0, 0))


class ClearingAndUnmetTests(unittest.TestCase):
    def test_random_markets_match_the_dict_loops_bit_for_bit(self):
        rng = np.random.default_rng(7)
        for _trial in range(30):
            pairs = sorted({(int(rng.integers(0, len(GOOD_NAMES))), int(rng.integers(0, len(AREA_NAMES)))) for _each in range(40)})
            count = len(pairs)
            first = np.array([pair[0] for pair in pairs], dtype=np.int64)
            area = np.array([pair[1] for pair in pairs], dtype=np.int64)
            extra = int(rng.integers(0, 3))             # the ledger's arrays may hold rows past the markets used
            delivered = np.where(rng.random(count + extra) < 0.3, 0.0, rng.random(count + extra) * 100.0)
            priced = np.where(rng.random(count + extra) < 0.2, np.nan, rng.random(count + extra) * 50.0)
            unmet = rng.random(count + extra) * 9.0
            unmet_order = rng.integers(0, 3, count + extra)
            markets = [(GOOD_NAMES[each[0]], AREA_NAMES[each[1]]) for each in pairs]
            good_column, area_column = columns_of_markets(first, area, GOOD_NAMES, AREA_NAMES, GOOD_ROW, AREA_ROW)
            shape = (3, 2)
            clearing, wanted = clearing_and_unmet(shape, delivered, priced, unmet, unmet_order, good_column, area_column)
            old_clearing, old_wanted = old_figures(markets, delivered, priced, unmet, unmet_order, shape)
            self.assertTrue(np.array_equal(clearing, old_clearing, equal_nan=True))
            self.assertTrue(np.array_equal(wanted, old_wanted))

    def test_a_market_with_no_goods_moved_or_no_price_leaves_the_price_blank(self):
        good_column, area_column = np.array([0, 1, 2]), np.array([0, 0, 0])
        clearing, _wanted = clearing_and_unmet((3, 1), np.array([0.0, 5.0, 5.0]), np.array([4.0, np.nan, 3.0]), np.zeros(3),
                                               np.zeros(3, dtype=np.int64), good_column, area_column)
        self.assertEqual(clearing[2, 0], 3.0)
        self.assertTrue(np.isnan(clearing[0, 0]) and np.isnan(clearing[1, 0]))


if __name__ == "__main__":
    unittest.main()
