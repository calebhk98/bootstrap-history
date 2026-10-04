"""Newcomers drawn by a margin. Where a good sells well above what its cheapest known recipe costs to
make it, more makers come in even though no buyer was turned away at that price: they expect to sell at
a lower price, to the buyers last year's bids show would take more there. Without this a market whose
makers are few stays a monopoly at whatever price its thin buying will bear (Complaint 398).

For each market with bids, the recipe with the lowest full cost per unit of the good (variable cost and
the capital charge, a joint output's cost shared by value) sets the entry price: that cost raised by
ENTRY_PRICE_MARGIN_SHARE, the band a margin must clear before founders risk a new workshop (Dixit 1989:
entry needs more than cost, so prices inside the band move nobody). Where last year's price is above the
entry price, the gap is what the year's bids would take at the entry price less the area's makers'
capacity, plant on the way included. Newcomers are built for a share of the gap, at most a share of the
capacity already there in a year, so an industry grows fast but does not jump past its buyers.
"""
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import unit_cost
from .entry import EntryPlan, UnmetDemand
from .entry_sizing import ENTRY_SHARE_OF_UNTRADED_DEMAND
from .goods_market import quantity_at
from .producers import Producer, live_input_prices, live_wages
from .types import AreaId, Bid, GoodId, Recipe

ENTRY_PRICE_MARGIN_SHARE = declare(
    "ENTRY_PRICE_MARGIN_SHARE", 0.25, kind="temporary_heuristic",
    unit="share above full unit cost the price must exceed before newcomers enter", source=None,
    confidence="D",
    why="Starting a workshop is a sunk cost and prices are uncertain, so founders wait for a margin "
        "beyond the cost of making the good (Dixit 1989, Complaints/reports/economy-research-price-"
        "stability-and-entry.md). The width should follow the sunk cost and the volatility of the "
        "price; neither is derived yet, so one share for every recipe.")
MARGIN_ENTRY_SHARE_OF_GAP = declare(
    "MARGIN_ENTRY_SHARE_OF_GAP", 0.5, kind="temporary_heuristic",
    unit="share of the gap between demand at the entry price and capacity newcomers are built for a year",
    source=None, confidence="D",
    why="Several founders see the same gap and each expects the others to take part of it; free entry "
        "overshoots when each acts on the whole (Mankiw and Whinston 1986). How much of a gap one "
        "year's founders fill is not measured.")
MARGIN_ENTRY_GROWTH_SHARE = declare(
    "MARGIN_ENTRY_GROWTH_SHARE", 0.5, kind="temporary_heuristic",
    unit="most capacity newcomers drawn by a margin add in a year, as a share of the area's capacity",
    source=None, confidence="D",
    why="New workshops need hands trained, tools made and customers found, so an industry grows by a "
        "share of what it already is; the share follows how fast skills and tools spread, which is "
        "not modelled.")


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


def demand_at(bids: Sequence[Bid], price: float) -> float:
    return math.fsum(quantity_at(bid, price) for bid in bids)


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


def margin_entry_plans(setup, record, view, area_map, bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                       planned: Sequence[Tuple[GoodId, AreaId]] = (), siting=None) -> List[EntryPlan]:
    """At most one newcomer per market whose price is above its cheapest recipe's entry price."""
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(setup.recipes):
        for good in setup.recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    skip = set(planned)
    plans = []
    for (good, area_id), bids in sorted(bids_by_market.items()):
        if (good, area_id) in skip or good not in makers or good not in area_map.goods():
            continue
        price = view.price(good, area_id)
        area = next((each for each in area_map.areas(good) if each.area_id == area_id), None)
        if price is None or price <= 0.0 or area is None:
            continue
        best = _cheapest(setup, record, view, good, area.anchor_tile, makers[good])
        if best is None:
            continue
        recipe_id, cost = best
        entry_price = cost * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
        if price <= entry_price:
            continue
        capacity = capacity_in_area(record.producers, setup.recipes, good, area.tiles, record.expansion_runs)
        gap = demand_at(bids, entry_price) - capacity
        if gap <= 0.0:
            continue
        added = gap * MARGIN_ENTRY_SHARE_OF_GAP
        added = min(added, MARGIN_ENTRY_GROWTH_SHARE * capacity) if capacity > 0.0 else gap * ENTRY_SHARE_OF_UNTRADED_DEMAND
        runs = added / setup.recipes[recipe_id].outputs[good]
        tile = area.anchor_tile
        if siting is not None:
            picked = siting(recipe_id, UnmetDemand(good, area_id, area.anchor_tile, added), runs)
            if picked is None:
                continue
            tile, runs = picked
        if runs > 0.0 and math.isfinite(runs):
            plans.append(EntryPlan(recipe_id, tile, good, runs, (price - cost) / cost))
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
