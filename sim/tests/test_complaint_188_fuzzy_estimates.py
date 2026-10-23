"""Complaint 188: labour needs shown as uncertain estimates while something is unknown (option `fuzzy_estimates`, off by
default). Only the display is fuzzy. The rules are the functions of sim/engine/fuzzy_estimates.py, called on a stand-in
for the game that holds only what they read (salt, done and active work, nodes). Whether a saved game keeps the option:
test_fuzzy_estimates_saved_rule."""
QUICK_TOPIC = True

import copy
import random
import unittest
from types import SimpleNamespace

from sim.engine import fuzzy_estimates as fuzzy
from sim.ui.proto.render_screen_why import _est, _est_tag

NODE_ID = "probe_work"
NODE = {"id": NODE_ID, "sch": 2, "art": 3, "ph": 400.0, "lab": {"smith": 120.0, "mason": 60.0}}
REAL_LAB = dict(NODE["lab"])


def game(salt=12345, enabled=True, done=(), active=None):
    """What the estimate functions read of a game."""
    return SimpleNamespace(state=SimpleNamespace(_fuzzy_estimates=enabled, _fuzzy_salt=salt,
                                                 scenario=SimpleNamespace(year=100)),
                           rng=random.Random(1), done=set(done), active=dict(active or {}),
                           nodes={NODE_ID: NODE, "other_work": dict(NODE, id="other_work")})


def why_reply():
    """The parts of a `why` reply the estimates rewrite."""
    return {"ok": True, "id": NODE_ID, "staff_needed": {"scholars": 2, "artisans": 3},
            "staff_to_keep_it_open": {"scholars": 1.0, "artisans": 2.0},
            "hired_labour": dict(REAL_LAB), "founder_hours": 400.0, "calendar_floor_years": 3.0,
            "cost": {"total": 1000.0, "labour": 600.0, "materials": 400.0},
            "failure_costs": 50.0, "failure_costs_hours": 40.0}


def figures(reply):
    flat = {"founder_hours": reply["founder_hours"], "calendar_floor_years": reply["calendar_floor_years"],
            "cost_total": reply["cost"]["total"], "scholars": reply["staff_needed"]["scholars"],
            "artisans": reply["staff_needed"]["artisans"], "keep_scholars": reply["staff_to_keep_it_open"]["scholars"],
            "keep_artisans": reply["staff_to_keep_it_open"]["artisans"]}
    for trade, hours in reply["hired_labour"].items():
        flat["hired:" + trade] = hours
    return flat


def fuzzed(sim_state, actor=None):
    return fuzzy.fuzz_why(sim_state, NODE_ID, why_reply(), actor)


class OptionOffTests(unittest.TestCase):
    def test_the_reply_is_untouched_with_the_option_off(self):
        reply = why_reply()
        self.assertEqual(fuzzy.fuzz_reply(game(enabled=False), "why", {}, copy.deepcopy(reply)), reply)

    def test_no_estimate_marker_with_the_option_off(self):
        self.assertNotIn("figures_are_estimates", fuzzy.fuzz_reply(game(enabled=False), "why", {}, why_reply()))

    def test_a_refused_reply_is_left_alone_with_the_option_on(self):
        refused = {"ok": False, "error": "no"}
        self.assertEqual(fuzzy.fuzz_reply(game(), "why", {}, dict(refused)), refused)


class StableDrawTests(unittest.TestCase):
    def test_a_repeated_look_shows_identical_figures(self):
        self.assertEqual(figures(fuzzed(game())), figures(fuzzed(game())))

    def test_the_same_salt_gives_the_same_figures_in_another_game_object(self):
        self.assertEqual(figures(fuzzed(game(salt=77))), figures(fuzzed(game(salt=77))))

    def test_another_salt_gives_other_figures(self):
        self.assertNotEqual(figures(fuzzed(game(salt=77))), figures(fuzzed(game(salt=78))))

    def test_another_actor_draws_its_own_estimates(self):
        self.assertNotEqual(figures(fuzzed(game(), "player")), figures(fuzzed(game(), "another_player")))

    def test_another_node_draws_its_own_ratio(self):
        self.assertNotEqual(fuzzy.ratio(game(), NODE_ID, "hours"), fuzzy.ratio(game(), "other_work", "hours"))

    def test_the_salt_is_drawn_once_from_the_games_rng_and_kept(self):
        fresh = game(salt=0)
        first = fuzzy.salt(fresh)
        self.assertGreater(first, 0)
        self.assertEqual(fuzzy.salt(fresh), first)


