"""The command line: validate, costs, path, plan, run, compare, play, agent."""
import collections, json, math, os, random, time
from collections import defaultdict

from .data import (CIVDIR, closure, critical_path, DEFAULTS, goal_catalog,
                   hard_pre, load, load_civ, load_geography, resolve_goal,
                   STARTING_KITS, STRATS, topo_order, win_condition_describe)


import argparse, sys

from .core import Sim
from . import protocol as _protocol
from . import settings
from .data import money_word, money_short
from .protocol import (
    _agent_available, _agent_dispatch, _agent_end_reason, _agent_help,
    _agent_state, _node_explain, civ_of_save, goal_of_save, final_report,
    load_state, parse_typed, render_final, render_pretty, save_state)
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
    site (core.py's own comment on `rng.sample(losable, ...)`) that once
    walked a bare, unsorted `set` of ids and was fixed by sorting it
    specifically because an earlier version did not - so a --deterministic
    run whose output depended on iteration order over some other such set
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
    placed. Leaving this out was a serious and completely invisible bug. The
    strategy file names 128 nodes explicitly and everything else was sorted
    goal-critical-first and then handed to this function WITHOUT telling it
    about those 128 - so every node whose prerequisites lived in the explicit
    list could never satisfy `all(p in placed)`, fell through to the bulk dump
    below, and lost its place entirely.

    The effect was not subtle. `cap_heat_1100` - tier 0, 225 denarii, two
    artisans, and a prerequisite of the goal - sorted to index 4 and came out
    of here at index 589. Sixty goal-critical nodes were pushed past 400. A Han
    China run then sat at year 700 holding 3.37 MILLION denarii, 57 scholars
    and 99 artisans, having never built a 225-denarii node it needed, because
    the optimizer works down this order and never got that far. Han reached the
    transistor in 0% of runs and the reason was never economic.
    """
    placed = set(already)
    out = []
    pref = list(preference)
    # hard_pre, NOT nodes[k]["pre"]. This function is what decides the order
    # the engine actually receives, and it was the last place still reading
    # `pre` alone after closure(), topo_order() and critical_path() had all
    # learned that a req_any group with exactly one real option is a
    # prerequisite rather than a choice. The effect was the whole point of
    # that work going nowhere: mat_manganese was correctly required, and came
    # out of here at index 187 behind the mat_bulk_steel at index 65 that
    # cannot be built without it.
    hard_pre_by_node = {node_id: hard_pre(nodes, node_id) for node_id in pref}
    # Index the dependants so each placement only revisits what it could free,
    # rather than rescanning the whole list: the old loop was O(n^2) with a
    # list.remove() inside it, over 2,700 nodes.
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


def cmd_validate(a):
    tree, prices, nodes, wages, goods = load()
    errs, warns = [], []
    for node_id, node_record in nodes.items():
        for prereq_id in node_record["pre"]:
            if prereq_id not in nodes: errs.append("%s: unknown prereq %s" % (node_id, prereq_id))
        for material_id in node_record["mat"]:
            if material_id not in goods: errs.append("%s: unpriced material %s" % (node_id, material_id))
        for trade_id in node_record["lab"]:
            if trade_id not in wages: errs.append("%s: unknown trade %s" % (node_id, trade_id))
        if not 0 <= node_record["risk"] <= 1: errs.append("%s: risk out of range" % node_id)
        if node_record["conf"] not in "ABC": warns.append("%s: odd confidence %s" % (node_id, node_record["conf"]))
        # A `why` on seven hand-written nodes killed the process with KeyError
        # 'sus' because I added them without the v1 scalars the explain path
        # still reads. Catch a missing field here, where it is a warning, rather
        # than in a player's session, where it is the end of their game.
        for field_name in ("sus", "gov", "cat", "pre", "ph", "cap", "up", "risk"):
            if field_name not in node_record:
                errs.append("%s: missing required field '%s'" % (node_id, field_name))
    try:
        topo_order(nodes)
    except RuntimeError as e:
        errs.append(str(e))

    # EVERY SELECTABLE GOAL, not just the default. meta.goals is the single
    # roster `goals`, the new-game wizard and every --goal flag all read
    # (see data.py's goal_catalog/resolve_goal) - a goal naming a node that
    # does not exist would not fail anywhere else until a player actually
    # picked it, which is exactly the kind of bug this command exists to
    # catch before that.
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
    if errs:
        print("ERRORS:"); [print("  " + message) for message in errs]
    if warns:
        print("WARNINGS:"); [print("  " + message) for message in warns]

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
    if getattr(a, "deep", False) and not errs:
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

    if not errs:
        print()
        print("OK: tree is a valid DAG, fully priced, every selectable goal's "
              "closure and critical path compute cleanly.")
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
# already aged 35", see core.py's `life_left`). Multiplying those two is the
# expression that used to disagree with itself across two printed lines;
# now cmd_path's printed budget, cmd_path's feasibility judgement and
# cmd_why's "% of a life" figure all call this one function, so whatever
# DEFAULTS says, they cannot say two different things about it again.
#
# (2,000 * 28 = 56,000 today - neither of the two old literals. That is not
# a third guess: it is what the honest expression above comes to under
# today's DEFAULTS, and it is smaller than the "corrected" 60,000 the
# complaint itself flagged as the obvious-but-wrong fix, because 28 years
# is the figure the mortality model actually uses, not the round 30 the old
# print statement typed.)
def _founder_lifetime_hours(cfg=None):
    """Founder-hours a whole working life holds: hours/year * expected
    working years, both read from `cfg` if given (a live Sim's config, which
    may override either) and otherwise from DEFAULTS - the same source
    core.py reads `founder_hours_per_year` and `founder_life_mean` from for
    the founder's real hours ledger and real mortality draw. No caller of
    this function may re-derive or re-type either input; that duplication is
    exactly what let the two numbers drift apart before.
    """
    cfg = cfg or {}
    hours_per_year = cfg.get("founder_hours_per_year", DEFAULTS["founder_hours_per_year"])
    expected_working_years = cfg.get("founder_life_mean", DEFAULTS["founder_life_mean"])
    return hours_per_year * expected_working_years


def cmd_path(a):
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, a.goal)
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
    # used to be two separately typed numbers (60,000 printed, 72,000
    # judged) that could disagree, and did. Both now come from one call, so
    # they say the same thing about the same DEFAULTS whatever those are.
    lifetime_hours = _founder_lifetime_hours()
    print("\nFounder-hours available in one lifetime at %s/yr for %s yrs: %s" %
          (f"{DEFAULTS['founder_hours_per_year']:,.0f}",
           f"{DEFAULTS['founder_life_mean']:,.0f}",
           f"{lifetime_hours:,.0f}"))
    print("Founder-hours demanded by this path                          : %s" % f"{cum_ph:,.0f}")
    print("=> %s" % ("feasible alone in principle, but not with the calendar floors"
                     if cum_ph < lifetime_hours else
                     "IMPOSSIBLE for one person. You must convert your hours into other people's hours."))


def cmd_costs(a):
    tree, prices, nodes, wages, goods = load()
    rows = sorted(nodes.values(), key=lambda n: -n["_total_cost"])[:a.top]
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


def _wilson_interval(successes, n, z=_Z95):
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
    if n <= 0:
        return (0.0, 1.0)
    rate = successes / n
    z_squared = z * z
    denom = 1.0 + z_squared / n
    centre = rate + z_squared / (2 * n)
    margin = z * math.sqrt((rate * (1.0 - rate) + z_squared / (4 * n)) / n)
    lower = (centre - margin) / denom
    upper = (centre + margin) / denom
    return (max(0.0, lower), min(1.0, upper))


def _fmt_rate_ci(successes, n):
    """'k/n (p%)  95% CI [lo%, hi%]' - the point estimate never appears alone
    anywhere in this file's output. A bare percentage from a few dozen
    Monte Carlo trials invites a reader to treat it as a measurement with no
    error bar, which is exactly the failure this function exists to close."""
    lower, upper = _wilson_interval(successes, n)
    rate = 100.0 * successes / n if n else 0.0
    return ("%d/%d (%.1f%%)  95%% CI [%.1f%%, %.1f%%] (Wilson score)"
            % (successes, n, rate, 100.0 * lower, 100.0 * upper))


# How few successes is too few to trust a median/quartile year-to-goal? There
# is no sharp cutoff, but under ~10 the order statistics are individual data
# points wearing a statistic's clothing - a "median" of 1 or 3 observations
# is just one of those observations, arbitrarily labelled. Below this, print
# the raw values and say so, instead of a quartile table that implies a
# distribution nobody has actually sampled.
_MIN_SUCCESSES_FOR_QUANTILES = 10


def _summarise(results, label):
    run_count = len(results)
    finished = [run for run in results if run.goal_year]
    success_count = len(finished)
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
    # AGGREGATE PROGRESS, LEADING - not the success rate. A batch this small
    # against a multi-century, near-certain-to-fail-or-succeed goal can be a
    # ~1% event either way (this project's own default invocation has
    # measured 0/25 and 1/125), and a bare rate at that sample size invites
    # reading it as "the" result instead of one thing among several this
    # batch can actually support saying. How far every run got - not only
    # the ones that finished - is informative at any N, including this one.
    tech = sorted(len(run.done) for run in results)
    quantile_of = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]
    print()
    print("technologies completed (whole tree, across all %d run%s):"
          % (run_count, "" if run_count == 1 else "s"))
    print("   worst %d | p25 %d | median %d | p75 %d | best %d"
          % (tech[0], quantile_of(tech, .25), quantile_of(tech, .5), quantile_of(tech, .75), tech[-1]))
    need = closure(results[0].nodes, results[0].goal)
    needed_count = len(need)
    progress = sorted(len(need & run.done) for run in results)
    print("goal's own closure completed (%d node%s needed):"
          % (needed_count, "" if needed_count == 1 else "s"))
    print("   worst %d/%d | p25 %d | median %d | p75 %d | best %d/%d"
          % (progress[0], needed_count, quantile_of(progress, .25), quantile_of(progress, .5), quantile_of(progress, .75),
             progress[-1], needed_count))
    causes = defaultdict(int)
    for run in results:
        if run.dead_reason: causes[run.dead_reason.split(":")[0]] += 1
        elif not run.goal_year: causes["ran out of horizon"] += 1
    if causes:
        print("failure modes       :")
        for cause, value in sorted(causes.items(), key=lambda x: -x[1]):
            print("   %-58s %3d (%.0f%%)" % (cause, value, 100.0 * value / len(results)))
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
    # THE SUCCESS RATE, BELOW THE FOLD, NOT AS THE HEADLINE - see the "what
    # this measures" line above for why, and this project's own diagnosis
    # (planner.py's docstring) for the number that made the point concrete:
    # recommended.json reached the goal in 0% of trials on Rome at a
    # 700-year horizon, and a run pointed at a strategy like that used to
    # print exactly that lone, uninterpreted "0%" as its headline, with the
    # median-year line blank underneath it and nothing else on the screen to
    # explain either fact. The progress tables above already say how far
    # those same trials got; this says how many of them finished.
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
    shortage_counter = collections.Counter()
    for run in results:
        shortage_counter.update(run.shortages)
    if shortage_counter:
        # RELABELLED, NOT RECOMPUTED. This used to print the same summed
        # Counter under the label "(median run)" - it is a SUM across every
        # run, not a median of anything. A true per-material median across
        # runs would need each run's count (including the runs that were
        # never short of that material at all, i.e. zero) aligned key by
        # key, which is a real change to what gets computed, not just what
        # gets printed - out of scope here. Relabelling the existing number
        # honestly is the fix that belongs in a "what gets printed" pass.
        print("years spent short of a raw material (SUM across %d runs, not a median):" % run_count)
        for material, value in shortage_counter.most_common(5):
            print("   %-12s %d run-years" % (material, value))
    forest_hectares = sorted(run.forest_ha for run in results)
    print("coppice woodland owned: median %.0f hectares" % forest_hectares[len(forest_hectares) // 2])
    reputations = sorted(run.reputation for run in results)
    print("final reputation    : median %.0f/100" % reputations[len(reputations) // 2])
    bounty_payments = [run.bounties_paid for run in results]
    if any(bounty_payments):
        print("bounties posted     : mean %.1f per run" % (sum(bounty_payments) / len(bounty_payments)))


def cmd_run(a):
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(a, "goal", None))
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    deterministic = getattr(a, "deterministic", False)
    res = []
    for i in range(a.mc):
        rng = DetRNG(a.seed + i) if deterministic else random.Random(a.seed + i)
        run_result = Sim(nodes, order, rng, events=not a.no_events,
                cfg={"immortal": not a.mortal,
                     "start_capital": STARTING_KITS[a.kit]["den"]},
                civ=load_civ(a.civ),
                bounty_set=(set() if a.no_bounties else bounties)).run(goal, a.horizon)
        res.append(run_result)
    _summarise(res, "%s%s%s" % (label,
                                "  [events disabled]" if a.no_events else "",
                                "  [deterministic]" if deterministic else ""))
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
    if getattr(a, "save_winner", None):
        won = [run_result for run_result in res if run_result.goal_year]
        if not won:
            sys.stderr.write("no trial reached the goal, so there is no winning "
                             "order to save\n")
        else:
            best = min(won, key=lambda s: s.goal_year)
            # ONLY WHAT THE GOAL NEEDS. The first version of this saved every
            # node the winning trial finished - 2,676 of them - and feeding that
            # back scored 0% against the 25% of the strategy it was captured
            # from, because the optimizer then ground through hundreds of side
            # branches the trial had built for revenue before it reached the
            # work that mattered. A finish order over everything is not a plan.
            # The 149 nodes of the goal's closure, in the order a run that won
            # actually completed them, is.
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
                       % (a.seed + res.index(best), a.mc, a.civ, goal,
                          best.goal_year),
                       "A captured order is a floor on what is achievable, not a "
                       "recommendation: it carries whatever luck that trial had, "
                       "and it includes side branches that trial happened to "
                       "build and may not have needed."],
                   "order": seq}
            with open(a.save_winner, "w") as save_file:
                json.dump(out, save_file, indent=1)
            sys.stderr.write("saved the winning order (%d nodes, goal in %d AD) "
                             "to %s\n" % (len(seq), best.goal_year, a.save_winner))
    if a.trace:
        run_result = res[0]
        print("\n--- trace of run 0 ---")
        for year, message in run_result.log:
            print("  %4d  %s" % (year, message))


def cmd_compare(a):
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(a, "goal", None))
    for name in ["rush", "topo", "recommended"]:
        try:
            label, order, bounties = load_strategy(name, nodes, goal)
        except SystemExit:
            continue
        # At 3000 nodes a full comparison takes tens of minutes. Without this
        # line, and without the flushes below, the command looks hung: stdout
        # is block-buffered when redirected, so nothing at all appeared until
        # the very end.
        sys.stderr.write("  running %s: %d trials...\n" % (name, a.mc))
        sys.stderr.flush()
        # COMMON RANDOM NUMBERS, ON PURPOSE. random.Random(a.seed + i) is
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
        deterministic = getattr(a, "deterministic", False)
        res = [Sim(nodes, order,
                   DetRNG(a.seed + i) if deterministic else random.Random(a.seed + i),
                   events=True,
                   cfg={"immortal": not getattr(a, "mortal", False),
                        "start_capital": STARTING_KITS.get(getattr(a,"kit","poor_scholar"),
                                                           STARTING_KITS["poor_scholar"])["den"]},
                   civ=load_civ(getattr(a, "civ", "rome_100ad")),
                   bounty_set=bounties).run(goal, a.horizon)
               for i in range(a.mc)]
        _summarise(res, "%s%s" % (label, "  [deterministic]" if deterministic else ""))
        sys.stdout.flush()


def _civ_for_session(a):
    """Which civilisation to start, honouring the save above the command line.

    A save says what game it is. Resuming should not need the flag repeated,
    and a flag that contradicts the file should say so rather than start the
    wrong game over the top of it - a playtester was handed
    `play --session england_1300.json` by the game itself and refused by it.
    """
    session = getattr(a, "session", None)
    asked = getattr(a, "civ", None)
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


def _goal_for_session(a, tree, nodes):
    """Which goal to start the strategy order for, honouring the save above
    the command line - same reasoning and same shape as _civ_for_session
    just above, and for the same reason: the order `load_strategy` hands
    back depends on the goal's own closure (see load_strategy's goal
    argument), so a resumed game has to know its goal BEFORE that call, not
    only after load_state runs.
    """
    session = getattr(a, "session", None)
    asked = getattr(a, "goal", None)
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
    `a.horizon` whether or not anyone typed it. A flag typed by hand always
    outranks anything remembered from an earlier sitting."""
    return any(tok == "--horizon" or tok.startswith("--horizon=")
              for tok in sys.argv)


