"""The command line's core: shared infrastructure, the batch/Monte Carlo
commands (run, compare, sensitivity, sweep), the static tree/civilisation
listings (validate, path, costs, goals), and main() itself.

CLI commands are split by subject across four files:
  - cli.py (this file) - shared infrastructure and the commands above.
  - cli_interactive.py - the human-facing front door: main menu, the New
    Game wizard, civilisation listing, and the `play` game loop/REPL.
  - cli_agent.py        - the machine-playable protocol: `agent`.
  - cli_analysis.py     - planning and diagnostic commands: `plan`, `search`,
    `why`.
Everything importable from `engine.cli` is: the functions living in the
other three files are re-imported below, at the bottom of this file (so
they can themselves import session/display helpers defined earlier in this
module - see the comment there for why the order matters).

`cmd_run`, `cmd_compare`, `cmd_sensitivity`, `cmd_sweep`, `cmd_validate`,
`cmd_path`, `cmd_costs` and `cmd_goals` live here rather than in one of the
other three: the first four all construct `Sim(...)` directly and share the
Monte Carlo/statistics helpers below (`_wilson_interval`, `_fmt_rate_ci`,
`_summarise`); the last four are simple, self-contained tree/civilisation
reads with no REPL or protocol machinery of their own. See cmd_sweep's own
placement note and cli_analysis.py's module docstring for the specific,
tested reason `cmd_sweep` cannot move into cli_analysis.py alongside
`cmd_plan`.
"""
import collections, json, math, os, random
from collections import defaultdict

from .data import (CIVDIR, closure, critical_path, DEFAULTS, goal_catalog,
                   hard_pre, load, load_civ, resolve_goal,
                   STARTING_KITS, STRATS, topo_order, win_condition_describe)


import argparse, sys

from .core import Sim
from . import protocol as _protocol
from . import settings
# civ_of_save/goal_of_save are the only names this file reads from
# .protocol; `cmd_agent` and everything else that needs
# _agent_available, _agent_dispatch, _agent_end_reason, _agent_help,
# _agent_state, _node_explain, final_report, load_state, parse_typed,
# render_final, render_pretty or save_state lives in cli_agent.py, which
# imports its own copies of what it needs straight from .protocol.
from .protocol import civ_of_save, goal_of_save
from constants import declare


# ----------------------------------------------------------------------------
# A DICE-FREE RNG, FOR --deterministic ON run/compare/play/agent.
#
# `path_search.py` built this first, to answer its own question - "does the
# planned order even get there with the dice off?" - see that module's
# docstring for the full argument (scarce trades, the capital trap, and why
# `--no-events` alone was never enough to ask it). It lives HERE, not there,
# because BOTH files need it and one of them has to be the one place it is
# actually defined: `path_search.py` already imports `load_strategy` and
# `topo_stable` from this module, so importing this the same way costs
# nothing, while the reverse - this module reaching into a standalone
# script's namespace - would tie every ordinary invocation of `run`/
# `compare`/`play`/`agent` to path_search.py's own module-load order for no
# reason. A second, independently-typed copy of the same class was the other
# option, and is exactly the duplication this project's own comments warn
# against elsewhere: two copies drift, and the drift is invisible until a fix
# lands in one and not the other.
# ----------------------------------------------------------------------------

class DetRNG(random.Random):
    """A seeded rng whose random() always returns 1.0.

    Every probability check anywhere in this engine is "< threshold" with
    threshold in (0, 1) - a project's own risk of failing outright
    (engine/projects.py `_complete`), the 3.5% yearly attrition roll, the 25%
    manumission roll, the fractional-headcount rounding in
    `labour.py:_stochastic_round`, and every dated hazard `society.py`'s
    `_shocks` rolls for (staff loss, a sack, and their own "does it come to
    nothing instead" counter-rolls) - so a draw of 1.0 is never below any of
    them: nothing fails, nobody dies, nothing is freed by luck, no hazard
    lands, every fraction rounds down. `randint`/`sample` are never reached in
    a run built this way (they sit behind `not self.founder_alive`, and a
    dice-free trial is always run with an immortal founder), so overriding
    `random()` alone is enough to make a whole run reproduce identically
    regardless of seed - the seed number itself stops mattering, which is the
    point: this is the world with the dice removed, not a world with better
    dice.

    NOT THE SAME THING AS `--no-events`, and deliberately independent of it.
    `--no-events` only silences DATED weather/plague/political hazards (this
    engine's `self.events` flag gating `_shocks` in core.py) and, alone,
    still leaves project-failure risk, attrition, manumission and stochastic
    rounding drawing from an ordinary seeded rng every time - see that flag's
    own help text, which says exactly this. This class is the other half: it
    changes how every roll comes out, not which code paths run. In practice,
    passing `--deterministic` without `--no-events` still ends up dice-free,
    because `_shocks` is itself built entirely from the same "< threshold"
    rolls this class always fails - but the two flags are kept separately
    documented rather than one silently implying the other, because a reader
    of `--no-events`'s own help text should not have to already know this
    class exists to understand what that flag alone does and does not do.
    """
    def random(self):
        return 1.0


def ensure_fixed_hash_seed(seed="0"):
    """A "deterministic" trial is not, unless this runs first.

    `DetRNG` makes every `random()` call return 1.0, which is exactly
    reproducible on its own - but CPython hashes strings differently in every
    process by default (`hash("machinist")` differs run to run unless
    `PYTHONHASHSEED` is fixed), and this engine has at least one documented
    site (core.py's own comment on `rng.sample(losable, ...)`) where walking
    a bare, unsorted `set` of ids would depend on that hash order - so a
    --deterministic run whose output depended on iteration order over some
    other such set
    would silently stop being reproducible process to process, for no reason
    a reader of a diff would ever see. `PYTHONHASHSEED` can only be set
    before the interpreter starts, not from inside an already-running one, so
    a process not launched with it fixed re-execs itself, once, with it set.
    Shared with `path_search.py`, which needs this exact same guarantee for
    its own dice-free search trials and imports this function for it rather
    than keeping a second copy - see that module's own docstring for the
    fuller account of why this matters and what was actually measured about
    it.
    """
    if os.environ.get("PYTHONHASHSEED") == seed:
        return
    env = dict(os.environ, PYTHONHASHSEED=seed)
    os.execvpe(sys.executable, [sys.executable] + sys.argv, env)


# ----------------------------------------------------------------------------
# DIFFICULTY, PRESENTED HONESTLY, AS WHAT IT ACTUALLY IS HERE: how long you
# have. The horizon was already a plain number the engine takes; a player who
# had just won the whole game proposed naming a few points on that same line
# - Challenge/Standard/Relaxed/Endless - rather than asking for four bare
# numbers with no sense of what any of them mean.
#
# THE ONE THING A NAME CANNOT FIX ON ITS OWN: the SAME horizon is a
# completely different offer depending which civilisation it is attached to.
# Measured with every stroke of luck removed - no events, no project
# failures, an immortal founder, the game's own planner doing the ordering -
# reaching the current goal has taken about 451 years from Han China and
# about 1,019 from Rome (see data/review/PATH_SEARCH.md section 6 for
# the method and the full tables). A 500-year Standard is generous for the
# one and short of reachable for the other, and a menu that offers both
# civilisations and both horizons with nothing connecting them is offering a
# choice it has not explained. See _new_game's own use of this table for
# where that connection actually gets said out loud, to whichever
# civilisation a player has just picked.
#
# THIS IS A MEASUREMENT OF THE PLANNER'S OWN POLICY, NOT A PROPERTY OF THE
# GAME - say so, if this is ever quoted outside this file. PATH_SEARCH.md
# section 4 traces Rome's 1,019-year figure to a specific, diagnosed cause
# (an early credit-exhaustion cycle the automatic optimizer falls into and
# does not climb back out of for roughly 850 years) and section 4.4 proves,
# by direct ablation, that no reordering of the strategy file - which is
# the entire space planner.py/path_search.py can search - changes it. A
# real, far stronger playthrough (playtest/fixtures/
# rome_434_goal_startable.json) reaches the SAME goal in 334 years, three
# times faster, by playing manually rather than by any order this table's
# own instrument can express. Do not read 1,019 as "Rome cannot be won
# faster" - only as "this structural instrument, searched honestly,
# including a move that tries to grow the household's own capacity (see
# PATH_SEARCH.md section 5), could not find an order that does."
#
# NOT RECOMPUTED HERE, EVER. A single dice-free trial takes anywhere from
# several seconds (a short horizon, as path_search.py's own search rounds
# run it) to minutes (a full-length one, per PATH_SEARCH.md's own timing
# notes) - far too slow for a menu a player is sitting in front of, and nor
# is it this file's place to duplicate planner.py/path_search.py's own
# measurement. Hand-updated if that document's own numbers change; a
# civilisation not in this table is simply not given a number, rather than
# being handed a guess dressed as a fact.
DICE_FREE_FLOOR_YEARS = {
    "han_china_100ad": 451,
    "rome_100ad": 1019,
}

# NAMED, NOT INVENTED. Every one of these is the SAME knob the engine always
# had (a plain year count the run ends at) - nothing here scales a cost, a
# risk, or a failure rate. The request named Challenge 400, Standard 500 and
# Relaxed "600-700"; 650 is the middle of that range, still a single whole
# number because the engine only ever took one. Endless is not a bigger
# number wearing a disguise - see ENDLESS_HORIZON_YEARS below for exactly
# what it is and is not.
# CHALLENGE'S NOTE NO LONGER QUOTES THE DICE-FREE FLOOR, AND MUST NOT. It used
# to say 400 years was "short of the measured dice-free floor for at least one
# civilisation ... means playing better than the unlucky-proof plan", pointing
# at DICE_FREE_FLOOR_YEARS above. Every word of that was true about the
# instrument and false as advice: a player reading it concludes Rome cannot be
# won in 400 years, and a player has since reached the same Rome goal's
# startable point in 334 years (playtest/fixtures/
# rome_434_goal_startable.json) under fog, on a second attempt, with the
# point-contact transistor failing six times in a row. 1,019 is not a floor
# under play, it is one policy's ceiling - see DICE_FREE_FLOOR_YEARS' own
# comment and PATH_SEARCH.md section 4. The note says what the setting is for
# instead, and the only per-goal number a player is given in this wizard is
# critical_path's, computed for the goal they actually picked.
# (key, label, years-or-None, one-line description)
HORIZON_MODES = (
    ("challenge", "Challenge", 400,
     "a tight run - enough calendar for the transistor if you play well, "
     "with little room left over for bad luck"),
    ("standard", "Standard", 500,
     "the game's own long-standing default"),
    ("relaxed", "Relaxed", 650,
     "room to recover from genuinely bad luck"),
    ("endless", "Endless", None,
     "no deadline at all - play until you choose to stop"),
)

