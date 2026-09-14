#!/usr/bin/env python3
"""Find a working order in the world with the dice removed, then see how much
of it survives them.

THE OWNER'S OWN DIAGNOSIS, TAKEN LITERALLY. `planner.py` computes one
structural ordering by critical-path method and stops; this module is what
"solve the deterministic problem first" actually looks like. `run
--no-events` already turns off dated shocks, but a project's own risk of
FAILING outright is a separate roll in `projects.py:_complete`
(`self.rng.random() < n["risk"]`) that fires whether or not events are on -
so a fully dice-free trial needs a seeded rng whose `random()` always returns
1.0, never below any probability threshold anywhere in the engine (a
project's failure risk, the 3.5% yearly attrition roll, the 25% manumission
roll, the fractional-headcount rounding in `_stochastic_round`). See
`DetRNG` in `engine/cli.py` - shared from there because `--deterministic` on
`run`/`compare`/`play`/`agent` needs the exact same rng, for the exact same
reason. Nothing in `core.py`, `projects.py`, `labour.py`, `society.py` or
`economy.py` is edited to get this - the same rules run, against a
different sequence of "how did that roll come out".

THE FIRST QUESTION - DOES THE CURRENT PLAN EVEN GET THERE WITH THE DICE
OFF? - turns out to have a real, specific answer, not a shrug: no, and not
because of money or the generic scholar/artisan pools, both of which end up
abundant (tens of millions of denarii, hundreds of scholars and artisans).
It stalls on a small, fixed set of NAMED CRAFT TRADES the tree calls
`TRADES_ABSENT` - chemist, electrician, engineer, machinist, optician -
which do not exist in this civilisation at all until you personally teach
them (`labour.py:trade_available`), and which grow ONLY through
`step()`'s once-a-year, two-people-at-a-time auto-teach (core.py, "4a2"),
gated further by a 25-year per-trade cooldown. Once a trade's headcount is
above zero, `market_supply(t) <= 0.0` - the sole trigger auto-teach uses to
decide a trade is worth training more of - is simply never true again unless
every last person of that trade dies out, so in a deathless, failure-free
world a trade that got taught once, early, for two people, STAYS at two
people for the rest of the run, however many projects are starved for it.
That is not a bug this module can fix (core.py/labour.py are not this
module's to edit); it is a fact about how the given rules grow named-trade
labour, and the only lever a strategy ORDER has over it is which nodes get
to spend that frozen, tiny pool of hours, and in what sequence.

THE BINDING CONSTRAINT, MEASURED: on Rome's planned order, three nodes -
`steam_atmospheric`, `interchangeable_parts`, `spectroscope` - go active
early, need machinist/chemist/engineer hours nothing else in the run can
supply, and never finish. Fifty-six of the tree's other 168 closure nodes sit
downstream of those three and can never even start. And the planner's own
`pick_side_branches` - which ranks candidates purely by return on capital,
with no idea the tree has any scarce labour at all - hands the household
several more nodes (locomotives, TNT, dynamite, double-acting engines) that
draw on the EXACT SAME five trades, spread through the order specifically so
they compete with the spine for it throughout the run. Ranking those
candidates by how soon they can even legally start instead looks like an
obvious fix and is NOT one - tried and measured (see `pick_side_branches`'s
own docstring and PATH_SEARCH.md), it left Rome roughly unchanged and cost
Han 124 years, or cost Rome the goal entirely within 1,200 years once
reworked to stop doing that to Han. Reverted; recorded so nobody re-walks
into it.

A SECOND, LARGER CONSTRAINT, MEASURED THE SAME WAY (against the real
rome_434_goal_startable.json / rome_380_corpus_bug.json fixtures - a player
three times stronger than this order): the planned order's dice-free trial
sits at capital -4,789, zero scholars, zero artisans and 30/168 of the
closure done at year 434 AD, against the fixture's +607,402,406 / 162 / 491
/ 167/168 at the SAME calendar year - and stays that poor, essentially
unchanged, for roughly 850 MORE years (see PATH_SEARCH.md). Every one of the
eight institutions `planner.pick_staffing` already names - the same ones
that train the scholars and artisans `staff_capacity()` gates almost
everything else on - was founded by that player 322 to 800+ years before
this order manages it. `diagnose_capital_trap` reads this off a live Sim
the same way `diagnose_scarce_trades` already does; `grow_supply` (move 3
below) is what tries to do something about it.

THE SEARCH. Three moves, applied to the CPM order `planner.backward_plan`
already computes, chosen because they attack these specific, measured
constraints rather than guessing at the space of all 168! orderings:

  1. PULL every side branch that draws on a currently-scarce trade OUT of
     the interleaved order entirely, to the very end (after the spine, after
     the goal). A side branch is optional by definition - it exists only to
     fund the spine - so one that competes with the spine for the one
     resource actually blocking the spine is worse than not building it at
     all, and `refine`'s own measured finding on staffing institutions
     already established that "obviously helpful" is not the same claim as
     "measured helpful" for this exact tree.

  2. WITHIN a tied CPM slack band (nodes the graph itself cannot tell apart -
     see planner.py's own comment on why this is exactly where a seed or a
     tie-break is honest to apply), move nodes that draw on a scarce trade
     to the FRONT of the band, smallest total scarce-trade hours first. This
     is shortest-processing-time-first, the standard remedy for many jobs
     queued on one non-shareable resource: it clears the queue soonest and
     is a strict refinement of the tie-break planner.py already documents as
     legitimate, not a new principle.

  3. GROW THE SUPPLY (`grow_supply`): when a dice-free trial reads as the
     capital trap above, try founding each of `planner.pick_staffing`'s
     institutions, one at a time, and keep only the ones a fresh dice-free
     trial measures as genuinely better - not "obviously helpful", the same
     discipline as move 1. This is the one move that can ADD something to
     the order rather than only resequence what moves 1 and 2 are given;
     see PATH_SEARCH.md for what it found when actually tried against this
     tree, honestly, rather than assumed either way.

All three moves are computed FROM a diagnostic run of the real Sim, not from
a second model of the tree - `diagnose_scarce_trades` and
`diagnose_capital_trap` read `s.active`, `s.employees`, `s.capital`,
`s.scholars`/`s.artisans` and `s.hours_you_can_call_on` off an actual
simulated household, the same object `run` would build. Each round
re-diagnoses from the current order's own simulated state, so a trade that
stops being scarce (finished, unblocked) stops being treated as one, and a
round - or a candidate institution - that does not improve on the previous
best is simply not kept - see `search()`. This is "repeatedly relaxing
whatever the binding constraint turns out to be", one of the two methods the
brief itself names, extended from "resequence what is named" (moves 1-2) to
"try adding what is missing" (move 3) once resequencing alone was measured,
across a wide range of side-branch counts and placements, not to touch this
particular constraint at all (PATH_SEARCH.md). Still chosen over a
from-scratch metaheuristic (random-restart hill-climbing over raw orderings,
simulated annealing, ...) because the constraints here are not diffuse -
they are five named trades and eight named institutions, provably - and
searching blindly over 168! orderings to rediscover a fact already visible
in `s.active`/`s.capital` would be slower and no more honest than reading it
off the Sim directly.
"""
import argparse, os, random, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from engine.data import TRADES_ABSENT, closure, load, load_civ, resolve_goal
from engine.core import Sim
# DetRNG AND ensure_fixed_hash_seed LIVE IN engine/cli.py NOW, NOT HERE.
# `--deterministic` on `run`/`compare`/`play`/`agent` needed the exact same
# rng and the exact same hash-seed fix this module already had, and a second,
# separately-typed copy of either is exactly the kind of duplication that
# drifts the moment one copy is fixed and the other is not - see DetRNG's own
# docstring, now in engine/cli.py, for the fuller argument. This module
# already imported `load_strategy`/`topo_stable` from there, so importing
# these two the same way costs nothing new.
from engine.cli import (load_strategy, topo_stable, DetRNG,
                        ensure_fixed_hash_seed)

