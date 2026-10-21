"""Complaint 91: automation leaves a per-turn audit trail of what it did, why and at what cost.

The trail's rules (a row's shape and cost, the years kept, the window the `automation` command reads, the
screen) are tested on a stand-in for the household; two named scenarios run automation on a game and reconcile
the trail with what the engine really did."""
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


# --- scenario: an automatic game's audit rows match what the engine really did
def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


def play_year(game):
    """One year of the staff, money and project work (where automation acts) and the calendar, without the
    market closing around it."""
    seat = game.playing_seats()[0]
    with game.act_as(seat):
        game.begin_seat_year()
        game.begin_world_year()
        game._step_apprenticeships()
        game._step_staff()
        game._step_money_seat()
        game._step_dated_shocks([seat])
        game._run_seat_work()
    game.state.scenario.year += 1


auto = sim(capital=2_000_000.0, manual=False)
auto.end_year = auto.cfg["start_year"] + auto.cfg["horizon_years"]
seen = {"hired": [], "opened": [], "reopened": [], "commissioned": []}


def watch(name, bucket, outcome, owner=auto):
    original = getattr(owner, name)

    def wrapper(*args, **kwargs):
        before = auto.capital
        held = dict(auto.employees)
        result = original(*args, **kwargs)
        seen[bucket].append((auto.year, outcome(args, result, held), before - auto.capital))
        return result
    setattr(owner, name, wrapper)


# hiring lives in the labour package; the outcome is the trade and the people the staff gained
watch("hire", "hired", lambda args, result, held: (args[0], round(auto.employees.get(args[0], 0.0) - held.get(args[0], 0.0)))
      if result and result[0] else None, owner=auto.labour)
watch("auto_open_ventures", "opened", lambda args, result, held: tuple(result))
watch("reopen_restaffed_ventures", "reopened", lambda args, result, held: tuple(result))
watch("auto_commission_for_blocked", "commissioned", lambda args, result, held: result, owner=auto.labour)

per_year = {}
for played in range(4):
    if played == 0:
        ask(auto, cmd="step", years=1)    # one full year through the step command
    else:
        play_year(auto)
    per_year[auto.year] = ask(auto, cmd="automation")
all_rows = [each for each_reply in per_year.values() for each in each_reply["rows"]]
hired_rows = [each for each in all_rows if each["action"] == "hire"]
hired_seen = [entry for entry in seen["hired"] if entry[1]]
rows_match = {}
for action, bucket in (("open", "opened"), ("reopen", "reopened")):
    rows_ = [each for each in all_rows if each["action"] == action]
    expected = [(year, ids, cost) for year, ids, cost in seen[bucket] if ids]
    rows_match[action] = (sorted((each["year"], tuple(each["ids"]), each["cost"]) for each in rows_)
                          == sorted((year, ids, round(cost, 1)) for year, ids, cost in expected))
commission_rows = [each for each in all_rows if each["action"] == "commission"]
commission_seen = [entry for entry in seen["commissioned"] if entry[1]]
check("scenario: every automatic hire, opening, reopening and commission of a played run has one row with the same "
      "trade, people, concerns and cost, and every row says why",
      all_rows and all(each_reply["ok"] for each_reply in per_year.values())
      and all(each["reason"] for each in all_rows) and hired_rows and hired_seen
      and sorted((each["year"], each["what"], each["cost"]) for each in hired_rows)
      == sorted((year, "%d %s" % (outcome[1], outcome[0]), round(cost, 1)) for year, outcome, cost in hired_seen)
      and all(rows_match.values()) and any(each["action"] == "open" for each in all_rows)
      and len(commission_rows) == len(commission_seen),
      (len(hired_rows), len(hired_seen), rows_match, [each["action"] for each in all_rows][:10]))

manual = sim(capital=2_000_000.0)
manual.end_year = manual.cfg["start_year"] + manual.cfg["horizon_years"]
play_year(manual)
manual_audit_empty = ask(manual, cmd="automation")["rows"] == []


def _material_step(binding, demand_key, policy):
    manual.capital = 5_000_000_000_000.0
    manual.state.household.automation_audit = []
    manual.state.founder.policy[policy] = True
    manual.annual_material_demand = lambda: {demand_key: 1_000_000.0}
    manual.resource_throttle = lambda: 0.3
    manual.state.holdings.binding = binding
    manual._step_materials()
    return [each for each in manual.state.household.automation_audit]


mine_rows = [each for each in _material_step("coal", "coal_kg", "auto_mine") if each["action"] == "mine"]
forest_rows = [each for each in _material_step("charcoal", "charcoal_kg", "auto_forest") if each["action"] == "forest"]
nitre_rows = [each for each in _material_step("saltpetre", "saltpetre_kg", "auto_mine") if each["action"] == "nitre"]
check("scenario: a manual game has an empty audit; auto-mine, auto-forest and nitre beds each record what they ordered, "
      "with the demand and capacity considered and the cost",
      manual_audit_empty
      and len(mine_rows) == 1 and mine_rows[0]["policy"] == "auto_mine"
      and mine_rows[0].get("reason_kind") == "mine_ordered" and mine_rows[0]["demand"] == 1_000_000.0
      and "active_capacity" in mine_rows[0] and "pending_capacity" in mine_rows[0]
      and len(forest_rows) == 1 and forest_rows[0]["cost"] > 0
      and len(nitre_rows) == 1 and nitre_rows[0]["cost"] > 0,
      (manual_audit_empty, mine_rows, forest_rows, nitre_rows))
