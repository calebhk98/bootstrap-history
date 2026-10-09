"""The actors' sales and purchases as orders in the agent economy's book. Part of the port (it imports `sim.economy.api`).

A firm's or a state's `market_sale` and `market_purchase` are noted through the year as plain dicts (kept in the
agent economy's stored record, so a save carries them). When the economy's year runs they become orders:

- a sale: the goods enter an account named for the seller and are offered at the lowest price the seller takes;
  after the clear the money the account holds is the seller's proceeds, and what did not sell goes back out;
- a purchase: the buyer's coin is turned into the economy's unit and held in an account named for the buyer as the
  budget of a bid for a fixed quantity; after the clear the goods it got are used up and the unspent budget returns.

The actors' coin and the economy's unit are two currencies of one book; they meet at `edge:exchange`, at the
opening wage that fixes the unit (`coin_per_unit`).
"""
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from sim.economy import api as economy_api
from sim.economy.api import (EDGE_CONSUMPTION, EDGE_EXCHANGE, EDGE_LEGACY, AgentOrders, Bid, GoodsMove, Offer,
                             Transfer)

SALE_PREFIX, BUY_PREFIX = "sale:", "buy:"


def note_sale(sales: List[dict], seller: str, material: str, tonnes: float,
              from_concerns: Optional[Sequence[Tuple[str, float]]]) -> None:
    """A seller's tonnes of a material for the year; the same seller and material join into one."""
    if tonnes <= 0.0:
        return
    for sale in sales:
        if sale["seller"] == seller and sale["material"] == material:
            sale["tonnes"] += tonnes
            sale["concerns"] = (sale["concerns"] or []) + [list(each) for each in (from_concerns or [])]
            return
    sales.append({"seller": seller, "material": material, "tonnes": float(tonnes),
                  "concerns": [list(each) for each in (from_concerns or [])]})


def note_purchase(purchases: List[dict], buyer: str, commodity: str, tonnes: float, budget: float) -> None:
    """A buyer's tonnes of a commodity for the year, with the coin it sets aside for them."""
    if tonnes <= 0.0 or budget <= 0.0:
        return
    for purchase in purchases:
        if purchase["buyer"] == buyer and purchase["commodity"] == commodity:
            purchase["tonnes"] += tonnes
            purchase["budget"] += budget
            return
    purchases.append({"buyer": buyer, "commodity": commodity, "tonnes": float(tonnes), "budget": float(budget)})


def sale_account(seller: str) -> str:
    return SALE_PREFIX + seller


def buy_account(buyer: str) -> str:
    return BUY_PREFIX + buyer


def good_for(economy, commodity: str, materials_in: Callable[[str], Sequence[str]]) -> Optional[str]:
    """The good of the economy a commodity is bought as: the first material of the commodity it trades."""
    traded = set(economy.area_map.goods())
    return next((material for material in materials_in(commodity) if material in traded), None)


def sale_orders(economy, sales: Sequence[dict], tonnes_per_unit: Callable[[str], float],
                tile_of: Callable[[str], str], reservation_of: Callable[[str, str, str, str], float]):
    """(goods moves, {account: AgentOrders}) that put the year's sales in the book. A seller's reservation for a
    material is the tonnes-weighted mean of what its concerns cost it to make a unit (`reservation_of(seller, node,
    material, tile)`); goods that came from no concern are offered at whatever the market pays."""
    moves, offers = [], {}
    for sale in sorted(sales, key=lambda each: (each["seller"], each["material"])):
        good = sale["material"]
        units = sale["tonnes"] / tonnes_per_unit(good)
        if good not in economy.area_map.goods() or units <= 0.0:
            continue
        seller = sale["seller"]
        tile = tile_of(seller)
        concerns = [(node, tonnes) for node, tonnes in sale["concerns"] if tonnes > 0.0]
        weight = sum(tonnes for _node, tonnes in concerns)
        reservation = (sum(reservation_of(seller, node, good, tile) * tonnes for node, tonnes in concerns) / weight
                       if weight > 0.0 else 0.0)
        account = sale_account(seller)
        moves.append(GoodsMove(EDGE_LEGACY, account, good, tile, units, "actor output"))
        offers.setdefault(account, []).append(
            Offer(account, good, economy.area_map.area_of(good, tile), tile, units, reservation))
    return moves, {account: AgentOrders(offers=tuple(each)) for account, each in offers.items()}