def _resolve_horizon(a, session):
    """How many years this sitting gets: the --horizon flag if it was
    actually typed, otherwise whatever the horizon was last set to for this
    save (see the in-game 'options' command and the New Game wizard, both of
    which write it to session.meta.json - see settings.py's module docstring
    for why that lives beside the save rather than inside it), otherwise the
    flag's ordinary default. A save nobody ever touched 'options' or the menu
    for has no meta file, so this returns exactly a.horizon and nothing about
    the flag-driven path changes.
    """
    if session and not _horizon_explicit():
        meta = settings.load_session_meta(session)
        horizon_years = meta.get("horizon_years")
        if isinstance(horizon_years, (int, float)) and horizon_years > 0:
            return int(horizon_years)
    return a.horizon


def cmd_play(a):
    """The game, typed, for a person at a keyboard.

    This used to be its own little REPL with six commands of its own - next
    year, available, status, start, stop, quit - and its own copy of what each
    one meant. Everything built since (money, hire, fire, train, work,
    commission, labour, policy, quote, close, mothball, restore, bribe, risk,
    save, load) went into the JSON protocol and none of it into here, so the
    human front door showed a fraction of the game and the menu's answer was to
    put a person in front of a JSON prompt.

    It now parses a typed line into the SAME command the JSON protocol takes
    (protocol.parse_typed) and hands it to the SAME dispatcher (_agent_dispatch),
    printing the readable rendering the --pretty path already uses. There is no
    second implementation to fall behind: a command added to the protocol is
    typeable here the day it is added.

    It is also always manual. The old default mode let the optimizer keep
    starting things regardless of what you typed, and its own docstring called
    that "advisory, not a real choice". A front door should not be the mode
    where your choices do not count; `run --trace` is still the way to watch
    the optimizer work.
    """
    # THE APPLICATION'S OWN PREFERENCES, APPLIED ONCE, HERE - not only from
    # the menu. `play` typed directly (no menu at all) is still a human at a
    # keyboard, on their own terminal, and display width/rows-per-page/
    # whether the tutorial prints are preferences about THAT, not about
    # which flags were passed - see _apply_display_prefs and settings.py's
    # module docstring. None of this touches `agent`. Named app_cfg, not
    # cfg: `cfg` below is the Sim's own config dict (immortal/horizon_years/
    # start_capital) and already existed under that name; the two must not
    # collide.
    app_cfg = _apply_display_prefs()
    tree, prices, nodes, wages, goods = load()
    goal = _goal_for_session(a, tree, nodes)
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    session = getattr(a, "session", None)
    # HOW MANY YEARS THIS SITTING GETS. Ordinarily just the --horizon flag,
    # but a save the New Game wizard started or the in-game 'options' command
    # touched remembers its own horizon between sittings - see
    # _resolve_horizon and settings.py's module docstring for why that is not
    # simply part of the save file. A flag typed by hand always wins.
    horizon = _resolve_horizon(a, session)
    cfg = {"immortal": not getattr(a, "mortal", False),
           "horizon_years": horizon}
    kit = getattr(a, "kit", None)
    if kit:
        cfg["start_capital"] = STARTING_KITS[kit]["den"]
    sim = Sim(nodes, order,
            DetRNG(a.seed) if getattr(a, "deterministic", False) else random.Random(a.seed),
            events=True, bounty_set=set(),
            manual=True, civ=load_civ(_civ_for_session(a)), cfg=cfg)
    sim.goal = goal
    sim.done_year = {}
    sim.end_year = sim.cfg["start_year"] + horizon
    sim.fog = bool(getattr(a, "fog", False))
    sim.revealed = set()
    # The reader is a person typing words, so the worked examples inside every
    # reply should be words too. See protocol.to_typed_hints.
    _protocol.TYPED_HINTS = True
    _protocol.MONEY_SHORT = money_short(sim.civ)

    # A --session THAT DOES NOT EXIST IS A TYPO, NOT AN INVITATION. Naming a
    # save file that is not there used to start a brand new default game -
    # Rome 100 AD, whatever you were playing - and then write it over that
    # filename on the first command. A tester nearly lost a forty-year England
    # run to a mistyped path. Starting a new game is what you do by naming a
    # civilisation, so require that to be explicit.
    if session and not os.path.exists(session) and not getattr(a, "civ", None):
        print("there is no save at %r, and no --civ given, so I do not know "
              "what game you meant. To resume, check the path; to start a new "
              "game there, say which civilisation with --civ." % session)
        return 1
    fresh = not (session and os.path.exists(session)) or _is_claimed_slot(session)
    # A CHECKPOINT DOES NOT GET AUTOSAVED OVER, EVER - see settings.is_checkpoint's
    # own comment for the whole story. `checkpoint_source` stays None for an
    # ordinary resume, in which case nothing below this differs from before:
    # `session` keeps naming the same file it always did, and it goes on
    # autosaving to it after every command, exactly as an ongoing session
    # always has. Only when the file being resumed is a frozen milestone does
    # `session` get reassigned - to a freshly claimed file, the same way a
    # brand new game's session file is claimed (_pick_session_filename) - so
    # that looking at a checkpoint to diagnose something never becomes the act
    # that moves it.
    checkpoint_source = None
    if not fresh:
        try:
            load_state(sim, session)
        except Exception as e:
            print("could not read the save file %r: %s" % (session, e))
            return 1
        if settings.is_checkpoint(session):
            checkpoint_source = session
            session = _pick_session_filename(sim.civ.get("id") or "game")
        else:
            print("Resumed from %s: %d AD." % (session, sim.year))

    if (fresh or checkpoint_source) and session:
        # WRITE IT NOW, not after the first command. The menu tells the player
        # "Saved to X. Come back with ..." and a break tester quit before
        # typing anything, found no file, followed the printed line anyway and
        # was dropped into a different civilisation's fresh game. A save the
        # game has promised has to exist from the moment it is promised. The
        # same promise holds for a checkpoint's forked session file: it has
        # been named out loud below, so it has to be real from that moment on.
        save_state(sim, session)
    if checkpoint_source:
        print("Resumed the checkpoint at %s: %d AD. A checkpoint stays "
              "exactly as it is - nothing you do now writes back into it. "
              "From here on, this game is autosaving to %s instead."
              % (checkpoint_source, sim.year, session))
    # THE WELCOME AND TUTORIAL TEXT IS A PREFERENCE NOW (Options: "show the
    # welcome message and tutorial on new games"). A player on their fifth
    # new game does not need the five starter verbs explained again every
    # time; a player who has never seen this game does. Gated as one block,
    # not line by line, because it is all the same kind of text - what a
    # first-timer needs and nobody else does - and a veteran who has turned
    # it off still gets the arrival capital/year from 'state' on request.
    if fresh and app_cfg.get("show_welcome", True):
        print()
        print(_wrap("You arrive in %d AD with %d %s and nothing else: no "
                    "employees, no slaves, and nobody who owes you anything. "
                    "What you have is everything you know."
                    % (sim.year, sim.capital, money_word(sim.civ))))
        # THE KIT SAID 4,000 AND YOU ARRIVED WITH 3,000, SILENTLY. Every
        # kit's figure (STARTING_KITS) is priced in Rome 100 AD denarii, the
        # same currency project_cost and everything else is calibrated
        # through - see price_index's own comment in data.py - and is then
        # converted at THIS civilisation's prices before a denarius of it
        # ever reaches the ledger. A blind Han playthrough picked "merchant,
        # 4,000 den" off the kit list and read "You arrive ... with 3000
        # cash" one screen later with no statement anywhere that the two
        # numbers were the same kit. The arithmetic was always right; only
        # the silence was a bug.
        if kit and abs(sim.price_index - 1.0) > 0.002:
            _quoted = STARTING_KITS.get(kit, {}).get("den")
            if _quoted:
                print(_wrap('The "%s" kit is quoted in Rome\'s prices (%d den); '
                            "here, prices run at %.3gx Rome's, so that arrived "
                            "as %d %s, not %d."
                            % (kit, _quoted, sim.price_index, sim.capital,
                               money_word(sim.civ), _quoted)))
        print()
        # `open` BELONGS IN THE OPENING. Finishing a project earns you
        # nothing until you open its doors, auto_open ships off for a player
        # by design, and this list of what to type first did not mention it -
        # so a play tester finished seven concerns worth 1,713 a year, left
        # every one of them shut, and walked into a debt spiral in year three.
        # The one rule a first-timer must know cannot be the one thing the
        # first screen leaves out.
        print(_wrap("Type commands in plain words. The five to start with are "
                    "'state' (where you stand), 'available' (what you could "
                    "begin today), 'why <name>' (what a thing is for and what "
                    "it costs), 'start <name>' (begin it) and 'step' (let a "
                    "year pass). When something is FINISHED it earns nothing "
                    "until you 'open' it. 'stuck' says why you are not getting "
                    "on; 'quit' leaves."))
        print()
        # THE FIVE ABOVE ARE A START, NOT THE WHOLE GAME, and saying so only
        # in passing - "'help' explains the rest", one clause at the end of a
        # paragraph about something else - undersold it badly: a player who
        # went on to win the entire game reported believing there were only
        # five help topics in total, and reached for `help` for the first
        # time only once a command she typed did not exist. There are far
        # more commands than these five, and `help` is where the rest of them
        # actually live, a topic at a time - named here, not left as a single
        # word to take on faith.
        print(_wrap("These five are a beginning, not the whole of it - there "
                    "are far more commands than this. 'help' lists the rest, "
                    "one topic at a time: %s. Reach for it the moment you "
                    "type a word the game does not know, not only once you "
                    "are stuck." % ", ".join(_protocol.HELP_TOPICS)))
        # THE WALKTHROUGH, NOT BURIED. `path <goal>` lays out everything
        # still standing between here and one thing AND which of it you
        # could start today, and it used to be findable only inside `help
        # commands`. An England player spent about forty minutes guessing
        # before finding it and said it reorganized the rest of play once
        # they had; two other players separately asked for exactly the join
        # it does. It has no business being harder to find than the five
        # above, once a player has a goal in mind - which, on arrival, they
        # already do.
        if not sim.fog:
            print()
            print(_wrap("Once you have a goal in mind: 'path <name>' lays "
                        "out everything still standing between here and "
                        "there, and which of it you could start TODAY. "
                        "This is the walkthrough."))
        print()
        print(_wrap("'options' shows the few things you can change without "
                    "restarting - right now, the horizon and whether the "
                    "founder can die of old age - and where this game is "
                    "being saved."))
        print()

    while True:
        # The same figure state reports: the pool LESS hours already sold for
        # wages. The prompt disagreeing with state about the one number on it
        # is how a tester found the accounting wrong in the first place.
        free_hours = max(0.0, sim.director_pool() - sim.director_hours_committed())
        # The prompt is built here and never passes through the renderer, so it
        # was the last place still saying "den" in a game counted in pence.
        # THE SAME TWO NUMBERS `why` PRINTS, for the same reason the hours
        # figure above matches state's: the prompt showed hired heads only
        # (s.scholars, s.artisans) while `why` compares a project's
        # requirement against effective_scholars() and craft_hands_available()
        # - both of which count the founder, and the second of which counts
        # hours under contract. A play tester read "sch 0 art 0" in the prompt
        # and "(you have 1, 0)" in `why` on the same turn and reported the
        # game as having lost count of their staff.
        prompt = ("[%d AD | %d %s | you:%d hr | sch %.0f art %.0f | rep %.0f] > "
                  % (sim.year, sim.capital, money_short(sim.civ), free_hours,
                     sim.effective_scholars(), sim.craft_hands_available(),
                     sim.reputation))
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            # Piped input runs out, and a person presses ctrl-D. Neither is a
            # crash, and the old loop raised EOFError out of the process.
            print()
            break
        # 'options' IS ANSWERED HERE, NOT BY THE DISPATCHER. It changes
        # things about the SITTING (the horizon, mortality, where this save
        # lives) rather than the game state the JSON protocol speaks about,
        # so it never becomes a command an agent script could send - see
        # _ingame_options and settings.py's module docstring for what it
        # covers and why each of those, specifically, is honest to change
        # without restarting.
        _tokens = line.strip().split()
        _word0 = _tokens[0].lower() if _tokens else ""
        if _word0 in ("options", "option", "settings"):
            session = _ingame_options(sim, session)
            continue
        # SESSION COMMANDS, BARE ONLY - see the block comment above
        # _ingame_saves for why these four exist and why each is intercepted
        # here rather than reaching parse_typed. 'save <file>'/'load <file>'
        # WITH an argument are deliberately left alone: those still fall
        # through to the JSON protocol's own sandboxed save/load below,
        # unchanged from before any of this existed.
        if _word0 == "saves" and len(_tokens) == 1:
            _ingame_saves(app_cfg, session)
            continue
        if _word0 == "save" and len(_tokens) == 1:
            _ingame_save_milestone(sim, session)
            continue
        if _word0 == "load" and len(_tokens) == 1:
            session = _ingame_load(app_cfg, sim, session, a)
            continue
        if _word0 == "menu" and len(_tokens) == 1:
            # NOT A LOSS. This game has already been saved after every
            # command that reached this point (see "SAVE FIRST, THEN SPEAK"
            # below) and --session itself is untouched - 'menu' only means
            # "I am done looking at this one for now", and cmd_menu's own
            # Load screen (or a bare resume with --session) is how to come
            # straight back to it.
            print()
            return cmd_menu(a)
        if _word0 == "restart" and len(_tokens) == 1:
            _confirm = _ask("   Start a different game? This one stays "
                            "exactly as saved, and you can resume it later. "
                            "[y/N] ", ["y", "n"], "n")
            if _confirm == "y":
                print()
                return _new_game(_load_civ_list(), app_cfg)
            continue
        cmd, err = parse_typed(line)
        if err:
            print("   " + err)
            continue
        if cmd is None:
            continue
        # HOW LONG THAT TOOK. Agents play this game as well as people do, and
        # an agent has no feel for which commands are slow: it cannot notice
        # that `step 50` always takes a while the way a person drumming their
        # fingers does, so it cannot tell you, and a real complaint about speed
        # goes unreported for rounds. Measured from the command being accepted
        # to its output being rendered, which is the interval the player
        # actually waits through.
        _t0 = time.time()
        try:
            resp = _agent_dispatch(sim, nodes, cmd)
        except Exception as e:            # never lose a session to a bug
            resp = {"ok": False,
                    "error": "internal error handling that command: %s: %s. "
                             "The game is intact; try something else."
                             % (type(e).__name__, e)}
        # SAVE FIRST, THEN SPEAK. The state change is already committed by the
        # time we get here, so writing it must not be contingent on the output
        # succeeding. A weird-play tester piped the game through `head`, which
        # closed the pipe and killed the process on the first print - and
        # twelve years of play went with it, twice, in a game whose own help
        # promises "progress is written to this file after every command...
        # close the terminal, anything".
        if session:
            save_state(sim, session)
        try:
            # 'state json' / 'portfolio json' / 'risk json': the raw reply,
            # one line, instead of the rendered screen. Every player of this
            # game is an AI agent parsing text, and several have lost runs
            # to parsing a prose table that was never meant to be a machine
            # interface - `agent` already gives a script this on every
            # command; this is the same line, on demand, inside `play`. It
            # is THE SAME resp dict `render_pretty` below would otherwise
            # render, produced by the one dispatcher both paths call, so
            # the prose and this JSON can never disagree about what
            # happened, and fog is scrubbed exactly once, upstream of both.
            if cmd.get("json"):
                _text = json.dumps(resp)
            else:
                _text = render_pretty(cmd.get("cmd"), resp)
            _took = time.time() - _t0
            # Only when it is worth knowing. A tenth of a second on every line
            # is noise that would bury the one command that took nine seconds.
            print(_text + ("\n   (took %.1fs)" % _took if _took >= 0.5 else ""))
            print()
        except BrokenPipeError:
            # Somebody closed the pipe. The game is saved; leave quietly.
            try:
                sys.stdout.close()
            except Exception:
                pass
            break
        if cmd.get("cmd") == "quit":
            break
        # NOT A BREAK. This used to end the process the moment the horizon was
        # reached, so a weird-play tester who ran out of years could type
        # exactly one more command and was then dropped back to the shell,
        # unable to read their own final position. The dispatcher already
        # refuses anything that would move the game on once it has ended; what
        # is left is looking at it, which is the whole point of finishing.
        end = _agent_end_reason(sim)
        if end and not getattr(a, "_said_end", False):
            a._said_end = True
            # THE SCOREBOARD, not one sentence. See protocol.final_report.
            print(render_final(final_report(sim, nodes)))
            print()
            print(_wrap("You can still look at anything; 'quit' when you are "
                        "done."))
            print()
    if _agent_end_reason(sim) and not getattr(a, "_said_end", False):
        print(render_final(final_report(sim, nodes)))
        print()
    print("Ended %d AD. %s" % (sim.year, _agent_end_reason(sim) or "stopped"))
    if session:
        print("Saved to %s. Come back with:" % session)
        print("   python3 sim/simulator.py play --session %s" % session)
    return 0


