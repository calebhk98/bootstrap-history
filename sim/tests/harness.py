"""Shared fixtures, imports and check-recording machinery for the split
test suite (see sim/tests/__main__.py for the runner).

This is test_regressions.py's own former preamble (import block, TREE/NODES/
ORDER/GOAL, check()/slow_check()/proto()sim()/run_it()/_par_map(), the
subprocess-timing patch and the --jobs parsing), moved here VERBATIM so every
topic module in this package can do `from .harness import *` and see exactly
what the old flat script saw at the top of the file. Every topic module is
still just top-level code that calls check()/slow_check() at import time,
in file order - splitting into files changes nothing about how a check runs,
only how the source is organised on disk.

A few names below (_mk_loom_sim, _hazard, _rel/_LOADTEST_DIR, and the whole
family of `from engine.protocol import X as _Y` mid-file imports) are not
part of the ORIGINAL top-of-file preamble - they are helpers the original
flat file defined once, inline, at their first point of use, and then called
again many hundreds (sometimes thousands) of lines later, in what is now a
DIFFERENT topic module. Since Python executed the whole file as one module,
that just worked; split into separate modules it would not, so those few
reusable, side-effect-free pieces (pure functions, pure imports, or a plain
string constant + an idempotent os.makedirs) are ALSO defined here once and
re-exported, while the topic module that originally introduced them keeps
its own verbatim copy too (harmless - it simply shadows the harness-provided
name with an identical one within that module's own namespace, exactly
reproducing the original file's behaviour there).
"""
import atexit, collections, copy, glob, json, os, random, re, shutil, subprocess, sys, time
import concurrent.futures as _concurrent_futures
import threading
import tempfile

# HERE is this repository's sim/ directory; ROOT is the repository itself.
#
# ROOT USED TO BE THE REPOSITORY'S PARENT, and the suite only ran at all if
# that parent happened to contain a directory literally named `rome`. Two
# things came of that, both bad. Every scratch file the suite writes
# (_loadtest_tmp, _playtest_tmp, and every subprocess run with cwd=ROOT)
# landed OUTSIDE the checkout, in whatever directory the checkout happened to
# sit in. And a check that globbed os.path.join(ROOT, "data", ...) - the
# natural spelling, and the one build_index.py already used - silently matched
# nothing, so ten assertions about the civilization files' event coverage ran
# zero times for as long as they existed without anyone noticing, because a
# for-loop over an empty glob does not fail, it just says nothing.
#
# ROOT is now the repository, so `os.path.join(ROOT, "data", ...)` means what
# it reads as, scratch files stay inside the checkout where .gitignore can see
# them, and nothing anywhere depends on what the checkout is called.
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import simulator as S
import planner as PLANNER
from engine import commodities as COMMOD

TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_LAB, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
FAILURES = []
# Counted rather than hand-maintained: the tally in the summary line was a
# literal that three separate rounds of additions had to remember to update.
CHECKS_RUN = []
SKIPPED = []
_LAST_AT = time.time()

# --- Where does the wall time actually go: waiting on a child process, or
# doing our own work in this one? Every subprocess call in this file - the
# ~150 through proto()/_run_agent()/_play()/_agent_session() and the ~30
# direct subprocess.run() calls - goes through subprocess.run, so patching
# the module function once here tallies all of them without touching any
# call site. Set ROME_TEST_PROFILE=<path> to also dump the full per-check
# timing table (not just the top 5 the normal summary prints) as JSON, for
# deciding what is actually worth optimising rather than guessing.
_SUBPROC_TIME = [0.0]
_SUBPROC_CALLS = [0]
_SUBPROC_LOCK = threading.Lock()
_real_subprocess_run = subprocess.run


def _timed_subprocess_run(*a, **kw):
    start_time = time.time()
    try:
        return _real_subprocess_run(*a, **kw)
    finally:
        elapsed_seconds = time.time() - start_time
        with _SUBPROC_LOCK:
            _SUBPROC_TIME[0] += elapsed_seconds
            _SUBPROC_CALLS[0] += 1


subprocess.run = _timed_subprocess_run
_PROFILE_OUT = os.environ.get("ROME_TEST_PROFILE")

# --- --jobs N: how many of the independent subprocess calls identified below
# (each a fresh `proto()`/subprocess.run() with no shared session file, and
# every one of them already independent of the others - that is what "fresh
# session" means) may run at once. This does NOT reorder anything a human or
# a diff would see: _par_map always returns results in the same order the
# inputs were given, in the same order check() is then called on them, so
# `--jobs 1` (the default) and `--jobs 4` print byte-identical output and
# differ only in wall time. Real parallelism, not merely concurrency: each
# unit of work is a CHILD PROCESS, so N of them genuinely run on N cores at
# once - the GIL never enters into it, because the only thing this process's
# own threads do is sit in os.waitpid.
JOBS = 1
for _jobs_argi, _jobs_arg in enumerate(sys.argv):
    if _jobs_arg == "--jobs" and _jobs_argi + 1 < len(sys.argv):
        try:
            JOBS = max(1, int(sys.argv[_jobs_argi + 1]))
        except ValueError:
            pass
    elif _jobs_arg.startswith("--jobs="):
        try:
            JOBS = max(1, int(_jobs_arg.split("=", 1)[1]))
        except ValueError:
            pass
