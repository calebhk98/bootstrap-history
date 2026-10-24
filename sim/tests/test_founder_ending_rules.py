"""Founder age, the dissolution's survivors, the victory block and `finish` (Complaints 220 to 264), each rule called on a
stand-in game that holds only what it reads. The mortality step is in test_founder_death_rules, what dissolution may forget
in test_losable_nodes."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine.core_step_phases import StepPhasesMixin
from sim.ui.proto import dispatch, dispatch_inspection, score, state


class FounderAgeTests(unittest.TestCase):
    def reply(self, immortal, alive):
        game = SimpleNamespace(
            cfg={"immortal": immortal, "founder_arrival_age": 40, "founder_life_mean": 30, "founder_life_sd": 5},
            founder_alive=alive, founder_age=lambda: 47, scholars=0.0, artisans=0.0, directors_extra=0.0,
            state=SimpleNamespace(acting_seat=0, seats=[0]))
        with mock.patch.object(state, "succession_block", return_value={}), \
             mock.patch.object(state, "_founder_death_info", return_value=None):
            return state._agent_state_founder(game)

    def test_a_living_mortal_founder_carries_the_age_as_a_number(self):
        self.assertEqual(self.reply(immortal=False, alive=True)["founder_age"], 47)

    def test_an_immortal_founder_carries_no_age(self):
        self.assertIsNone(self.reply(immortal=True, alive=True)["founder_age"])


class DissolutionSurvivorsTests(unittest.TestCase):
    def game(self, dispersed):
        projects = SimpleNamespace(done={"corpus_dispersed", "plain"}, granted={"plain"})
        return SimpleNamespace(state=SimpleNamespace(projects=projects),
                               corpus_is_dispersed=lambda node_id: node_id in dispersed)

    def test_a_dispersed_corpus_changes_what_the_ending_says_survived(self):
        survived = StepPhasesMixin._what_survived_the_dissolution(self.game({"corpus_dispersed"}))
        forgotten = StepPhasesMixin._what_survived_the_dissolution(self.game(set()))
        self.assertNotEqual(survived, forgotten)  # presentation: the ending sentence is the only exposure of the branch taken
        self.assertIn("1 works", survived)  # presentation: the count of the founder's works named


class VictoryReportTests(unittest.TestCase):
    def report(self, total):
        game = SimpleNamespace(goal_year=130, cfg={"start_year": 100})
        report = {"goal_in_words": "Transistor", "points": 42.0, "total": total,
                  "achievements": {"won_one": {"won": True}, "lost_one": {"won": False}}}
        with mock.patch.object(score, "score_report", return_value=report):
            return score.victory_report(game, {})

    def test_it_carries_the_year_the_years_taken_the_points_and_the_achievements_won(self):
        out = self.report(total=None)
        self.assertEqual((out["year"], out["elapsed_years"], out["points_so_far"], out["achievements"], out["goal_in_words"]),
                         (130, 30, 42.0, ["won_one"], "Transistor"))

    def test_a_withheld_total_is_told_differently_from_a_shown_one(self):
        self.assertNotEqual(self.report(None)["to_see_your_score"], self.report(0.5)["to_see_your_score"])


class FinishTests(unittest.TestCase):
    def finish(self, ended):
        game = SimpleNamespace(year=140, dead_reason=None)
        with mock.patch.object(dispatch_inspection, "final_report", return_value={"score": {"total": 0.4}}):
            reply = dispatch_inspection._cmd_finish(game, {}, {}, ended)
        return game, reply

    def test_finishing_a_live_run_ends_it_and_gives_the_score(self):
        game, reply = self.finish(ended=None)
        self.assertTrue(game.dead_reason)
        self.assertEqual((reply["ok"], reply["score"]["total"]), (True, 0.4))

    def test_finishing_an_ended_run_keeps_its_reason(self):
        game, _ = self.finish(ended="the horizon")
        self.assertIsNone(game.dead_reason)

    def test_an_ended_run_refuses_a_step(self):
        self.assertIs(dispatch._cmd_step(SimpleNamespace(), {}, {"years": 1}, "the founder died")["ok"], False)


if __name__ == "__main__":
    unittest.main()
