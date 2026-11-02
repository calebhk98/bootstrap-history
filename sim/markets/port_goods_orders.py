"""A seat's goods orders in the year's clearing, as its staff are (port_staff.py). Part of the port (it imports `sim.economy.api`).

A seat's buy or sell command posts an order into the port's stored record (`stored["seat_orders"]`, {seat id: [order]}); nothing
settles at once. When the economy's year runs each order becomes a bid or an offer for its own goods account:

- a buy: the seat pays up to its price limit for the tonnes into the buy account `goods:<seat>:buy:<n>`, which bids for them;
- a sale: the tonnes leave the seat's stock for the sale account `goods:<seat>:sale:<n>`, which offers them at the seat's minimum.

A buy's limit is the market price ceiling; the carriage to the seat's tile and the order's cost factor (a project's opposition
and geography) are reserved with it and charged on the tonnes that arrive. After the clearing the goods the buy account holds go
to the seat's stock, the carriage and factor on them are charged, and the rest of the money is refunded; the sale account's
unsold goods go back to the seat's stock and its money is the sale's proceeds. What each seat bought and sold is kept as
`stored["seat_trades"]`, the figure the next year reads, with `"orders"`: one result per order, including an order whose payment
was refused or whose goods the seat no longer held (with the refusal's cause), so none vanishes silently.
"""
from sim.agents.api import edges
from sim.economy import api as economy_api
from sim.economy.api import EDGE_EXCHANGE, EDGE_LEGACY, AgentOrders, Bid, GoodsMove, Offer, Transfer
from sim.ledger.api import ChangeStock, PayEdge, ReceiveFromEdge
from sim.refusal import Refusal
from sim.world.material_units import tonnes_per_unit

from . import port_staff

GOODS_PREFIX = "goods:"


def buy_account(seat_id, index):
    return "%s%s:buy:%d" % (GOODS_PREFIX, seat_id, index)


def sale_account(seat_id, index):
    return "%s%s:sale:%d" % (GOODS_PREFIX, seat_id, index)


# ---- the posted orders (the port's stored record) ----

def add_order(stored, seat_id, order):
    """The seat's order, {"side": "buy"|"sell", "material", "good", "stock_key", "tonnes", "limit_per_tonne", "carriage_per_tonne",
    "cost_factor", "project"}, waits for the year's clearing. A buy's limit is the market price per tonne at most; carriage and
    the cost factor are charged on the tonnes that arrive."""
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


def order_results(stored, seat_id):
    """[result] of every order the last clearing handled for the seat: the order's fields, "bought_tonnes" and "paid" (money
    charged, with carriage and factor) for a buy or "sold_tonnes" and "proceeds" for a sale, and "refused" ({"cause", "text"} or
    None)."""
    return [dict(result) for result in stored.get("seat_trades", {}).get(seat_id, {}).get("orders", ())]


def reserve(order):
    """(money a buy order reserves in all, of which the extra beyond the market limit): the limit, the carriage and the factor."""
    market = order["limit_per_tonne"] * order["tonnes"]
    carriage = order.get("carriage_per_tonne", 0.0) * order["tonnes"]
    extra = (market + carriage) * (order.get("cost_factor", 1.0) - 1.0) + carriage
    return market + extra, extra


def committed_money(orders):
    """Money a seat's posted buy orders reserve."""
    return sum(reserve(order)[0] for order in orders if order["side"] == "buy")


def staff_funding_coin(sim, economy, seat_id, tile_of):
    """Money the port will draw from the seat for its staff places this year, ahead of any goods order."""
    hours = economy_api.working_hours_per_year(economy)
    with sim.act_as(seat_id):
        wanted = port_staff.places_with_once(sim.labour.staff_posting(), sim.labour.once_posting(), hours)
        if not wanted:
            return 0.0
        _bids, units = port_staff.employer_bids(economy, seat_id, wanted, tile_of(sim.labour.base_tile()),
                                                sim.view("spending_power")("buy"))
    return units * economy_api.coin_per_unit(economy)


# ---- the year ----

def refused(order, cause, text):
    """The result of an order that was not posted, with the cause the seat sees."""
    return {"side": order["side"], "material": order["material"], "stock_key": order["stock_key"], "tonnes": order["tonnes"],
            "project": order.get("project"), "refused": {"cause": cause, "text": str(text)}}


