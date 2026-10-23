"""Scenarios (Complaint 207 and 640): the player's notes in one played game, through the command dispatch, and through a
save and a load. The rules are in test_ui_notes."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.ui import memory
from sim.ui.proto.notes_store import note_log_rows


def ask(**fields):
    return S._agent_dispatch(game, NODES, fields)


game = unopened_sim()
visible = next(node_id for node_id in sorted(NODES) if game.is_visible(node_id))
added = ask(cmd="note", text="%s because grain is short" % visible)["added"]
check("a note written to a played game carries the year and the attached project",
      added["year"] == game.year and added["project"] == visible, added)

# Fog: the played game has projects the player has not seen.
game.fog, game.revealed = True, set()
unseen = next((node_id for node_id in sorted(NODES) if not game.is_visible(node_id)), None)
refusal = ask(cmd="note", project=unseen, text="spy")
check("a fogged project of a played game cannot be attached and the refusal does not name it",
      unseen is not None and refusal["ok"] is False and NODES[unseen]["name"] not in refusal["error"], refusal)
game.fog = False

# Notes survive a save and a load.
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "game.json")
    before = note_log_rows(game)
    memory.save_state(game, path)
    memory.restore(game, {})
    check("forgotten notes are gone", note_log_rows(game) == [])
    memory.load_state(game, path)
    check("notes persist through save and load", before and note_log_rows(game) == before)
