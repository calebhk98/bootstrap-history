"""Ask the price solver for a price.

Prices are calculated from recipes, land rent, wages and transport by
`sim/prices/solve_prices_core.py` (the design is written up in the docstring of `sim/prices/solve_prices.py`, which holds no code), gated to what a civilization has reached
(Complaints/38). This module is the engine's one call into the solver. It is
thin: it imports the solver rather than re-implementing it. There is no price
book; a material nothing can make has no price.

THE WAGE ARGUMENT (`prices_json` below) is a wage document in the
shape the solver reads, built by `sim.labour.wages.WageSchedule.document()`, so the solver and
payroll read one wage vector. Its unskilled-trade rate is the money value of one
labour hour.

THE INTERFACE. One function matters to a caller:

    solved_prices(held_technology_ids, prices_json)   -> a SolvedPrices

and one function does the actual replacement `data.py` wants:

    priced_goods_table(held_technology_ids, prices_json)
        -> (goods_in_money, provenance)

`goods_in_money` is a plain {material: price} dict in the wage document's
coin. `provenance` is {material: "solved" | "gated"}: "solved" is priced under
the held technologies, "gated" at a technique not held but within reach, with
held-technique inputs (see priced_goods_table). A material neither makes is
absent: a price needs a seller, and a trading partner's offer is priced by the
goods market, not here.

CACHE KEY: THE SET OF GATE NODES HELD, PLUS THE CIVILIZATION FOR LAND RENT.
See RENT NEEDS A CIVILIZATION below for why a bare gate-node set stopped
being enough. The gate-node reasoning that follows is otherwise unchanged.
A gated solve is costly, but only a small share of the tree's nodes is ever named by a
`requires_node` anywhere in `data/production/` - a GATE, in this file's
terms (the share is `len(all_gate_nodes()) / len(tree nodes)`). Every other node a civilization holds cannot possibly change which
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
`solve_prices_core.techniques_available_to` for why those two are not gates
either), and `solved_prices` below intersects it with whatever the caller
passes as `held_technology_ids` before ever touching the cache. A caller
may pass its FULL technology set without pre-filtering; the exact same
gate-only key comes out the far side. This is also, incidentally, exactly
the right input to hand `solve_prices_core.techniques_available_to` for the
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
below) and because prices computed here are never part of a save: a solve is
kept in this process and in the solve cache on disk (`sim/prices/solve_cache.py`, keyed on the data and
source it was computed from), and a miss re-solves from the same data.

The one hazard this project has actually been burned by - `id()` recycling a
freed object's address into a live cache entry, see CLAUDE.md section 6 and
Complaints/27 - is guarded the same way `sim/engine/data.py`'s own
`descendants()` guards it: the cache entry holds the `production_entries`
object itself, not just its `id()`, and a lookup confirms the hit with `is`
before trusting it. A caller that hands in a DIFFERENT `production_entries`
object (a test building synthetic data, mainly) can never collide with a
real one that happens to reuse the same gate-node ids.

LABOUR-HOURS TO DENARII. `sim/prices/solve_prices_core.py` prices everything in
labour-hours - one hour of the unskilled trade, its numeraire (`solve_prices_core.numeraire_trade`), equals 1.0 - because a
recipe graph can produce relative amounts of unskilled effort. Money enters
only here, at the edge: the wage document carries `money_per_labour_hour`,
which `sim.workforce.wage_schedule.build_schedule` derives from the
civilisation's coin (the coin material's solved labour hours per kg times the
coin's mass), so a price in money is its labour hours times that rate.
`denarii_per_labour_hour` is the one place the rate is read.

WHAT THIS DOES NOT HANDLE, LEFT FOR THE NEXT STEP. the solver
prices MINOR JOINT BYPRODUCTS (platinum, coal tar and the like) by mass where no reference price
exists: lower bounds rather than independent prices (`sim/prices/joint_allocation.py`). This file reports
them as "solved" rather than a third category, because a third provenance state is a design decision
of its own; `SolvedPrices.chosen_recipe_by_material` is exposed for a caller that wants to recover the
distinction.

RENT IS AN ARGUMENT (Complaints/507). `solved_prices` takes
`rent_hours_per_kg_by_material` and charges exactly that (empty: none). A
caller with none takes the opening's stand-in from `sim/prices/rent_standin.py`,
computed once per solve and threaded through `compute_resolvable_materials` and
`solve`; it is the only place a demanded quantity still reaches a price.

RENT NEEDS A CIVILIZATION, AND SO DOES THE CACHE KEY. The land stand-in is
genuinely per-civilization - `sim/world/land.py` prices the margin of
cultivation over a CIVILIZATION'S OWN HELD REGIONS, and two civilizations can
hold the exact same gate-node set while holding completely different
territory. A cache key of `gate_nodes_held` alone cannot distinguish them, so
`solved_prices` and `priced_goods_table` take an explicit `civilization_id`
parameter and fold it into the cache key alongside `gate_nodes_held`, together
with the rent a caller supplied. It defaults to `None`, which resolves to the
reference civilisation (`engine_seam.load_civ(None)`) - the same default the CLI uses when `--civ` is omitted.
"""
import contextlib
import functools
import json
import math
import os
import sys
from typing import Any, Callable, Dict, FrozenSet, Iterable, Iterator, List, Mapping, Optional, Set, Tuple