class MarkedAsEstimatesTests(unittest.TestCase):
    def test_the_reply_marks_the_figures_that_are_estimates(self):
        reply = fuzzed(game())
        self.assertTrue(reply["figures_are_estimates"])
        self.assertIn("founder_hours", reply["figures_are_estimates"])
        self.assertEqual(reply["estimates_note"], fuzzy.ESTIMATE_NOTE)

    def test_a_marked_field_reads_as_an_estimate_on_the_screen(self):
        # presentation: the tilde and the (est.) tag
        reply = {"figures_are_estimates": ["founder_hours"]}
        self.assertEqual(_est(reply, "founder_hours", 400), "~400")
        self.assertEqual(_est_tag(reply, "founder_hours"), " (est.)")
        self.assertEqual(_est(reply, "cost", 400), "400")
        self.assertEqual(_est_tag(reply, "cost"), "")


class RangeTests(unittest.TestCase):
    def test_each_shown_value_lies_between_nothing_and_twice_the_real_one(self):
        for salt in range(1, 60):
            shown = figures(fuzzed(game(salt=salt)))
            real = {"founder_hours": NODE["ph"], "scholars": NODE["sch"], "artisans": NODE["art"]}
            for key, value in real.items():
                self.assertTrue(0 <= shown[key] <= 2 * value + 1e-9, (salt, key, shown[key]))
            for trade, hours in REAL_LAB.items():
                self.assertTrue(0 <= shown["hired:" + trade] <= 2 * hours + 1e-9, (salt, trade, shown))

    def test_figures_are_shown_inexactly(self):
        exact = {"founder_hours": NODE["ph"], "scholars": NODE["sch"], "artisans": NODE["art"]}
        shown = figures(fuzzed(game()))
        self.assertTrue([key for key, value in exact.items() if shown[key] != value])

    def test_a_real_figure_of_nothing_stays_nothing(self):
        self.assertEqual(fuzzy.estimate(game(), NODE_ID, "x", 0, 2), 0)
        self.assertIsNone(fuzzy.estimate(game(), NODE_ID, "x", None, 2))


class DecoyTests(unittest.TestCase):
    def test_one_to_three_decoy_trades_are_listed_before_starting_beside_the_real_ones(self):
        for salt in range(1, 40):
            labour = fuzzed(game(salt=salt))["hired_labour"]
            decoys = set(labour) - set(REAL_LAB)
            self.assertTrue(1 <= len(decoys) <= 3, (salt, labour))
            self.assertTrue(set(REAL_LAB) <= set(labour))

    def test_decoys_are_the_same_on_every_look(self):
        self.assertEqual(fuzzy.decoy_hours(game(), NODE_ID), fuzzy.decoy_hours(game(), NODE_ID))

    def test_decoys_drop_out_at_start(self):
        started = game(active={NODE_ID: {"ph_left": NODE["ph"]}})
        self.assertEqual(set(fuzzed(started)["hired_labour"]), set(REAL_LAB))

    def test_decoys_drop_out_when_done(self):
        self.assertEqual(fuzzy.decoy_hours(game(done={NODE_ID}), NODE_ID), {})