# THE SAME FLOOR core.py's Sim.__init__ APPLIES AT YEAR ZERO (see
# _ingame_options below, "THE SAME DRAW core.py's Sim.__init__ makes"), kept
# as its own declared name because core.py has not migrated its own copy to
# declare() yet - two independent literals with the same value, not one
# shared source, so a change to one will not reach the other.
INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS = declare(
    "INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS", 5, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Floor under the gaussian draw for a founder's remaining lifespan, "
        "so a bad roll (or a mean/sd combination that puts real weight below "
        "zero) cannot hand a newly-mortal founder a negative or "
        "vanishingly short life. Not derived from any mortality curve; "
        "picked to guarantee a few years of remaining play regardless of "
        "the draw.")


def _ingame_options(s, session):
    """The 'options' command, typed mid-game. Returns the session path to use
    from here on (unchanged, unless 'move this save' was used).

    ONLY THE THINGS THAT ARE HONEST TO CHANGE WITHOUT RESTARTING ARE OFFERED
    HERE. Three of the five things a new game asks about are NOT, on purpose:

      - civilisation: the whole world (prices, values, what is missing, what
        is coming) is keyed to it. There is no "change civilisation" that
        would not just be starting a different game while pretending to be
        this one.
      - starting kit: it names an amount of money the founder arrived with.
        The founder arrived however many years ago this save's year 1 was;
        re-picking that now would only ever mean handing yourself money you
        did not start with, i.e. cheating, dressed as a settings screen.
      - fog of war: see protocol.load_state's own comment on this - a save
        played with fog cannot be resumed without it, because there is no
        way to make a player un-know the whole tree they have already seen.
        The reverse is just as dishonest: turning fog ON after playing
        without it would claim to hide a tree this sitting has already been
        shown in full.

    Horizon and mortality are not like that. The horizon is a date the
    player is choosing to stop by, not a fact about the world - moving it,
    either direction, changes nothing about what has already happened.
    Mortality can honestly move exactly one way: choosing, from this year on,
    to let the founder age and die is a real choice a person can make midway
    through anything; choosing to UNDO having already accepted that is not a
    choice available to anyone in this founder's position, so it is not
    offered here either - see the menu below, which only ever offers "on".
    """
    while True:
        mortal_on = not s.cfg.get("immortal", True)
        cur_end = getattr(s, "end_year",
                          s.cfg["start_year"] + s.cfg.get("horizon_years", 500))
        print()
        print("-" * 78)
        print("   OPTIONS")
        print("-" * 78)
        print("   civilisation : %s, %d AD                (fixed for this game)"
              % (s.civ.get("name", s.civ.get("id", "?")), s.cfg["start_year"]))
        print("   fog of war   : %-3s                          (fixed for this game)"
              % ("on" if getattr(s, "fog", False) else "off"))
        print("   mortality    : %s"
              % ("on - the founder ages, and can die of it" if mortal_on
                 else "off - the founder does not age"))
        # NO DEADLINE, SAID PLAINLY - not a nine-digit year nobody asked to
        # read. Endless is still, underneath, the large-but-ordinary number
        # ENDLESS_HORIZON_YEARS describes (see its own comment on why); this
        # is the one screen in cli.py that knows that and says the honest
        # thing instead of the literal one.
        if _is_endless_horizon(cur_end, s.cfg["start_year"]):
            print("   horizon      : none - Endless. Play until you choose to stop.")
        else:
            print("   horizon      : ends %d AD  (now %d AD, %d years left)"
                  % (cur_end, s.year, max(0, cur_end - s.year)))
        print("   this save    : %s"
              % (session or "(not being saved anywhere - restart with --session "
                            "to change that)"))
        print()
        print("   1) change the horizon")
        print("   2) turn mortality on from this year forward%s"
              % ("  (already on)" if mortal_on else ""))
        if session:
            print("   3) move this save to a different file")
        print("   b) back to the game")
        try:
            raw = input("\n   > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return session
        word = raw.split()[0] if raw.split() else ""

        if word in ("", "b", "back"):
            return session

        elif word in ("1", "horizon"):
            try:
                raw2 = input("   New end year (a whole number of AD, > %d), "
                             "or 'endless' for no deadline at all: "
                             % s.year).strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                print("   -- unchanged.")
                continue
            if raw2.lower() in ("endless", "none", "forever", "no deadline",
                               "no limit", "unlimited"):
                new_end = s.year + ENDLESS_HORIZON_YEARS
            else:
                try:
                    new_end = int(raw2)
                except ValueError:
                    print("   -- that is not a whole number of years, or "
                          "'endless'.")
                    continue
                if new_end <= s.year:
                    print("   -- %d AD has already passed (or is now); the "
                          "game would end the moment you left this menu. Pick "
                          "a later year." % new_end)
                    continue
            new_horizon = new_end - s.cfg["start_year"]
            s.end_year = new_end
            s.cfg["horizon_years"] = new_horizon
            if session:
                meta = settings.load_session_meta(session)
                meta["horizon_years"] = new_horizon
                settings.save_session_meta(session, meta)
            print("   -- done. This game now has no deadline (Endless)."
                  if _is_endless_horizon(new_end, s.cfg["start_year"]) else
                  "   -- done. This game now ends in %d AD." % new_end)

        elif word in ("2", "mortal", "mortality") and not mortal_on:
            print(_wrap("From this year on the founder ages, and can die of "
                        "it, the same as anyone in this world - see 'why' on "
                        "any of the nodes that outlive one lifetime. This "
                        "cannot be undone: there is no honest way to give "
                        "the founder back an immortality already spent part "
                        "of a life without."))
            confirm = _ask("   Turn mortality on now? [y/N] ", ["y", "n"], "n")
            if confirm == "y":
                # THE SAME DRAW core.py's Sim.__init__ makes for a mortal
                # founder at year zero (self.life_left = ... rng.gauss(...)),
                # made here instead because that constructor only ever runs
                # once, at the start of the game, and this founder is
                # choosing to become mortal partway through it. See core.py
                # around "founder remaining lifespan" for the line this
                # mirrors.
                mean = s.cfg.get("founder_life_mean", DEFAULTS["founder_life_mean"])
                std_dev = s.cfg.get("founder_life_sd", DEFAULTS["founder_life_sd"])
                s.cfg["immortal"] = False
                s.life_left = max(INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS,
                                  s.rng.gauss(mean, std_dev))
                s.founder_alive = True
                print("   -- done. Mortality is on from %d AD." % s.year)
            else:
                print("   -- unchanged.")

        elif word in ("3", "move", "movesave") and session:
            try:
                raw3 = input("   New path for this save (ending .json): ").strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw3:
                print("   -- unchanged.")
                continue
            newp = os.path.expanduser(raw3)
            if not newp.lower().endswith(".json"):
                newp += ".json"
            if os.path.abspath(newp) == os.path.abspath(session):
                print("   -- that is where it already is.")
                continue
            if os.path.exists(newp):
                print("   -- %s already exists; pick a name that is not taken."
                      % newp)
                continue
            try:
                parent = os.path.dirname(os.path.abspath(newp))
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent, exist_ok=True)
                save_state(s, newp)
            except OSError as e:
                print("   -- could not write there: %s" % e)
                continue
            settings.move_session_meta(session, newp)
            old = session
            session = newp
            try:
                os.remove(old)
            except OSError:
                pass
            print("   -- moved. This game now saves to %s" % session)
            print("   Come back to it with:")
            print("      python3 sim/simulator.py play --session %s" % session)

        else:
            print("   -- not a choice right now.")


# ----------------------------------------------------------------------------
# SESSION COMMANDS, TYPED DIRECTLY WHILE PLAYING - no backing out to the main
# menu and back in. A player who had just won the whole game said autosaves
# plus the manual saves they made at moments that mattered to them were a
# real part of how they played, and none of 'saves' (what do I have),
# 'load' (switch to a different one) or 'menu' (go back without losing this
# one) existed as something you could simply type. 'save <file>' and
# 'load <file>' already worked mid-game - they are the JSON protocol's own
# sandboxed commands (see protocol.py's SAVE_SUFFIXES/_unsafe_path and help
# topic 'save'/'load'), reachable here because cmd_play's loop hands every
# typed line to the same parser and dispatcher the JSON protocol uses. What
# did not exist was anything that knows about the SAVE DIRECTORY cli.py
# itself manages (settings.resolve_save_dir, settings.list_saves) - the bare
# forms below, intercepted in cmd_play before a line ever reaches that
# parser, the same way 'options' already is.
# ----------------------------------------------------------------------------