del _jobs_argi, _jobs_arg


def _par_map(fn, items):
    """Run fn(item) for each item in items, concurrently when --jobs > 1.

    Only ever used where every call is already known to be independent of
    every other (a fresh subprocess, no shared file) - see each call site's
    own comment. Sequential fallback (--jobs 1, or a single item) is exactly
    today's plain list comprehension, so this changes nothing about what
    runs or in what order results come back, only whether more than one
    child process may be in flight at once.
    """
    items = list(items)
    if JOBS <= 1 or len(items) <= 1:
        return [fn(x) for x in items]
    with _concurrent_futures.ThreadPoolExecutor(max_workers=min(JOBS, len(items))) as executor:
        return list(executor.map(fn, items))


# --- progress, to stderr only (stdout - the thing diffed against an older
# run - must stay byte-for-byte what it always was, --jobs or not). A suite
# that runs for minutes with no output looks the same as one that is hung,
# to a human watching or an agent that will be killed for taking too long.
_PROGRESS_EVERY = 100
_PROGRESS_START = time.time()


def _progress_ping():
    if len(CHECKS_RUN) % _PROGRESS_EVERY == 0:
        sys.stderr.write("  ... %d checks, %.0fs elapsed\n"
                          % (len(CHECKS_RUN), time.time() - _PROGRESS_START))
        sys.stderr.flush()


def sim(civ="rome_100ad", capital=None, manual=True, events=False):
    config = {"start_capital": capital} if capital is not None else None
    test_sim = S.Sim(NODES, ORDER, random.Random(1), events=events, manual=manual,
              civ=S.load_civ(civ), cfg=config)
    test_sim.goal, test_sim.done_year = GOAL, {}
    return test_sim


def run_it(s, *keys):
    """Build a concern AND keep its doors open.

    Every capability in the engine is gated on running() - built, and still
    being maintained - because a school nobody pays for trains no scholars.
    A check that wants the capability has to open the place, the same as a
    player would.
    """
    for key in keys:
        s.done.add(key)
        s.operating.add(key)
    s._done_changed()
    return s


# SLOW CHECKS ARE OPT-IN. Three of these cost 83 of the suite's 89 seconds,
# because they each simulate a couple of hundred years to test a long-run
# property. A suite you run after every change has to be seconds, or you stop
# running it, which is the exact rot this file exists to prevent. So the
# default run is fast and the expensive ones go behind --slow, to be run every
# few commits and before anything is called finished.
SLOW = "--slow" in sys.argv or os.environ.get("ROME_SLOW_TESTS")


def slow_check(name, fn):
    """Run an expensive check only when asked; otherwise say it was skipped.

    `fn` returns `(ok, detail)`, so the detail comes back with the result and
    is only built when the check actually runs. This used to take a third
    `detail_fn` argument that nothing read: no caller ever passed one, and a
    caller who did would have watched their detail vanish. Found by vulture.
    """
    if not SLOW:
        SKIPPED.append(name)
        return
    ok, detail = fn()
    check(name, ok, detail)


# SAME FLAG, ONE LEVEL UP. slow_check() above opts one expensive CHECK out of
# an otherwise-fast topic; SLOW_TOPICS opts a whole TOPIC MODULE out, because
# in these five the expense is not one buried check but the module's normal
# way of working - many full `proto()` subprocess sessions, or many checks
# that each step a Sim over a century or two, one after another. A per-topic
# timing run (see sim/tests/__main__.py, which is what actually reads this
# set) found these five cost 52.7% of the suite's wall time between them:
SLOW_TOPICS = {
    # 21.65s, 19.9% of the suite - the single biggest topic file, and both
    # kinds of expense at once: 37 real `proto()` subprocess sessions plus
    # 17 separate loops that each run a Sim across a century or more of
    # years, to see a policy or a hazard option actually play out long run
    # rather than just accept in year one.
    "round2_policy_hazards_options",
    # `round8_fixes` (8.57s) and `round9` (8.39s) USED TO BE LISTED HERE AND
    # ARE GONE, because the topics themselves are gone: both were named for
    # the development round that produced them rather than for anything they
    # test, and their checks now live in the fifteen subject-named topics
    # that replaced them. Re-timed after that move, the most expensive piece
    # either of them left behind is player_guidance_commands at 5.29s, then
    # knowledge_risk_and_sacking at 4.10s, and the other thirteen are under
    # two seconds each. Neither is worth opting 394 checks out of a default
    # run, so nothing inherited the slow tag: regrouping by subject spread
    # the subprocess cost thin enough that the concentration this set exists
    # to manage stopped existing. The default suite went from 45s to 62s in
    # exchange, which is those checks now running every time instead of only
    # under --slow.
    #
    # A name in here that matches no topic is silent: it skips nothing and
    # says nothing, which is exactly how these two went on looking like they
    # were saving time after the topics had been deleted underneath them.
    # sim/tests/test_suite_portability.py now fails if that happens again.
    # 8.18s, 7.5% - Complaints/47's fix (weather drawn per home region and
    # pooled by cultivable-land share, not one draw for a whole civilisation)
    # can only be told apart from the old single-draw behaviour by actually
    # running enough years for a distribution to show up in, across every
    # home region a civilisation holds.
    "regional_weather_wiring",
    # 7.15s, 6.6% - Complaints/50's fix (weather correlated across
    # geography.json's land tiles by real distance, not by region label)
    # needs enough tiles and enough sampled years for a correlation-by-
    # -distance curve to mean anything; fewer years would just be noise.
    "growing_season_weather_correlation",
}