import planner as _planner


def deterministic_sim(nodes, order, goal, civ, horizon, bounty_set=None):
    """One dice-free trial of `order` against `civ`, to `horizon` years."""
    s = Sim(nodes, order, DetRNG(1), events=False,
            cfg={"immortal": True}, civ=load_civ(civ),
            bounty_set=set(bounty_set or ()))
    s.run(goal, horizon)
    return s


def fitness(s, need):
    """Higher is better. Reaching the goal beats not reaching it outright;
    among runs that reach it, earlier beats later; among runs that do not,
    more of the goal's own closure finished beats less, and surplus capital
    (not in arrears, not sitting on an unfunded programme) breaks the last
    tie. A plain tuple comparison reads this correctly with no weighting to
    tune, which is the whole reason it is shaped this way rather than as one
    blended score.
    """
    done = sum(1 for k in need if k in s.done)
    return (1 if s.goal_year else 0, -(s.goal_year or 10 ** 9), done, s.capital)


# ----------------------------------------------------------------------------
# Diagnose the binding constraint FROM the simulator's own state
# ----------------------------------------------------------------------------

def diagnose_scarce_trades(s, nodes, outstanding, backlog_ratio=6.0):
    """Which of the five taught trades (TRADES_ABSENT) are actually the
    thing holding this run up, read off a simulated household rather than
    guessed at.

    A trade counts as scarce here if (a) more than one node still
    outstanding wants it at all, and (b) the total hours those nodes still
    need of it (`backlog`) is worth more than `backlog_ratio` years of what
    the household can currently draw on in a single year
    (`hours_you_can_call_on`, the same ceiling `lab_year_draw` itself pays
    projects out of). `backlog_ratio` is a judgement call, not a measured
    constant: too low and a trade that is merely busy this decade gets
    treated as permanently frozen; too high and the five-trades-frozen-at-
    two-forever wall this module exists to work around goes undetected. 6
    years of backlog against one year of throughput is comfortably past
    "busy" for a game whose calendar floors are measured in single-digit
    years per node.
    """
    scarce = {}
    for t in TRADES_ABSENT:
        contested = [k for k in outstanding if nodes[k]["lab"].get(t, 0.0) > 0]
        if len(contested) < 2:
            continue
        backlog = sum(nodes[k]["lab"][t] for k in contested)
        supply = max(1.0, s.hours_you_can_call_on(t))
        if backlog / supply > backlog_ratio:
            scarce[t] = {"contested": contested, "backlog": backlog,
                         "supply_per_year": supply,
                         "employees": s.employees.get(t, 0.0)}
    return scarce