class SpreadTests(unittest.TestCase):
    def test_the_spread_is_full_before_the_work_starts(self):
        self.assertEqual(fuzzy.spread(game(), NODE_ID), 1.0)

    def test_the_spread_halves_at_start(self):
        self.assertEqual(fuzzy.spread(game(active={NODE_ID: {"ph_left": NODE["ph"]}}), NODE_ID), 0.5)

    def test_the_founder_hours_deviation_halves_at_start(self):
        before = fuzzy.ratio(game(), NODE_ID, "hours") - 1.0
        after = fuzzy.ratio(game(active={NODE_ID: {"ph_left": NODE["ph"]}}), NODE_ID, "hours") - 1.0
        self.assertGreater(abs(before), 0.02)
        self.assertAlmostEqual(after, before / 2.0)

    def test_the_hired_hours_deviation_halves_at_start(self):
        before = fuzzy.ratio(game(), NODE_ID, "lab.smith") - 1.0
        after = fuzzy.ratio(game(active={NODE_ID: {"ph_left": NODE["ph"]}}), NODE_ID, "lab.smith") - 1.0
        self.assertAlmostEqual(after, before / 2.0)

    def test_the_spread_narrows_in_proportion_to_the_work_done(self):
        spreads = [fuzzy.spread(game(active={NODE_ID: {"ph_left": NODE["ph"] * left}}), NODE_ID)
                   for left in (1.0, 0.5, 0.1, 0.0)]
        self.assertEqual(spreads[0], 0.5)
        self.assertAlmostEqual(spreads[1], 0.25)
        self.assertAlmostEqual(spreads[2], 0.05)
        self.assertEqual(spreads[3], 0.0)
        self.assertEqual(spreads, sorted(spreads, reverse=True))

    def test_the_halfway_deviation_is_half_the_start_deviation(self):
        start = fuzzy.ratio(game(active={NODE_ID: {"ph_left": NODE["ph"]}}), NODE_ID, "hours") - 1.0
        halfway = fuzzy.ratio(game(active={NODE_ID: {"ph_left": NODE["ph"] * 0.5}}), NODE_ID, "hours") - 1.0
        self.assertAlmostEqual(halfway, start / 2.0)

    def test_completion_shows_the_exact_figures(self):
        done = game(done={NODE_ID})
        self.assertEqual(fuzzy.spread(done, NODE_ID), 0.0)
        reply = fuzzy.fuzz_why(done, NODE_ID, why_reply())
        self.assertEqual(reply, why_reply())


class SharedDrawTests(unittest.TestCase):
    def test_the_available_row_hours_match_what_why_shows(self):
        sim_state = game()
        row = {"id": NODE_ID, "cost": 1000.0, "founder_hours": 400.0}
        fuzzy.fuzz_row(sim_state, NODE_ID, row)
        self.assertEqual(row["founder_hours"], fuzzed(sim_state)["founder_hours"])

    def test_the_available_row_hours_lie_within_twice_the_real_hours(self):
        row = {"id": NODE_ID, "founder_hours": 400.0}
        fuzzy.fuzz_row(game(), NODE_ID, row)
        self.assertTrue(0 <= row["founder_hours"] <= 2 * NODE["ph"] + 1e-9)

    def test_the_start_reply_shows_the_same_estimate_as_why_not_the_exact_hours(self):
        started = game(active={NODE_ID: {"ph_left": NODE["ph"]}})
        reply = {"ok": True, "started": NODE_ID, "founder_hours_needed": 400.0}
        fuzzy.fuzz_start(started, NODE_ID, reply)
        self.assertEqual(reply["founder_hours_needed"], fuzzed(started)["founder_hours"])
        self.assertNotEqual(reply["founder_hours_needed"], NODE["ph"])

    def test_a_row_for_finished_work_is_untouched(self):
        row = {"id": NODE_ID, "founder_hours": 400.0, "cost": 1000.0}
        fuzzy.fuzz_row(game(done={NODE_ID}), NODE_ID, row)
        self.assertEqual(row, {"id": NODE_ID, "founder_hours": 400.0, "cost": 1000.0})


class ExactNeedHiddenTests(unittest.TestCase):
    def test_the_blocked_reason_with_a_number_is_made_vague(self):
        reply = why_reply()
        reply["start_blocked_reason"] = "needs 3 trained craftsmen, and only 1.0 can be put on it"
        fuzzy.fuzz_why(game(), NODE_ID, reply)
        self.assertNotIn("3 trained craftsmen", reply["start_blocked_reason"])
        self.assertNotRegex(reply["start_blocked_reason"], r"\d")

    def test_a_blocker_naming_staff_or_money_is_made_vague(self):
        reply = why_reply()
        reply["blockers"] = [{"kind": "specialists", "text": "needs 3 smiths"}, {"kind": "money", "text": "short 40 den"},
                             {"kind": "prerequisite", "text": "needs 3 nodes first"}]
        fuzzy.fuzz_why(game(), NODE_ID, reply)
        self.assertNotRegex(reply["blockers"][0]["text"], r"\d")
        self.assertNotRegex(reply["blockers"][1]["text"], r"\d")
        self.assertIn("3", reply["blockers"][2]["text"])


if __name__ == "__main__":
    unittest.main()