def check(name, ok, detail=""):
    """Record a check, and how long the work before it took.

    The elapsed figure is the gap since the previous check, which is near
    enough to "what did this one cost" and needs no instrumentation at the
    call sites. It exists because the suite grew past fifteen minutes and got
    killed before finishing, and nobody could say which checks were expensive
    without timing them one at a time by hand.
    """
    global _LAST_AT
    now = time.time()
    took = now - _LAST_AT
    _LAST_AT = now
    CHECKS_RUN.append((name, took))
    _progress_ping()
    # str(): a failing check whose detail was a dict, a list or None used to
    # kill the whole suite here on a TypeError, so the one run that had
    # something to report was the one run that reported nothing.
    detail = "" if detail is None else str(detail)
    print("  %-58s %s%s" % (name, "ok" if ok else "FAIL " + detail,
                            "   %4.0fs" % took if took >= 1.0 else ""))
    if not ok:
        FAILURES.append(name + " " + detail)


def proto(lines, civ="rome_100ad", kit=None, fog=False):
    """Drive the real protocol in a real subprocess, as a player would."""
    cmd = [sys.executable, os.path.join(HERE, "simulator.py"), "agent", "--civ", civ]
    if kit:
        cmd += ["--kit", kit]
    if fog:
        cmd += ["--fog"]
    completed_process = subprocess.run(cmd, input="\n".join(json.dumps(command) for command in lines) + "\n",
                       capture_output=True, text=True, timeout=300, cwd=ROOT)
    parsed_lines = []
    for line in completed_process.stdout.splitlines():
        try:
            parsed_lines.append(json.loads(line))
        except ValueError:
            pass
    return parsed_lines, completed_process.stdout, completed_process.returncode


# ============================================================================
# Everything below this line is NOT part of the original file's top-of-file
# preamble. Each piece is a reusable, side-effect-free fixture (a pure
# function, a pure "from engine.X import Y as Z" alias, or a plain constant
# plus an idempotent os.makedirs) that the original flat script defined once
# inline and then called again much later, in what is now a different topic
# module. See this module's own docstring above for why duplicating the
# definition (once here, once in the topic module that originally introduced
# it) exactly reproduces the original behaviour everywhere.
# ============================================================================

# --- from sim/test_regressions.py's old "load/save" block (originally
# introduced around its own robustness-checks section): every save/load path
# used by the tests lives under one relative scratch directory, so that a
# real player's own relative save path is what's being exercised.
_LOADTEST_DIR = "_loadtest_tmp"
_loadtest_abs = os.path.join(ROOT, _LOADTEST_DIR)
os.makedirs(_loadtest_abs, exist_ok=True)


def _rel(name):
    return "%s/%s" % (_LOADTEST_DIR, name)


# --- from the old "THE CORRECTION" options section: the scratch directory
# session files for `play`-driven checks live under, elsewhere reused far
# past that section (e.g. the fog/rewind checks later on).
_PLAY_DIR = "_playtest_tmp"


# A GREEN RUN LEAVES NOTHING BEHIND; A RED ONE LEAVES THE EVIDENCE.
#
# Both scratch directories are created relative to ROOT, and ROOT is now the
# repository, so they sit inside the checkout where they are visible (and
# .gitignore'd) rather than being dropped in whatever directory the checkout
# happened to live in. Visible means they have to be tidied, and `--only`
# runs never reach the one topic module that used to rmtree _playtest_tmp on
# its way past. Doing it at interpreter exit covers every entry point and
# every topic selection.
#
# Only on a clean run, though. When a check fails, the save file or session
# transcript that failed it is usually the fastest way to see why, and
# deleting it on the way out would be the sort of helpfulness that costs an
# hour later.
@atexit.register
def _remove_scratch_dirs_if_green():
    if FAILURES:
        return
    for scratch_dir in (_LOADTEST_DIR, _PLAY_DIR):
        shutil.rmtree(os.path.join(ROOT, scratch_dir), ignore_errors=True)


