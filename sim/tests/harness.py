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
# Games in the suite open after a few hidden spin-up years rather than the declared bounds, cached apart
# from full games' (sim/markets/port_year.py); a cold full spin-up costs many minutes per start.
os.environ.setdefault("ROME_SPIN_UP_YEARS", "3,2")

# collections, copy, glob, re and tempfile are not used in this file; topic modules use them bare and rely on
# `from .harness import *` to put them in scope.

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
from sim.prices import commodities as COMMOD

TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_LAB, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
FAILURES = []
# Counted rather than hand-maintained: the tally in the summary line was a
# literal that three separate rounds of additions had to remember to update.
CHECKS_RUN = []
SKIPPED = []
# Above zero while a topic module is imported only for its helpers: its module-level checks belong to its own topic.
MUTED = [0]
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


def hours_money(hours, civ="rome_100ad"):
    """Labour hours in a civilisation's own coin (Rome's by default)."""
    return hours * S.starting_schedule(civ).money_per_labour_hour


def sim(civ="rome_100ad", capital=None, manual=True, events=False, surveyed=None):
    """A game on the agent economy. `surveyed` lists the materials whose deposits the game has already found
    (a mine names a found deposit; the metals and coal by default, `()` for none)."""
    config = {"start_capital": capital} if capital is not None else None
    test_sim = S.Sim(NODES, ORDER, random.Random(1), events=events, manual=manual,
              civ=S.load_civ(civ), cfg=config)
    test_sim.goal, test_sim.done_year = GOAL, {}
    for material in (("coal",) + tuple(_ore_goods(test_sim.view("legacy_world_map")()))) if surveyed is None else tuple(surveyed):
        found_deposits_of(test_sim, material)
    return test_sim


def unopened_sim(civ="rome_100ad", capital=None, manual=True, events=False, surveyed=None):
    """A game whose agent economy has not opened: the engine's own figures answer every question, as they do while
    the economy opens, and no hidden years run. For tests that read only the data, the map or the setup built from
    them (and, since nothing is cleared, for mechanisms that need the engine's own tables)."""
    return build_unopened(lambda: sim(civ=civ, capital=capital, manual=manual, events=events, surveyed=surveyed))


def build_unopened(factory):
    """`factory()` (a call that builds a `Sim`) with the agent economy left unopened: see `unopened_sim`."""
    from unittest import mock
    from sim.engine import foreign_economy_data
    from sim.markets.port import EconomyPort
    every_record = foreign_economy_data.foreign_economy_records

    def supported_records():
        return tuple(record for record in every_record() if not record.get("agent_economy", False))

    # The opening cast may be seeded during construction, before the economy opens.
    with mock.patch.object(EconomyPort, "open_agent", lambda self: None), \
            mock.patch.object(foreign_economy_data, "foreign_economy_records", supported_records):
        game = factory()
    game.view("legacy_economy")()._opening = True
    game.assembly.modules["foreign_trade"].needs.foreign_economy_records = supported_records   # the partners of the books only
    return game


def _ore_goods(world_map):
    from sim.geography import api as _geography
    return _geography.ore_goods(world_map)


def found_deposits_of(game, material):
    """Give the game the deposits of `material` that thorough prospecting of its held tiles would find, without
    paying for the search, so a test can open a mine (a mine names a deposit it has found)."""
    from sim.geography import api as _geography
    resources = game.assembly.modules["resources"]
    resource_id = resources.mine_resource_id(material)
    if resource_id is None:
        return []
    seed = "tests"
    held = _geography.tiles_held(game.civ, game.view("legacy_world_map")())
    for tile in sorted(held, key=lambda tile: -_geography.endowment(tile, resource_id, game.view("legacy_world_map")())["undiscovered_expected"]):
        found = _geography.prospect(tile, resource_id, 1e12, seed, game.view("legacy_world_map")())
        known = {row["id"] for row in resources.seat.deposits_found}
        resources.seat.deposits_found.extend(dict(row) for row in found if row["id"] not in known)
    return game.found_deposits(material)


def concern_needing_craftsmen_to_supervise():
    """A concern the founder's own scholar can cover, that needs more craftsmen than the founder and
    the closure slack can cover alone (and no more than the six hired in the fixtures), so losing every
    hired craftsman shuts it. Of those, the cheapest to open: a fixture's founder holds little, and what
    the opening prices a heavy build's materials at is not what these tests are about."""
    probe = sim()
    cover = probe.FOUNDER_IS_WORTH + probe.STAFFING_CLOSURE_SLACK
    fits = []
    for candidate_id in sorted(NODES):
        node = NODES[candidate_id]
        if probe.is_venture(candidate_id) and node["art"] > 0 and not (node.get("lab") or {}).get("artisan"):
            scholars, craftsmen = probe.venture_hands(candidate_id)
            if (scholars <= probe.labour.effective_scholars() and cover < craftsmen <= 5.5
                    and probe.venture_foreman(candidate_id)[0] is None):
                fits.append((probe.venture_capex(candidate_id), candidate_id))
    if not fits:
        raise AssertionError("no concern needs craftsmen to supervise")
    return min(fits)[1]


