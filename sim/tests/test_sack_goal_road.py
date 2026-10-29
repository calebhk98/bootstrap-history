"""A sack's report counts the lost technologies standing on the road to the goal it is asked about now (Complaint 765:
the hazards module kept the first goal's road for the rest of the game, whatever the goal or the seat)."""
QUICK_TOPIC = True

import unittest

from sim.reporting.api import RecordEvent
from sim.tests import hazards_host, module_harness


class SackGoalRoad(unittest.TestCase):

    def on_road_reported(self, roads, goals):
        """The `on_road` fact of one sack per goal in `goals`, asked in turn; `roads` maps a goal to the nodes it needs."""
        current = {"node": goals[0]}
        module = hazards_host.build(
            goal=lambda: current, tree_nodes={"first": {}, "second": {}},
            on_road_to_goal=lambda node_id: node_id in roads[current["node"]],
            mechanic=lambda name: {"corpus": []})
        reported = []
        for goal_node in goals:
            current["node"] = goal_node
            module.log_corpus_loss(["a", "b"], None)
            reported.append([command for command in module_harness.sent(module) if isinstance(command, RecordEvent)][-1].facts["on_road"])
        return reported

    def test_a_second_goal_is_counted_against_its_own_road(self):
        roads = {"first": {"a", "b"}, "second": {"a"}}
        self.assertEqual(self.on_road_reported(roads, ["first", "second"]), [2, 1])


if __name__ == "__main__":
    unittest.main()
