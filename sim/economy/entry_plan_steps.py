"""The steps one entry plan takes, as small compiled helpers the plan loops (`entry_unmet_kernel.py`) call: how many runs a newcomer is
built for given the trade each market carried (`entry_sizing.sized_runs`), and the tile it is sited on (`EntryTables.siting`).

Every function is the Python of the same name over arrays. `traded` is a (good column, tile row) grid of the units the good's market
carried last year, NaN for a good with no market (`entry_year._traded_volume`'s None). The siting state (`capacity`, `committed`)
is written to as sites are claimed, as the Python closure writes it.

Tables read (all indexed by recipe row, good column, tile row):
    sizing   `SizingTables`   what the size rule reads of each recipe: the inputs a run cannot go ahead without (`hard_inputs`)
    sites    `SiteTables`     what the siting rule reads of each recipe, worked out for the recipes the loop may meet
"""
import numpy

from sim.compiled_tables.spec import Column, TableSpec
from sim.jit import njit

from .entry_kernels import site_choice
from .entry_sizing import ENTRY_SHARE_OF_INPUT_VOLUME, ENTRY_SHARE_OF_TRADED_VOLUME, ENTRY_SHARE_OF_UNTRADED_DEMAND
from .year_arrays_costs import KERNEL

NO_TILE = -1

SIZING = TableSpec("SizingTables", (
    Column("hard_inputs", numpy.float64, "units of each good a run cannot go ahead without (inputs less the tools' wear)", "units per run",
           width=0),
))
SizingTables = SIZING.make_type(__name__)

SITES = TableSpec("SiteTables", (
    Column("sited", numpy.bool_, "the recipe is bound to the sites its limits declare", "flag"),
    Column("runs_anywhere", numpy.bool_, "the recipe may be worked on its market's anchor tile without a siting search", "flag"),
    Column("tonnes_out", numpy.float64, "tonnes of output a run carries to its market", "tonnes per run"),
    Column("hours_per_run", numpy.float64, "hours a run takes in an entrant's first year", "hours per run"),
    Column("order_count", numpy.int64, "how many candidate tiles a sited recipe has in `order`", "tiles"),
    Column("order", numpy.int64, "a sited recipe's suited tiles in the setup's tile order, the first `order_count` of them", "tile row",
           width=0),
    Column("fits", numpy.bool_, "the tile's climate and people allow the recipe", "flag", width=0),
    Column("suited", numpy.bool_, "fits, and the recipe's limit is declared on the tile where it is site-bound", "flag", width=0),
    Column("supply_tiles", numpy.bool_, "a maker of one of the recipe's fixed-site inputs stands on the tile", "flag", width=0),
))
SiteTables = SITES.make_type(__name__)


@njit(**KERNEL)
def runs_supported(volume, per_run, trial_runs):
    """`entry_sizing._runs_supported`: the runs a market's trade could feed or absorb; no limit where the good is not traded (`volume`
    NaN) or a run takes none of it."""
    if numpy.isnan(volume) or per_run <= 0.0:
        return numpy.inf
    if volume > 0.0:
        return ENTRY_SHARE_OF_INPUT_VOLUME * volume / per_run
    return trial_runs


@njit(**KERNEL)
def sized_runs_at(recipe, good, runs_by_gap, whole_gap_runs, tile, works_at, unfilled, traded, outputs, plant_goods, sizing):
    """`entry_sizing.sized_runs` with a traded grid: the share of the gap held to the good's market at `tile` (with the `unfilled`
    demand counted as trade) and to the markets of the recipe's inputs and plant goods where it is worked (`works_at`, or `tile`
    when `works_at` is NO_TILE)."""
    trial_runs = ENTRY_SHARE_OF_UNTRADED_DEMAND * whole_gap_runs
    volume = traded[good, tile]
    if numpy.isnan(volume):
        market_runs = numpy.inf
    else:
        market_runs = ENTRY_SHARE_OF_TRADED_VOLUME * (volume + unfilled) / outputs[recipe, good]
        if volume <= 0.0:
            market_runs = max(trial_runs, market_runs)
    at = tile if works_at == NO_TILE else works_at
    supply_runs = numpy.inf
    for input_good in range(traded.shape[0]):
        supply_runs = min(supply_runs, runs_supported(traded[input_good, at], sizing.hard_inputs[recipe, input_good], trial_runs))
        supply_runs = min(supply_runs, runs_supported(traded[input_good, at], plant_goods[recipe, input_good], trial_runs))
    return min(runs_by_gap, min(market_runs, supply_runs))


@njit(**KERNEL)
def candidate_tiles(recipe, good, anchor, sites, of_good_tile):
    """The tiles (rows) a newcomer of the recipe may be sited on when it is not worked on the anchor: a sited recipe's own order;
    else the tiles it is suited to that are in the market's area (the area of `good` on the anchor) or hold a maker of its fixed-site
    input, in tile row order (`EntryTables.siting`)."""
    if sites.sited[recipe]:
        return sites.order[recipe, :sites.order_count[recipe]].copy()
    area = of_good_tile[good, anchor]
    found = numpy.empty(sites.suited.shape[1], dtype=numpy.int64)
    count = 0
    for tile in range(sites.suited.shape[1]):
        if sites.suited[recipe, tile] and ((area >= 0 and of_good_tile[good, tile] == area) or sites.supply_tiles[recipe, tile]):
            found[count] = tile
            count += 1
    return found[:count].copy()


@njit(**KERNEL)
def site_newcomer(recipe, good, anchor, runs, tables, siting, sites, of_good_tile, takes_land):
    """`EntryTables.siting`'s function: (tile row, runs) for a newcomer of the recipe wanting `runs` runs in the market of `good`
    anchored on tile `anchor`, or (NO_TILE, 0) when no tile suits it. The runs are booked in `siting.capacity` and `siting.committed`.
    `siting` is a tuple of the arrays the siting reads and writes (see `entry_siting_state`)."""
    (tonnes, supply_weight, supply_present, carriage, hauls, yield_rt, limit_rt, short_of_land, hands_hours, capacity, committed) = siting
    if sites.runs_anywhere[recipe] and not (takes_land and short_of_land[anchor]) and sites.fits[recipe, anchor]:
        capacity[recipe, anchor] += runs
        committed[anchor] += runs * sites.hours_per_run[recipe]
        return anchor, runs
    candidates = candidate_tiles(recipe, good, anchor, sites, of_good_tile)
    return site_choice(recipe, anchor, candidates, runs, sites.tonnes_out[recipe], tables, tonnes, supply_weight, supply_present, carriage,
                       hauls, yield_rt, limit_rt, takes_land, short_of_land, hands_hours, capacity, committed, sites.hours_per_run[recipe])
