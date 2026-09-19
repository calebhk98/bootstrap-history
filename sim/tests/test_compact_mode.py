"""The agent-oriented compact mode: Complaints/35 section 1.

A player of this game who is itself an AI agent asked for "an explicit
agent-oriented compact mode that can return highly structured state without
losing the human-readable explanations... I wouldn't rush to remove the
prose." This tests the two pieces that answer it, both confined to
sim/engine/proto/*.py:

  'json'    - a PRESENTATION switch, generalised from three commands
              (state/risk/portfolio) to every command a typed line can
              reach: adding the word 'json' anywhere on the line asks for
              the reply's own structured dict, unrendered, instead of the
              screen render.py would otherwise print. See typed.py's
              _split_json_flag and its own long comment for why this and
              'compact' are two different fields rather than one spelled
              two ways.
  'compact' - a CONTENT switch, new: on 'why', 'state' (and 'step', which
              is a state reply plus what happened) and 'stuck' - the three
              commands whose whole job is explaining why something is
              blocked - it folds their existing reasoning fields into one
              small, identically-shaped extra set of keys
              ("blocked"/"blocked_by"/"explanation" on `why`,
              "blocked_projects" on `state`, "blockers" on `stuck`), on
              top of every field the plain reply already had. Nothing is
              removed. See dispatch.py's _add_compact_fields.

THE SAFETY PROPERTY THE TASK NAMED - mode off, byte-identical - is proven
below by running the real `agent` protocol twice: once against this
checkout as it stands, and once against a mirror of it with ONLY the three
files this work touched (typed.py, dispatch.py, help.py) reverted to their
content at e98e461, everything else - including whatever six other agents
are concurrently doing to society.py, labour.py, economy.py, constants.py
and cli.py in this same shared checkout - held identical between the two
runs by construction (a symlink to the one real copy on disk, not a second
copy of it). If those two runs disagree on any command that never asked for
'json' or 'compact', the disagreement can only be something this work did,
because nothing else differs between them. The mirror is built with
symlinks precisely so this test never writes into the shared checkout: the
only bytes it ever creates are the (up to) three reverted files, in a
tempfile.mkdtemp() outside the repository entirely.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from .harness import *  # noqa: F401,F403


# ===========================================================================
# PART 1: unit-level checks on the parser (typed.py) and the enricher
# (dispatch.py), directly - fast, and independent of whatever state the rest
# of the engine is in on any given day in this shared checkout.
# ===========================================================================

from sim.engine.proto.typed import parse_typed as _PT, _split_json_flag
from sim.engine.proto.dispatch import (_add_compact_fields, _compact_why,
                                   _compact_state, _compact_stuck)


# --- the three commands that already had their own hand-rolled 'json' scan
# must still parse exactly as they always have - this is the regression the
# task called out by name: "if you have to change an existing message, that
# is a red flag". These three exact-equality checks are the ones
# test_scanners_and_scheduling.py already made; repeated here because this
# file is what a reviewer of THIS change should be able to read start to
# finish without cross-referencing another topic module.
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

# --- `why`, blocked: the illustrative shape the task asked for by name -
# {"blocked_by": ..., "explanation": ...} - built from fields the plain
# reply already carries (missing_prerequisites, start_blocked_reason),
# never invented.
_why_blocked = {"ok": True, "id": "x", "name": "X", "done": False, "active": False,
                "can_start_now": False,
                "missing_prerequisites": ["units_standards", "patron_local"],
                "start_blocked_reason": "MISSING PREREQUISITES: units_standards, "
                                        "patron_local"}
_compact = _compact_why(_why_blocked)
check("_compact_why adds status/blocked/blocked_by/explanation and keeps "
      "every original field",
      (_compact["status"] == "blocked" and _compact["blocked"] is True
       and _compact["blocked_by"] == ["units_standards", "patron_local"]
       and _compact["explanation"] == _why_blocked["start_blocked_reason"]
       and all(_compact[key] == value for key, value in _why_blocked.items())),
      _compact)

# --- `why`, startable: blocked is false and blocked_by is empty, not
# omitted - a script checking `resp["blocked"]` should never have to also
# check whether the key exists.
_why_open = {"ok": True, "id": "y", "name": "Y", "done": False, "active": False,
            "can_start_now": True}
_compact_open = _compact_why(_why_open)
check("_compact_why on a startable node: blocked False, blocked_by empty, "
      "no explanation manufactured out of nothing",
      (_compact_open["status"] == "startable" and _compact_open["blocked"] is False
       and _compact_open["blocked_by"] == [] and "explanation" not in _compact_open),
      _compact_open)

# --- `state`/`step`: every reason already on the per-project dict
# (why_underfunded, waiting_on, the abandonment countdown) lands in one
# flat, iterable list; a project with nothing wrong is not listed at all.
_fake_state = {
    "ok": True, "year": 120,
    "active": {
        "proj_a": {"name": "Project A", "why_underfunded": "short of smith-hours"},
        "proj_b": {"name": "Project B", "waiting_on": "your hours"},
        "proj_c": {"name": "Project C", "will_be_abandoned_in_years": 1,
                   "because_nobody_here_can": ["smith"]},
        "proj_d": {"name": "Project D"},
    },
    "stuck": {"you_are_stuck": "you have been in arrears 9 years..."},
}
_compact_state_out = _compact_state(_fake_state)
_ids_listed = sorted(row["id"] for row in _compact_state_out["blocked_projects"])
check("_compact_state lists every project with a reason, and only those",
      _ids_listed == ["proj_a", "proj_b", "proj_c"], _ids_listed)
check("_compact_state's per-project explanation is the field the plain "
      "reply already had, not a rewritten one",
      next(row["explanation"] for row in _compact_state_out["blocked_projects"]
           if row["id"] == "proj_a") == "short of smith-hours")
check("_compact_state folds the abandonment countdown into the "
      "explanation when that is the only reason on record",
      "abandoned" in next(row["explanation"]
                          for row in _compact_state_out["blocked_projects"]
                          if row["id"] == "proj_c"))
check("_compact_state surfaces stall_diagnosis's headline as a top-level "
      "'explanation' too, since that is the one sentence a stuck run's "
      "own state reply already leads with",
      _compact_state_out["explanation"] == _fake_state["stuck"]["you_are_stuck"])
check("_compact_state changes nothing on the original dict (no in-place "
      "mutation of the reply the plain path would have returned)",
      "blocked_projects" not in _fake_state and "explanation" not in _fake_state)
check("_compact_state on a reply with nothing active adds no empty key",
      "blocked_projects" not in _compact_state({"ok": True, "active": {}}),
      _compact_state({"ok": True, "active": {}}))

# --- `stuck`: the two id-keyed sub-dicts (each_waiting_on,
# each_why_underfunded) become one list of {id, explanation}, the same
# shape `why` and `state` use above, with the underfunded reason folded in
# as an extra field on the matching row rather than a second parallel list
# a reader has to zip by hand.
_fake_stuck = {
    "ok": True,
    "what_is_holding_you_up": [
        {"what": "work in hand", "how_many": 2,
         "each_waiting_on": {"proj_a": "your hours", "proj_b": "smith-hours"},
         "each_why_underfunded": {"proj_b": "arrears ate the cash for it"}},
        {"what": "money", "why": "3 things are startable and the cheapest "
                                 "costs more than you can raise"},
    ],
}
_compact_stuck_out = _compact_stuck(_fake_stuck)
_blockers = _compact_stuck_out["blockers"]
check("_compact_stuck produces one entry per reason, in order",
      [blocker["reason"] for blocker in _blockers] == ["work in hand", "money"], _blockers)
check("_compact_stuck flattens each_waiting_on into a list of {id, explanation}",
      sorted((project["id"], project["explanation"]) for project in _blockers[0]["projects"])
      == [("proj_a", "your hours"), ("proj_b", "smith-hours")],
      _blockers[0]["projects"])
check("_compact_stuck folds each_why_underfunded onto the matching project "
      "row instead of leaving it a second dict to cross-reference by hand",
      next(project["also_why_underfunded"] for project in _blockers[0]["projects"]
           if project["id"] == "proj_b") == "arrears ate the cash for it")
check("_compact_stuck carries the plain 'why' sentence through for a "
      "reason that never had a per-project breakdown",
      _blockers[1]["explanation"]
      == "3 things are startable and the cheapest costs more than you can raise")


# ===========================================================================
# PART 3: end-to-end, through the real dispatcher, on a live Sim - the
# commands that do not depend on whatever the other six agents are
# mid-editing in society.py right now (that risk is real and is exactly
# why PART 2 above tests the enrichers on synthetic data too: this part is
# the live-integration check, not the only check).
# ===========================================================================

_ptest_sim = sim()
_ptest_blocked = next(node_id for node_id in ORDER
                      if node_id not in _ptest_sim.done and not _ptest_sim.can_start(node_id))
_ptest_why_plain = S._agent_dispatch(_ptest_sim, NODES, {"cmd": "why", "id": _ptest_blocked})
_ptest_why_compact = S._agent_dispatch(
    _ptest_sim, NODES, {"cmd": "why", "id": _ptest_blocked, "compact": True})
check("live `why` on an actually-blocked node: compact mode is a strict "
      "superset of the plain reply",
      all(_ptest_why_compact.get(key) == value for key, value in _ptest_why_plain.items()),
      (_ptest_why_plain, _ptest_why_compact))
check("live `why` compact reply says blocked:true and names what it is "
      "blocked by, for a node this fresh game cannot start yet",
      _ptest_why_compact.get("blocked") is True and _ptest_why_compact.get("blocked_by"),
      _ptest_why_compact)
check("live `why` compact reply is JSON-serialisable (this is what an "
      "agent would actually receive over the wire)",
      bool(json.dumps(_ptest_why_compact)))

_ptest_stuck_plain = S._agent_dispatch(_ptest_sim, NODES, {"cmd": "stuck"})
_ptest_stuck_compact = S._agent_dispatch(_ptest_sim, NODES, {"cmd": "stuck", "compact": True})
check("live `stuck`: compact mode is a strict superset of the plain reply",
      all(_ptest_stuck_compact.get(key) == value for key, value in _ptest_stuck_plain.items()),
      (_ptest_stuck_plain, _ptest_stuck_compact))
check("live `stuck` compact reply carries a 'blockers' list matching the "
      "number of reasons the plain reply gave",
      (isinstance(_ptest_stuck_compact.get("what_is_holding_you_up"), list)
       and len(_ptest_stuck_compact["blockers"])
       == len(_ptest_stuck_compact["what_is_holding_you_up"])),
      _ptest_stuck_compact)

# --- `available` never claimed an enricher (see this file's own module
# docstring on which commands were deliberately left out): compact mode on
# it is a pure no-op beyond json presentation, and that is asserted here so
# a future change to _COMPACT_ENRICHERS does not silently start rewriting a
# reply this task's own report says was left alone on purpose.
# TWO FRESH SIMS, not one sim asked twice. _agent_available carries one
# real piece of state across calls on the SAME Sim - "MOST RESTS ON THESE"
# (s._said_stack_caution) is only ever said once per Sim, deliberately, so
# it does not bury itself in noise on the tenth 'available' of a session -
# and re-using _ptest_sim for both halves of this comparison would make the
# second call's reply differ from the first's for a reason that has
# nothing to do with compact mode at all.
_ptest_avail_plain = S._agent_dispatch(sim(), NODES, {"cmd": "available"})
_ptest_avail_compact = S._agent_dispatch(sim(), NODES, {"cmd": "available", "compact": True})
check("`available` is unaffected by compact mode - not one of the three "
      "commands the enricher covers, by deliberate choice (see module "
      "docstring)",
      _ptest_avail_plain == _ptest_avail_compact, (_ptest_avail_plain, _ptest_avail_compact))

# --- the typed path all the way through: a person (or agent) typing plain
# words at `play`'s prompt reaches the same enriched reply a hand-written
# JSON command would, because parse_typed's output is handed to the exact
# same _agent_dispatch every other front door calls.
_typed_cmd, _typed_err = _PT("why %s compact" % _ptest_blocked)
check("typed 'why <id> compact' parses with no error", _typed_err is None, _typed_err)
_typed_resp = S._agent_dispatch(sim(), NODES, _typed_cmd)
check("typed 'why <id> compact', run through the real dispatcher end to "
      "end, carries the same blocked_by the hand-written JSON command did",
      _typed_resp.get("blocked_by") == _ptest_why_compact.get("blocked_by"),
      _typed_resp)


# ===========================================================================
# PART 4: dispatch.py applies compact mode LAST, after both localisation
# passes - a structural check (source order), not a behavioural sample, so
# it holds regardless of which civilisation a future check happens to run
# against. See _agent_dispatch's own comment for why the ordering matters:
# anything a compact field copies out of the reply (a sentence, a list of
# ids) must already carry the civilisation's own money word, or compact
# mode would show an agent one civilisation's numbers dressed in another's
# vocabulary.
# ===========================================================================
import inspect
from sim.engine.proto import dispatch as _dispatch_mod

_dispatch_src = inspect.getsource(_dispatch_mod._agent_dispatch)
_i_money = _dispatch_src.index("_localise_money")
_i_words = _dispatch_src.index("_localise_words")
_i_compact = _dispatch_src.index("_add_compact_fields")
check("_agent_dispatch applies compact enrichment after BOTH localisation "
      "passes, not before either of them",
      _i_money < _i_compact and _i_words < _i_compact,
      (_i_money, _i_words, _i_compact))


# ===========================================================================
# PART 5: THE BYTE-IDENTICAL PROOF. Mode off (no 'json', no 'compact'
# anywhere in the command) must be indistinguishable from this checkout's
# state at e98e461, for the three files this work touched - proven by
# actually running the real `agent` protocol against a mirror with those
# three files reverted, and diffing stdout byte for byte against the same
# commands run against this checkout as it stands. See this module's own
# docstring for why a symlink mirror rather than a second full copy, and
# why that also makes the result immune to whatever the other six agents
# sharing this checkout are doing to the files this work does NOT touch.
# ===========================================================================

_TOUCHED_FILES = (
    "sim/engine/proto/typed.py",
    "sim/engine/proto/dispatch.py",
    "sim/engine/proto/help.py",
)
_BASELINE_REF = "e98e461"
_SKIP_MIRROR_NAMES = {".git", "__pycache__", "_loadtest_tmp", "_playtest_tmp"}


def _git_show(ref, relpath):
    completed = subprocess.run(["git", "show", "%s:%s" % (ref, relpath)],
                               cwd=ROOT, capture_output=True, text=True)
    if completed.returncode != 0:
        return None
    return completed.stdout


def _mirror_with_overrides(src_dir, dst_dir, overrides):
    """Recreate src_dir at dst_dir: wherever a path leads to (or through) one
    of `overrides` (a dict of {path-relative-to-ROOT: replacement text}) a
    real directory or file is created; everywhere else, ONE symlink back
    into the actual checkout stands in for a whole file or a whole
    subtree. So the only bytes this test ever writes anywhere are the
    override files themselves, and the mirror sees every live edit any
    other agent makes to a file it did NOT override, for free, because it
    is not a copy of that file - it is a link to it.
    """
    os.makedirs(dst_dir, exist_ok=True)
    for name in sorted(os.listdir(src_dir)):
        if name in _SKIP_MIRROR_NAMES:
            continue
        src = os.path.join(src_dir, name)
        rel = os.path.relpath(src, ROOT)
        dst = os.path.join(dst_dir, name)
        touches = any(rel == override or rel.startswith(override + os.sep) or override.startswith(rel + os.sep)
                     for override in overrides)
        if not touches:
            try:
                os.symlink(src, dst)
            except (OSError, AttributeError):
                if os.path.isdir(src):
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*_SKIP_MIRROR_NAMES))
                else:
                    shutil.copy2(src, dst)
        elif os.path.isdir(src):
            _mirror_with_overrides(src, dst, overrides)
        else:
            with open(dst, "w", encoding="utf-8") as file:
                file.write(overrides[rel])


def _run_agent(tree_root, lines, civ="rome_100ad", seed=1):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"       # never write .pyc anywhere
    completed = subprocess.run(
        [sys.executable, os.path.join(tree_root, "sim", "simulator.py"), "agent",
         "--civ", civ, "--seed", str(seed), "--deterministic"],
        input="\n".join(json.dumps(line) for line in lines) + "\n",
        capture_output=True, text=True, timeout=300, cwd=tree_root, env=env)
    return completed.stdout, completed.stderr, completed.returncode


# A REPRESENTATIVE SET: every command the reviewer named by name (state,
# available, why), and the other high-traffic read commands 'compact' now
# also reaches (stuck, log, capacity, mines, labour, money, population,
# materials, economy, changes, portfolio, ventures, score, values, risk).
# Deliberately NONE of them pass 'json' or 'compact' - this is the mode-OFF
# path, and the whole point is that it must not have moved. `step`/mutating
# commands are left out only because a mismatch there could come from the
# OTHER six agents' own in-flight changes to core.py/labour.py/society.py/
# economy.py landing mid-suite, which is a real risk on this shared
# checkout and not one this file exists to catch - see the module
# docstring on why the two runs nonetheless see identical (if currently
# broken) behaviour from those files either way, since neither run
# touches them.
#
# `help` IS DELIBERATELY EXCLUDED FROM THIS SET. help.py's "commands" topic
# now documents 'json'/'compact' (see the check just below this block) and
# that is a real, intended change to what {"cmd":"help"} returns, on every
# call, flag or no flag - the byte-identical guarantee this proof exists
# for is about REPLIES TO THE MODE BEING OFF, i.e. that asking for
# something unrelated to compact mode still gets exactly what it always
# got; it was never a promise that documentation of a new feature would
# not mention the feature.
_REPRESENTATIVE_LINES = [
    {"cmd": "state"},
    {"cmd": "available"},
    {"cmd": "available", "subject": "metallurgy"},
    {"cmd": "available", "find": "furnace"},
    {"cmd": "why", "id": _ptest_blocked},
    {"cmd": "stuck"},
    {"cmd": "log"},
    {"cmd": "money"},
    {"cmd": "values"},
    {"cmd": "materials"},
    {"cmd": "risk"},
    {"cmd": "labour"},
    {"cmd": "population"},
    {"cmd": "capacity"},
    {"cmd": "mines"},
    {"cmd": "economy"},
    {"cmd": "changes"},
    {"cmd": "portfolio"},
    {"cmd": "ventures"},
    {"cmd": "score"},
]

# --- THE DOCUMENTATION CHANGE ITSELF, checked directly (rather than left
# implicit by its absence from the byte-identical set above): the new
# feature has to actually be discoverable from inside the game, or a
# player typing 'help commands' - the one place this game's own help
# system tells a newcomer to look - would never learn either word exists.
_help_commands = S._agent_help(sim(), "commands")["commands"]
check("'help commands' documents the new json/compact words, so a player "
      "typing 'help' can actually discover them",
      any("compact" in key or "json" in key for key in _help_commands),
      sorted(_help_commands.keys()))

_baseline_dir = None
try:
    _overrides = {}
    _missing_ref = False
    for _relpath in _TOUCHED_FILES:
        _text = _git_show(_BASELINE_REF, _relpath)
        if _text is None:
            _missing_ref = True
            break
        _overrides[_relpath] = _text
    if _missing_ref:
        check("byte-identical proof: could read %s's own copy of every "
              "touched file from git" % _BASELINE_REF, False,
              "git show %s:<path> failed - is this checkout shallow?"
              % _BASELINE_REF)
    else:
        _baseline_dir = tempfile.mkdtemp(prefix="compact_mode_baseline_")
        _mirror_with_overrides(ROOT, _baseline_dir, _overrides)
        _cur_out, _cur_err, _cur_rc = _run_agent(ROOT, _REPRESENTATIVE_LINES)
        _base_out, _base_err, _base_rc = _run_agent(_baseline_dir, _REPRESENTATIVE_LINES)
        if _cur_out == _base_out:
            _diff_detail = ""
        else:
            _diff_at = next((i for i in range(min(len(_cur_out), len(_base_out)))
                            if _cur_out[i] != _base_out[i]),
                           min(len(_cur_out), len(_base_out)))
            _lo, _hi = max(0, _diff_at - 120), _diff_at + 120
            _diff_detail = ("first differing byte at %d (of %d/%d)\n  current : %r"
                           "\n  baseline: %r"
                           % (_diff_at, len(_cur_out), len(_base_out),
                              _cur_out[_lo:_hi], _base_out[_lo:_hi]))
        check("byte-identical proof: mode-OFF stdout is identical between "
              "this checkout and %s for every representative command "
              "(the only difference between the two runs is the three "
              "files this task touched)" % _BASELINE_REF,
              _cur_out == _base_out, _diff_detail)
        check("byte-identical proof: same return code both sides",
              _cur_rc == _base_rc, (_cur_rc, _base_rc))
finally:
    if _baseline_dir:
        shutil.rmtree(_baseline_dir, ignore_errors=True)
