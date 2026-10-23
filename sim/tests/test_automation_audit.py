"""Complaint 91: automation leaves a per-turn audit trail of what it did, why and at what cost.

The trail's rules (a row's shape and cost, the years kept, the window the `automation` command reads, the
screen) are tested on a stand-in for the household; the phases that write
rows over stand-ins are in test_automation_wiring."""
QUICK_TOPIC = True
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine import automation_audit
from sim.ui.proto.dispatch_automation import _cmd_automation
from sim.ui.proto.render_typed import _RENDERERS


def household_at(year, capital=1000.0, rows=()):
    """The parts of a game the audit reads: a year, a household with capital and a trail."""
    return SimpleNamespace(state=SimpleNamespace(
        scenario=SimpleNamespace(year=year), household=SimpleNamespace(capital=capital, automation_audit=list(rows))))


# --- a row says year, policy, action, what, reason and cost
stand_in = household_at(120, capital=900.0)
row = automation_audit.record(stand_in, "auto_hire", "hire", "3 artisan", "staff target 5.0 against 2.0 held", 1000.0,
                              ids=["a"])
check("a row says year, policy, action, what, reason and cost, plus anything extra it was given",
      {"year", "policy", "action", "what", "reason", "cost"} <= set(row) and row["year"] == 120
      and row["policy"] == "auto_hire" and row["ids"] == ["a"] and stand_in.state.household.automation_audit == [row])
check("the cost of a row is what capital fell by since the action began", row["cost"] == 100.0, row["cost"])
skipped = automation_audit.record_skip(stand_in, "auto_start", "further projects", "cap reached", reason_kind="x")
check("a skip is a row with action 'skipped', costing nothing, and carries its reason", skipped["action"] == "skipped"
      and skipped["cost"] == 0.0 and skipped["reason"] == "cap reached" and skipped["reason_kind"] == "x", skipped)
check("an order id names its policy, its subject and its year",
      automation_audit.order_id("auto_mine", "coal", 130) == "auto_mine:coal:130")

# --- the window of years kept and read
trail = household_at(200, rows=[{"year": 200 - offset} for offset in range(automation_audit.YEARS_KEPT + 3)])
automation_audit.begin_year(trail)
check("the trail is kept to a few years",
      {each["year"] for each in trail.state.household.automation_audit}
      == {200 - offset for offset in range(automation_audit.YEARS_KEPT)}, trail.state.household.automation_audit)
read = household_at(200, rows=[{"year": year} for year in (196, 197, 198, 199, 200)])
check("by default the rows read are the year just played (and the one in progress)",
      {each["year"] for each in automation_audit.rows(read)} == {199, 200}, automation_audit.rows(read))
check("years widens the window", {each["year"] for each in automation_audit.rows(read, 3)} == {197, 198, 199, 200})
check("a window of nothing still reads the year just played", {each["year"] for each in automation_audit.rows(read, 0)} == {199, 200})

# --- the command and the screen
reply = _cmd_automation(read, {}, {"cmd": "automation", "years": 2}, None)
check("the automation command lists the rows of the window, with a count", reply["ok"] and reply["years"] == 2
      and len(reply["rows"]) == 3 and "3 automatic actions" in reply["note"], reply)
empty = _cmd_automation(household_at(200), {}, {"cmd": "automation"}, None)
check("with nothing automatic in the window the audit is empty and says so", empty["rows"] == [] and empty["ok"], empty)
# presentation: the printed screen leads with the policy and shows reason and cost
text = _RENDERERS["automation"]({"rows": [dict(row, reason="staff target 5.0 against 2.0 held")]})
check("the printed screen leads with the policy and shows what, reason and cost",
      "WHAT AUTOMATION DID" in text and "AUTO_HIRE" in text and "3 artisan" in text
      and "staff target" in text and "Cost: 100" in text, text)
