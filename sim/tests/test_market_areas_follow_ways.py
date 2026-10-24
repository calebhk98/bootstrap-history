"""Complaints/416: market-area partitions follow the built ways. When the ways change, what the economy remembers about
each market (prices, volumes, merchants' expectations) moves to the area that now holds the old market's anchor
(`market_areas_follow.follow`), and the economy asks for that only when the ways did change. The partitions are written
out here as stand-ins; the partitioning itself is the area map's rule."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy.accounts import Book
from sim.economy.economy import Economy
from sim.economy.market_areas_follow import follow, old_areas_by_new
from sim.economy.market_memory import KEY_SEPARATOR, MarketMemory, market_key
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec

GOOD = "grain_kg"


def area(area_id, anchor_tile):
    return types.SimpleNamespace(area_id=area_id, anchor_tile=anchor_tile)


class Partition:
    """A partition of one good's markets: area id by tile."""

    def __init__(self, area_of_tile, anchors):
        self.area_of_tile = area_of_tile
        self.anchors = anchors

    def goods(self):
        return [GOOD]

    def areas(self, good):
        return [area(area_id, anchor) for area_id, anchor in self.anchors.items()]

    def area_of(self, good, tile):
        return self.area_of_tile[tile]


SPLIT = Partition({"town": "a:town", "farms": "a:farms", "hills": "a:hills"}, {"a:town": "town", "a:farms": "farms", "a:hills": "hills"})
JOINED = Partition({"town": "a:one", "farms": "a:one", "hills": "a:one"}, {"a:one": "farms"})


def record_remembering(prices):
    record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec("coin", "fiat", None, 0.0, None))
    record.memory.prices = {market_key(GOOD, area_id): price for area_id, price in prices.items()}
    record.memory.usual_prices = dict(record.memory.prices)
    return record


class FollowTests(unittest.TestCase):

    def test_a_new_area_follows_the_old_area_that_held_its_anchor_tile(self):
        self.assertEqual(old_areas_by_new(SPLIT, JOINED), {GOOD: {"a:one": "a:farms"}})

    def test_remembered_prices_move_to_the_new_area_of_the_old_anchor(self):
        record = record_remembering({"a:town": 1.0, "a:farms": 2.0, "a:hills": 3.0})
        follow(record, SPLIT, JOINED)
        self.assertEqual(record.memory.prices, {market_key(GOOD, "a:one"): 2.0})
        self.assertEqual(record.memory.usual_prices, {market_key(GOOD, "a:one"): 2.0})

    def test_every_remembered_market_names_an_area_that_exists(self):
        record = record_remembering({"a:town": 1.0, "a:farms": 2.0, "a:hills": 3.0})
        record.memory.prices[market_key("labourer", "wage_area")] = 9.0
        follow(record, SPLIT, JOINED)
        existing = {area.area_id for area in JOINED.areas(GOOD)}
        for key in record.memory.prices:
            first, _separator, area_id = key.partition(KEY_SEPARATOR)
            if first == GOOD:
                self.assertIn(area_id, existing)
        self.assertEqual(record.memory.prices[market_key("labourer", "wage_area")], 9.0)

    def test_a_split_partition_gives_each_new_area_the_memory_of_the_one_old_area_it_came_from(self):
        record = record_remembering({"a:one": 5.0})
        follow(record, JOINED, SPLIT)
        self.assertEqual(record.memory.prices, {market_key(GOOD, area_id): 5.0 for area_id in SPLIT.anchors})

    def test_a_merchants_expectations_move_with_the_markets(self):
        record = record_remembering({"a:farms": 2.0})
        record.merchants["merchant:1"] = types.SimpleNamespace(
            expected_prices={(GOOD, "a:farms"): 2.0}, expected_volumes={(GOOD, "a:town"): 4.0}, price_history={}, routes={})
        follow(record, SPLIT, JOINED)
        merchant = record.merchants["merchant:1"]
        self.assertEqual(merchant.expected_prices, {(GOOD, "a:one"): 2.0})
        self.assertEqual(merchant.expected_volumes, {})


class SetImprovementsTests(unittest.TestCase):
    def economy(self, improvements):
        rebuilt = []
        return types.SimpleNamespace(improvements=improvements, record=types.SimpleNamespace(ways={}),
                                     _rebuild_carriage=lambda: rebuilt.append(True) or True, rebuilt=rebuilt)

    def test_unchanged_ways_leave_the_areas_alone(self):
        economy = self.economy({"a|b": {"road": True}})
        change = Economy.set_improvements
        self.assertFalse(change(economy, {"a|b": {"road": True}}))
        self.assertEqual(economy.rebuilt, [])

    def test_new_ways_are_kept_on_the_record_and_the_carriage_is_rebuilt_over_them(self):
        economy = self.economy({})
        change = Economy.set_improvements
        self.assertTrue(change(economy, {"a|b": {"road": True}}))
        self.assertEqual(economy.improvements, {"a|b": {"road": True}})
        self.assertEqual(economy.record.ways, {"a|b": {"road": True}})
        self.assertEqual(economy.rebuilt, [True])


if __name__ == "__main__":
    unittest.main()
