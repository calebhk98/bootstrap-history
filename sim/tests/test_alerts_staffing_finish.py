"""Complaints 81, 129, 205, 233, 235, 241: blocker kinds declared, luckless nodes, alert tiers and stop reasons."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.step_alerts import step_alerts, alert_severity
from sim.engine.proto.step_stops import severe_stop_reason

# --- 129: every start check declares the kind of blocker it reports
live = sim()
undeclared = [check_function.__name__ for check_function in live._START_REASON_CHECKS
              if getattr(check_function, "blocker_kind", None) not in live.BLOCKER_KINDS]
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
alerts = step_alerts(events=[{"year": 100, "message": "CREDIT EXHAUSTED: x"}], lost=[], closed_concerns=[],
                     founder_died={"aged_about": 60, "year": 100}, goal_year=None, stopped_early="stopped",
                     population_change=0.0, staffing_line="Staffing this year: closed 2")
check("the alerts block carries the staffing line and orders by severity",
      any(alert.startswith("Staffing this year") for alert in alerts) and alerts[0].startswith("FOUNDER DIED")
      and alerts[-1].startswith("STOPPED EARLY"), alerts)

# --- 81: extra reasons for a step to stop early
check("a quiet year gives no stop reason", severe_stop_reason([], [], [], []) is None)
check("a newly unlocked objective stops the step",
      "objective" in (severe_stop_reason([], [], [], ["Reach the goal"]) or ""))
check("a severe failure stops the step",
      "failed" in (severe_stop_reason([{"year": 1, "message": "FAILED at Grid: it did not work."}], [], [], []) or ""))
check("a minor failure does not stop the step",
      severe_stop_reason([{"year": 1, "message": "FAILED at Grid (minor): lost 3"}], [], [], []) is None)
check("a concern closed for want of staff stops the step",
      "staff" in (severe_stop_reason([], ["Smithy"], [], []) or ""))
check("a newly blocked project stops the step",
      "blocked" in (severe_stop_reason([], [], ["Loom"], []) or ""))
