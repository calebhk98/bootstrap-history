"""A trial newcomer for a market with buyers and no maker in its area.

A market nobody makes for remembers a price nobody has sold at, so the ordinary entry rule (entry.py),
which judges a newcomer's return at that price, can wait for ever: Mexica's rich highland tiles went
hungry while no food maker came. Here a newcomer is judged at its own cost instead. The recipe with the
lowest full cost per unit (variable cost and the capital charge, a joint output's cost shared by value)
sets the entry price, that cost raised by ENTRY_PRICE_MARGIN_SHARE; where the year's bids would take
output at that price, a newcomer is built for a trial share of what they would take.

Entry drawn by a margin where makers already exist was tried and taken out: it made grain prices
swing (Complaints/reports/agent-economy-review-round-four.md).
"""
import math
from dataclasses import replace
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import unit_cost
from .entry import EntryPlan, UnmetDemand
from .entry_sizing import ENTRY_SHARE_OF_UNTRADED_DEMAND
from .producers import Producer, live_input_prices, live_wages
from .types import AreaId, Bid, GoodId, Recipe

ENTRY_PRICE_MARGIN_SHARE = declare(
    "ENTRY_PRICE_MARGIN_SHARE", 0.25, kind="temporary_heuristic",
    unit="share above full unit cost a trial newcomer expects to sell at", source=None, confidence="D",
    why="A founder starting a workshop nobody runs yet asks more than cost to cover the risk of an untried "
        "market (Dixit 1989, Complaints/reports/economy-research-price-stability-and-entry.md). The "
        "margin should follow the sunk cost and the uncertainty; neither is derived yet.")


def full_cost_per_unit(recipe: Recipe, good: GoodId, output_prices: Mapping[GoodId, float],
                       input_prices: Mapping[GoodId, float], wages: Mapping[str, float], rate: float,
                       rent: float = 0.0, yield_factor: float = 1.0) -> float:
    """Variable cost and capital charge of a run, per unit of `good`; a joint run's cost is shared among
    its outputs by value at `output_prices`. Infinite when a cost cannot be priced."""
    made = recipe.outputs.get(good, 0.0) * yield_factor
    if made <= 0.0:
        return math.inf
    run_cost = (unit_cost.variable_cost_per_run(recipe, input_prices, wages, rent)
                + unit_cost.capital_charge_per_run(recipe, input_prices, wages, rate))
    if not math.isfinite(run_cost):
        return math.inf
    revenue = unit_cost.revenue_per_run(recipe, output_prices)
    own_value = recipe.outputs[good] * output_prices.get(good, 0.0)
    share = own_value / revenue if revenue > 0.0 and own_value > 0.0 else 1.0
    return run_cost * share / made


def demand_at(bids: Sequence[Bid], price: float, price_now: float) -> float:
    """What the bids, made at `price_now`, would take at `price`. A bid's floor is needed whatever the
    price; the rest of its budget, beyond what the floor costs now, is spending a buyer shares out by
    budget, so it buys in inverse proportion to the price. A buyer's ceiling still holds."""
    total = 0.0
    for bid in bids:
        if bid.budget <= 0.0 or price > bid.maximum_price:
            continue
        surplus = max(0.0, bid.budget - bid.floor_quantity * price_now)
        total += bid.floor_quantity + surplus / price
    return total


def capacity_in_area(producers: Mapping[str, Producer], recipes: Mapping[str, Recipe], good: GoodId,
                     area_tiles, coming: Mapping[str, float]) -> float:
    """Output of `good` the makers on the area's tiles could reach, counting plant still to come."""
    tiles = set(area_tiles)
    total = 0.0
    for producer_id, producer in producers.items():
        made = recipes[producer.recipe_id].outputs.get(good, 0.0)
        if made > 0.0 and producer.tile in tiles:
            total += (producer.capacity_runs * producer.yield_factor + coming.get(producer_id, 0.0)) * made
    return total


def trial_entry_plans(setup, record, view, area_map, bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                      planned: Sequence[Tuple[GoodId, AreaId]] = (), siting=None) -> List[EntryPlan]:
    """At most one trial newcomer per market with bids and no maker in its area."""
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(setup.recipes):
        for good in setup.recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    skip = set(planned)
    plans = []
    for (good, area_id), bids in sorted(bids_by_market.items()):
        if (good, area_id) in skip or good not in makers or good not in area_map.goods():
            continue
        area = next((each for each in area_map.areas(good) if each.area_id == area_id), None)
        if area is None or capacity_in_area(record.producers, setup.recipes, good, area.tiles,
                                            record.expansion_runs) > 0.0:
            continue
        best = _cheapest(setup, record, view, good, area.anchor_tile, makers[good])
        if best is None:
            continue
        recipe_id, cost = best
        entry_price = cost * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
        price = view.price(good, area_id)
        # a household's ceiling comes from what substitutes are remembered to cost; in a market nobody
        # makes for, those memories are as stale as its own, so only its budget bounds the trial. Other
        # buyers' ceilings (what an input is worth to a run, a cargo to its destination) stand.
        wanted = demand_at([replace(bid, maximum_price=math.inf) if bid.buyer in record.cohorts else bid
                            for bid in bids], entry_price, price if price and price > 0.0 else entry_price)
        if wanted <= 0.0:
            continue
        added = wanted * ENTRY_SHARE_OF_UNTRADED_DEMAND
        runs = added / setup.recipes[recipe_id].outputs[good]
        tile = area.anchor_tile
        if siting is not None:
            picked = siting(recipe_id, UnmetDemand(good, area_id, area.anchor_tile, added), runs)
            if picked is None:
                continue
            tile, runs = picked
        if runs > 0.0 and math.isfinite(runs):
            plans.append(EntryPlan(recipe_id, tile, good, runs, ENTRY_PRICE_MARGIN_SHARE))
    return plans


def _cheapest(setup, record, view, good, tile, recipe_ids) -> Optional[Tuple[str, float]]:
    rate = view.interest_rate(setup.currency_id)
    best = None
    for recipe_id in recipe_ids:
        recipe = setup.recipes[recipe_id]
        probe = Producer("probe", "probe", recipe_id, tile, 1.0)
        outputs = {each: view.price(each, view.area_of(each, tile)) for each in recipe.outputs}
        outputs = {each: price for each, price in outputs.items() if price is not None}
        rent = record.land_rent.get(tile, 0.0) * setup.land_per_run.get(recipe_id, 0.0)
        cost = full_cost_per_unit(recipe, good, outputs, live_input_prices(probe, recipe, view),
                                  live_wages(probe, recipe, view), rate, rent)
        if math.isfinite(cost) and cost > 0.0 and (best is None or cost < best[1]):
            best = (recipe_id, cost)
    return best