# --- from the old "HISTORICAL EVENTS ANSWER TO WHAT WAS ACTUALLY BUILT"
# section: look up one named hazard from a civilisation file, by name.
def _hazard(civname, hazard_name):
    civ_data = S.load_civ(civname)
    return next(hazard for hazard in civ_data["hazards"] if hazard["name"] == hazard_name)


# --- from the old "TWO LOOMS COMPETE" goods-market section: n_looms real,
# distinct textiles-category venture nodes, all opened the same year, aged
# the same number of years.
def _mk_loom_sim(n_looms, age_years):
    """n_looms real, distinct textiles-category venture nodes, all opened
    the same year, aged the same number of years. Uses real tree nodes
    (not synthetic ones), the same way the rest of this file does."""
    candidates = sorted(node_id for node_id, node in NODES.items()
                  if node.get("cat") == "textiles" and node.get("rev"))
    assert len(candidates) >= n_looms, "not enough textiles venture nodes in the tree"
    chosen = candidates[:n_looms]
    loom_sim = sim(civ="rome_100ad", capital=5_000_000.0)
    loom_sim.artisans = loom_sim.scholars = 100.0 * n_looms
    # These fixtures exercise goods-market arithmetic, not labour scarcity.
    # Supply every qualified trade so each selected historical concern can
    # obtain both its workers and its specialist foreman.
    for trade in S.WAGES:
        loom_sim.employees[trade] = 100.0 * n_looms
    loom_sim.year = 100
    for node_id in chosen:
        loom_sim.done.add(node_id)
        loom_sim.done_year[node_id] = 100
    loom_sim._done_changed()
    for node_id in chosen:
        for trade, required in NODES[node_id].get("lab", {}).get("trades", {}).items():
            loom_sim.employees[trade] = max(loom_sim.employees.get(trade, 0.0),
                                     float(required) * n_looms)
        ok, msg = loom_sim.open_venture(node_id)
        assert ok, (node_id, msg)
    loom_sim.year = 100 + age_years
    return loom_sim, chosen


# --- mid-file "from engine.X import Y as Z" aliases: pure, side-effect-free
# imports the original flat file did inline, at first use, then relied on
# again in what is now a different topic module. Collected here so every
# topic module sees the same names via `from .harness import *`, regardless
# of which one first imports them; each one is also still imported (harmlessly,
# redundantly) inline at its original spot, verbatim.
from engine import cli as _CLI, settings as _SETTINGS
from engine import protocol as _protocol
from engine.protocol import _short_of_staff
from engine.protocol import render_pretty as _RP
from engine.protocol import _waiting_on as _WO
from engine.protocol import final_report as _FRPT, render_final as _RF
from engine import labour as _sp_labour, projects as _sp_projects
from engine.data import closure as _closure
from engine.protocol import _agent_log as _AL
from engine.protocol import parse_typed as _PT
from engine.protocol import _unlocked_by as _UB, _downstream_of as _DS
from engine.protocol import (render_state as _RSTATE, render_risk as _RRISK,
                             render_why as _RWHY, render_ventures as _RVENT,
                             render_path as _RPATH)
from engine.protocol import (_agent_capacity as _ACAP, _agent_economy as _AECO,
                             _agent_changes as _ACHG, _agent_mines as _AMINES,
                             render_capacity as _RCAP, render_economy as _REECO,
                             render_changes as _RCHG)
from engine.protocol import parse_typed as _PT2
from engine.protocol import TYPED_ALIASES as _TYPED_ALIASES
from engine import protocol as _PROTO
from engine.protocol import (score_report as _SCORE, render_score as _RSCORE,
                             SCORE_WEIGHTS as _SW)
from engine.protocol import _agent_portfolio as _APORT, render_portfolio as _RPORT
from engine.protocol import _portfolio_constraint as _PCON
import inspect as _insp_sp
import inspect as _insp2
import inspect as _insp3
import re as _re_rem
import re as _re_names
import shutil as _shutil
import hashlib
import shutil
import collections as _coll
import importlib as _IL
import io as _IO, contextlib as _CTX
import time as _time

# `from .harness import *` must hand every topic module everything the old
# flat script had at global scope, including the (many) leading-underscore
# names above - a plain `import *` skips those unless __all__ says otherwise.
# Computed, not hand-listed, so nothing added above is ever silently dropped.
__all__ = [name for name in list(globals()) if not name.startswith("__")]
