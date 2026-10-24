"""Complaints/522: a resumed economy holds the market memory the unbroken one holds. A year's flows change the
return-trip emptiness the areas are partitioned for only at the next year's start (`follow_flows`); a record saved between
carries the memory keyed by the areas of the older emptiness. So a resume partitions by the emptiness the record saved,
and `follow` carries the memory to the areas a later partition makes. Each rule is called on built inputs."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy.economy import Economy
from sim.economy.market_areas_follow import follow
from sim.economy.market_memory import MarketMemory, market_key


class Setup:
    """An `EconomySetup` that records what the economy asks of it."""

    def __init__(self):
        self.carriage_asked = []
        self.table = object()
        self.map = object()

    def carriage_table(self, ways, imbalance):
        self.carriage_asked.append((ways, imbalance))
        return self.table

    def area_map(self, carriage):
        self.carriage_of_map = carriage
        return self.map


class ResumeTests(unittest.TestCase):
    def test_the_resume_partitions_for_the_emptiness_the_record_saved_not_the_one_its_ledger_implies(self):
        setup = Setup()
        record = types.SimpleNamespace(ways={"road": {"road": True}}, area_imbalance=0.75,
                                       carried={"town": {"farms": 10.0}, "farms": {"town": 10.0}})
        economy = types.SimpleNamespace()
        Economy.__init__(economy, setup, record)
        self.assertEqual(setup.carriage_asked, [({"road": {"road": True}}, 0.75)])
        self.assertIs(economy.carriage, setup.table)
        self.assertIs(setup.carriage_of_map, setup.table)
        self.assertIs(economy.area_map, setup.map)


class FollowFlows(unittest.TestCase):
    def economy(self, saved_imbalance, carried):
        rebuilt = []
        return types.SimpleNamespace(record=types.SimpleNamespace(area_imbalance=saved_imbalance, carried=carried),
                                     _rebuild_carriage=lambda: rebuilt.append(True) or True, rebuilt=rebuilt)

    def test_opposite_flows_change_the_emptiness_and_the_areas_are_partitioned_again(self):
        economy = self.economy(1.0, {"town": {"farms": 10.0}, "farms": {"town": 10.0}})
        self.assertTrue(Economy.follow_flows(economy))
        self.assertLess(economy.record.area_imbalance, 1.0)
        self.assertEqual(economy.rebuilt, [True])

    def test_flows_that_leave_the_emptiness_where_it_was_leave_the_areas_alone(self):
        economy = self.economy(1.0, {})
        self.assertFalse(Economy.follow_flows(economy))
        self.assertEqual(economy.rebuilt, [])


class Area:
    def __init__(self, area_id, anchor_tile):
        self.area_id, self.anchor_tile = area_id, anchor_tile


class Partition:
    """The areas of one good: `{area id: anchor tile}`; a tile belongs to the area whose anchor it is."""

    def __init__(self, areas_by_good):
        self.by_good = {good: [Area(area_id, tile) for area_id, tile in areas.items()] for good, areas in areas_by_good.items()}

    def goods(self):
        return tuple(sorted(self.by_good))

    def areas(self, good):
        return tuple(self.by_good[good])

    def area_of(self, good, tile):
        return next(area.area_id for area in self.by_good[good] if area.anchor_tile == tile)


class FollowCarriesTheMemory(unittest.TestCase):
    def test_each_new_area_takes_the_memory_of_the_old_area_holding_its_anchor_tile(self):
        old = Partition({"grain": {"old:a": "town", "old:b": "farms"}})
        new = Partition({"grain": {"new:x": "town"}})
        memory = MarketMemory(prices={market_key("grain", "old:a"): 3.0, market_key("grain", "old:b"): 5.0},
                              currency_of_area={"old:a": "coin", "old:b": "coin"})
        record = types.SimpleNamespace(memory=memory, merchants={}, volumes={market_key("grain", "old:a"): 7.0},
                                       unsold={}, unmet={}, margin_years={}, curves={})
        follow(record, old, new)
        self.assertEqual(memory.prices, {market_key("grain", "new:x"): 3.0})
        self.assertEqual(record.volumes, {market_key("grain", "new:x"): 7.0})
        self.assertEqual(memory.currency_of_area, {"new:x": "coin"})

    def test_a_market_that_is_not_a_goods_stays_where_it_is(self):
        old = Partition({"grain": {"old:a": "town"}})
        new = Partition({"grain": {"new:x": "town"}})
        memory = MarketMemory(prices={market_key("labourer", "old:a"): 1.0})
        record = types.SimpleNamespace(memory=memory, merchants={}, volumes={}, unsold={}, unmet={}, margin_years={}, curves={})
        follow(record, old, new)
        self.assertEqual(memory.prices, {market_key("labourer", "old:a"): 1.0})


if __name__ == "__main__":
    unittest.main()
