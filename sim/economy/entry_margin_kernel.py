"""The margin's and the trial's plans (`entry_margin.margin_entry_plans`, `entry_trial.trial_entry_plans`) as compiled loops over the markets
with bids, in market order, each plan sited on the tile that suits it with the siting booking the capacity and hands the next sees.

Both read, per market, its good column, anchor tile row, place in the year's bids block (`block` as in `entry_unmet_kernel`), price now
(NaN: none) and its recipes in the order tried (`rank_first`, `rank_count` into `rank_recipe` and `rank_cost`, cheapest first, the full
cost per unit of the good). They write rows of `plans` (`entry_plan_table.py`) and return how many it holds, or minus one when it is full.
The margin also reads each market's reachable capacity, expected price, years the expected price has stood above the entry price and whether
an earlier plan took the market (`skipped`), and writes `years_out` and `counted` (a market whose streak the rule keeps)."""
import numpy

from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.jit import njit

from .bid_columns import demand_at_columns
from .entry_margin import MARGIN_ENTRY_GROWTH_SHARE, MARGIN_ENTRY_SHARE_OF_GAP
from .entry_plan_steps import site_newcomer
from .entry_sizing import ENTRY_SHARE_OF_UNTRADED_DEMAND
from .entry_trial import ENTRY_PRICE_MARGIN_SHARE
from .producers_close import LOSS_YEARS_BEFORE_EXIT
from .year_arrays_costs import KERNEL


@njit(**KERNEL)
def streak_after(years, expected_price, entry_price):
    """`entry_margin.margin_streak`: the years in a row the expected price has stood above the entry price, after this year."""
    return years + 1 if expected_price > entry_price else 0


@njit(**KERNEL)
def streak_has_lasted(years):
    """`entry_margin.margin_has_lasted`."""
    return years >= LOSS_YEARS_BEFORE_EXIT


@njit(**KERNEL)
def demand_in_market(block, place, price, price_now):
    """`entry_trial.demand_at` of the market's bids in the block (`place` is a row of the block's `start`)."""
    start = block[6]
    first, last = start[place], start[place + 1]
    return demand_at_columns(block[0][first:last], block[1][first:last], block[2][first:last], block[3][first:last], block[4][first:last],
                             block[5][first:last], price, price_now)


@njit(**KERNEL)
def margin_plans(market_good, market_anchor, market_place, market_capacity, market_price, market_expected, market_years, market_skipped,
                 rank_first, rank_count, rank_recipe, rank_cost, block, tables, outputs, siting, sites, of_good_tile, plans, years_out,
                 counted):
    """The margin's plans, market by market (see the module docstring)."""
    recipe_scalar = tables[6]
    for market in range(market_good.shape[0]):
        if rank_count[market] == 0:
            continue
        counted[market] = True
        good, price, expected = market_good[market], market_price[market], market_expected[market]
        first = rank_first[market]
        years_out[market] = streak_after(market_years[market], min(expected, price) if price > 0.0 else expected,
                                          rank_cost[first] * (1.0 + ENTRY_PRICE_MARGIN_SHARE))
        if market_skipped[market] or not streak_has_lasted(years_out[market]):
            continue
        ceiling = min(expected, price if price > 0.0 else expected)
        capacity = market_capacity[market]
        room = MARGIN_ENTRY_GROWTH_SHARE * capacity
        for position in range(first, first + rank_count[market]):
            cost = rank_cost[position]
            entry_price = cost * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
            if entry_price >= ceiling or room <= 0.0:
                break
            recipe = rank_recipe[position]
            gap = max(0.0, demand_in_market(block, market_place[market], entry_price, price if price > 0.0 else entry_price) - capacity)
            added = min(MARGIN_ENTRY_SHARE_OF_GAP * gap, room)
            made = outputs[recipe, good]
            runs = added / made
            tile = market_anchor[market]
            if runs > 0.0:
                tile, runs = site_newcomer(recipe, good, market_anchor[market], runs, tables, siting, sites, of_good_tile,
                                           recipe_scalar[recipe, 1] > 0.0)
                if tile < 0:
                    continue
            if runs > 0.0 and numpy.isfinite(runs):
                row = claim_row(plans)
                if row == NO_ROOM:
                    return -1
                plans.recipe_row[row] = recipe
                plans.tile_row[row] = tile
                plans.good_col[row] = good
                plans.runs[row] = runs
                plans.yearly_return[row] = (expected - cost) / cost
                room -= runs * made
                capacity += runs * made
    return plans.row_count[0]


@njit(**KERNEL)
def trial_plans(market_good, market_anchor, market_place, market_price, rank_first, rank_count, rank_recipe, rank_cost, block, tables,
                outputs, siting, sites, of_good_tile, plans):
    """The trial's plans, market by market: each recipe for a share of what the bids would still take at its entry price beyond what the
    cheaper recipes' newcomers were built for."""
    recipe_scalar = tables[6]
    for market in range(market_good.shape[0]):
        good, price = market_good[market], market_price[market]
        built = 0.0
        for position in range(rank_first[market], rank_first[market] + rank_count[market]):
            entry_price = rank_cost[position] * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
            wanted = demand_in_market(block, market_place[market], entry_price, price if price > 0.0 else entry_price) - built
            if wanted <= 0.0:
                break
            recipe = rank_recipe[position]
            made = outputs[recipe, good]
            runs = wanted * ENTRY_SHARE_OF_UNTRADED_DEMAND / made
            tile, runs = site_newcomer(recipe, good, market_anchor[market], runs, tables, siting, sites, of_good_tile,
                                       recipe_scalar[recipe, 1] > 0.0)
            if tile < 0:
                continue
            if runs > 0.0 and numpy.isfinite(runs):
                row = claim_row(plans)
                if row == NO_ROOM:
                    return -1
                plans.recipe_row[row] = recipe
                plans.tile_row[row] = tile
                plans.good_col[row] = good
                plans.runs[row] = runs
                plans.yearly_return[row] = ENTRY_PRICE_MARGIN_SHARE
                built += runs * made
    return plans.row_count[0]
