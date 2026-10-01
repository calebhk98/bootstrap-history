"""Ask the price solver for a price, with the book as fallback.

`data/prices.json` is a list of numbers the game trusts because nothing else
computes them - "91.8% the author's own estimates," in the price solver's own
words. `sim/solve_prices.py` can now compute a real number for most of them,
gated to what a civilization has actually reached (Complaints/39), but it is
still standalone: nothing in `sim/engine/` calls it. This module is that
call. It is deliberately thin - it does not re-implement the solver, it
imports it - and it is deliberately the ONLY new surface this round touches
beyond `sim/engine/data.py`, per this change's own scope: economy.py, which
actually spends a price on something, is another agent's file this round.

THE WAGE ARGUMENT (`prices_json` below) is a wage document in the book's
shape, built by `sim.world.wages.WageSchedule.document()`, so the solver and
payroll read one wage vector. Its labourer rate is the money value of one
labour hour.

THE INTERFACE. One function matters to a caller:

    solved_prices(held_technology_ids, prices_json)   -> a SolvedPrices

and one function does the actual replacement `data.py` wants:

    priced_goods_table(held_technology_ids, book_goods_denarii, prices_json)
        -> (goods_denarii, provenance)

`goods_denarii` is a plain {material: price} dict in the SAME units and over
the SAME keys as `prices.json`'s own goods table, so a caller that already
consumes that table (which is all of `sim/engine/economy.py`, untouched this
round) would not have to change to use it. `provenance` is {material:
"solved" | "book"} for every material the book prices - the measurable
burndown the stakeholder asked for: as more of `data/production/` gets
`requires_node` labels and more materials resolve, the "book" count in that
dict falls, and that count is the whole point of this file existing.

CACHE KEY: THE SET OF GATE NODES HELD, PLUS THE CIVILIZATION FOR LAND RENT.
See RENT NEEDS A CIVILIZATION below for why a bare gate-node set stopped
being enough. The gate-node reasoning that follows is otherwise unchanged.
`solve_prices.py`'s own docstring measured this: a gated solve costs 0.371s,
but only 82 of the tree's 2,864 nodes (2.9%) are ever named by a
`requires_node` anywhere in `data/production/` - a GATE, in this file's
terms. Every other node a civilization holds cannot possibly change which
technique is cheapest, because no recipe's availability depends on it. So
caching on the full held-technology set (which changes on almost every
turn, as ordinary non-gate nodes complete) would almost never hit, and
caching on the gate subset intersected with what is held changes only on the
roughly 3% of unlocks that could actually move a price - at most 82 distinct
values over an entire game, and typically far fewer. `all_gate_nodes` computes
that subset once from `data/production/` itself (every distinct
non-null `requires_node`, which by construction excludes both the
"available to everyone" state - `requires_node: null` - and the "nobody has
classified this yet" state - the field absent entirely; see
`solve_prices.techniques_available_to` for why those two are not gates
either), and `solved_prices` below intersects it with whatever the caller
passes as `held_technology_ids` before ever touching the cache. A caller
may pass its FULL technology set without pre-filtering; the exact same
gate-only key comes out the far side. This is also, incidentally, exactly
the right input to hand `solve_prices.techniques_available_to` for the
actual solve: a technique's `requires_node` is checked for membership in
`reached_nodes`, and a technique's `requires_node` is always a gate node by
this module's own construction, so the intersected set answers every
membership test the full held set would have, and answers it identically.

WHAT INVALIDATES THE CACHE. Nothing, ever, on its own - this is a plain
process-lifetime memo, not a TTL or an LRU. A cache entry stops being used
the moment the caller's held-technology set intersects the gate set
differently than before (a new gate node unlocked, which is the only event
that CAN change a solved price - see above), and a differently-keyed entry
is simply a different dict entry; nothing is ever evicted. This is safe
because `data/production/` does not change while one game is running (it is
committed data, read once and reused - see `_default_production_entries`
below) and because prices computed here are NEVER PERSISTED: nothing in this
module is a `SAVE_FIELDS` entry, no cached vector is written to a save, and
per CLAUDE.md section 3.5 it must not become one - a saved price vector from
an old build would be exactly the kind of migration hazard that section
rules out, and there is no need to invite it when a cache miss just re-solves
from the same committed data a fresh load would read anyway.

The one hazard this project has actually been burned by - `id()` recycling a
freed object's address into a live cache entry, see CLAUDE.md section 6 and
Complaints/27 - is guarded the same way `sim/engine/data.py`'s own
`descendants()` guards it: the cache entry holds the `production_entries`
object itself, not just its `id()`, and a lookup confirms the hit with `is`
before trusting it. A caller that hands in a DIFFERENT `production_entries`
object (a test building synthetic data, mainly) can never collide with a
real one that happens to reuse the same gate-node ids.

LABOUR-HOURS TO DENARII. `sim/solve_prices.py` prices everything in
labour-hours - one hour of `labourer`, its numeraire, equals 1.0 - because a
recipe graph can produce relative amounts of unskilled effort. Money enters
only here, at the edge: the wage document carries `money_per_labour_hour`,
which `sim.engine.wage_provider.build_schedule` derives from the
civilisation's coin (the coin material's solved labour hours per kg times the
coin's mass), so a price in money is its labour hours times that rate.
`denarii_per_labour_hour` is the one place the rate is read.

THIS MODULE DOES NOT DECIDE WHICH MATERIALS GET REPLACED - THAT SWITCH
LIVES IN `data.py`, AND IS OFF BY DEFAULT. `priced_goods_table` overlays a
solved price wherever `solve_prices` finds one AND the material is already a
key in the book (this round does not add new materials to the goods table,
only replaces the value under an existing key - a bigger wiring change than
"ask the solver first, fall back to the book"); everything else keeps its
book price, unchanged, and is marked "book" in the provenance dict rather
than silently agreeing with the book by accident. Nothing in this module is
called anywhere by default - see `sim/engine/data.py`'s `load()`, whose
`use_solved_prices` argument defaults to False specifically so this file's
existence changes no behaviour until something opts in.

WHAT THIS DOES NOT HANDLE, LEFT FOR THE NEXT STEP. `solve_prices.py` itself
flags MINOR JOINT BYPRODUCTS (silver from lead smelting and the like) as
mass-split artifacts rather than independent prices - see that module's own
docstring. This file still reports them as "solved" rather than a third
category, because inventing a three-way provenance split is a bigger design
decision than this round's brief ("solved, or book") asks for; a caller that
cares can already recover the distinction by re-running
`solve_prices.minor_joint_byproducts_are_unanchored` against the same
`SolvedPrices.chosen_recipe_by_material`, which is exposed for exactly that
kind of downstream question.

RENT MUST BE THREADED THROUGH HERE THE SAME WAY `main()` DOES IT (see
Complaints/43). `sim/solve_prices.py`'s own `main()` computes
`rent_hours_per_kg_by_ore_material` and `land_rent_hours_per_hectare` once
per run and threads the result through `compute_resolvable_materials` and
`solve` as `rent_hours_per_kg_by_material` - that is how `python3 sim/
solve_prices.py` prints a nonzero `hectare_land`. `solved_prices` below
calls the same two functions and passes the result through the same
argument, which is what keeps this module from silently falling into the
RENT_IS_ZERO behaviour Complaints/43 is about, since that argument
defaults to `None` in both functions when omitted.

RENT NEEDS A CIVILIZATION, AND SO DOES THE CACHE KEY.
`rent_hours_per_kg_by_ore_material` is safe to leave out of the
cache key (see WHAT THIS DOES NOT HANDLE above for its Rome-anchored
demand figure, which is not yet per-civilization either) but
`land_rent_hours_per_hectare` is genuinely per-civilization -
`sim/world/land.py` prices the margin of cultivation over a
CIVILIZATION'S OWN HELD REGIONS, and two civilizations can hold the exact
same gate-node set while holding completely different territory. A cache
key of `gate_nodes_held` alone cannot distinguish them, so a second
civilization asking this module for a price after a first one had already
solved would be silently handed the first civilization's land rent.
`solved_prices` and `priced_goods_table` below therefore take
an explicit `civilization_id` parameter and fold it into the cache key
alongside `gate_nodes_held`. It defaults to `None`, which resolves to
`solve_prices.DEFAULT_LAND_CIVILIZATION` (Rome) - the same default the CLI
uses when `--civ` is omitted - so every existing call site (which never
knew this parameter existed) keeps behaving exactly as it did with
`use_solved_prices=False`, and a NEW call site that wants a different
civilization's land priced correctly has to say so explicitly. This is a
correctness fix, not a widening of the wiring's scope: no new material is
priced, no new switch is flipped, `use_solved_prices` is still `False` by
default in `sim/engine/data.py`.
"""
import json
import os
import sys
from typing import Any, Dict, FrozenSet, Iterable, Optional, Set, Tuple