def post(sim, economy, orders_by_seat, tile_of):
    """({account: AgentOrders}, {seat id: [one entry per order]}) for the year; each order's payment is in its own buy account and
    its goods in its own sale account. An order that cannot be posted has an entry with its refusal."""
    coin, currency = economy_api.coin_per_unit(economy), economy_api.currency_id(economy)
    traded = economy.area_map.goods()
    bids, offers, moves, transfers, posted = {}, {}, [], [], {}
    for seat_id, orders in sorted(orders_by_seat.items()):
        with sim.act_as(seat_id):
            tile = tile_of(sim.labour.base_tile())
            entries = posted.setdefault(seat_id, [])
            for index, order in enumerate(orders):
                good = order["good"]
                if good is None or good not in traded:
                    entries.append({"refused": refused(order, "not_traded", "%s is not traded in the economy." % order["material"])})
                    continue
                if order["tonnes"] <= 0.0 or not order["limit_per_tonne"] > 0.0:
                    entries.append({"refused": refused(order, "no_quantity", "the order has no quantity or no price limit.")})
                    continue
                per_unit = tonnes_per_unit(good)
                area = economy.area_map.area_of(good, tile)
                price = order["limit_per_tonne"] * per_unit / coin
                if order["side"] == "buy":
                    units = order["tonnes"] / per_unit
                    budget = units * price
                    extra = reserve(order)[1] / coin
                    paid = sim.send(PayEdge(edges.EDGE_MARKET, (budget + extra) * coin, "materials ordered"))
                    if isinstance(paid, Refusal):
                        entries.append({"refused": refused(order, "cannot_pay", paid)})
                        continue
                    account = buy_account(seat_id, index)
                    transfers.append(Transfer(EDGE_EXCHANGE, account, currency, budget + extra, "materials ordered"))
                    bids.setdefault(account, []).append(
                        Bid(account, good, area, tile, 0.0, units, price, 0.0, budget, maximum_price=price))
                    entries.append({"order": order, "account": account, "extra": extra, "budget": budget})
                else:
                    tonnes = min(order["tonnes"], sim.material_stock_t(order["stock_key"]))
                    if tonnes <= 0.0:
                        entries.append({"refused": refused(order, "not_held", "no %s is held to sell." % order["material"])})
                        continue
                    moved = sim.send(ChangeStock(order["stock_key"], -tonnes))
                    if isinstance(moved, Refusal):
                        entries.append({"refused": refused(order, "not_held", moved)})
                        continue
                    account = sale_account(seat_id, index)
                    moves.append(GoodsMove(EDGE_LEGACY, account, good, tile, tonnes / per_unit, "seat goods for sale"))
                    offers.setdefault(account, []).append(Offer(account, good, area, tile, tonnes / per_unit, price))
                    entries.append({"order": order, "account": account, "offered": tonnes})
    economy_api.post_transfers(economy, transfers)
    economy_api.move_goods(economy, moves)
    return ({account: AgentOrders(bids=tuple(bids.get(account, ())), offers=tuple(offers.get(account, ())))
             for account in sorted(set(bids) | set(offers))}, posted)


def settle(sim, economy, posted):
    """After the clearing: {seat id: {"bought": {stock key: tonnes}, "sold": {stock key: tonnes}, "orders": [result]}}. Bought
    goods and unsold goods go to the seat's stock; a purchase's carriage and cost factor are charged on the tonnes that arrived;
    the money its account still holds goes to the purse (a purchase's unspent payment, a sale's proceeds)."""
    coin, currency = economy_api.coin_per_unit(economy), economy_api.currency_id(economy)
    book = economy_api.economy_book(economy)
    moves, transfers, settled = [], [], []
    for seat_id, entries in sorted(posted.items()):
        for entry in entries:
            if "refused" in entry:
                settled.append((seat_id, entry, None, 0.0))
                continue
            tonnes = 0.0
            for good, tiles in sorted(book.holdings(entry["account"])["goods"].items()):
                for tile, quantity in sorted(tiles.items()):
                    if quantity > 0.0:
                        moves.append(GoodsMove(entry["account"], EDGE_LEGACY, good, tile, quantity, "seat goods delivered"))
                        tonnes += quantity * tonnes_per_unit(good)
            money = max(0.0, book.balance(entry["account"], currency))
            if money > 0.0:
                transfers.append(Transfer(entry["account"], EDGE_EXCHANGE, currency, money, "exchange"))
            settled.append((seat_id, entry, tonnes, money * coin))
    economy_api.move_goods(economy, moves)
    economy_api.post_transfers(economy, transfers)
    trades = {}
    for seat_id, entry, tonnes, money in settled:
        trade = trades.setdefault(seat_id, {"bought": {}, "sold": {}, "orders": []})
        if tonnes is None:
            trade["orders"].append(entry["refused"])
            continue
        order = entry["order"]
        key = order["stock_key"]
        result = {"side": order["side"], "material": order["material"], "stock_key": key, "tonnes": order["tonnes"],
                  "project": order.get("project"), "refused": None}
        with sim.act_as(seat_id):
            if tonnes > 0.0:
                sim.send(ChangeStock(key, tonnes))
            if order["side"] == "buy":
                spent = max(0.0, entry["budget"] * coin - max(0.0, money - entry["extra"] * coin))
                carriage = order.get("carriage_per_tonne", 0.0) * tonnes
                charged = min(money, (spent + carriage) * (order.get("cost_factor", 1.0) - 1.0) + carriage)
                if money - charged > 0.0:
                    sim.send(ReceiveFromEdge(edges.EDGE_MARKET, money - charged, "materials order unspent"))
                trade["bought"][key] = trade["bought"].get(key, 0.0) + tonnes
                result.update(bought_tonnes=tonnes, paid=spent + charged)
            else:
                if money > 0.0:
                    sim.send(ReceiveFromEdge(edges.EDGE_MARKET, money, "materials sold"))
                sold = max(0.0, entry["offered"] - tonnes)
                trade["sold"][key] = trade["sold"].get(key, 0.0) + sold
                result.update(sold_tonnes=sold, proceeds=money)
        trade["orders"].append(result)
    for trade in trades.values():
        trade["bought"] = {key: amount for key, amount in trade["bought"].items() if amount > 0.0}
        trade["sold"] = {key: amount for key, amount in trade["sold"].items() if amount > 0.0}
    return trades
