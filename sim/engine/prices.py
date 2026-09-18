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

CACHE KEY: THE SET OF GATE NODES HELD, NOT THE FULL TECHNOLOGY SET.
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

LABOUR-HOURS TO DENARII, AND WHY THIS DIRECTION IS THE RIGHT ONE.
`sim/solve_prices.py` prices everything in labour-hours - one hour of
`labourer`, its numeraire, by construction equals 1.0 - because that is a
number a recipe graph can actually produce: relative amounts of unskilled
effort. `data/prices.json` and every consumer of `goods` in
`sim/engine/economy.py` are in denarii. `solve_prices.py --compare` already
has to cross this exact boundary to judge the solver against the book, and
it does it by dividing the book's denarii figure by the labourer wage rate
(also denarii per hour) to get BOTH sides into hours before comparing them:

    book_hours = book_price_denarii / wage_rates_denarii_per_hour["labourer"]

This module needs the other direction - a solved number in hours has to
become a denarii figure `economy.py` can subtract from a household's purse -
which is the same equation solved for the term that direction leaves alone:

    price_denarii = price_hours * wage_rates_denarii_per_hour["labourer"]

Multiplying (rather than dividing again, or using some other rate) is the
only conversion consistent with `--compare`'s own arithmetic: hours is
denarii divided by the labourer rate, so getting back to denarii is
multiplying by that same rate, not a different one and not its reciprocal
taken twice. Getting this backwards - dividing instead of multiplying, or
using a different trade's wage - would silently rescale every solved price
by the square of the labourer wage or by an unrelated trade's ratio, exactly
the mistake this module's own docstring was told to be explicit about.
`denarii_per_labour_hour` below is the one place that rate is read, so there
is exactly one line to check rather than one per caller.

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
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))              # sim/engine
SIMDIR = os.path.dirname(HERE)                                  # sim
if SIMDIR not in sys.path:
    # solve_prices.py and validate_production.py are siblings of this
    # package, not inside it - they are standalone tools this file is
    # reusing rather than duplicating (see the module docstring). This
    # mutates global interpreter state, which is exactly why it happens here
    # rather than at import time of sim/engine/data.py: it only runs the
    # moment something actually asks this module for a price, so a caller
    # that never opts into solved prices never pays for it or risks it.
    sys.path.insert(0, SIMDIR)

import solve_prices                                             # noqa: E402
from validate_production import load_production                 # noqa: E402


class SolvedPrices(object):
    """One gated solve's result, cached and handed back verbatim on a hit.

    `prices_in_labour_hours` and `chosen_recipe_by_material` are exactly
    `solve_prices.solve`'s own return values, kept in the solver's native
    unit (see LABOUR-HOURS TO DENARII in the module docstring) so a caller
    that wants the solver's own numeraire, not a converted one, still can.
    `resolvable_materials` is which materials have ANY path to a price under
    this held-technology set - the set `priced_goods_table` overlays onto
    the book, and everything outside it is where the book fallback matters.
    """
    __slots__ = ("prices_in_labour_hours", "resolvable_materials",
                "chosen_recipe_by_material", "converged", "iterations_run",
                "gate_nodes_held")

    def __init__(self, prices_in_labour_hours, resolvable_materials,
                chosen_recipe_by_material, converged, iterations_run,
                gate_nodes_held):
        self.prices_in_labour_hours = prices_in_labour_hours
        self.resolvable_materials = resolvable_materials
        self.chosen_recipe_by_material = chosen_recipe_by_material
        self.converged = converged
        self.iterations_run = iterations_run
        self.gate_nodes_held = gate_nodes_held


# `data/production/` is committed data: it does not change while a game is
# running, so it only ever needs to be read and merged once per process, and
# every caller that does not hand in its own `production_entries` (real
# engine use, always; only tests with synthetic data pass their own) shares
# this ONE object. Sharing the object, not just the data, is what lets the
# cache below use `is` rather than re-hashing the whole dict on every lookup
# - see WHAT INVALIDATES THE CACHE above.
_DEFAULT_PRODUCTION_ENTRIES = None

