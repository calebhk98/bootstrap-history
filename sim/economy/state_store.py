"""A state's wealth in durable stores: the cash it keeps beyond its plan and its reserve goes partly into
the goods households hold as wealth, chosen and split by the same rule (`households_store`). Nothing
here names a good."""
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from . import households_basket, households_store
from .types import Bid, Offer


@dataclass(frozen=True)
class Treasury:
    """What the store rule reads of a holder: who it is, where it keeps goods, what it expects of prices."""
    agent_id: str
    tile: str
    expected_inflation: float


def orders(setup, record, view) -> Tuple[List[Bid], List[Offer], Dict[str, float]]:
    """(bids, offers, quantity kept by good) for the state's store this year. Bids spend the cash left
    unplanned; offers sell the excess over the target and, in a deficit, enough to meet it. The kept
    stock is what the state's other lines must leave alone."""
    budget, state, tile = record.state_budget, setup.state_agent, setup.capital_tile
    basket = setup.basket_for(tile)
    priced = households_basket.need_prices(basket, view, tile)
    holder = Treasury(state, tile, budget.expected_inflation)
    weights, prices, held = households_store.store_holding(holder, view, setup.specs, priced)
    if not weights:
        return [], [], {}
    money = setup.currency_id
    cash = record.book.balance(state, money)
    real_rate = view.interest_rate(money) - holder.expected_inflation
    store_value = math.fsum(held[good] * prices[good] for good in weights)
    above_buffer = budget.unplanned_cash + store_value
    bids, _spend = households_store.store_bids(holder, view, setup.specs, basket, weights, prices, held,
                                               above_buffer, real_rate, budget.unplanned_cash)
    offers = households_store.store_offers(holder, view, setup.specs, weights, prices, held, above_buffer,
                                           real_rate, cash, cash + budget.deficit)
    return bids, offers, {good: quantity for good, quantity in held.items() if quantity > 0.0}
