"""Scenario: the parallelism notes reach a running game's `start` and `state` replies. The rules are in
test_parallelism_note."""
from .harness import *  # noqa: F401,F403

game = sim(capital=1_000_000.0)
target = next((node_id for node_id in game.order if NODES[node_id]["yrs"] >= 2 and game.can_start(node_id)), None)
check("a real startable multi-year project exists to test the note against", target is not None, target)
if target:
    first = S._agent_dispatch(game, NODES, {"cmd": "start", "id": target})
    second_target = next((node_id for node_id in game.order if NODES[node_id]["yrs"] >= 2 and game.can_start(node_id)), None)
    second = S._agent_dispatch(game, NODES, {"cmd": "start", "id": second_target}) if second_target else {}
    check("starting the first long project carries the note, and a second in the same run does not repeat it",
          "a_calendar_floor_is_not_exclusive_research_time" in first
          and "a_calendar_floor_is_not_exclusive_research_time" not in second, (list(first), list(second)))

spare = sim(capital=1_000_000.0)
long_target = next((node_id for node_id in spare.order
                    if NODES[node_id]["yrs"] >= 3 and NODES[node_id]["ph"] > 0 and spare.can_start(node_id)), None)
check("a startable project with real founder-hours and a real calendar floor exists", long_target is not None, long_target)
if long_target:
    S._agent_dispatch(spare, NODES, {"cmd": "start", "id": long_target})
    spare.active[long_target]["ph_left"] = 0.0     # its hours spent for the year: purely calendar-bound
    reply = S._agent_dispatch(spare, NODES, {"cmd": "state"})
    check("when every active project only waits on the calendar and real founder-hours sit unused, state says so",
          bool(reply.get("free_hours_going_unused")), reply.get("free_hours_going_unused"))