def ready_for_entry(game, money=None):
    """Ready a game for firm entry: the home strata hold savings (a game whose agent economy has not run has
    empty purses, and a firm is founded from a stratum's savings). The opening cast (strata and governments)
    is seeded first when it has not been. `money` is the savings of each free home stratum; by default the
    entrepreneurial share of a year's output between them. Returns the game."""
    if not game.view("cast")().state.home_country:
        game.view("seeded_actor_registry")()
    free = [stratum for stratum in game.view("cast")().of_kind("stratum")
            if stratum.record.country is None and not stratum.is_bonded()]
    if money is None:
        from sim.agents.tuning import ENTREPRENEURIAL_CAPITAL_SHARE
        money = game.view("actor_world")().society_output() * ENTREPRENEURIAL_CAPITAL_SHARE / max(1, len(free))
    for stratum in free:
        stratum.money = money
    return game


def noted_sale_tonnes(game, material, seller=None):
    """Tonnes of `material` the actors (or just `seller`) have noted for the year's market: a sale enters the agent
    economy's book as an order when the year clears, so until then this is where it stands."""
    return sum(sale["tonnes"] for sale in game.view("legacy_economy")().agent.stored.get("sales", [])
               if sale["material"] == material and (seller is None or sale["seller"] == seller))


def state_seeking(game, requisition=0.16, office=0.06):
    """Put the state in need: the rates it takes at full notice from the income it can see, as a
    year's shortfall would leave them. Returns the game."""
    record = game.view("state_treasury")().record
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
from .discovery import TESTS_DIR, discover_topics, discover_quick_topics, discover_serial_topics

QUICK_TOPICS = discover_quick_topics()
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
    if MUTED[0]:
        return
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
    """Drive the real `simulator.py agent` protocol, in this process (cli_in_process.py)."""
    from sim.tests import cli_in_process
    arguments = ["agent", "--civ", civ]
    if kit:
        arguments += ["--kit", kit]
    if fog:
        arguments += ["--fog"]
    completed_process = cli_in_process.run(
        arguments, "\n".join(json.dumps(command) for command in lines) + "\n")
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
def use_scratch_tag(tag):
    """Give this process its own scratch directories, as a worker started with --worker-tag gets."""
    global _SCRATCH_TAG, _LOADTEST_DIR, _loadtest_abs, _PLAY_DIR
    _SCRATCH_TAG = "_" + tag
    _LOADTEST_DIR = "_loadtest_tmp" + _SCRATCH_TAG
    _loadtest_abs = os.path.join(ROOT, _LOADTEST_DIR)
    os.makedirs(_loadtest_abs, exist_ok=True)
    _PLAY_DIR = "_playtest_tmp" + _SCRATCH_TAG


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
        ratios.append(test_sim.view("demographic_flows")().nutrition_ratio)
    return ratios


# --- from the old "TWO LOOMS COMPETE" goods-market section: n_looms real,
# distinct textiles-category venture nodes, all opened the same year, aged
# the same number of years.
def _mk_loom_sim(n_looms, age_years):
    """n_looms real, distinct output-earning venture nodes, all opened
    the same year, aged the same number of years. Uses real tree nodes
    (not synthetic ones), the same way the rest of this file does."""
    loom_sim = sim(civ="rome_100ad", capital=5_000_000.0)
    # a node earns only from its output, so the chosen concerns are those that take money from it
    candidates = sorted(node_id for node_id in NODES
                        if loom_sim.is_venture(node_id) and loom_sim.concern_takings(node_id, 1.0) > 0)
    assert len(candidates) >= n_looms, "not enough output-earning venture nodes in the tree"
    chosen = candidates[:n_looms]
    staff = loom_sim.state.seats[loom_sim.state.acting_seat].modules["workforce"]
    staff.artisans = staff.scholars = 100.0 * n_looms
    # These fixtures exercise goods-market arithmetic, not labour scarcity.
    # Supply every qualified trade so each selected historical concern can
    # obtain both its workers and its specialist foreman.
    for trade in S.WAGES:
        staff.employees[trade] = 100.0 * n_looms
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


# --- aliases that topic modules use bare through `from .harness import *`; harness.py's own body does not call them.
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
