"""What the protocol tells a fogged player: the revenue range, when it becomes exact, the road progress count and the
society's values. Each rule is called on a stand-in game carrying only what it reads."""

QUICK_TOPIC = True

import types
import unittest

from sim.ui.proto.economy import _agent_values
from sim.ui.proto.state import _agent_state_goal
from sim.ui.proto.techtree import _fog_revenue_estimate, _revenue_known_exactly
from sim.tests.ui_stand_in import Game


def game(nodes, goal="goal", civ_id="rome", done=(), granted=(), done_year=None, year=100, fog=True, closure=None):
    return Game(
        nodes=nodes, civ={"id": civ_id}, goal=goal, cfg={"start_capital": 5000.0}, done=set(done),
        granted=set(granted), done_year=done_year or {}, year=year, fog=fog, goal_year=None, manual=False,
        goal_closure=closure, value_weights={}, state=Game())


def many_nodes(count=40, confidence="B"):
    return {"n%d" % i: {"name": "n%d" % i, "rev": 100.0 + 37.0 * i, "conf": confidence} for i in range(count)}


class FogRevenueEstimate(unittest.TestCase):

    def test_a_range_with_low_below_high_contains_the_true_revenue(self):
        nodes = many_nodes()
        sim = game(nodes)
        for node_id, node in nodes.items():
            low, high = _fog_revenue_estimate(sim, node_id)
            self.assertLess(low, high)
            self.assertLessEqual(low, node["rev"])
            self.assertGreaterEqual(high, node["rev"])

    def test_the_same_game_asked_twice_gets_the_same_range(self):
        sim = game(many_nodes())
        self.assertEqual(_fog_revenue_estimate(sim, "n3"), _fog_revenue_estimate(sim, "n3"))

    def test_a_different_civilisation_is_not_guaranteed_the_same_range(self):
        nodes = many_nodes()
        same = sum(_fog_revenue_estimate(game(nodes), key) == _fog_revenue_estimate(game(nodes, civ_id="han"), key)
                   for key in nodes)
        self.assertLess(same, len(nodes))

    def test_most_ranges_are_not_centred_on_the_truth(self):
        nodes = many_nodes()
        sim = game(nodes)
        off_centre = 0
        for node_id, node in nodes.items():
            low, high = _fog_revenue_estimate(sim, node_id)
            off_centre += (node["rev"] - low) != (high - node["rev"])
        self.assertGreaterEqual(off_centre, len(nodes) * 0.5)

    def test_a_worse_attested_figure_gets_a_wider_range(self):
        widths = {}
        for confidence in ("A", "B", "C"):
            low, high = _fog_revenue_estimate(game(many_nodes(confidence=confidence)), "n20")
            widths[confidence] = high - low
        self.assertLess(widths["A"], widths["B"])
        self.assertLess(widths["B"], widths["C"])

    def test_a_thing_that_earns_nothing_has_no_range(self):
        self.assertIsNone(_fog_revenue_estimate(game({"n": {"name": "n", "rev": 0.0}}), "n"))


class RevenueKnownExactly(unittest.TestCase):

    def test_a_node_not_done_is_a_guess(self):
        self.assertFalse(_revenue_known_exactly(game({}), "n"))

    def test_a_granted_node_is_known(self):
        self.assertTrue(_revenue_known_exactly(game({}, done={"n"}, granted={"n"}), "n"))

    def test_a_node_finished_this_year_is_still_a_guess(self):
        self.assertFalse(_revenue_known_exactly(game({}, done={"n"}, done_year={"n": 100}), "n"))

    def test_a_node_run_for_three_years_is_known(self):
        self.assertFalse(_revenue_known_exactly(game({}, done={"n"}, done_year={"n": 98}), "n"))
        self.assertTrue(_revenue_known_exactly(game({}, done={"n"}, done_year={"n": 97}), "n"))


class RoadProgress(unittest.TestCase):

    def road_game(self, fog, done):
        nodes = {"goal": {"name": "The Goal"}, "a": {"name": "a"}, "b": {"name": "b"}}
        return game(nodes, fog=fog, done=done, closure={"goal", "a", "b"})

    def test_under_fog_the_count_of_the_road_held_is_given_and_never_the_total(self):
        sim = self.road_game(True, {"a"})
        out = _agent_state_goal(sim, sim.nodes, None)
        self.assertEqual(out["on_the_road_to_the_goal_so_far"], 1)
        self.assertNotIn("the_whole_road_was", out)

    def test_with_fog_off_the_field_is_absent(self):
        sim = self.road_game(False, {"a"})
        self.assertIsNone(_agent_state_goal(sim, sim.nodes, None)["on_the_road_to_the_goal_so_far"])


class SocietyValues(unittest.TestCase):

    def test_every_weight_is_listed_with_its_number_sorted_by_field(self):
        sim = game({})
        sim.value_weights = {"w_novelty": 0.123456, "w_commerce": 1.0, "_hidden": 5.0}
        rows = _agent_values(sim)["values"]
        self.assertEqual([row["field"] for row in rows], ["w_commerce", "w_novelty"])
        self.assertEqual(rows[1]["value"], 0.123)


if __name__ == "__main__":
    unittest.main()