def purchase_orders(economy, purchases: Sequence[dict], tonnes_per_unit: Callable[[str], float],
                    tile_of: Callable[[str], str], materials_in: Callable[[str], Sequence[str]], coin_per_unit: float):
    """({account: AgentOrders}, [(buyer, coin to turn into units, units)]) for the year's purchases. Each is a bid
    for a fixed quantity that pays up to the whole budget."""
    orders, funding = {}, []
    for purchase in sorted(purchases, key=lambda each: (each["buyer"], each["commodity"])):
        good = good_for(economy, purchase["commodity"], materials_in)
        if good is None:
            continue
        units = purchase["tonnes"] / tonnes_per_unit(good)
        budget = purchase["budget"] / coin_per_unit
        if units <= 0.0 or budget <= 0.0:
            continue
        buyer, account = purchase["buyer"], buy_account(purchase["buyer"])
        tile = tile_of(buyer)
        area = economy.area_map.area_of(good, tile)
        bid = Bid(account, good, area, tile, 0.0, units, budget / units, 0.0, budget, maximum_price=budget / units)
        held = orders.get(account)
        orders[account] = AgentOrders(bids=(held.bids if held else ()) + (bid,))
        funding.append((buyer, purchase["budget"], budget))
    return orders, funding


def fund(economy, funding: Sequence[Tuple[str, float, float]]) -> None:
    """The units the bids hold: from the exchange edge into each buy account (the coin side is the caller's)."""
    currency = economy.setup.currency_id
    economy_api.post_transfers(economy, [Transfer(EDGE_EXCHANGE, buy_account(buyer), currency, units, "exchange")
                                         for buyer, _coin, units in funding])


def close(economy, sales: Sequence[dict], purchases: Sequence[dict]):
    """Close every account after the clear. Unsold goods go back out; goods bought are used up; the money each
    account holds goes to the exchange edge. Returns ({seller: units of money its sales fetched}, {buyer: units of
    its budget left unspent}, {buyer: units of goods it bought})."""
    book, currency = economy_api.economy_book(economy), economy.setup.currency_id
    accounts = ([(sale_account(actor), actor, EDGE_LEGACY, "unsold actor output")
                 for actor in sorted({sale["seller"] for sale in sales})]
                + [(buy_account(actor), actor, EDGE_CONSUMPTION, "used by the buyer")
                   for actor in sorted({purchase["buyer"] for purchase in purchases})])
    proceeds: Dict[str, float] = {}
    refunds: Dict[str, float] = {}
    bought: Dict[str, float] = {}
    moves, transfers = [], []
    for account, actor, outflow, label in accounts:
        for good, tiles in book.holdings(account)["goods"].items():
            for tile, quantity in sorted(tiles.items()):
                if quantity > 0.0:
                    moves.append(GoodsMove(account, outflow, good, tile, quantity, label))
                    if outflow == EDGE_CONSUMPTION:
                        bought[actor] = bought.get(actor, 0.0) + quantity
        money = max(0.0, book.balance(account, currency))
        if money > 0.0:
            transfers.append(Transfer(account, EDGE_EXCHANGE, currency, money, "exchange"))
            (proceeds if outflow == EDGE_LEGACY else refunds)[actor] = money
    economy_api.move_goods(economy, moves)
    economy_api.post_transfers(economy, transfers)
    return proceeds, refunds, bought
