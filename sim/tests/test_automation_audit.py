"""Complaint 91: automation leaves a per-turn audit trail of what it did, why and at what cost."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.render_typed import _RENDERERS


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


auto = sim(capital=2_000_000.0, manual=False)
auto.end_year = auto.cfg["start_year"] + auto.cfg["horizon_years"]

seen = {"hired": [], "opened": [], "reopened": [], "commissioned": []}
year_of = lambda: auto.year


def watch(name, bucket, outcome):
    original = getattr(auto, name)

    def wrapper(*args, **kwargs):
        before = auto.capital
        result = original(*args, **kwargs)
        seen[bucket].append((year_of(), outcome(args, result), before - auto.capital))
        return result
    setattr(auto, name, wrapper)


watch("hire", "hired", lambda args, result: (args[0], args[1]) if result and result[0] else None)
watch("auto_open_ventures", "opened", lambda args, result: tuple(result))
watch("reopen_restaffed_ventures", "reopened", lambda args, result: tuple(result))
watch("auto_commission_for_blocked", "commissioned", lambda args, result: result)

per_year = {}
for _ in range(12):
    ask(auto, cmd="step", years=1)
    per_year[auto.year] = ask(auto, cmd="automation")

all_rows = [row for reply in per_year.values() for row in reply["rows"]]
check("the automation command lists rows", all_rows and all(reply["ok"] for reply in per_year.values()), per_year.get(auto.year))
check("every row says year, policy, action, what, reason and cost",
      all({"year", "policy", "action", "what", "reason", "cost"} <= set(row) and row["reason"] for row in all_rows),
      all_rows[:2])

hired_rows = [row for row in all_rows if row["action"] == "hire"]
hired_seen = [entry for entry in seen["hired"] if entry[1]]
check("the run did hire through automation", hired_rows and hired_seen, (len(hired_rows), len(hired_seen)))
check("every successful automatic hire has a row of the same trade, count and cost",
      sorted((year, row["what"], row["cost"]) for year, row in ((row["year"], row) for row in hired_rows))
      == sorted((year, "%d %s" % (outcome[1], outcome[0]), round(cost, 1)) for year, outcome, cost in hired_seen),
      (hired_rows[:2], hired_seen[:2]))

for action, bucket in (("open", "opened"), ("reopen", "reopened")):
    rows_ = [row for row in all_rows if row["action"] == action]
    expected = [(year, ids, cost) for year, ids, cost in seen[bucket] if ids]
    check("every %s call that did something has one row naming its concerns and cost" % action,
          sorted((row["year"], tuple(row["ids"]), row["cost"]) for row in rows_)
          == sorted((year, ids, round(cost, 1)) for year, ids, cost in expected), (rows_[:2], expected[:2]))
check("the run opened something automatically", any(row["action"] == "open" for row in all_rows),
      [row["action"] for row in all_rows][:10])

commission_rows = [row for row in all_rows if row["action"] == "commission"]
commission_seen = [entry for entry in seen["commissioned"] if entry[1]]
check("every automatic commission has a row", len(commission_rows) == len(commission_seen),
      (commission_rows, commission_seen))

latest = next(reply for year, reply in sorted(per_year.items(), reverse=True) if reply["rows"])
check("by default the reply is only the year just played",
      all(row["year"] == auto.year - 1 for row in per_year[auto.year]["rows"]), per_year[auto.year]["rows"][:2])
wider = ask(auto, cmd="automation", years=3)
check("years widens the window", len({row["year"] for row in wider["rows"]}) > 1, wider["rows"][:1])
check("the window is kept to a few years", min(row["year"] for row in auto.state.household.automation_audit)
      > auto.year - 6, auto.state.household.automation_audit[:1])
text = _RENDERERS["automation"](latest)
check("the printed screen leads with the policy and shows reason and cost",
      "AUTOMATION" in text and latest["rows"][0]["reason"][:20] in text, text[:400])

manual = sim(capital=2_000_000.0)
manual.end_year = manual.cfg["start_year"] + manual.cfg["horizon_years"]
ask(manual, cmd="step", years=2)
check("a manual game with no automation has an empty audit", ask(manual, cmd="automation")["rows"] == [])


def _material_step(binding, demand_key, policy):
    test_sim = sim(capital=5_000_000_000_000.0, manual=False)
    test_sim.state.founder.policy[policy] = True
    test_sim.annual_material_demand = lambda: {demand_key: 1_000_000.0}
    test_sim.resource_throttle = lambda: 0.3
    test_sim.state.economy.binding = binding
    test_sim._step_materials()
    return test_sim


mined = _material_step("coal", "coal_kg", "auto_mine")
mine_rows = [row for row in mined.state.household.automation_audit if row["action"] == "mine"]
check("auto-mine records what it ordered, the demand and the capacity it considered",
      len(mine_rows) == 1 and mine_rows[0]["policy"] == "auto_mine"
      and "demand 1000000" in mine_rows[0]["reason"]
      and "pending capacity considered" in mine_rows[0]["reason"], mine_rows)

wooded = _material_step("charcoal", "charcoal_kg", "auto_forest")
forest_rows = [row for row in wooded.state.household.automation_audit if row["action"] == "forest"]
check("auto-forest records the hectares it bought and its cost",
      len(forest_rows) == 1 and forest_rows[0]["cost"] > 0, forest_rows)

nitre = _material_step("saltpetre", "saltpetre_kg", "auto_mine")
nitre_rows = [row for row in nitre.state.household.automation_audit if row["action"] == "nitre"]
check("auto-mine's nitre beds are recorded with their cost",
      len(nitre_rows) == 1 and nitre_rows[0]["cost"] > 0, nitre_rows)
