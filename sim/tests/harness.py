"""Shared fixtures, imports and check-recording machinery for the split
test suite (see sim/tests/__main__.py for the runner).

Every topic module does `from .harness import *` to see everything defined
here: the import block, TREE/NODES/ORDER/GOAL, check()/slow_check()/proto()/
sim()/run_it()/_par_map(), the subprocess-timing patch and the --jobs
parsing. Every topic module is just top-level code that calls
check()/slow_check() at import time, in file order - splitting into files
changes nothing about how a check runs, only how the source is organised on
disk.

A few names below (_hazard, _rel/_LOADTEST_DIR, and the whole
family of `from ui.protocol import X as _Y` mid-file imports) are
reusable, side-effect-free pieces (pure functions, pure imports, or a plain
string constant + an idempotent os.makedirs) that topic modules import
through the harness rather than defining local copies.
"""
import atexit, collections, copy, glob, json, os, random, re, shutil, subprocess, sys, time
import concurrent.futures as _concurrent_futures
import threading
import tempfile

# Games started without --seed draw a fresh one; the suite needs them to replay.
os.environ.setdefault("ROME_DEFAULT_SEED", "1")

# ruff reports collections, copy, glob and re (from the combined import just
# above) and tempfile as unused in THIS file - correctly, harness.py itself
# never calls them. They stay because other topic modules use them bare
# (collections.Counter, copy.deepcopy, glob.glob, re.compile, tempfile.*)
# without importing them locally, relying on `from .harness import *` to put
# the name in scope, exactly as this file's own docstring above describes.
# Confirmed by checking every topic module for a bare use with no local
# import of its own: collections -> test_scanners_and_scheduling.py; copy ->
# test_explicit_starting_techs.py, test_round8g_display.py; glob ->
# test_civilisation_data_integrity.py; re -> test_mines.py and others;
# tempfile -> test_round2_policy_hazards_options.py and others.

# HERE is this repository's sim/ directory; ROOT is the repository itself.
#
# ROOT MUST BE THE REPOSITORY, NOT ITS PARENT: computing it as the parent
# only works if that parent happens to contain a directory literally named
# `rome`, and breaks in two ways the moment it does not. Every scratch file
# the suite writes (_loadtest_tmp, _playtest_tmp, and every subprocess run
# with cwd=ROOT) would land OUTSIDE the checkout, in whatever directory the
# checkout happens to sit in. And a check that globs
# os.path.join(ROOT, "data", ...) - the natural spelling - would silently match nothing, so assertions
# about the civilization files' event coverage would run zero times without
# anyone noticing, because a for-loop over an empty glob does not fail, it
# just says nothing.
#
# ROOT is the repository, so `os.path.join(ROOT, "data", ...)` means what it
# reads as, scratch files stay inside the checkout where .gitignore can see
# them, and nothing anywhere depends on what the checkout is called.
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)
while HERE in sys.path:
	sys.path.remove(HERE)
from sim.tests.isolation import isolate_home
# The suite never touches the real home: settings and saves go to a per-run temporary directory.
isolate_home()
from sim import simulator as S
# PLANNER and COMMOD are unused in harness.py itself for the same reason as
# the note above: test_people_attrition_scholars.py and test_reputation.py
# use PLANNER, and test_literacy_market_pricing.py and
# test_commodities_wired_in.py use COMMOD, bare and without their own import.
from sim.engine import planner as PLANNER
from sim.engine import commodities as COMMOD

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

# --jobs N: how many independent child processes may run at once. Results
# keep input order, so output is identical for any N; the default is the
# cores this process may use, and --jobs 1 runs everything sequentially.
def _available_cores():
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)


JOBS = _available_cores()
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

# A parallel-run worker (see __main__.py) is launched with `--worker-tag TAG`;
# its scratch directories get that suffix so concurrent topics never share
# one. Read from argv rather than the environment so a suite run started
# from inside a topic does not inherit it.
_SCRATCH_TAG = ""
if "--worker-tag" in sys.argv and sys.argv.index("--worker-tag") + 1 < len(sys.argv):
    _SCRATCH_TAG = "_" + sys.argv[sys.argv.index("--worker-tag") + 1]


def _par_map(function, items):
    """Run function(item) for each item in items, concurrently when --jobs > 1.

    Only ever used where every call is already known to be independent of
    every other (a fresh subprocess, no shared file) - see each call site's
    own comment. Sequential fallback (--jobs 1, or a single item) is exactly
    today's plain list comprehension, so this changes nothing about what
    runs or in what order results come back, only whether more than one
    child process may be in flight at once.
    """
    items = list(items)
    if JOBS <= 1 or len(items) <= 1:
        return [function(item) for item in items]
    with _concurrent_futures.ThreadPoolExecutor(max_workers=min(JOBS, len(items))) as executor:
        return list(executor.map(function, items))


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