# TYPE ALIASES.
#
# Prices: a {material: price} table, in EITHER unit this module handles -
# labour-hours (solve_prices.py's own numeraire) or denarii
# (prices.json's/economy.py's) - see LABOUR-HOURS TO DENARII in the module
# docstring above for the conversion between them. The unit is never part
# of the type, the same way it is never part of a plain `float`; each
# function's own docstring says which one it is holding.
Prices = Dict[str, float]

# One entry of `data/production/*.json`'s own `materials` block, as
# `validate_production.load_production` hands it back (merged, but
# otherwise unchanged from the JSON). Left as `Dict[str, Any]` rather than
# a TypedDict: `data/production/_SCHEMA.md` documents a genuinely
# per-process-shape schema (a smelting entry and a synthesis entry do not
# share a field list), and this module only ever passes these entries
# through to `solve_prices.py` and `validate_production.py` (both
# unannotated, out of this task's scope) without reading their fields
# itself - the one exception, `entry.get("requires_node")` /
# `entry.get("outputs")` in `all_gate_nodes`/`priced_goods_table`, reads
# exactly the two fields every entry shares regardless of process shape.
ProductionEntries = Dict[str, Any]

# {material: "solved" | "gated" | "no_recipe"} - see priced_goods_table's
# own docstring for what the three strings mean. A plain Dict[str, str]
# rather than a Literal-keyed TypedDict: the KEYS are material ids, open
# and data-driven, exactly the case CLAUDE.md's TypedDict guidance carves
# out for a plain mapping - the fixed part is the three VALUES, which are
# documented in prose at every function that produces or reads one rather
# than re-declared as a type this small module has no other user of.
Provenance = Dict[str, str]

