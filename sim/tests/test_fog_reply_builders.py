"""Fog in replies: no reply structure holds the id of a node the player has not heard of. Each test calls one function on
written-out known and hidden nodes and reads the returned values.

Which commands go through the shared filter and which build their own:

Shared filter (`scrub_hidden_ids`, reached through the module's `fog_scrub`; `missing_prereq_message` is the one way to turn a
missing list into words, tested in test_fog_leak3): `why` (start_blocked_reason and the blockers' text), `bounty`
(missing_prereq_message), `log` (_log_scrub), and every command that takes an id (the guard in the command dispatch,
tested in test_fog_reply_rules and test_names_and_fog).

Own builders, tested below: `why` (_explain_visible_prerequisites), `options` (_fogged), `commitments` (_goal, _institutions),
`education` (_schools), `note`/`notes` (_project_name, _entry, candidates), `goals watch` (_row), `why <metric>`
(_relief_rows, conditions_for_metric, known_metrics), `economy` (_power_tiers, _power_waiting_on), the list of nodes by
state (tree_filters._row), and the spelling suggestions (_did_you_mean)."""
QUICK_TOPIC = True

import json
import types
import unittest
from unittest import mock

from sim.knowledge.api import HIDDEN_ID_PLACEHOLDER, scrub_hidden_ids
from sim.knowledge.module import Knowledge
from sim.tests import module_harness
from sim.ui.proto import anatomy, economy, goals_watch, tree_filters
from sim.ui.proto.dispatch_notes import _entry, _project_name
from sim.ui.proto.dispatch_options import _fogged
from sim.ui.proto.nodes import _did_you_mean
from sim.ui.proto.notes_projects import candidates
from sim.ui.proto.screen_commitments import _goal, _institutions
from sim.ui.proto.screen_education import _schools
from sim.ui.proto.state_log import _log_scrub
from sim.ui.proto.techtree import _explain_visible_prerequisites
from sim.tests.ui_stand_in import Game

KNOWN, HIDDEN, HIDDEN_LONGER = "iron_smelting", "zz_hidden_theory", "zz_hidden_theory_applied"
IDS = {KNOWN: "Iron smelting", HIDDEN: "Hidden theory", HIDDEN_LONGER: "Hidden theory applied"}


def node(name, **fields):
    return dict({"name": name, "pre": [], "cat": "metallurgy", "kind": "ENGINEERING"}, **fields)


NODES = {node_id: node(name) for node_id, name in IDS.items()}


def seen(reply):
    """Every id of a hidden node found anywhere in a reply's values and keys, as whole words."""
    text = json.dumps(reply, sort_keys=True)
    return [node_id for node_id in (HIDDEN, HIDDEN_LONGER) if node_id in text]


def stand_in(fog=True, **fields):
    heard = fields.pop("heard", {KNOWN})
    game = Game(
        nodes=NODES, fog=fog, goal=HIDDEN_LONGER, done=set(), granted=set(), active={}, forgotten={},
        is_visible=lambda node_id, _memo=None: (not fog) or node_id in heard)
    game.__dict__.update(fields)
    return game


class SharedFilterTests(unittest.TestCase):

    def text(self):
        return "needs %s then %s and finally %s" % (HIDDEN_LONGER, KNOWN, HIDDEN)

    def test_scrub_replaces_each_hidden_id_and_keeps_the_known_one(self):
        scrubbed = scrub_hidden_ids(self.text(), NODES, lambda node_id: node_id == KNOWN)
        self.assertEqual(scrubbed, "needs %s then %s and finally %s" % (HIDDEN_ID_PLACEHOLDER, KNOWN, HIDDEN_ID_PLACEHOLDER))

    def test_scrub_with_everything_visible_changes_nothing(self):
        self.assertEqual(scrub_hidden_ids(self.text(), NODES, lambda node_id: True), self.text())

    def test_a_namespaced_id_is_not_a_hidden_id_with_a_prefix_in_it(self):
        text = "mod:%s and %s" % (HIDDEN, HIDDEN)
        self.assertEqual(scrub_hidden_ids(text, NODES, lambda node_id: False),
                         "mod:%s and %s" % (HIDDEN, HIDDEN_ID_PLACEHOLDER))

    def fog_scrub(self, text, fog=True):
        knowledge = module_harness.build(Knowledge, views={
            "legacy_fog": fog, "legacy_tree": NODES, "legacy_projects": Game(done=set(), active={}, revealed={KNOWN}),
            "start_check": lambda node_id, ignore_trade, memo, why: (False, None)})
        return knowledge.fog_scrub(text)

    def test_fog_scrub_hides_ids_the_player_has_not_heard_of(self):
        self.assertEqual(seen(self.fog_scrub(self.text())), [])

    def test_fog_scrub_passes_text_through_when_fog_is_off_and_when_there_is_none(self):
        self.assertEqual(self.fog_scrub(self.text(), fog=False), self.text())
        self.assertIsNone(self.fog_scrub(None))
        self.assertEqual(self.fog_scrub(""), "")