def book_money(denarii, civ="rome_100ad"):
    """Book denarii in a civilisation's own coin (Rome's by default)."""
    from sim.engine import money_units
    return money_units.book_to_money(
        denarii, S.starting_schedule(civ).money_per_labour_hour)


def sim(civ="rome_100ad", capital=None, manual=True, events=False, agent_economy=None):
    """A game on the default economy; `agent_economy=False` opts out to the engine's own yearly market."""
    config = {"start_capital": capital} if capital is not None else {}
    if agent_economy is not None:
        config["agent_economy"] = agent_economy
    config = config or None
    test_sim = S.Sim(NODES, ORDER, random.Random(1), events=events, manual=manual,
              civ=S.load_civ(civ), cfg=config)
    test_sim.goal, test_sim.done_year = GOAL, {}
    return test_sim


def concern_needing_craftsmen_to_supervise():
    """A concern that earns, needs no scholars, and holds more craftsmen than the founder
    and the closure slack can cover alone (more than its build crew shown as staff_needed), so losing every hired craftsman shuts it."""
    probe = sim()
    for candidate_id in sorted(NODES):
        node = NODES[candidate_id]
        if node["rev"] > 0 and node["sch"] == 0 and node["art"] > 0 and not (node.get("lab") or {}).get("artisan"):
            scholars, craftsmen = probe.venture_hands(candidate_id)
            if scholars == 0 and max(node["art"], probe.FOUNDER_IS_WORTH + probe.STAFFING_CLOSURE_SLACK) < craftsmen <= 5.5 and probe.venture_foreman(candidate_id)[0] is None:
                return candidate_id
    raise AssertionError("no concern needs craftsmen to supervise")


def state_seeking(game, requisition=0.16, office=0.06):
    """Put the state in need: the rates it takes at full notice from the income it can see, as a
    year's shortfall would leave them. Returns the game."""
    record = game.state_treasury().record
    record.levy_requisition_rate, record.levy_office_rate = requisition, office
    return game


def run_it(sim_state, *keys):
    """Build a concern AND keep its doors open.

    Every capability in the engine is gated on running() - built, and still
    being maintained - because a school nobody pays for trains no scholars.
    A check that wants the capability has to open the place, the same as a
    player would.
    """
    for key in keys:
        sim_state.done.add(key)
        sim_state.operating.add(key)
    sim_state._done_changed()
    return sim_state


# SLOW CHECKS ARE OPT-IN. Three of these cost 83 of the suite's 89 seconds,
# because they each simulate a couple of hundred years to test a long-run
# property. A suite you run after every change has to be seconds, or you stop
# running it, which is the exact rot this file exists to prevent. So the
# default run is fast and the expensive ones go behind --slow, to be run every
# few commits and before anything is called finished.
SLOW = "--slow" in sys.argv or os.environ.get("ROME_SLOW_TESTS")


def slow_check(name, run_check):
    """Run an expensive check only when asked; otherwise say it was skipped.

    `run_check` returns `(passed, detail)`, so the detail comes back with the result and
    is only built when the check actually runs. This used to take a third
    `detail_fn` argument that nothing read: no caller ever passed one, and a
    caller who did would have watched their detail vanish. Found by vulture.
    """
    if not SLOW:
        SKIPPED.append(name)
        return
    passed, detail = run_check()
    check(name, passed, detail)


# Topic discovery lives in discovery.py so --list needs no heavy imports.
from .discovery import TESTS_DIR, discover_topics, discover_slow_topics, discover_serial_topics

SLOW_TOPICS = discover_slow_topics()
SERIAL_TOPICS = discover_serial_topics()


def check(name, passed, detail=""):
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
    print("  %-58s %s%s" % (name, "ok" if passed else "FAIL " + detail,
                            "   %4.0fs" % took if took >= 1.0 else ""))
    if not passed:
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
# Everything below this line is a reusable, side-effect-free fixture (a pure
# function, a pure "from engine.X import Y as Z" alias, or a plain constant
# plus an idempotent os.makedirs) that some topic modules also define for
# themselves, verbatim, inside their own namespace. See this module's own
# docstring above for why that duplication is harmless.
# ============================================================================

# Every save/load path used by the tests lives under one relative scratch
# directory, so that a real player's own relative save path is what's being
# exercised.
_LOADTEST_DIR = "_loadtest_tmp" + _SCRATCH_TAG
_loadtest_abs = os.path.join(ROOT, _LOADTEST_DIR)
os.makedirs(_loadtest_abs, exist_ok=True)


def _rel(name):
    return "%s/%s" % (_LOADTEST_DIR, name)


