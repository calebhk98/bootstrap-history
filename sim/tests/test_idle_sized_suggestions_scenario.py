"""Scenarios (Complaint 640; the rules are in test_idle_sized_suggestions): `idle` sizes what the hours could do on a
whole game, and a multi-year `step` names the kind of delay behind the idle hours before it proceeds."""
from .harness import *  # noqa: F401,F403


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


test_sim = sim(capital=1_000_000.0)
idle = ask(test_sim, cmd="idle")
uses = idle.get("potential_uses", {})
program = uses.get("development_program")
check("idle offers a development program sized by its own hours and cost", isinstance(program, dict)
      and {"id", "cash_cost", "directed_hours_per_year", "years"} <= set(program), uses)
check("the program is something startable today", program and test_sim.can_start(program["id"]), program)

# a sized training suggestion for each oversubscribed trade
crowded = test_sim
crowded.trade_demand_vs_supply = lambda: {"machinist": {
    "demand_hours_this_year": 5000.0, "supply_hours_this_year": 1000.0, "oversubscribed": True,
    "projects_drawing_on_it": ["x"]}}
sized = ask(crowded, cmd="idle")["potential_uses"]["train_oversubscribed_trades"]
check("an oversubscribed trade gets a sized teaching suggestion", isinstance(sized, list) and len(sized) == 1, sized)
check("the sized suggestion is the trade's, with the command to teach it",
      sized[0]["trade"] == "machinist" and sized[0]["command"].startswith("train machinist"), sized)

# the pre-step warning names the delay kind
waiting = sim(capital=1_000_000.0)
target = next((node_id for node_id in waiting.order
               if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 0 and waiting.can_start(node_id)), None)
waiting.end_year = waiting.cfg["start_year"] + waiting.cfg["horizon_years"]
ask(waiting, cmd="start", id=target)
waiting.active[target]["ph_left"] = 0.0
waiting.active[target]["cost_left"] = 0.0
waiting.active[target]["lab_left"] = {}
stepped = ask(waiting, cmd="step", years=2)
warning = stepped.get("multi_year_hours_warning") or ""
check("a multi-year step with idle hours names what the running projects wait on", "calendar" in (stepped.get("multi_year_hours_waiting_on") or ()),
      stepped.get("multi_year_hours_warning") or sorted(stepped))
