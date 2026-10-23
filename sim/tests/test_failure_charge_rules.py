"""Rules of what a failed project costs: `failure_loss` is the one figure `why` quotes and `_fail_attempt` charges, a
failure takes no more than the purse and the credit line bear and bills the rest to the project, a bounty's claimant
failing costs the poster nothing and leaves the work to retry, and the coin guard is paid only from the room under the
credit line."""
QUICK_TOPIC = True

import collections
import unittest
from types import SimpleNamespace

from sim.agents.api import edges
from sim.engine.coin_guard_rule import coin_guard_paid, room_under_credit_line
from sim.engine.economy_credit import CreditMixin
from sim.engine.project_materials import ProjectMaterialsMixin
from sim.engine.projects_completion import CompletionMixin

NODE_ID = "kiln"


class BillSim(ProjectMaterialsMixin):
    """The reads `failure_bill` and `failure_loss` make: the running project's frozen cost, the cost a start today
    would have, and the part of it that is up-front materials."""

    FAILURE_RESET_SHARE = 0.4

    def __init__(self, risk, running_cost, cost_now, up_front, running):
        self.nodes = {NODE_ID: {"risk": risk}}
        self.state = SimpleNamespace(projects=SimpleNamespace(active={NODE_ID: {}} if running else {}))
        self._running_cost, self._cost_now, self._up_front = running_cost, cost_now, up_front

    def project_cost(self, node_id):
        return self._running_cost

    def project_cost_now(self, node_id):
        return self._cost_now

    def _up_front_materials_money(self, node_id):
        return self._up_front


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


class FailingSim(CompletionMixin):
    """What `_fail_attempt` reads: a project record, a purse with a credit line, and the rules it calls."""

    def __init__(self, capital, loss, claimed, credit_base=500.0):
        self.nodes = {NODE_ID: {"name": "Kiln", "ph": 100.0, "risk": 0.2, "mat": {}, "lab": {}}}
        self.state = SimpleNamespace(
            projects=SimpleNamespace(
                active={NODE_ID: {"yrs": 4.0, "ph_left": 0.0, "cost_left": 10.0}},
                failed_attempts=collections.Counter(),
                bountied={NODE_ID} if claimed else set()),
            household=SimpleNamespace(capital=capital, log=[]),
            scenario=SimpleNamespace(year=-100))
        self.loss, self.credit_base = loss, credit_base
        self.paid = []
        self.learned = []

    def credit_limit(self, _capital=None):
        return self.credit_base

    bearable_part_of = CreditMixin.bearable_part_of

    def pay_edge(self, edge_name, amount, purpose):
        self.paid.append((edge_name, amount))
        self.state.household.capital -= amount

    def mechanic(self, node_id, name):
        return None

    def learn_from_failed_attempt(self, node_id):
        self.learned.append(node_id)

    def failure_loss(self, node_id):
        return self.loss

    def failure_severity(self, node_id, lost, means):
        return "major"

    def funding_capacity(self):
        return 1000.0

    def rebuild_work_factor(self, node_id):
        return 0.5

    def _retry_calendar_retain(self, node_id):
        return 0.25

    def effective_risk(self, node_id):
        return 0.1

    def lose_what_was_risked(self, node_id):
        return []

    def state_interest(self, node):
        return 0


class FailedAttemptChargeTests(unittest.TestCase):
    def test_a_loss_inside_the_purse_is_paid_whole_and_nothing_is_added_to_the_project(self):
        sim = FailingSim(capital=1000.0, loss=300.0, claimed=False)
        sim._fail_attempt(NODE_ID, 0.2)
        self.assertEqual(sim.paid, [(edges.EDGE_DESTROYED, 300.0)])
        self.assertEqual(sim.state.projects.active[NODE_ID]["cost_left"], 10.0)

    def test_a_loss_past_the_credit_line_is_borne_to_the_line_and_the_rest_billed_to_the_project(self):
        sim = FailingSim(capital=0.0, loss=5000.0, claimed=False)
        sim._fail_attempt(NODE_ID, 0.2)
        borne = sim.paid[0][1]
        self.assertLess(borne, 5000.0)
        self.assertGreaterEqual(sim.state.household.capital, -sim.credit_limit() - 1e-9)
        self.assertAlmostEqual(sim.state.projects.active[NODE_ID]["cost_left"], 10.0 + 5000.0 - borne)

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


if __name__ == "__main__":
    unittest.main()