HERE = os.path.dirname(os.path.abspath(__file__))              # sim/engine
SIMDIR = os.path.dirname(HERE)                                  # sim
REPO_ROOT = os.path.dirname(SIMDIR)                             # repo root
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sim import joint_allocation, solve_prices              # noqa: E402
from sim.validate_production import load_production             # noqa: E402
from sim.world import wages                                     # noqa: E402
from sim.engine import money_units, wage_provider                # noqa: E402
from sim.engine import solve_cache                              # noqa: E402


class SolvedPrices(object):
    """One gated solve's result, cached and handed back verbatim on a hit.

    `prices_in_labour_hours` and `chosen_recipe_by_material` are exactly
    `solve_prices.solve`'s own return values, kept in the solver's native
    unit (see LABOUR-HOURS TO DENARII in the module docstring) so a caller
    that wants the solver's own numeraire, not a converted one, still can.
    `resolvable_materials` is which materials have ANY path to a price under
    this held-technology set - the set `priced_goods_table` overlays onto
    the book, and everything outside it is where the book fallback matters.
    `civilization_id` is the civilization `land_rent_hours_per_hectare` was
    solved against (see RENT NEEDS A CIVILIZATION in the module docstring) -
    kept on the result so a caller inspecting a cache hit can see which
    territory its land rent came from, rather than having to trust the
    cache key blindly.
    """
    __slots__ = ("prices_in_labour_hours", "resolvable_materials",
                "chosen_recipe_by_material", "converged", "iterations_run",
                "gate_nodes_held", "civilization_id")

    def __init__(self, prices_in_labour_hours: Prices,
                resolvable_materials: Set[str],
                chosen_recipe_by_material: Dict[str, Any],
                converged: bool, iterations_run: int,
                gate_nodes_held: FrozenSet[str], civilization_id: str) -> None:
        self.prices_in_labour_hours = prices_in_labour_hours
        self.resolvable_materials = resolvable_materials
        self.chosen_recipe_by_material = chosen_recipe_by_material
        self.converged = converged
        self.iterations_run = iterations_run
        self.gate_nodes_held = gate_nodes_held
        self.civilization_id = civilization_id