def _ingame_saves(cfg, session):
    """'saves', typed bare mid-game: what is in the configured save
    directory, without leaving for the main menu's Load screen. Read-only -
    'load', typed bare, is what switches this session to one of them."""
    save_dir, rows, civ_index, need = _save_listing(cfg)
    print()
    print("-" * 78)
    print("   SAVES  (in %s)" % save_dir)
    print("-" * 78)
    if not rows:
        print(_wrap("Nothing there yet."))
        print()
        return
    cur_abs = os.path.abspath(session) if session else None
    for i, row in enumerate(rows, 1):
        marker = ("<- this game" if cur_abs
                  and os.path.abspath(row["path"]) == cur_abs else None)
        _print_save_row(i, row, civ_index, need, marker)
    print(_wrap("'load' switches this session to one of these; 'save' on "
                "its own keeps a new copy of exactly this moment, alongside "
                "whatever this game is already autosaving to."))
    print()


def _pick_milestone_filename(civ_id):
    """A distinct filename for a manual, in-play 'save' - never the name
    --session is already autosaving to, so a milestone asked for by name is
    never quietly overwritten by the very next ordinary turn's autosave.
    Same claim-by-creating discipline as _pick_session_filename, for the
    same reason: two milestones saved in the same second must not collide."""
    save_dir = settings.resolve_save_dir()
    prefix = os.path.join(save_dir, civ_id) + "_saved_"
    attempt = 1
    while True:
        candidate = "%s%d.json" % (prefix, attempt)
        try:
            os.close(os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644))
            return candidate
        except FileExistsError:
            attempt += 1
        except OSError:
            return candidate


def _ingame_save_milestone(s, session):
    """'save', typed bare mid-game (no filename): a snapshot of exactly this
    moment, kept in the managed save directory alongside whatever --session
    is already autosaving to - so a player can come back to THIS point
    later even after the ongoing game has moved well past it. 'save <file>'
    with a name is untouched: that is still the JSON protocol's own
    sandboxed save, a relative path beside wherever the game was started."""
    path = _pick_milestone_filename(s.civ.get("id") or "game")
    try:
        save_state(s, path)
    except OSError as e:
        print("   -- could not write there: %s" % e)
        return
    # MARKED AS FROZEN, in the file's own sidecar - not only by its name. See
    # settings.is_checkpoint for why both signals exist: the filename alone
    # (matched by _pick_milestone_filename's own pattern) already says this is
    # a milestone, but this marker is what keeps that true if the file is
    # later renamed through the game's own "move this save" option, which
    # already carries a sidecar's fields to the new name
    # (settings.move_session_meta).
    settings.save_session_meta(path, {"checkpoint": True})
    print("   -- saved a copy of %d AD to %s" % (s.year, path))
    if session:
        print("      (this game's ongoing save at %s is untouched, and keeps "
              "saving after every command as before)" % session)


