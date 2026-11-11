"""relevant_nodes lists the tech nodes a route search can read (a sea leg's lane nodes and a mode's required nodes), and the
compiled graph is shared by held sets that differ only outside it."""

QUICK_TOPIC = True

import unittest

from sim.geography import routes_compile, routes_graph, routes_modes
from sim.geography.map_source import load_map


class RelevantNodesTest(unittest.TestCase):
    def setUp(self):
        self.world_map = load_map()

    def test_relevant_nodes_cover_every_edge_lane_and_mode_requirement(self):
        relevant = routes_compile.relevant_nodes(self.world_map)
        for edge in routes_graph.graph(self.world_map).edges:
            self.assertLessEqual(edge.lane_nodes, relevant)
        for mode in routes_modes.modes(self.world_map).values():
            self.assertLessEqual(frozenset(mode.get("requires_nodes") or ()), relevant)

    def test_held_sets_differing_outside_the_relevant_nodes_share_one_compiled_graph(self):
        relevant = routes_compile.relevant_nodes(self.world_map)
        modes = sorted(routes_modes.modes(self.world_map))[:1]
        first = routes_compile.compiled_for(self.world_map, modes, {}, None, None, relevant)
        again = routes_compile.compiled_for(self.world_map, modes, {}, None, None, relevant | {"not_a_node_any_edge_needs"})
        self.assertIs(first, again)


if __name__ == "__main__":
    unittest.main()
