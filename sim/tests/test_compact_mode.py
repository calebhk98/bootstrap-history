"""The agent-oriented compact mode (the parser, the enrichers on synthetic replies, and the help text; no live game is read):
Complaints/reports/playthrough-review-han-china-100-to-400ad.md section 1.

A player of this game who is itself an AI agent asked for "an explicit
agent-oriented compact mode that can return highly structured state without
losing the human-readable explanations... I wouldn't rush to remove the
prose." This tests the two pieces that answer it, both confined to
sim/ui/proto/*.py:

  'json'    - a PRESENTATION switch, generalised from three commands
              (state/risk/portfolio) to every command a typed line can
              reach: adding the word 'json' anywhere on the line asks for
              the reply's own structured dict, unrendered, instead of the
              screen render.py would otherwise print. See typed.py's
              _split_json_flag and its own long comment for why this and
              'compact' are two different fields rather than one spelled
              two ways.
  'compact' - a SHORT SUMMARY of the reply on 'state', 'step', 'why' and
              'stuck' (see sim/ui/proto/compact.py): only the fields a
              turn needs, far smaller than 'json' and than the text screen.
              Implies 'json'. Complaints/169.

The compact agent output mode keeps reason-carrying prose; the mode-off path is byte-identical.
"""
QUICK_TOPIC = True

import json
import os
import subprocess
import sys
import types

from .harness import *  # noqa: F401,F403


# ===========================================================================
# PART 1: unit-level checks on the parser (typed.py) and the enricher
# (dispatch.py), directly - fast, and independent of whatever state the rest
# of the engine is in on any given day in this shared checkout.
# ===========================================================================

from sim.ui.proto.typed import parse_typed as _PT, _split_json_flag
from sim.ui.proto.dispatch import _add_compact_fields
from sim.ui.proto.compact import compact_why as _compact_why
from sim.ui.proto.compact import compact_state as _compact_state
from sim.ui.proto.compact import compact_stuck as _compact_stuck


# --- the three commands that already had their own hand-rolled 'json' scan
# must still parse exactly as they always have - this is the regression the
# task called out by name: "if you have to change an existing message, that
# is a red flag". These three are exact-equality checks.
check("'state json' still parses exactly as before",
      _PT("state json")[0] == {"cmd": "state", "full": False, "json": True},
      _PT("state json"))
check("'state full json' still parses exactly as before",
      _PT("state full json")[0] == {"cmd": "state", "full": True, "json": True},
      _PT("state full json"))
check("'portfolio json' still parses exactly as before",
      _PT("portfolio json")[0] == {"cmd": "portfolio", "json": True},
      _PT("portfolio json"))
check("'portfolio' (no word typed) still carries json:false, unchanged",
      _PT("portfolio")[0] == {"cmd": "portfolio", "json": False},
      _PT("portfolio"))
check("'risk json' still parses exactly as before",
      _PT("risk json")[0] == {"cmd": "risk", "json": True},
      _PT("risk json"))
check("'hazards json' (the alias) still parses exactly as before",
      _PT("hazards json")[0] == {"cmd": "risk", "json": True},
      _PT("hazards json"))
check("bare 'state' (nobody typed the word) carries no new field bloat",
      _PT("state")[0] == {"cmd": "state", "full": False, "json": False},
      _PT("state"))

# --- THE GENERALISATION: every other command now accepts the same word,
# where it previously either silently mis-parsed it (the exact bug
# _absorb_key_colons's own comment describes happening three times already:
# a bare word with no matching case falls through to "this is a search
# term") or dropped it on the floor.
_GENERALISED = [
    ("available json", {"cmd": "available", "json": True}),
    ("available", {"cmd": "available"}),   # untyped: no key added at all
    ("why fud_wheelbarrow json", {"cmd": "why", "id": "fud_wheelbarrow", "json": True}),
    ("stuck json", {"cmd": "stuck", "json": True}),
    ("log json", {"cmd": "log", "json": True}),
    ("capacity json", {"cmd": "capacity", "json": True}),
    ("mines json", {"cmd": "mines", "json": True}),
    ("labour json", {"cmd": "labour", "trade": None, "json": True}),
    ("money json", {"cmd": "money", "json": True}),
    ("economy json", {"cmd": "economy", "full": False, "json": True}),
    ("changes json", {"cmd": "changes", "years": 5, "json": True}),
    ("values json", {"cmd": "values", "json": True}),
    ("materials json", {"cmd": "materials", "json": True}),
    ("population json", {"cmd": "population", "json": True}),
    ("ventures json", {"cmd": "ventures", "json": True}),
    ("score json", {"cmd": "score", "json": True}),
]
for _line, _expected in _GENERALISED:
    _got, _err = _PT(_line)
    check("typed %r now sets json:true, generalised beyond state/risk/"
          "portfolio" % _line, _got == _expected, (_got, _err))

