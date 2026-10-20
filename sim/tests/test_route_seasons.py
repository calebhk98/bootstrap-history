"""A mode can be closed part of the year on the edges its closure rules name; a haul pays the expected wait."""
import copy
import unittest

from sim.geography import queries, routes_modes, routes_search, routes_seasons
from sim.tests.test_geography_routes import small_map

QUICK_TOPIC = False
LANE = {"id": "winter_sea", "edge_classes": ["coast"], "closed_days_per_year": 120, "wait_span_km": 500,
        "kind": "heuristic", "conf": "D", "source": "test", "why": "test"}
PASS = {"id": "snow", "edge_classes": ["land"], "closed_days_per_year": 150, "wait_span_km": 500,
        "kind": "heuristic", "conf": "D", "source": "test", "why": "test"}
PRICES = {"foot": 1.0, "sail": 1.0}


def closed_map(mode_id=None, rule=None):
    """The small map with every shipped closure removed and, when given, one rule on one mode."""
    world_map = small_map()
    world_map.catalogues["route_modes"] = copy.deepcopy(world_map.catalogues["route_modes"])
    for mode in world_map.catalogues["route_modes"].values():
        mode.pop("closures", None)
    if rule is not None:
        world_map.catalogues["route_modes"][mode_id]["closures"] = [rule]
    return world_map


class ExpectedWaitTests(unittest.TestCase):
    def test_wait_is_the_chance_of_arriving_closed_times_half_the_closure(self):
        self.assertAlmostEqual(routes_seasons.expected_wait_days(120, 500, 500), 120 / 365 * 60)

    def test_a_short_hop_pays_its_share_of_the_wait_span(self):
        whole = routes_seasons.expected_wait_days(120, 500, 500)
        self.assertAlmostEqual(routes_seasons.expected_wait_days(120, 250, 500), whole / 2)

    def test_no_closure_no_wait(self):
        self.assertEqual(routes_seasons.expected_wait_days(0, 500, 500), 0.0)


class SeasonalRouteTests(unittest.TestCase):
    def haul(self, world_map, modes):
        return routes_search.route(world_map, ["a1"], ["b1"], modes, mode_costs=PRICES, handling_costs={})

    def test_a_closed_sea_lane_takes_longer_and_costs_more_than_the_open_lane(self):
        open_haul = self.haul(closed_map(), {"sail"})
        closed_haul = self.haul(closed_map("sail", LANE), {"sail"})
        self.assertGreater(closed_haul["days"], open_haul["days"])
        self.assertGreater(closed_haul["cost_per_tonne"], open_haul["cost_per_tonne"])
        self.assertGreater(closed_haul["legs"][0]["wait_days"], 0.0)
        self.assertNotIn("wait_days", open_haul["legs"][0])

    def test_a_closed_pass_diverts_to_the_open_lane_when_that_is_cheaper(self):
        modes = {"foot", "sail"}
        prices = {"foot": 1.0, "sail": 1.05}
        open_haul = routes_search.route(closed_map(), ["a1"], ["b1"], modes, mode_costs=prices, handling_costs={})
        self.assertEqual([leg["mode"] for leg in open_haul["legs"]], ["foot"])
        shut = routes_search.route(closed_map("foot", PASS), ["a1"], ["b1"], modes, mode_costs=prices,
                                   handling_costs={})
        self.assertEqual([leg["mode"] for leg in shut["legs"]], ["sail"])

    def test_a_rule_whose_condition_fails_changes_nothing(self):
        rule = dict(LANE, coldest_month_c_below=-100)
        self.assertEqual(self.haul(closed_map("sail", rule), {"sail"}), self.haul(closed_map(), {"sail"}))

    def test_other_modes_are_unchanged(self):
        self.assertEqual(self.haul(closed_map("sail", LANE), {"foot"}), self.haul(closed_map(), {"foot"}))

    def test_the_cost_search_agrees_with_the_full_search(self):
        world_map = closed_map("sail", LANE)
        costs = routes_search.costs_from(world_map, ["a1"], {"sail"}, mode_costs=PRICES, handling_costs={})
        self.assertAlmostEqual(costs["b1"], self.haul(world_map, {"sail"})["cost_per_tonne"])


class ShippedDataTests(unittest.TestCase):
    def test_every_shipped_closure_is_sourced_and_labelled(self):
        found = 0
        for mode_id, mode in routes_modes.modes(queries._map(None)).items():
            for rule in mode.get("closures", ()):
                found += 1
                for field in ("id", "closed_days_per_year", "wait_span_km", "kind", "conf", "source", "why"):
                    self.assertTrue(rule.get(field), (mode_id, field))
                self.assertLess(rule["closed_days_per_year"], 365)
        self.assertGreater(found, 0)


if __name__ == "__main__":
    unittest.main()
