"""Complaint 640 rules: the expected calendar cost of a risky node with retries (`expected_calendar_years`), the hazard timeline's
escalating urgency (`hazard_timeline`), the one-shot first-timer tip (`_worth_knowing_early`), the free-prerequisite hint
(`free_prereq_hint`) and a process controller's relief on a node's risk (`effective_risk`). Each is called on the projects module (or the
hazards module) over plain values carrying only what it reads. The banked calendar arithmetic is test_retry_calendar; retry learning on the risk is
test_industry_depth; the save contract of the retry counts is the `--session` round trip."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.hazards import advice
from sim.projects import constants as projects_constants
from sim.knowledge.api import free_prereq_hint
from sim.tests import hazards_host
from sim.tests.test_industry_depth import world
from sim.ui import protocol
from sim.ui.proto import state_waiting

from .harness import NODES
from sim.engine import ui_port
from sim.tests.ui_stand_in import Game, ui_state

FLOOR = 4.0


def calendar_world(risk=0.3, experience=None):
    """The depth stand-in with the calendar readers `expected_calendar_years` calls, floor FLOOR years."""
    stub = world(experience=experience)
    stub.nodes["loom"]["risk"] = risk
    module = stub.projects
    module.calendar_floor = lambda node_id: FLOOR
    module.payment_schedule_years = lambda node_id: 0.0
    stub._retry_calendar_retain = module._retry_calendar_retain
    stub.effective_risk = lambda node_id, precaution=None: module.effective_risk(node_id, precaution=False)
    return stub


def expected_years(stub):
    return stub.projects.expected_calendar_years("loom")


class ExpectedCalendarYears(unittest.TestCase):
    def test_a_risk_free_node_expects_exactly_its_earliest_completion(self):
        self.assertAlmostEqual(expected_years(calendar_world(risk=0.0)), FLOOR)

    def test_a_risky_nodes_expected_calendar_cost_is_more_than_its_bare_floor(self):
        self.assertGreater(expected_years(calendar_world()), FLOOR)

    def test_retry_learning_makes_it_less_than_the_plain_geometric_series(self):
        self.assertLess(expected_years(calendar_world()), FLOOR / (1.0 - 0.3))

    def test_it_matches_a_sum_driven_by_effective_risk_at_each_hypothetical_attempt(self):
        stub = calendar_world()
        manual_total, survive, attempt = 0.0, 1.0, 0
        while survive > 1e-15:
            years = FLOOR if attempt == 0 else FLOOR * (1.0 - stub._retry_calendar_retain("loom", attempt))
            manual_total += survive * years
            stub.projects.seat.failed_attempts["loom"] = attempt
            with stub.after_failed_attempts("loom", attempt):
                survive *= stub.effective_risk("loom")
            attempt += 1
        stub.projects.seat.failed_attempts.clear()
        self.assertAlmostEqual(expected_years(stub), manual_total, places=6)

    def test_the_projection_leaves_the_real_failure_count_as_it_found_it(self):
        stub = calendar_world()
        stub.projects.seat.failed_attempts["loom"] = 2
        expected_years(stub)
        self.assertEqual(stub.projects.seat.failed_attempts["loom"], 2)
        fresh = calendar_world()
        expected_years(fresh)
        self.assertNotIn("loom", fresh.projects.seat.failed_attempts)

    def test_three_prior_failures_leave_less_expected_time_than_attempt_one_faced(self):
        stub = calendar_world()
        before = expected_years(stub)
        stub.projects.seat.failed_attempts["loom"] = 3
        for _ in range(3):
            stub.learn_from_failed_attempt("loom")
        self.assertLess(expected_years(stub), before)


class ControllerRelief(unittest.TestCase):
    def test_a_completed_controller_cuts_a_process_control_nodes_risk_by_the_relief_factor(self):
        stub = world(mechanic=lambda name: {"controller": {"failure_kind": "process_control"}} if name == "failure_relief" else {})
        stub.nodes["loom"]["failure_kind"] = "process_control"
        bare = stub.projects.effective_risk("loom", precaution=False)
        stub.state.projects.done.add("controller")
        relieved = stub.projects.effective_risk("loom", precaution=False)
        self.assertAlmostEqual(bare, 0.3)
        self.assertAlmostEqual(relieved, 0.3 * projects_constants.CONTROL_RELIEF_FACTOR)
        self.assertGreater(relieved, 0.0)


def timeline_for(hazards, year, relief=1.0, hedge_years=None):
    """`hazard_timeline` over hazards written out as (name, start year, in progress), unhedged unless `relief` is low."""
    rows = [({"name": name, "staff_loss": 0.4}, start, start + 5, in_progress) for name, start, in_progress in hazards]
    module = hazards_host.build(year=year)
    module.hazard_relief = lambda kind: (relief, "why")
    module.hazard_advice = lambda kind: {"even_started_today_the_real_hedges_here_take_years": hedge_years or {"quickest": 3, "slowest": 10}}
    with mock.patch.object(advice, "hazards_not_yet_past", return_value=rows):
        return module.hazard_timeline()


class HazardTimeline(unittest.TestCase):
    def test_the_same_hazards_urgency_escalates_as_the_date_closes_in(self):
        far = timeline_for([("Settlement", 150, False)], year=100)[0]
        near = timeline_for([("Settlement", 150, False)], year=148)[0]
        self.assertEqual(far["urgency"], "on the horizon")
        self.assertEqual(near["urgency"], "too late to hedge")

    def test_a_hazard_under_way_is_happening_now(self):
        self.assertEqual(timeline_for([("Settlement", 150, True)], year=151)[0]["urgency"], "happening now")

    def test_a_hazard_already_hedged_reads_as_hedged(self):
        self.assertEqual(timeline_for([("Settlement", 150, False)], year=100, relief=0.5)[0]["urgency"], "hedged")

    def test_the_timeline_is_sorted_nearest_first_and_calm_rows_after_the_first_lose_their_sentence(self):
        rows = timeline_for([("Later", 200, False), ("Sooner", 120, False), ("Latest", 300, False)], year=100)
        self.assertEqual([row["name"] for row in rows], ["Sooner", "Later", "Latest"])
        self.assertIn("headline", rows[0])
        self.assertNotIn("headline", rows[1])


class FirstTimerTip(unittest.TestCase):
    def test_a_fresh_early_game_is_told_once_and_the_flag_is_set(self):
        sim = Game(year=100, cfg={"start_year": 100}, state=ui_state())
        first = state_waiting._worth_knowing_early(sim)
        self.assertTrue(first)
        self.assertTrue(ui_port.said_command_index(sim))
        self.assertIsNone(state_waiting._worth_knowing_early(sim))

    def test_a_game_far_past_its_opening_is_never_told(self):
        sim = Game(year=150, cfg={"start_year": 100}, state=ui_state())
        self.assertIsNone(state_waiting._worth_knowing_early(sim))

    def test_the_one_shot_flag_is_saved_so_a_restart_does_not_say_it_again(self):
        self.assertIn("_said_command_index", protocol.SAVE_FIELDS)


HINT_NODES = {"cap_free": {"pre": [], "ph": 0, "yrs": 0, "risk": 0, "_total_cost": 0},
              "cap_free_blocked": {"pre": ["thermometer"], "ph": 0, "yrs": 0, "risk": 0, "_total_cost": 0},
              "costly": {"pre": [], "ph": 100, "yrs": 1, "risk": 0.1, "_total_cost": 5000}}


class FreePrerequisiteHint(unittest.TestCase):
    def test_a_free_startable_prerequisite_says_so_and_gives_the_command(self):
        hint = free_prereq_hint(HINT_NODES, ["cap_free"], set())
        self.assertIn("cap_free", hint)
        self.assertIn("start cap_free", hint)

    def test_a_free_node_that_is_itself_blocked_is_not_offered(self):
        self.assertEqual(free_prereq_hint(HINT_NODES, ["cap_free_blocked"], set()), "")

    def test_it_is_offered_once_what_blocked_it_is_done(self):
        self.assertIn("start cap_free_blocked", free_prereq_hint(HINT_NODES, ["cap_free_blocked"], {"thermometer"}))

    def test_an_ordinary_expensive_prerequisite_gets_no_hint(self):
        self.assertEqual(free_prereq_hint(HINT_NODES, ["costly"], set()), "")


class FreeCapabilityPremise(unittest.TestCase):
    def test_the_capability_nodes_the_hint_exists_for_are_still_free(self):
        free = [node_id for node_id, node in NODES.items()
                if node_id.startswith("cap_") and (node.get("_total_cost") or 0) <= 1
                and (node.get("ph") or 0) == 0 and (node.get("yrs") or 0) == 0 and (node.get("risk") or 0) == 0]
        self.assertGreaterEqual(len(free), 8, sorted(free))


if __name__ == "__main__":
    unittest.main()