# --- THE BUG THIS WOULD OTHERWISE BE. Without stripping 'json' up front,
# 'available json' has no case that recognises the bare word, so it falls
# to "a bare word is a subject" and searches for a subject literally called
# "json" - the exact failure mode _absorb_key_colons's own docstring
# describes for 'all:true', 'limit:N' and 'reverse:true'. Pinned so nobody
# reintroduces it by moving the strip somewhere order-dependent.
check("'available json' is the json flag, NOT a subject search for the "
      "literal word \"json\"",
      "subject" not in _PT("available json")[0], _PT("available json"))

# --- 'compact' IMPLIES 'json' (so a reply asked for in compact form is
# actually shown raw, not rendered back into a table that does not know
# the new fields exist), and 'compact' is otherwise reserved for the three
# commands whose reply the enricher actually understands.
check("'why <id> compact' sets both json and compact",
      _PT("why fud_wheelbarrow compact")[0]
      == {"cmd": "why", "id": "fud_wheelbarrow", "json": True, "compact": True},
      _PT("why fud_wheelbarrow compact"))
check("'state compact' sets both json and compact, on top of state's own "
      "full:false default",
      _PT("state compact")[0]
      == {"cmd": "state", "full": False, "json": True, "compact": True},
      _PT("state compact"))
check("'stuck compact' sets both json and compact",
      _PT("stuck compact")[0] == {"cmd": "stuck", "json": True, "compact": True},
      _PT("stuck compact"))
check("'compact' on a command the enricher has no opinion about still sets "
      "the field (asking costs nothing; _add_compact_fields is a no-op "
      "for it) rather than being silently swallowed",
      _PT("money compact")[0] == {"cmd": "money", "json": True, "compact": True},
      _PT("money compact"))
check("typing 'json' ALONE never sets compact",
      "compact" not in _PT("why fud_wheelbarrow json")[0],
      _PT("why fud_wheelbarrow json"))

# --- _split_json_flag itself: the word is gone from the returned tokens
# either way, so no downstream parser (train's 'from', available's
# 'subject' tail-join, an id lookup) ever sees it as a stray word.
check("_split_json_flag strips 'json' and reports want_json",
      _split_json_flag(["furnace", "json"]) == (["furnace"], True, False),
      _split_json_flag(["furnace", "json"]))
check("_split_json_flag strips 'compact' and reports both flags "
      "(compact implies json)",
      _split_json_flag(["furnace", "compact"]) == (["furnace"], True, True),
      _split_json_flag(["furnace", "compact"]))
check("_split_json_flag leaves an ordinary line untouched",
      _split_json_flag(["furnace", "coal"]) == (["furnace", "coal"], False, False),
      _split_json_flag(["furnace", "coal"]))


# ===========================================================================
# PART 2: the enricher itself, on synthetic replies - so this is exercised
# whether or not the live engine currently runs end to end (six other
# agents are mid-edit on society.py/labour.py/economy.py/constants.py in
# this same checkout as this is written; see PART 3's own comment on why
# that cannot affect this file's verdict either way).
# ===========================================================================

# --- errors pass through completely untouched - a compact reply is never
# asked of something that failed, and forcing the enrichers to handle that
# case explicitly (rather than relying on duck-typing happening to work) is
# the whole reason each starts with the same ok-guard.
_ERR = {"ok": False, "error": "no such thing"}
check("_compact_why leaves an error reply alone",
      _compact_why(_ERR) == _ERR, _compact_why(_ERR))
check("_compact_state leaves an error reply alone",
      _compact_state(_ERR) == _ERR, _compact_state(_ERR))
check("_compact_stuck leaves an error reply alone",
      _compact_stuck(_ERR) == _ERR, _compact_stuck(_ERR))
check("_add_compact_fields is a no-op for a command the table does not cover",
      _add_compact_fields("money", {"ok": True, "capital": 5.0})
      == {"ok": True, "capital": 5.0},
      _add_compact_fields("money", {"ok": True, "capital": 5.0}))

# --- `why`, blocked: status/blocked/blocked_by/explanation only.
_why_blocked = {"ok": True, "id": "x", "name": "X", "done": False, "active": False,
                "can_start_now": False,
                "missing_prerequisites": ["units_standards", "patron_local"],
                "start_blocked_reason": "MISSING PREREQUISITES: units_standards, "
                                        "patron_local", "cost": 5, "detail": "long"}
_compact = _compact_why(_why_blocked)
check("compact_why gives status/blocked/blocked_by/explanation and drops the rest",
      (_compact["status"] == "blocked" and _compact["blocked"] is True
       and _compact["blocked_by"] == ["units_standards", "patron_local"]
       and _compact["explanation"] == _why_blocked["start_blocked_reason"]
       and "detail" not in _compact and "cost" not in _compact),
      _compact)
_compact_open = _compact_why({"ok": True, "id": "y", "name": "Y", "done": False,
                              "active": False, "can_start_now": True})
check("compact_why on a startable node: blocked False, blocked_by empty, "
      "no explanation manufactured",
      (_compact_open["status"] == "startable" and _compact_open["blocked"] is False
       and _compact_open["blocked_by"] == [] and "explanation" not in _compact_open),
      _compact_open)