# `data/production/` is committed data: it does not change while a game is
# running, so it only ever needs to be read and merged once per process, and
# every caller that does not hand in its own `production_entries` (real
# engine use, always; only tests with synthetic data pass their own) shares
# this ONE object. Sharing the object, not just the data, is what lets the
# cache below use `is` rather than re-hashing the whole dict on every lookup
# - see WHAT INVALIDATES THE CACHE above.
_DEFAULT_PRODUCTION_ENTRIES: Optional[ProductionEntries] = None

# {(frozenset(gate_node_ids_held), civilization_id): (production_entries_object, SolvedPrices)}
# The production_entries object is held here, alongside the result, purely
# so a lookup can confirm identity with `is` before trusting a hit - the
# same id()-recycling guard `sim/engine/data.py`'s own `descendants()` uses,
# for the same reason (CLAUDE.md section 6, Complaints/27). civilization_id
# joined the key alongside the gate-node set for the reason RENT NEEDS A
# CIVILIZATION in the module docstring gives: land rent depends on which
# civilization's own territory is being priced, and two civilizations can
# hold an identical gate-node set while holding entirely different regions.
_SOLVE_CACHE: Dict[Tuple[FrozenSet[str], str], Tuple[ProductionEntries, SolvedPrices]] = {}


def _default_production_entries() -> ProductionEntries:
    global _DEFAULT_PRODUCTION_ENTRIES
    if _DEFAULT_PRODUCTION_ENTRIES is None:
        entries, duplicates = load_production()
        if duplicates:
            # validate_production.py is supposed to make this state
            # unreachable in committed data; refusing loudly here rather
            # than silently dropping one author's work is the same choice
            # solve_prices.py's own main() makes when it finds duplicates.
            raise ValueError(
                "data/production/ has duplicate material keys, which "
                "validate_production.py should never let through: %s"
                % "; ".join(duplicates))
        _DEFAULT_PRODUCTION_ENTRIES = entries
    return _DEFAULT_PRODUCTION_ENTRIES


def reset_caches_for_tests() -> None:
    """Clear both module-level caches.

    Only tests should call this: it exists because several tests build
    their own small, synthetic `production_entries` and need a clean cache
    between them, and because a real engine process never wants to see
    `data/production/` change mid-run (see WHAT INVALIDATES THE CACHE in the
    module docstring) so nothing else has a reason to call it.
    """
    global _DEFAULT_PRODUCTION_ENTRIES
    _DEFAULT_PRODUCTION_ENTRIES = None
    _SOLVE_CACHE.clear()


def all_gate_nodes(production_entries: Optional[ProductionEntries] = None) -> FrozenSet[str]:
    """Every distinct tech-tree node id that gates at least one technique.

    A technique's `requires_node` is a gate only when it names an actual
    node: `requires_node: null` means available to everyone (not a gate -
    nothing to hold) and a missing `requires_node` means nobody has
    classified the entry yet (also not a gate - see
    `solve_prices.techniques_available_to`, which treats both the same way,
    by dropping or admitting the technique itself rather than by ever
    treating the field as a node id). `.get("requires_node")` already
    returns None for both of those cases, which is why testing "is not
    None" here is enough to keep only genuine gates.
    """
    if production_entries is None:
        production_entries = _default_production_entries()
    return frozenset(
        entry["requires_node"]
        for entry in production_entries.values()
        if entry.get("requires_node") is not None)


def solver_trade_registry(production_entries: ProductionEntries) -> Dict[str, Any]:
    """The trade registry, checked against the loaded technologies as well as recipes."""
    from .catalog import load_mod_tree_nodes, load_trade_registry
    root = os.path.dirname(os.path.dirname(HERE))
    return load_trade_registry(root, production_entries, nodes=load_mod_tree_nodes(root))


def denarii_per_labour_hour(prices_json: Dict[str, Any]) -> float:
    """Money one labour hour is worth: the wage document's coin-anchored
    conversion (see LABOUR-HOURS TO DENARII in the module docstring)."""
    return prices_json["money_per_labour_hour"]


def hours_to_denarii(price_in_labour_hours: float, prices_json: Dict[str, Any]) -> float:
    """Labour hours times the money one labour hour is worth."""
    return price_in_labour_hours * denarii_per_labour_hour(prices_json)


