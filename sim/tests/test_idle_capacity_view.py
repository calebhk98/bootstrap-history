"""Complaint 101: an `idle` view of directed hours, what they could do, and why the wait."""
from .harness import *  # noqa: F401,F403

from sim.engine.proto import command_registry


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


test_sim = sim(capital=1_000_000.0)
idle = ask(test_sim, cmd="idle")
check("idle answers", idle.get("ok"), idle)
check("directed capacity is the engine's director pool",
      abs(idle["directed_hours_this_year"] - test_sim.director_pool()) < 1, idle)
check("committed is the engine's committed hours",
      abs(idle["committed_hours"] - test_sim.director_hours_committed()) < 1, idle)
check("idle is capacity less committed",
      abs(idle["idle_hours"] - max(0.0, idle["directed_hours_this_year"] - idle["committed_hours"])) < 1, idle)
uses = idle.get("potential_uses", {})
startable = [node_id for node_id in NODES if node_id not in test_sim.done and node_id not in test_sim.active
             and test_sim.can_start(node_id)]
check("potential uses count what is startable today", uses.get("startable_today") == len(startable),
      (uses, len(startable)))
check("potential uses count the free ones", uses.get("startable_at_no_cash_cost")
      == sum(1 for node_id in startable if test_sim.project_cost(node_id) <= 0), uses)
check("it offers selling hours for wages as a use", "work" in str(uses.get("wage_work", "")), uses)
check("it never spends hours itself", test_sim.director_hours_committed() == idle["committed_hours"])

target = next((node_id for node_id in test_sim.order
               if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 0 and test_sim.can_start(node_id)), None)
ask(test_sim, cmd="start", id=target)
test_sim.active[target]["ph_left"] = 0.0
waiting = ask(test_sim, cmd="idle")
check("when every project is only waiting on the calendar it says the delay is the calendar",
      waiting["delay_kinds"].get("calendar") == [target], waiting.get("delay_kinds"))
check("a calendar wait is explained as not removable and not exclusive",
      "calendar" in waiting.get("what_the_wait_is", "") and "else" in waiting.get("what_the_wait_is", ""),
      waiting.get("what_the_wait_is"))
check("idle is in the command registry", "idle" in command_registry.COMMANDS)
