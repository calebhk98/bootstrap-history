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

from . import entry_practice, unit_cost
from .entry import EntryPlan, UnmetDemand
from .entrant_rent import site_rent_per_run
from .entry_sizing import ENTRY_SHARE_OF_UNTRADED_DEMAND
from .producers import Producer, live_input_prices_at, live_wages_at
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
    budget, so it buys in inverse proportion to the price, up to what the bid's own schedule would take there
    (`flexible_quantity`; a buyer with none takes its floor and no more, however cheap the good). A buyer's
    ceiling still holds."""
    total = 0.0
    for bid in bids:
        if bid.budget <= 0.0 or price > bid.maximum_price:
            continue
        surplus = max(0.0, bid.budget - bid.floor_quantity * price_now)
        reach = bid.flexible_quantity * math.exp(min(700.0, -bid.elasticity * math.log(price / bid.reference_price))) \
            if bid.flexible_quantity > 0.0 and bid.reference_price > 0.0 and price > 0.0 else 0.0
        total += bid.floor_quantity + min(surplus / price, reach)
    return total


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


def trial_entry_plans(setup, record, view, area_map, bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                      planned: Sequence[Tuple[GoodId, AreaId]] = (), siting=None) -> List[EntryPlan]:
    """Trial newcomers for each market with bids and no maker in its area: every recipe whose entry price
    the bids would still take output at, cheapest first, each for a share of what the cheaper ones leave."""
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(setup.recipes):
        for good in setup.recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    skip = set(planned)
    capacity_terms = capacity_terms_by_good(record.producers, setup.recipes, record.expansion_runs)
    plans = []
    for (good, area_id), bids in sorted(bids_by_market.items()):
        if (good, area_id) in skip or good not in makers or good not in area_map.goods():
            continue
        area = next((each for each in area_map.areas(good) if each.area_id == area_id), None)
        if area is None or capacity_in_area(capacity_terms, good, area.tiles) > 0.0:
            continue
        price = view.price(good, area_id)
        built = 0.0
        booked = recipes_by_cost(setup, record, view, good, area.anchor_tile, makers[good])
        if not booked:
            continue
        # the newcomers' learning is judged on the trial share of what the bids take at the price now, or at the
        # cheapest booked cost's entry price where nothing has sold
        reference = price if price and price > 0.0 else booked[0][1] * (1.0 + ENTRY_PRICE_MARGIN_SHARE)
        trial_output = ENTRY_SHARE_OF_UNTRADED_DEMAND * demand_at(bids, reference, reference)
        for recipe_id, cost in recipes_by_cost(setup, record, view, good, area.anchor_tile, makers[good], trial_output):
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


def recipes_by_cost(setup, record, view, good, tile, recipe_ids,
                    output_per_year: Optional[float] = None) -> List[Tuple[str, float]]:
    """(recipe, full cost per unit of `good`) for each recipe that can be costed, cheapest first. With `output_per_year`
    (units of `good` a newcomer would make a year) a recipe is costed at the hours its newcomer needs over the years it
    is judged on (entry_practice.py); without, at the booked hours."""
    rate = view.interest_rate(setup.currency_id)
    ranked = []
    for recipe_id in recipe_ids:
        recipe = setup.recipes[recipe_id]
        if output_per_year is not None and recipe.outputs.get(good, 0.0) > 0.0:
            recipe = entry_practice.planned_recipe(recipe, entry_practice.crews_of_recipe(record.producers)(recipe_id),
                                                   output_per_year / recipe.outputs[good])
        outputs = {each: view.price(each, view.area_of(each, tile)) for each in recipe.outputs}
        outputs = {each: price for each, price in outputs.items() if price is not None}
        rent = site_rent_per_run(setup, record, view, recipe_id, tile)
        cost = full_cost_per_unit(recipe, good, outputs, live_input_prices_at(tile, recipe, view),
                                  live_wages_at(tile, recipe, view), rate, rent)
        if math.isfinite(cost) and cost > 0.0:
            ranked.append((recipe_id, cost))
    return sorted(ranked, key=lambda item: (item[1], item[0]))