# WHAT "ENDLESS" ACTUALLY IS: a very large, ordinary, finite number of years,
# not a true absence of one. A save file, `state`'s own JSON reply, and every
# bit of arithmetic anywhere in this engine that reads a horizon
# (`end_year - year`, `start_year + horizon_years`, and so on) expects a
# plain number, never `None` or infinity - and this file is not the place to
# teach all of those call sites a special "no limit" value, several of which
# live in protocol.py. 9,999 years is the answer instead: an order of
# magnitude past the longest dice-free floor measured for any civilisation
# above (1,019, for Rome) and further past that than any real game has ever
# been played, so nobody playing an actual game reaches it - which is the
# only property "endless" needs to have in practice. `run`/`compare`/`plan`
# and flag-driven `play`/`agent` never see this constant at all: it is
# reached only from the New Game wizard and the in-game 'options' command
# choosing it explicitly, never from a bare --horizon flag, whose own
# argparse default (500) is completely unchanged by any of this.
ENDLESS_HORIZON_YEARS = 9999


def _is_endless_horizon(end_year, start_year):
    """Whether an end_year amounts to the Endless mode above, for display
    purposes only - nothing about how the game actually runs checks this;
    it only decides whether a screen says 'no deadline' or a specific year."""
    return (end_year - start_year) >= ENDLESS_HORIZON_YEARS


def load_strategy(name, nodes, goal):
    # A NAME OR A PATH. --save-winner writes a strategy file wherever you ask it
    # to, and there was no way to read one back: this looked only inside the
    # strategies directory for name + ".json", so the captured order of a run
    # that actually reached the goal could be written and never used.
    path = os.path.join(STRATS, str(name) + ".json")
    if not os.path.exists(path) and os.path.exists(str(name)):
        path = str(name)
    if os.path.exists(path):
        strategy_data = json.load(open(path))
        order = [node_id for node_id in strategy_data["order"] if node_id in nodes]
        # Everything the strategy did not name gets a sensible default ordering:
        # things the goal needs first, then cheapest first. Falling
        # back to alphabetical order made the simulation spend a century acquiring
        # ox carts before it touched a furnace.
        # FROM THE TREE, NOT SPELLED OUT HERE. This named the goal by hand, so
        # when the win condition moved from the 1947 point-contact device to the
        # 1951 junction transistor, the ordering that decides what an unnamed
        # node is worth would have gone on ranking against the old one for ever,
        # silently and with nothing failing.
        need = closure(nodes, goal)
        rest = [node_id for node_id in nodes if node_id not in order]
        rest.sort(key=lambda k: (k not in need, nodes[k]["_total_cost"], k))
        # STABILISE THE WHOLE THING TOGETHER, not the two halves separately.
        # Sorting `rest` on its own left 681 places where a node preceded its
        # own prerequisite, because a node in `rest` knows nothing about where
        # in `order` its prerequisites sit (and the strategy's own list is not
        # perfectly ordered either: soap_hard is listed before potash_soda,
        # which it needs). One pass over the concatenation keeps the strategy's
        # preference wherever it is legal and repairs it where it is not.
        full = topo_stable(nodes, order + rest)
        return strategy_data.get("label", name), full, set(strategy_data.get("bounties", []))
    if name == "topo":
        need = closure(nodes, goal)
        order = topo_order(nodes, need)
        return ("bare topological order to the goal",
                order + [node_id for node_id in topo_order(nodes) if node_id not in need], set())
    if name == "cheapest":
        order = sorted(nodes, key=lambda k: nodes[k]["_total_cost"])
        return "cheapest first", topo_stable(nodes, order), set()
    raise SystemExit("unknown strategy: %s" % name)


def topo_stable(nodes, preference, already=()):
    """Reorder `preference` so no node precedes its prerequisites, disturbing
    the given order as little as possible.

    `already`: nodes that are ALREADY ahead of this list and must count as
    placed. Omitting a node from `already` that is genuinely ahead of this
    list is a serious and completely invisible bug: if a strategy names
    some nodes explicitly and sorts everything else goal-critical-first,
    handing this function that remainder WITHOUT telling it about the
    explicit nodes means every node whose prerequisites live in the
    explicit list can never satisfy `all(p in placed)`, falls through to
    the bulk dump below, and loses its place entirely - a cheap,
    goal-critical node can end up hundreds of places later than it belongs,
    starving the optimizer of work it needed early.
    """
    placed = set(already)
    out = []
    pref = list(preference)
    # hard_pre, NOT nodes[k]["pre"]: this function decides the order the
    # engine actually receives, and a req_any group with exactly one real
    # option is a prerequisite, not a choice - reading `pre` alone here
    # could place a node like mat_bulk_steel ahead of mat_manganese even
    # though mat_bulk_steel cannot actually be built without it.
    hard_pre_by_node = {node_id: hard_pre(nodes, node_id) for node_id in pref}
    # Index the dependants so each placement only revisits what it could free,
    # rather than rescanning the whole list: a list.remove() inside a scan of
    # the whole list is O(n^2) over 2,700 nodes.
    waiting = {}
    ready = []
    for node_id in pref:
        missing = sum(1 for prereq_id in hard_pre_by_node[node_id] if prereq_id not in placed)
        waiting[node_id] = missing
        if not missing:
            ready.append(node_id)
    dependants = {}
    inset = set(pref)
    for node_id in pref:
        for prereq_id in hard_pre_by_node[node_id]:
            if prereq_id in inset:
                dependants.setdefault(prereq_id, []).append(node_id)
    rank = {node_id: i for i, node_id in enumerate(pref)}
    import heapq
    heap = [(rank[node_id], node_id) for node_id in ready]
    heapq.heapify(heap)
    seen = set()
    while heap:
        _rank, node_id = heapq.heappop(heap)
        if node_id in seen:
            continue
        seen.add(node_id)
        out.append(node_id)
        placed.add(node_id)
        for dependent_id in dependants.get(node_id, ()):
            waiting[dependent_id] -= 1
            if waiting[dependent_id] == 0 and dependent_id not in seen:
                heapq.heappush(heap, (rank[dependent_id], dependent_id))
    # Anything genuinely unreachable (a prerequisite outside both lists) keeps
    # its preferred order rather than being dropped.
    if len(out) < len(pref):
        out.extend(node_id for node_id in pref if node_id not in seen)
    return out


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

# HOW LONG THE `validate --deep` REACHABILITY PROBE RUNS, per goal. Longer
# than the structural critical-path floor because a probe with no search-
# rounds relaxation (see cmd_validate's own comment on this) needs slack to
# actually reach a goal it structurally can, but capped because this runs one
# real Sim trial per goal per civilisation and a menu-adjacent command has to
# stay fast. Balances thoroughness against runtime; not derived from
# anything about the tree or the civilisations it probes.
VALIDATE_DEEP_PROBE_HORIZON_YEARS_PER_FLOOR_YEAR = declare(
    "VALIDATE_DEEP_PROBE_HORIZON_YEARS_PER_FLOOR_YEAR", 2.5,
    kind="temporary_heuristic", unit="probe years per critical-path floor year",
    source=None, confidence="D",
    why="How much slack over the structural critical-path floor the "
        "reachability probe gets before it is declared 'not reached'. A "
        "real trial needs more calendar time than the floor (which assumes "
        "every roll goes right and no year is ever spent short of money, "
        "people or material - see critical_path's own docstring), and 2.5x "
        "was picked to give a CPM-ordered, dice-free trial room to actually "
        "finish without the probe running long. A real mechanism would "
        "measure how much slack a CPM order typically needs over its floor, "
        "goal by goal, instead of applying one ratio to all of them.")
VALIDATE_DEEP_PROBE_HORIZON_MIN_YEARS = declare(
    "VALIDATE_DEEP_PROBE_HORIZON_MIN_YEARS", 50, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Floor under the scaled probe horizon above, for a goal whose "
        "critical path is very short - so a five-year-floor lifetime goal "
        "still gets a probe window long enough to build anything around it, "
        "rather than being cut off almost immediately. Picked to feel "
        "sufficient, not measured against how long the shortest goals "
        "actually take under real play.")
VALIDATE_DEEP_PROBE_HORIZON_MAX_YEARS = declare(
    "VALIDATE_DEEP_PROBE_HORIZON_MAX_YEARS", 350, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Ceiling on the scaled probe horizon above, so a goal with a long "
        "critical-path floor (the transistor's own structural floor runs "
        "well past a century) does not turn this structural-checks command "
        "into a multi-minute run - see this command's own comment on why "
        "--deep is opt-in at all. Picked for speed, not because 350 years "
        "is a meaningful ceiling on what a real trial might need.")


def _check_node_prereqs(node_id, node_record, nodes):
    errs = []
    for prereq_id in node_record["pre"]:
        if prereq_id not in nodes: errs.append("%s: unknown prereq %s" % (node_id, prereq_id))
    return errs


def _check_node_materials(node_id, node_record, goods):
    errs = []
    for material_id in node_record["mat"]:
        if material_id not in goods: errs.append("%s: unpriced material %s" % (node_id, material_id))
    return errs


def _check_node_trades(node_id, node_record, wages):
    errs = []
    for trade_id in node_record["lab"]:
        if trade_id not in wages: errs.append("%s: unknown trade %s" % (node_id, trade_id))
    return errs


def _check_node_risk(node_id, node_record):
    errs = []
    if not 0 <= node_record["risk"] <= 1: errs.append("%s: risk out of range" % node_id)
    return errs


def _check_node_confidence(node_id, node_record):
    warns = []
    if node_record["conf"] not in "ABC": warns.append("%s: odd confidence %s" % (node_id, node_record["conf"]))
    return warns


def _check_node_required_fields(node_id, node_record):
    # A `why` on seven hand-written nodes killed the process with KeyError
    # 'sus' because I added them without the v1 scalars the explain path
    # still reads. Catch a missing field here, where it is a warning, rather
    # than in a player's session, where it is the end of their game.
    errs = []
    for field_name in ("sus", "gov", "cat", "pre", "ph", "cap", "up", "risk"):
        if field_name not in node_record:
            errs.append("%s: missing required field '%s'" % (node_id, field_name))
    return errs


def _validate_nodes(nodes, goods, wages):
    """Run every per-node check and gather what each one finds. One function
    per check, so a check that finds nothing just contributes nothing -
    nobody has to remember to guard the call site."""
    errs, warns = [], []
    for node_id, node_record in nodes.items():
        errs += _check_node_prereqs(node_id, node_record, nodes)
        errs += _check_node_materials(node_id, node_record, goods)
        errs += _check_node_trades(node_id, node_record, wages)
        errs += _check_node_risk(node_id, node_record)
        warns += _check_node_confidence(node_id, node_record)
        errs += _check_node_required_fields(node_id, node_record)
    return errs, warns


