"""Rules of what a failed project costs: `failure_loss` is the one figure `why` quotes and `_fail_attempt` charges, a
failure takes no more than the purse and the credit line bear and bills the rest to the project, a bounty's claimant
failing costs the poster nothing and leaves the work to retry, and the coin guard is paid only from the room under the
credit line."""
QUICK_TOPIC = True

import collections
import unittest
from types import SimpleNamespace

from sim.agents.api import edges
from sim.coin.rules import coin_guard_paid, room_under_credit_line
from sim.ledger.api import PayEdge
from sim.production.api import LearnFromFailure
from sim.projects import constants as projects_constants
from sim.reporting.api import RecordEvent
from sim.tests import materials_stand_in, projects_host

NODE_ID = "kiln"


class BillSim:
    """The reads `failure_bill` and `failure_loss` make: the running project's frozen cost, the cost a start today
    would have, and the part of it that is up-front materials."""

    def __init__(self, risk, running_cost, cost_now, up_front, running):
        module = materials_stand_in.build(
            tree_nodes={NODE_ID: {"risk": risk}}, failure_reset_share=0.4,
            legacy_projects=materials_stand_in.projects(active={NODE_ID: {}} if running else {}),
            project_cost=lambda node_id: running_cost, project_cost_now=lambda node_id: cost_now)
        module.up_front_materials_money = lambda node_id: up_front
        self.failure_loss = module.failure_loss


class FailureLossTests(unittest.TestCase):
    def test_a_start_not_yet_made_loses_the_share_of_its_bill_after_the_up_front_materials(self):
        sim = BillSim(risk=0.2, running_cost=0.0, cost_now=1000.0, up_front=400.0, running=False)
        self.assertAlmostEqual(sim.failure_loss(NODE_ID), 0.4 * 600.0)

    def test_holding_the_materials_does_not_make_a_failure_cost_more(self):
        empty = BillSim(0.2, 0.0, 1000.0, 400.0, False).failure_loss(NODE_ID)
        stocked = BillSim(0.2, 0.0, 1000.0, 0.0, False).failure_loss(NODE_ID)
        self.assertLessEqual(empty, stocked)

    def test_a_running_project_loses_the_share_of_its_frozen_bill(self):
        sim = BillSim(risk=0.2, running_cost=700.0, cost_now=5000.0, up_front=900.0, running=True)
        self.assertAlmostEqual(sim.failure_loss(NODE_ID), 0.4 * 700.0)

    def test_a_project_that_cannot_fail_loses_nothing(self):
        self.assertEqual(BillSim(0.0, 700.0, 5000.0, 0.0, True).failure_loss(NODE_ID), 0.0)

    def test_a_bill_the_materials_more_than_cover_loses_nothing_not_less_than_nothing(self):
        self.assertEqual(BillSim(0.2, 0.0, 100.0, 300.0, False).failure_loss(NODE_ID), 0.0)


class CoinGuardTests(unittest.TestCase):
    def test_the_room_is_purse_plus_credit_plus_takings_less_outgoings(self):
        self.assertEqual(room_under_credit_line(100.0, 500.0, 50.0, 20.0, 30.0, 10.0), 590.0)

    def test_a_year_that_already_spends_past_the_line_leaves_no_room(self):
        self.assertEqual(room_under_credit_line(-400.0, 100.0, 0.0, 50.0, 50.0, 0.0), 0.0)

    def test_the_guard_is_paid_only_to_the_room(self):
        self.assertEqual(coin_guard_paid(1e12, 590.0), 590.0)
        self.assertEqual(coin_guard_paid(40.0, 590.0), 40.0)
        self.assertEqual(coin_guard_paid(40.0, 0.0), 0.0)


class FailingSim:
    """What `_fail_attempt` reads: a project record, a purse with a credit line, and the rules it calls."""

    instrument_spec = None

    can_bear = 1e18
    FAILURE_RESET_SHARE = projects_constants.FAILURE_RESET_SHARE

    def __init__(self, capital, loss, claimed):
        nodes = {NODE_ID: {"name": "Kiln", "ph": 100.0, "risk": 0.2, "mat": {}, "lab": {}}, "gauge": {"name": "Gauge"}}
        self.state = SimpleNamespace(
            projects=SimpleNamespace(
                done=set(),
                active={NODE_ID: {"yrs": 4.0, "ph_left": 0.0, "cost_left": 10.0}},
                failed_attempts=collections.Counter(),
                bountied={NODE_ID} if claimed else set()),
            household=SimpleNamespace(capital=capital, log=[]),
            scenario=SimpleNamespace(year=-100))
        self.loss = loss
        self.paid = []
        self.learned = []
        self.rng = SimpleNamespace(uniform=lambda low, high: low)
        module = self.module = projects_host.build(
            tree=nodes, legacy_projects=self.state.projects, techniques_held=lambda: self.state.projects.done, funding_capacity=1000.0, state_interest=lambda node: 0,
            failure_loss=lambda node_id: self.loss, bearable_part_of=self.bearable_part_of,
            mechanic=lambda name: {NODE_ID: self.instrument_spec} if name == "diagnosis_instrument" and self.instrument_spec else {},
            legacy_dice=self.rng, money_text=lambda amount, grouped=False, short=False: "%d" % amount,
            plain_number=lambda value, digits=0: "%d" % value)
        module.needs.send = self.send
        module.failure_severity = lambda node_id, lost, means: "major"
        module.rebuild_work_factor = lambda node_id: 0.5
        module._retry_calendar_retain = lambda node_id, attempt_index=None: 0.25
        module.effective_risk = lambda node_id, precaution=None: 0.1
        module.lose_what_was_risked = lambda node_id: []

    def bearable_part_of(self, amount):
        self.asked_to_bear = amount
        return min(amount, self.can_bear)

    def send(self, command):
        if isinstance(command, PayEdge):
            self.paid.append((command.edge, command.amount))
            self.state.household.capital -= command.amount
        elif isinstance(command, LearnFromFailure):
            self.learned.append(command.node_id)
        elif isinstance(command, RecordEvent):
            self.state.household.log.append((self.state.scenario.year, command))
        return None

    def _fail_attempt(self, node_id, risk):
        self.module._fail_attempt(node_id, risk)