class LogScrubTests(unittest.TestCase):

    def test_ids_and_names_of_hidden_nodes_are_redacted_from_a_log_line(self):
        line = "completed: Hidden theory applied; %s unlocked Iron smelting" % HIDDEN
        game = stand_in()
        game.fog_scrub = lambda text: scrub_hidden_ids(text, NODES, game.is_visible)
        scrubbed = _log_scrub(game, line)
        self.assertEqual(seen(scrubbed), [])
        self.assertNotIn("Hidden theory", scrubbed)
        self.assertIn("Iron smelting", scrubbed)

    def test_a_forgotten_node_is_named_as_forgotten_not_as_unheard_of(self):
        game = stand_in(forgotten={HIDDEN: 100})
        game.fog_scrub = lambda text: text
        self.assertEqual(_log_scrub(game, "lost Hidden theory"), "lost something you have since forgotten")


class WhyPrerequisiteTests(unittest.TestCase):

    def nodes(self):
        target = node("Target", pre=[KNOWN, HIDDEN, HIDDEN_LONGER])
        return dict(NODES, target=target)

    def explain(self, **fields):
        game = stand_in(**fields)
        nodes = self.nodes()
        game.nodes = nodes
        with mock.patch("sim.ui.proto.techtree.ui_port.prerequisite_names",
                        lambda nodes, ids: {node_id: nodes[node_id]["name"] for node_id in ids}):
            return _explain_visible_prerequisites(game, nodes, "target", nodes["target"])

    def test_no_prerequisite_id_or_name_the_player_has_not_heard_of_is_listed_and_the_count_says_how_many(self):
        reply = self.explain()
        self.assertEqual(seen(reply), [])
        self.assertEqual(reply["direct_prerequisites"], [KNOWN])
        self.assertEqual(reply["missing_prerequisites"], [KNOWN])
        self.assertEqual(reply["prerequisite_names"], {KNOWN: "Iron smelting"})
        self.assertEqual(reply["prerequisites_you_have_not_heard_of"], 2)

    def test_a_granted_node_is_missing_nothing(self):
        self.assertEqual(self.explain(granted={"target"})["missing_prerequisites"], [])

    def test_with_fog_off_every_prerequisite_is_listed_and_no_count_is_given(self):
        reply = self.explain(fog=False)
        self.assertEqual(reply["direct_prerequisites"], [KNOWN, HIDDEN, HIDDEN_LONGER])
        self.assertIsNone(reply["prerequisites_you_have_not_heard_of"])