def _validate_topo_order(nodes):
    try:
        topo_order(nodes)
    except RuntimeError as error:
        return [str(error)]
    return []


def _validate_goal_rows(tree, nodes):
    # EVERY SELECTABLE GOAL, not just the default. meta.goals is the single
    # roster `goals`, the new-game wizard and every --goal flag all read
    # (see data.py's goal_catalog/resolve_goal) - a goal naming a node that
    # does not exist would not fail anywhere else until a player actually
    # picked it, which is exactly the kind of bug this command exists to
    # catch before that.
    errs = []
    default_goal = tree["meta"]["goal_node"]
    if default_goal not in nodes:
        errs.append("meta.goal_node %r does not exist" % default_goal)
    catalog = goal_catalog(tree)
    goal_rows = []
    for goal in catalog:
        node = goal.get("node")
        if node not in nodes:
            errs.append("meta.goals: %r names a node that does not exist" % node)
            continue
        need = closure(nodes, node)
        yrs, chain = critical_path(nodes, node)
        goal_rows.append((goal, node, need, yrs, chain))
    return errs, default_goal, goal_rows


def _print_validate_summary(nodes, goal_rows, default_goal):
    print("nodes            : %d" % len(nodes))
    print("edges            : %d" % sum(len(node_record["pre"]) for node_record in nodes.values()))
    print("total capital     : %s den across all %d nodes" % (f"{sum(node_record['_total_cost'] for node_record in nodes.values()):,.0f}", len(nodes)))
    print("total founder hrs : %s" % f"{sum(node_record['ph'] for node_record in nodes.values()):,}")
    print()
    print("GOALS (%d selectable; 'goals' prints this table alone)" % len(goal_rows))
    print("%-34s %9s %10s  %s" % ("name", "closure", "floor(yr)", "node"))
    print("-" * 90)
    for goal, node, need, yrs, chain in goal_rows:
        print("%-34s %9d %10.1f  %s%s"
              % (goal.get("name", node)[:34], len(need), yrs, node,
                 "  <- DEFAULT" if node == default_goal else ""))
    print()


def _print_validate_findings(errs, warns):
    if errs:
        print("ERRORS:"); [print("  " + message) for message in errs]
    if warns:
        print("WARNINGS:"); [print("  " + message) for message in warns]


def _validate_reachability(args, errs, nodes, goal_rows):
    # REACHABILITY, PER CIVILISATION - opt in with --deep, because this runs
    # a real dice-free Sim (see path_search.deterministic_sim) once per
    # civilisation for every goal above, and that is seconds of real work
    # per trial rather than the instant structural checks above it. A lower
    # bound, not a verdict: this is one CPM-ordered trial with no search-
    # rounds relaxation, the same "does the straightforward plan even get
    # there" question path_search.py's own module docstring asks of the
    # transistor itself - a goal this reports as "not reached" may still be
    # reachable with a smarter order (see plan --search-rounds) or more
    # calendar time than the capped probe horizon below allows.
    if getattr(args, "deep", False) and not errs:
        print()
        print("REACHABILITY (dice-free, immortal, one CPM-ordered trial per "
              "civilisation, capped horizon - a lower bound, see above)")
        _simdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _simdir not in sys.path:
            sys.path.insert(0, _simdir)
        import planner as _planner
        from path_search import deterministic_sim
        civ_ids = sorted(filename[:-5] for filename in os.listdir(CIVDIR)
                         if filename.endswith(".json") and not filename.startswith("_"))
        for goal, node, need, yrs, chain in goal_rows:
            probe_horizon = min(VALIDATE_DEEP_PROBE_HORIZON_MAX_YEARS,
                                max(VALIDATE_DEEP_PROBE_HORIZON_MIN_YEARS,
                                    int(math.ceil(yrs * VALIDATE_DEEP_PROBE_HORIZON_YEARS_PER_FLOOR_YEAR))))
            cells = []
            for civ in civ_ids:
                probe_sim = Sim(nodes, [], random.Random(1), events=False, civ=load_civ(civ))
                order, cost, extras, staffing = _planner.backward_plan(
                    nodes, node, probe_sim, side_branches=12, side_branch_every=8)
                full = _planner._repaired(nodes, node, order)
                probe_result = deterministic_sim(nodes, full, node, civ, probe_horizon)
                cells.append("%s: %s" % (civ, ("%d AD" % probe_result.goal_year) if probe_result.goal_year
                                         else "not within %dy" % probe_horizon))
            print("  %-30s %s" % (goal.get("name", node)[:30], "  |  ".join(cells)))


def _print_validate_ok(errs):
    if not errs:
        print()
        print("OK: tree is a valid DAG, fully priced, every selectable goal's "
              "closure and critical path compute cleanly.")


def cmd_validate(args):
    tree, prices, nodes, wages, goods = load()
    errs, warns = _validate_nodes(nodes, goods, wages)
    errs += _validate_topo_order(nodes)
    goal_errs, default_goal, goal_rows = _validate_goal_rows(tree, nodes)
    errs += goal_errs

    _print_validate_summary(nodes, goal_rows, default_goal)
    _print_validate_findings(errs, warns)
    _validate_reachability(args, errs, nodes, goal_rows)
    _print_validate_ok(errs)
    return 1 if errs else 0


# Complaints/38: A FOUNDER'S WHOLE WORKING LIFE, IN HOURS - used only to say
# how big a number is, never to gate anything a player can actually do
# (neither cmd_path nor cmd_why stops a player starting a project past this
# many hours; this is a claim made TO the player, not a rule enforced on
# them). USED to be a separately typed 72,000, two lines below a SEPARATE
# printed sentence deriving 60,000 from "2000/yr for 30 yrs" - both wrong,
# because both were literals and DEFAULTS["founder_hours_per_year"] is DATA a
# civilisation can set (see that field's own "2,000, NOT 2,400" comment for
# why it moved off the 2,400 that made 72,000 exact). Typing a corrected
# 60,000 in its place would only move the drift, not close it: if a scenario
# ever sets founder_hours_per_year (or the expected working-life figure
# below) to something else, a typed number is wrong again the moment it
# does.
#
# So there is no typed lifetime figure any more. `_founder_lifetime_hours()`
# computes it from the same two DEFAULTS entries the rest of the engine
# reads for exactly this founder: `founder_hours_per_year` (how many hours a
# year the founder works, same figure a hired man is paid by) and
# `founder_life_mean` (the founder's EXPECTED REMAINING WORKING LIFE IN
# YEARS - not a new "expected working years" invented for this print
# statement, but the existing DEFAULTS entry core.py itself uses as the mean
# of the founder's mortality draw: "founder remaining lifespan, elite male
# already aged 35", see core.py's `life_left`). Multiplying those two must
# go through one function, not be duplicated separately at each print
# site: cmd_path's printed budget, cmd_path's feasibility judgement and
# cmd_why's "% of a life" figure all call this one function, so whatever
# DEFAULTS says, they cannot say two different things about it.
#
# (2,000 * 28 = 56,000 today. This is not a hardcoded literal because a
# literal drifts the moment DEFAULTS changes, and the drift is easy to get
# wrong even when "fixed" by hand: 28 years is the figure the mortality
# model actually uses for founder_life_mean, not a round 30 a hand-typed
# literal might use instead.)
def _founder_lifetime_hours(cfg=None):
    """Founder-hours a whole working life holds: hours/year * expected
    working years, both read from `cfg` if given (a live Sim's config, which
    may override either) and otherwise from DEFAULTS - the same source
    core.py reads `founder_hours_per_year` and `founder_life_mean` from for
    the founder's real hours ledger and real mortality draw. No caller of
    this function may re-derive or re-type either input: that duplication
    is exactly what lets two figures that should agree drift apart.
    """
    cfg = cfg or {}
    hours_per_year = cfg.get("founder_hours_per_year", DEFAULTS["founder_hours_per_year"])
    expected_working_years = cfg.get("founder_life_mean", DEFAULTS["founder_life_mean"])
    return hours_per_year * expected_working_years


def cmd_path(args):
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, args.goal)
    need = closure(nodes, goal)
    order = topo_order(nodes, need)
    cum_cost = cum_ph = 0.0
    print("%-4s %-39s %8s %9s %6s %5s %5s" %
          ("#", "node", "yourhrs", "cost(den)", "years", "risk", "conf"))
    print("-" * 88)
    for i, node_id in enumerate(order, 1):
        node_record = nodes[node_id]
        cum_cost += node_record["_total_cost"]; cum_ph += node_record["ph"]
        print("%-4d %-39s %8d %9s %6.1f %5.2f %5s" %
              (i, node_id[:39], node_record["ph"], f"{node_record['_total_cost']:,.0f}", node_record["yrs"], node_record["risk"], node_record["conf"]))
    print("-" * 88)
    print("TOTAL  %d nodes   %s founder-hours   %s denarii" %
          (len(order), f"{cum_ph:,.0f}", f"{cum_cost:,.0f}"))
    yrs, chain = critical_path(nodes, goal)
    print("\nLongest serial chain (%.1f yr floor, cannot be bought down with money):" % yrs)
    for node_id in chain:
        print("   -> %s  (%.1f yr floor, %d your-hrs)" % (node_id, nodes[node_id]["yrs"], nodes[node_id]["ph"]))
    # Complaints/38: the printed budget and the feasibility judgement below
    # both come from one call (_founder_lifetime_hours), so they say the
    # same thing about the same DEFAULTS whatever those are.
    lifetime_hours = _founder_lifetime_hours()
    print("\nFounder-hours available in one lifetime at %s/yr for %s yrs: %s" %
          (f"{DEFAULTS['founder_hours_per_year']:,.0f}",
           f"{DEFAULTS['founder_life_mean']:,.0f}",
           f"{lifetime_hours:,.0f}"))
    print("Founder-hours demanded by this path                          : %s" % f"{cum_ph:,.0f}")
    print("=> %s" % ("feasible alone in principle, but not with the calendar floors"
                     if cum_ph < lifetime_hours else
                     "IMPOSSIBLE for one person. You must convert your hours into other people's hours."))


def cmd_costs(args):
    tree, prices, nodes, wages, goods = load()
    rows = sorted(nodes.values(), key=lambda n: -n["_total_cost"])[:args.top]
    print("%-34s %10s %10s %10s %8s %6s" % ("node", "labour", "materials", "capital", "TOTAL", "rev/yr"))
    print("-" * 84)
    for node_record in rows:
        print("%-34s %10s %10s %10s %8s %6s" % (
            node_record["id"][:34], f"{node_record['_labour_cost']:,.0f}", f"{node_record['_material_cost']:,.0f}",
            f"{node_record['cap']:,.0f}", f"{node_record['_total_cost']:,.0f}", f"{node_record['rev']:,}"))
    print()
    prof = sorted([node_record for node_record in nodes.values() if node_record["rev"]], key=lambda n: -(n["rev"] / max(n["_total_cost"], 1)))
    print("Best return on capital (revenue per denarius of setup cost):")
    for node_record in prof[:12]:
        print("  %-32s %6.2f  (rev %s / cost %s)" %
              (node_record["id"][:32], node_record["rev"] / max(node_record["_total_cost"], 1), f"{node_record['rev']:,}", f"{node_record['_total_cost']:,.0f}"))


