"""Complaint 100, items 9 and 10: the closing-concerns pointer explains itself once, and a long run of
active projects collapses to a bounded list plus a summary by what they wait on."""
from .harness import *  # noqa: F401,F403

from sim.engine.proto.render_screens_big import _state_concerns, _state_running


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


# item 9: the shut-concerns explanation is whole the first time, short afterwards, whole again on `full`
game = sim(capital=1_000_000.0)
shut = next(node_id for node_id in NODES if NODES[node_id]["rev"] > 0)
game.done.add(shut)
first = ask(game, cmd="state")
second = ask(game, cmd="state")
forced = ask(game, cmd="state", full=True)
check("the first state shows shut concerns", first.get("you_know_how_to_run_but_have_not_opened"), first.get("you_know_how_to_run_but_have_not_opened"))
check("the first state carries no 'seen' mark", not first.get("shut_concerns_pointer_seen"))
check("a later state marks the pointer as already explained", second.get("shut_concerns_pointer_seen") is True)
check("`full` explains it again", not forced.get("shut_concerns_pointer_seen"))
whole = "\n".join(_state_concerns(first))
brief = "\n".join(_state_concerns(second))
check("the whole line says what to do about shut concerns", "have not opened them" in whole, whole)
check("the repeat is shorter and still points at 'ventures'",
      len(brief) < len(whole) and "ventures" in brief and "have not opened them" not in brief, brief)

# item 10: many active projects
crowd = {"project_%02d" % number: {"founder_hours_total": 100, "founder_hours_left": 50, "still_to_pay": 10,
                                   "waiting_on": "the calendar" if number % 2 else "money", "name": "Project %d" % number}
         for number in range(40)}
lines = _state_running({"active": crowd})
check("a long run of active projects is bounded", len(lines) < 40, len(lines))
check("the rest are summarised by what they wait on and point at 'portfolio'",
      any("portfolio" in line and "calendar" in line and "money" in line for line in lines), lines[-3:])
few = _state_running({"active": dict(list(crowd.items())[:3])})
check("a short list is shown in full", sum(1 for line in few if line.startswith("  project_")) == 3, few)

# item 4: the staffing-as-a-share explanation is shown once, then again on `full`
staffed = sim(capital=1_000_000.0)
staffed.done.add(shut)
first_ventures = ask(staffed, cmd="ventures")
second_ventures = ask(staffed, cmd="ventures")
again = ask(staffed, cmd="ventures", full=True)
key = "these_are_a_share_of_their_year_not_a_headcount"
check("ventures explains staff shares the first time", bool(first_ventures.get(key)), sorted(first_ventures))
check("ventures repeats only a one-line pointer to the staff-share explanation",
      0 < len(second_ventures.get(key) or "") < len(first_ventures.get(key) or "") and "full" in second_ventures[key],
      (first_ventures.get(key), second_ventures.get(key)))
check("ventures full explains it again", bool(again.get(key)))
