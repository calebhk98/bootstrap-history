"""Ask the price solver for a price.

Prices are calculated from recipes, land rent, wages and transport by
`sim/engine/solve_prices.py`, gated to what a civilization has reached
(Complaints/38). This module is the engine's one call into the solver. It is
thin: it imports the solver rather than re-implementing it. There is no price
book; a material nothing can make has no price.

THE WAGE ARGUMENT (`prices_json` below) is a wage document in the
shape the solver reads, built by `sim.labour.wages.WageSchedule.document()`, so the solver and
payroll read one wage vector. Its labourer rate is the money value of one
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

LABOUR-HOURS TO DENARII. `sim/engine/solve_prices.py` prices everything in
labour-hours - one hour of `labourer`, its numeraire, equals 1.0 - because a
recipe graph can produce relative amounts of unskilled effort. Money enters
only here, at the edge: the wage document carries `money_per_labour_hour`,
which `sim.engine.wage_schedule.build_schedule` derives from the
civilisation's coin (the coin material's solved labour hours per kg times the
coin's mass), so a price in money is its labour hours times that rate.
`denarii_per_labour_hour` is the one place the rate is read.

WHAT THIS DOES NOT HANDLE, LEFT FOR THE NEXT STEP. `solve_prices.py` itself
flags MINOR JOINT BYPRODUCTS (platinum, coal tar and the like) that were split
by mass as lower bounds rather than independent prices - see that module's own
docstring. This file still reports them as "solved" rather than a third
category, because a third provenance state is a design decision of its own; a caller that
cares can already recover the distinction by re-running
`solve_prices.minor_joint_byproducts_split_by_mass` against the same
`SolvedPrices.chosen_recipe_by_material`, which is exposed for exactly that
kind of downstream question.

RENT IS AN ARGUMENT (Complaints/507). `solved_prices` takes
`rent_hours_per_kg_by_material` and charges exactly that (empty: none). A
caller with none takes the opening's stand-in from `sim/engine/rent_standin.py`,
computed once per solve and threaded through `compute_resolvable_materials` and
`solve`; it is the only place a demanded quantity still reaches a price.

RENT NEEDS A CIVILIZATION, AND SO DOES THE CACHE KEY. The land stand-in is
genuinely per-civilization - `sim/world/land.py` prices the margin of
cultivation over a CIVILIZATION'S OWN HELD REGIONS, and two civilizations can
hold the exact same gate-node set while holding completely different
territory. A cache key of `gate_nodes_held` alone cannot distinguish them, so
`solved_prices` and `priced_goods_table` take an explicit `civilization_id`
parameter and fold it into the cache key alongside `gate_nodes_held`, together
with the rent a caller supplied. It defaults to `None`, which resolves to
`solve_prices.DEFAULT_LAND_CIVILIZATION` (the default civilisation) - the same
default the CLI uses when `--civ` is omitted.
"""
import json
import math
import os
import sys
from typing import Any, Dict, FrozenSet, Iterable, Mapping, Optional, Set, Tuple

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

# {material: "solved" | "gated"} - see priced_goods_table's own docstring
# for what the two strings mean. A plain Dict[str, str]: the KEYS are
# material ids, open and data-driven.
Provenance = Dict[str, str]

HERE = os.path.dirname(os.path.abspath(__file__))              # sim/engine
SIMDIR = os.path.dirname(HERE)                                  # sim
REPO_ROOT = os.path.dirname(SIMDIR)                             # repo root
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from sim.engine import disposal_cost, rent_standin, solve_prices, solve_prices_reach  # noqa: E402
from sim.engine.validate_production import load_production             # noqa: E402
from sim.labour.api import wages                                     # noqa: E402
from sim.labour.api import wage_provider                # noqa: E402
from sim.engine import solve_cache                              # noqa: E402
from sim.constants import declare                                # noqa: E402
from sim.geography.api import tiles_held                    # noqa: E402


