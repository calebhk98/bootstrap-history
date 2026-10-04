"""The note and notes commands: the player's own reasons, kept with the year (Complaint 207)."""
from .command_registry import command
from .notes_projects import resolve_project, split_leading_project
from .notes_store import MAX_TEXT, add_note, all_notes, clean_text, drop_note

PAGE = 20


def _project_name(sim, node_id):
    """The project's name, or None when there is none or fog hides it."""
    if node_id is None or node_id not in sim.nodes or (sim.fog and not sim.is_visible(node_id)):
        return None
    return sim.nodes[node_id].get("name", node_id)


def _entry(sim, row):
    visible = _project_name(sim, row["project"]) is not None
    return {"n": row["n"], "year": row["year"], "text": row["text"],
            "project": row["project"] if visible else None,
            "project_name": _project_name(sim, row["project"])}


def _drop(sim, number):
    row = drop_note(sim, number)
    if row is None:
        return {"ok": False, "error": "no note number %s. 'notes' lists them with their numbers" % number}
    return {"ok": True, "dropped": _entry(sim, row)}


def _whole_number(text):
    return int(text) if str(text).strip().isdigit() else None


@command("note", group="overview",
         summary="write down why you are doing something, kept with the year",
         usage=["note <text>", "note <project id or name> <text>", "note drop <n>",
                '{"cmd":"note","text":"...","project":"<id>"}'],
         options={"<text>": "your words, kept as typed (long notes are cut, see the reply)",
                  "<project>": "a project you know of, by id or exact name, to attach the note to it",
                  "--": "put before the text so a leading project name is read as plain text",
                  "drop <n>": "remove note number n"},
         description="Notes are yours alone: the game never reads them. 'notes' lists them, newest "
                     "first, and can show those of one project.")
def _cmd_note(sim, nodes, cmd, ended):
    text = str(cmd.get("text") or "")
    words = text.split()
    if len(words) == 2 and words[0].lower() == "drop" and _whole_number(words[1]) is not None:
        return _drop(sim, int(words[1]))
    if cmd.get("drop") is not None:
        number = _whole_number(cmd["drop"])
        return _drop(sim, number) if number is not None else {"ok": False, "error": "drop needs a note number"}
    node_id = None
    if cmd.get("project"):
        node_id, error = resolve_project(sim, cmd["project"])
        if error:
            return {"ok": False, "error": error}
    elif len(words) > 1:
        node_id, rest = split_leading_project(sim, words)
        text = rest if node_id or words[0] == "--" else text
    if not clean_text(text):
        return {"ok": False, "error": "write something: 'note <text>' or 'note <project> <text>'"}
    row = add_note(sim, text, node_id)
    if row is None:
        return {"ok": False, "error": "too many notes; 'notes' then 'note drop <n>' to clear some"}
    reply = {"ok": True, "added": _entry(sim, row)}
    if len(str(text).strip()) > MAX_TEXT:
        reply["cut"] = "the note was cut to its first %d characters" % MAX_TEXT
    return reply


@command("notes", group="overview",
         summary="your notes, newest first",
         usage=["notes", "notes <project id or name>", "notes limit:10 offset:10"],
         options={"<project>": "only the notes attached to this project",
                  "limit / offset": "page size and position"},
         description="What you wrote with 'note', with its number, year and project.")
def _cmd_notes(sim, nodes, cmd, ended):
    rows = all_notes(sim)
    shown_project = None
    if cmd.get("project"):
        shown_project, error = resolve_project(sim, cmd["project"])
        if error:
            return {"ok": False, "error": error}
        rows = [row for row in rows if row["project"] == shown_project]
    rows.reverse()
    offset = max(0, _whole_number(cmd.get("offset", 0)) or 0)
    limit = max(1, min(100, _whole_number(cmd.get("limit", PAGE)) or PAGE))
    page = rows[offset:offset + limit]
    reply = {"ok": True, "count": len(rows), "entries": [_entry(sim, row) for row in page],
             "filter": _project_name(sim, shown_project)}
    if offset + len(page) < len(rows):
        reply["more"] = "%d more; 'notes limit:%d offset:%d'" % (
            len(rows) - offset - len(page), limit, offset + len(page))
    if not rows:
        reply["hint"] = "none yet; 'note <text>' writes one"
    return reply
