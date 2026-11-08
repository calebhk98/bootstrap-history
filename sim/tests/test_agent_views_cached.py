"""The agent economy's rate, people by tile and trade, floor costs and hours offered are cached on the markets module's `memory` channel,
which every write to the market memory, the economy's building and the repricing of the money bump (see test_wage_views_cached.py).
A debug game re-checks each cached read against a fresh computation (`SHADOW_CHECK_EVERY`)."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.markets.channels import MEMORY
from sim.markets.module_spec import MODULE_SPECS as MARKETS_SPECS
from sim.assembly.api import KEYED
from sim.workforce.world import AgentEconomyReads

CACHED_ON_MEMORY = ("agent_rate", "agent_people_by_tile_and_trade", "agent_need_floor_costs", "agent_hours_offered_cell")


class DeclaredViews(unittest.TestCase):
    def view(self, name):
        return next(view for view in MARKETS_SPECS[0].publishes if view.name == name)

    def test_each_is_cached_on_the_memory_channel(self):
        for name in CACHED_ON_MEMORY:
            self.assertTrue(self.view(name).cached, name)
            self.assertEqual(self.view(name).channels, (MEMORY,), name)

    def test_the_hours_cell_is_keyed_and_the_quote_it_answers_for_stays_uncached(self):
        self.assertEqual(self.view("agent_hours_offered_cell").kind, KEYED)
        self.assertFalse(self.view("agent_hours_offered_at").cached)


class WorkforceReadsTheCell(unittest.TestCase):
    def test_the_hours_offered_are_read_from_the_keyed_view_by_trade_and_tile(self):
        asked = []

        class Cells:
            def __getitem__(self, cell):
                asked.append(cell)
                return 123.0

        world = AgentEconomyReads.__new__(AgentEconomyReads)
        world._needs = SimpleNamespace(agent_hours_offered_cell=Cells())
        self.assertEqual(world.agent_hours_offered_at("smith", "tile"), 123.0)
        self.assertEqual(asked, [("smith", "tile")])


if __name__ == "__main__":
    unittest.main()
