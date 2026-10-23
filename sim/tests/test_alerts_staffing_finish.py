"""Complaints 79, 125, 201, 229, 231, 237: blocker kinds declared, luckless nodes, alert tiers and stop reasons.

Rules are tested on the data, on built alerts and on a stand-in for the labour's world; two named scenarios (test_alerts_staffing_finish_scenario) read
the `labour` reply and the staff step's departures off a game."""
QUICK_TOPIC = True
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.blockers import BLOCKER_KINDS
from sim.labour.labour_staff_ledger import StaffLedgerMixin
from sim.refusal import cause_of
from sim.ui.proto.step_alerts import step_alerts, alert_severity
from sim.ui.proto.step_stops import severe_stop_reason

# --- 129: every start check declares the kind of blocker it reports
undeclared = [check_function.__name__ for check_function in S.Sim._START_REASON_CHECKS
              if getattr(check_function, "blocker_kind", None) not in BLOCKER_KINDS]
check("every start check declares a known blocker kind", not undeclared, undeclared)

# --- 241: a pure concept (science, no materials, no trades) cannot fail by luck
luckless = [node_id for node_id, node in NODES.items()
            if node.get("kind") == "SCIENCE" and not node["mat"] and not node["lab"]]
check("set-up: some knowledge nodes have no physical component", bool(luckless))
check("a knowledge-only node carries no chance of failing",
      all(NODES[node_id]["risk"] == 0 for node_id in luckless),
      [node_id for node_id in luckless if NODES[node_id]["risk"]][:3])
check("a node with materials or trades keeps its chance of failing",
      any(node["risk"] > 0 for node in NODES.values() if node["mat"] or node["lab"]))

# --- 81: severity tiers on alerts
check("alert severity ranks a death above credit trouble above an early stop",
      alert_severity("FOUNDER DIED, aged about 60") < alert_severity("CREDIT EXHAUSTED 100: x")
      < alert_severity("STOPPED EARLY: x"))
alerts = step_alerts(events=[{"year": 100, "message": "CREDIT EXHAUSTED: x", "event_kind": "credit_exhausted"}], lost=[], closed_concerns=[],
                     founder_died={"aged_about": 60, "year": 100}, goal_year=None, stopped_early="stopped",
                     population_change=0.0, staffing_line="Staffing this year: closed 2")
check("the alerts block carries the staffing line and orders by severity",
      any(alert.startswith("Staffing this year") for alert in alerts) and alerts[0].startswith("FOUNDER DIED")
      and alerts[-1].startswith("STOPPED EARLY"), alerts)

# --- 81: extra reasons for a step to stop early
check("a quiet year gives no stop reason", severe_stop_reason([], [], [], []) is None)
check("a newly unlocked objective stops the step",
      cause_of(severe_stop_reason([], [], [], ["Reach the goal"])) == "new_objective")
check("a severe failure stops the step",
      cause_of(severe_stop_reason([{"year": 1, "message": "FAILED at Grid: it did not work.", "event_kind": "project_failed", "facts": {"severity": "major"}}], [], [], [])) == "project_failed")
check("a minor failure does not stop the step",
      severe_stop_reason([{"year": 1, "message": "FAILED at Grid (minor): lost 3", "event_kind": "project_failed", "facts": {"severity": "minor"}}], [], [], []) is None)
check("a concern closed for want of staff stops the step",
      cause_of(severe_stop_reason([], ["Smithy"], [], [])) == "staff_closure")
check("a newly blocked project stops the step",
      cause_of(severe_stop_reason([], [], ["Loom"], [])) == "project_blocked")

# --- 233: departures are split by cause, never pooled
def departures(cause, counts, stops=()):
    log = []
    ledger = SimpleNamespace(_world=SimpleNamespace(
        concerns_to_close_for_staffing=lambda: list(stops), stopped_yearly_value=lambda node_ids: 0.0,
        state=SimpleNamespace(household=SimpleNamespace(log=log), scenario=SimpleNamespace(year=100))))
    ledger.yearly_value_of = lambda node_ids: ledger._world.stopped_yearly_value(node_ids)
    StaffLedgerMixin.log_staff_lost(ledger, cause, counts)
    return [message for _, message in log]


deaths = departures("death", {"scholar": 1, "artisan": 3.0})
offers = departures("better offers", {"artisan": 2})
check("a departure is a line of its own cause, with the trades and people lost, never pooled",
      len(deaths) == 1 and cause_of(deaths[0]) == "staff_lost" and deaths[0].facts["reason"] == "death"
      and deaths[0].facts["trades"] == {"scholar": 1, "artisan": 3.0}
      and len(offers) == 1 and offers[0].facts["reason"] == "better_offers" and offers[0].facts["trades"] == {"artisan": 2},
      (deaths, offers))
# presentation: the line completes "you lose <people> to <cause>"
check("the line reads 'you lose <people> to <cause>', one cause each",
      str(deaths[0]) == "you lose 3 artisans, 1 scholar to death" and str(offers[0]) == "you lose 2 artisans to better offers",
      (str(deaths[0]), str(offers[0])))
stopping = departures("death", {"artisan": 1}, stops=["smithy"])
check("a loss that leaves a concern the staffing rule will shut is its own kind of event",
      cause_of(stopping[0]) == "staff_lost_stops_concerns" and stopping[0].facts["stops"] == ["smithy"], stopping)
check("nobody lost is no line", departures("death", {"artisan": 0}) == [])
