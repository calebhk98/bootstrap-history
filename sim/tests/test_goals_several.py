"""goals_several: goals keyed by id with a reach year each, promotion of a watched goal, the
anatomy hook and goal-cache invalidation (Complaint 422), run with `--only goals_several`."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.ui import memory
from sim.ui.proto import anatomy


def ask(game, **fields):
    return S._agent_dispatch(game, NODES, fields)


general_goal = "goal_literacy_common"
elite_goal = "goal_literate_nation"

# A goal change drops every cache keyed on the old goal.
game = sim()
game.goal = general_goal
road = {node_id for node_id in NODES if game.on_road_to_goal(node_id)}
check("the goal road is cached for the first goal", road == S.closure(NODES, general_goal))
game.goal = elite_goal
check("changing the goal drops the cached road",
      {node_id for node_id in NODES if game.on_road_to_goal(node_id)} == S.closure(NODES, elite_goal))
game._goal_critical_floor = 123.0
game.goal = general_goal
check("changing the goal drops the cached critical floor", getattr(game, "_goal_critical_floor", None) is None)

# Each goal keeps its own reach year.
game = sim()
game.goal = general_goal
game.civ["literacy_general"] = 0.5
game._check_win_conditions(1000)
check("the first goal records its year", game.goal_year == 1000 and game.state.seat_progress.goal_years == {general_goal: 1000},
      game.state.seat_progress.goal_years)
game.set_goal(elite_goal)
check("a new goal starts with no reach year", game.goal_year is None and game.goal == elite_goal)
game.civ["literacy_general"] = 0.9
game._check_win_conditions(1007)
check("the second goal records its own year", game.goal_year == 1007, game.goal_year)
check("the first goal's year is kept", game.state.seat_progress.goal_years == {general_goal: 1000, elite_goal: 1007},
      game.state.seat_progress.goal_years)
game.set_goal(general_goal)
check("returning to a reached goal restores its year", game.goal_year == 1000, game.goal_year)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "game.json")
    memory.save_state(game, path)
    game.state.seat_progress.goal_years = {}
    memory.load_state(game, path)
    check("goal years round-trip a save", game.state.seat_progress.goal_years == {general_goal: 1000, elite_goal: 1007},
          game.state.seat_progress.goal_years)

# A watched goal is promoted once the formal goal is reached.
game = sim()
game.goal = general_goal
game.civ["literacy_general"] = 0.0
other = next(row["id"] for row in ask(game, cmd="goals")["choices"]
             if row["id"] != elite_goal and not NODES[row["id"]].get("win_condition"))
ask(game, cmd="goals", action="watch", goal=other)
early = ask(game, cmd="goals", action="promote")
check("promotion is refused before the formal goal is reached", early["ok"] is False and game.goal == general_goal, early)
game.civ["literacy_general"] = 1.0
game._check_win_conditions(1000)
promoted = ask(game, cmd="goals", action="promote", goal=other)
check("a watched goal becomes the formal goal after a win", promoted["ok"] is not False and game.goal == other, promoted)
check("the promoted goal leaves the watch list", promoted["watched"] == [] and promoted["formal"]["id"] == other, promoted)
check("the new formal goal has no year yet, the old one keeps its", game.goal_year is None
      and game.state.seat_progress.goal_years == {general_goal: 1000})
check("only a watched goal can be promoted", ask(game, cmd="goals", action="promote", goal=general_goal)["ok"] is False)

# The anatomy hook.
game = sim()
rows = game.win_condition_anatomy({"metric": "literacy_general", "op": ">=", "value": 0.2})
check("the hook returns (label, value, unit) rows", rows and all(len(row) == 3 for row in rows), rows)
check("the hook reports the live metric", any(row[0] == "current" and row[1] == game.civ.get("literacy_general") for row in rows), rows)
game.WIN_CONDITION_ANATOMY["mod_metric"] = lambda sim_, condition: [("grain stock", 3.0, "tonnes")]
try:
    check("a mod registers its own anatomy", game.win_condition_anatomy({"metric": "mod_metric"}) == [("grain stock", 3.0, "tonnes")])
    reply = anatomy.anatomy_for(game, {"metric": "mod_metric", "op": ">=", "value": 1.0})
    check("the anatomy command uses the hook for a metric it has no rule for",
          reply["generic"] is False and reply["rows"][0]["label"] == "grain stock", reply)
finally:
    del game.WIN_CONDITION_ANATOMY["mod_metric"]