# TYPE ALIASES.
#
# Prices: a {material: price} table, in EITHER unit this module handles -
# labour-hours (the solver's own numeraire) or denarii
# (the economy module's) - see LABOUR-HOURS TO DENARII in the module
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
# through to `solve_prices_core.py` and `validate_production.py` (both
# unannotated, out of this task's scope) without reading their fields
# itself - the one exception, `entry.get("requires_node")` /
# `entry.get("outputs")` in `all_gate_nodes`/`priced_goods_table`, reads
# exactly the two fields every entry shares regardless of process shape.
ProductionEntries = Dict[str, Any]

# {material: "solved" | "gated"} - see priced_goods_table's own docstring
# for what the two strings mean. A plain Dict[str, str]: the KEYS are
# material ids, open and data-driven.
Provenance = Dict[str, str]

HERE = os.path.dirname(os.path.abspath(__file__))              # sim/prices
SIMDIR = os.path.dirname(HERE)                                  # sim
REPO_ROOT = os.path.dirname(SIMDIR)                             # repo root
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sim.prices import disposal_cost, rent_standin, solve_prices_reach, solve_prices_core  # noqa: E402
from sim.prices.engine_seam import load_production             # noqa: E402
from sim.prices import engine_seam, solve_cache             # noqa: E402
from sim.constants import declare                                # noqa: E402
from sim.geography.api import crop_climate, tiles_held     # noqa: E402


class SolvedPrices(object):
    """One gated solve's result, cached and handed back verbatim on a hit.

    `prices_in_labour_hours` and `chosen_recipe_by_material` are exactly
    `solve_prices_core.solve`'s own return values, kept in the solver's native
    unit (see LABOUR-HOURS TO DENARII in the module docstring) so a caller
    that wants the solver's own numeraire, not a converted one, still can.
    `resolvable_materials` is which materials have ANY path to a price under
    this held-technology set - the set `priced_goods_table` prices
    directly; everything outside it is priced as "gated" or not at all.
    `civilization_id` is the civilization `land_rent_hours_per_hectare` was
    solved against (see RENT NEEDS A CIVILIZATION in the module docstring) -
    kept on the result so a caller inspecting a cache hit can see which
    territory its land rent came from, rather than having to trust the
    cache key blindly.
    """
    __slots__ = ("prices_in_labour_hours", "resolvable_materials",
                "chosen_recipe_by_material", "converged", "iterations_run",
                "gate_nodes_held", "civilization_id", "interest_rate")

    def __init__(self, prices_in_labour_hours: Prices,
                resolvable_materials: Set[str],
                chosen_recipe_by_material: Dict[str, Any],
                converged: bool, iterations_run: int,
                gate_nodes_held: FrozenSet[str], civilization_id: str,
                interest_rate: float = 0.0) -> None:
        self.prices_in_labour_hours = prices_in_labour_hours
        self.resolvable_materials = resolvable_materials
        self.chosen_recipe_by_material = chosen_recipe_by_material
        self.converged = converged
        self.iterations_run = iterations_run
        self.gate_nodes_held = gate_nodes_held
        self.civilization_id = civilization_id
        self.interest_rate = interest_rate


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
_SOLVE_CACHE: Dict[Tuple[Any, ...], Tuple[ProductionEntries, SolvedPrices]] = {}
_TREE_NODES: Dict[str, Any] = {}
_TREE_NODES_BY_DIRECTORY: Dict[str, Dict[str, Any]] = {}