def stuck_active(s, need):
    """Nodes the goal needs that have been active a while and are making
    little or no headway - the visible symptom `diagnose_scarce_trades`
    explains the cause of. Purely descriptive (used for the report, not the
    search itself), read straight off `s.active`.
    """
    out = []
    for k, st in s.active.items():
        if k not in need:
            continue
        if st.get("stalled_years", 0) > 0 or st.get("short_of_trade") or st.get("waiting_on_money"):
            out.append(k)
    return sorted(out)


def diagnose_capital_trap(s, need, min_closure_frac=0.9):
    """Is this dice-free household caught in the insolvency cycle
    `engine/projects.py` (`enforce_credit_limit`/`auto_open_ventures`) itself
    documents as a known risk - "half the credit line is the line: below it
    you can still open your way out, above it you are digging" - rather than
    genuinely progressing?

    MEASURED, AGAINST THE 434 AD FIXTURE, NOT GUESSED. Rome's planned order,
    run dice-free to year 434, sits at capital -4,789, zero scholars, zero
    artisans, 30/168 of the closure done; the fixture (a real, far stronger
    playthrough) is at +607,402,406, 162 scholars, 491 artisans, 167/168 at
    the SAME calendar year. Traced further, the planned order's own capital
    stays negative and its scholars/artisans stay at exactly 0.00 for roughly
    850 more years (see PATH_SEARCH.md): a run in this state is not merely
    slow, it is not accumulating either of the two things - money or trained
    people - that everything else in the engine gates on. Both being still
    at (approximately) zero this deep into a run, with most of the goal's
    own closure still undone, is the read-off-the-Sim signature of that
    trap, not a structural guess about WHY it is trapped.

    NOT "capital < 0" ALONE - a household that is merely poor early on, on
    its way to being rich later (Han's own dice-free trial dips negative for
    a while too, see PATH_SEARCH.md section 1), is not this. It is the
    COMBINATION - negative capital, no staff to speak of, most of a long
    goal still undone - that marks a household stuck rather than simply
    early.
    """
    if s.capital >= 0:
        return None
    if s.scholars > 1.0 or s.artisans > 1.0:
        return None
    done_frac = sum(1 for k in need if k in s.done) / max(1, len(need))
    if done_frac >= min_closure_frac:
        return None
    return {"capital": s.capital, "scholars": s.scholars, "artisans": s.artisans,
            "closure_done_frac": done_frac}


