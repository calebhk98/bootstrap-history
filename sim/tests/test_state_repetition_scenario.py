"""Complaint 100, items 4 and 9 through the command handlers: `state` and `ventures` mark an explanation as seen
and `full` brings it back. Complaint 640: the once-only rule is `already_explained` in test_state_repetition; this is
the wiring of the two commands on one game."""
from .harness import *  # noqa: F401,F403


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


# item 9: the shut-concerns explanation is marked seen after the first time, and not on `full`
game = unopened_sim(capital=1_000_000.0)
shut = next(node_id for node_id in NODES if NODES[node_id]["rev"] > 0)
game.done.add(shut)
first = ask(game, cmd="state")
second = ask(game, cmd="state")
forced = ask(game, cmd="state", full=True)
check("the first state shows shut concerns", first.get("you_know_how_to_run_but_have_not_opened"), first.get("you_know_how_to_run_but_have_not_opened"))
check("the first state carries no 'seen' mark", not first.get("shut_concerns_pointer_seen"))
check("a later state marks the pointer as already explained", second.get("shut_concerns_pointer_seen") is True)
check("`full` explains it again", not forced.get("shut_concerns_pointer_seen"))

# item 4: the staffing-as-a-share explanation is shown once, then again on `full`
staffed = unopened_sim(capital=1_000_000.0)
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
