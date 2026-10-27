"""ui_anatomy: the `anatomy` command (Complaint 69). Complaint 640: the rules (the target and gap, the rows, the goal and
named forms, the fog) are called on a stand-in game that holds only what the command reads; the check that the
literacy anatomy reads the education screen's numbers is `test_the_literacy_rows_are_the_education_reports_numbers` here."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.ui.proto import anatomy as anatomy_module
from sim.ui.proto import command_registry
from sim.ui.proto.dispatch_anatomy import _cmd_anatomy
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed
from sim.tests.ui_stand_in import FactViews

_EDUCATION = {
    "literacy": {"general": 0.05, "general_ceiling": 0.4, "general_next_year": 0.06,
                 "elite": 0.2, "elite_ceiling": 0.5, "elite_next_year": 0.21},
    "schools": [{"flow_added": 1.0}, {"flow_added": 0.0}], "schooling_flow": 3.0,
    "effective_schooling_flow": 3.5, "printing_adopted": 0.0, "farm_share_of_hours": 0.8,
    "literacy_limited_by": "schools", "recent_change": {"note": "no census yet"}}


class _Game(FactViews):
    """Only what the anatomy command reads."""

    def __init__(self, nodes, goal=None, fog=False, visible=(), done=(), civ=None, **attributes):
        self.nodes, self.goal, self.fog = nodes, goal, fog
        self._visible, self.done, self.civ = set(visible), set(done), civ or {}
        self.__dict__.update(attributes)

    def is_visible(self, node_id):
        return node_id in self._visible

    def literacy(self, kind):
        return _EDUCATION["literacy"]["general" if kind == "literacy_general" else "elite"]

    def hazard_relief(self, kind):
        return (0.7, "")

    def hazard_relief_entries(self, kind):
        return [{"label": "clean water", "factor": 0.8, "node": "water"},
                {"label": "quarantine", "factor": 0.9, "node": "hidden_measure", "lapsed_node": True}]


def _goal(metric, value, source=None, **extra):
    condition = {"metric": metric, "op": ">=", "value": value, **({"source": source} if source else {}), **extra}
    return {"name": "Goal " + metric, "win_condition": condition}


def _ask(game, **fields):
    return _cmd_anatomy(game, game.nodes, dict(cmd="anatomy", **fields), None)


def _literacy_game(**options):
    return _Game({"lit": _goal("literacy_general", 0.2), "relief": _goal("epidemic_relief", 0.5)},
                 goal="lit", visible=("lit", "relief"), **options)


class TargetTests(unittest.TestCase):

    def test_a_higher_is_better_goal_below_its_target_has_a_gap_and_is_not_met(self):
        target = anatomy_module._target({"op": ">=", "value": 0.2}, 0.05)
        self.assertEqual((target["gap"], target["met"]), (0.15, False))

    def test_a_goal_at_or_past_its_target_has_no_gap_and_is_met(self):
        target = anatomy_module._target({"op": ">=", "value": 0.2}, 0.3)
        self.assertEqual((target["gap"], target["met"]), (0.0, True))

    def test_a_lower_is_better_goal_measures_its_gap_from_above(self):
        target = anatomy_module._target({"op": "<=", "value": 0.2}, 0.5)
        self.assertEqual((target["gap"], target["met"]), (0.3, False))

    def test_a_value_that_cannot_be_read_gives_no_gap_and_no_verdict(self):
        target = anatomy_module._target({"op": ">=", "value": 0.2}, None)
        self.assertEqual((target["gap"], target["met"]), (None, None))


class AnatomyForTests(unittest.TestCase):

    def test_a_directly_read_attribute_is_a_row_and_the_current_value(self):
        game = _Game({}, score=0.3)
        reply = anatomy_module.anatomy_for(game, {"metric": "score", "source": "attribute", "path": "score",
                                                   "op": ">=", "value": 0.5})
        self.assertEqual((reply["current"], reply["generic"], reply["target"]["gap"]), (0.3, False, 0.2))
        self.assertEqual([row["value"] for row in reply["rows"]], [0.3])

    def test_a_metric_with_no_breakdown_is_generic_with_its_target_and_a_note(self):
        reply = anatomy_module.anatomy_for(_Game({}), {"metric": "mod_metric", "op": ">=", "value": 0.5})
        self.assertTrue(reply["generic"])
        self.assertEqual((reply["current"], reply["target"]["value"], reply["rows"]), (None, 0.5, []))
        self.assertIn("note", reply)

    def test_the_literacy_rows_are_the_education_reports_numbers(self):
        game = _literacy_game()
        with mock.patch.object(anatomy_module, "education_report", lambda sim: _EDUCATION):
            reply = _ask(game)
        rows = {row["label"]: row["value"] for row in reply["rows"]}
        self.assertEqual(reply["current"], _EDUCATION["literacy"]["general"])
        self.assertEqual(rows["current"], _EDUCATION["literacy"]["general"])
        self.assertEqual(rows["ceiling"], _EDUCATION["literacy"]["general_ceiling"])
        self.assertEqual(rows["schools running"], 1)
        self.assertEqual(rows["farm share of working hours"], _EDUCATION["farm_share_of_hours"])

    def test_the_elite_form_answers_with_its_own_rows(self):
        game = _literacy_game()
        with mock.patch.object(anatomy_module, "education_report", lambda sim: _EDUCATION):
            reply = _ask(game, what="literacy_elite")
        self.assertEqual((reply["metric"], reply["current"]), ("literacy_elite", _EDUCATION["literacy"]["elite"]))

    def test_epidemic_relief_ends_with_its_total_and_hides_an_unseen_measure_under_fog(self):
        game = _literacy_game(fog=True)
        game.visible = None
        game._visible = {"lit", "relief", "water"}
        reply = _ask(game, what="epidemic_relief")
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["rows"][-1]["value"], round(1.0 - 0.7, 4))
        labels = [row["label"] for row in reply["rows"]]
        self.assertIn("clean water", labels)
        # presentation: the label standing in for a measure the player cannot see
        self.assertIn("an unseen measure", labels)
        self.assertNotIn("quarantine", labels)


class FormsTests(unittest.TestCase):

    def test_a_research_goal_is_pointed_to_path_and_leverage(self):
        game = _Game({"research": {"name": "R"}}, goal="research", visible=("research",))
        reply = _ask(game)
        self.assertTrue(reply["ok"] and reply["research_goal"])

    def test_an_unknown_metric_is_refused(self):
        self.assertFalse(_ask(_literacy_game(), what="no_such_metric")["ok"])

    def test_the_listing_names_the_metrics_goals_measure_and_those_with_a_breakdown(self):
        reply = _ask(_literacy_game(), what="list")
        self.assertIn("literacy_general", reply["metrics"])
        self.assertIn("literacy_general", reply["with_breakdown"])

    def test_a_metric_only_a_mod_goal_names_is_known_and_answered_with_that_goals_target(self):
        game = _Game({"probe": _goal("mod_probe", 0.5)}, goal="probe", visible=("probe",))
        reply = _ask(game, what="mod_probe")
        self.assertTrue(reply["generic"])
        self.assertEqual(reply["target"]["value"], 0.5)

    def test_under_fog_a_goal_that_is_not_in_view_is_refused_with_a_cause(self):
        game = _literacy_game(fog=True)
        game._visible = set()
        reply = _ask(game)
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"].cause, "goal_out_of_view")

    def test_under_fog_a_named_metric_is_still_answered(self):
        game = _literacy_game(fog=True)
        game._visible = {"lit"}
        with mock.patch.object(anatomy_module, "education_report", lambda sim: _EDUCATION):
            self.assertTrue(_ask(game, what="literacy_elite")["ok"])

    def test_under_fog_the_metrics_of_goals_out_of_view_are_not_listed(self):
        game = _Game({"probe": _goal("mod_probe", 0.5)}, goal="probe", fog=True, visible=())
        self.assertNotIn("mod_probe", anatomy_module.known_metrics(game))


class CommandRegistryTests(unittest.TestCase):

    def test_anatomy_and_its_aliases_clash_with_no_other_command(self):
        entry = command_registry.COMMANDS["anatomy"]
        clash = [word for word in ("anatomy",) + tuple(entry["aliases"])
                 if sum(1 for name, other in command_registry.COMMANDS.items()
                        if word == name or word in other["aliases"]) != 1]
        self.assertEqual(clash, [])

    def test_the_typed_line_carries_the_named_metric(self):
        self.assertEqual(parse_typed("anatomy literacy_general")[0], {"cmd": "anatomy", "what": "literacy_general"})


class RenderTests(unittest.TestCase):
    """The screen, on hand-written replies; the subject is presentation."""

    def test_the_screen_shows_target_current_value_and_the_gap_and_lists_each_row(self):
        reply = {"ok": True, "metric": "literacy_general", "description": "literacy reaches 20%",
                 "current": 0.05, "target": {"op": ">=", "value": 0.2, "gap": 0.15, "met": False},
                 "rows": [{"label": "ceiling", "value": 0.4, "unit": "fraction", "note": "most it can reach"},
                          {"label": "schools running", "value": 0, "unit": "schools", "note": ""}],
                 "generic": False}
        text = render_pretty("anatomy", reply)
        # presentation: percentages, points to go and row labels are what a player reads
        for word in ("5.00%", "20.00%", "15.00 points to go", "ceiling", "40.00%", "schools running"):
            self.assertIn(word, text)

    def test_a_generic_reply_renders_with_its_no_breakdown_sentence_and_an_unknown_value(self):
        reply = {"ok": True, "metric": "mod_metric", "description": None, "current": None,
                 "target": {"op": ">=", "value": 0.5, "gap": None, "met": None}, "rows": [],
                 "generic": True, "note": "no breakdown is available for this metric yet"}
        text = render_pretty("anatomy", reply)
        # presentation: the sentence and the word for an unreadable value
        self.assertIn("no breakdown", text)
        self.assertIn("unknown", text)

    def test_a_research_goal_reply_renders_its_pointer(self):
        text = render_pretty("anatomy", {"ok": True, "research_goal": True, "note": "see path and leverage"})
        self.assertIn("leverage", text)   # presentation: the pointer's wording


if __name__ == "__main__":
    unittest.main()
