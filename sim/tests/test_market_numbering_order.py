"""`number_area_markets`: the goods markets of an area map are numbered as one sorted batch, so a market's number does not depend on
which writer touched the market first, nor on the order the map lists its goods and areas in."""
QUICK_TOPIC = True

import unittest
from collections import namedtuple

from sim.economy.labour_state import mirror_wages
from sim.economy.market_memory import MarketMemory
from sim.labour.api import MarketState
from sim.economy.market_memory_areas import area_market_keys, number_area_markets

Area = namedtuple("Area", ("area_id",))


class FakeAreaMap:
    def __init__(self, areas_by_good):
        self._areas = areas_by_good

    def goods(self):
        return tuple(self._areas)

    def areas(self, good):
        return tuple(Area(area_id) for area_id in self._areas[good])


ORDERED = {"grain": ["a2", "a1"], "iron": ["a3"], "cloth": ["a1", "a3", "a2"]}
SHUFFLED = {"iron": ["a3"], "cloth": ["a2", "a3", "a1"], "grain": ["a1", "a2"]}


def state_after(areas_by_good):
    memory = MarketMemory()
    number_area_markets(memory, FakeAreaMap(areas_by_good))
    return memory.tables.state()


class AreaMarketsAreNumberedAsOneSortedBatch(unittest.TestCase):

    def test_the_numbering_does_not_follow_the_order_the_map_lists_goods_and_areas(self):
        self.assertEqual(state_after(ORDERED), state_after(SHUFFLED))

    def test_the_numbering_is_sorted_by_market_key(self):
        state = state_after(ORDERED)
        self.assertEqual(state["goods_markets"], sorted(area_market_keys(FakeAreaMap(ORDERED))))
        self.assertEqual(state["goods"], sorted(ORDERED))
        self.assertEqual(state["areas"], ["a1", "a2", "a3"])

    def test_numbering_the_map_again_changes_nothing(self):
        memory = MarketMemory()
        number_area_markets(memory, FakeAreaMap(ORDERED))
        before = memory.tables.state()
        generation = memory.tables.generation
        number_area_markets(memory, FakeAreaMap(SHUFFLED))
        self.assertEqual(memory.tables.state(), before)
        self.assertEqual(memory.tables.generation, generation)

    def test_a_write_to_each_area_market_after_the_map_is_numbered_adds_no_number_in_any_order(self):
        keys = area_market_keys(FakeAreaMap(ORDERED))
        for write_order in (keys, list(reversed(keys))):
            memory = MarketMemory()
            number_area_markets(memory, FakeAreaMap(ORDERED))
            before = memory.tables.state()
            for key in write_order:
                memory.tables.goods_row_for_write(key)
            self.assertEqual(memory.tables.state(), before)


class MirroredWagesAreNumberedInSortedOrder(unittest.TestCase):

    def test_labour_markets_are_numbered_sorted_whatever_order_the_core_named_its_wages_in(self):
        states = []
        for wages in ({"town": {"smith": 3.0, "baker": 1.0}, "port": {"smith": 3.5}},
                      {"port": {"smith": 3.5}, "town": {"baker": 1.0, "smith": 3.0}}):
            memory = MarketMemory()
            mirror_wages(memory.wages, MarketState(workers={}, trainees={}, wages=wages))
            states.append(memory.tables.state())
        self.assertEqual(states[0], states[1])
        self.assertEqual(states[0]["labour_markets"], ["baker|town", "smith|port", "smith|town"])


if __name__ == "__main__":
    unittest.main()