class OptionsAndScreensTests(unittest.TestCase):

    def test_a_setting_whose_value_is_a_hidden_node_shows_no_id(self):
        rows = _fogged(stand_in(), NODES, [{"key": "goal", "value": HIDDEN, "shown_as": HIDDEN},
                                          {"key": "other", "value": KNOWN, "shown_as": "plain text"}])
        self.assertEqual(seen(rows), [])
        self.assertEqual(rows[1], {"key": "other", "value": KNOWN, "shown_as": "plain text"})

    def test_the_commitments_goal_names_neither_id_nor_name_under_fog(self):
        reply = _goal(stand_in(goal_year=None))
        self.assertEqual((reply["id"], reply["name"]), (None, None))
        self.assertEqual(seen(reply), [])

    def test_the_commitments_goal_is_named_with_fog_off(self):
        reply = _goal(stand_in(fog=False, goal_year=None))
        self.assertEqual((reply["id"], reply["name"]), (HIDDEN_LONGER, "Hidden theory applied"))

    def test_institutions_list_only_the_ones_the_player_has_heard_of(self):
        nodes = {KNOWN: node("Iron smelting", kind="INSTITUTION"), HIDDEN: node("Hidden theory", kind="INSTITUTION")}
        game = stand_in(done={KNOWN, HIDDEN}, running=lambda node_id: True, institution_units=lambda node_id: 1.0)
        game.nodes = nodes
        rows = _institutions(game)
        self.assertEqual([row["id"] for row in rows], [KNOWN])
        self.assertEqual(seen(rows), [])

    def test_schools_list_only_the_ones_the_player_has_heard_of(self):
        game = stand_in(has=lambda node_id: True, running=lambda node_id: True, institution_units=lambda node_id: 1.0,
                        effect_holds=lambda node_id, spec: True, effect_value=lambda node_id, spec: 0.1)
        with mock.patch("sim.ui.proto.screen_education.ui_port.effect_terms",
                        lambda sim, kind: [(KNOWN, {}), (HIDDEN, {}), (HIDDEN_LONGER, {})]):
            rows = _schools(game)
        self.assertEqual([row["id"] for row in rows], [KNOWN])
        self.assertEqual(seen(rows), [])

    def test_a_watched_goal_the_player_has_not_heard_of_shows_progress_but_no_id_or_name(self):
        game = stand_in()
        with mock.patch.object(goals_watch.ui_port, "closure", lambda nodes, node_id: {node_id, KNOWN}):
            hidden_row = goals_watch._row(game, HIDDEN)
            known_row = goals_watch._row(game, KNOWN)
        self.assertEqual((hidden_row["id"], hidden_row["name"]), (None, None))
        self.assertEqual((hidden_row["done"], hidden_row["total"]), (0, 2))
        self.assertEqual((known_row["id"], known_row["name"]), (KNOWN, "Iron smelting"))
        self.assertEqual(seen([hidden_row]), [])


class NotesTests(unittest.TestCase):

    def test_a_hidden_project_has_no_name(self):
        self.assertIsNone(_project_name(stand_in(), HIDDEN))
        self.assertEqual(_project_name(stand_in(), KNOWN), "Iron smelting")
        self.assertEqual(_project_name(stand_in(fog=False), HIDDEN), "Hidden theory")

    def test_a_note_about_a_hidden_project_shows_the_text_but_not_the_project(self):
        reply = _entry(stand_in(), {"n": 1, "year": 100, "text": "remember", "project": HIDDEN})
        self.assertEqual(reply, {"n": 1, "year": 100, "text": "remember", "project": None, "project_name": None})

    def test_a_note_about_a_known_project_names_it(self):
        reply = _entry(stand_in(), {"n": 1, "year": 100, "text": "remember", "project": KNOWN})
        self.assertEqual((reply["project"], reply["project_name"]), (KNOWN, "Iron smelting"))

    def test_only_visible_nodes_are_candidates_for_a_typed_project(self):
        with mock.patch("sim.ui.proto.notes_projects.NODE_IDS_LOWER", {HIDDEN: HIDDEN, KNOWN: KNOWN}), \
                mock.patch("sim.ui.proto.notes_projects.NODE_NAME_NORM", {"hiddentheory": (HIDDEN,)}):
            self.assertEqual(candidates(stand_in(), HIDDEN), [])
            self.assertEqual(candidates(stand_in(), "Hidden theory"), [])
            self.assertEqual(candidates(stand_in(), KNOWN), [KNOWN])


