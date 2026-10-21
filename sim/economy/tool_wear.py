"""The tools a trade's workers wear out, as a demand for goods.

A trade's data states the tool stock a worker keeps in use and the goods' service lives; the port turns
those into `wear_per_hour` (units worn out per hour worked, by trade and good). An employer's recipe then
carries the wear of the hours it hires as an ordinary input (`with_tool_wear`), bought on the goods market
and booked like any other input. A household working its own plot holds the stock it works with as a
durable (`tool_bids`): it buys what wore out and what is short of the stock the hours need. Nothing here
names a good or a trade.
"""
import dataclasses
import math
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .types import Bid, GoodId, GoodSpec, Recipe, ToolFallback, TradeId

TOOL_BID_PRICE_MARGIN = 0.25      # budget set aside above last year's price, as for a household's floors

WearPerHour = Mapping[TradeId, Mapping[GoodId, float]]


def with_tool_wear(recipe: Recipe, wear_per_hour: WearPerHour, makeable: Iterable[GoodId],
                   order: Optional[Mapping[TradeId, Sequence[GoodId]]] = None,
                   hours_factors: Optional[Mapping[TradeId, Tuple[Mapping[GoodId, float], float]]] = None) -> Recipe:
    """`recipe` with the tools its hired hours wear added to its inputs (and listed in `tool_wear`). A tool
    nothing in the society makes is not charged, and a recipe never wears the tool it makes. With `order` (a
    trade's tool goods, first choice first) a trade wears the first it can have made; the later ones it can have
    made are the recipe's `tool_fallbacks` for that tool, each with the extra hours it asks, and then working by
    hand. `hours_factors` is {trade: (hours factor by tool good, hours factor by hand)}. Without `order` every
    good with a wear is its own tool."""
    makeable = frozenset(makeable)
    hours_factors = hours_factors or {}
    wear: Dict[GoodId, float] = {}
    backups: Dict[GoodId, Dict[GoodId, List[Tuple[float, float, TradeId]]]] = {}
    by_hand: Dict[GoodId, List[Tuple[float, float, TradeId]]] = {}
    for trade, hours in recipe.labour_hours.items():
        rates = wear_per_hour.get(trade, {})
        goods = [good for good in (order.get(trade, ()) if order is not None else sorted(rates)) if good in makeable]
        if order is None:
            goods = [good for good in goods if rates.get(good, 0.0) > 0.0]
            chain = [[good] for good in goods]
        else:
            chain = [goods] if goods else []
        for tools in chain:
            first = tools[0]
            if rates.get(first, 0.0) <= 0.0 or first in recipe.outputs:
                continue
            wear[first] = wear.get(first, 0.0) + hours * rates[first]
            factor_by_good, factor_by_hand = hours_factors.get(trade, ({}, 1.0))
            for later in tools[1:]:
                if rates.get(later, 0.0) > 0.0 and later not in recipe.outputs:
                    backups.setdefault(first, {}).setdefault(later, []).append(
                        (hours * rates[later], factor_by_good.get(later, 1.0), trade))
            by_hand.setdefault(first, []).append((hours, factor_by_hand, trade))
    if not wear:
        return recipe
    inputs = dict(recipe.inputs)
    for good, quantity in wear.items():
        inputs[good] = inputs.get(good, 0.0) + quantity
    fallbacks = {}
    for first in wear:
        rows = [_fallback(later, rows_of, recipe) for later, rows_of in backups.get(first, {}).items()]
        if order is not None:
            rows.append(_fallback("", [(hours, factor, trade) for hours, factor, trade in by_hand[first]], recipe, by_hand=True))
        fallbacks[first] = tuple(rows)
    return dataclasses.replace(recipe, inputs=inputs, tool_wear=wear, tool_fallbacks=fallbacks if order is not None else {})


def _fallback(good: GoodId, rows: List[Tuple[float, float, TradeId]], recipe: Recipe, by_hand: bool = False) -> ToolFallback:
    """One fallback tier: units a run (by hand draws none), and the hours factor of the trades that wear the tool,
    weighted by their hours."""
    trades = tuple(sorted({trade for _quantity, _factor, trade in rows}))
    hours = math.fsum(recipe.labour_hours[trade] for trade in trades)
    factor = math.fsum(recipe.labour_hours[trade] * factor for _quantity, factor, trade in rows) / hours if hours > 0.0 else 1.0
    units = 0.0 if by_hand else math.fsum(quantity for quantity, _factor, _trade in rows)
    return ToolFallback(good, units, factor, trades)


def tool_stock_wanted(recipe: Recipe, hours: float, specs: Mapping[GoodId, GoodSpec]) -> Dict[GoodId, float]:
    """The tools kept in use to work `hours` of the recipe a year: the wear of those hours over a service life."""
    run_hours = sum(recipe.labour_hours.values())
    if hours <= 0.0 or run_hours <= 0.0:
        return {}
    wanted = {}
    for good, per_run in recipe.tool_wear.items():
        spec = specs.get(good)
        if spec is not None and spec.service_life_years > 0.0:
            wanted[good] = per_run * hours / run_hours * spec.service_life_years
    return wanted


def tool_bids(buyer, tile, area_of, price_of, held_of, recipes: Mapping[str, Recipe], hours_by_recipe: Mapping[str, float],
              specs: Mapping[GoodId, GoodSpec], cash: float) -> List[Bid]:
    """A household's bids for the tools its own-plot hours wear: the stock the hours keep in use, less what it
    holds after this year's wear (the durable rule). `area_of(good)`, `price_of(good)` (last year's, or None)
    and `held_of(good)` read the market and the household's holdings. Budgets sum to no more than `cash`."""
    wanted: Dict[GoodId, float] = {}
    for recipe_id, hours in sorted(hours_by_recipe.items()):
        for good, stock in tool_stock_wanted(recipes[recipe_id], hours, specs).items():
            wanted[good] = wanted.get(good, 0.0) + stock
    rows = []
    for good, stock in sorted(wanted.items()):
        price = price_of(good)
        if price is None or price <= 0.0:
            continue
        held = held_of(good)
        wear = held * min(1.0, 1.0 / specs[good].service_life_years)
        quantity = max(0.0, stock - held + wear)
        if quantity > 0.0:
            rows.append((good, quantity, price))
    wanted_cash = sum(quantity * price * (1.0 + TOOL_BID_PRICE_MARGIN) for _good, quantity, price in rows)
    scale = min(1.0, max(0.0, cash) / wanted_cash) if wanted_cash > 0.0 else 0.0
    return [Bid(buyer, good, area_of(good), tile, quantity, 0.0, price, 0.0,
                quantity * price * (1.0 + TOOL_BID_PRICE_MARGIN) * scale)
            for good, quantity, price in rows if scale > 0.0]
