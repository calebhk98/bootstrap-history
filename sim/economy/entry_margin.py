"""Newcomers drawn by a lasting margin. Once sellers raise their asks until they sell, buyers are no longer
turned away (entry.py goes quiet) while a market whose makers are few sells far above what its cheapest
known recipe costs. Here such a market gains makers, on the price people expect rather than the one they
saw: the market's usual (smoothed) price against the entry price, the cheapest recipe's full cost raised
by ENTRY_PRICE_MARGIN_SHARE. A harvest's spike barely moves a usual price, and the usual price must stay
above the entry price for as many years in a row as a losing producer waits before it exits, so entry and
exit wait alike.

The gap is what the year's bids would take at the entry price less the capacity there and coming (a
floor stays a floor; only spending beyond it grows as the price falls). Newcomers fill a share of it, at
most the pace at which incumbents change their own output, so grain and other staples do not swing
(Complaints/reports/agent-economy-review-round-four.md). The cost counts land rent (location rent at the
recipe's tile) and the capital charge. A market with no maker at all is entry_trial.py's.
"""
import math
from typing import Dict, List, Mapping, Sequence, Set, Tuple

import numpy

from sim.constants import declare

from . import year_bids
from .entry import EntryPlan, UnmetDemand
from .entry_bid_markets import makers_of, weigh
from .goods_market_column import MarketColumn
from .entry_trial import ENTRY_PRICE_MARGIN_SHARE, demand_at, reachable_capacity, recipes_by_cost, recipes_by_cost_many
from .market_memory import market_key
from .producers import OUTPUT_CHANGE_SHARE_PER_YEAR
from .producers_close import LOSS_YEARS_BEFORE_EXIT
from .stock_residue import STOCK_RESIDUE_UNITS
from .types import AreaId, Bid, GoodId

MARGIN_ENTRY_SHARE_OF_GAP = declare(
    "MARGIN_ENTRY_SHARE_OF_GAP", 0.5, kind="temporary_heuristic",
    unit="share of the gap between demand at the entry price and capacity newcomers are built for a year",
    source=None, confidence="D",
    why="Several founders see the same gap and each expects the others to take part of it; free entry "
        "overshoots when each acts on the whole (Mankiw and Whinston 1986). How much of a gap one "
        "year's founders fill is not measured.")
# newcomers drawn by a margin add at most the pace at which a producer can change its own output a year,
# so entry and growth are held to one speed
MARGIN_ENTRY_GROWTH_SHARE = OUTPUT_CHANGE_SHARE_PER_YEAR


def margin_streak(years: int, expected_price: float, entry_price: float) -> int:
    """Years in a row the expected price has stood above the entry price, after this year."""
    return years + 1 if expected_price > entry_price else 0


def margin_has_lasted(years: int) -> bool:
    return years >= LOSS_YEARS_BEFORE_EXIT


def gap_at_entry_price(bids: Sequence[Bid], entry_price: float, price_now: float, capacity: float) -> float:
    """What the bids would take at the entry price beyond the output makers can reach."""
    return max(0.0, demand_at(bids, entry_price, price_now if price_now > 0.0 else entry_price) - capacity)


def keep_streaks(record, kept: Dict[str, int]) -> None:
    """`record.goods.margin_years` holds the streaks of `kept` (market key -> years) and no other market's: a market not weighed this year
    starts its wait again. The column (or dictionary) is changed in place."""
    margin_years = record.goods.margin_years
    if isinstance(margin_years, MarketColumn):
        margin_years.replace_rows(margin_years.rows_of(list(kept)), numpy.array(list(kept.values()), dtype=numpy.float64))
        return
    for key in [key for key in margin_years if key not in kept]:
        del margin_years[key]
    margin_years.update(kept)


