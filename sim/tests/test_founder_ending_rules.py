"""Founder age, the dissolution's survivors, the victory block and `finish` (Complaints 220 to 264), each rule called on a
stand-in game that holds only what it reads. The mortality step is in test_founder_death_rules, what dissolution may forget
in test_losable_nodes."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.seats import founder_rules
from sim.seats.api import SeatsSeat
from sim.seats.module import Seats
from sim.tests import module_harness
from sim.ui.proto import dispatch, dispatch_inspection, score, state
from sim.tests.ui_stand_in import Game


class FounderAgeTests(unittest.TestCase):
    def reply(self, immortal, alive):
        game = Game(
            cfg={"immortal": immortal, "founder_arrival_age": 40, "founder_life_mean": 30, "founder_life_sd": 5},
            founder_alive=alive, founder_age=lambda: 47, view=lambda name: (lambda: {"scholars": 0.0, "artisans": 0.0, "directors_extra": 0.0, "slaves": 0, "freedmen": 0, "employees": {}}),
            state=Game(acting_seat=0), seat_list=lambda: {"joined": [0]})
        with mock.patch.object(state, "succession_block", return_value={}), \
             mock.patch.object(state, "_founder_death_info", return_value=None):
            return state._agent_state_founder(game)

    def test_a_living_mortal_founder_carries_the_age_as_a_number(self):
        self.assertEqual(self.reply(immortal=False, alive=True)["founder_age"], 47)

    def test_an_immortal_founder_carries_no_age(self):
        self.assertIsNone(self.reply(immortal=True, alive=True)["founder_age"])


class DissolutionSurvivorsTests(unittest.TestCase):
    def test_a_dispersed_corpus_changes_what_the_ending_says_survived(self):
        survived = founder_rules.what_survived(True, 1)
        forgotten = founder_rules.what_survived(False, 1)
        self.assertNotEqual(survived, forgotten)  # presentation: the ending sentence is the only exposure of the branch taken
        self.assertIn("1 works", survived)  # presentation: the count of the founder's works named

    def test_the_module_counts_only_the_works_the_founder_built(self):
        module = module_harness.build(Seats, seat=SeatsSeat(), views={
            "techniques_held": {"corpus_dispersed", "plain"}, "techniques_granted": {"plain"},
            "corpus_dispersed": lambda node_id: node_id == "corpus_dispersed"})
        self.assertEqual(module._survivors(), founder_rules.what_survived(True, 1))


class VictoryReportTests(unittest.TestCase):
    def report(self, total):
        game = Game(goal_year=130, cfg={"start_year": 100})
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
        game = Game(year=140, dead_reason=None)
        with mock.patch.object(dispatch_inspection, "final_report", return_value={"score": {"total": 0.4}}):
            reply = dispatch_inspection._cmd_finish(game, {}, {}, ended)
        return game, reply

    def test_finishing_a_live_run_ends_it_and_gives_the_score(self):
        game, reply = self.finish(ended=None)
        self.assertTrue(game.sent[0].reason)
        self.assertEqual((reply["ok"], reply["score"]["total"]), (True, 0.4))

    def test_finishing_an_ended_run_keeps_its_reason(self):
        game, _ = self.finish(ended="the horizon")
        self.assertEqual(game.sent, [])

    def test_an_ended_run_refuses_a_step(self):
        self.assertIs(dispatch._cmd_step(Game(), {}, {"years": 1}, "the founder died")["ok"], False)


if __name__ == "__main__":
    unittest.main()
