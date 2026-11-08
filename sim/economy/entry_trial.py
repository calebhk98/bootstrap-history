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
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import bid_columns, entry_practice, unit_cost
from .entry import EntryPlan, UnmetDemand
from .entrant_rent import site_rent_per_run
from .entry_sizing import ENTRY_SHARE_OF_UNTRADED_DEMAND
from .producers import Producer, live_input_prices_at, live_wages_at
from .types import AreaId, Bid, GoodId, Recipe
from .rates import own_rate

ENTRY_PRICE_MARGIN_SHARE = declare(
    "ENTRY_PRICE_MARGIN_SHARE", 0.25, kind="temporary_heuristic",
    unit="share above full unit cost a trial newcomer expects to sell at", source=None, confidence="D",
    why="A founder starting a workshop nobody runs yet asks more than cost to cover the risk of an untried "
        "market (Dixit 1989, Complaints/reports/economy-research-price-stability-and-entry.md). The "
        "margin should follow the sunk cost and the uncertainty; neither is derived yet.")


def demand_at(bids: Sequence[Bid], price: float, price_now: float) -> float:
    """What the bids, made at `price_now`, would take at `price`. A bid's floor is needed whatever the
    price; the rest of its budget, beyond what the floor costs now, is spending a buyer shares out by
    budget, so it buys in inverse proportion to the price, up to what the bid's own schedule would take there
    (`flexible_quantity`; a buyer with none takes its floor and no more, however cheap the good). A buyer's
    ceiling still holds."""
    return bid_columns.demand_at(bid_columns.columns_of(bids), price, price_now)


def capacity_terms_by_good(producers: Mapping[str, Producer], recipes: Mapping[str, Recipe],
                           coming: Mapping[str, float]) -> Dict[GoodId, List[Tuple[str, float]]]:
    """Per good, each maker's (tile, reachable output of the good) in producer id order, plant to come counted."""
    terms: Dict[GoodId, List[Tuple[str, float]]] = {}
    for producer_id, producer in sorted(producers.items()):
        for good, made in recipes[producer.recipe_id].outputs.items():
            if made > 0.0:
                terms.setdefault(good, []).append(
                    (producer.tile,
                     (producer.capacity_runs * producer.yield_factor + coming.get(producer_id, 0.0)) * made))
    return terms


def capacity_in_area(terms: Mapping[GoodId, Sequence[Tuple[str, float]]], good: GoodId, area_tiles) -> float:
    """Output of `good` the makers on the area's tiles could reach (terms: capacity_terms_by_good)."""
    tiles = set(area_tiles)
    total = 0.0
    for tile, term in terms.get(good, ()):
        if tile in tiles:
            total += term
    return total


def reachable_capacity(record, setup, costs=None):
    """`f(good, area)`: the output of `good` the makers on the market area's tiles could reach, plant to come counted
    (`capacity_in_area` of `capacity_terms_by_good`); with `costs` (entry_tables.EntryTables) read from the year's arrays."""
    if costs is not None:
        in_area = costs.capacity_in()
        return lambda good, area: in_area(good, area.area_id)
    terms = capacity_terms_by_good(record.producers, setup.recipes, record.credit.expansion_runs)
    return lambda good, area: capacity_in_area(terms, good, area.tiles)