class MetricAndEconomyTests(unittest.TestCase):

    def test_a_relief_measure_the_player_has_not_heard_of_is_called_an_unseen_measure(self):
        game = stand_in(hazard_relief_entries=lambda kind: [
            {"node": KNOWN, "label": "Iron smelting", "factor": 0.8},
            {"node": HIDDEN, "label": "Hidden theory", "factor": 0.5}])
        with mock.patch.object(anatomy, "current_value", lambda sim, condition: 0.5):
            rows = anatomy._relief_rows(game, {})
        self.assertEqual([row["label"] for row in rows[:2]], ["Iron smelting", "an unseen measure"])
        self.assertEqual(seen(rows), [])
        self.assertNotIn("Hidden theory", json.dumps(rows))

    def goals(self):
        goal = lambda value: {"metric": "population", "op": ">=", "value": value}
        return dict(NODES, **{HIDDEN: node("Hidden theory", win_condition=goal(0.9)),
                              KNOWN: node("Iron smelting", win_condition=goal(0.5))})

    def test_goals_for_a_metric_leave_out_the_hidden_ones(self):
        game = stand_in(nodes=self.goals())
        rows = anatomy.conditions_for_metric(game, "population")
        self.assertEqual([condition["value"] for condition, _ in rows], [0.5])
        self.assertEqual(seen(rows), [])

    def test_known_metrics_leave_out_a_metric_only_a_hidden_goal_measures(self):
        nodes = {HIDDEN: node("Hidden theory", win_condition={"metric": "secret_metric", "op": ">=", "value": 1}),
                 KNOWN: node("Iron smelting", win_condition={"metric": "open_metric", "op": ">=", "value": 1})}
        names = anatomy.known_metrics(stand_in(nodes=nodes))
        self.assertIn("open_metric", names)
        self.assertNotIn("secret_metric", names)

    def power_nodes(self):
        tier = lambda rank, scale: {"mechanics": {"power_tier": {"rank": rank, "label": scale + " power", "scale": scale}}}
        return {KNOWN: node("Water wheel", **tier(1, "workshop")), HIDDEN: node("Grid", **tier(2, "grid"))}

    def test_power_tiers_name_only_the_rungs_the_player_has_heard_of(self):
        nodes = self.power_nodes()
        game = stand_in(nodes=nodes, has=lambda node_id: node_id == KNOWN, installed_generation_kw_by_tier=lambda: {KNOWN: 5.0})
        tiers, highest = economy._power_tiers(game, nodes)
        self.assertEqual([tier["id"] for tier in tiers], [KNOWN])
        self.assertEqual(highest, "workshop power")
        self.assertEqual(seen(tiers), [])

    def test_projects_waiting_on_power_leave_out_hidden_ones(self):
        nodes = dict(self.power_nodes(), **{"seen_user": node("Seen user", pre=[KNOWN]),
                                            "hidden_user": node("Hidden user", pre=[KNOWN])})
        game = stand_in(nodes=nodes, heard={KNOWN, "seen_user"}, has=lambda node_id: False)
        reply = economy._power_waiting_on(game, nodes, False)
        self.assertEqual(json.dumps(reply).count("hidden_user"), 0)
        self.assertIn("seen_user", json.dumps(reply))


class ListAndSuggestionTests(unittest.TestCase):

    def test_a_blocked_row_lists_only_the_missing_prerequisites_it_may_name_and_counts_the_rest(self):
        nodes = dict(NODES, target=node("Target", pre=[KNOWN, HIDDEN, HIDDEN_LONGER]))
        game = stand_in(nodes=nodes, project_cost=lambda node_id: 10.0, start_reason=lambda node_id: (False, "blocked"),
                        stock_needed_by=lambda node_id: None)
        row = tree_filters._row(game, nodes, "target", "blocked")
        self.assertEqual(row["missing"], [KNOWN])
        self.assertEqual(row["hidden_missing"], 2)
        self.assertEqual(seen(row), [])

    def test_a_misspelling_is_never_answered_with_a_node_the_player_has_not_heard_of(self):
        reply = _did_you_mean("zz_hidden", NODES, sim=stand_in())
        self.assertEqual(reply, [])

    def test_the_same_misspelling_with_fog_off_finds_them(self):
        reply = _did_you_mean("zz_hidden", NODES, sim=stand_in(fog=False))
        self.assertEqual(sorted(reply), sorted([HIDDEN, HIDDEN_LONGER]))


if __name__ == "__main__":
    unittest.main()
