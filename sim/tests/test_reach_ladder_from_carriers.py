"""Complaints/416: the reach ladder is derived from the carriers' own days per tile, not from two
labelled parameters."""
QUICK_TOPIC = True

import unittest

from sim.geography import api, reach_bands, routes_graph, routes_modes, routes_rates


def _mean_km(world_map, edge_class):
    kms = [edge.km for edge in routes_graph.graph(world_map).edges if edge.edge_class == edge_class]
    return sum(kms) / len(kms)


def _level_pace(world_map, mode_id, edge_class):
    mode = routes_modes.modes(world_map)[mode_id]
    return routes_rates.compute_rate(world_map, mode, edge_class, 0.0, 0.0).km_per_day


class ReachLadderTests(unittest.TestCase):

    def setUp(self):
        self.world_map = api.open_map()

    def test_no_ladder_parameter_is_authored(self):
        ids = set(self.world_map.catalogue("parameters"))
        self.assertFalse({"reach_band_first_days", "reach_band_ratio"} & ids)

    def test_the_first_step_is_the_days_the_slowest_coastal_carrier_takes_over_a_typical_coastal_hop(self):
        slowest = min(_level_pace(self.world_map, mode_id, "coast")
                      for mode_id, mode in routes_modes.modes(self.world_map).items() if "coast" in mode["edge_classes"])
        first, _ratio = reach_bands.ladder(self.world_map)
        self.assertAlmostEqual(first, _mean_km(self.world_map, "coast") / slowest)

    def test_each_step_multiplies_by_the_spread_of_the_carriers_paces(self):
        paces = [routes_rates.compute_rate(self.world_map, mode, edge_class, 0.0, 0.0).km_per_day
                 for mode in routes_modes.modes(self.world_map).values() for edge_class in mode["edge_classes"]]
        steps = reach_bands.farthest_level(self.world_map) - 2
        _first, ratio = reach_bands.ladder(self.world_map)
        self.assertAlmostEqual(ratio ** steps, max(paces) / min(paces))

    def test_levels_rise_with_days_and_a_place_no_route_joins_is_the_farthest(self):
        first, ratio = reach_bands.ladder(self.world_map)
        top = reach_bands.farthest_level(self.world_map)
        self.assertEqual(reach_bands.level_of(self.world_map, 0.0), 0)
        self.assertEqual(reach_bands.level_of(self.world_map, first), 1)
        self.assertEqual(reach_bands.level_of(self.world_map, first * ratio * 0.99), 2)
        levels = [reach_bands.level_of(self.world_map, first * ratio ** step) for step in range(top + 2)]
        self.assertEqual(levels, sorted(levels))
        self.assertEqual(reach_bands.level_of(self.world_map, None), top)
        self.assertEqual(reach_bands.level_of(self.world_map, first * ratio ** top), top)


if __name__ == "__main__":
    unittest.main()
