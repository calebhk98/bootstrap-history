"""A seat's goods orders in the year's clearing, as its staff are (port_staff.py). Part of the port (it imports `sim.economy.api`).

A seat's buy or sell command posts an order into the port's stored record (`stored["seat_orders"]`, {seat id: [order]}); nothing
settles at once. When the economy's year runs each order becomes a bid or an offer for the seat's goods accounts:

- a buy: the seat pays up to its price limit for the tonnes into the buy account `goods:<seat>`, which bids for them;
- a sale: the tonnes leave the seat's stock for the sale account `goods:<seat>:sale`, which offers them at the seat's minimum.

After the clearing the goods the buy account holds go to the seat's stock and the money it holds is refunded; the sale account's
unsold goods go back to the seat's stock and its money is the sale's proceeds. What each seat bought and sold is kept as
`stored["seat_trades"]`, the figure the next year reads. An order whose payment is refused, or whose goods the seat no longer holds, is
not posted.
"""
from sim.agents.api import edges
from sim.economy import api as economy_api
from sim.economy.api import EDGE_EXCHANGE, EDGE_LEGACY, AgentOrders, Bid, GoodsMove, Offer, Transfer
from sim.ledger.api import ChangeStock, PayEdge, ReceiveFromEdge
from sim.refusal import Refusal
from sim.world.material_units import tonnes_per_unit

GOODS_PREFIX = "goods:"


def buy_account(seat_id):
    return GOODS_PREFIX + seat_id


def sale_account(seat_id):
    return GOODS_PREFIX + seat_id + ":sale"


# ---- the posted orders (the port's stored record) ----

def add_order(stored, seat_id, order):
    """The seat's order, {"side": "buy"|"sell", "material", "good", "stock_key", "tonnes", "limit_per_tonne"}, waits for the year's clearing."""
    stored.setdefault("seat_orders", {}).setdefault(seat_id, []).append(order)


def posted_orders(stored, seat_id=None):
    """The orders waiting: one seat's list, or {seat id: list} of every seat's."""
    orders = stored.get("seat_orders", {})
    return list(orders.get(seat_id, ())) if seat_id is not None else {seat: list(each) for seat, each in orders.items()}


def posted_tonnes(stored, seat_id, side, stock_key):
    """Tonnes of a commodity the seat has ordered to buy or sell and the year's clearing has not yet settled."""
    return sum(order["tonnes"] for order in stored.get("seat_orders", {}).get(seat_id, ())
               if order["side"] == side and order["stock_key"] == stock_key)


def traded_tonnes(stored, seat_id, side):
    """{commodity: tonnes} the seat bought ("bought") or sold ("sold") in the last clearing."""
    return dict(stored.get("seat_trades", {}).get(seat_id, {}).get(side, {}))


# ---- the year ----

def post(sim, economy, orders_by_seat, tile_of):
    """({account: AgentOrders}, {seat id: what it posted}) for the year; each posting seat's payment is in its buy account and its
    goods in its sale account."""
    coin, currency = economy_api.coin_per_unit(economy), economy_api.currency_id(economy)
    traded = economy.area_map.goods()
    bids, offers, moves, transfers, posted = {}, {}, [], [], {}
    for seat_id, orders in sorted(orders_by_seat.items()):
        with sim.act_as(seat_id):
            tile = tile_of(sim.labour.base_tile())
            for order in orders:
                good = order["good"]
                per_unit = tonnes_per_unit(good)
                if good not in traded or order["tonnes"] <= 0.0 or not order["limit_per_tonne"] > 0.0:
                    continue
                area = economy.area_map.area_of(good, tile)
                price = order["limit_per_tonne"] * per_unit / coin
                kept = posted.setdefault(seat_id, {"buy": {}, "sell": {}, "offered": {}})
                if order["side"] == "buy":
                    units = order["tonnes"] / per_unit
                    budget = units * price
                    if isinstance(sim.send(PayEdge(edges.EDGE_MARKET, budget * coin, "materials ordered")), Refusal):
                        continue
                    account = buy_account(seat_id)
                    transfers.append(Transfer(EDGE_EXCHANGE, account, currency, budget, "materials ordered"))
                    bids.setdefault(account, []).append(
                        Bid(account, good, area, tile, 0.0, units, price, 0.0, budget, maximum_price=price))
                    kept["buy"][good] = order["stock_key"]
                else:
                    tonnes = min(order["tonnes"], sim.material_stock_t(order["stock_key"]))
                    if tonnes <= 0.0 or isinstance(sim.send(ChangeStock(order["stock_key"], -tonnes)), Refusal):
                        continue
                    account = sale_account(seat_id)
                    moves.append(GoodsMove(EDGE_LEGACY, account, good, tile, tonnes / per_unit, "seat goods for sale"))
                    offers.setdefault(account, []).append(Offer(account, good, area, tile, tonnes / per_unit, price))
                    kept["sell"][good] = order["stock_key"]
                    kept["offered"][order["stock_key"]] = kept["offered"].get(order["stock_key"], 0.0) + tonnes
    economy_api.post_transfers(economy, transfers)
    economy_api.move_goods(economy, moves)
    return ({account: AgentOrders(bids=tuple(bids.get(account, ())), offers=tuple(offers.get(account, ())))
             for account in sorted(set(bids) | set(offers))}, posted)


def settle(sim, economy, posted):
    """After the clearing: {seat id: {"bought": {commodity: tonnes}, "sold": {commodity: tonnes}}}. Bought goods and unsold goods
    go to the seat's stock, the money its accounts hold goes to its purse (a purchase's unspent payment, a sale's proceeds)."""
    coin, currency = economy_api.coin_per_unit(economy), economy_api.currency_id(economy)
    book = economy_api.economy_book(economy)
    moves, transfers, settled, trades = [], [], [], {}
    for seat_id, kinds in sorted(posted.items()):
        for side, account, label in (("buy", buy_account(seat_id), "materials order unspent"),
                                     ("sell", sale_account(seat_id), "materials sold")):
            if not kinds[side]:
                continue
            tonnes = {}
            for good, tiles in sorted(book.holdings(account)["goods"].items()):
                for tile, quantity in sorted(tiles.items()):
                    if quantity > 0.0:
                        moves.append(GoodsMove(account, EDGE_LEGACY, good, tile, quantity, "seat goods delivered"))
                        key = kinds[side].get(good, good)
                        tonnes[key] = tonnes.get(key, 0.0) + quantity * tonnes_per_unit(good)
            money = max(0.0, book.balance(account, currency))
            if money > 0.0:
                transfers.append(Transfer(account, EDGE_EXCHANGE, currency, money, "exchange"))
            settled.append((seat_id, side, tonnes, money * coin, label, kinds))
    economy_api.move_goods(economy, moves)
    economy_api.post_transfers(economy, transfers)
    for seat_id, side, tonnes, money, label, kinds in settled:
        trade = trades.setdefault(seat_id, {"bought": {}, "sold": {}})
        with sim.act_as(seat_id):
            for key, amount in sorted(tonnes.items()):
                sim.send(ChangeStock(key, amount))
            if money > 0.0:
                sim.send(ReceiveFromEdge(edges.EDGE_MARKET, money, label))
        if side == "buy":
            trade["bought"] = {key: amount for key, amount in tonnes.items() if amount > 0.0}
        else:
            trade["sold"] = {key: offered - tonnes.get(key, 0.0) for key, offered in kinds["offered"].items()
                             if offered - tonnes.get(key, 0.0) > 0.0}
    return trades