def _solve_to_json(production_entries: ProductionEntries,
                   gate_nodes_held: FrozenSet[str], civilization_id: str,
                   document_ratios: Dict[str, float]) -> Dict[str, Any]:
    """Run the solver for one held-gate set; the result is JSON-able."""
    # `gate_nodes_held` is exactly the right thing to hand
    # `techniques_available_to` as `reached_nodes`: every `requires_node` it
    # will ever check membership for is, by `all_gate_nodes`'s own
    # construction, a gate node, so restricting the membership set to the
    # gate nodes actually held changes no answer - see CACHE KEY above.
    available_entries, _unreached, _unclassified = \
        solve_prices.techniques_available_to(production_entries, gate_nodes_held)
    producers_of = solve_prices.build_producers_index(available_entries)
    wage_by_trade = dict(document_ratios)
    # A trade the document does not list is paid by the same training rule
    # the labour market uses.
    registry = solver_trade_registry(production_entries)
    training_years = wage_provider.training_years_by_trade(registry)
    for trade in registry:
        wage_by_trade.setdefault(trade, wages.training_premium(
            training_years[trade], wage_provider.reference_discount_rate()))

    # RENT. See RENT WAS MISSING FROM THIS FILE in the module docstring:
    # `main()` in sim/solve_prices.py computes exactly these two dicts and
    # merges them the same way before ever calling `compute_resolvable_
    # materials` or `solve` - this mirrors that, rather than re-deriving a
    # third way to combine them.
    rent_hours_per_kg_by_material = solve_prices.rent_hours_per_kg_by_ore_material(
        available_entries, wage_by_trade)
    rent_hours_per_kg_by_material.update(
        solve_prices.land_rent_hours_per_hectare(
            available_entries, wage_by_trade, civilization_id=civilization_id))

    resolvable_materials = solve_prices.compute_resolvable_materials(
        available_entries, producers_of,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
    (prices_in_labour_hours, iterations_run, residual,
     chosen_recipe_by_material) = solve_prices.solve(
        available_entries, producers_of, resolvable_materials, wage_by_trade,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
        demand_anchors=joint_allocation.build_demand_anchors(civilization_id))

    return {
        "prices_in_labour_hours": prices_in_labour_hours,
        "resolvable_materials": sorted(resolvable_materials),
        "chosen_recipe_by_material": chosen_recipe_by_material,
        "converged": residual < solve_prices.CONVERGENCE_TOLERANCE,
        "iterations_run": iterations_run,
    }


def solved_prices(held_technology_ids: Iterable[str],
                  prices_json: Dict[str, Any],
                  production_entries: Optional[ProductionEntries] = None,
                  civilization_id: Optional[str] = None) -> SolvedPrices:
    """A `SolvedPrices` for this held-technology set, solving on a cache
    miss and returning the cached vector on a hit. See CACHE KEY in the
    module docstring: the cache is keyed on the intersection of
    `held_technology_ids` with `all_gate_nodes`, together with
    `civilization_id`, not on the full held-technology set, which is what
    keeps a whole game's worth of calls to a bound few dozen solves.

    `civilization_id` decides whose territory `land_rent_hours_per_hectare`
    prices (see RENT NEEDS A CIVILIZATION in the module docstring); it
    defaults to `None`, which resolves to `solve_prices.
    DEFAULT_LAND_CIVILIZATION` (Rome), matching what the CLI does when
    `--civ` is omitted. Passing `held_technology_ids` from a civilization's
    `starting_techs` without ALSO passing that civilization's own id here
    would silently price its land as Rome's - the parameter is separate
    from `held_technology_ids` on purpose, so a caller cannot get this
    right by accident and cannot get it wrong without a value showing up
    somewhere to say so.
    """
    if production_entries is None:
        production_entries = _default_production_entries()
    civilization_id = civilization_id or solve_prices.DEFAULT_LAND_CIVILIZATION

    gate_nodes_held = frozenset(all_gate_nodes(production_entries)
                                & set(held_technology_ids))
    document_ratios = solve_prices.wage_ratios_by_trade(prices_json)
    # Wages move with the labour market, so the cache is keyed on them too.
    cache_key = (gate_nodes_held, civilization_id,
                 tuple(sorted(document_ratios.items())))

    cached = _SOLVE_CACHE.get(cache_key)
    if cached is not None and cached[0] is production_entries:
        return cached[1]

    def compute() -> Dict[str, Any]:
        return _solve_to_json(production_entries, gate_nodes_held,
                              civilization_id, document_ratios)
    if production_entries is _DEFAULT_PRODUCTION_ENTRIES:
        # Only the committed catalogue is persisted; synthetic catalogues are not.
        try:
            key = solve_cache.solve_key({
                "production": production_entries, "gates": sorted(gate_nodes_held),
                "civilization": civilization_id, "wage_ratios": document_ratios})
        except OSError:
            key = None  # an input file cannot be read: solve without the cache
        stored = (solve_cache.cached_json(key, compute) if key
                  else json.loads(json.dumps(compute())))
    else:
        stored = json.loads(json.dumps(compute()))
    result = SolvedPrices(
        prices_in_labour_hours=stored["prices_in_labour_hours"],
        resolvable_materials=set(stored["resolvable_materials"]),
        chosen_recipe_by_material=stored["chosen_recipe_by_material"],
        converged=stored["converged"],
        iterations_run=stored["iterations_run"],
        gate_nodes_held=gate_nodes_held,
        civilization_id=civilization_id)
    _SOLVE_CACHE[cache_key] = (production_entries, result)
    return result


def priced_goods_table(held_technology_ids: Iterable[str],
                       book_goods_denarii: Prices,
                       prices_json: Dict[str, Any],
                       production_entries: Optional[ProductionEntries] = None,
                       civilization_id: Optional[str] = None
                       ) -> Tuple[Prices, Provenance]:
    """(goods_denarii, provenance) - the book's own goods table with a
    solved price substituted wherever the solver can produce one for a
    material this held-technology set already prices in the book, and
    provenance is the burndown THE GOAL asks to make measurable, and it has
    THREE states rather than two, because a straight solved/book split
    measures the wrong thing:

      "solved"     - a computed price replaced the book's.
      "gated"      - something DOES make this material, and nothing this
                     era can run. Not a gap. A Roman cannot smelt aluminium
                     and no amount of authoring will change that.
      "no_recipe"  - nothing anywhere makes it. The real gap, and the only
                     one of the three that authoring can close.

    The distinction matters because an undifferentiated solved/book count
    for the default civilisation reads as 85 missing recipes, when sixty-eight of those
    have recipes and are correctly gated out by era, leaving a real gap of
    nine - and five of THOSE want deleting rather than filling (two are
    people rather than materials, two are dead keys nothing consumes any
    more, one is a stale duplicate). Quoting the undifferentiated number
    overstates the remaining work by roughly an order of magnitude.

    A caveat this function cannot fix, recorded where the next reader will
    meet it: a "gated" material still falls back to the BOOK price, which
    is its own modelling question. If Rome cannot make aluminium, the
    honest answer is probably that Rome cannot have it at any price, or
    that it arrives at an import price - not that it costs what a modern
    author guessed. That is a decision about trade and availability, not
    about this table.

    Resolvable materials absent from the book are deliberately added here;
    minor joint byproducts retain the solver's existing treatment.
    `civilization_id` is passed straight through to
    `solved_prices` - see RENT NEEDS A CIVILIZATION in the module docstring
    for why land rent needs it and what happens if it is left out.
    """
    solved = solved_prices(held_technology_ids, prices_json,
                           production_entries=production_entries,
                           civilization_id=civilization_id)

    # Everything any recipe anywhere can make, ignoring era entirely. This
    # is what separates "nothing makes it" from "nothing HERE makes it".
    all_entries = (production_entries if production_entries is not None
                   else _default_production_entries())
    makeable_by_someone = set(all_entries)
    for entry in all_entries.values():
        makeable_by_someone.update((entry.get("outputs") or {}))

    goods_denarii = money_units.convert_book_table(
        book_goods_denarii, prices_json["money_per_labour_hour"])
    provenance = {}
    for material in book_goods_denarii:
        provenance[material] = ("gated" if material in makeable_by_someone
                                else "no_recipe")
    for material in solved.resolvable_materials:
        goods_denarii[material] = hours_to_denarii(
            solved.prices_in_labour_hours[material], prices_json)
        provenance[material] = "solved"
    return goods_denarii, provenance