_Z95 = 1.959963984540054  # two-sided 95% normal quantile, to stdlib float precision


def _wilson_interval(successes, trial_count, z_score=_Z95):
    """95% (by default) Wilson score confidence interval for a binomial rate.

    NOT the textbook p +/- z*sqrt(p(1-p)/n) normal-approximation interval.
    That formula is built on a normal approximation to the binomial that
    breaks down exactly where this tool lives: when p is small and n is a few
    dozen trials, it can and does return a negative lower bound - a
    "confidence interval" that includes impossible, negative probabilities.
    An audit of this simulator's default invocation found success rates of
    0/25 and 1/125; the normal approximation is not fit to report on either
    one. Wilson's interval inverts the actual binomial test statistic instead
    of a Gaussian stand-in for it, so it stays inside [0, 1] everywhere,
    including at p=0 and p=1, and is the standard textbook fix for this exact
    failure mode (see e.g. Agresti & Coull 1998). Stdlib-only: math.sqrt.
    """
    if trial_count <= 0:
        return (0.0, 1.0)
    rate = successes / trial_count
    z_squared = z_score * z_score
    denom = 1.0 + z_squared / trial_count
    centre = rate + z_squared / (2 * trial_count)
    margin = z_score * math.sqrt((rate * (1.0 - rate) + z_squared / (4 * trial_count)) / trial_count)
    lower = (centre - margin) / denom
    upper = (centre + margin) / denom
    return (max(0.0, lower), min(1.0, upper))


def _fmt_rate_ci(successes, trial_count):
    """'k/n (p%)  95% CI [lo%, hi%]' - the point estimate never appears alone
    anywhere in this file's output. A bare percentage from a few dozen
    Monte Carlo trials invites a reader to treat it as a measurement with no
    error bar, which is exactly the failure this function exists to close."""
    lower, upper = _wilson_interval(successes, trial_count)
    rate = 100.0 * successes / trial_count if trial_count else 0.0
    return ("%d/%d (%.1f%%)  95%% CI [%.1f%%, %.1f%%] (Wilson score)"
            % (successes, trial_count, rate, 100.0 * lower, 100.0 * upper))


# How few successes is too few to trust a median/quartile year-to-goal? There
# is no sharp cutoff, but under ~10 the order statistics are individual data
# points wearing a statistic's clothing - a "median" of 1 or 3 observations
# is just one of those observations, arbitrarily labelled. Below this, print
# the raw values and say so, instead of a quartile table that implies a
# distribution nobody has actually sampled.
_MIN_SUCCESSES_FOR_QUANTILES = 10


def _summarise_header(label, run_count):
    print("\n=== %s ===" % label)
    print("runs                : %d" % run_count)
    # WHAT THIS COMMAND ACTUALLY MEASURES, SAID ONCE, UP FRONT, BEFORE ANY
    # NUMBER. `--mc N` re-rolls ONE FIXED strategy order against N different
    # random event sequences and reports how that order coped; it has never
    # chosen or improved the order, and does not here either - see
    # planner.py's own docstring for the full argument (recommended.json:
    # 0% on Rome at a 700-year horizon; a computed order: 100%, same tree,
    # same civilisation, the entire difference being ordering). 'plan' and
    # 'search' are the commands that compute an order; this one only tells
    # you how the order it was handed holds up.
    print("this measures ONE FIXED order's luck, %d roll%s of it - it does not "
          "choose or improve the order. 'plan' (critical-path method) and "
          "'search' (dice-free, relaxed against the binding constraint) are "
          "the commands that do that."
          % (run_count, "" if run_count == 1 else "s"))


def _summarise_tech_completed(results, run_count, quantile_of):
    # AGGREGATE PROGRESS, LEADING - not the success rate. A batch this small
    # against a multi-century, near-certain-to-fail-or-succeed goal can be a
    # ~1% event either way (this project's own default invocation has
    # measured 0/25 and 1/125), and a bare rate at that sample size invites
    # reading it as "the" result instead of one thing among several this
    # batch can actually support saying. How far every run got - not only
    # the ones that finished - is informative at any N, including this one.
    tech = sorted(len(run.done) for run in results)
    print()
    print("technologies completed (whole tree, across all %d run%s):"
          % (run_count, "" if run_count == 1 else "s"))
    print("   worst %d | p25 %d | median %d | p75 %d | best %d"
          % (tech[0], quantile_of(tech, .25), quantile_of(tech, .5), quantile_of(tech, .75), tech[-1]))


def _summarise_goal_closure(results, quantile_of):
    need = closure(results[0].nodes, results[0].goal)
    needed_count = len(need)
    progress = sorted(len(need & run.done) for run in results)
    print("goal's own closure completed (%d node%s needed):"
          % (needed_count, "" if needed_count == 1 else "s"))
    print("   worst %d/%d | p25 %d | median %d | p75 %d | best %d/%d"
          % (progress[0], needed_count, quantile_of(progress, .25), quantile_of(progress, .5), quantile_of(progress, .75),
             progress[-1], needed_count))


def _summarise_failure_modes(results):
    causes = defaultdict(int)
    for run in results:
        if run.dead_reason: causes[run.dead_reason.split(":")[0]] += 1
        elif not run.goal_year: causes["ran out of horizon"] += 1
    if causes:
        print("failure modes       :")
        for cause, value in sorted(causes.items(), key=lambda x: -x[1]):
            print("   %-58s %3d (%.0f%%)" % (cause, value, 100.0 * value / len(results)))


def _summarise_stuck_nodes(results):
    # where do runs get stuck. PRECISE EVEN AT N=25: almost every run that
    # does not reach the goal is blocked on one of a small handful of nodes,
    # which is a near-certain event rather than the ~1% one the success rate
    # itself often is - see the rate section below for that distinction said
    # out loud where a reader is looking at both numbers side by side.
    stuck = defaultdict(int)
    for run in results:
        if not run.goal_year:
            run_need = closure(run.nodes, run.goal)
            missing_nodes = [node_id for node_id in topo_order(run.nodes, run_need) if node_id not in run.done]
            if missing_nodes: stuck[missing_nodes[0]] += 1
    if stuck:
        print("first blocked node  :")
        for node_id, value in sorted(stuck.items(), key=lambda x: -x[1])[:6]:
            print("   %-58s %3d" % (node_id, value))


def _summarise_success_rate(label, run_count, success_count):
    # THE SUCCESS RATE, BELOW THE FOLD, NOT AS THE HEADLINE - see the "what
    # this measures" line above for why. A lone, uninterpreted "0%" printed
    # as a headline, with nothing else on the screen to explain it, reads as
    # the goal being unreachable rather than as one order's bad luck under
    # one horizon. The progress tables above already say how far those same
    # trials got; this says how many of them finished.
    print()
    if success_count == 0:
        # DO NOT SILENTLY PRINT A TABLE OF ZEROS. Zero successes out of N is
        # a statement about THIS ORDER's luck under THIS horizon, not a
        # verdict on the goal - recommended.json scores exactly this at a
        # 500-700 year horizon while a computed order has reached 100%, same
        # tree, same civilisation. Re-running this same order with a
        # different --seed will not change that; a different ORDER might.
        print("*** ZERO of %d trials reached the goal under this order. ***" % run_count)
        print("    Before reading anything below as a verdict on the GOAL: this is a")
        print("    known losing order at this horizon, not evidence the goal is out of")
        print("    reach. 'plan' (critical-path method) or 'search' (dice-free, relaxed")
        print("    against the binding constraint) compute a different order instead of")
        print("    re-testing this one against more luck.")
    print("reached the goal    : %s" % _fmt_rate_ci(success_count, run_count))
    # --no-events IS NOT A NOISE-FREE BASELINE. See the --no-events help text
    # for the full explanation; this is the one-line reminder at the point
    # where a reader is actually looking at numbers from such a run.
    if "[events disabled]" in label:
        print("                      NOTE: '--no-events' turns off weather/plague/")
        print("                      political hazards only. Project-failure rolls")
        print("                      (projects.py _complete) and fractional-headcount")
        print("                      rounding (labour.py _stochastic_round) still draw")
        print("                      from the same RNG regardless of this flag, so this")
        print("                      batch still has real seed-to-seed variance - it is")
        print("                      reproducible for one seed, not noise-free. See")
        print("                      --deterministic for a run where that is also true.")
    if "[deterministic]" in label and run_count > 1:
        print("                      NOTE: '--deterministic' replaces the rng with one")
        print("                      that always rolls the side that never fails, so")
        print("                      every one of these %d trials is identical - there"
              % run_count)
        print("                      is no luck left for more trials to re-roll. This")
        print("                      is the order's single dice-free outcome, repeated.")


def _summarise_year_reached(results, finished, success_count, run_count):
    if success_count == 0:
        pass  # already said above, plainly, before the rate line itself
    elif success_count < _MIN_SUCCESSES_FOR_QUANTILES:
        years_reached = sorted(run.goal_year for run in finished)
        print("year reached        : only %d success%s in %d trials - too few for a"
              % (success_count, "" if success_count == 1 else "es", run_count))
        print("                      median/quartiles; that would just relabel a")
        print("                      handful of individual runs as a distribution.")
        print("                      observed year%s: %s"
              % ("" if success_count == 1 else "s", ", ".join(str(year) for year in years_reached)))
        print("                      trust the CI on the rate above instead.")
    else:
        years_reached = sorted(run.goal_year for run in finished)
        year_at_percentile = lambda p: years_reached[min(len(years_reached) - 1, int(p * len(years_reached)))]
        print("year reached        : best %d | p25 %d | median %d | p75 %d | worst %d"
              % (years_reached[0], year_at_percentile(.25), year_at_percentile(.5), year_at_percentile(.75), years_reached[-1]))
        start = results[0].cfg["start_year"]
        print("elapsed from %d AD  : median %d years" % (start, year_at_percentile(.5) - start))


def _summarise_shortages(results, run_count):
    shortage_counter = collections.Counter()
    for run in results:
        shortage_counter.update(run.shortages)
    if shortage_counter:
        # RELABELLED, NOT RECOMPUTED: this is a SUM across every run, not a
        # median of anything, so the label must say so. A true per-material
        # median across runs would need each run's count (including runs
        # that were never short of that material at all, i.e. zero) aligned
        # key by key, which is a real change to what gets computed, not
        # just what gets printed - out of scope here.
        print("years spent short of a raw material (SUM across %d runs, not a median):" % run_count)
        for material, value in shortage_counter.most_common(5):
            print("   %-12s %d run-years" % (material, value))


