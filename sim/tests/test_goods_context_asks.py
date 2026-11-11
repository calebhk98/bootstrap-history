"""`ClearingContext.ask_known_areas_and_tiles`: the lending rate of every numbered area and the band multiple of every numbered tile are in the
context's tables afterwards, as the packing and decision kernels would have had them asked one at a time (written-out areas and tiles)."""
QUICK_TOPIC = True

import math
import types
import unittest

import numpy

from sim.compiled_tables.ids import IdTable
from sim.economy.ask_adjust import ASK_BAND_CEILING
from sim.economy.goods_table_context import ClearingContext

RATES = {"coin": 0.05}
CURRENCY_OF_AREA = {"grain:rome": "coin", "grain:gaul": "denar"}
SUBSTITUTION = {"town": 3.0, "farm": 1.0, "hill": 1.2}


def context_of(areas, tiles):
    view = types.SimpleNamespace(interest_rate=RATES.get, currency_of=lambda area: CURRENCY_OF_AREA[area])
    setup = types.SimpleNamespace(basket_for=lambda tile: types.SimpleNamespace(substitution=SUBSTITUTION[tile], needs=()))
    orders = types.SimpleNamespace(memory_tables=types.SimpleNamespace(areas=IdTable("area", areas)))
    record = types.SimpleNamespace(book=types.SimpleNamespace(tile_ids=IdTable("tile", tiles)))
    return ClearingContext(setup, record, view, orders, None, None)


class AskKnownTest(unittest.TestCase):
    def test_every_area_has_its_rate_and_a_currency_without_one_is_nan(self):
        context = context_of(["grain:gaul", "grain:rome"], ["farm"])
        context.ask_known_areas_and_tiles()
        rates, known = context.area_rates()
        self.assertTrue(known.all())
        self.assertTrue(math.isnan(rates[0]))          # areas are numbered in name order: gaul first
        self.assertEqual(rates[1], 0.05)

    def test_every_tile_has_its_band_multiple_capped_at_the_ceiling(self):
        context = context_of(["grain:rome"], ["farm", "hill", "town"])
        context.ask_known_areas_and_tiles()
        for tile in range(3):
            context.note_band_multiple(tile, "grain")
        multiples = context.band_multiple_table("grain")
        self.assertEqual(multiples[0], ASK_BAND_CEILING)           # a substitution of one has no markup limit but the ceiling
        self.assertEqual(multiples[1], min(1.2 / 0.2, ASK_BAND_CEILING))
        self.assertEqual(multiples[2], min(3.0 / 2.0, ASK_BAND_CEILING))

    def test_a_tile_numbered_later_is_still_missing_until_asked(self):
        context = context_of(["grain:rome"], ["farm"])
        context.ask_known_areas_and_tiles()
        context.record.book.tile_ids.admit(["town"])
        self.assertTrue(numpy.isnan(context.band_multiple_table("grain")[1]))


if __name__ == "__main__":
    unittest.main()
