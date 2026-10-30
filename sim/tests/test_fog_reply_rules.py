"""What a fogged reply may say, each rule called on a stand-in game that holds only what it reads (Complaint 640):
`path` is switched off under fog, the goal is named but never its id, a refusal of an unheard-of name cannot be told
from a refusal of a name that does not exist, a held node is not also missing something, and the digest ranks leverage
before price. The id-filtering of `missing_prereq_message` and `bounty_refusal` is in test_fog_leak3."""
QUICK_TOPIC = True

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.refusal import cause_of
from sim.ui.proto import command_registry, techtree
from sim.ui.proto.dispatch import KNOWN_COMMANDS, _agent_dispatch_inner
from sim.ui.proto.dispatch_inspection_path import _cmd_path
from sim.ui.proto.nodes import _did_you_mean
from sim.ui.proto.state import _agent_state_goal

from .harness import GOAL, NODES
from sim.tests.ui_stand_in import Game

PREREQUISITES_OF_GOAL = list(NODES[GOAL]["pre"])


def fogged_stand_in(heard=()):
    return Game(nodes=NODES, fog=True, goal=GOAL, done=set(), active={}, revealed=set(heard),
                           is_visible=lambda node_id, _memo=None: node_id in heard)


def dispatch(game, command, node_id):
    with mock.patch("sim.ui.proto.dispatch.material_story", return_value=None):
        return _agent_dispatch_inner(game, NODES, {"cmd": command, "id": node_id})


class PathUnderFogTests(unittest.TestCase):
    def test_path_is_refused_wholesale_whether_or_not_the_node_is_done(self):
        for done in (set(), {"identity_cover"}):
            game = Game(fog=True, goal=GOAL, done=done)
            reply = _cmd_path(game, NODES, {"id": "identity_cover"}, None)
            self.assertIs(reply["ok"], False)
            self.assertNotIn("remaining", reply)


class UnknownCommandTests(unittest.TestCase):
    def test_the_refusal_names_every_command_there_is(self):
        error = command_registry.unknown_command_error("frobnicate")
        missing = [command for command in KNOWN_COMMANDS if command != "quit" and command not in error]
        self.assertEqual(missing, [])  # presentation: the hint is a sentence that must list every command


class GoalUnderFogTests(unittest.TestCase):
    def test_goal_id_is_withheld_and_its_name_is_given(self):
        game = Game(cfg={"immortal": True}, fog=True, goal=GOAL, nodes=NODES, goal_year=None,
                               manual=True, done=set())
        with mock.patch("sim.ui.proto.state._goal_progress_count", return_value=0):
            reply = _agent_state_goal(game, NODES, None)
        self.assertIsNone(reply["goal"])
        self.assertEqual(reply["goal_in_words"], NODES[GOAL]["name"])

    def test_every_command_but_why_refuses_the_goal_without_naming_what_it_rests_on(self):
        game = fogged_stand_in()
        for command in ("bounty", "start", "mothball"):
            reply = dispatch(game, command, GOAL)
            self.assertEqual(cause_of(reply["error"]), "goal_not_yet_actionable")
            self.assertEqual([prereq for prereq in PREREQUISITES_OF_GOAL if prereq in json.dumps(str(reply["error"]))], [])


class RefusalsAreAlikeTests(unittest.TestCase):
    def test_a_name_not_heard_of_and_a_name_that_does_not_exist_get_the_same_refusal(self):
        game = fogged_stand_in()
        replies = [dispatch(game, "why", word)["error"] for word in ("telescope", "zzzznotathing", "dynamo")]
        self.assertEqual({cause_of(error) for error in replies}, {"never_heard_of"})
        self.assertEqual({str(error).split("Among the things")[0] for error in replies}, {str(replies[0]).split("Among the things")[0]})
        self.assertEqual([error.choices for error in replies], [[], [], []])

    def test_a_misspelling_offers_nothing_the_player_has_not_heard_of(self):
        tree = {"transistor_a": {}, "transistor_b": {}, "vacuum_tube": {}}
        for word in ("transistor", "vacuum", "semiconductor"):
            self.assertEqual(_did_you_mean(word, tree, sim=fogged_stand_in()), [])

    def test_a_typo_in_a_heard_of_name_gets_the_real_suggestion(self):
        tree = {"ag2_marling": {}, "ag2_reaper": {}}
        self.assertEqual(_did_you_mean("ag2_marlingg", tree, sim=Game(fog=False)), ["ag2_marling"])


class HeldNodeTests(unittest.TestCase):
    NODE = {"pre": ["cap_heat_1100"]}

    def game(self, granted):
        return Game(fog=False, granted=set(granted), done={"cap_heat_1300"})

    def test_a_granted_node_is_held_and_missing_nothing(self):
        game = self.game({"cap_heat_1300"})
        with mock.patch.object(techtree.ui_port, "prerequisite_names", return_value=[]):
            reply = techtree._explain_visible_prerequisites(game, {}, "cap_heat_1300", self.NODE)
        self.assertEqual(reply["missing_prerequisites"], [])
        self.assertIs(techtree._explain_grant_route(game, {}, "cap_heat_1300", self.NODE)["held_without_building_it"], True)

    def test_a_node_not_granted_still_lists_what_it_misses(self):
        with mock.patch.object(techtree.ui_port, "prerequisite_names", return_value=[]):
            reply = techtree._explain_visible_prerequisites(self.game(set()), {}, "cap_heat_1300", self.NODE)
        self.assertEqual(reply["missing_prerequisites"], ["cap_heat_1100"])


class AvailableDigestTests(unittest.TestCase):
    TREE = {name: {"id": name, "name": name, "cat": "c", "ph": 1, "yrs": 1, "risk": 0.1}
            for name in ("cheap_spine", "dear_spine", "cheap_leaf", "dear_leaf")}
    COST = {"cheap_spine": 1.0, "dear_spine": 90.0, "cheap_leaf": 2.0, "dear_leaf": 80.0}
    RESTS = {"cheap_spine": 50, "dear_spine": 40, "cheap_leaf": 0, "dear_leaf": 0}

    def game(self):
        return Game(project_cost=self.COST.get, effective_risk=lambda node_id: 0.1,
                               failure_loss=lambda node_id: 1.0, venture_real_earnings=lambda node_id: 7.0,
                               venture_upkeep_quote=lambda node_id: {"now": 3.0, "at_full_staffing": 4.0})

    def test_leverage_is_picked_before_price_so_a_cheap_spine_node_is_not_hidden(self):
        with mock.patch.object(techtree, "downstream_count", lambda nodes, node_id: self.RESTS[node_id]):
            leverage, cheap = techtree._digest_leverage_and_cheap(self.game(), self.TREE, list(self.TREE))
        self.assertEqual(leverage[:2], ["cheap_spine", "dear_spine"])
        self.assertTrue(set(leverage).isdisjoint(cheap))

    def test_a_fogged_row_shows_what_it_earns_what_it_costs_after_and_what_rests_on_it(self):
        with mock.patch.object(techtree, "downstream_count", lambda nodes, node_id: self.RESTS[node_id]), \
             mock.patch.object(techtree, "_fog_revenue_estimate", return_value=None), \
             mock.patch.object(techtree, "_staff_fields", return_value={}):
            row = techtree._brief(self.game(), self.TREE, "cheap_spine", True)
        self.assertEqual((row["earns_per_year"], row["costs_per_year_after"]), (7.0, 3.0))
        self.assertIn("how_much_rests_on_this", row)


if __name__ == "__main__":
    unittest.main()