# ----------------------------------------------------------------------------
# The moves
# ----------------------------------------------------------------------------

def _needs(nodes, k, trades):
    return any(nodes[k]["lab"].get(t, 0.0) > 0 for t in trades)


def _scarce_hours(nodes, k, trades):
    return sum(nodes[k]["lab"].get(t, 0.0) for t in trades)


def pull_scarce_extras(order, nodes, need, scarce):
    """Move 1: any node OUTSIDE the goal's own closure that draws on a
    currently-scarce trade goes to the very end, after everything the goal
    needs. It is there to fund the spine; a side branch that instead
    competes with the spine for the one resource holding the spine up is a
    net cost, not a net gain - see the module docstring's measured account
    of the seven of Rome's twelve picked side branches that do exactly this.
    Relative order of everything else is untouched.
    """
    if not scarce:
        return list(order)
    keep, pulled = [], []
    for k in order:
        if k not in need and _needs(nodes, k, scarce):
            pulled.append(k)
        else:
            keep.append(k)
    return keep + pulled


def spt_within_slack_bands(order, nodes, need, c, scarce):
    """Move 2: within each tied CPM slack band (planner.py's own definition
    of "the graph cannot tell these apart"), nodes that draw on a currently
    scarce trade move to the front of the band, smallest total scarce-trade
    hours first - shortest-processing-time-first, which clears a shared,
    non-shareable resource in the least total time. Nodes outside the goal's
    closure (no CPM slack of their own) and nodes that need no scarce trade
    keep their existing relative order, band by band.
    """
    if not scarce:
        return list(order)
    slack = c["slack"]
    out = []
    i = 0
    n = len(order)
    while i < n:
        k = order[i]
        if k not in need:
            out.append(k)
            i += 1
            continue
        band = round(slack.get(k, 0.0), 3)
        j = i
        group = []
        # A "band" is a maximal run of CONSECUTIVE spine nodes sharing this
        # exact slack value - not every node in the tree with this slack,
        # because side branches interleaved between them are not fungible
        # with spine placement and moving spine nodes PAST an interleaved
        # side branch would silently undo the funding cadence `interleave`
        # was built to give the household.
        while j < n and order[j] in need and round(slack.get(order[j], 0.0), 3) == band:
            group.append(order[j])
            j += 1
        group.sort(key=lambda x: (0, _scarce_hours(nodes, x, scarce)) if _needs(nodes, x, scarce)
                                  else (1, 0.0))
        out.extend(group)
        i = j
    return out