class SolvedPrices(object):
    """One gated solve's result, cached and handed back verbatim on a hit.

    `prices_in_labour_hours` and `chosen_recipe_by_material` are exactly
    `solve_prices.solve`'s own return values, kept in the solver's native
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


def solver_wage_ratios(production_entries: ProductionEntries,
                       document_ratios: Dict[str, float]) -> Dict[str, float]:
    """Wage of every trade the entries use, in labour hours an hour: the document's, and for a trade
    it does not list the same training rule the labour market uses."""
    wage_by_trade = dict(document_ratios)
    registry = solver_trade_registry(production_entries)
    training_years = wage_provider.training_years_by_trade(registry)
    for trade in registry:
        wage_by_trade.setdefault(trade, wages.training_premium(
            training_years[trade], wage_provider.reference_discount_rate()))
    return wage_by_trade


def default_production_entries() -> ProductionEntries:
    """The committed production catalogue, read once per process."""
    return _default_production_entries()


def waste_dump_minimum_distance(civilization: Optional[Mapping[str, Any]]) -> float:
    """The nearest a state lets waste be tipped to settlement and water, in km; none unless the record says."""
    if civilization is None:
        return 0.0
    return float(civilization.get("waste_dump_minimum_distance_kilometres") or 0.0)


def territory_fingerprint(civilization: Optional[Mapping[str, Any]]) -> Optional[Tuple[Any, ...]]:
    """What of a held civilisation the solve reads beyond its id: its people, its ground and its dump rule."""
    if civilization is None:
        return None
    return (civilization.get("population"), tuple(tiles_held(civilization)),
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


def _held(civilization: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    return None if civilization is None else {civilization["id"]: civilization}


# The engine's solves stop at this largest relative price change per round, far looser than the solver's own
# tolerance (tighter than any price the game shows or any decision it takes).
ENGINE_SOLVE_TOLERANCE = declare(
    "ENGINE_SOLVE_TOLERANCE", 1e-5, kind="temporary_heuristic", unit="largest relative price change in a round",
    source=None, confidence="D",
    why="Stops the in-game price solve once prices settle to the precision play can see; the solver's "
        "own tolerance runs many more rounds for digits nothing reads.")


def _solve_to_json(production_entries: ProductionEntries,
                   gate_nodes_held: FrozenSet[str], civilization_id: str,
                   document_ratios: Dict[str, float],
                   admitted_entry_keys: FrozenSet[str] = frozenset(),
                   interest_rate: float = 0.0,
                   civilization: Optional[Mapping[str, Any]] = None,
                   farmed_hectares: Optional[float] = None,
                   in_game: bool = False, initial_prices: Optional[Dict[str, float]] = None,
                   rent_hours_per_kg_by_material: Optional[Mapping[str, float]] = None) -> Dict[str, Any]:
    """Run the solver for one held-gate set; the result is JSON-able. `in_game` starts from `initial_prices`
    (when given) and stops at ENGINE_SOLVE_TOLERANCE; otherwise the solve is cold and exact. The rent charged is
    `rent_hours_per_kg_by_material` when given (none at all if empty), else the opening's stand-in."""
    # `gate_nodes_held` is exactly the right thing to hand
    # `techniques_available_to` as `reached_nodes`: every `requires_node` it
    # will ever check membership for is, by `all_gate_nodes`'s own
    # construction, a gate node, so restricting the membership set to the
    # gate nodes actually held changes no answer - see CACHE KEY above.
    available_entries, _unreached, _unclassified = \
        solve_prices.techniques_available_to(production_entries, gate_nodes_held)
    for entry_key in admitted_entry_keys:
        available_entries[entry_key] = production_entries[entry_key]
    producers_of = solve_prices.build_producers_index(available_entries)
    wage_by_trade = solver_wage_ratios(production_entries, document_ratios)

    if rent_hours_per_kg_by_material is None:
        rent_hours_per_kg_by_material = rent_standin.stand_in_rent(
            available_entries, wage_by_trade, civilization_id=civilization_id,
            civilizations=_held(civilization), farmed_hectares=farmed_hectares)
    else:
        rent_hours_per_kg_by_material = dict(rent_hours_per_kg_by_material)

    resolvable_materials = solve_prices.compute_resolvable_materials(
        available_entries, producers_of,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
    (prices_in_labour_hours, iterations_run, residual,
     chosen_recipe_by_material, resolvable_materials) = solve_prices_reach.solve_priced_materials(
        available_entries, producers_of, resolvable_materials, wage_by_trade,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
        interest_rate=interest_rate,
        dump_minimum_distance_kilometres=waste_dump_minimum_distance(civilization),
        **({"initial_prices": initial_prices, "tolerance": ENGINE_SOLVE_TOLERANCE} if in_game else {}))

    return {
        "prices_in_labour_hours": prices_in_labour_hours,
        "resolvable_materials": sorted(resolvable_materials),
        "chosen_recipe_by_material": chosen_recipe_by_material,
        "converged": residual < (ENGINE_SOLVE_TOLERANCE if in_game else solve_prices.CONVERGENCE_TOLERANCE),
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
                  rent_hours_per_kg_by_material: Optional[Mapping[str, float]] = None) -> SolvedPrices:
    """A `SolvedPrices` for this held-technology set, solving on a cache
    miss and returning the cached vector on a hit. See CACHE KEY in the
    module docstring: the cache is keyed on the intersection of
    `held_technology_ids` with `all_gate_nodes`, together with
    `civilization_id`, not on the full held-technology set, which is what
    keeps a whole game's worth of calls to a bound few dozen solves.

    `civilization_id` decides whose territory the land rent stand-in
    prices (see RENT NEEDS A CIVILIZATION in the module docstring); it
    defaults to `None`, which resolves to `solve_prices.
    DEFAULT_LAND_CIVILIZATION` (the default civilisation), matching what the CLI does when
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
    (`sim/engine/rent_standin.py`, the only place a demanded quantity still enters a price).
    """
    return solved_prices_at_wages(
        held_technology_ids, solve_prices.wage_ratios_by_trade(prices_json), production_entries, civilization_id,
        admitted_entry_keys, interest_rate, civilization, farmed_hectares, rent_hours_per_kg_by_material)


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
    if civilization is not None:
        civilization_id = civilization["id"]
        if interest_rate is None:
            interest_rate = float(civilization["starting_interest_rate"])
    civilization_id = civilization_id or solve_prices.DEFAULT_LAND_CIVILIZATION
    starting_rate = (float(civilization["starting_interest_rate"]) if civilization is not None
                     else solve_prices.load_starting_interest_rate(civilization_id))
    if interest_rate is None:
        interest_rate = starting_rate
    territory = territory_fingerprint(civilization)
    farmed_area = farmed_hectares
    farmed_hectares = band_farmed_hectares(farmed_hectares)

    gate_nodes_held = frozenset(all_gate_nodes(production_entries)
                                & set(held_technology_ids))
    rent_key = None if rent_hours_per_kg_by_material is None else tuple(sorted(rent_hours_per_kg_by_material.items()))
    # Wages move with the labour market, so the cache is keyed on them too.
    cache_key = (gate_nodes_held, civilization_id,
                 tuple(sorted(document_ratios.items())), admitted_entry_keys, interest_rate, territory,
                 farmed_hectares, rent_key)

    cached = _SOLVE_CACHE.get(cache_key)
    if cached is not None and cached[0] is production_entries:
        return cached[1]

    in_game = production_entries is _DEFAULT_PRODUCTION_ENTRIES

    def compute() -> Dict[str, Any]:
        # A solve at another rate starts from the same solve at the starting rate (itself started cold), so
        # its result depends on its own inputs only, never on which solves ran before it.
        initial = None
        if in_game and interest_rate != starting_rate:
            initial = solved_prices_at_wages(
                held_technology_ids, document_ratios, production_entries, civilization_id, admitted_entry_keys,
                starting_rate, civilization, farmed_area, rent_hours_per_kg_by_material).prices_in_labour_hours
        return _solve_to_json(production_entries, gate_nodes_held,
                              civilization_id, document_ratios, admitted_entry_keys, interest_rate,
                              civilization, farmed_hectares, in_game, initial, rent_hours_per_kg_by_material)
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
_SOLVER_SOURCE = ("sim.engine.prices",)


def _tree_nodes() -> Dict[str, Any]:
    """The tech tree by node id, read once per process."""
    if _TREE_NODES.get("nodes") is None:
        from .catalog import load_mod_tree_nodes
        root = os.path.dirname(os.path.dirname(HERE))
        _TREE_NODES["nodes"] = {node["id"]: node for node in load_mod_tree_nodes(root)}
    return _TREE_NODES["nodes"]


def _unheld_steps_to(node_id: str, held: Set[str]) -> int:
    """How many technologies not yet held stand between a society and this one, itself included."""
    nodes = _tree_nodes()
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
        from .data import closure
        cached[node_id] = frozenset(closure(nodes, node_id))
    return cached[node_id]


def production_entries_outputs(production_entries: ProductionEntries) -> Set[str]:
    return {material for entry in production_entries.values() for material in (entry.get("outputs") or {})}


def entries_in_reach(held: Set[str], held_gate_nodes: FrozenSet[str], resolvable_materials: Set[str],
                     production_entries: ProductionEntries) -> FrozenSet[str]:
    """`_entries_in_reach`, remembered per argument set: a society asks again for the techniques it holds."""
    memo = _TREE_NODES.setdefault("in_reach", {})
    if memo.get("entries") is not production_entries:
        memo.clear()
        memo["entries"] = production_entries
    key = (frozenset(held), frozenset(held_gate_nodes), frozenset(resolvable_materials))
    if key not in memo:
        memo[key] = _entries_in_reach(held, held_gate_nodes, resolvable_materials, production_entries)
    return memo[key]


def _entries_in_reach(held: Set[str], held_gate_nodes: FrozenSet[str], resolvable_materials: Set[str],
                      production_entries: ProductionEntries) -> FrozenSet[str]:
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
        candidates[key] = (_unheld_steps_to(gate, held), key)
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


def _climate_allows(entry, civilization_id, held_tiles=None):
    """Whether the territory has a climate the entry's crop grows in; entries naming none always do."""
    if not entry or not entry.get("grown_in_climate_classes"):
        return True
    from sim.geography.api import crop_climate
    if held_tiles is None:
        from .data import load_civ
        held_tiles = tiles_held(load_civ(civilization_id))
    return crop_climate.entry_grows_in(entry, held_tiles)


def climate_allows_entry(entry: Optional[Mapping[str, Any]], civilization: Mapping[str, Any]) -> bool:
    """Whether a civilisation's territory has the climate the entry's crop grows in."""
    return _climate_allows(entry, civilization["id"], tuple(tiles_held(civilization)))


def priced_goods_in_hours(held_technology_ids: Iterable[str],
                          document_ratios: Dict[str, float],
                          production_entries: Optional[ProductionEntries] = None,
                          civilization_id: Optional[str] = None,
                          interest_rate: Optional[float] = None,
                          civilization: Optional[Mapping[str, Any]] = None,
                          farmed_hectares: Optional[float] = None,
                          rent_hours_per_kg_by_material: Optional[Mapping[str, float]] = None
                          ) -> Tuple[Prices, Provenance, Dict[str, str]]:
    """(hours, provenance, recipe) per material: what `priced_goods_table` prices, in labour hours, with the
    recipe that makes each. Wages are hours of unskilled labour an hour of each trade is worth."""
    entries = (production_entries if production_entries is not None
               else _default_production_entries())
    held = frozenset(held_technology_ids)
    arguments = dict(production_entries=production_entries, civilization_id=civilization_id,
                     interest_rate=interest_rate, civilization=civilization, farmed_hectares=farmed_hectares,
                     rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
    solved = solved_prices_at_wages(held, document_ratios, **arguments)
    in_reach = solved_prices_at_wages(
        solved.gate_nodes_held, document_ratios,
        admitted_entry_keys=entries_in_reach(held, solved.gate_nodes_held, solved.resolvable_materials, entries),
        **arguments)
    hours = {}
    provenance = {}
    recipe = {}
    territory = civilization_id or solve_prices.DEFAULT_LAND_CIVILIZATION
    held_tiles = None if civilization is None else tuple(tiles_held(civilization))
    for table, label in ((in_reach, "gated"), (solved, "solved")):
        for material in table.resolvable_materials:
            if material not in table.chosen_recipe_by_material:
                continue    # no technique in this table delivers it (a heat it cannot reach): the price is a placeholder
            if not _climate_allows(entries.get(table.chosen_recipe_by_material[material]), territory, held_tiles):
                continue    # a crop the territory's climate cannot grow is not made here; only a partner could sell it
            hours[material] = table.prices_in_labour_hours[material]
            provenance[material] = label
            recipe[material] = table.chosen_recipe_by_material[material]
    return hours, provenance, recipe


def priced_goods_table(held_technology_ids: Iterable[str],
                       prices_json: Dict[str, Any],
                       production_entries: Optional[ProductionEntries] = None,
                       civilization_id: Optional[str] = None,
                       interest_rate: Optional[float] = None,
                       civilization: Optional[Mapping[str, Any]] = None,
                       farmed_hectares: Optional[float] = None
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
    without reading a file by id. The rent charged is the opening's stand-in.
    """
    hours, provenance, _recipe = priced_goods_in_hours(
        held_technology_ids, solve_prices.wage_ratios_by_trade(prices_json), production_entries, civilization_id,
        interest_rate, civilization, farmed_hectares)
    return {material: hours_to_denarii(cost, prices_json) for material, cost in hours.items()}, provenance