# --- from the old "THE CORRECTION" options section: the scratch directory
# session files for `play`-driven checks live under, elsewhere reused far
# past that section (e.g. the fog/rewind checks later on).
_PLAY_DIR = "_playtest_tmp" + _SCRATCH_TAG


# A GREEN RUN LEAVES NOTHING BEHIND; A RED ONE LEAVES THE EVIDENCE.
#
# Both scratch directories are created relative to ROOT, and ROOT is the
# repository, so they sit inside the checkout where they are visible (and
# .gitignore'd) rather than being dropped in whatever directory the checkout
# happens to live in. Visible means they have to be tidied, and `--only`
# runs never reach whichever single topic module would otherwise rmtree
# _playtest_tmp on its way past. Doing it at interpreter exit covers every
# entry point and every topic selection.
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


def nutrition_ratios_over_years(test_sim, years):
    """Run demographic recovery and return each year's nutrition ratio."""
    ratios = []
    for year in years:
        test_sim._demographic_recovery(year)
        ratios.append(test_sim._last_demographic_step.nutrition_ratio)
    return ratios


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
    loom_sim = sim(civ="rome_100ad", capital=5_000_000.0, agent_economy=False)   # legacy: callers assert on the engine's goods-market arithmetic
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
        opened, msg = loom_sim.open_venture(node_id)
        assert opened, (node_id, msg)
    loom_sim.year = 100 + age_years
    return loom_sim, chosen


# --- mid-file "from engine.X import Y as Z" aliases: pure, side-effect-free
# imports the original flat file did inline, at first use, then relied on
# again in what is now a different topic module. Collected here so every
# topic module sees the same names via `from .harness import *`, regardless
# of which one first imports them; each one is also still imported (harmlessly,
# redundantly) inline at its original spot, verbatim.
#
# ruff's F401 pass flags every name below as unused, because none of them is
# called from harness.py's own body - each exists only so that a LATER topic
# module can use it without importing it again itself, via `from .harness
# import *` (harness.py's __all__ near the end of this file is computed from
# globals(), which ruff cannot follow statically, so it cannot see the
# re-export either). Checked one by one, over every file in this package, for
# a bare use with no local import of its own, before deciding which of these
# to keep:
#   _CLI            -> test_five_things_winner.py
#   _protocol       -> test_scanners_and_scheduling.py, test_five_things_winner.py,
#                      test_affordability_and_credit.py, test_sort_nearest.py,
#                      test_parallelism_note.py, test_labour_hiring_and_wages.py,
#                      test_allocate.py
#   _RP             -> test_scanners_and_scheduling.py, test_interface_honesty.py,
#                      test_names_and_fog.py, test_industrial_dashboard.py,
#                      test_player_log.py, test_project_pacing.py,
#                      test_eminence_scandal_and_reputation.py, test_ventures_lifecycle.py
#   _WO             -> test_scanners_and_scheduling.py, test_affordability_and_credit.py
#   _FRPT, _RF      -> test_scanners_and_scheduling.py
#   _PT             -> test_scanners_and_scheduling.py, test_people_attrition_scholars.py,
#                      test_complaints_17_24.py, test_fog_leak3.py
#   _RSTATE         -> test_scanners_and_scheduling.py
#   _RWHY           -> test_arrears_visibility.py
#   _PROTO, _RPORT  -> test_arrears_visibility.py
# Everything else in this block (_SETTINGS, _short_of_staff, _sp_labour,
# _sp_projects, _closure, _AL, _UB, _DS, _RRISK, _RVENT, _RPATH, _ACAP, _AECO,
# _ACHG, _AMINES, _RCAP, _REECO, _RCHG, _PT2, _TYPED_ALIASES, _SCORE, _RSCORE,
# _SW, _APORT, _PCON, plus the stdlib re-imports as _insp_sp/_insp2/_insp3/
# _re_rem/_re_names/_shutil/_coll/_IL/_IO/_CTX/_time and the bare hashlib and
# duplicate shutil) had no such consumer anywhere in sim/tests - genuinely
# dead, not a re-export, so removed rather than kept "just in case".
from sim.ui import cli as _CLI
from sim.ui import protocol as _protocol
from sim.ui.protocol import render_pretty as _RP
from sim.ui.protocol import _waiting_on as _WO
from sim.ui.protocol import final_report as _FRPT, render_final as _RF
from sim.ui.protocol import parse_typed as _PT
from sim.ui.protocol import render_state as _RSTATE, render_why as _RWHY
from sim.ui import protocol as _PROTO
from sim.ui.protocol import render_portfolio as _RPORT

# `from .harness import *` must hand every topic module everything the old
# flat script had at global scope, including the (many) leading-underscore
# names above - a plain `import *` skips those unless __all__ says otherwise.
# Computed, not hand-listed, so nothing added above is ever silently dropped.
__all__ = [name for name in list(globals()) if not name.startswith("__")]
