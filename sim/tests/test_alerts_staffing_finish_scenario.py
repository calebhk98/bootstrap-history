"""SCENARIO (Complaint 640): the labour reply's per-trade ceiling and the staff step's departures by cause, in a game (the rules are in test_alerts_staffing_finish)."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.blockers import BLOCKER_KINDS
from sim.labour.labour_staff_ledger import StaffLedgerMixin
from sim.refusal import cause_of
from sim.ui.proto.step_alerts import step_alerts, alert_severity
from sim.ui.proto.step_stops import severe_stop_reason

# --- scenario: the `labour` reply carries a per-trade ceiling label and the workforce block, and the screen renders it
from sim.ui.protocol import _agent_dispatch
from sim.ui.proto.render_screens_economy import render_labour
live = sim()
labour_reply = _agent_dispatch(live, NODES, {"cmd": "labour"})
label = labour_reply.get("and_how_many_of_the_lettered_trades_this_society_supplies", "")
workforce = labour_reply.get("workforce") or {}
# presentation: the label says each trade has its own ceiling
check("scenario: the labour reply's ceiling label is per trade, not one shared total, and it carries a workforce block "
      "that the screen renders",
      "own ceiling" in label and "scholar" in label and "in total" not in label
      and {"depends_on_one_person", "expected_losses_per_year", "in_training"} <= set(workforce)
      and "WORKFORCE RISK" in render_labour(labour_reply), (label, workforce))

# --- scenario: the staff step labels its departures by cause
staffed = sim(capital=10000000.0, events=False)
staffed.employees["scholar"] = 8.0
staffed.employees["artisan"] = 40.0
staffed.labour._resync_pools()
for _ in range(12):
    staffed._step_staff()
loss_lines = [message for _, message in staffed.log if cause_of(message) in ("staff_lost", "staff_lost_stops_concerns")]
check("scenario: over twelve years the staff step logs departures, each of one cause: death or better offers",
      loss_lines and all(line.facts["reason"] in ("death", "better_offers") for line in loss_lines),
      [str(line) for line in loss_lines[:3]])
