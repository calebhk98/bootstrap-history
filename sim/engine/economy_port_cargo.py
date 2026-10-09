"""Trader cargo that touches home, as orders in the agent economy's book.

Part of the port (it imports `sim.economy.api`). Each cargo leg between home and a partner gets an account in the
book. A landing cargo ("in") arrives over the partner's edge and is offered at any price; a taking cargo ("out")
is bought with the money the trader put in and handed to the partner's edge. After the clear the account is
closed: its money goes back to the trader's purse, the goods nobody took go back over the partner's edge.
A leg is a plain dict (`sim/engine/trader_cargo.py` makes it); money in a leg is the engine's, the book's is the
economy's coin, converted by `coin_per_unit`.
"""
from sim.economy import api as economy_api
from sim.economy.api import EDGE_CARGO, AgentOrders, Bid, GoodsMove, Offer, Transfer, external_edge

LANDING, TAKING = "in", "out"


def _enters_book(economy, leg):
    """Whether the leg is home's trade in a good the economy trades."""
    return leg["kind"] in (LANDING, TAKING) and leg["tonnes"] > 0.0 and leg["material"] in economy.area_map.goods()


def cargo_orders(economy, legs, tonnes_per_unit):
    """(goods moves, {account: orders}, money transfers) that put the legs' cargo in the book this year."""
    moves, orders, fundings = [], {}, []
    tile, coin = economy.setup.port_tile, economy.setup.coin_per_unit
    for leg in sorted(legs, key=lambda each: each["id"]):
        if not _enters_book(economy, leg):
            continue
        good, account = leg["material"], leg["id"]
        units = leg["tonnes"] / tonnes_per_unit(good)
        area = economy.area_map.area_of(good, tile)
        if leg["kind"] == LANDING:
            moves.append(GoodsMove(external_edge(leg["partner"]), account, good, tile, units, "cargo landed"))
            orders[account] = AgentOrders(offers=(Offer(account, good, area, tile, units, 0.0),))
            continue
        budget = leg["paid"] / coin
        worth_per_unit = (leg["received"] - leg.get("carriage", 0.0)) / coin / units
        if budget <= 0.0 or worth_per_unit <= 0.0:
            continue
        fundings.append(Transfer(EDGE_CARGO, account, economy.setup.currency_id, budget, "cargo funds"))
        # a merchant's order is for a fixed quantity (elasticity zero), at most what the cargo will fetch abroad
        orders[account] = AgentOrders(bids=(Bid(account, good, area, tile, 0.0, units, budget / units, 0.0, budget,
                                                maximum_price=worth_per_unit),))
    return moves, orders, fundings


def close_cargo_accounts(economy, legs, tonnes_per_unit):
    """Close each booked leg's account after the clear; {leg id: {"tonnes": tonnes the market took from a landing
    cargo or sold to a taking one, "money": a landing cargo's proceeds or a taking cargo's unspent funds}}."""
    results, moves, transfers = {}, [], []
    coin, currency = economy.setup.coin_per_unit, economy.setup.currency_id
    for leg in sorted(legs, key=lambda each: each["id"]):
        if not _enters_book(economy, leg):
            continue
        good, account, edge = leg["material"], leg["id"], external_edge(leg["partner"])
        held = economy_api.account_holdings(economy, account)["goods"].get(good, {})
        money = max(0.0, economy_api.account_balance(economy, account))
        units = leg["tonnes"] / tonnes_per_unit(good)
        held_units = sum(held.values())
        moves.extend(GoodsMove(account, edge, good, tile, quantity, "cargo returned" if leg["kind"] == LANDING
                               else "cargo taken") for tile, quantity in sorted(held.items()) if quantity > 0.0)
        if money > 0.0:
            transfers.append(Transfer(account, EDGE_CARGO, currency, money, "cargo takings"))
        moved_units = units - held_units if leg["kind"] == LANDING else held_units
        results[account] = {"tonnes": max(0.0, moved_units) * tonnes_per_unit(good), "money": money * coin}
    economy_api.move_goods(economy, moves)
    economy_api.post_transfers(economy, transfers)
    return results