# --- `state`: the short summary, from a synthetic full reply.
_fake_state = {
    "ok": True, "year": 120, "capital": 500.0, "net_per_year": -12.0,
    "founder_hours_available": 900.0, "concerns_you_run": 2,
    "you_know_how_to_run_but_have_not_opened": 3, "reputation": 5.0,
    "eminence": 0.1, "protection": 0.02, "scandal_now": 1.0, "scandal_danger": 25.0,
    "prominence": {"now": 0.3, "dangerous_above": 26.0, "note": "long prose"},
    "goal": "g", "goal_reached": False, "ended": False,
    "literacy": {"general": 0.1},
    "active": {
        "proj_a": {"name": "Project A", "why_underfunded": "short of smith-hours"},
        "proj_b": {"name": "Project B", "waiting_on": "your hours"},
        "proj_c": {"name": "Project C", "will_be_abandoned_in_years": 1},
        "proj_d": {"name": "Project D"},
    },
    "stuck": {"you_are_stuck": "you have been in arrears 9 years..."},
}
_compact_state_out = _compact_state(_fake_state)
_by_id = {row["id"]: row for row in _compact_state_out["projects"]}
# presentation: the one-line blocker is the compact mode's wording
check("compact_state lists every active project with its one-line blocker",
      sorted(_by_id) == ["proj_a", "proj_b", "proj_c", "proj_d"]
      and _by_id["proj_a"]["blocker"] == "short of smith-hours"
      and _by_id["proj_b"]["blocker"] == "your hours"
      and "abandoned" in _by_id["proj_c"]["blocker"]
      and _by_id["proj_d"]["blocker"] is None, _by_id)
check("compact_state carries the headline fields and no bulk fields",
      (_compact_state_out["year"] == 120 and _compact_state_out["money"] == 500.0
       and _compact_state_out["net_per_year"] == -12.0
       and _compact_state_out["founder_hours_free"] == 900.0
       and _compact_state_out["concerns"] == {"running": 2, "shut": 3}
       and _compact_state_out["standing"]["reputation"] == 5.0
       and _compact_state_out["danger"]["prominence"] == 0.3
       and _compact_state_out["danger"]["scandal"] == 1.0
       and _compact_state_out["stuck"].startswith("you have been in arrears")
       and "literacy" not in _compact_state_out), _compact_state_out)
check("compact_state does not mutate the reply it was given",
      "projects" not in _fake_state and "money" not in _fake_state)
check("compact_state adds no step keys to a plain state reply",
      "events" not in _compact_state_out and "completed" not in _compact_state_out)
_compact_step = _compact_state(dict(_fake_state, events=[{"year": 120, "message": "m"}],
                                    completed=[{"id": "t1", "name": "T"}], lost=[]))
check("compact on a step reply keeps what happened, in short form",
      (_compact_step["completed"] == ["t1"] and _compact_step["lost"] == []
       and _compact_step["events"] == [{"year": 120, "message": "m"}]), _compact_step)

# --- `stuck`: one entry per reason, per-project reasons as {id, explanation}.
_fake_stuck = {
    "ok": True, "you_could_begin": 4, "and_could_pay_for": 2,
    "and_the_cheapest_thing_you_could_start_now": "cheap",
    "what_is_holding_you_up": [
        {"what": "work in hand", "how_many": 2,
         "each_waiting_on": {"proj_a": "your hours", "proj_b": "smith-hours"}},
        {"what": "money", "why": "3 things are startable and the cheapest "
                                 "costs more than you can raise"},
    ],
}
_blockers = _compact_stuck(_fake_stuck)["blockers"]
check("compact_stuck produces one entry per reason, in order",
      [blocker["reason"] for blocker in _blockers] == ["work in hand", "money"], _blockers)
check("compact_stuck flattens each_waiting_on into {id, explanation}",
      _blockers[0]["projects"] == [{"id": "proj_a", "explanation": "your hours"},
                                   {"id": "proj_b", "explanation": "smith-hours"}],
      _blockers[0]["projects"])
check("compact_stuck carries a plain 'why' sentence through",
      _blockers[1]["explanation"].startswith("3 things are startable"))
check("compact_stuck keeps the counts and the cheapest start",
      _compact_stuck(_fake_stuck)["could_begin"] == 4
      and _compact_stuck(_fake_stuck)["cheapest_start"] == "cheap")


from sim.ui.proto import help as _help_module


# --- THE DOCUMENTATION CHANGE ITSELF, checked directly (rather than left
# implicit by its absence from the byte-identical set above): the new
# feature has to actually be discoverable from inside the game, or a
# player typing 'help commands' - the one place this game's own help
# system tells a newcomer to look - would never learn either word exists.
_help_commands = _help_module._topic_commands(types.SimpleNamespace(fog=False))["commands"]
check("'help commands' documents the new json/compact words, so a player "
      "typing 'help' can actually discover them",
      any("compact" in key or "json" in key for key in _help_commands),
      sorted(_help_commands.keys()))
