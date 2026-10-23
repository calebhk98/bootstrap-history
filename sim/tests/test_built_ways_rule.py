"""Complaints/416: building a way charges the quoted money once, records the way only when it opens, and is refused
without the money, the technology or a held border. Called on a stand-in builder (test_ways_crew_and_works)."""
QUICK_TOPIC = True

import unittest

from sim.geography import api as geography
from sim.tests.test_ways_crew_and_works import _builder_for, _flat, _open


class BuildingARuleTests(unittest.TestCase):

    def setUp(self):
        self.edge = _flat(geography.open_map())
        self.key = geography.edge_key(self.edge.tile_a, self.edge.tile_b)

    def test_building_charges_the_quote_once_and_records_the_way_only_when_it_opens(self):
        builder = _builder_for(self.edge)
        quote = builder.way_quote(self.edge.tile_a, self.edge.tile_b, "road")
        self.assertGreater(quote["money"], 0.0)
        ok, message = builder.build_way(self.edge.tile_a, self.edge.tile_b, "road")
        self.assertTrue(ok, message)
        self.assertEqual(builder.paid, [quote["money"]])
        self.assertNotIn(self.key, builder.state.economy.improvements)
        _open(builder, quote["years"])
        self.assertTrue(builder.state.economy.improvements[self.key]["road"])
        self.assertEqual(builder.paid, [quote["money"]])

    def test_building_is_refused_when_the_budget_is_below_the_quote(self):
        builder = _builder_for(self.edge)
        quote = builder.way_quote(self.edge.tile_a, self.edge.tile_b, "road")
        builder.spending_power = lambda kind: quote["money"] * 0.5
        self.assertFalse(builder.build_way(self.edge.tile_a, self.edge.tile_b, "road")[0])
        self.assertEqual((builder.paid, builder.market.pressed, builder.state.economy.ways_under_construction),
                         ([], [], {}))

    def test_building_is_refused_for_a_tile_the_nation_does_not_hold(self):
        builder = _builder_for(self.edge)
        self.assertFalse(builder.build_way(self.edge.tile_a, "no_such_tile", "road")[0])
        self.assertEqual((builder.paid, builder.state.economy.ways_under_construction), ([], {}))

    def test_building_is_refused_without_the_technology(self):
        builder = _builder_for(self.edge)
        builder.state.projects.granted = set()
        self.assertFalse(builder.build_way(self.edge.tile_a, self.edge.tile_b, "road")[0])
        self.assertEqual((builder.paid, builder.state.economy.ways_under_construction), ([], {}))


if __name__ == "__main__":
    unittest.main()
