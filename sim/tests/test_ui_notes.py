"""ui_notes: the note and notes commands (Complaint 207), run with `--only ui_notes`."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.ui import memory
from sim.ui.proto.notes_store import MAX_TEXT, note_log_rows, notes_for
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed

# Renderers, on hand-written replies.
entry = {"n": 3, "year": 1301, "text": "mill before the loom", "project": "x", "project_name": "Water mill"}
listing = render_pretty("notes", {"ok": True, "count": 1, "entries": [entry]})
check("a note line shows number, year, text and project", "#3" in listing and "[Water mill]" in listing, listing)
check("an empty list says how to start", "note <text>" in render_pretty(
    "notes", {"ok": True, "count": 0, "entries": [], "hint": "none yet; 'note <text>' writes one"}))
check("a drop is confirmed", "dropped note #3" in render_pretty("note", {"ok": True, "dropped": entry}))

# Typed lines reach the handler with the words intact.
check("typed note keeps its words", parse_typed("note Build the mill, then 2 looms")[0]
      == {"cmd": "note", "text": "Build the mill, then 2 looms"})
check("typed notes takes paging", parse_typed("notes limit:5 offset:5")[0] == {"cmd": "notes", "limit": 5, "offset": 5})


def ask(**fields):
    return S._agent_dispatch(game, NODES, fields)


game = sim()
visible = next(node_id for node_id in sorted(NODES) if game.is_visible(node_id))
visible_name = NODES[visible]["name"]
check("a bare note is stored with the year", ask(cmd="note", text="  keep   spacing  ")["added"]["year"] == game.year)
check("note text is kept verbatim", ask(cmd="notes")["entries"][0]["text"] == "keep   spacing")
check("a long note is cut and says so", "cut" in ask(cmd="note", text="x" * (MAX_TEXT + 5)))
check("an empty note is refused", ask(cmd="note", text="  ")["ok"] is False)

attached = ask(cmd="note", text="%s because grain is short" % visible)
check("a leading project id attaches the note",
      attached["added"]["project"] == visible and attached["added"]["text"] == "because grain is short", attached)
check("a leading project name attaches too",
      ask(cmd="note", text="%s second thought" % visible_name)["added"]["project"] == visible)
check("-- keeps a leading project name as plain text",
      ask(cmd="note", text="-- %s is just words" % visible)["added"]["project"] is None)
check("notes_for returns the project's notes oldest first",
      [row["text"] for row in notes_for(game, visible)] == ["because grain is short", "second thought"])
check("notes filters by project and lists newest first",
      [row["text"] for row in ask(cmd="notes", project=visible)["entries"]] == ["second thought", "because grain is short"])
check("note_log_rows has the household log's (year, text) shape",
      note_log_rows(game) and all(isinstance(year, int) and isinstance(text, str) for year, text in note_log_rows(game)))

page = ask(cmd="notes", limit=2)
check("a page is bounded and says how to continue", len(page["entries"]) == 2 and "offset:2" in page["more"], page)
first = page["entries"][0]["n"]
check("drop removes one note", ask(cmd="note", text="drop %d" % first)["dropped"]["n"] == first
      and all(row["n"] != first for row in ask(cmd="notes", limit=100)["entries"]))
check("dropping a missing note says so", ask(cmd="note", text="drop 9999")["ok"] is False)

# Fog: an unseen project cannot be named, and the refusal does not name it.
game.fog, game.revealed = True, set()
unseen = next((node_id for node_id in sorted(NODES) if not game.is_visible(node_id)), None)
check("the fogged game has something unseen", unseen is not None)
if unseen:
    refusal = ask(cmd="note", project=unseen, text="spy")
    check("a fogged project cannot be attached",
          refusal["ok"] is False and NODES[unseen]["name"] not in refusal["error"], refusal)
    check("a fogged id typed first is plain text", ask(cmd="note", text="%s x" % unseen)["added"]["project"] is None)
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
