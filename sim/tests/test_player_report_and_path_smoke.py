"""SMOKE: the end-of-run report, `why` (its full-chain figures) and `path` on unopened Rome games, reading the reply's fields. The
rules under the replies are the tree and protocol topics. No years run."""
import unittest

from sim.engine.data import closure
from sim.knowledge.api import LearnTechnique
from sim.tests.harness import GOAL, NODES, S, unopened_sim
from sim.ui.proto.score import final_report


def _ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


class EndOfRunTest(unittest.TestCase):
    def test_the_report_gives_the_whole_road_and_the_steps_that_would_have_come_next_and_no_advice_is_given(self):
        game = unopened_sim()
        game.year = 9999
        report = final_report(game, NODES)
        self.assertEqual(report["the_whole_road_was"], len(closure(NODES, GOAL)))
        self.assertIsNotNone(report["still_to_build_when_it_ended"])
        self.assertTrue(report["the_next_things_would_have_been"])
        self.assertIsNone(S._agent_state(game, NODES).get("stuck"))


class PathAndWhyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = unopened_sim()

    def test_the_chain_behind_a_node_is_the_sum_of_what_each_of_them_would_cost(self):
        reply = _ask(self.game, cmd="why", id="telescope")
        behind = sorted(closure(NODES, "telescope") - {"telescope"} - set(self.game.done))
        self.assertAlmostEqual(reply["chain_cost"], sum(self.game.view("project_cost")(node_id) for node_id in behind), delta=0.5)

    def test_the_chain_counts_down_as_prerequisites_are_built_and_the_whole_road_stays_the_same(self):
        before = _ask(self.game, cmd="why", id="telescope")
        for node_id in ("patron_local", "workshop_first", "identity_cover"):
            self.game.send(LearnTechnique(node_id))
        after = _ask(self.game, cmd="why", id="telescope")
        self.assertLess(after["chain_size"], before["chain_size"])
        self.assertLess(after["chain_founder_hours"], before["chain_founder_hours"])
        self.assertLess(after["chain_cost"], before["chain_cost"])
        self.assertEqual(after["chain_size_counting_what_you_have_built"], before["chain_size_counting_what_you_have_built"])

    def test_path_names_what_on_the_route_is_shut_rather_than_unbuilt_and_how_to_reopen_it(self):
        game = unopened_sim()
        game.send(LearnTechnique("lead_chamber"))
        game.state.projects.mothballed.add("lead_chamber")
        reply = _ask(game, cmd="path", id=GOAL)
        self.assertIn("lead_chamber", reply.get("on_this_route_but_shut_down") or [])
        self.assertTrue(reply.get("reopen_them_with"))

if __name__ == "__main__":
    unittest.main()
