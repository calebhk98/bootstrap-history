"""Planning and diagnostic commands: `plan`, `search`, `why`.

`plan` and `search` compute a strategy order
(critical-path method, optionally refined by `path_search.py`'s dice-free
search) instead of walking a hand-written list; `why` explains one tree node
in isolation. None of the three is reached from `play` or `agent` - see each
function's own docstring for why a strategy file is public information, not
a live look into a fogged session's own state.

`cmd_sweep` stayed behind in cli.py rather than joining this file: it
constructs `Sim(...)` directly, and `sim/tests/test_complaint_38_founder_lifetime.py`
monkeypatches `engine.cli.Sim` before calling it, to record every cfg a
sweep point builds. That patch rebinds the name `Sim` only in cli.py's own
namespace - a function defined here would keep resolving `Sim` against
THIS module's `from .core import Sim`, unaffected by the patch, and the
test would silently stop recording anything. `cmd_plan` also calls
`Sim(...)` (its --refine-rounds path) but nothing patches `engine.cli.Sim`
before calling `cmd_plan`, so moving it here is safe - see cli.py's own
comments on `DetRNG` and `Sim` for the general shape of this hazard.
"""
import os, random, sys

from .data import closure, critical_path, load, load_civ, resolve_goal, topo_order
from .core import Sim
from sim.constants import declare
from sim.unit_conversions import PERCENT_SCALE
from sim.presentation import EXPLAIN_NEAR_MATCH_SUGGESTIONS_SHOWN
from sim.world.agriculture import (
    DEFAULT_STORAGE_TECHNIQUE, annual_food_demand_kg_per_person,
    calculate_granary_runway, granary_capacity_kg,
)

from .cli import _founder_lifetime_hours


def granary_projection(sim):
    """Player-facing forecast backed by the same calculation as the turn."""
    demand = (sim._adult_equivalent_population(sim.population)
              * annual_food_demand_kg_per_person())
    return calculate_granary_runway(
        sim.farm_stock_kg, demand,
        DEFAULT_STORAGE_TECHNIQUE.spoilage_rate_per_year,
        granary_capacity_kg(demand))


def cmd_plan(args):
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
    _repodir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _repodir not in sys.path:
        sys.path.insert(0, _repodir)
    from sim import planner as _planner
    tree, _prices, nodes, _wages, _goods = load()
    goal = resolve_goal(tree, nodes, args.goal)
    if not args.search_rounds:
        # UNCHANGED FROM BEFORE. Purely structural CPM, optionally refined
        # against real trials - the path every existing caller and test
        # already exercises.
        order, rationale, _cpm_result = _planner.plan(
            civ=args.civ, goal=args.goal, seed_strategy=args.seed_strategy,
            side_branches=args.side_branches, side_branch_every=args.side_branch_every,
            refine_rounds=args.refine_rounds, trial_count=args.mc,
            horizon=args.horizon, seed=args.seed)
        label = ("PLANNED (CPM): backward-chained from %s over its "
                "prerequisite closure for %s%s" % (goal, args.civ,
                ", refined against real trials" if args.refine_rounds else ""))
        _planner.write_strategy(args.out, label, rationale, order)
        print("wrote %d nodes to %s" % (len(order), args.out))
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
    from sim import path_search as _search
    _search.ensure_fixed_hash_seed()
    seed_order = _planner.load_seed(args.seed_strategy, nodes)
    order, extras, history = _search.search(
        civ=args.civ, goal=args.goal, side_branches=args.side_branches,
        side_branch_every=args.side_branch_every, rounds=args.search_rounds,
        horizon=args.search_horizon, backlog_ratio=args.search_backlog_ratio,
        seed_order=seed_order,
        grow_supply_moves=not args.search_no_grow_supply)
    last = history[-1]
    rationale = [
        "Deterministic search (path_search.py): critical-path order, then "
        "%d round(s) of diagnosing the binding constraint against a "
        "dice-free trial (no events, no project failures, immortal "
        "founder, %d-year horizon) and relaxing it, keeping whichever "
        "round scored best." % (len(history), args.search_horizon),
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
    if args.refine_rounds:
        # SAME RELATIONSHIP `plan()` ALREADY HAS TO `refine()`: the search's
        # own order and side branches become what gets measured and
        # advanced round by round, instead of planner.plan() deriving a
        # fresh CPM pass that does not know about the search's relaxation.
        probe_sim = Sim(nodes, [], random.Random(args.seed), events=False, civ=load_civ(args.civ))
        order, extras, score = _planner.refine(
            nodes, goal, probe_sim, order, extras, args.civ, args.mc, args.horizon, args.seed,
            args.refine_rounds, args.side_branch_every)
        if score is not None:
            rationale.append(
                "Refined over %d round(s) of %d trials each at a %d-year "
                "horizon (seed %d), starting from the search's own order: "
                "%d/%d trials reached the goal in the final round."
                % (args.refine_rounds, args.mc, args.horizon, args.seed, score[0], args.mc))
    label = ("PLANNED (CPM + deterministic search%s): backward-chained from "
            "%s over its prerequisite closure for %s" % (
                ", refined against real trials" if args.refine_rounds else "",
                goal, args.civ))
    _planner.write_strategy(args.out, label, rationale, order)
    print("wrote %d nodes to %s" % (len(order), args.out))
    for line in rationale:
        print("  - " + line)
    return 0


def cmd_search(args):
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
    _repodir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _repodir not in sys.path:
        sys.path.insert(0, _repodir)
    from sim import path_search as _search
    order, rationale = _search.plan_and_write(
        args.civ, args.goal, args.out, args.side_branches, args.side_branch_every, args.rounds,
        args.horizon, args.backlog_ratio, args.seed_strategy, args.no_grow_supply)
    print("wrote %d nodes to %s" % (len(order), args.out))
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


def cmd_why(args):
    """Explain one node: what it needs, what needs it, and what it costs."""
    tree, prices, nodes, wages, goods = load()
    node_id = args.node
    if node_id not in nodes:
        near = [candidate_id for candidate_id in nodes if args.node.lower() in candidate_id.lower()]
        raise SystemExit("unknown node. did you mean: %s" % (", ".join(near[:EXPLAIN_NEAR_MATCH_SUGGESTIONS_SHOWN]) or "no idea"))
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
          (f"{node_record['ph']:,}", PERCENT_SCALE * node_record["ph"] / lifetime_hours,
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
    _goal_here = resolve_goal(tree, nodes, getattr(args, "goal", None))
    if _goal_here in blocks or _goal_here == node_id:
        print("   INCLUDING THE GOAL. This node is on the critical path.")
