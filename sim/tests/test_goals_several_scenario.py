"""SCENARIO: a game's goals reach in turn, keep their years through a save, and a watched goal is promoted by the
`goals` command. The rules (goal-cache invalidation, the year bookkeeping, the anatomy hook) are in `test_goals_several`."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.ui import memory


def ask(game, **fields):
    return S._agent_dispatch(game, NODES, fields)


general_goal = "goal_literacy_common"
elite_goal = "goal_literate_nation"

# Each goal keeps its own reach year.
game = unopened_sim()
game.goal = general_goal
game.set_literacy("literacy_general", 0.5)
game._check_win_conditions(1000)
check("the first goal records its year", game.goal_year == 1000 and game.state.seat_progress.goal_years == {general_goal: 1000},
      game.state.seat_progress.goal_years)
game.set_goal(elite_goal)
check("a new goal starts with no reach year", game.goal_year is None and game.goal == elite_goal)
game.set_literacy("literacy_general", 0.9)
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
game = unopened_sim()
game.goal = general_goal
game.set_literacy("literacy_general", 0.0)
other = next(row["id"] for row in ask(game, cmd="goals")["choices"]
             if row["id"] != elite_goal and not NODES[row["id"]].get("win_condition"))
ask(game, cmd="goals", action="watch", goal=other)
early = ask(game, cmd="goals", action="promote")
check("promotion is refused before the formal goal is reached", early["ok"] is False and game.goal == general_goal, early)
game.set_literacy("literacy_general", 1.0)
game._check_win_conditions(1000)
promoted = ask(game, cmd="goals", action="promote", goal=other)
check("a watched goal becomes the formal goal after a win", promoted["ok"] is not False and game.goal == other, promoted)
check("the promoted goal leaves the watch list", promoted["watched"] == [] and promoted["formal"]["id"] == other, promoted)
check("the new formal goal has no year yet, the old one keeps its", game.goal_year is None
      and game.state.seat_progress.goal_years == {general_goal: 1000})
check("only a watched goal can be promoted", ask(game, cmd="goals", action="promote", goal=general_goal)["ok"] is False)
