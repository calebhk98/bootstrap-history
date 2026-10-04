"""The player's own notes: free text with the year, optionally attached to a project (Complaint 207).

Kept through `memory.remembered`, so they ride along with every save and load the UI makes."""
from sim.ui import memory

TOPIC = "notes"
MAX_TEXT = 500
MAX_NOTES = 1000
NOTE_PREFIX = "note: "


def _store(sim):
    store = memory.remembered(sim, TOPIC)
    store.setdefault("next", 1)
    store.setdefault("rows", [])
    return store


def clean_text(text):
    """The player's words, kept as typed apart from line breaks and the length bound."""
    return " ".join(str(text or "").splitlines()).strip()[:MAX_TEXT]


def add_note(sim, text, node_id=None):
    """Store one note; returns the row, or None when there is no text or the store is full."""
    text = clean_text(text)
    store = _store(sim)
    if not text or len(store["rows"]) >= MAX_NOTES:
        return None
    row = {"n": store["next"], "year": sim.year, "text": text, "project": node_id}
    store["next"] += 1
    store["rows"].append(row)
    return dict(row)


def drop_note(sim, number):
    rows = _store(sim)["rows"]
    for index, row in enumerate(rows):
        if row["n"] == number:
            return rows.pop(index)
    return None


def all_notes(sim):
    """Every note, oldest first."""
    return [dict(row) for row in _store(sim)["rows"]]


def note_log_rows(sim):
    """(year, text) rows in the shape of the household log, for merging into `log`."""
    return [(row["year"], NOTE_PREFIX + row["text"]) for row in _store(sim)["rows"]]


def notes_for(sim, node_id):
    """The notes attached to one project, oldest first, for `why`."""
    return [row for row in all_notes(sim) if row["project"] == node_id]