def grow_supply(nodes, goal, need, s0, cur_order, cur_extras, civ, horizon,
                 side_branch_every, base_fit, log):
    """Move 3: GROW THE SUPPLY, rather than only resequence what is already
    named - the move the brief itself asked for and the first two moves
    cannot express between them.

    Pulling a side branch to the end (move 1) or resequencing a tied slack
    band (move 2) both only change WHICH of the goal's own closure or the
    named side branches goes first; neither can add anything NEW. The
    player behind rome_434_goal_startable.json reached 434 AD with 607
    million denarii, 636 employees and 167/168 of the closure done -
    against this order's -4,789, zero, zero and 30/168 at the identical
    calendar year (see PATH_SEARCH.md) - and every one of the eight
    institutions `planner.pick_staffing` already NAMES (it schedules none
    of them - see its own docstring) was founded by that player 322 to 800+
    years before this order manages it. That is growth this move can
    actually try: found an institution, and see whether the household it
    produces is genuinely better off, not assume it either way.

    MEASURED, NOT ASSUMED, ONE AT A TIME. `pick_staffing`'s own earlier
    finding - "putting them in this order made the run worse" - tested
    adding ALL of them, unconditionally, at the very front. This tries each
    one individually, appended to whatever extras already survived, and
    keeps it only if a fresh dice-free trial's `fitness` is STRICTLY better
    with it than without - the same "measure, do not assume" discipline
    `refine()` (planner.py) already applies to a captured winner's order,
    applied here to a candidate institution instead. A candidate that is
    not kept is not tried again the same way; the order is exactly as if it
    had never been offered.
    """
    candidates = [k for k in _planner.pick_staffing(nodes, need, s0)
                  if k not in cur_extras]
    extras = list(cur_extras)
    fit = base_fit
    tried = []
    for k in candidates:
        trial_extras = extras + [k]
        spine = [x for x in cur_order if x in need]
        trial_order = _planner.interleave(spine, trial_extras, side_branch_every)
        full = _planner._repaired(nodes, goal, trial_order)
        sim = deterministic_sim(nodes, full, goal, civ, horizon)
        trial_fit = fitness(sim, need)
        kept = trial_fit > fit
        tried.append({"institution": k, "kept": kept, "fitness": trial_fit})
        log("    try founding %-22s -> %s (closure %d, capital %.0f)"
            % (k, "kept: genuinely better" if kept else "discarded: no better",
               trial_fit[2], trial_fit[3]))
        if kept:
            extras, fit = trial_extras, trial_fit
    return extras, fit, tried


# ----------------------------------------------------------------------------
# The search itself: diagnose, relax, re-simulate, keep what improves
# ----------------------------------------------------------------------------