class FailedAttemptChargeTests(unittest.TestCase):
    def test_a_loss_inside_the_purse_is_paid_whole_and_nothing_is_added_to_the_project(self):
        sim = FailingSim(capital=1000.0, loss=300.0, claimed=False)
        sim._fail_attempt(NODE_ID, 0.2)
        self.assertEqual(sim.paid, [(edges.EDGE_DESTROYED, 300.0)])
        self.assertEqual(sim.state.projects.active[NODE_ID]["cost_left"], 10.0)

    def test_the_part_the_purse_cannot_bear_is_billed_to_the_project_to_redo(self):
        sim = FailingSim(capital=0.0, loss=5000.0, claimed=False)
        sim.can_bear = 1200.0
        sim._fail_attempt(NODE_ID, 0.2)
        self.assertEqual(sim.asked_to_bear, 5000.0)
        self.assertEqual(sim.paid, [(edges.EDGE_DESTROYED, 1200.0)])
        self.assertEqual(sim.state.projects.active[NODE_ID]["cost_left"], 10.0 + 5000.0 - 1200.0)

    def test_the_attempt_is_counted_the_hours_reset_and_part_of_the_calendar_banked(self):
        sim = FailingSim(capital=1000.0, loss=300.0, claimed=False)
        sim._fail_attempt(NODE_ID, 0.2)
        record = sim.state.projects.active[NODE_ID]
        self.assertEqual(sim.state.projects.failed_attempts[NODE_ID], 1)
        self.assertAlmostEqual(record["ph_left"], 100.0 * 0.5 * sim.FAILURE_RESET_SHARE)
        self.assertAlmostEqual(record["yrs"], 4.0 * 0.25)

    def test_a_failed_bounty_charges_the_poster_nothing_and_stays_the_claimants_work(self):
        sim = FailingSim(capital=1000.0, loss=300.0, claimed=True)
        sim._fail_attempt(NODE_ID, 0.2)
        record = sim.state.projects.active[NODE_ID]
        self.assertEqual(sim.paid, [(edges.EDGE_DESTROYED, 0.0)])
        self.assertEqual(sim.state.household.capital, 1000.0)
        self.assertEqual(record["cost_left"], 10.0)
        self.assertEqual(record["ph_left"], 0.0)
        self.assertIn(NODE_ID, sim.state.projects.bountied)
        self.assertEqual(sim.state.projects.failed_attempts[NODE_ID], 1)

    def test_a_failed_bounty_logs_that_the_claimant_failed_and_the_prize_holds(self):
        sim = FailingSim(capital=1000.0, loss=300.0, claimed=True)
        sim._fail_attempt(NODE_ID, 0.2)
        _year, line = sim.state.household.log[-1]
        self.assertEqual(line.kind, "project_failed")
        self.assertEqual(line.facts["severity"], "claimed")
        self.assertEqual(line.facts["lost"], 0.0)

    def test_a_failure_with_no_instrument_needed_teaches(self):
        sim = FailingSim(capital=1000.0, loss=300.0, claimed=False)
        sim._fail_attempt(NODE_ID, 0.2)
        self.assertEqual(sim.learned, [NODE_ID])


class FailureTeachesTests(unittest.TestCase):
    SPEC = {"instrument": "gauge", "needed": 2.0, "quantity": "purity", "unit": "ppm", "needed_words": "purity"}

    def fail(self, holds_instrument):
        sim = FailingSim(capital=1000.0, loss=300.0, claimed=False)
        sim.instrument_spec = self.SPEC
        if holds_instrument:
            sim.state.projects.done.add("gauge")
        sim._fail_attempt(NODE_ID, 0.2)
        return sim

    def test_a_failure_that_cannot_be_measured_teaches_nothing(self):
        self.assertEqual(self.fail(holds_instrument=False).learned, [])

    def test_the_same_failure_with_the_instrument_held_teaches(self):
        self.assertEqual(self.fail(holds_instrument=True).learned, [NODE_ID])

    def test_the_failure_is_counted_either_way(self):
        for holds in (False, True):
            self.assertEqual(self.fail(holds).state.projects.failed_attempts[NODE_ID], 1)


if __name__ == "__main__":
    unittest.main()
