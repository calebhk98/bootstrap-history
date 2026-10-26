"""Complaint 91: automation leaves a per-turn audit trail of what it did, why and at what cost.

The trail's rules (a row's shape and cost, the years kept, the window the `automation` command reads) are tested on
plain values in reporting's rules; the module's commands are tested over its own state; the screen is tested on rows.
The phases that write rows over stand-ins are in test_automation_wiring."""
QUICK_TOPIC = True
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.reporting import rules
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, ReportingSeat
from sim.reporting.module import Reporting
from sim.tests import module_harness
from sim.ui.proto.dispatch_automation import _cmd_automation
from sim.ui.proto.render_typed import _RENDERERS

# --- a row says year, policy, action, what, reason and cost
row = rules.audit_row(120, "auto_hire", "hire", "3 artisan", "staff target 5.0 against 2.0 held", 1000.0, 900.0,
                      {"ids": ["a"]})
check("a row says year, policy, action, what, reason and cost, plus anything extra it was given",
      {"year", "policy", "action", "what", "reason", "cost"} <= set(row) and row["year"] == 120
      and row["policy"] == "auto_hire" and row["ids"] == ["a"], row)
check("the cost of a row is what capital fell by since the action began", row["cost"] == 100.0, row["cost"])
check("an order id names its policy, its subject and its year",
      rules.order_id("auto_mine", "coal", 130) == "auto_mine:coal:130")

# --- the window of years kept and read
rows = [{"year": 200 - offset} for offset in range(rules.YEARS_KEPT + 3)]
check("the trail is kept to a few years",
      {each["year"] for each in rules.kept_rows(rows, 200)} == {200 - offset for offset in range(rules.YEARS_KEPT)})
read = [{"year": year} for year in (196, 197, 198, 199, 200)]
check("by default the rows read are the year just played (and the one in progress)",
      {each["year"] for each in rules.recent_rows(read, 200)} == {199, 200})
check("years widens the window", {each["year"] for each in rules.recent_rows(read, 200, 3)} == {197, 198, 199, 200})
check("a window of nothing still reads the year just played",
      {each["year"] for each in rules.recent_rows(read, 200, 0)} == {199, 200})
check("the rows read come oldest first",
      [each["year"] for each in rules.recent_rows(read, 200, 3)] == [197, 198, 199, 200])

# --- the module records what it is told, over its own seat state
module = module_harness.build(Reporting, views={"year": 120, "acting_balance": 900.0}, seat=ReportingSeat())
recorded = module.record_automation(RecordAutomation("auto_hire", "hire", "3 artisan", "staff target", 1000.0,
                                                      {"ids": ["a"]}))
check("the module appends the row, costed against the acting balance",
      module.seat.automation_audit == [recorded] and recorded["cost"] == 100.0 and recorded["year"] == 120, recorded)
skipped = module.record_automation_skip(RecordAutomationSkip("auto_start", "further projects", "cap reached",
                                                             {"reason_kind": "x"}))
check("a skip is a row with action 'skipped', costing nothing, and carries its reason", skipped["action"] == "skipped"
      and skipped["cost"] == 0.0 and skipped["reason"] == "cap reached" and skipped["reason_kind"] == "x", skipped)
module.seat.automation_audit.append({"year": 100})
module.trim_audit()
check("the start of a seat's year drops the rows older than the years kept",
      [each["year"] for each in module.seat.automation_audit] == [120, 120], module.seat.automation_audit)
check("the rows view answers from the seat's trail", len(module.automation_rows(1)) == 2)

# --- the command and the screen
stood_in = SimpleNamespace(view=lambda name: (lambda years: rules.recent_rows(read, 200, years)))
reply = _cmd_automation(stood_in, {}, {"cmd": "automation", "years": 2}, None)
check("the automation command lists the rows of the window, with a count", reply["ok"] and reply["years"] == 2
      and len(reply["rows"]) == 3 and "3 automatic actions" in reply["note"], reply)
empty = _cmd_automation(SimpleNamespace(view=lambda name: (lambda years: [])), {}, {"cmd": "automation"}, None)
check("with nothing automatic in the window the audit is empty and says so", empty["rows"] == [] and empty["ok"], empty)
# presentation: the printed screen leads with the policy and shows reason and cost
text = _RENDERERS["automation"]({"rows": [dict(row, reason="staff target 5.0 against 2.0 held")]})
check("the printed screen leads with the policy and shows what, reason and cost",
      "WHAT AUTOMATION DID" in text and "AUTO_HIRE" in text and "3 artisan" in text
      and "staff target" in text and "Cost: 100" in text, text)