def search(civ="rome_100ad", goal=None, side_branches=12, side_branch_every=8,
           rounds=6, horizon=500, backlog_ratio=6.0, seed_order=None,
           grow_supply_moves=True, log=print):
    """Plan by CPM, then repeatedly diagnose the binding constraint against a
    dice-free trial of the current order and relax it, keeping whichever
    round's order scored best (see `fitness`).

    `seed_order`: the same kind of tie-break `planner.backward_plan` already
    accepts (a previous plan's or a captured winner's order) - passed
    straight through to the initial CPM pass so `--search-rounds` composes
    with `--seed-strategy` instead of ignoring it.

    `grow_supply_moves`: try `grow_supply` (move 3, founding institutions
    one at a time, kept only if measured better) whenever a round's own
    dice-free trial reads as the capital trap `diagnose_capital_trap`
    describes. Tried AT MOST ONCE per search() call, regardless of how many
    rounds run: the trap, once present, is measured (PATH_SEARCH.md) to
    persist for centuries under this order, so a round that finds it still
    present after growth was already tried once would only re-discover the
    same "no better" answer at the cost of one dice-free trial per
    candidate institution, every round, for no new evidence. `False` skips
    move 3 entirely and reproduces the exact behaviour this module had
    before it existed.

    Returns (best_order, best_extras, history) where `history` is one dict
    per round: the scarce trades found, the stuck nodes they explain, the
    capital trap diagnosis (if any) and what growing supply did about it,
    and the fitness reached - the evidence `main()` writes into the
    strategy file's own rationale and PATH_SEARCH.md draws its numbers from.
    """
    ensure_fixed_hash_seed()
    tree, prices, nodes, wages, goods = load()
    goal = resolve_goal(tree, nodes, goal)
    need = closure(nodes, goal)
    s0 = Sim(nodes, [], random.Random(1), events=False, civ=load_civ(civ))
    order, c, extras, staffing = _planner.backward_plan(
        nodes, goal, s0, seed_order=seed_order, side_branches=side_branches,
        side_branch_every=side_branch_every)

    history = []
    best_order, best_extras, best_fit = order, extras, None
    cur_order, cur_extras = order, extras
    grown = False
    for rnd in range(rounds):
        full = _planner._repaired(nodes, goal, cur_order)
        sim = deterministic_sim(nodes, full, goal, civ, horizon)
        fit = fitness(sim, need)
        stuck = stuck_active(sim, need)
        outstanding = [k for k in (need | set(cur_extras)) if k not in sim.done]
        scarce = diagnose_scarce_trades(sim, nodes, outstanding, backlog_ratio)
        trap = diagnose_capital_trap(sim, need)
        rec = {"round": rnd, "goal_year": sim.goal_year,
               "closure_done": fit[2], "capital": sim.capital,
               "stuck": stuck, "scarce_trades": sorted(scarce),
               "scarce_detail": scarce, "capital_trap": trap, "grow_supply_tried": []}
        history.append(rec)
        log("  round %d: %d/%d closure nodes done%s, stuck on %s, scarce trade(s): %s%s"
            % (rnd, fit[2], len(need),
               (" (goal reached %d AD)" % sim.goal_year) if sim.goal_year else "",
               ", ".join(stuck) or "(nothing)", ", ".join(sorted(scarce)) or "(none)",
               ", capital trap (capital %.0f, %.1f closure done)"
               % (trap["capital"], trap["closure_done_frac"]) if trap else ""))
        if best_fit is None or fit > best_fit:
            best_fit, best_order, best_extras = fit, cur_order, cur_extras
        if sim.goal_year:
            log("  goal reached; stopping the search early")
            break
        # MOVE 3, AT MOST ONCE: grow the supply itself rather than only
        # resequence what is already named - see grow_supply's own
        # docstring for why this is a genuinely different kind of move from
        # 1 and 2 below, and the module docstring / PATH_SEARCH.md for why
        # it is tried and measured here rather than assumed to help.
        if grow_supply_moves and trap and not grown:
            grown = True
            log("  capital trap detected; trying grow_supply (founding "
                "institutions one at a time, kept only if measured better)")
            new_extras, new_fit, tried = grow_supply(
                nodes, goal, need, s0, cur_order, cur_extras, civ, horizon,
                side_branch_every, fit, log)
            rec["grow_supply_tried"] = tried
            if new_fit > fit:
                cur_extras = new_extras
                cur_order = _planner.interleave(
                    [k for k in cur_order if k in need], cur_extras, side_branch_every)
                fit = new_fit
                if fit > best_fit:
                    best_fit, best_order, best_extras = fit, cur_order, cur_extras
                log("  grow_supply improved this round's order; continuing "
                    "from it")
                continue
            log("  grow_supply tried %d candidate(s), kept none: no "
                "institution measured better than the order without it"
                % len(tried))
        if not scarce:
            # Nothing currently reads as a resource bottleneck by this
            # round's own diagnosis. Either the run is money/calendar-bound
            # instead (nothing this module can relax - see planner.py's own
            # position on not modelling money live) or a previous round
            # already relaxed everything this method knows how to relax;
            # burning the rest of the round budget re-deriving the same
            # order would not find anything new.
            log("  no scarce-trade bottleneck detected; stopping early")
            break
        spine = [k for k in cur_order if k in need]
        new_spine = spt_within_slack_bands(spine, nodes, need, c, scarce)
        new_order = pull_scarce_extras(
            _planner.interleave(new_spine, cur_extras, side_branch_every),
            nodes, need, scarce)
        if new_order == cur_order:
            log("  relaxation made no change to the order; stopping early")
            break
        cur_order = new_order
    return best_order, best_extras, history


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--civ", default="rome_100ad")
    ap.add_argument("--goal", default=None)
    ap.add_argument("--out", required=True, help="strategy file to write")
    ap.add_argument("--side-branches", type=int, default=12)
    ap.add_argument("--side-branch-every", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--horizon", type=int, default=500,
                    help="dice-free horizon used WHILE searching - kept short "
                         "for speed; verify the winner separately at a longer "
                         "horizon and then against real seeds")
    ap.add_argument("--backlog-ratio", type=float, default=6.0)
    ap.add_argument("--seed-strategy", default=None,
                    help="a strategy name or path whose order breaks ties "
                         "among nodes the critical path ranks as equally "
                         "urgent, same as planner.py's own --seed-strategy")
    ap.add_argument("--no-grow-supply", action="store_true",
                    help="skip move 3 (founding institutions one at a time, "
                         "kept only if measured better) and reproduce this "
                         "module's behaviour before it existed - moves 1 and "
                         "2 (pulling/resequencing what is already named) only")
    a = ap.parse_args()
    t0 = time.time()
    order, rationale = plan_and_write(
        a.civ, a.goal, a.out, a.side_branches, a.side_branch_every, a.rounds,
        a.horizon, a.backlog_ratio, a.seed_strategy, a.no_grow_supply)
    print("wrote %d nodes to %s in %.1fs" % (len(order), a.out, time.time() - t0))
    for line in rationale:
        print("  - " + line)


