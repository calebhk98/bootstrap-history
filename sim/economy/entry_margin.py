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
from typing import Dict, List, Mapping, Sequence, Tuple

from sim.constants import declare

from .entry import EntryPlan, UnmetDemand
from .entry_trial import (ENTRY_PRICE_MARGIN_SHARE, capacity_in_area, capacity_terms_by_good, demand_at,
                          recipes_by_cost)
from .market_memory import market_key
from .producers import OUTPUT_CHANGE_SHARE_PER_YEAR
from .producers_close import LOSS_YEARS_BEFORE_EXIT
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


def added_output(gap: float, capacity: float) -> float:
    """What newcomers add in a year: a share of the gap, no more than the pace incumbents grow at."""
    return min(MARGIN_ENTRY_SHARE_OF_GAP * gap, MARGIN_ENTRY_GROWTH_SHARE * capacity)


def margin_entry_plans(setup, record, view, area_map, bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                       planned: Sequence[Tuple[GoodId, AreaId]] = (), siting=None) -> List[EntryPlan]:
    """Newcomers for each market with makers whose expected price has stood above its entry price for
    long enough: every recipe whose entry price is under the expected price, cheapest first, shares the
    year's growth. Keeps the market's streak in `record.margin_years`."""
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(setup.recipes):
        for good in setup.recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    skip = set(planned)
    capacity_terms = capacity_terms_by_good(record.producers, setup.recipes, record.expansion_runs)
    plans = []
    for (good, area_id), bids in sorted(bids_by_market.items()):
        if good not in makers or good not in area_map.goods():
            continue
        area = next((each for each in area_map.areas(good) if each.area_id == area_id), None)
        capacity = capacity_in_area(capacity_terms, good, area.tiles) if area is not None else 0.0
        if capacity <= 0.0:
            continue                                        # no maker: the trial newcomer's market
        key = market_key(good, area_id)
        price = view.price(good, area_id) or 0.0
        expected = record.memory.usual_prices.get(key, price)
        ranked = recipes_by_cost(setup, record, view, good, area.anchor_tile, makers[good])
        if not ranked:
            continue
        # the margin must be there in the smoothed price and in the year's price: entry that waited on the
        # smoothed price alone kept adding makers for years after the price had fallen to cost
        record.margin_years[key] = margin_streak(
            record.margin_years.get(key, 0), min(expected, price) if price > 0.0 else expected,
            ranked[0][1] * (1.0 + ENTRY_PRICE_MARGIN_SHARE))
        if (good, area_id) in skip or not margin_has_lasted(record.margin_years[key]):
            continue
        room = MARGIN_ENTRY_GROWTH_SHARE * capacity
        for recipe_id, cost in ranked:
            entry_price = cost * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
            if entry_price >= min(expected, price if price > 0.0 else expected) or room <= 0.0:
                break
            gap = gap_at_entry_price(bids, entry_price, price, capacity)
            added = min(MARGIN_ENTRY_SHARE_OF_GAP * gap, room)
            runs = added / setup.recipes[recipe_id].outputs[good]
            tile = area.anchor_tile
            if siting is not None and runs > 0.0:
                picked = siting(recipe_id, UnmetDemand(good, area_id, area.anchor_tile, added), runs)
                if picked is None:
                    continue
                tile, runs = picked
            if runs > 0.0 and math.isfinite(runs):
                plans.append(EntryPlan(recipe_id, tile, good, runs, (expected - cost) / cost))
                room -= runs * setup.recipes[recipe_id].outputs[good]
                capacity += runs * setup.recipes[recipe_id].outputs[good]
    return plans