def _default_production_entries() -> ProductionEntries:
    global _DEFAULT_PRODUCTION_ENTRIES
    if _DEFAULT_PRODUCTION_ENTRIES is None:
        entries, _no_duplicates = load_production()    # the one canonical catalogue: a duplicate key is not representable
        _DEFAULT_PRODUCTION_ENTRIES = entries
    return _DEFAULT_PRODUCTION_ENTRIES


def reset_caches_for_tests() -> None:
    """Clear this module's caches, the default production entries and the numeraires.

    Only tests should call this: it exists because several tests build
    their own small, synthetic `production_entries` and need a clean cache
    between them. The caches of `making_cost` and `energy_prices` hold the entries object they were built
    from and confirm a hit with `is`, so replacing the default entries here makes them miss.
    """
    global _DEFAULT_PRODUCTION_ENTRIES
    _DEFAULT_PRODUCTION_ENTRIES = None
    _SOLVE_CACHE.clear()
    _TREE_NODES.clear()
    _TREE_NODES_BY_DIRECTORY.clear()
    solve_prices_core.forget_numeraires()
    rent_standin.forget_land_rents()


def all_gate_nodes(production_entries: Optional[ProductionEntries] = None) -> FrozenSet[str]:
    """Every distinct tech-tree node id that gates at least one technique.

    A technique's `requires_node` is a gate only when it names an actual
    node: `requires_node: null` means available to everyone (not a gate -
    nothing to hold) and a missing `requires_node` means nobody has
    classified the entry yet (also not a gate - see
    `solve_prices_core.techniques_available_to`, which treats both the same way,
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


def denarii_per_labour_hour(prices_json: Dict[str, Any]) -> float:
    """Money one labour hour is worth: the wage document's coin-anchored
    conversion (see LABOUR-HOURS TO DENARII in the module docstring)."""
    return prices_json["money_per_labour_hour"]


def hours_to_denarii(price_in_labour_hours: float, prices_json: Dict[str, Any]) -> float:
    """Labour hours times the money one labour hour is worth."""
    return price_in_labour_hours * denarii_per_labour_hour(prices_json)


def trades_used(production_entries: ProductionEntries) -> List[str]:
    """Every trade a production entry works or builds its plant with, sorted."""
    trades = set()
    for entry in production_entries.values():
        trades.update(entry.get("labour_hours") or {})
        for plant in entry.get("capital") or ():
            trades.update(plant.get("build_labour_hours") or {})
    return sorted(trades)


def solver_wage_ratios(production_entries: ProductionEntries,
                       document_ratios: Dict[str, float]) -> Dict[str, float]:
    """Wage of every trade the entries use, in labour hours an hour: the document's. A trade the entries
    use that the document does not list is an error; the wage document owns every wage, the solver invents none."""
    missing = sorted(trade for trade in trades_used(production_entries) if trade not in document_ratios)
    if missing:
        raise ValueError("the wage document lists no wage for the trades %s; every trade the solver "
                         "prices needs one" % missing)
    return dict(document_ratios)


def default_production_entries(mods_dir: Optional[str] = None) -> ProductionEntries:
    """The production catalogue of `mods_dir`, read once per directory; the committed one when none is named."""
    if mods_dir is None:
        return _default_production_entries()
    return engine_seam.load_production(mods_dir)[0]


def waste_dump_minimum_distance(civilization: Optional[Mapping[str, Any]]) -> float:
    """The nearest a state lets waste be tipped to settlement and water, in km; none unless the record says."""
    if civilization is None:
        return 0.0
    return float(civilization.get("waste_dump_minimum_distance_kilometres") or 0.0)


def territory_fingerprint(civilization: Optional[Mapping[str, Any]]) -> Optional[Tuple[Any, ...]]:
    """What of a held civilisation the solve reads beyond its id: its people, its ground, its staple (the land rent
    stand-in prices it) and its dump rule."""
    if civilization is None:
        return None
    return (civilization.get("population"), tuple(tiles_held(civilization)), civilization.get("staple"),
            waste_dump_minimum_distance(civilization))


# Cleared area changes every year by a little; solves are keyed on bands of this relative width.
FARMED_AREA_BAND_RATIO = 1.05

# The market rate moves with every round of lending; a solve is keyed on the band holding it, so the
# capital charge is re-solved only when the rate has moved a band.
INTEREST_RATE_BAND = declare(
    "INTEREST_RATE_BAND", 0.01, kind="temporary_heuristic", unit="yearly interest rate (a share, not percent)",
    source=None, confidence="D",
    why="Width of the band the live market rate is rounded to before the solver charges plant and "
        "stock; stands in for re-solving at every move of the rate, which the solve's cost forbids.")


def band_interest_rate(rate: float, starting_rate: float) -> float:
    """The live market rate rounded to a band measured from the starting rate (so the starting rate is its own band)."""
    steps = round((rate - starting_rate) / INTEREST_RATE_BAND)
    return max(0.0, starting_rate + steps * INTEREST_RATE_BAND)


def band_farmed_hectares(farmed_hectares: Optional[float]) -> Optional[float]:
    """The centre of the geometric band holding the farmed area, so rent is re-solved only when clearing moves a band."""
    if farmed_hectares is None or farmed_hectares <= 0.0:
        return None
    steps = round(math.log(farmed_hectares) / math.log(FARMED_AREA_BAND_RATIO))
    return FARMED_AREA_BAND_RATIO ** steps


# The engine's solves stop at this largest relative price change per round, far looser than the solver's own
# tolerance (tighter than any price the game shows or any decision it takes).
ENGINE_SOLVE_TOLERANCE = declare(
    "ENGINE_SOLVE_TOLERANCE", 1e-5, kind="temporary_heuristic", unit="largest relative price change in a round",
    source=None, confidence="D",
    why="Stops the in-game price solve once prices settle to the precision play can see; the solver's "
        "own tolerance runs many more rounds for digits nothing reads.")


def civilization_record(civilization: Optional[Mapping[str, Any]], civilization_id: Optional[str] = None,
                        mods_dir: Optional[str] = None) -> Mapping[str, Any]:
    """The civilisation record every solve reads: the one the caller holds, else the mod-applied record of
    `civilization_id` (the reference civilisation's when none). An id that names no record is an error."""
    if civilization is not None:
        return civilization
    return engine_seam.load_civ(civilization_id, mods_dir)


def _solve_to_json(production_entries: ProductionEntries,
                   gate_nodes_held: FrozenSet[str],
                   document_ratios: Dict[str, float],
                   civilization: Mapping[str, Any],
                   admitted_entry_keys: FrozenSet[str] = frozenset(),
                   interest_rate: float = 0.0,
                   farmed_hectares: Optional[float] = None,
                   in_game: bool = False,
                   rent_hours_per_kg_by_material: Optional[Mapping[str, float]] = None) -> Dict[str, Any]:
    """Run the solver for one held-gate set; the result is JSON-able. `in_game` stops at ENGINE_SOLVE_TOLERANCE;
    otherwise the solve runs to the solver's own tolerance. The rent charged is
    `rent_hours_per_kg_by_material` when given (none at all if empty), else the opening's stand-in."""
    # `gate_nodes_held` is exactly the right thing to hand
    # `techniques_available_to` as `reached_nodes`: every `requires_node` it
    # will ever check membership for is, by `all_gate_nodes`'s own
    # construction, a gate node, so restricting the membership set to the
    # gate nodes actually held changes no answer - see CACHE KEY above.
    available_entries, _unreached, _unclassified = \
        solve_prices_core.techniques_available_to(production_entries, gate_nodes_held)
    for entry_key in admitted_entry_keys:
        available_entries[entry_key] = production_entries[entry_key]
    producers_of = solve_prices_core.build_producers_index(available_entries)
    wage_by_trade = solver_wage_ratios(production_entries, document_ratios)

    if rent_hours_per_kg_by_material is None:
        rent_hours_per_kg_by_material = rent_standin.stand_in_rent(
            available_entries, wage_by_trade, civilization, farmed_hectares=farmed_hectares)
    else:
        rent_hours_per_kg_by_material = dict(rent_hours_per_kg_by_material)

    resolvable_materials = solve_prices_core.compute_resolvable_materials(
        available_entries, producers_of,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
    (prices_in_labour_hours, iterations_run, residual,
     chosen_recipe_by_material, resolvable_materials) = solve_prices_reach.solve_priced_materials(
        available_entries, producers_of, resolvable_materials, wage_by_trade,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
        interest_rate=interest_rate,
        dump_minimum_distance_kilometres=waste_dump_minimum_distance(civilization),
        **({"tolerance": ENGINE_SOLVE_TOLERANCE} if in_game else {}))

    return {
        "prices_in_labour_hours": prices_in_labour_hours,
        "resolvable_materials": sorted(resolvable_materials),
        "chosen_recipe_by_material": chosen_recipe_by_material,
        "converged": residual < (ENGINE_SOLVE_TOLERANCE if in_game else solve_prices_core.CONVERGENCE_TOLERANCE),
        "iterations_run": iterations_run,
    }


def solved_prices(held_technology_ids: Iterable[str],
                  prices_json: Dict[str, Any],
                  production_entries: Optional[ProductionEntries] = None,
                  civilization_id: Optional[str] = None,
                  admitted_entry_keys: FrozenSet[str] = frozenset(),
                  interest_rate: Optional[float] = None,
                  civilization: Optional[Mapping[str, Any]] = None,
                  farmed_hectares: Optional[float] = None,
                  rent_hours_per_kg_by_material: Optional[Mapping[str, float]] = None,
                  unskilled_trade: Optional[str] = None) -> SolvedPrices:
    """A `SolvedPrices` for this held-technology set, solving on a cache
    miss and returning the cached vector on a hit. See CACHE KEY in the
    module docstring: the cache is keyed on the intersection of
    `held_technology_ids` with `all_gate_nodes`, together with
    `civilization_id`, not on the full held-technology set, which is what
    keeps a whole game's worth of calls to a bound few dozen solves.

    `civilization_id` decides whose territory the land rent stand-in
    prices (see RENT NEEDS A CIVILIZATION in the module docstring); it
    defaults to `None`, which resolves to the reference
    civilisation (`engine_seam.load_civ(None)`), matching what the CLI does when
    `--civ` is omitted. Passing `held_technology_ids` from a civilization's
    `starting_techs` without ALSO passing that civilization's own id here
    would silently price its land as the default civilisation's - the parameter is separate
    from `held_technology_ids` on purpose, so a caller cannot get this
    right by accident and cannot get it wrong without a value showing up
    somewhere to say so.

    `interest_rate` is the yearly rate each plant's build bill must earn over its depreciation (the
    market rate); `None` is the civilisation's starting rate, which is the market rate until a market
    has met. It is part of the cache key.

    `civilization`, when the caller holds the civilisation (a record that may exist only in memory),
    supplies its id, starting rate, population and home regions instead of a file read by id; the
    territory is part of the cache key, so a variant that keeps a file's id is solved as itself.

    `farmed_hectares` is the area the society has cleared; rent is read from the best ground that area
    covers. It is banded (`band_farmed_hectares`) in the cache key; `None` sizes demand to the population.

    `rent_hours_per_kg_by_material` is the rent the caller charges, in hours per unit of each extracted
    good and per hectare of land; empty charges none. `None` takes the opening's stand-in
    (`sim/prices/rent_standin.py`, the only place a demanded quantity still enters a price).
    """
    return solved_prices_at_wages(
        held_technology_ids, solve_prices_core.wage_ratios_by_trade(prices_json, unskilled_trade), production_entries, civilization_id,
        admitted_entry_keys, interest_rate, civilization, farmed_hectares, rent_hours_per_kg_by_material)


# one list per open `recording_solves` block
_solve_recordings: List[List[Tuple[tuple, Dict[str, Any]]]] = []


def _noting_calls(function: Callable) -> Callable:
    """`function`, noting each call's arguments in every open `recording_solves` block."""
    @functools.wraps(function)
    def noting(*arguments, **keywords):
        for calls in _solve_recordings:
            calls.append((arguments, keywords))
        return function(*arguments, **keywords)
    return noting


@contextlib.contextmanager
def recording_solves() -> Iterator[List[Tuple[tuple, Dict[str, Any]]]]:
    """Within the block, the (arguments, keywords) of every `solved_prices_at_wages` call, in order."""
    calls: List[Tuple[tuple, Dict[str, Any]]] = []
    _solve_recordings.append(calls)
    try:
        yield calls
    finally:
        _solve_recordings.remove(calls)


@_noting_calls
def solved_prices_at_wages(held_technology_ids: Iterable[str],
                           document_ratios: Dict[str, float],
                           production_entries: Optional[ProductionEntries] = None,
                           civilization_id: Optional[str] = None,
                           admitted_entry_keys: FrozenSet[str] = frozenset(),
                           interest_rate: Optional[float] = None,
                           civilization: Optional[Mapping[str, Any]] = None,
                           farmed_hectares: Optional[float] = None,
                           rent_hours_per_kg_by_material: Optional[Mapping[str, float]] = None) -> SolvedPrices:
    """`solved_prices` for wages given as hours of unskilled labour an hour of each trade is worth."""
    if production_entries is None:
        production_entries = _default_production_entries()
    civilization = civilization_record(civilization, civilization_id)
    civilization_id = civilization["id"]
    starting_rate = float(civilization["starting_interest_rate"])
    if interest_rate is None:
        interest_rate = starting_rate
    territory = territory_fingerprint(civilization)
    farmed_hectares = band_farmed_hectares(farmed_hectares)

    gate_nodes_held = frozenset(all_gate_nodes(production_entries)
                                & set(held_technology_ids))
    rent_key = None if rent_hours_per_kg_by_material is None else tuple(sorted(rent_hours_per_kg_by_material.items()))
    # Wages move with the labour market, so the cache is keyed on them too.
    cache_key = (gate_nodes_held, civilization_id, tuple(sorted(document_ratios.items())), admitted_entry_keys,
                 interest_rate, territory, farmed_hectares, rent_key)

    cached = _SOLVE_CACHE.get(cache_key)
    if cached is not None and cached[0] is production_entries:
        return cached[1]

    in_game = production_entries is _DEFAULT_PRODUCTION_ENTRIES

    def compute() -> Dict[str, Any]:
        return _solve_to_json(production_entries, gate_nodes_held, document_ratios, civilization,
                              admitted_entry_keys, interest_rate, farmed_hectares, in_game,
                              rent_hours_per_kg_by_material)
    if production_entries is _DEFAULT_PRODUCTION_ENTRIES:
        # Only the committed catalogue is persisted; synthetic catalogues are not.
        try:
            key = solve_cache.solve_key({
                "production": production_entries, "gates": sorted(gate_nodes_held),
                "civilization": civilization_id, "wage_ratios": document_ratios,
                "admitted_entries": sorted(admitted_entry_keys), "interest_rate": interest_rate,
                "territory": territory, "farmed_hectares": farmed_hectares, "rent": rent_key},
                source_modules=_SOLVER_SOURCE)
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
        civilization_id=civilization_id, interest_rate=interest_rate)
    _SOLVE_CACHE[cache_key] = (production_entries, result)
    return result


# The solve reads only its inputs and the code this module imports, so only that source keys the cache.
_SOLVER_SOURCE = ("sim.prices.prices",)


def _tree_nodes(mods_dir: Optional[str] = None) -> Dict[str, Any]:
    """The tech tree by node id with the mods of `mods_dir` applied (the committed ones when none), read once per directory."""
    if mods_dir is not None:
        if mods_dir not in _TREE_NODES_BY_DIRECTORY:
            root = os.path.dirname(os.path.dirname(HERE))
            _TREE_NODES_BY_DIRECTORY[mods_dir] = {node["id"]: node for node in engine_seam.load_mod_tree_nodes(root, mods_dir)}
        return _TREE_NODES_BY_DIRECTORY[mods_dir]
    if _TREE_NODES.get("nodes") is None:
        root = os.path.dirname(os.path.dirname(HERE))
        _TREE_NODES["nodes"] = {node["id"]: node for node in engine_seam.load_mod_tree_nodes(root)}
    return _TREE_NODES["nodes"]


def _unheld_steps_to(node_id: str, held: Set[str], mods_dir: Optional[str] = None) -> int:
    """How many technologies not yet held stand between a society and this one, itself included."""
    nodes = _tree_nodes(mods_dir)
    if node_id not in nodes:
        return len(nodes)
    return len(_requirements_of(nodes, node_id) - held)


def _requirements_of(nodes: Dict[str, Any], node_id: str) -> FrozenSet[str]:
    """Everything a node needs, itself included; worked out once per tree, since the tree does not change."""
    cached = _TREE_NODES.setdefault("requirements", {})
    if cached.get("tree") is not nodes:
        cached.clear()
        cached["tree"] = nodes
    if node_id not in cached:
        cached[node_id] = frozenset(engine_seam.closure(nodes, node_id))
    return cached[node_id]


def production_entries_outputs(production_entries: ProductionEntries) -> Set[str]:
    return {material for entry in production_entries.values() for material in (entry.get("outputs") or {})}


# how many argument sets the in-reach memo keeps before it starts over (a game asks for a few dozen)
IN_REACH_MEMO_LIMIT = 256


def entries_in_reach(held: Set[str], held_gate_nodes: FrozenSet[str], resolvable_materials: Set[str],
                     production_entries: ProductionEntries, mods_dir: Optional[str] = None) -> FrozenSet[str]:
    """`_entries_in_reach`, remembered per argument set: a society asks again for the techniques it holds."""
    memo = _TREE_NODES.setdefault("in_reach", {})
    if memo.get("entries") is not production_entries:
        memo.clear()
        memo["entries"] = production_entries
    key = (frozenset(held), frozenset(held_gate_nodes), frozenset(resolvable_materials))
    if key not in memo:
        if len(memo) > IN_REACH_MEMO_LIMIT:
            memo.clear()
            memo["entries"] = production_entries
        memo[key] = _entries_in_reach(held, held_gate_nodes, resolvable_materials, production_entries, mods_dir)
    return memo[key]


def _entries_in_reach(held: Set[str], held_gate_nodes: FrozenSet[str], resolvable_materials: Set[str],
                      production_entries: ProductionEntries, mods_dir: Optional[str] = None) -> FrozenSet[str]:
    """Keys of techniques not held that make only materials the held set cannot make, where the technique
    is the fewest research steps away for every material it makes.

    Such a technique prices a new material through the techniques held for everything else and cannot
    undercut one already held; a later, cheaper route to the same material, or a joint process whose
    co-product a nearer technique already makes, is left out (the material then prices at the nearer one)."""
    # a waste co-product (manure, straw) is tipped when nobody takes it, so it neither shuts a joint process out
    # because the held set already makes it nor decides which technique is nearest
    products = {material for material in production_entries_outputs(production_entries)
                if material not in disposal_cost.waste_materials()}
    candidates = {}
    for key, entry in production_entries.items():
        gate = entry.get("requires_node")
        outputs = entry.get("outputs") or {}
        if gate is None or gate in held_gate_nodes or not any(material in products for material in outputs):
            continue
        if any(material in resolvable_materials and material in products for material in outputs):
            continue
        candidates[key] = (_unheld_steps_to(gate, held, mods_dir), key)
    nearest: Dict[str, Tuple[int, str]] = {}
    for key, rank in candidates.items():
        for material in production_entries[key]["outputs"]:
            if material not in products:
                continue
            if material not in nearest or rank < nearest[material]:
                nearest[material] = rank
    return frozenset(key for key, rank in candidates.items()
                     if all(nearest[material] == rank for material in production_entries[key]["outputs"]
                           if material in products))


def _climate_allows(entry, held_tiles):
    """Whether the territory has a climate the entry's crop grows in; entries naming none always do."""
    if not entry or not entry.get("grown_in_climate_classes"):
        return True
    return crop_climate.entry_grows_in(entry, held_tiles)


def climate_allows_entry(entry: Optional[Mapping[str, Any]], civilization: Mapping[str, Any]) -> bool:
    """Whether a civilisation's territory has the climate the entry's crop grows in."""
    return _climate_allows(entry, tuple(tiles_held(civilization)))


def priced_goods_in_hours(held_technology_ids: Iterable[str],
                          document_ratios: Dict[str, float],
                          production_entries: Optional[ProductionEntries] = None,
                          civilization_id: Optional[str] = None,
                          interest_rate: Optional[float] = None,
                          civilization: Optional[Mapping[str, Any]] = None,
                          farmed_hectares: Optional[float] = None,
                          rent_hours_per_kg_by_material: Optional[Mapping[str, float]] = None,
                          mods_dir: Optional[str] = None
                          ) -> Tuple[Prices, Provenance, Dict[str, str]]:
    """(hours, provenance, recipe) per material: what `priced_goods_table` prices, in labour hours, with the
    recipe that makes each. Wages are hours of unskilled labour an hour of each trade is worth."""
    entries = (production_entries if production_entries is not None
               else default_production_entries(mods_dir))
    held = frozenset(held_technology_ids)
    civilization = civilization_record(civilization, civilization_id, mods_dir)
    arguments = dict(production_entries=entries, civilization_id=civilization["id"],
                     interest_rate=interest_rate, civilization=civilization, farmed_hectares=farmed_hectares,
                     rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
    solved = solved_prices_at_wages(held, document_ratios, **arguments)
    in_reach = solved_prices_at_wages(
        solved.gate_nodes_held, document_ratios,
        admitted_entry_keys=entries_in_reach(held, solved.gate_nodes_held, solved.resolvable_materials, entries, mods_dir),
        **arguments)
    hours = {}
    provenance = {}
    recipe = {}
    held_tiles = tuple(tiles_held(civilization))
    for table, label in ((in_reach, "gated"), (solved, "solved")):
        for material in table.resolvable_materials:
            if material not in table.chosen_recipe_by_material:
                continue    # no technique in this table delivers it (a heat it cannot reach): the price is a placeholder
            if not _climate_allows(entries.get(table.chosen_recipe_by_material[material]), held_tiles):
                continue    # a crop the territory's climate cannot grow is not made here; only a partner could sell it
            hours[material] = table.prices_in_labour_hours[material]
            provenance[material] = label
            recipe[material] = table.chosen_recipe_by_material[material]
    return hours, provenance, recipe


def goods_in_hours(held_technology_ids: Iterable[str],
                   document: Dict[str, Any],
                   civilization: Mapping[str, Any],
                   farmed_hectares: Optional[float] = None,
                   interest_rate: Optional[float] = None,
                   production_entries: Optional[ProductionEntries] = None,
                   unskilled_trade: Optional[str] = None,
                   mods_dir: Optional[str] = None
                   ) -> Tuple[Prices, Provenance]:
    """(labour-hour cost of each good, provenance): the one builder of the goods table. `document` is the wage
    document of the civilisation's opening schedule, which supplies the wage ratios against the hour of
    `unskilled_trade` (the live registry's, else the committed one's); the table is in labour hours and a caller
    states it in a coin by `rules.money_prices`."""
    hours, provenance, _recipe = priced_goods_in_hours(
        held_technology_ids, solve_prices_core.wage_ratios_by_trade(document, unskilled_trade, mods_dir), production_entries,
        interest_rate=interest_rate, civilization=civilization, farmed_hectares=farmed_hectares, mods_dir=mods_dir)
    return hours, provenance


def priced_goods_table(held_technology_ids: Iterable[str],
                       prices_json: Dict[str, Any],
                       production_entries: Optional[ProductionEntries] = None,
                       civilization_id: Optional[str] = None,
                       interest_rate: Optional[float] = None,
                       civilization: Optional[Mapping[str, Any]] = None,
                       farmed_hectares: Optional[float] = None,
                       unskilled_trade: Optional[str] = None,
                       mods_dir: Optional[str] = None
                       ) -> Tuple[Prices, Provenance]:
    """(goods_in_money, provenance) - what it costs to make every material
    the recipes can make, in the coin of `prices_json`. A cost, not a price: the
    price somebody pays is the economy's.

      "solved" - made under the technologies this society holds.
      "gated"  - nothing this society holds makes it, but a technique it does
                 not hold does; costed at that technique with every other
                 input costed as this society makes it, so a good and the
                 inputs its own route buys sit in one cost system.
                 A technique is in reach when its node is the fewest research steps
                 from what the society holds (`entries_in_reach`).

    A material nothing in reach makes is absent: a trading partner that makes it may still sell it
    (the goods market prices that at the partner's cost plus freight and merchants' terms); where no
    one does, it cannot be bought.

    `civilization_id` and `interest_rate` are passed straight through to `solved_prices` - see RENT
    NEEDS A CIVILIZATION in the module docstring. `civilization`, when the caller holds
    it, supplies the rate, territory and home regions (which decide the crops its climate grows)
    without reading a file by id. The rent charged is the opening's stand-in. `unskilled_trade` is the trade whose hour
    the wages are stated against: the live registry's, else the committed one's.
    """
    civilization = civilization_record(civilization, civilization_id, mods_dir)
    hours, provenance = goods_in_hours(
        held_technology_ids, prices_json, civilization, farmed_hectares, interest_rate, production_entries, unskilled_trade, mods_dir)
    return {material: hours_to_denarii(cost, prices_json) for material, cost in hours.items()}, provenance
