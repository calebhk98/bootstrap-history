"""ui_notes: the note and notes commands (Complaint 207). Complaint 640: the rules are called on a stand-in game that holds
the real tree and an interface slot; the save and load of notes in a played game is in test_ui_notes_scenario."""
QUICK_TOPIC = True

import types
import unittest

from .harness import NODES
from sim.ui.proto.dispatch_notes import _cmd_note, _cmd_notes
from sim.ui.proto.notes_store import MAX_TEXT, note_log_rows, notes_for
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.typed import parse_typed

VISIBLE = next(node_id for node_id in sorted(NODES) if NODES[node_id].get("name"))
VISIBLE_NAME = NODES[VISIBLE]["name"]


def _game(fog=False, visible=()):
    game = types.SimpleNamespace(nodes=NODES, year=1301, fog=fog, state=types.SimpleNamespace(interface={}))
    game.is_visible = lambda node_id, **_options: node_id in visible
    return game


def _note(game, **fields):
    return _cmd_note(game, NODES, dict(cmd="note", **fields), None)


def _notes(game, **fields):
    return _cmd_notes(game, NODES, dict(cmd="notes", **fields), None)


class WritingTests(unittest.TestCase):

    def test_a_bare_note_is_stored_with_the_year(self):
        game = _game()
        self.assertEqual(_note(game, text="  keep   spacing  ")["added"]["year"], game.year)

    def test_note_text_is_kept_verbatim_apart_from_the_edges(self):
        game = _game()
        _note(game, text="  keep   spacing  ")
        self.assertEqual(_notes(game)["entries"][0]["text"], "keep   spacing")

    def test_a_long_note_is_cut_to_the_bound_and_the_reply_carries_a_cut_field(self):
        game = _game()
        reply = _note(game, text="x" * (MAX_TEXT + 5))
        self.assertIn("cut", reply)
        self.assertEqual(len(reply["added"]["text"]), MAX_TEXT)

    def test_an_empty_note_is_refused(self):
        self.assertFalse(_note(_game(), text="  ")["ok"])


class ProjectAttachmentTests(unittest.TestCase):

    def test_a_leading_project_id_attaches_the_note_and_leaves_the_rest_as_its_text(self):
        added = _note(_game(), text="%s because grain is short" % VISIBLE)["added"]
        self.assertEqual((added["project"], added["text"]), (VISIBLE, "because grain is short"))

    def test_a_leading_project_name_attaches_too(self):
        self.assertEqual(_note(_game(), text="%s second thought" % VISIBLE_NAME)["added"]["project"], VISIBLE)

    def test_two_dashes_keep_a_leading_project_name_as_plain_text(self):
        self.assertIsNone(_note(_game(), text="-- %s is just words" % VISIBLE)["added"]["project"])

    def test_notes_for_returns_the_projects_notes_oldest_first(self):
        game = _game()
        _note(game, text="%s because grain is short" % VISIBLE)
        _note(game, text="%s second thought" % VISIBLE_NAME)
        self.assertEqual([row["text"] for row in notes_for(game, VISIBLE)], ["because grain is short", "second thought"])

    def test_notes_filters_by_project_and_lists_newest_first(self):
        game = _game()
        _note(game, text="unattached")
        _note(game, text="%s because grain is short" % VISIBLE)
        _note(game, text="%s second thought" % VISIBLE_NAME)
        self.assertEqual([row["text"] for row in _notes(game, project=VISIBLE)["entries"]],
                         ["second thought", "because grain is short"])

    def test_the_log_rows_have_the_household_logs_year_and_text_shape(self):
        game = _game()
        _note(game, text="one")
        rows = note_log_rows(game)
        self.assertTrue(rows and all(isinstance(year, int) and isinstance(text, str) for year, text in rows))


class PagingAndDroppingTests(unittest.TestCase):

    def test_a_page_is_bounded_and_carries_the_next_offset(self):
        game = _game()
        for number in range(5):
            _note(game, text="note %d" % number)
        page = _notes(game, limit=2)
        self.assertEqual(len(page["entries"]), 2)
        self.assertIn("more", page)
        self.assertEqual(len(_notes(game, limit=2, offset=2)["entries"]), 2)
        self.assertNotIn("more", _notes(game, limit=2, offset=4))

    def test_drop_removes_one_note_by_its_number(self):
        game = _game()
        for number in range(3):
            _note(game, text="note %d" % number)
        first = _notes(game)["entries"][0]["n"]
        self.assertEqual(_note(game, text="drop %d" % first)["dropped"]["n"], first)
        self.assertTrue(all(row["n"] != first for row in _notes(game, limit=100)["entries"]))

    def test_dropping_a_missing_note_is_refused(self):
        self.assertFalse(_note(_game(), text="drop 9999")["ok"])

    def test_no_notes_gives_a_hint_field(self):
        self.assertIn("hint", _notes(_game()))


class FogTests(unittest.TestCase):
    """An unseen project cannot be named, and the refusal does not name it."""

    def test_a_fogged_project_cannot_be_attached_and_the_refusal_does_not_name_it(self):
        game = _game(fog=True, visible=())
        refusal = _note(game, project=VISIBLE, text="spy")
        self.assertFalse(refusal["ok"])
        self.assertNotIn(VISIBLE_NAME, refusal["error"])

    def test_a_fogged_id_typed_first_is_plain_text(self):
        game = _game(fog=True, visible=())
        self.assertIsNone(_note(game, text="%s x" % VISIBLE)["added"]["project"])

    def test_a_project_in_view_is_attached_under_fog(self):
        game = _game(fog=True, visible=(VISIBLE,))
        self.assertEqual(_note(game, text="%s x" % VISIBLE)["added"]["project"], VISIBLE)

    def test_a_note_on_a_project_that_fog_later_hides_lists_without_the_project(self):
        game = _game(fog=False)
        _note(game, text="%s kept" % VISIBLE)
        game.fog = True
        entry = _notes(game)["entries"][0]
        self.assertEqual((entry["project"], entry["project_name"]), (None, None))


class TypedAndScreenTests(unittest.TestCase):

    def test_typed_note_keeps_its_words(self):
        self.assertEqual(parse_typed("note Build the mill, then 2 looms")[0],
                         {"cmd": "note", "text": "Build the mill, then 2 looms"})

    def test_typed_notes_takes_paging(self):
        self.assertEqual(parse_typed("notes limit:5 offset:5")[0], {"cmd": "notes", "limit": 5, "offset": 5})

    def test_a_note_line_shows_number_year_text_and_project(self):
        entry = {"n": 3, "year": 1301, "text": "mill before the loom", "project": "x", "project_name": "Water mill"}
        listing = render_pretty("notes", {"ok": True, "count": 1, "entries": [entry]})
        # presentation: a note line reads "#n", the year, the text and "[project name]"
        for word in ("#3", "1301", "mill before the loom", "[Water mill]"):
            self.assertIn(word, listing)

    def test_an_empty_list_says_how_to_start(self):
        text = render_pretty("notes", {"ok": True, "count": 0, "entries": [], "hint": "none yet; 'note <text>' writes one"})
        self.assertIn("note <text>", text)   # presentation: the hint's wording

    def test_a_drop_is_confirmed(self):
        entry = {"n": 3, "year": 1301, "text": "x", "project": None, "project_name": None}
        self.assertIn("dropped note #3", render_pretty("note", {"ok": True, "dropped": entry}))   # presentation: confirmation wording


if __name__ == "__main__":
    unittest.main()