def _summarise_misc_stats(results):
    forest_hectares = sorted(run.forest_ha for run in results)
    print("coppice woodland owned: median %.0f hectares" % forest_hectares[len(forest_hectares) // 2])
    reputations = sorted(run.reputation for run in results)
    print("final reputation    : median %.0f/100" % reputations[len(reputations) // 2])
    bounty_payments = [run.bounties_paid for run in results]
    if any(bounty_payments):
        print("bounties posted     : mean %.1f per run" % (sum(bounty_payments) / len(bounty_payments)))


def _summarise(results, label):
    run_count = len(results)
    finished = [run for run in results if run.goal_year]
    success_count = len(finished)
    quantile_of = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]
    _summarise_header(label, run_count)
    _summarise_tech_completed(results, run_count, quantile_of)
    _summarise_goal_closure(results, quantile_of)
    _summarise_failure_modes(results)
    _summarise_stuck_nodes(results)
    _summarise_success_rate(label, run_count, success_count)
    _summarise_year_reached(results, finished, success_count, run_count)
    _summarise_shortages(results, run_count)
    _summarise_misc_stats(results)


def _run_trials(nodes, order, bounties, goal, args, deterministic):
    """Run args.mc trials of Sim under the strategy already loaded by the
    caller, and return their results in trial order."""
    res = []
    for i in range(args.mc):
        rng = DetRNG(args.seed + i) if deterministic else random.Random(args.seed + i)
        run_result = Sim(nodes, order, rng, events=not args.no_events,
                cfg={"immortal": not args.mortal,
                     "start_capital": STARTING_KITS[args.kit]["den"]},
                civ=load_civ(args.civ),
                bounty_set=(set() if args.no_bounties else bounties)).run(goal, args.horizon)
        res.append(run_result)
    return res


# KEEP THE PATH OF A RUN THAT WORKED. When a trial reaches the goal it
# proves an order of work that gets there in this civilisation, and the
# engine threw that away and went back to walking the same fixed list from
# recommended.json on the next invocation. A whole day of balance work in
# this project was spent measuring a strategy that loses while runs that won
# were being discarded unread.
#
# The order is done_year, not done_in_order(): what matters for a strategy
# is the sequence the work was FINISHED in, which is the sequence a player
# would have to start it in. Granted technologies are dropped because they
# are not choices anybody made, and ties within a year are broken by id so
# the file is reproducible.
def _save_winning_order(res, nodes, goal, args):
    won = [run_result for run_result in res if run_result.goal_year]
    if not won:
        sys.stderr.write("no trial reached the goal, so there is no winning "
                         "order to save\n")
        return
    best = min(won, key=lambda s: s.goal_year)
    # ONLY WHAT THE GOAL NEEDS: the goal's closure, not every node the
    # winning trial finished. Saving every node a winning trial finished and
    # feeding that back as a strategy would let the optimizer grind through
    # hundreds of side branches the trial built for revenue before it
    # reached the work that mattered - a finish order over everything is
    # not a plan. The nodes of the goal's closure, in the order a run that
    # won actually completed them, is.
    _need = closure(nodes, goal)
    seq = sorted((node_id for node_id in best.done
                  if node_id in _need and node_id not in best.granted),
                 key=lambda k: (best.done_year.get(k, 0), k))
    out = {"label": "CAPTURED: the order a run that reached the goal in "
                    "%d AD actually finished its work in" % best.goal_year,
           "rationale": [
               "Not designed. Observed: trial seed %d of a --mc %d run on "
               "%s reached %s in %d AD, and this is the sequence it "
               "finished things in."
               % (args.seed + res.index(best), args.mc, args.civ, goal,
                  best.goal_year),
               "A captured order is a floor on what is achievable, not a "
               "recommendation: it carries whatever luck that trial had, "
               "and it includes side branches that trial happened to "
               "build and may not have needed."],
           "order": seq}
    with open(args.save_winner, "w") as save_file:
        json.dump(out, save_file, indent=1)
    sys.stderr.write("saved the winning order (%d nodes, goal in %d AD) "
                     "to %s\n" % (len(seq), best.goal_year, args.save_winner))


def _print_run_trace(res):
    run_result = res[0]
    print("\n--- trace of run 0 ---")
    for year, message in run_result.log:
        print("  %4d  %s" % (year, message))


def cmd_run(args):
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(args, "goal", None))
    label, order, bounties = load_strategy(args.strategy, nodes, goal)
    deterministic = getattr(args, "deterministic", False)
    res = _run_trials(nodes, order, bounties, goal, args, deterministic)
    _summarise(res, "%s%s%s" % (label,
                                "  [events disabled]" if args.no_events else "",
                                "  [deterministic]" if deterministic else ""))
    if getattr(args, "save_winner", None):
        _save_winning_order(res, nodes, goal, args)
    if args.trace:
        _print_run_trace(res)


def cmd_compare(args):
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(args, "goal", None))
    for name in ["rush", "topo", "recommended"]:
        try:
            label, order, bounties = load_strategy(name, nodes, goal)
        except SystemExit:
            continue
        # At 3000 nodes a full comparison takes tens of minutes. Without this
        # line, and without the flushes below, the command looks hung: stdout
        # is block-buffered when redirected, so nothing at all appeared until
        # the very end.
        sys.stderr.write("  running %s: %d trials...\n" % (name, args.mc))
        sys.stderr.flush()
        # COMMON RANDOM NUMBERS, ON PURPOSE. random.Random(args.seed + i) is
        # reseeded identically for trial i under EVERY strategy in this loop,
        # so "rush" trial 7 and "recommended" trial 7 see the same weather,
        # the same plagues, the same project-failure rolls - only the order
        # of work differs. That is what lets a difference between strategies'
        # outcomes be attributed to the strategy instead of to which one
        # happened to draw the luckier seeds; it is the textbook variance-
        # reduction technique of the same name, not a bug. cmd_sweep and
        # cmd_sensitivity do the same thing for the same reason. DO NOT
        # "fix" this by drawing a fresh, unseeded RNG per strategy - that
        # would look more random and measure less: it would reintroduce the
        # between-strategy noise this line exists to cancel out.
        deterministic = getattr(args, "deterministic", False)
        res = [Sim(nodes, order,
                   DetRNG(args.seed + i) if deterministic else random.Random(args.seed + i),
                   events=True,
                   cfg={"immortal": not getattr(args, "mortal", False),
                        "start_capital": STARTING_KITS.get(getattr(args,"kit","poor_scholar"),
                                                           STARTING_KITS["poor_scholar"])["den"]},
                   civ=load_civ(getattr(args, "civ", "rome_100ad")),
                   bounty_set=bounties).run(goal, args.horizon)
               for i in range(args.mc)]
        _summarise(res, "%s%s" % (label, "  [deterministic]" if deterministic else ""))
        sys.stdout.flush()


def _civ_for_session(args):
    """Which civilisation to start, honouring the save above the command line.

    A save says what game it is. Resuming should not need the flag repeated,
    and a flag that contradicts the file should say so rather than start the
    wrong game over the top of it, even when the contradicting command line
    is one the game itself printed for the player to reuse.
    """
    session = getattr(args, "session", None)
    asked = getattr(args, "civ", None)
    if session and os.path.exists(session) and not _is_claimed_slot(session):
        saved = civ_of_save(session)
        if saved:
            if asked and asked != saved:
                # Said out loud on stdout, where the player is looking, and then
                # a non-zero exit. A refusal only argparse can see is a refusal
                # nobody reads.
                print("that save is a %s game; you asked for %s. Drop the --civ "
                      "flag to resume it, or point --session somewhere else."
                      % (saved, asked))
                raise SystemExit(1)
            return saved
    return asked or "rome_100ad"


def _goal_for_session(args, tree, nodes):
    """Which goal to start the strategy order for, honouring the save above
    the command line - same reasoning and same shape as _civ_for_session
    just above, and for the same reason: the order `load_strategy` hands
    back depends on the goal's own closure (see load_strategy's goal
    argument), so a resumed game has to know its goal BEFORE that call, not
    only after load_state runs.
    """
    session = getattr(args, "session", None)
    asked = getattr(args, "goal", None)
    if session and os.path.exists(session) and not _is_claimed_slot(session):
        saved = goal_of_save(session)
        if saved and saved in nodes:
            if asked and asked != saved:
                print("that save is playing toward %s; you asked for %s. Drop "
                      "the --goal flag to resume it, or point --session "
                      "somewhere else." % (saved, asked))
                raise SystemExit(1)
            return saved
    return resolve_goal(tree, nodes, asked)


def _horizon_explicit():
    """True if --horizon appeared on the actual command line this process was
    started with, as opposed to argparse's default of 500 that is present in
    `args.horizon` whether or not anyone typed it. A flag typed by hand always
    outranks anything remembered from an earlier sitting."""
    return any(tok == "--horizon" or tok.startswith("--horizon=")
              for tok in sys.argv)


def _resolve_horizon(args, session):
    """How many years this sitting gets: the --horizon flag if it was
    actually typed, otherwise whatever the horizon was last set to for this
    save (see the in-game 'options' command and the New Game wizard, both of
    which write it to session.meta.json - see settings.py's module docstring
    for why that lives beside the save rather than inside it), otherwise the
    flag's ordinary default. A save nobody ever touched 'options' or the menu
    for has no meta file, so this returns exactly args.horizon and nothing about
    the flag-driven path changes.
    """
    if session and not _horizon_explicit():
        meta = settings.load_session_meta(session)
        horizon_years = meta.get("horizon_years")
        if isinstance(horizon_years, (int, float)) and horizon_years > 0:
            return int(horizon_years)
    return args.horizon


def cmd_sensitivity(args):
    """Ablation study: how much is each defensive or institutional node worth?

    Removes one node from the strategy (so it is never built) and re-runs. Nodes
    that are prerequisites of the goal cannot be ablated and are reported as such.
    """
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(args, "goal", None))
    label, order, bounties = load_strategy(args.strategy, nodes, goal)
    need = closure(nodes, goal)

    # COMMON RANDOM NUMBERS: trial() reseeds random.Random(args.seed + i)
    # identically for every call - baseline and every ablation see the same
    # per-trial shocks, differing only in which node was dropped. See
    # cmd_compare for the full rationale; do not randomise this per call.
    def trial(drop=None):
        trimmed_order = [node_id for node_id in order if node_id != drop]
        res = [Sim(nodes, trimmed_order, random.Random(args.seed + i), events=True,
                   bounty_set=bounties).run(goal, args.horizon)
               for i in range(args.mc)]
        succ = sum(1 for result in res if result.goal_year)
        successful_years = sorted(result.goal_year for result in res if result.goal_year)
        return (100.0 * succ / len(res), successful_years[len(successful_years) // 2] if successful_years else None, succ, len(res))

    base_rate, base_med, base_succ, base_n = trial()
    print("baseline (%s): %s" % (args.strategy, _fmt_rate_ci(base_succ, base_n)))
    print("  median year reached: %s AD" % base_med)
    if 0 < base_succ < _MIN_SUCCESSES_FOR_QUANTILES:
        print("  (that median is %d observation%s wearing a statistic's clothing -"
              " read it as an anecdote, not a distribution)"
              % (base_succ, "" if base_succ == 1 else "s"))
    print("A node's value shows up in the CALENDAR at least as much as in the")
    print("success rate, so both are scored. 'delay' is how many years later the")
    print("median run reaches the goal (%s) when this node is never built.\n" % goal)
    print("%-24s %8s %16s %8s %8s   %s" %
          ("node removed", "success", "95% CI", "median", "delay", "verdict"))
    print("-" * 96)
    cands = ["plague_preparedness", "corpus_written", "corpus_dispersed", "printing_press",
             "rag_paper", "school_founded", "academy_network", "endowment_land",
             "freedman_staff", "collegium_licensed", "patron_senatorial", "patron_imperial",
             "semaphore_telegraph", "citizenship", "mirror_amalgam", "lens_grinding",
             "crop_rotation", "world_map", "sanitation_antisepsis", "telegraph_electric"]
    rows = _run_ablation_trials(cands, nodes, need, trial, base_rate)
    scored = _score_ablations(rows, base_med)
    _print_ablation_table(scored)


def _run_ablation_trials(cands, nodes, need, trial, base_rate):
    """Run the ablation trial for each candidate node, printing an
    immediate row for anything that cannot be ablated because it is a hard
    prerequisite of the goal, and collecting the rest for scoring."""
    rows = []
    for node_id in cands:
        if node_id not in nodes:
            continue
        if node_id in need:
            print("%-26s %10s %10s   hard prerequisite of the goal, cannot be skipped" % (node_id, "-", "-"))
            continue
        success_rate, median_year, succ, ntot = trial(node_id)
        rows.append((base_rate - success_rate, node_id, success_rate, median_year, succ, ntot))
    return rows


def _score_ablations(rows, base_med):
    scored = []
    for rate_drop, node_id, success_rate, median_year, succ, ntot in rows:
        delay = (median_year - base_med) if (median_year and base_med) else 999
        # one point of success rate is worth roughly two years of delay
        score = rate_drop + delay / 2.0
        scored.append((score, node_id, success_rate, median_year, rate_drop, delay, succ, ntot))
    return scored


def _ablation_verdict(score):
    return ("CRITICAL, do not skip" if score > 20 else
            "clearly worth it" if score > 8 else
            "worth it" if score > 3 else
            "marginal in this model" if score > -3 else
            "the model says this costs more than it returns")


def _print_ablation_table(scored):
    for score, node_id, success_rate, median_year, rate_drop, delay, succ, ntot in sorted(scored, reverse=True):
        verdict = _ablation_verdict(score)
        lower, upper = _wilson_interval(succ, ntot)
        confidence_interval = "[%.0f%%,%.0f%%]" % (100.0 * lower, 100.0 * upper)
        print("%-24s %7.0f%% %16s %8s %+8s   %s" %
              (node_id, success_rate, confidence_interval, median_year or "never", ("%d yr" % delay) if median_year else "n/a", verdict))


# Complaints/38 section 2: cmd_sweep's "mortality" axis sweeps
# founder_life_mean and needs a spread to draw around each mean point. This
# USED to be a separately declared 4.0, half of DEFAULTS["founder_life_sd"]
# (8.0) - the standard deviation every ordinary game, core.py's own
# founder-lifespan draw, and this file's own _ingame_options all actually
# use. A sweep whose whole purpose is to show how the OUTCOME is distributed
# under mortality was doing so at half the real variance, understating the
# tail in both directions - exactly the thing a sweep is for. Fixed by
# deleting the second number: the mortality axis below now reads
# DEFAULTS["founder_life_sd"] directly, the same way it already reads
# DEFAULTS["founder_life_mean"] for its central values, so there is only one
# place left that can disagree with itself.


def cmd_sweep(args):
    """Sweep a starting condition and show how the outcome and the FAILURE MODE move.

    The failure mode moving is the interesting part. More starting capital does
    not simply help: past a point it switches you from dying poor and untaught to
    being denounced as a magician, because money buys speed, speed buys
    visibility, and visibility in Trajanic Rome is dangerous.
    """
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(args, "goal", None))
    label, order, bounties = load_strategy(args.strategy, nodes, goal)
    sweeps = {
        "capital":  ("start_capital", [2000, 5000, 10320, 25000, 50000, 200000, 1000000]),
        "lifespan": ("founder_life",  [10, 15, 20, 28, 35, 45, 60]),
        "hours":    ("founder_hours_per_year", [1000, 1500, 2000, 2500, 3000]),
        "mortality":("founder_life_mean", [10, 15, 20, 28, 40, 60]),
    }
    key, values = sweeps[args.axis]
    print("sweeping %s under strategy '%s', %d runs per point\n" % (args.axis, args.strategy, args.mc))
    print("%-12s %8s %16s %8s %8s   %s" %
          (args.axis, "success", "95% CI", "median", "p25", "dominant failure"))
    print("-" * 92)
    any_thin = False
    any_success = False
    for value in values:
        cfg, life = _sweep_point_cfg(key, value)
        res = _run_sweep_point(nodes, order, bounties, goal, args, cfg, life)
        thin, succeeded = _print_sweep_row(value, res)
        any_thin = any_thin or thin
        any_success = any_success or succeeded
    _print_sweep_footer(any_thin, any_success, args.axis, args.strategy)


def _sweep_point_cfg(key, value):
    """Build the (cfg, life) pair one sweep point runs Sim under: cfg goes
    straight into Sim's config, and life (when not None) is set directly on
    the Sim afterward because life_left is not a cfg key."""
    cfg, life = {}, None
    if key == "founder_life_mean":
        cfg = {"immortal": False, "founder_life_mean": value,
               "founder_life_sd": DEFAULTS["founder_life_sd"]}
    elif key == "founder_life":
        life = value
    else:
        cfg[key] = value
    return cfg, life


def _run_sweep_point(nodes, order, bounties, goal, args, cfg, life):
    """Run args.mc trials at one sweep point and return their results."""
    res = []
    for i in range(args.mc):
        # COMMON RANDOM NUMBERS across the points of this sweep, same
        # reasoning as cmd_compare: trial i sees the same shocks at every
        # value this sweep visits, so a change down this column is the swept
        # variable acting, not a different draw of luck. Do not reseed per value.
        sim = Sim(nodes, order, random.Random(args.seed + i), events=True, cfg=cfg,
                  bounty_set=bounties)
        if life is not None:
            sim.life_left = float(life)
        res.append(sim.run(goal, args.horizon))
    return res


def _sweep_point_failure_causes(res):
    failure_causes = defaultdict(int)
    for run in res:
        if not run.goal_year:
            failure_causes[(run.dead_reason or "ran out of horizon").split(":")[0]] += 1
    return failure_causes


def _print_sweep_row(value, res):
    """Print one row of the sweep table. Returns (thin, succeeded) so the
    caller can decide whether the footer notes about thin medians and
    all-zero sweeps are needed."""
    succ = sum(1 for run in res if run.goal_year)
    successful_years = sorted(run.goal_year for run in res if run.goal_year)
    failure_causes = _sweep_point_failure_causes(res)
    worst = max(failure_causes.items(), key=lambda x: x[1]) if failure_causes else ("none", 0)
    lower, upper = _wilson_interval(succ, len(res))
    thin = 0 < succ < _MIN_SUCCESSES_FOR_QUANTILES
    print("%-12s %7.0f%% %16s %8s %8s   %s" %
          (f"{value:,}", 100.0 * succ / len(res),
           "[%.0f%%,%.0f%%]" % (100.0 * lower, 100.0 * upper),
           (str(successful_years[len(successful_years) // 2]) + "*" if thin else successful_years[len(successful_years) // 2]) if successful_years else "never",
           successful_years[len(successful_years) // 4] if successful_years else "-",
           "%s (%d)" % (worst[0][:44], worst[1]) if worst[1] else "-"))
    return thin, succ > 0


def _print_sweep_footer(any_thin, any_success, axis, strategy):
    print("\nWatch the failure column, not the success column. When it changes, the")
    print("binding constraint has changed and so should your strategy.")
    if any_thin:
        print("* median from under %d successes - an anecdote, not a distribution;"
              % _MIN_SUCCESSES_FOR_QUANTILES)
        print("  trust the 95%% CI on success rate at that point instead.")
    if not any_success:
        # DO NOT SILENTLY PRINT A TABLE OF ZEROS. Every point on this sweep
        # scored 0% - '%s' is a known-losing order at every value of %s
        # tried here, at this horizon, not merely at one unlucky point on
        # it. That is a statement about the ORDER, not about whether the
        # goal is reachable at all (recommended.json scores exactly this
        # while a computed order has reached 100%, same tree, same
        # civilisation) - 'plan' or 'search' compute a different order
        # instead of sweeping this one across more starting conditions.
        print("\n*** EVERY point on this sweep scored 0%% - '%s' never reached the goal"
              % strategy)
        print("    at any %s tried, not only at one unlucky value. Before reading" % axis)
        print("    anything above as 'this starting condition is impossible': this looks")
        print("    like a known-losing ORDER at this horizon, not a fact about %s. Run"
              % axis)
        print("    'plan' (critical-path method) or 'search' (dice-free, relaxed against")
        print("    the binding constraint) to compute a different order, then sweep that.")


def cmd_goals(args):
    """List every selectable goal: the transistor and every alternative in
    data/tech_tree.json meta.goals, with its closure size and dice-free
    critical-path floor - the same pair of numbers 'validate' prints, on
    their own, for picking a goal rather than auditing the tree. See
    'validate --deep' for whether each one is actually reachable, one CPM
    trial per civilisation.
    """
    tree, prices, nodes, wages, goods = load()
    default_goal = tree["meta"]["goal_node"]
    catalog = goal_catalog(tree, nodes)
    print("%-34s %9s %10s  %-11s %s" % ("name", "closure", "floor(yr)", "scale", "node"))
    print("-" * 100)
    for goal in catalog:
        node = goal["node"]
        need = closure(nodes, node)
        yrs, _chain = critical_path(nodes, node)
        print("%-34s %9d %10.1f  %-11s %s%s"
              % (goal.get("name", node)[:34], len(need), yrs, goal.get("scale", ""), node,
                 "  <- DEFAULT" if node == default_goal else ""))
        if goal.get("blurb"):
            print("    " + goal["blurb"])
        win_condition = nodes[node].get("win_condition")
        if win_condition:
            print("    won by measurement, not by building: %s"
                  % win_condition_describe(nodes[node]))
    return 0


# THE APPLICATION'S OWN DISPLAY WIDTH - see _apply_display_prefs below and
# settings.py's module docstring ("DISPLAY WIDTH"). Starts at the number
# this file's own _wrap always hardcoded, so a process that never calls
# _apply_display_prefs (nothing in this file does on import; every
# human-facing entry point calls it exactly once, at its own top) renders
# exactly as it always did.
_DISPLAY_WIDTH = 76


def _apply_display_prefs(cfg=None):
    """Read the application's display preferences once and apply them for
    the rest of this process: how wide a line wraps (here, and in
    protocol.py's renderers - see protocol.DISPLAY_WIDTH's own comment) and
    how many rows a long table pages by default (protocol.
    DEFAULT_AVAILABLE_LIMIT). Returns the config, so a caller that already
    needs it (cmd_menu, _new_game, _options_menu) is not reading the file
    twice.

    CALLED FROM EVERY HUMAN-FACING ENTRY POINT - cmd_menu and cmd_play - and
    from NOWHERE in cmd_agent. `agent` speaks a stable JSON protocol (and,
    with --pretty, a readable rendering alongside it) that a script or
    another process depends on looking the same regardless of whose
    terminal, or whose saved preferences, happen to be on the machine it
    runs on; a human's own cosmetic choices about their own terminal have no
    business changing what a script sees. See settings.py's module
    docstring for where these preferences actually live.
    """
    if cfg is None:
        cfg = settings.load_config()
    global _DISPLAY_WIDTH
    _DISPLAY_WIDTH = settings.resolve_display_width(cfg)
    _protocol.DISPLAY_WIDTH = _DISPLAY_WIDTH
    _protocol.DEFAULT_AVAILABLE_LIMIT = settings.resolve_rows_per_page(cfg)
    return cfg


def _wrap(text, width=None, indent="   "):
    if width is None:
        width = _DISPLAY_WIDTH
    words, lines, cur = text.split(), [], ""
    for word in words:
        if len(cur) + len(word) + 1 > width:
            lines.append(indent + cur); cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(indent + cur)
    return "\n".join(lines)


def _is_claimed_slot(path):
    """A session file that exists but holds nothing yet.

    _pick_session_filename claims its name by creating the file, so between
    the menu picking a name and the first command being saved there is a
    zero-byte file on disk. That is a NEW GAME, not a corrupt save, and
    treating it as one made a freshly started game unresumable.
    """
    try:
        return os.path.getsize(path) == 0
    except OSError:
        return False


def _pick_session_filename(civ_id):
    """A save name for a game the menu is about to start, picked so it never
    silently overwrites an existing one.

    An absolute path into the save directory (see settings.resolve_save_dir):
    ~/.rome-saves by default, or wherever a player has redirected saves to
    from the Options menu, ROME_SAVE_DIR, or both. This is a different path
    from the one `_unsafe_path` in protocol.py governs - that one is for the
    typed/JSON 'save' command, a deliberately sandboxed relative filename
    beside wherever the game was started; this one is for the file the menu
    and --session write to after every command, which has always been
    allowed to be absolute.
    """
    # CLAIMED, NOT MERELY CHECKED. This tested os.path.exists and returned the
    # name without creating anything, so six games started at once all saw the
    # same gap and all picked rome_100ad_78.json: five of them overwrote each
    # other, under a banner promising you can resume exactly where you left
    # off. O_EXCL makes the check and the claim one operation.
    #
    # And it counts UP FROM THE HIGHEST rather than filling the first gap, so
    # moving a save out of the directory does not turn its number into a slot
    # some later game takes.
    # IN A DIRECTORY OF ITS OWN. Save files must not accumulate in the
    # repository root beside the source. A game that writes a file after
    # every command has to put them somewhere a person can find and delete -
    # and, now, somewhere a player stuck with a non-persistent $HOME can move
    # away from entirely. See settings.py's module docstring.
    save_dir = settings.resolve_save_dir()
    civ_id = os.path.join(save_dir, civ_id)
    highest = 1
    prefix = civ_id + "_"
    try:
        for save_name in (os.path.join(save_dir, filename) for filename in os.listdir(save_dir)):
            if save_name.startswith(prefix) and save_name.endswith(".json"):
                try:
                    highest = max(highest, int(save_name[len(prefix):-5]))
                except ValueError:
                    pass
    except OSError:
        pass
    attempt = highest if os.path.exists("%s.json" % civ_id) else 1
    while True:
        candidate = ("%s.json" % civ_id) if attempt == 1 else ("%s_%d.json" % (civ_id, attempt))
        try:
            os.close(os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
            return candidate
        except FileExistsError:
            attempt += 1
        except OSError:
            # Cannot write here at all; hand back a name and let `save` report
            # the real error rather than looping for ever.
            return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # NOT required: typing the bare command should open the menu rather than
    # print a usage error at somebody who has just arrived.
    sub = parser.add_subparsers(dest="cmd", required=False)
    subparser = sub.add_parser("validate")
    subparser.add_argument("--deep", action="store_true",
                   help="also run one dice-free, immortal, CPM-ordered trial per "
                        "goal per civilisation (see 'goals' for the roster) and "
                        "report whether each one reaches its goal within a capped "
                        "horizon - a lower bound on reachability, not a verdict. "
                        "Takes real time (one Sim trial per cell); the structural "
                        "checks above run either way and are instant.")
    sub.add_parser("civs")
    sub.add_parser("goals", help="list the selectable goals - the transistor and every "
                                 "alternative in data/tech_tree.json meta.goals - with "
                                 "each one's closure size and dice-free critical-path floor.")
    subparser = sub.add_parser("path"); subparser.add_argument("goal", nargs="?")
    subparser = sub.add_parser("costs"); subparser.add_argument("--top", type=int, default=20)
    subparser = sub.add_parser("why"); subparser.add_argument("node")
    subparser.add_argument("--goal", default=None,
                   help="which goal to report 'on the critical path' against. "
                        "Default: the tree's own default goal (the transistor).")
    subparser = sub.add_parser("sweep")
    subparser.add_argument("axis", choices=["capital", "lifespan", "hours", "mortality"])
    subparser.add_argument("--strategy", default="recommended")
    subparser.add_argument("--goal", default=None,
                   help="which goal to sweep against. See 'goals' for the roster; "
                        "default is the tree's own default (the transistor).")
    subparser.add_argument("--mc", type=int, default=200)
    subparser.add_argument("--seed", type=int, default=1)
    subparser.add_argument("--horizon", type=int, default=500)
    for name in ("run", "compare"):
        subparser = sub.add_parser(name)
        subparser.add_argument("--strategy", default="recommended")
        subparser.add_argument("--goal", default=None,
                       help="which goal to aim at. See 'goals' for the roster; "
                            "default is the tree's own default (the transistor).")
        subparser.add_argument("--mc", type=int, default=200)
        subparser.add_argument("--seed", type=int, default=1)
        subparser.add_argument("--horizon", type=int, default=500)
        subparser.add_argument("--no-events", action="store_true",
                       help="turn off weather/plague/political hazard rolls. NOT a "
                            "noise-free baseline: project-failure risk (projects.py "
                            "_complete) and fractional-headcount rounding (labour.py "
                            "_stochastic_round) both draw from the same self.rng "
                            "regardless of this flag, so a --no-events batch still "
                            "has real seed-to-seed variance. What this flag actually "
                            "buys you is a run reproducible for one fixed seed, same "
                            "as with events on - not determinism across seeds. See "
                            "--deterministic for a run where every one of those "
                            "rolls, not only the dated hazards this flag silences, "
                            "comes out the same way every time.")
        subparser.add_argument("--no-bounties", action="store_true")
        subparser.add_argument("--civ", default="rome_100ad",
                       help="which civilization to play. See data/civilizations/")
        subparser.add_argument("--kit", default="poor_scholar",
                       help="starting wealth: " + ", ".join(STARTING_KITS))
        subparser.add_argument("--mortal", action="store_true",
                       help="turn the founder's mortality back on (default: immortal, "
                            "so the run measures the TREE and not a lifespan lottery)")
        subparser.add_argument("--deterministic", action="store_true",
                       help="replace this run's rng with one whose random() always "
                            "returns 1.0 (DetRNG, engine/cli.py - the same class "
                            "path_search.py's own dice-free search trials use): no "
                            "project ever fails outright, nobody is lost to the "
                            "yearly attrition roll, nobody is freed by the "
                            "manumission roll, and every fractional headcount rounds "
                            "down. THIS IS NOT WHAT --no-events DOES, and --no-events "
                            "ALONE DOES NOT DO THIS: that flag only silences dated "
                            "weather/plague/political hazards and, by itself, still "
                            "leaves every roll above drawing from an ordinary seeded "
                            "rng (see --no-events' own help). With --mc greater than "
                            "1, every trial comes out identical under this flag - "
                            "there is no luck left to re-roll, which is the point, "
                            "not a bug. A dice-free trial answers 'does this order "
                            "even get there' at all; it does not choose a better "
                            "order - see 'plan' and 'search' for that.")
        subparser.add_argument("--trace", action="store_true")
        # WRITE DOWN A PATH THAT WORKED, so the next measurement can start from
        # evidence instead of from the same losing list. Feed the file back in
        # with --strategy <path>.
        subparser.add_argument("--save-winner", metavar="FILE", default=None,
                       help="if any trial reaches the goal, write the order the "
                            "best one finished its work in to FILE, as a "
                            "strategy you can pass back to --strategy")
    subparser = sub.add_parser("sensitivity")
    subparser.add_argument("--strategy", default="recommended")
    subparser.add_argument("--goal", default=None,
                   help="which goal to measure sensitivity against. See 'goals' "
                        "for the roster; default is the tree's own default "
                        "(the transistor).")
    subparser.add_argument("--mc", type=int, default=200)
    subparser.add_argument("--seed", type=int, default=1)
    subparser.add_argument("--horizon", type=int, default=500)
    subparser = sub.add_parser("plan", help="work backward from the goal over its prerequisite "
                                    "closure (critical-path method) and write a strategy "
                                    "file, instead of hand-writing one or gambling on a "
                                    "Monte Carlo run until one happens to win. See "
                                    "sim/planner.py. A developer/optimizer tool, "
                                    "like compare/sweep/sensitivity - never reached from "
                                    "play or agent.")
    subparser.add_argument("--civ", default="rome_100ad")
    subparser.add_argument("--goal", default=None)
    subparser.add_argument("--out", required=True, metavar="FILE",
                   help="strategy file to write; feed it back in with --strategy")
    subparser.add_argument("--seed-strategy", default=None,
                   help="a strategy name or path (e.g. captured_han_386, or a "
                        "previous --out) whose order breaks ties among nodes the "
                        "critical path itself ranks as equally urgent")
    subparser.add_argument("--side-branches", type=int, default=12,
                   help="how many revenue-positive nodes outside the goal's own "
                        "requirements to weave in, to fund the spine. 0 disables")
    subparser.add_argument("--side-branch-every", type=int, default=8)
    subparser.add_argument("--refine-rounds", type=int, default=0,
                   help="plan, run --mc real trials, capture the winner's finish "
                        "order, re-plan from it, repeat this many times. 0 (the "
                        "default) is purely structural and instant")
    subparser.add_argument("--mc", type=int, default=12,
                   help="trials per refinement round (ignored if --refine-rounds 0)")
    subparser.add_argument("--horizon", type=int, default=700)
    subparser.add_argument("--seed", type=int, default=1)
    # DETERMINISTIC SEARCH: solve the dice-free problem first (see
    # sim/path_search.py), instead of only computing one structural CPM
    # pass. --search-rounds 0 (the default) leaves `plan` doing only the
    # structural CPM pass; a nonzero value diagnoses the binding constraint against a dice-free
    # trial of the CPM order (no events, no project failures, immortal
    # founder - see path_search.DetRNG) and relaxes it, round by round,
    # keeping whichever round's order actually scored best.
    subparser.add_argument("--search-rounds", type=int, default=0,
                   help="diagnose the binding constraint against a dice-free "
                        "trial and relax it, up to this many rounds, before "
                        "applying --refine-rounds (if any). 0 (default) skips "
                        "this and is purely the structural CPM pass")
    subparser.add_argument("--search-horizon", type=int, default=500,
                   help="dice-free horizon used WHILE searching (kept short "
                        "for speed - see path_search.py's own module "
                        "docstring on why a longer, slower verification run "
                        "is a separate step, not part of the search loop)")
    subparser.add_argument("--search-backlog-ratio", type=float, default=6.0)
    subparser.add_argument("--search-no-grow-supply", action="store_true",
                   help="skip the search's move 3 (founding institutions "
                        "one at a time, kept only if a fresh dice-free trial "
                        "measures the result as genuinely better) and use "
                        "only moves 1-2 (pulling/resequencing what is "
                        "already named) - the search's behaviour before "
                        "move 3 existed")
    subparser = sub.add_parser("search", help="path_search.py's dice-free search on its own, "
                                      "the other front door onto the same machinery "
                                      "'plan --search-rounds' folds into a CPM-seeded "
                                      "pipeline. Answers 'does this order even get "
                                      "there with the dice off' and relaxes the "
                                      "binding constraint it finds, round by round. "
                                      "See sim/path_search.py. A developer/"
                                      "optimizer tool, like plan/compare/sweep/"
                                      "sensitivity - never reached from play or agent.")
    subparser.add_argument("--civ", default="rome_100ad")
    subparser.add_argument("--goal", default=None)
    subparser.add_argument("--out", required=True, metavar="FILE",
                   help="strategy file to write; feed it back in with --strategy")
    subparser.add_argument("--side-branches", type=int, default=12,
                   help="how many revenue-positive nodes outside the goal's own "
                        "requirements to weave in, to fund the spine. 0 disables")
    subparser.add_argument("--side-branch-every", type=int, default=8)
    subparser.add_argument("--rounds", type=int, default=6,
                   help="how many rounds of diagnose-and-relax to run at most; "
                        "a round that reaches the goal, finds no scarce trade "
                        "left, or makes no change to the order stops early")
    subparser.add_argument("--horizon", type=int, default=500,
                   help="dice-free horizon used WHILE searching - kept short "
                        "for speed; verify the winner separately at a longer "
                        "horizon and then against real seeds (e.g. 'run "
                        "--strategy FILE --mc N')")
    subparser.add_argument("--backlog-ratio", type=float, default=6.0)
    subparser.add_argument("--seed-strategy", default=None,
                   help="a strategy name or path whose order breaks ties "
                        "among nodes the critical path ranks as equally "
                        "urgent, same as plan's own --seed-strategy")
    subparser.add_argument("--no-grow-supply", action="store_true",
                   help="skip move 3 (founding institutions one at a time, "
                        "kept only if measured better) and use only moves "
                        "1-2 (pulling/resequencing what is already named) - "
                        "this search's behaviour before move 3 existed")
    sub.add_parser("menu", help="pick a civilisation, read where you have landed, "
                                "and start. This is what a bare invocation does.")
    subparser = sub.add_parser("play")
    subparser.add_argument("--strategy", default="recommended")
    subparser.add_argument("--goal", default=None,
                   help="which goal to play toward. See 'goals' for the roster "
                        "(the transistor and every alternative); default is the "
                        "tree's own default. Omit when resuming a --session: "
                        "the save says which goal it is.")
    subparser.add_argument("--seed", type=int, default=1)
    subparser.add_argument("--horizon", type=int, default=500)
    subparser.add_argument("--civ", default=None,
                   help="which civilisation. Omit when resuming a --session: the "
                        "save says which game it is.")
    subparser.add_argument("--kit", default="poor_scholar",
                   help="starting wealth: " + ", ".join(STARTING_KITS))
    subparser.add_argument("--fog", action="store_true")
    subparser.add_argument("--mortal", action="store_true")
    subparser.add_argument("--deterministic", action="store_true",
                   help="replace this session's rng with one whose random() always "
                        "returns 1.0 (DetRNG - same class 'run'/'compare' --deterministic "
                        "and path_search.py's own search trials use): project failure, "
                        "the yearly attrition roll, the manumission roll and fractional-"
                        "headcount rounding all come out the way they would with no "
                        "luck at all, good or bad. 'play' has no --no-events flag, so "
                        "dated weather/plague/political hazards still fire every year - "
                        "but they too are gated by the same kind of roll this flag "
                        "always fails, so in practice this alone is a fully dice-free "
                        "sitting. A developer/diagnostic tool, not something an "
                        "ordinary playthrough needs.")
    subparser.add_argument("--session", default=None,
                   help="a save file. Loaded if it exists, written after every "
                        "command, so you can stop and come back later")
    subparser.add_argument("--manual", action="store_true",
                   help="accepted and ignored: play is always manual now. Nothing "
                        "starts unless you start it. The old advisory mode, where "
                        "the optimizer kept starting things regardless of what you "
                        "typed, is gone; use 'run --trace' to watch it work.")
    subparser = sub.add_parser("agent", help="JSON protocol so a script or an AI agent can play "
                                     "and choose its own research path. See the module "
                                     "docstring for the command table.")
    subparser.add_argument("--strategy", default="recommended",
                   help="only used to seed the display order in 'available'; nothing "
                        "is auto-started, this command always runs manual")
    subparser.add_argument("--goal", default=None,
                   help="which goal to play toward. See 'goals' for the roster; "
                        "default is the tree's own default. Omit when resuming a "
                        "--session: the save says which goal it is.")
    subparser.add_argument("--seed", type=int, default=1)
    subparser.add_argument("--horizon", type=int, default=500)
    subparser.add_argument("--civ", default=None,
                   help="which civilisation. Omit when resuming a --session: the "
                        "save says which game it is.")
    subparser.add_argument("--kit", default="poor_scholar",
                   help="starting wealth: " + ", ".join(STARTING_KITS))
    subparser.add_argument("--no-events", action="store_true",
                   help="turn off weather/plague/political hazard rolls, for a "
                        "playthrough with fewer surprises. This does NOT make the "
                        "session noise-free: project-failure risk (projects.py "
                        "_complete) and fractional-headcount rounding (labour.py "
                        "_stochastic_round) still draw from the same self.rng "
                        "either way. A --session is reproducible run-to-run because "
                        "it replays the same seed, not because this flag removed "
                        "the randomness - it only removed the hazard rolls.")
    subparser.add_argument("--fog", action="store_true",
                   help="fog of war: you see what you have built and what you could "
                        "begin next, and nothing about where any of it leads")
    subparser.add_argument("--mortal", action="store_true",
                   help="turn the founder's mortality back on (default: immortal, "
                        "same meaning as on 'run'/'compare'/'play')")
    subparser.add_argument("--deterministic", action="store_true",
                   help="replace this session's rng with one whose random() always "
                        "returns 1.0 (DetRNG - same class 'run'/'compare'/'play' "
                        "--deterministic and path_search.py's own search trials use): "
                        "project failure, the yearly attrition roll, the manumission "
                        "roll and fractional-headcount rounding all come out the way "
                        "they would with no luck at all. THIS IS NOT --no-events AND "
                        "--no-events ALONE DOES NOT DO THIS - see that flag's own help "
                        "just above. Combine the two for the same fully dice-free "
                        "session path_search.py's own trials run.")
    subparser.add_argument("--session", default=None,
                   help="a save file. Loaded if it exists, written after every "
                        "command, so you can play across separate invocations "
                        "without holding a process open")
    subparser.add_argument("--script", default=None,
                   help="path to a JSON file holding a list of command objects, "
                        "played in order instead of reading stdin")
    subparser.add_argument("--pretty", action="store_true",
                   help="alongside the ordinary JSON line on stdout - unchanged, "
                        "still exactly one object per line - print a human-readable "
                        "rendering of each reply to stderr. Never changes stdout; "
                        "a script reading only stdout sees no difference at all.")
    args = parser.parse_args()
    if not args.cmd:
        args.cmd = "menu"
    return {"validate": cmd_validate, "path": cmd_path, "costs": cmd_costs,
            "why": cmd_why, "sweep": cmd_sweep, "civs": cmd_civs, "menu": cmd_menu,
            "goals": cmd_goals,
            "run": cmd_run, "compare": cmd_compare, "play": cmd_play, "agent": cmd_agent,
            "sensitivity": cmd_sensitivity, "plan": cmd_plan,
            "search": cmd_search}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)


# ----------------------------------------------------------------------------
# Re-exported here so every name that simulator.py, path_search.py,
# planner.py and this project's own tests import from `engine.cli` by name
# still resolves. Deliberately placed at the END of this file, not the
# top: cli_interactive.py and cli_agent.py both do `from .cli import
# _apply_display_prefs, _wrap, _is_claimed_slot, _pick_session_filename, ...`
# (session/display helpers defined earlier in THIS file), so those names
# must already exist in this module's namespace before Python starts
# executing cli_interactive.py/cli_agent.py/cli_analysis.py - i.e. this
# import must come after every name they read from here, not before.
# ----------------------------------------------------------------------------
from .cli_interactive import cmd_civs, cmd_menu, cmd_play
from .cli_agent import cmd_agent
from .cli_analysis import cmd_plan, cmd_search, cmd_why
