"""Shared fixtures, imports and check-recording machinery for the split
test suite (see rome/sim/tests/__main__.py for the runner).

This is test_regressions.py's own former preamble (import block, TREE/NODES/
ORDER/GOAL, check()/slow_check()/proto()/sim()/run_it()/_par_map(), the
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
import collections, copy, glob, json, os, random, re, subprocess, sys, time
import concurrent.futures as _concurrent_futures
import threading
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(HERE))
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
    t0 = time.time()
    try:
        return _real_subprocess_run(*a, **kw)
    finally:
        dt = time.time() - t0
        with _SUBPROC_LOCK:
            _SUBPROC_TIME[0] += dt
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
    with _concurrent_futures.ThreadPoolExecutor(max_workers=min(JOBS, len(items))) as ex:
        return list(ex.map(fn, items))


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
    cfg = {"start_capital": capital} if capital is not None else None
    s = S.Sim(NODES, ORDER, random.Random(1), events=events, manual=manual,
              civ=S.load_civ(civ), cfg=cfg)
    s.goal, s.done_year = GOAL, {}
    return s


def run_it(s, *keys):
    """Build a concern AND keep its doors open.

    Every capability in the engine is gated on running() - built, and still
    being maintained - because a school nobody pays for trains no scholars.
    A check that wants the capability has to open the place, the same as a
    player would.
    """
    for k in keys:
        s.done.add(k)
        s.operating.add(k)
    s._done_changed()
    return s


# SLOW CHECKS ARE OPT-IN. Three of these cost 83 of the suite's 89 seconds,
# because they each simulate a couple of hundred years to test a long-run
# property. A suite you run after every change has to be seconds, or you stop
# running it, which is the exact rot this file exists to prevent. So the
# default run is fast and the expensive ones go behind --slow, to be run every
# few commits and before anything is called finished.
SLOW = "--slow" in sys.argv or os.environ.get("ROME_SLOW_TESTS")


def slow_check(name, fn, detail_fn=None):
    """Run an expensive check only when asked; otherwise say it was skipped."""
    if not SLOW:
        SKIPPED.append(name)
        return
    ok, detail = fn()
    check(name, ok, detail)


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
    p = subprocess.run(cmd, input="\n".join(json.dumps(c) for c in lines) + "\n",
                       capture_output=True, text=True, timeout=300, cwd=ROOT)
    out = []
    for ln in p.stdout.splitlines():
        try:
            out.append(json.loads(ln))
        except ValueError:
            pass
    return out, p.stdout, p.returncode


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

# --- from rome/sim/test_regressions.py's old "load/save" block (originally
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


# --- from the old "HISTORICAL EVENTS ANSWER TO WHAT WAS ACTUALLY BUILT"
# section: look up one named hazard from a civilisation file, by name.
def _hazard(civname, hazard_name):
    _c = S.load_civ(civname)
    return next(h for h in _c["hazards"] if h["name"] == hazard_name)


# --- from the old "TWO LOOMS COMPETE" goods-market section: n_looms real,
# distinct textiles-category venture nodes, all opened the same year, aged
# the same number of years.
def _mk_loom_sim(n_looms, age_years):
    """n_looms real, distinct textiles-category venture nodes, all opened
    the same year, aged the same number of years. Uses real tree nodes
    (not synthetic ones), the same way the rest of this file does."""
    cand = sorted(k for k, n in NODES.items()
                  if n.get("cat") == "textiles" and n.get("rev"))
    assert len(cand) >= n_looms, "not enough textiles venture nodes in the tree"
    chosen = cand[:n_looms]
    s = sim(civ="rome_100ad", capital=5_000_000.0)
    s.artisans = s.scholars = 100.0 * n_looms
    # These fixtures exercise goods-market arithmetic, not labour scarcity.
    # Supply every qualified trade so each selected historical concern can
    # obtain both its workers and its specialist foreman.
    for trade in S.WAGES:
        s.employees[trade] = 100.0 * n_looms
    s.year = 100
    for k in chosen:
        s.done.add(k)
        s.done_year[k] = 100
    s._done_changed()
    for k in chosen:
        for trade, required in NODES[k].get("lab", {}).get("trades", {}).items():
            s.employees[trade] = max(s.employees.get(trade, 0.0),
                                     float(required) * n_looms)
        ok, msg = s.open_venture(k)
        assert ok, (k, msg)
    s.year = 100 + age_years
    return s, chosen


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
__all__ = [_n for _n in list(globals()) if not _n.startswith("__")]
