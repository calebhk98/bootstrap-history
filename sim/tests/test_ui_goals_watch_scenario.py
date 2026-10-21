"""Scenarios (Complaint 268 and 640): watched goals in one played game: the `commitments` screen lists them, a fogged
game hides what it must, and what is watched survives a save and a load. The rules are in test_ui_goals_watch."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.ui import memory


def ask(**fields):
    return S._agent_dispatch(game, NODES, fields)


game = sim()
report = ask(cmd="goals")
other = report["choices"][0]
reply = ask(cmd="goals", action="watch", goal=other["name"])
check("a goal watched by name in a played game is listed by `goals` and by `commitments`",
      [row["id"] for row in reply["watched"]] == [other["id"]]
      and [row["id"] for row in ask(cmd="commitments")["secondary_goals"]] == [other["id"]], reply["watched"])

# Fog: the real tree has goals the player cannot know.
game.fog, game.revealed = True, set()
fogged = ask(cmd="goals")
unseen = next((row for row in report["choices"] + [report["formal"]]
               if row["id"] != other["id"] and not game.is_visible(row["id"])), None)
check("the fogged played game hides some goal, counts it, and never names it on `commitments`",
      unseen is not None and fogged["unknown_goals"] > 0 and fogged["formal"]["id"] is None
      and all(row["name"] is None or game.is_visible(row["id"]) for row in ask(cmd="commitments")["secondary_goals"]),
      fogged)
refusal = ask(cmd="goals", action="watch", goal=NODES[unseen["id"]]["name"])
check("a fogged goal's name cannot be watched in a played game", refusal["ok"] is False, refusal)
game.fog = False

# What is watched survives a save and a load.
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "game.json")
    memory.save_state(game, path)
    memory.restore(game, {})
    check("forgotten watches are gone", ask(cmd="goals")["watched"] == [])
    memory.load_state(game, path)
    check("watched goals persist", [row["id"] for row in ask(cmd="goals")["watched"]] == [other["id"]])
