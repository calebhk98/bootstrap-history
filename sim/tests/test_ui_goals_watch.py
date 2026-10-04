"""ui_goals_watch: the in-game goals view and watched goals (Complaint 268), run with `--only ui_goals_watch`."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.ui import memory
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed

# Renderers, on hand-written replies.
formal = {"id": None, "name": None, "done": 4, "total": 40, "reached": False, "year_reached": None}
hidden = {"id": None, "name": None, "done": 1, "total": 9, "reached": False}
text = render_pretty("goals", {"ok": True, "formal": formal, "watched": [hidden], "choices": [],
                               "unknown_goals": 3, "fog": True, "note": "n"})
check("a fogged goal shows only counts", "4 of 40" in text and "1 of 9" in text and "3 more" in text, text)
check("typed goals watch carries the goal words",
      parse_typed("goals watch Steam engine")[0] == {"cmd": "goals", "action": "watch", "goal": "Steam engine"})
check("bare goals stays bare", parse_typed("goals")[0] == {"cmd": "goals"})


def ask(**fields):
    return S._agent_dispatch(game, NODES, fields)


game = sim()
report = ask(cmd="goals")
check("the view shows progress toward the formal goal",
      report["formal"]["id"] == game.goal and report["formal"]["total"] > 0
      and report["formal"]["done"] <= report["formal"]["total"], report.get("formal"))
other = report["choices"][0]
reply = ask(cmd="goals", action="watch", goal=other["name"])
check("a goal can be watched by name", [row["id"] for row in reply["watched"]] == [other["id"]], reply)
check("the formal goal is untouched", game.goal == report["formal"]["id"])
check("the reply says a watched goal is only tracked", "tracked here only" in reply["note"])
check("a watched goal leaves the choices", all(row["id"] != other["id"] for row in reply["choices"]))
check("the formal goal cannot be watched", ask(cmd="goals", action="watch", goal=game.goal)["ok"] is False)
check("commitments lists the watched goal",
      [row["id"] for row in ask(cmd="commitments")["secondary_goals"]] == [other["id"]])
check("an unknown goal is refused", ask(cmd="goals", action="watch", goal="no such goal at all")["ok"] is False)

# Fog: a goal the player cannot know is never named and cannot be watched.
game.fog, game.revealed = True, set()
unseen = next((row for row in report["choices"] + [report["formal"]]
               if row["id"] != other["id"] and not game.is_visible(row["id"])), None)
check("the fogged game hides some goal", unseen is not None)
fogged = ask(cmd="goals")
check("under fog the formal goal is a count", fogged["formal"]["id"] is None and fogged["formal"]["name"] is None
      and fogged["formal"]["total"] > 0, fogged["formal"])
check("under fog hidden goals are only counted", fogged["unknown_goals"] > 0
      and all(game.is_visible(row["id"]) for row in fogged["choices"]), fogged)
refusal = ask(cmd="goals", action="watch", goal=NODES[unseen["id"]]["name"])
check("a fogged goal's name cannot be watched", refusal["ok"] is False and NODES[unseen["id"]]["name"] not in refusal["error"].replace(
    "%r" % NODES[unseen["id"]]["name"], ""), refusal)
check("the fogged commitments screen has no hidden name",
      all(row["name"] is None or game.is_visible(row["id"]) for row in ask(cmd="commitments")["secondary_goals"]))
game.fog = False

unwatched = ask(cmd="goals", action="unwatch", goal=other["id"])
check("a goal can be unwatched", unwatched["watched"] == [], unwatched)

# What is watched survives a save and a load.
ask(cmd="goals", action="watch", goal=other["id"])
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "game.json")
    memory.save_state(game, path)
    memory.restore(game, {})
    check("forgotten watches are gone", ask(cmd="goals")["watched"] == [])
    memory.load_state(game, path)
    check("watched goals persist", [row["id"] for row in ask(cmd="goals")["watched"]] == [other["id"]])
