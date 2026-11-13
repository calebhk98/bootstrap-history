"""The plans for markets with unmet demand (`entry.entry_plans`) as one compiled loop: for each market in order, its recipes best
return first, each built for a share of what the better ones leave of the gap, held to the trade the markets carried, sited on the
tile that suits it, the siting booking the capacity and hands the next candidate sees.

Reads (`entry_plan_steps.py` documents the tables): per market its good column, anchor tile row, unmet quantity, place in the year's
bids block (-1 where it has none) and its recipes in the order tried (`rank_first`, `rank_count` into `rank_recipe`). `block` is the
year's bids block as a tuple of its six figure columns and its `start` (`year_bids.YearBids`). Writes the rows of `plans`
(`entry_plan_table.py`) and returns how many it holds."""
import numpy

from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.jit import njit

from .bid_columns import sum_taken_at_columns
from .entry import ENTRY_SHARE_OF_UNMET_DEMAND
from .entry_kernels import full_cost_one
from .entry_plan_steps import NO_TILE, site_newcomer, sized_runs_at
from .stock_residue import STOCK_RESIDUE_UNITS
from .year_arrays_costs import KERNEL


@njit(**KERNEL)
def unfilled_at_cost(recipe, good, anchor, place, output_per_year, made, block, tables, own_rate, traded):
    """`entry_backed.unfilled_at_cost`: the units the market's bids take at the recipe's full cost per unit (its newcomer on the
    hours it is judged on, planned for `output_per_year`) beyond what the market traded; zero where the market has no bids or the
    recipe cannot be costed."""
    start = block[6]
    if place < 0 or start[place + 1] == start[place]:
        return 0.0
    cost = full_cost_one(recipe, anchor, good, output_per_year / made, own_rate, tables)
    if not numpy.isfinite(cost) or not cost > 0.0:
        return 0.0
    first, last = start[place], start[place + 1]
    taken = sum_taken_at_columns(block[0][first:last], block[1][first:last], block[2][first:last], block[3][first:last],
                                 block[4][first:last], block[5][first:last], cost)
    volume = traded[good, anchor]
    return max(0.0, taken - max(0.0, 0.0 if numpy.isnan(volume) else volume))


@njit(**KERNEL)
def unmet_plans(market_good, market_anchor, market_quantity, market_place, rank_first, rank_count, rank_recipe, rank_return, block,
                tables, own_rate, outputs, plant_goods, sizing, traded, siting, sites, of_good_tile, plans):
    """The plans of every market, in market order, written to `plans`; returns the number of rows in it, or minus one when it is full
    (it is sized for one row per recipe tried, so it is not)."""
    recipe_scalar = tables[6]
    for market in range(market_good.shape[0]):
        good, anchor = market_good[market], market_anchor[market]
        remaining = market_quantity[market]
        for position in range(rank_first[market], rank_first[market] + rank_count[market]):
            recipe = rank_recipe[position]
            if remaining < STOCK_RESIDUE_UNITS:
                break
            made = outputs[recipe, good]
            whole_gap_runs = remaining / made
            backed = unfilled_at_cost(recipe, good, anchor, market_place[market], whole_gap_runs * ENTRY_SHARE_OF_UNMET_DEMAND * made,
                                      made, block, tables, own_rate, traded)
            runs = sized_runs_at(recipe, good, whole_gap_runs * ENTRY_SHARE_OF_UNMET_DEMAND, whole_gap_runs, anchor, NO_TILE, backed,
                                 traded, outputs, plant_goods, sizing)
            tile = anchor
            if runs > 0.0 and numpy.isfinite(runs):
                picked, taken = site_newcomer(recipe, good, anchor, runs, tables, siting, sites, of_good_tile,
                                              recipe_scalar[recipe, 1] > 0.0)
                if picked < 0:
                    continue
                runs = sized_runs_at(recipe, good, taken, whole_gap_runs, anchor, picked, backed, traded, outputs, plant_goods, sizing)
                tile = picked
            if runs * made >= STOCK_RESIDUE_UNITS and numpy.isfinite(runs):      # an entrant of residue size is no entrant
                row = claim_row(plans)
                if row == NO_ROOM:
                    return -1
                plans.recipe_row[row] = recipe
                plans.tile_row[row] = tile
                plans.good_col[row] = good
                plans.runs[row] = runs
                plans.yearly_return[row] = rank_return[position]
                remaining -= runs * made
    return plans.row_count[0]