def _ingame_load(cfg, s, session, a):
    """'load', typed bare mid-game: switch this running game to a different
    save in the managed directory, without going back to the main menu.
    Returns the session path to use from here on - unchanged if nothing was
    picked or the load was refused. 'load <file>' with a name is untouched:
    that is still the JSON protocol's own sandboxed relative load.

    A save from a different civilisation is refused, loudly, by load_state
    itself (_validate_save checks `_civ` against this running game's own) -
    not re-checked here, so there is exactly one place that decides it.
    """
    save_dir, rows, civ_index, need = _save_listing(cfg)
    print()
    print("-" * 78)
    print("   LOAD A DIFFERENT SAVE  (in %s)" % save_dir)
    print("-" * 78)
    if not rows:
        print(_wrap("Nothing there to switch to."))
        print()
        return session
    for i, row in enumerate(rows, 1):
        _print_save_row(i, row, civ_index, need)
    print("   b) never mind, keep playing this one")
    try:
        raw = input("\n   Which one? [1-%d, or b] " % len(rows)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(); return session
    if raw in ("", "b", "back", "q", "quit"):
        return session
    if not (raw.isdigit() and 1 <= int(raw) <= len(rows)):
        print("   -- a number from the list above, or b.")
        return session
    chosen = rows[int(raw) - 1]["path"]
    try:
        load_state(s, chosen)
    except Exception as e:
        print("   -- could not load %s: %s" % (chosen, e))
        return session
    # THE HORIZON, AGAIN, THE SAME WAY _resolve_horizon DOES AT STARTUP. It
    # is not part of what load_state restores (see settings.py's module
    # docstring) - it lives in a sidecar keyed to THIS filename, so switching
    # files means reading that file's own sidecar, not keeping whatever
    # horizon the game just left behind.
    meta = settings.load_session_meta(chosen)
    horizon_years = meta.get("horizon_years")
    if isinstance(horizon_years, (int, float)) and horizon_years > 0:
        s.cfg["horizon_years"] = int(horizon_years)
        s.end_year = s.cfg["start_year"] + int(horizon_years)
    # A STALE "already said the ending" FLAG WOULD LIE HERE TWICE OVER: it
    # could suppress the scoreboard for a save that HAD already ended, or
    # (after this session later ends on its own) skip announcing THAT ending
    # because some earlier game's flag was still set. Either way, a load is
    # a new look at a position this process has not narrated yet.
    a._said_end = False
    # A CHECKPOINT SWITCHED TO IS STILL A CHECKPOINT - same guarantee as a
    # checkpoint named on the command line (see cmd_play's own comment on
    # `checkpoint_source`, right above the equivalent check there): switching
    # this running game to a frozen milestone must not turn the very next
    # command into the write that unfreezes it. This is the one other place
    # besides cmd_play/cmd_agent that can point the ongoing autosave at a
    # file, so it needs the identical fork.
    if settings.is_checkpoint(chosen):
        forked = _pick_session_filename(s.civ.get("id") or "game")
        save_state(s, forked)
        print("   -- switched to the checkpoint at %s: %d AD. A checkpoint "
              "stays exactly as it is - nothing you do now writes back into "
              "it. From here on, this game is autosaving to %s instead."
              % (chosen, s.year, forked))
        return forked
    print("   -- switched to %s: %d AD." % (chosen, s.year))
    return chosen


# ----------------------------------------------------------------------------
# Machine-playable interface: `agent`
#
# See the module docstring for the protocol table. In short: every line in,
# every line out, is one JSON object. `state` reports; `start`/`stop`/`bounty`/
# `buy` act; `step` advances the calendar. It is built on the same Sim.manual
# and start_project()/stop_project() this file's step()/can_start() comments
# already explain, so an agent driving this gets EXACTLY the consequences of
# its own choices, nothing the optimizer would have chosen for it.
# ----------------------------------------------------------------------------


def cmd_agent(a):
    """Machine-playable driver: JSON in, JSON out. See the module docstring for
    the protocol. Runs in Sim.manual mode ALWAYS, regardless of any other flag:
    the entire point of this command is that a script chooses the research
    path, so the optimizer's own auto-start (step() 4b) is never in play here.
    That is different from `play --manual`, which is the same guarantee for a
    human at a keyboard; `agent` is that guarantee for a script or an LLM.
    """
    tree, prices, nodes, wages, goods = load()
    goal = _goal_for_session(a, tree, nodes)
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    # `run`/`compare`/`play` all take --mortal; `agent` silently did not, so
    # the founder was immortal in every scripted or JSON-driven game no
    # matter what was asked for - and the menu (below) was printing a
    # "--mortal" flag on its suggested agent command line that argparse would
    # have rejected outright, because the flag did not exist here at all.
    cfg = {"start_capital": STARTING_KITS[a.kit]["den"], "horizon_years": a.horizon,
           "immortal": not getattr(a, "mortal", False)}
    sim = Sim(nodes, order,
            DetRNG(a.seed) if getattr(a, "deterministic", False) else random.Random(a.seed),
            events=not a.no_events,
            cfg=cfg, civ=load_civ(_civ_for_session(a)), bounty_set=set(), manual=True)
    sim.goal = goal
    sim.done_year = {}
    sim.end_year = sim.cfg["start_year"] + a.horizon
    sim.fog = bool(getattr(a, "fog", False))
    sim.revealed = set()
    pretty = bool(getattr(a, "pretty", False))

    session = getattr(a, "session", None)
    checkpoint_source = None
    if session and os.path.exists(session) and not _is_claimed_slot(session):
        try:
            load_state(sim, session)
        except Exception as e:
            sys.stdout.write(json.dumps(
                {"ok": False, "error": "could not read the save file %r: %s" % (session, e)}
            ) + "\n")
            return 1
        # A FROZEN CHECKPOINT DOES NOT BECOME THE AUTOSAVE TARGET HERE EITHER
        # - same fix, same reason, as cmd_play's own `checkpoint_source` (see
        # its comment there for the whole story). `agent` has no screen to
        # print prose to, so this is said on stderr instead, the same channel
        # the opening "welcome" briefing already uses for anything the
        # protocol itself did not ask for.
        if settings.is_checkpoint(session):
            checkpoint_source = session
            session = _pick_session_filename(sim.civ.get("id") or "game")
            save_state(sim, session)
            sys.stderr.write(json.dumps(
                {"checkpoint_resumed":
                 "%s is a frozen checkpoint; nothing further is written back "
                 "into it. This run is autosaving to %s instead."
                 % (checkpoint_source, session)}) + "\n")
            sys.stderr.flush()

    def emit(obj, op=None):
        # THE JSON LINE IS UNCHANGED, ALWAYS, REGARDLESS OF --pretty. It is
        # written first, exactly as before pretty rendering existed, so a
        # script reading only stdout sees byte-identical output whether or
        # not a human also asked for a readable view. The readable view - if
        # asked for - is a SEPARATE line on stderr, alongside the JSON, never
        # instead of it, so nothing that parses stdout has to change either.
        #
        # ALLOWED TO RAISE BrokenPipeError, on purpose. Every caller below
        # saves the session BEFORE calling this, so a pipe that closes mid-write
        # can only cost the reply, never the state change that produced it. See
        # the save-before-emit comment on the stdin loop for why that ordering
        # is load-bearing and not cosmetic.
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()
        if pretty:
            sys.stderr.write(render_pretty(op, obj) + "\n\n")
            sys.stderr.flush()

    # A player who has been told nothing but the path to this file must still be
    # able to start. On a new game the first line out is the whole briefing,
    # unasked, because there is nowhere else for them to learn it.
    # To STDERR, deliberately. stdout is the protocol and must stay exactly one
    # reply per command: an unsolicited line there shifts every index and breaks
    # anything parsing positionally, which it promptly did to my own tests.
    if not (session and os.path.exists(session)):
        sys.stderr.write(json.dumps(
            {"welcome": _agent_help(sim),
             "read this first": "This is the only instruction you get. Everything "
                                "else is here or in {\"cmd\":\"help\"}."},
            indent=1) + "\n")
        sys.stderr.flush()

    if a.script:
        try:
            cmds = json.load(open(a.script))
        except (OSError, ValueError) as e:
            emit({"ok": False, "error": "could not read script %r: %s" % (a.script, e)})
            return 1
        if not isinstance(cmds, list):
            emit({"ok": False, "error": "--script file must contain a JSON list of command objects"})
            return 1
        for command_obj in cmds:
            resp = _agent_dispatch(sim, nodes, command_obj)
            # SAVE BEFORE YOU SPEAK. See the stdin loop below for why: the same
            # ordering bug lived in both loops, and only the stdin one is what a
            # human normally drives, so it is the one the playtesters actually
            # hit, but a --script run piped through something that closes early
            # loses exactly the same way.
            if session:
                save_state(sim, session)
            try:
                emit(resp, command_obj.get("cmd") if isinstance(command_obj, dict) else None)
            except BrokenPipeError:
                try:
                    sys.stdout.close()
                except Exception:
                    pass
                return 0
        return 0

    # REPL over stdin/stdout: one JSON command per line in, one JSON object
    # per line out. This is the primary form; --script above is a thin
    # wrapper that replays a fixed list through the same dispatcher.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            cmd = json.loads(line)
        except ValueError as e:
            try:
                emit({"ok": False, "error": "invalid JSON: %s" % e})
            except BrokenPipeError:
                break
            continue
        # The dispatcher guards non-object input and replies politely, and then
        # THIS line used to kill the process: cmd.get on a bare null, number,
        # string or list is an AttributeError. A playtester reopened the
        # "malformed input ends your game" class through the quit check, one
        # line after the guard that was supposed to prevent exactly that.
        try:
            resp = _agent_dispatch(sim, nodes, cmd)
        except Exception as e:                      # never lose a session to a bug
            resp = {"ok": False,
                    "error": "internal error handling that command: %s: %s. "
                             "The game is intact; try something else."
                             % (type(e).__name__, e)}
        # SAVE FIRST, THEN SPEAK - the same fix `play` already has (see its own
        # "SAVE FIRST, THEN SPEAK" comment), missing here until now. By this
        # line `_agent_dispatch` has already mutated `s` in memory - a `step`
        # command has already moved the calendar - so writing that to disk
        # cannot be left waiting on whether the reply is printed successfully.
        # Two testers found the gap independently, the same way: piping `agent`
        # through `head` closes stdout, SIGPIPE kills the process on the write
        # below, and whatever had just happened - for one of them, a hundred
        # years of `step` - was never written to the save at all, though it had
        # genuinely happened. The game's own help promises you can "close the
        # terminal, anything" and come back; a promise that holds only when
        # nobody closes the pipe first is not that promise.
        if session:
            save_state(sim, session)
        try:
            emit(resp, cmd.get("cmd") if isinstance(cmd, dict) else None)
        except BrokenPipeError:
            # Somebody closed the pipe. The game is saved; leave quietly, the
            # same way `play` does for the same reason.
            try:
                sys.stdout.close()
            except Exception:
                pass
            break
        if isinstance(cmd, dict) and cmd.get("cmd") == "quit":
            break
    return 0


def cmd_sensitivity(a):
    """Ablation study: how much is each defensive or institutional node worth?

    Removes one node from the strategy (so it is never built) and re-runs. Nodes
    that are prerequisites of the goal cannot be ablated and are reported as such.
    """
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(a, "goal", None))
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    need = closure(nodes, goal)

    # COMMON RANDOM NUMBERS: trial() reseeds random.Random(a.seed + i)
    # identically for every call - baseline and every ablation see the same
    # per-trial shocks, differing only in which node was dropped. See
    # cmd_compare for the full rationale; do not randomise this per call.
    def trial(drop=None):
        trimmed_order = [node_id for node_id in order if node_id != drop]
        res = [Sim(nodes, trimmed_order, random.Random(a.seed + i), events=True,
                   bounty_set=bounties).run(goal, a.horizon)
               for i in range(a.mc)]
        succ = sum(1 for result in res if result.goal_year)
        successful_years = sorted(result.goal_year for result in res if result.goal_year)
        return (100.0 * succ / len(res), successful_years[len(successful_years) // 2] if successful_years else None, succ, len(res))

    base_rate, base_med, base_succ, base_n = trial()
    print("baseline (%s): %s" % (a.strategy, _fmt_rate_ci(base_succ, base_n)))
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
    rows = []
    for node_id in cands:
        if node_id not in nodes:
            continue
        if node_id in need:
            print("%-26s %10s %10s   hard prerequisite of the goal, cannot be skipped" % (node_id, "-", "-"))
            continue
        success_rate, median_year, succ, ntot = trial(node_id)
        rows.append((base_rate - success_rate, node_id, success_rate, median_year, succ, ntot))
    scored = []
    for rate_drop, node_id, success_rate, median_year, succ, ntot in rows:
        delay = (median_year - base_med) if (median_year and base_med) else 999
        # one point of success rate is worth roughly two years of delay
        score = rate_drop + delay / 2.0
        scored.append((score, node_id, success_rate, median_year, rate_drop, delay, succ, ntot))
    for score, node_id, success_rate, median_year, rate_drop, delay, succ, ntot in sorted(scored, reverse=True):
        verdict = ("CRITICAL, do not skip" if score > 20 else
                   "clearly worth it" if score > 8 else
                   "worth it" if score > 3 else
                   "marginal in this model" if score > -3 else
                   "the model says this costs more than it returns")
        lower, upper = _wilson_interval(succ, ntot)
        confidence_interval = "[%.0f%%,%.0f%%]" % (100.0 * lower, 100.0 * upper)
        print("%-24s %7.0f%% %16s %8s %+8s   %s" %
              (node_id, success_rate, confidence_interval, median_year or "never", ("%d yr" % delay) if median_year else "n/a", verdict))


def cmd_plan(a):
    """Work backward from the goal instead of walking a hand-written list.

    `run`/`compare` measure how well an `order` copes with bad luck; this is
    the thing that actually COMPUTES one, by critical-path method over the
    goal's prerequisite closure, instead of either hand-writing a guess
    (recommended.json, 0% on Rome at a 700-year horizon) or capturing
    whatever a lucky trial happened to do (captured_han_386.json - a floor,
    not a method). See sim/planner.py for the reasoning in full; this is
    a thin CLI wrapper, the same relationship `cmd_run` has to `Sim.run`.

    NEVER REACHED FROM `play` OR `agent`. Both of those are how a fogged
    player actually sees this game, and neither one calls this function or
    imports planner.py; a strategy file is public information a player
    already has access to (it is a file in the repository, the same as
    recommended.json), not a live look into a fogged session's own state.
    """
    _simdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _simdir not in sys.path:
        sys.path.insert(0, _simdir)
    import planner as _planner
    tree, _prices, nodes, _wages, _goods = load()
    goal = resolve_goal(tree, nodes, a.goal)
    if not a.search_rounds:
        # UNCHANGED FROM BEFORE. Purely structural CPM, optionally refined
        # against real trials - the path every existing caller and test
        # already exercises.
        order, rationale, _cpm_result = _planner.plan(
            civ=a.civ, goal=a.goal, seed_strategy=a.seed_strategy,
            side_branches=a.side_branches, side_branch_every=a.side_branch_every,
            refine_rounds=a.refine_rounds, mc=a.mc, horizon=a.horizon, seed=a.seed)
        label = ("PLANNED (CPM): backward-chained from %s over its "
                "prerequisite closure for %s%s" % (goal, a.civ,
                ", refined against real trials" if a.refine_rounds else ""))
        _planner.write_strategy(a.out, label, rationale, order)
        print("wrote %d nodes to %s" % (len(order), a.out))
        for line in rationale:
            print("  - " + line)
        return 0
    # SOLVE THE DICE-FREE PROBLEM FIRST (see sim/path_search.py):
    # diagnose the binding constraint against a trial with the dice removed
    # entirely and relax it, round by round, and USE that order directly -
    # not merely as a --seed-strategy tie-break for a fresh CPM pass, which
    # would silently re-run `pick_side_branches`/`interleave` and put every
    # side branch the search pulled to the end right back into the middle of
    # the spine, undoing the one relaxation move that does that.
    import path_search as _search
    _search.ensure_fixed_hash_seed()
    seed_order = _planner.load_seed(a.seed_strategy, nodes)
    order, extras, history = _search.search(
        civ=a.civ, goal=a.goal, side_branches=a.side_branches,
        side_branch_every=a.side_branch_every, rounds=a.search_rounds,
        horizon=a.search_horizon, backlog_ratio=a.search_backlog_ratio,
        seed_order=seed_order,
        grow_supply_moves=not a.search_no_grow_supply)
    last = history[-1]
    rationale = [
        "Deterministic search (path_search.py): critical-path order, then "
        "%d round(s) of diagnosing the binding constraint against a "
        "dice-free trial (no events, no project failures, immortal "
        "founder, %d-year horizon) and relaxing it, keeping whichever "
        "round scored best." % (len(history), a.search_horizon),
        "Final round %d: %d/%d closure nodes done%s. Scarce trade(s) "
        "diagnosed: %s."
        % (last["round"], last["closure_done"], len(closure(nodes, goal)),
           (", goal reached %d AD" % last["goal_year"]) if last["goal_year"] else "",
           ", ".join(last["scarce_trades"]) or "(none)"),
    ]
    _grown = [round_record for round_record in history if round_record["grow_supply_tried"]]
    if _grown:
        _n_tried = sum(len(round_record["grow_supply_tried"]) for round_record in _grown)
        _kept = [institution_trial["institution"] for round_record in _grown for institution_trial in round_record["grow_supply_tried"] if institution_trial["kept"]]
        rationale.append(
            "Grow-supply (move 3): a capital trap was diagnosed and %d "
            "candidate institution(s) were tried, one at a time, each kept "
            "only if a fresh dice-free trial measured strictly better with "
            "it than without. Kept: %s."
            % (_n_tried, ", ".join(_kept) if _kept else "none - no "
               "institution measured better than the order without it"))
    if a.refine_rounds:
        # SAME RELATIONSHIP `plan()` ALREADY HAS TO `refine()`: the search's
        # own order and side branches become what gets measured and
        # advanced round by round, instead of planner.plan() deriving a
        # fresh CPM pass that does not know about the search's relaxation.
        probe_sim = Sim(nodes, [], random.Random(a.seed), events=False, civ=load_civ(a.civ))
        order, extras, score = _planner.refine(
            nodes, goal, probe_sim, order, extras, a.civ, a.mc, a.horizon, a.seed,
            a.refine_rounds, a.side_branch_every)
        if score is not None:
            rationale.append(
                "Refined over %d round(s) of %d trials each at a %d-year "
                "horizon (seed %d), starting from the search's own order: "
                "%d/%d trials reached the goal in the final round."
                % (a.refine_rounds, a.mc, a.horizon, a.seed, score[0], a.mc))
    label = ("PLANNED (CPM + deterministic search%s): backward-chained from "
            "%s over its prerequisite closure for %s" % (
                ", refined against real trials" if a.refine_rounds else "",
                goal, a.civ))
    _planner.write_strategy(a.out, label, rationale, order)
    print("wrote %d nodes to %s" % (len(order), a.out))
    for line in rationale:
        print("  - " + line)
    return 0


def cmd_search(a):
    """`path_search.py`'s own dice-free search, reached directly instead of
    only through `plan --search-rounds`.

    `plan` alone is one structural CPM pass; `plan --search-rounds N` folds
    THIS SAME search into a CPM-seeded pipeline (and can go on to
    --refine-rounds against real trials afterward). This command is the
    other front door onto the identical machinery, for the case that started
    this file's own docstring: "does the current plan even get there with
    the dice off?", asked on its own, at path_search.py's own standalone
    defaults, without also having to think about CPM seeding or refinement.
    See sim/path_search.py for the full reasoning - the scarce named
    trades, the capital trap, and the three moves (pull, resequence, grow
    supply) this measures against a real Sim with the dice removed rather
    than guesses at.

    A THIN WRAPPER, LIKE `cmd_plan`. This calls `path_search.plan_and_write`
    - the exact function `path_search.py`'s own `main()` calls - so a change
    to what the search does, or to how its result gets written and explained,
    happens in one place for both front doors, not two.

    NEVER REACHED FROM `play` OR `agent`, for the same reason `plan` is not:
    both are developer/optimizer tools, and a strategy file either one
    writes is public information already sitting in the repository, not a
    live look into a fogged session's own state.
    """
    _simdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _simdir not in sys.path:
        sys.path.insert(0, _simdir)
    import path_search as _search
    order, rationale = _search.plan_and_write(
        a.civ, a.goal, a.out, a.side_branches, a.side_branch_every, a.rounds,
        a.horizon, a.backlog_ratio, a.seed_strategy, a.no_grow_supply)
    print("wrote %d nodes to %s" % (len(order), a.out))
    for line in rationale:
        print("  - " + line)
    return 0


# FOUR NUMBERS `cmd_why` PRINTS TO DESCRIBE MECHANICS IT DOES NOT ITSELF RUN -
# every one of these is a duplicate of a value computed for real elsewhere in
# the engine, kept here only so a player can see the consequence of a choice
# before making it. Declaring them does not remove the duplication (the real
# fix is cli.py reading the engine's own values instead of repeating them),
# but it does mean a `why` on it can say plainly which duplicate this is and
# what happens if the two ever disagree.
WHY_FAILURE_LOSS_FRACTION = declare(
    "WHY_FAILURE_LOSS_FRACTION", 0.4, kind="temporary_heuristic",
    unit="fraction of cost and hours lost on a failed attempt", source=None,
    confidence="C",
    why="What `why` tells a player a failed attempt at a risky node would "
        "cost them, in money and in hours - duplicating the 0.4 that "
        "engine/projects.py actually charges when a project fails "
        "(ph_left set to node['ph']*0.4, and the money loss computed as "
        "node['_total_cost']*0.4*cost_money_factor() - see that file's own "
        "'40, NOT 60' comment). Declared here, at the same value, because "
        "this file does not import projects.py's ProjectsMixin and so has "
        "no name to import instead; if that 0.4 is ever retuned there this "
        "line will go stale silently until someone notices the two numbers "
        "disagree.")
WHY_BOUNTY_PRICE_MULTIPLE = declare(
    "WHY_BOUNTY_PRICE_MULTIPLE", 2.5, kind="temporary_heuristic",
    unit="multiple of build cost", source=None, confidence="C",
    why="The 'about how much a public bounty would cost' estimate `why` "
        "prints, duplicating the 2.5x engine/projects.py's post_bounty() "
        "actually charges (see that function's own comment on a playtester "
        "who found `why` and `bounty` quoting different figures for the "
        "same node before this line existed at all). This estimate omits "
        "civ_cost_factor() and material_cost_factor(), which the real "
        "charge applies and this preview does not, so it is already an "
        "approximation even before considering the two multipliers might "
        "drift apart.")
WHY_OPPOSITION_COST_PCT = declare(
    "WHY_OPPOSITION_COST_PCT", 25, kind="temporary_heuristic",
    unit="percent added per unit of state opposition (-gov)", source=None,
    confidence="C",
    why="The 'costs X% more' a `why` screen quotes for an opposed node - 100 "
        "times engine/economy.py's own declared OPPOSITION_COST_PER_UNIT "
        "(0.25), which opposition_factor() actually applies to project cost. "
        "Declared separately, at the matching value, because this file has "
        "no live Sim to read that constant off of in cmd_why (no Sim object "
        "is constructed here at all - this command works from tree data "
        "alone) and gov, the node's raw -3..+3 trait, is not the same "
        "quantity opposition_factor() multiplies by (state_interest(), a "
        "continuous function of gov and other factors) - so this is already "
        "an approximation of what an opposed build will actually cost, not "
        "an exact preview of it.")
WHY_OPPOSITION_SUSPICION_PER_UNIT = declare(
    "WHY_OPPOSITION_SUSPICION_PER_UNIT", 3, kind="temporary_heuristic",
    unit="suspicion points per unit of state opposition (-gov)", source=None,
    confidence="D",
    why="The '+X extra suspicion' a `why` screen quotes for an opposed node. "
        "FLAGGED: engine/projects.py's own post_bounty() comment says "
        "publicity 'used to also add to a suspicion scalar that nothing "
        "ever read' before scandal/eminence replaced it - which suggests "
        "the mechanic this line describes may no longer exist in the engine "
        "at all, and this could be describing a consequence that does not "
        "happen. Left at its source value rather than silently removed or "
        "changed - a literal migration must not also fix what it says, the "
        "same discipline _founder_lifetime_hours()'s own comment explains "
        "for a case that WAS worth fixing (Complaints/38); worth an actual "
        "read of whether 'sus' still does anything before the next hand "
        "touches this line.")


def cmd_why(a):
    """Explain one node: what it needs, what needs it, and what it costs."""
    tree, prices, nodes, wages, goods = load()
    node_id = a.node
    if node_id not in nodes:
        near = [candidate_id for candidate_id in nodes if a.node.lower() in candidate_id.lower()]
        raise SystemExit("unknown node. did you mean: %s" % (", ".join(near[:8]) or "no idea"))
    node_record = nodes[node_id]
    print("%s  [%s, confidence %s]" % (node_record["name"], node_record["cat"], node_record["conf"]))
    print("=" * 78)
    print(node_record["note"])
    print()
    print("Recipe          : knowledge/%s" % node_record["kb"])
    # Complaints/38: same computed budget cmd_path prints and judges against
    # - see _founder_lifetime_hours()'s own comment - so this percentage
    # cannot go stale against either of those the way a separately typed
    # "72,000-hour life" did.
    lifetime_hours = _founder_lifetime_hours()
    print("Your hours      : %s   (%.1f%% of a %s-hour life)" %
          (f"{node_record['ph']:,}", 100.0 * node_record["ph"] / lifetime_hours,
           f"{lifetime_hours:,.0f}"))
    print("Hired labour    : %s" % (", ".join("%s %s h" % (trade, f"{hours:,}") for trade, hours in node_record["lab"].items()) or "none"))
    print("Materials       : %s" % (", ".join("%s %s" % (material, f"{quantity:,}") for material, quantity in node_record["mat"].items()) or "none"))
    print("Cost            : %s den labour + %s materials + %s capital = %s TOTAL"
          % (f"{node_record['_labour_cost']:,.0f}", f"{node_record['_material_cost']:,.0f}",
             f"{node_record['cap']:,}", f"{node_record['_total_cost']:,.0f}"))
    print("Upkeep          : %s den/yr        Revenue: %s den/yr" % (f"{node_record['up']:,}", f"{node_record['rev']:,}"))
    print("Calendar floor  : %.1f years (money cannot buy this down)" % node_record["yrs"])
    # WHAT A FAILURE COSTS, not only how likely one is. The rate was on the
    # screen and the sum never was, so three players in a row read "10% per
    # attempt" as a small thing and were not expecting the 35,433 pence it
    # took off a 141,824-pence project. The share is a flat 40% every time;
    # what varies is the size of what you started, which is exactly the
    # number a player is holding in their head when they decide.
    if node_record["risk"]:
        print("Failure risk    : %.0f%% per attempt - a failure costs %s (40%%) "
              "and %s of your hours to do again"
              % (100 * node_record["risk"],
                 f"{node_record['_total_cost'] * WHY_FAILURE_LOSS_FRACTION:,.0f}",
                 f"{node_record['ph'] * WHY_FAILURE_LOSS_FRACTION:,.0f}"))
    else:
        print("Failure risk    : none")
    print("Staff needed    : %d trained scholars, %d trained artisans" % (node_record["sch"], node_record["art"]))
    print("Suspicion       : %+d       State interest: %+d%s" % (node_record.get("sus", 0), node_record.get("gov", 0),
          ("  <- OPPOSED. Costs %d%% more, +%d extra suspicion, needs %s"
           % (WHY_OPPOSITION_COST_PCT * -node_record.get("gov", 0),
              WHY_OPPOSITION_SUSPICION_PER_UNIT * -node_record.get("gov", 0),
              "senatorial patronage" if node_record.get("gov", 0) <= -2 else "a patron"))
          if node_record.get("gov", 0) < 0 else ""))
    eligible = (node_record["cat"] in ("glass_optics", "metallurgy", "precision",
                "power", "agriculture", "information", "instruments"))
    print("Bounty          : %s" % ("YES, can be bought as a public prize for about %s den"
                                    % f"{node_record['_total_cost'] * WHY_BOUNTY_PRICE_MULTIPLE:,.0f}" if eligible else
                                    "no, a local craftsman could not recognise success"))
    print()
    print("DIRECT PREREQUISITES")
    for prereq_id in node_record["pre"] or ["(none, you can start this on arrival)"]:
        print("   %s" % (("%-30s %s" % (prereq_id, nodes[prereq_id]["name"])) if prereq_id in nodes else prereq_id))
    need = closure(nodes, node_id) - {node_id}
    print("\nFULL CHAIN BEHIND IT: %d nodes, %s of your hours, %s denarii, %.0f-year serial floor"
          % (len(need), f"{sum(nodes[descendant_id]['ph'] for descendant_id in need):,}",
             f"{sum(nodes[descendant_id]['_total_cost'] for descendant_id in need):,.0f}", critical_path(nodes, node_id)[0]))
    print("   " + ", ".join(topo_order(nodes, need)))
    # req_any COUNTS: see protocol._unlocked_by. Ten nodes, among them the
    # Norse clinker hull and bog-iron bloomery and the Mexica's chinampa, were
    # reported as dead ends because this scanned hard prerequisites only.
    from .protocol import _unlocked_by
    unlocks = _unlocked_by(node_id, nodes)
    print("\nDIRECTLY UNLOCKS")
    for unlock_id in unlocks or ["(nothing, this is a leaf)"]:
        print("   %s" % (("%-30s %s" % (unlock_id, nodes[unlock_id]["name"])) if unlock_id in nodes else unlock_id))
    # FOLLOWING SUBSTITUTION GROUPS TOO: see protocol._downstream_of for why
    # this is not closure()'s question. The chinampa printed "TOTAL DOWNSTREAM:
    # 0" while feeding terracing through a req_any option.
    from .protocol import _downstream_of
    blocks = _downstream_of(node_id, nodes)
    print("\nTOTAL DOWNSTREAM: %d nodes depend on this, directly or indirectly." % len(blocks))
    _goal_here = resolve_goal(tree, nodes, getattr(a, "goal", None))
    if _goal_here in blocks or _goal_here == node_id:
        print("   INCLUDING THE GOAL. This node is on the critical path.")


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


def cmd_sweep(a):
    """Sweep a starting condition and show how the outcome and the FAILURE MODE move.

    The failure mode moving is the interesting part. More starting capital does
    not simply help: past a point it switches you from dying poor and untaught to
    being denounced as a magician, because money buys speed, speed buys
    visibility, and visibility in Trajanic Rome is dangerous.
    """
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, getattr(a, "goal", None))
    label, order, bounties = load_strategy(a.strategy, nodes, goal)
    sweeps = {
        "capital":  ("start_capital", [2000, 5000, 10320, 25000, 50000, 200000, 1000000]),
        "lifespan": ("founder_life",  [10, 15, 20, 28, 35, 45, 60]),
        "hours":    ("founder_hours_per_year", [1000, 1500, 2000, 2500, 3000]),
        "mortality":("founder_life_mean", [10, 15, 20, 28, 40, 60]),
    }
    key, values = sweeps[a.axis]
    print("sweeping %s under strategy '%s', %d runs per point\n" % (a.axis, a.strategy, a.mc))
    print("%-12s %8s %16s %8s %8s   %s" %
          (a.axis, "success", "95% CI", "median", "p25", "dominant failure"))
    print("-" * 92)
    any_thin = False
    any_success = False
    for value in values:
        cfg, life = {}, None
        if key == "founder_life_mean":
            cfg = {"immortal": False, "founder_life_mean": value,
                   "founder_life_sd": DEFAULTS["founder_life_sd"]}
        elif key == "founder_life":
            life = value
        else:
            cfg[key] = value
        res = []
        for i in range(a.mc):
            # COMMON RANDOM NUMBERS across the points of this sweep, same
            # reasoning as cmd_compare: trial i sees the same shocks at every
            # value of v, so a change down this column is the swept variable
            # acting, not a different draw of luck. Do not reseed per v.
            sim = Sim(nodes, order, random.Random(a.seed + i), events=True, cfg=cfg,
                      bounty_set=bounties)
            if life is not None:
                sim.life_left = float(life)
            res.append(sim.run(goal, a.horizon))
        succ = sum(1 for run in res if run.goal_year)
        successful_years = sorted(run.goal_year for run in res if run.goal_year)
        failure_causes = defaultdict(int)
        for run in res:
            if not run.goal_year:
                failure_causes[(run.dead_reason or "ran out of horizon").split(":")[0]] += 1
        worst = max(failure_causes.items(), key=lambda x: x[1]) if failure_causes else ("none", 0)
        lower, upper = _wilson_interval(succ, len(res))
        thin = 0 < succ < _MIN_SUCCESSES_FOR_QUANTILES
        any_thin = any_thin or thin
        any_success = any_success or succ > 0
        print("%-12s %7.0f%% %16s %8s %8s   %s" %
              (f"{value:,}", 100.0 * succ / len(res),
               "[%.0f%%,%.0f%%]" % (100.0 * lower, 100.0 * upper),
               (str(successful_years[len(successful_years) // 2]) + "*" if thin else successful_years[len(successful_years) // 2]) if successful_years else "never",
               successful_years[len(successful_years) // 4] if successful_years else "-",
               "%s (%d)" % (worst[0][:44], worst[1]) if worst[1] else "-"))
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
              % a.strategy)
        print("    at any %s tried, not only at one unlucky value. Before reading" % a.axis)
        print("    anything above as 'this starting condition is impossible': this looks")
        print("    like a known-losing ORDER at this horizon, not a fact about %s. Run"
              % a.axis)
        print("    'plan' (critical-path method) or 'search' (dice-free, relaxed against")
        print("    the binding constraint) to compute a different order, then sweep that.")


def cmd_goals(a):
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


# THE SAME DEFAULT engine/society.py DECLARES AS EMINENCE_DANGER_WEIGHT_DEFAULT
# (0.5) - kept as its own name because this file has no Sim/SocietyMixin
# instance to read that constant from (cmd_civs works from the raw civ JSON
# files directly, before any game has started), same shape as
# INGAME_MORTALITY_MIN_REMAINING_LIFE_YEARS just above.
CIVS_EMINENCE_DANGER_DEFAULT = declare(
    "CIVS_EMINENCE_DANGER_DEFAULT", 0.5, kind="temporary_heuristic",
    unit="dimensionless weight", source=None, confidence="D",
    why="What this screen shows for 'eminence is dangerous' when a "
        "civilisation's own JSON does not set w_eminence_danger - a mid-scale "
        "default rather than a claim about any specific civilisation. "
        "Matches engine/society.py's EMINENCE_DANGER_WEIGHT_DEFAULT, which "
        "is the value actually used if a live game hits the same missing "
        "field; declared separately here so the two can be told apart if "
        "they are ever retuned independently, and so a reader of this file "
        "alone can see this number is not invented for display.")


def cmd_civs(a):
    """List the civilizations you can play, and what makes each one different.

    home_regions and base_reach used to be printed here and read NOWHERE
    ELSE: that was the entire bug this session fixed. They now actually
    drive Sim.region_reach() and Sim.material_reach() (see simulator.py),
    which is a much better reason to show them, so this now also names the
    home ground itself rather than just the region ids.
    """
    geo = load_geography()
    region_names = {rid: region_record.get("name", rid)
                    for rid, region_record in (geo.get("regions") or {}).items()
                    if not rid.startswith("_")}
    for civ_filename in sorted(os.listdir(CIVDIR)):
        # Files starting with "_" are schema/reference data, not a playable
        # civilization (e.g. _TECH_EFFECTS.json), same convention this file
        # already uses everywhere else for "_"-prefixed keys and entries.
        if not civ_filename.endswith(".json") or civ_filename.startswith("_"):
            continue
        civ_data = json.load(open(os.path.join(CIVDIR, civ_filename)))
        value = civ_data["values"]
        print("%-16s %s, %s" % (civ_data["id"], civ_data["name"], civ_data["year"]))
        print("   %s" % civ_data.get("blurb", ""))
        homes = [region_names.get(region_id, region_id) for region_id in civ_data.get("home_regions") or []]
        print("   home ground: %s" % (", ".join(homes) if homes else "(none set)"))
        print("   population %s   state capacity %.2f   base_reach %d (how far it already "
              "routinely travels)   starts with %d technologies"
              % (f"{civ_data.get('population',0):,}", civ_data.get("state_capacity", 0),
                 civ_data.get("base_reach", 0), len(civ_data.get("starting_techs", []))))
        print("   fears the inexplicable %.2f | fears heterodoxy %.2f | resents machines %+.2f "
              "| bribable %.2f | habituates %.2f"
              % (value["w_magic_fear"], value["w_religious_rigidity"], value["w_labour_saving"],
                 value["bribability"], value["adaptation_rate"]))
        print("   eminence is dangerous %.2f  (how much prominence ITSELF endangers you)"
              % value.get("w_eminence_danger", CIVS_EMINENCE_DANGER_DEFAULT))
        mults = civ_data.get("cost_multipliers") or {}
        if mults:
            easy = sorted((cost_pair for cost_pair in mults.items() if cost_pair[1] < 1.0), key=lambda x: x[1])[:4]
            hard = sorted((cost_pair for cost_pair in mults.items() if cost_pair[1] > 1.0), key=lambda x: -x[1])[:4]
            if easy:
                print("   good at : " + ", ".join("%s x%.2f" % cost_pair for cost_pair in easy))
            if hard:
                print("   bad at  : " + ", ".join("%s x%.2f" % cost_pair for cost_pair in hard))
        print()
    print("starting kits (--kit):")
    for kit_id, kit_data in STARTING_KITS.items():
        print("   %-14s %9s den   %s" % (kit_id, f"{kit_data['den']:,}", kit_data["desc"]))
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
    # IN A DIRECTORY OF ITS OWN. Eighty-nine save files had accumulated in the
    # repository root beside the source, and a play tester said so: "saves land
    # in the repo root, next to eighty others". A game that writes a file after
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


def _ask(prompt, options, default=None):
    """Ask until the answer is one of options. Empty input takes the default."""
    while True:
        try:
            raw = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not raw and default is not None:
            return default
        if raw in ("q", "quit", "exit"):
            return None
        for option in options:
            if raw == option or (len(raw) == 1 and option.startswith(raw)):
                return option
        print("   -- I did not understand that. Options: %s" % ", ".join(options))


def _load_civ_list():
    civs = []
    for civ_filename in sorted(os.listdir(CIVDIR)):
        if not civ_filename.endswith(".json") or civ_filename.startswith("_"):
            continue
        civs.append(json.load(open(os.path.join(CIVDIR, civ_filename))))
    civs.sort(key=lambda c: c.get("year", 0))
    return civs


def _new_game(civs, cfg):
    """The wizard: pick a civilisation, read where you have landed, choose
    fog/kit/mortality/goal/horizon, and start. Returns cmd_play's exit code once a
    game has actually begun, or None if the player backed out first - in
    which case cmd_menu's own loop is what should run next, not this
    function again."""
    tree, _prices, nodes, _wages, _goods = load()
    print("-" * 78)
    print("   WHERE, AND WHEN")
    print("-" * 78)
    for i, civ_record in enumerate(civs, 1):
        print()
        print("   %d) %s, %d" % (i, civ_record.get("name", civ_record["id"]), civ_record.get("year", 0)))
        print(_wrap(civ_record.get("blurb", ""), indent="      "))
        print("      %s people   state capacity %.2f   prices %.2fx Rome"
              % (f"{civ_record.get('population', 0):,}", civ_record.get("state_capacity", 0),
                 civ_record.get("price_index", 1.0)))
    print()
    default_i = next((i for i, civ_record in enumerate(civs, 1)
                      if civ_record.get("id") == cfg.get("default_civ")), None)
    prompt = ("   Which one? [1-%d%s, or b to go back] "
              % (len(civs), (", default %d" % default_i) if default_i else ""))
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        if raw.lower() in ("q", "quit", "exit", "b", "back"):
            return None
        if not raw and default_i:
            civ = civs[default_i - 1]
            break
        if raw.isdigit() and 1 <= int(raw) <= len(civs):
            civ = civs[int(raw) - 1]
            break
        print("   -- a number from 1 to %d." % len(civs))

    opening = civ.get("opening") or {}
    print()
    print("=" * 78)
    print(("   %s, %d" % (civ.get("name", civ["id"]), civ.get("year", 0))).upper())
    print("=" * 78)
    for key, heading in (("arrival", None),
                         ("what_you_can_see", "What you can see"),
                         ("what_is_missing", "What is missing"),
                         ("what_is_coming", "What is coming, and only you know it"),
                         ("what_this_models", "The size of your own reach")):
        if not opening.get(key):
            continue
        print()
        if heading:
            print("   %s" % heading.upper())
        print(_wrap(opening[key]))
    if not opening:
        print()
        print(_wrap(civ.get("blurb", "")))
    print()

    print("-" * 78)
    print(_wrap("FOG OF WAR. With it on you see what you have built, what you "
                "could begin today as a one-line summary, and things you have "
                "heard of but cannot yet start. You cannot see where anything "
                "leads. With it off you can see the whole tree and plan a "
                "route through it. This cannot be changed once you start - a "
                "save played with it on can never be resumed without it, and "
                "one played without it has already seen too much to fog "
                "again.", indent="   "))
    fog_default = "y" if cfg.get("default_fog", True) else "n"
    fog = _ask("\n   Fog of war? [%s] " % ("Y/n" if fog_default == "y" else "y/N"),
               ["y", "n"], fog_default)
    if fog is None:
        return None
    print()
    print("-" * 78)
    print("   WHAT YOU ARRIVED WITH")
    for name, kit in STARTING_KITS.items():
        print("      %-14s %9s den" % (name, f"{kit['den']:,}"))
        if kit.get("desc"):
            print(_wrap(kit["desc"], indent="         "))
    kit_default = cfg.get("default_kit", "poor_scholar")
    if kit_default not in STARTING_KITS:
        kit_default = "poor_scholar"
    kit = _ask("\n   Which? [%s, default %s] " % ("/".join(STARTING_KITS), kit_default),
               list(STARTING_KITS), kit_default)
    if kit is None:
        return None
    print()
    print("-" * 78)
    print(_wrap("MORTALITY. By default the founder does not age, which measures "
                "the tree rather than a lifespan lottery. Turned on, you get one "
                "human life and everything you have not made permanent dies with "
                "you. The premise of the whole game is that one is the honest "
                "number. You can turn this on later, mid-game, without "
                "restarting (see the in-game 'options' command) - but not off "
                "again once it is on, the same as fog.", indent="   "))
    mortal_default = "y" if cfg.get("default_mortal", False) else "n"
    mortal = _ask("\n   Let the founder age and die? [%s] "
                 % ("Y/n" if mortal_default == "y" else "y/N"),
                 ["y", "n"], mortal_default)
    if mortal is None:
        return None
    print()
    print("-" * 78)
    print(_wrap("THE GOAL. The transistor (1951) is the original target and "
                "still the default, and from scratch it takes centuries - which "
                "is the whole reason the founder does not age by default. Below "
                "are the alternatives: achievements a single lifetime can "
                "actually finish, and a handful almost as large as the "
                "transistor itself. 'closure' is how many other things it needs "
                "first; 'floor' is the fewest calendar years that work could "
                "possibly take, with every dice roll going your way.",
                indent="   "))
    print()
    goals = goal_catalog(tree, nodes)
    default_goal_id = cfg.get("default_goal") or tree["meta"]["goal_node"]
    if default_goal_id not in nodes:
        default_goal_id = tree["meta"]["goal_node"]
    default_gi = next((i for i, goal_row in enumerate(goals, 1)
                       if goal_row["node"] == default_goal_id), 1)
    for i, goal_row in enumerate(goals, 1):
        node = goal_row["node"]
        need = closure(nodes, node)
        yrs, _chain = critical_path(nodes, node)
        print("   %d) %s  (closure %d, floor %.0fy%s)"
              % (i, goal_row.get("name", node), len(need), yrs,
                 ", %s" % goal_row["scale"] if goal_row.get("scale") else ""))
        if goal_row.get("blurb"):
            print(_wrap(goal_row["blurb"], indent="         "))
        if nodes[node].get("win_condition"):
            print(_wrap("Won by measurement, not by building: %s."
                        % win_condition_describe(nodes[node]), indent="         "))
    print()
    while True:
        try:
            rawg = input("   Which one? [1-%d, default %d, or b to go back] "
                         % (len(goals), default_gi)).strip()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        if rawg.lower() in ("q", "quit", "exit", "b", "back"):
            return None
        if not rawg:
            goal = goals[default_gi - 1]["node"]
            break
        if rawg.isdigit() and 1 <= int(rawg) <= len(goals):
            goal = goals[int(rawg) - 1]["node"]
            break
        print("   -- a number from 1 to %d." % len(goals))
    print()
    print("-" * 78)
    print(_wrap("HORIZON. The game ends automatically this many years after "
                "arrival, mostly so a run that is truly stuck stops rather than "
                "running forever. Unlike the choices above, this one you CAN "
                "change later without restarting - the in-game 'options' "
                "command.", indent="   "))

    print("-" * 78)
    print(_wrap("DIFFICULTY, IN THIS GAME, MEANS ONE THING: how long you have. "
                "Nothing below changes what anything costs or how likely it is "
                "to fail - the tree and the risk are the same whatever you "
                "pick here. What changes is only the calendar you are racing.",
                indent="   "))
    print()
    # THE ONE HONEST THING A MODE MENU CAN SAY HERE: the same number of years
    # is a completely different offer depending which civilisation it is
    # attached to - see DICE_FREE_FLOOR_YEARS's own comment for the measurement
    # and data/review/PATH_SEARCH.md for the method. Said to the player
    # NOW, about the civilisation they just picked, rather than left for them
    # to discover by overshooting a horizon that was never going to be enough.
    # THE FLOOR OF THE GOAL YOU JUST PICKED, not of the default one. This said
    # "reaching the transistor takes about N years" from a table of per-civ
    # figures, which was right while there was one goal and is wrong now that
    # there are seventeen - a lifetime goal with a 5-year floor and the
    # transistor with a 142-year one cannot share a sentence. critical_path is
    # the same measurement, computed for the actual choice, so there is nothing
    # to keep in step. It is a floor and not a forecast: it assumes every roll
    # goes your way and no year is ever spent short of money, people or
    # material, which no real run manages.
    _floor_yrs, _ = critical_path(nodes, goal)
    _goal_label = nodes.get(goal, {}).get("name", goal)
    if _floor_yrs:
        print(_wrap("What you just chose - %s - cannot be done in fewer than "
                    "about %d years even with every roll going your way, and a "
                    "real run takes substantially longer than its floor. Pick a "
                    "calendar with that in mind."
                    % (_goal_label, _floor_yrs), indent="   "))
        print()

    for i, (_key, _label, _yrs, _note) in enumerate(HORIZON_MODES, 1):
        print("   %d) %-10s %s" % (i, _label,
              ("%d years - %s" % (_yrs, _note)) if _yrs else _note))
    print("   %d) an exact number of years" % (len(HORIZON_MODES) + 1))
    # THE REMEMBERED DEFAULT MUST STILL ACCEPT IN ONE BLANK LINE, the same
    # contract every other question in this wizard already has (see "REMEMBERED
    # FOR NEXT TIME" below) - whether last time's horizon happens to match a
    # named preset or not. A player who remembered 321 years specifically
    # must not be routed through an extra "how many years?" prompt just
    # because 321 is not one of the four named numbers.
    default_h = cfg.get("default_horizon", 500)
    _mode_by_years = {mode[2]: mode[0] for mode in HORIZON_MODES if mode[2]}
    _mode_by_years[ENDLESS_HORIZON_YEARS] = "endless"
    _default_key = _mode_by_years.get(default_h)
    _default_idx = (next(i for i, mode in enumerate(HORIZON_MODES, 1)
                         if mode[0] == _default_key)
                    if _default_key else len(HORIZON_MODES) + 1)
    while True:
        try:
            rawh = input("\n   Which? [1-%d, default %d, or b to go back] "
                         % (len(HORIZON_MODES) + 1, _default_idx)).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        if rawh in ("q", "quit", "exit", "b", "back"):
            return None
        if not rawh:
            if _default_key:
                _key, _label, _yrs, _note = HORIZON_MODES[_default_idx - 1]
                horizon = _yrs if _yrs else ENDLESS_HORIZON_YEARS
                break
            # No preset matches the remembered horizon - accept IT directly,
            # not the custom prompt's own separate default, with no second
            # question asked.
            horizon = default_h
            break
        if rawh.isdigit() and 1 <= int(rawh) <= len(HORIZON_MODES) + 1:
            choice = int(rawh)
        else:
            _match = next((i for i, mode in enumerate(HORIZON_MODES, 1)
                          if rawh in (mode[0], mode[1].lower())), None)
            if _match is None:
                print("   -- a number from 1 to %d, a name, or b."
                      % (len(HORIZON_MODES) + 1))
                continue
            choice = _match
        if choice == len(HORIZON_MODES) + 1:
            try:
                rawh2 = input("   How many years? [default %d, or b to go "
                              "back] " % default_h).strip()
            except (EOFError, KeyboardInterrupt):
                print(); return None
            if rawh2.lower() in ("q", "quit", "exit", "b", "back"):
                return None
            if not rawh2:
                horizon = default_h
                break
            try:
                horizon = int(rawh2)
                if horizon <= 0:
                    raise ValueError
            except ValueError:
                print("   -- a whole number of years, more than 0.")
                continue
            break
        else:
            _key, _label, _yrs, _note = HORIZON_MODES[choice - 1]
            horizon = _yrs if _yrs else ENDLESS_HORIZON_YEARS
            break

    # REMEMBERED FOR NEXT TIME, SILENTLY - not a settings screen's job. A
    # player who favours one civilisation and kit should not have to retype
    # them every game, and used to be able to set that from the main-menu
    # Options screen; that screen is for the APPLICATION now (see
    # settings.py's module docstring), so the wizard remembers its own
    # answers instead, the way a file dialog remembers its last folder. This
    # writes back exactly the six fields CONFIG_DEFAULTS calls "default_*",
    # and nothing else cfg might hold (display width, rows per page, the
    # welcome toggle) - those are the player's, set from Options, and this
    # wizard has no business overwriting them.
    cfg["default_civ"] = civ["id"]
    cfg["default_kit"] = kit
    cfg["default_fog"] = (fog == "y")
    cfg["default_mortal"] = (mortal == "y")
    cfg["default_goal"] = goal
    cfg["default_horizon"] = horizon
    settings.save_config(cfg)

    # THIS USED TO STOP HERE: print the command for the JSON protocol and ASK
    # whether to play. A tester put it plainly - "it should be the save
    # starting. It should have you pick, then you immediately jump in" - and
    # they were right: everything above this point is a choice about WHAT
    # game to start, not whether to start one, and a menu that ends by
    # handing you a command line to go run yourself is not a front door, it
    # is a man page. So: pick where the save goes, say so once, and go.
    #
    # AND IT USED TO GO INTO `agent`, which speaks JSON. The reason given at
    # the time was that only `agent` had a session file, and that `play`
    # without --manual was not a real choice. Both were true and neither was
    # a good enough reason to sit a person down in front of
    # {"cmd":"available"}: the answer was to fix `play`, which now takes a
    # --session of its own and is always manual, and speaks typed words over
    # the same dispatcher the JSON protocol uses. `agent` is still there, and
    # is still the right thing for a script.
    session = _pick_session_filename(civ["id"])
    # THE HORIZON HAS TO SURVIVE A RESUME TOO, and it is not part of what
    # save_state writes (see settings.py's module docstring) - so it gets
    # the same sidecar the in-game 'options' command uses to change it later.
    settings.save_session_meta(session, {"horizon_years": horizon})
    print()
    print("=" * 78)
    print(_wrap(
        "Starting now. Progress is written to this file after every command, "
        "so you can stop any time - close the terminal, anything - and come "
        "back to exactly where you left off with:"))
    print()
    print("      python3 sim/simulator.py play --session %s" % session)
    print()

    class Args:
        pass
    args = Args()
    args.strategy = "recommended"
    args.goal = goal
    args.seed = 1
    args.horizon = horizon
    args.civ = civ["id"]
    args.kit = kit
    args.mortal = (mortal == "y")
    args.fog = (fog == "y")
    args.session = session
    args.manual = True
    return cmd_play(args)


def _save_listing(cfg):
    """(save_dir, rows, civ_index, need) - everything both `_load_game` (the
    main-menu door) and `_ingame_saves`/`_ingame_load` (the same list, typed
    mid-game - see PLAYER REQUEST #3 below) print a save row from. One
    implementation, so the two screens cannot quietly drift apart the way
    the fog-progress fraction almost did when this was still duplicated.
    """
    tree, prices, nodes, wages, goods = load()
    default_goal = tree["meta"]["goal_node"]
    # EACH SAVE NAMES ITS OWN GOAL NOW (see protocol.py's _goal/save_state),
    # so the closure a save's progress is measured against has to be THAT
    # goal's, not always the transistor's.
    _need_cache = {}
    def _need_for(goal_id):
        goal_id = goal_id if goal_id in nodes else default_goal
        hit = _need_cache.get(goal_id)
        if hit is None:
            hit = _need_cache[goal_id] = closure(nodes, goal_id)
        return goal_id, hit
    civ_index = {civ_record["id"]: civ_record for civ_record in _load_civ_list()}
    save_dir = settings.resolve_save_dir(cfg)
    rows = settings.list_saves(save_dir)
    # EACH ROW CARRIES ITS OWN GOAL AND ITS OWN CLOSURE. _need_for above was
    # written for this and then never wired to the rows, because the save-row
    # renderer was factored out in a different branch at the same time; a
    # listing that measured every save against the transistor's 168 nodes would
    # report a save playing a five-node lifetime goal as 3/168 done.
    for _row in rows:
        _gid, _gneed = _need_for(_row.get("goal"))
        _row["goal_id"] = _gid
        _row["goal_name"] = nodes.get(_gid, {}).get("name", _gid)
        _row["goal_need"] = _gneed
    # The fourth element is the DEFAULT goal's closure, kept only as the
    # fallback a row without a readable goal uses. Each row carries its own
    # above, which is the number that actually gets printed.
    _default_gid, _default_need = _need_for(None)
    return save_dir, rows, civ_index, _default_need


def _print_save_row(i, r, civ_index, need, marker=None):
    """The lines `_load_game`, `_ingame_saves` and `_ingame_load` all print
    for one save: which civilisation, how far along, when it was last
    touched. A save played WITH fog does not get the goal-progress fraction
    shown here: that number (X of Y toward the transistor) says how big the
    whole tree is, which is exactly what fog exists to keep a player from
    knowing before they have earned it, and a listing screen is not exempt
    from that just because no Sim object exists yet.
    """
    if not r["readable"]:
        print("   %d) %s" % (i, r["filename"]))
        print("      could not be read as a save from this game; skipping "
              "its details")
        print()
        return
    civ_record = civ_index.get(r["civ_id"], {})
    name = civ_record.get("name", r["civ_id"] or "unknown civilisation")
    start = civ_record.get("year")
    year = r["year"]
    elapsed = ("  (%d years in)" % (year - start)
              if isinstance(start, (int, float)) and isinstance(year, (int, float))
              else "")
    print("   %d) %s%s" % (i, r["filename"], "   %s" % marker if marker else ""))
    print("      %s  -  now %s AD%s" % (name, year, elapsed))
    status = []
    if r.get("goal_year"):
        # NAMED, because there are seventeen goals now and "reached the
        # transistor" is wrong for sixteen of them. Safe to name even for a
        # fogged save: this one was finished, so the player knows what it was.
        status.append("REACHED %s in %s AD"
                      % ((r.get("goal_name") or "its goal").upper(),
                         r["goal_year"]))
    elif r.get("dead_reason"):
        status.append("ended: %s" % r["dead_reason"])
    elif r.get("founder_alive") is False:
        status.append("founder has died")
    done = r.get("done") or []
    if r["fog"]:
        status.append("%d technologies built" % len(done))
    else:
        _need = r.get("goal_need") or need
        progress = len(_need.intersection(done))
        status.append("%d/%d toward %s"
                      % (progress, len(_need), r.get("goal_name") or "the goal"))
    status.append("fog %s" % ("on" if r["fog"] else "off"))
    if r.get("reputation") is not None:
        status.append("rep %.0f" % r["reputation"])
    print("      " + "  |  ".join(status))
    print("      last played %s" % settings.humanize_age(r["mtime"]))
    print()


def _load_game(cfg):
    """List what is in the configured save directory and resume one.

    See _print_save_row for what each entry shows and why.
    """
    save_dir, rows, civ_index, need = _save_listing(cfg)

    print("-" * 78)
    print("   LOAD A SAVED GAME")
    print("-" * 78)
    print("   looking in: %s" % save_dir)
    print()
    if not rows:
        print(_wrap("Nothing there yet. Start a new game first, or type the "
                    "path to a save file below if you have one somewhere else."))
        print()
    for i, row in enumerate(rows, 1):
        _print_save_row(i, row, civ_index, need)

    print("   b) back to the main menu")
    if rows:
        prompt = "   Which one? [1-%d, p to type a path instead, or b] " % len(rows)
    else:
        prompt = "   p) type a path to a save file, or b) back"
    while True:
        try:
            raw = input("\n" + prompt + "\n   > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return None
        low = raw.lower()
        if low in ("b", "back", "q", "quit", "exit"):
            return None
        if low in ("p", "path"):
            try:
                path = input("   Path to the save file: ").strip()
            except (EOFError, KeyboardInterrupt):
                print(); return None
            if not path:
                continue
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                print("   -- nothing at %s" % path)
                continue
            chosen = path
            break
        if raw.isdigit() and rows and 1 <= int(raw) <= len(rows):
            chosen = rows[int(raw) - 1]["path"]
            break
        print("   -- a number from the list above, 'p', or 'b'.")

    class Args:
        pass
    args = Args()
    args.strategy = "recommended"
    args.seed = 1
    args.horizon = 500
    args.civ = None
    args.kit = "poor_scholar"
    args.mortal = False
    args.fog = False
    args.session = chosen
    args.manual = True
    return cmd_play(args)


def _options_menu(cfg):
    """Preferences about the APPLICATION, not about any one game: where
    saves go, how wide a line wraps, how many rows a long table shows
    before paging, and whether the welcome/tutorial text prints on a new
    game. See settings.py's module docstring for why this screen holds
    exactly these and none of the things a playthrough itself decides
    (civilisation, starting kit, fog, mortality, horizon) - those are
    remembered from the New Game wizard's last answers instead (see
    _new_game), and the couple of them that are honestly changeable
    mid-game (horizon, mortality) have their own, much smaller, in-game
    'options' command (_ingame_options) for a game already running.
    """
    while True:
        cfg = _apply_display_prefs(cfg)
        cur_width = settings.resolve_display_width(cfg)
        width_src = ("override" if isinstance(cfg.get("display_width"), (int, float))
                                   and cfg["display_width"] else
                    "detected from your terminal")
        print()
        print("-" * 78)
        print("   OPTIONS")
        print("-" * 78)
        print(_wrap("Preferences about this PROGRAM, not about any one game - "
                    "they apply whether you are starting a new one, loading an "
                    "old one, or running it from the command line with flags. "
                    "What a single playthrough is (civilisation, starting kit, "
                    "fog, mortality, the horizon) is asked when that game "
                    "starts, not here."))
        print()
        print("   1) save location      : %s"
              % settings.resolve_save_dir(cfg, ensure=False))
        print("   2) display width      : %d columns (%s)" % (cur_width, width_src))
        print("   3) rows per table      : %d" % settings.resolve_rows_per_page(cfg))
        print("   4) welcome/tutorial text on new games : %s"
              % ("on" if cfg.get("show_welcome", True) else "off"))
        print("   b) back to the main menu")
        try:
            raw = input("\n   > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); return cfg
        word = raw.split()[0] if raw.split() else ""

        if word in ("", "b", "back"):
            return cfg

        elif word in ("1", "save", "location"):
            cur = settings.resolve_save_dir(cfg, ensure=False)
            print(_wrap("Where new games are saved, and where 'Load a saved "
                        "game' looks. Existing save files are not moved - use "
                        "'options' inside a game in progress to move that one "
                        "game's save."))
            if os.environ.get(settings.SAVE_DIR_ENV):
                print(_wrap("Note: the %s environment variable is set to %r "
                            "right now and overrides whatever is chosen here "
                            "until it is unset."
                            % (settings.SAVE_DIR_ENV,
                               os.environ[settings.SAVE_DIR_ENV])))
            try:
                raw2 = input("   New save directory [currently %s, blank to "
                             "leave unchanged]: " % cur).strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                continue
            newdir = os.path.expanduser(raw2)
            try:
                os.makedirs(newdir, exist_ok=True)
                probe = os.path.join(newdir, ".rome-write-test")
                with open(probe, "w"):
                    pass
                os.remove(probe)
            except OSError as e:
                print("   -- could not use that directory: %s" % e)
                continue
            cfg["save_dir"] = newdir
            settings.save_config(cfg)
            print("   -- saved. New games, and 'Load a saved game', will use %s"
                  % newdir)

        elif word in ("2", "width", "display"):
            print(_wrap("How many columns text wraps to and tables are sized "
                        "for. Left alone, the game asks your terminal and uses "
                        "that (right now it reads %d). Set a number to "
                        "override it - for a terminal that cannot be asked, or "
                        "one you simply want narrower or wider - or type "
                        "'auto' to go back to asking the terminal."
                        % settings.resolve_display_width(
                            dict(cfg, display_width=None))))
            try:
                raw2 = input("   New width [currently %d (%s), a number, "
                             "'auto', or blank to leave unchanged]: "
                             % (cur_width, width_src)).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                continue
            if raw2 in ("auto", "detect", "default"):
                cfg["display_width"] = None
                settings.save_config(cfg)
                print("   -- saved. Width will be asked from your terminal "
                      "from now on.")
                continue
            try:
                display_width = int(raw2)
                if display_width < 20:
                    raise ValueError
            except ValueError:
                print("   -- a whole number of columns (at least 20), 'auto', "
                      "or blank.")
                continue
            cfg["display_width"] = display_width
            settings.save_config(cfg)
            print("   -- saved. %d columns from now on." % display_width)

        elif word in ("3", "rows", "page"):
            try:
                raw2 = input("   Rows per table before paging [currently %d, "
                             "blank to leave unchanged]: "
                             % settings.resolve_rows_per_page(cfg)).strip()
            except (EOFError, KeyboardInterrupt):
                print(); continue
            if not raw2:
                continue
            try:
                rows_per_page = int(raw2)
                if rows_per_page <= 0:
                    raise ValueError
            except ValueError:
                print("   -- a whole number of rows, more than 0.")
                continue
            cfg["rows_per_page"] = rows_per_page
            settings.save_config(cfg)
            print("   -- saved.")

        elif word in ("4", "welcome", "tutorial"):
            value = _ask("   Show the welcome message and tutorial on new games? "
                     "[y/n] ", ["y", "n"],
                     "y" if cfg.get("show_welcome", True) else "n")
            if value:
                cfg["show_welcome"] = (value == "y")
                settings.save_config(cfg)
                print("   -- saved.")

        else:
            print("   -- 1 to 4, or b.")


def cmd_menu(a):
    """The front door for a person, rather than for a script.

    Everything here can be done with command-line flags, and the flags are
    what a script should use. This exists because "what do I type" was the
    first thing every human tester had to be told out of band, and because a
    game about arriving somewhere should be able to tell you where you have
    arrived before it asks you to make decisions about it.

    Three doors: start a new game, resume one from a list rather than a
    remembered filename, or change a few things that should not need a flag
    every time (chiefly where saves go - see settings.py). Five playtesters
    reached for --help before this existed; the point of this function is
    that none of them should have had to know that flag existed at all.
    """
    civs = _load_civ_list()
    # THE APPLICATION'S OWN PREFERENCES, BEFORE THE FIRST LINE IS PRINTED, so
    # even this opening banner wraps to a player's chosen/detected width -
    # see _apply_display_prefs. Reloaded every time the loop comes back
    # around (below) so a width or welcome-text change made from Options
    # takes effect the moment the player is back at this menu, with no
    # restart.
    cfg = _apply_display_prefs()

    if cfg.get("show_welcome", True):
        print()
        print("=" * 78)
        print("   ONE PERSON, AND EVERYTHING THEY KNOW".center(78))
        print("=" * 78)
        print()
        print(_wrap(
            "You are one person, dropped into a pre-industrial society, carrying "
            "the knowledge of how modern technology works and none of the industry "
            "that makes it. Knowing how a thing works is free. Building it is not: "
            "it costs your own hours, other people's hours, money, materials, and "
            "years you do not get back."))
        print()
        print(_wrap(
            "You arrive alone. No employees, no slaves, nobody who owes you "
            "anything, and about enough money to eat for a few months."))
        print()

    while True:
        cfg = _apply_display_prefs()
        print("-" * 78)
        print("   MAIN MENU")
        print("-" * 78)
        print()
        print("   1) New game")
        print("   2) Load a saved game")
        print("   3) Options")
        print("   q) Quit")
        try:
            raw = input("\n   > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); return 0
        word = raw.split()[0] if raw.split() else ""

        if word in ("q", "quit", "exit"):
            return 0
        elif word in ("1", "new", "start"):
            print()
            return_code = _new_game(civs, cfg)
            if return_code is not None:
                return return_code
            print()
        elif word in ("2", "load", "resume", "continue"):
            print()
            return_code = _load_game(cfg)
            if return_code is not None:
                return return_code
            print()
        elif word in ("3", "options", "option", "settings"):
            _options_menu(cfg)
            print()
        else:
            print("   -- 1, 2, 3 or q.\n")


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
    # pass. --search-rounds 0 (the default) leaves `plan` exactly as it was;
    # a nonzero value diagnoses the binding constraint against a dice-free
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