# {frozenset(gate_node_ids_held): (production_entries_object, SolvedPrices)}
# The production_entries object is held here, alongside the result, purely
# so a lookup can confirm identity with `is` before trusting a hit - the
# same id()-recycling guard `sim/engine/data.py`'s own `descendants()` uses,
# for the same reason (CLAUDE.md section 6, Complaints/27).
_SOLVE_CACHE = {}


def _default_production_entries():
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


def reset_caches_for_tests():
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


def all_gate_nodes(production_entries=None):
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


def denarii_per_labour_hour(prices_json):
    """Denarii one hour of unskilled (`labourer`) labour is worth, read from
    `prices.json`'s own wage table - the one number LABOUR-HOURS TO DENARII
    in the module docstring needs, read in exactly one place so there is
    exactly one place to check it is read correctly."""
    return (prices_json["wage_rates_denarii_per_hour"]
            [solve_prices.NUMERAIRE_TRADE]["rate"])


def hours_to_denarii(price_in_labour_hours, prices_json):
    """`price_hours * labourer_denarii_per_hour` - see LABOUR-HOURS TO
    DENARII in the module docstring for why multiplication, not division, is
    the correct direction and why the labourer rate specifically is the
    right rate to multiply by."""
    return price_in_labour_hours * denarii_per_labour_hour(prices_json)


def solved_prices(held_technology_ids, prices_json, production_entries=None):
    """A `SolvedPrices` for this held-technology set, solving on a cache
    miss and returning the cached vector on a hit. See CACHE KEY in the
    module docstring: the cache is keyed on the intersection of
    `held_technology_ids` with `all_gate_nodes`, not on the full set, which
    is what keeps a whole game's worth of calls to a bound few dozen solves.
    """
    if production_entries is None:
        production_entries = _default_production_entries()

    gate_nodes_held = frozenset(all_gate_nodes(production_entries)
                                & set(held_technology_ids))

    cached = _SOLVE_CACHE.get(gate_nodes_held)
    if cached is not None and cached[0] is production_entries:
        return cached[1]

    # `gate_nodes_held` is exactly the right thing to hand
    # `techniques_available_to` as `reached_nodes`: every `requires_node` it
    # will ever check membership for is, by `all_gate_nodes`'s own
    # construction, a gate node, so restricting the membership set to the
    # gate nodes actually held changes no answer - see CACHE KEY above.
    available_entries, _unreached, _unclassified = \
        solve_prices.techniques_available_to(production_entries, gate_nodes_held)
    producers_of = solve_prices.build_producers_index(available_entries)
    resolvable_materials = solve_prices.compute_resolvable_materials(
        available_entries, producers_of)
    wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
    (prices_in_labour_hours, iterations_run, residual,
     chosen_recipe_by_material) = solve_prices.solve(
        available_entries, producers_of, resolvable_materials, wage_by_trade)

    result = SolvedPrices(
        prices_in_labour_hours=prices_in_labour_hours,
        resolvable_materials=resolvable_materials,
        chosen_recipe_by_material=chosen_recipe_by_material,
        converged=residual < solve_prices.CONVERGENCE_TOLERANCE,
        iterations_run=iterations_run,
        gate_nodes_held=gate_nodes_held)
    _SOLVE_CACHE[gate_nodes_held] = (production_entries, result)
    return result


def priced_goods_table(held_technology_ids, book_goods_denarii, prices_json,
                       production_entries=None):
    """(goods_denarii, provenance) - the book's own goods table with a
    solved price substituted wherever the solver can produce one for a
    material this held-technology set already prices in the book, and
    provenance is {material: "solved" | "book"} for every material the book
    prices, which is the burndown THE GOAL asks to make measurable: as more
    of `data/production/` gets `requires_node` labels, more materials
    resolve, and the "book" count in this dict falls. See the module
    docstring for what this deliberately does not do (add new materials the
    book never had, or treat a minor joint byproduct any differently).
    """
    solved = solved_prices(held_technology_ids, prices_json,
                           production_entries=production_entries)
    rate = denarii_per_labour_hour(prices_json)

    goods_denarii = dict(book_goods_denarii)
    provenance = dict.fromkeys(book_goods_denarii, "book")
    for material in solved.resolvable_materials:
        if material not in book_goods_denarii:
            continue
        goods_denarii[material] = hours_to_denarii(
            solved.prices_in_labour_hours[material], prices_json)
        provenance[material] = "solved"
    return goods_denarii, provenance
