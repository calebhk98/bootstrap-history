"""Regression coverage for complaints 192, 193, 206, 213, 217 and 232: finding things
and reading replies. Searches never reach beyond what a player may see.

The typed grammar and the search filters are called on plain inputs here; the replies of a fogged game are
test_command_search_and_text_scenario."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.ui.proto.typed import parse_typed
from sim.ui.proto import tree_filters as _tree_filters


def _typed(line):
    command, error = parse_typed(line)
    return command or {}, error


# ---- 217: one grammar for available arguments --------------------------------------
_command, _error = _typed("available metallurgy limit 80")
check("217: a subject followed by 'limit 80' keeps the subject and sets the limit",
      _command.get("subject") == "metallurgy" and _command.get("limit") == 80, _command)
_command, _error = _typed("available metallurgy limit:80")
check("217: 'limit:80' after a subject is the same",
      _command.get("subject") == "metallurgy" and _command.get("limit") == 80, _command)
_command, _error = _typed("available subject metallurgy offset 3")
check("217: 'subject X offset 3' keeps the subject and sets the offset",
      _command.get("subject") == "metallurgy" and _command.get("offset") == 3, _command)
_command, _error = _typed("available offset 30 subject metallurgy")
check("217: options before 'subject X' still work",
      _command.get("subject") == "metallurgy" and _command.get("offset") == 30, _command)
_command, _error = _typed("available power and precision limit 5 sort risk")
check("217: a several-word subject stops at the first option word",
      _command.get("subject") == "power and precision" and _command.get("limit") == 5
      and _command.get("sort") == "risk", _command)
_command, _error = _typed("available find iron smelting reverse")
check("217: 'find' takes every word up to the next option",
      _command.get("find") == "iron smelting" and _command.get("reverse") is True, _command)
_command, _error = _typed("available limit banana")
check("217: a limit that is not a number is refused, not swallowed",
      _error is not None and "limit" in _error, (_command, _error))

# ---- 197: the knowledge-file name is not a subject a search matches -----------------
_synthetic = {"a": {"name": "Signal flags", "cat": "comms", "kb": "50_electricity.md#flags",
                    "pre": []}}
check("197: find does not match a node by its knowledge-file name",
      not _tree_filters.matches_find(_synthetic, "electricity", "a"))
check("197: find still matches by name",
      _tree_filters.matches_find(_synthetic, "signal", "a"))
check("196: find matches by id words and a crude stem",
      _tree_filters.matches_find({"b": {"name": "Blast furnace", "cat": "metallurgy", "pre": []}}, "furnaces", "b")
      and _tree_filters.matches_find({"b": {"name": "Blast furnace", "cat": "metallurgy", "pre": []}}, "blast", "b"))
check("196: every query word must reach the node unless any_term is given",
      not _tree_filters.matches_find(_synthetic, "signal banana", "a")
      and _tree_filters.matches_find(_synthetic, "signal banana", "a", any_term=True))
check("196: an empty query matches nothing", not _tree_filters.matches_find(_synthetic, "   ", "a"))

# ---- 217: a tag is not a subject, and the refusal names both lists ---------------------
_tag, _category, _refusal = _tree_filters.parse_topic({"tag": "optics"}, _synthetic)
check("217: a tag that is not a tag is refused with the tags to choose from, and a pointer to the subject list",
      _refusal is not None and bool(_refusal.choices) and "optics" not in _refusal.choices,
      _refusal)
check("217: a tag that exists is accepted",
      _tree_filters.parse_topic({"tag": next(iter(_refusal.choices))}, _synthetic)[2] is None, _refusal.choices)
check("217: an unknown state is refused naming the states",
      _tree_filters.parse_state({"state": "banana"})[1].choices == list(_tree_filters.STATES)
      and _tree_filters.parse_state({"state": "completed"}) == ("done", None)
      and _tree_filters.parse_state({}) == (None, None))