def plan_and_write(civ="rome_100ad", goal=None, out=None, side_branches=12,
                    side_branch_every=8, rounds=6, horizon=500,
                    backlog_ratio=6.0, seed_strategy=None,
                    no_grow_supply=False, log=print):
    """The whole CLI pipeline in one call: fix the hash seed, run `search()`,
    build the rationale a strategy file's own reader sees, and write it to
    `out`.

    ONE BODY, TWO FRONT DOORS. This module's own `main()` above and
    `simulator.py search` (engine/cli.py's `cmd_search`) both call this
    instead of each independently turning `search()`'s return value into a
    written file and a printed rationale - the same principle `cmd_plan`
    already applies to `planner.plan()`, and for the same reason: two places
    deciding what a search result MEANS is two places that can quietly
    disagree about it, one bugfix at a time.
    """
    ensure_fixed_hash_seed()
    _tree0, _p0, _nodes0, _w0, _g0 = load()
    seed_order = _planner.load_seed(seed_strategy, _nodes0)
    order, extras, history = search(civ, goal, side_branches, side_branch_every,
                                    rounds, horizon, backlog_ratio,
                                    seed_order=seed_order,
                                    grow_supply_moves=not no_grow_supply, log=log)
    tree, _p, nodes, _w, _g = load()
    goal = resolve_goal(tree, nodes, goal)
    last = history[-1]
    grown = [h for h in history if h["grow_supply_tried"]]
    kept = [t["institution"] for h in grown for t in h["grow_supply_tried"] if t["kept"]]
    rationale = [
        "Deterministic search (rome/sim/path_search.py): CPM order, then up "
        "to %d rounds of diagnosing the binding constraint against a "
        "dice-free trial (no events, no project failures, immortal founder) "
        "and relaxing it, keeping whichever round scored best." % rounds,
        "Final round %d: %d/%d closure nodes done%s. Scarce trade(s) found: "
        "%s." % (last["round"], last["closure_done"],
                len(closure(nodes, goal)),
                (", goal reached %d AD" % last["goal_year"]) if last["goal_year"] else "",
                ", ".join(last["scarce_trades"]) or "(none)"),
    ]
    if grown:
        n_tried = sum(len(h["grow_supply_tried"]) for h in grown)
        rationale.append(
            "Grow-supply (move 3): a capital trap was diagnosed and %d "
            "candidate institution(s) were tried, one at a time, each kept "
            "only if a fresh dice-free trial measured strictly better with "
            "it than without. Kept: %s."
            % (n_tried, ", ".join(kept) if kept else "none - no institution "
               "measured better than the order without it"))
    _planner.write_strategy(out, "SEARCHED (deterministic): %s over %s's "
                            "critical-path order, relaxed against its own "
                            "scarce-trade bottleneck" % (goal, civ),
                            rationale, order)
    return order, rationale


if __name__ == "__main__":
    main()
