"""Complaints/416: building a way charges the quoted money once, records the way only when it opens, and is refused
without the money, the technology or a held border. Called on a stand-in builder (test_ways_crew_and_works)."""
QUICK_TOPIC = True

import unittest

from sim.geography import api as geography
from sim.land import ways_rules
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
        self.assertNotIn(self.key, builder.world.improvements)
        _open(builder, quote["years"])
        self.assertTrue(builder.world.improvements[self.key]["road"])
        self.assertEqual(builder.paid, [quote["money"]])

    def test_building_is_refused_when_the_budget_is_below_the_quote(self):
        builder = _builder_for(self.edge)
        quote = builder.way_quote(self.edge.tile_a, self.edge.tile_b, "road")
        builder.cash = quote["money"] * 0.5
        self.assertFalse(builder.build_way(self.edge.tile_a, self.edge.tile_b, "road")[0])
        self.assertEqual((builder.paid, builder.market.pressed, builder.world.ways_under_construction),
                         ([], [], {}))

    def test_building_is_refused_for_a_tile_the_nation_does_not_hold(self):
        builder = _builder_for(self.edge)
        self.assertFalse(builder.build_way(self.edge.tile_a, "no_such_tile", "road")[0])
        self.assertEqual((builder.paid, builder.world.ways_under_construction), ([], {}))

    def test_building_is_refused_without_the_technology(self):
        builder = _builder_for(self.edge)
        builder.granted = set()
        self.assertFalse(builder.build_way(self.edge.tile_a, self.edge.tile_b, "road")[0])
        self.assertEqual((builder.paid, builder.world.ways_under_construction), ([], {}))


class WaysRulesTests(unittest.TestCase):

    def test_the_money_is_the_labour_then_each_bill_in_order(self):
        self.assertEqual(ways_rules.way_money(100.0, 2.0, [10.0, 5.0]), 215.0)
        self.assertEqual(ways_rules.way_money(100.0, 2.0, []), 200.0)

    def test_the_crew_hours_are_the_found_share_of_the_crew_the_work_calls_for(self):
        self.assertEqual(ways_rules.crew_hours_a_year(5, 1000.0, 10), 500.0)
        self.assertEqual(ways_rules.way_years(1000.0, 500.0), 2.0)

    def test_a_way_whose_time_has_passed_opens_and_gives_back_its_crew(self):
        pending = {"a|b": {"road": {"due": 10.0, "trade": "labourer", "crew_hours": 40.0, "engineered": True, "pressed": 9}}}
        built = {}
        calls = ways_rules.open_ways(pending, built, 10.0)
        self.assertEqual((pending, built, calls), ({}, {"a|b": {"road": True, "engineered": True}}, [("release", "labourer", 40.0)]))

    def test_a_way_still_building_leans_on_its_trade_once_a_year(self):
        pending = {"a|b": {"road": {"due": 12.0, "trade": "labourer", "crew_hours": 40.0, "engineered": False, "pressed": 9}}}
        self.assertEqual(ways_rules.open_ways(pending, {}, 10.0), [("press", "labourer", 40.0)])
        self.assertEqual(pending["a|b"]["road"]["pressed"], 10.0)
        self.assertEqual(ways_rules.open_ways(pending, {}, 10.0), [])

    def test_a_start_is_refused_for_an_unknown_technology_a_standing_way_or_one_being_built(self):
        quote = {"node": "road_node"}
        self.assertIn("do not know", ways_rules.start_refusal("road", "here", quote, set(), False, False))
        self.assertIn("already stands", ways_rules.start_refusal("road", "here", quote, {"road_node"}, True, False))
        self.assertIn("already being built", ways_rules.start_refusal("road", "here", quote, {"road_node"}, False, True))
        self.assertIsNone(ways_rules.start_refusal("road", "here", {"node": None}, set(), False, False))

    def test_a_port_is_said_to_stand_on_one_tile_and_a_road_between_two(self):
        self.assertEqual(ways_rules.where("a", "a"), "on a")
        self.assertEqual(ways_rules.where("a", "b"), "between a and b")


if __name__ == "__main__":
    unittest.main()