def trial_entry_plans(setup, record, view, area_map, bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                      planned: Sequence[Tuple[GoodId, AreaId]] = (), siting=None, costs=None) -> List[EntryPlan]:
    """Trial newcomers for each market with bids and no maker in its area: every recipe whose entry price
    the bids would still take output at, cheapest first, each for a share of what the cheaper ones leave. With `costs`
    (entry_tables.EntryTables) the recipes are costed for all the markets at once."""
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(setup.recipes):
        for good in setup.recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    skip = set(planned)
    capacity_in = reachable_capacity(record, setup, costs)
    areas_of: Dict[GoodId, Dict[AreaId, object]] = {}
    known_goods = set(area_map.goods())
    markets = []
    for (good, area_id), bids in sorted(bids_by_market.items()):
        if (good, area_id) in skip or good not in makers or good not in known_goods:
            continue
        if good not in areas_of:
            areas_of[good] = {each.area_id: each for each in area_map.areas(good)}
        area = areas_of[good].get(area_id)
        if area is None or capacity_in(good, area) > 0.0:
            continue
        markets.append((good, area_id, bids, area, view.price(good, area_id)))
    booked_all = recipes_by_cost_many(setup, record, view, [(good, area.anchor_tile, makers[good], None)
                                                           for good, _area_id, _bids, area, _price in markets], costs)
    # the newcomers' learning is judged on the trial share of what the bids take at the price now, or at the
    # cheapest booked cost's entry price where nothing has sold
    trial_markets, trial_requests = [], []
    for market, booked in zip(markets, booked_all):
        if not booked:
            continue
        good, _area_id, bids, area, price = market
        reference = price if price and price > 0.0 else booked[0][1] * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
        trial_markets.append(market)
        trial_requests.append((good, area.anchor_tile, makers[good], ENTRY_SHARE_OF_UNTRADED_DEMAND * demand_at(bids, reference, reference)))
    plans = []
    for (good, area_id, bids, area, price), ranked in zip(trial_markets, recipes_by_cost_many(setup, record, view, trial_requests, costs)):
        built = 0.0
        for recipe_id, cost in ranked:
            entry_price = cost * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
            wanted = demand_at(bids, entry_price, price if price and price > 0.0 else entry_price) - built
            if wanted <= 0.0:
                break
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
                built += runs * setup.recipes[recipe_id].outputs[good]
    return plans


def recipes_by_cost_many(setup, record, view, requests, costs=None, single=None) -> List[List[Tuple[str, float]]]:
    """`recipes_by_cost` (or `single`) for each (good, tile, recipe ids, output a year or None); with `costs`
    (entry_tables.EntryTables) in one pass over the year's arrays."""
    if costs is not None:
        return costs.recipes_by_cost_many(requests)
    single = recipes_by_cost if single is None else single
    return [single(setup, record, view, *request) for request in requests]


def recipes_by_cost(setup, record, view, good, tile, recipe_ids,
                    output_per_year: Optional[float] = None, costs=None) -> List[Tuple[str, float]]:
    """(recipe, full cost per unit of `good`) for each recipe that can be costed, cheapest first. With `output_per_year`
    (units of `good` a newcomer would make a year) a recipe is costed at the hours its newcomer needs over the years it
    is judged on (entry_practice.py); without, at the booked hours. With `costs` (entry_tables.EntryTables) the
    same rule is read from the year's arrays."""
    if costs is not None:
        return costs.recipes_by_cost(good, tile, recipe_ids, output_per_year)
    rate = own_rate(view, setup.currency_id)
    ranked = []
    for recipe_id in recipe_ids:
        recipe = setup.recipes[recipe_id]
        if output_per_year is not None and recipe.outputs.get(good, 0.0) > 0.0:
            recipe = entry_practice.planned_recipe(recipe, entry_practice.crews_of_recipe(record.producers)(recipe_id),
                                                   output_per_year / recipe.outputs[good])
        outputs = {each: view.price(each, view.area_of(each, tile)) for each in recipe.outputs}
        outputs = {each: price for each, price in outputs.items() if price is not None}
        rent = site_rent_per_run(setup, record, view, recipe_id, tile)
        cost = unit_cost.full_cost_per_unit(recipe, good, outputs, live_input_prices_at(tile, recipe, view),
                                            live_wages_at(tile, recipe, view), rate, rent)
        if math.isfinite(cost) and cost > 0.0:
            ranked.append((recipe_id, cost))
    return sorted(ranked, key=lambda item: (item[1], item[0]))