def margin_entry_plans(setup, record, view, area_map, bids_by_market, planned: Sequence[Tuple[GoodId, AreaId]] = (), siting=None, costs=None,
                       weighed=None) -> List[EntryPlan]:
    """Newcomers for each market with makers whose expected price has stood above its entry price for
    long enough: every recipe whose entry price is under the expected price, cheapest first, shares the
    year's growth. Keeps the market's streak in `record.goods.margin_years`; a market with no maker, no costable recipe, no price or no bids this year loses its streak.
    With `costs` (entry_tables.EntryTables) the recipes of all the markets are costed at once. `bids_by_market` is the year's bids block
    (`year_bids.YearBids`) or a mapping of market to bids; `weighed` the block's markets as `entry_bid_markets.weigh` made them (made here when
    not given). The demands at every entry price a market could reach are worked out first in one call (they do not depend on the plans
    made); the plans are then taken market by market in order."""
    block = year_bids.of(bids_by_market)
    makers = makers_of(setup.recipes)
    skip = set(planned)
    if weighed is None:
        weighed = weigh(block, makers, area_map, view, reachable_capacity(record, setup, costs))
    markets = []
    for each in weighed:
        key = market_key(each.good, each.area_id)
        if each.capacity <= 0.0 or each.price is None:       # no maker: the trial newcomer's market; or no price
            record.goods.margin_years.pop(key, None)
            continue
        markets.append(each)
    ranked_all = recipes_by_cost_many(setup, record, view, [(each.good, each.area.anchor_tile, makers[each.good],
                                                            MARGIN_ENTRY_GROWTH_SHARE * each.capacity) for each in markets], costs, recipes_by_cost)
    counted: Set[str] = set()
    reached = []            # (market, expected price, [(recipe id, cost)] the market's price would let in, where its questions start)
    places, prices, prices_now = [], [], []
    for each, ranked in zip(markets, ranked_all):
        key = market_key(each.good, each.area_id)
        price = each.price
        expected = record.memory.usual_prices.get(key, price)
        if not ranked:
            record.goods.margin_years.pop(key, None)
            continue
        counted.add(key)
        # the margin must be there in the smoothed price and in the year's price: entry that waited on the
        # smoothed price alone kept adding makers for years after the price had fallen to cost
        record.goods.margin_years[key] = margin_streak(
            record.goods.margin_years.get(key, 0), min(expected, price) if price > 0.0 else expected,
            ranked[0][1] * (1.0 + ENTRY_PRICE_MARGIN_SHARE))
        if (each.good, each.area_id) in skip or not margin_has_lasted(record.goods.margin_years[key]):
            continue
        ceiling = min(expected, price if price > 0.0 else expected)
        entries = []
        for recipe_id, cost in ranked:
            entry_price = cost * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
            if entry_price >= ceiling:
                break
            entries.append((recipe_id, cost))
            places.append(each.place)
            prices.append(entry_price)
            prices_now.append(price if price > 0.0 else entry_price)
        reached.append((each, expected, entries, len(places) - len(entries)))
    demands = block.demand_at_many(places, prices, prices_now).tolist()
    plans = []
    for each, expected, entries, asked in reached:
        capacity = each.capacity
        room = MARGIN_ENTRY_GROWTH_SHARE * capacity
        for recipe_id, cost in entries:
            if room <= 0.0:
                break
            gap = max(0.0, demands[asked] - capacity)
            asked += 1
            added = min(MARGIN_ENTRY_SHARE_OF_GAP * gap, room)
            runs = added / setup.recipes[recipe_id].outputs[each.good]
            tile = each.area.anchor_tile
            if siting is not None and runs > 0.0:
                picked = siting(recipe_id, UnmetDemand(each.good, each.area_id, each.area.anchor_tile, added), runs)
                if picked is None:
                    continue
                tile, runs = picked
            if runs * setup.recipes[recipe_id].outputs[each.good] >= STOCK_RESIDUE_UNITS and math.isfinite(runs):      # residue size is no entrant
                plans.append(EntryPlan(recipe_id, tile, each.good, runs, (expected - cost) / cost))
                room -= runs * setup.recipes[recipe_id].outputs[each.good]
                capacity += runs * setup.recipes[recipe_id].outputs[each.good]
    for key in set(record.goods.margin_years) - counted:     # a market that was not weighed this year starts its wait again
        del record.goods.margin_years[key]
    return plans
