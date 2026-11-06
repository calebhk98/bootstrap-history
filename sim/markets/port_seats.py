"""What each seat's concerns sold in the year's clearing, kept so the next forecast counts only what buyers took.

Part of the port (it imports `sim.economy.api`). A seat's output is offered in the clearing (port_seat_concerns);
after it the seat's account holds the money the units that sold fetched and the units that did not. The per-material
result is stored with the economy (`stored["seat_sales"]`, in coin) and read back as an outlook.
"""
from sim.agents.api import edges
from sim.economy import api as economy_api
from sim.ledger.api import ReceiveFromEdge, pay_edge_or_log

from sim.production.api import concern_sales


def unsold_units(economy, seat_id):
    """{good: units} the seat's account still holds after the clearing."""
    held = economy_api.account_holdings(economy, seat_id)["goods"]
    return {good: sum(tiles.values()) for good, tiles in held.items() if sum(tiles.values()) > 0.0}


def record_year(economy, offered_by_seat, proceeds_units, coin):
    """{seat: {material: [offered units, sold units, proceeds in coin]}} for the seats that offered output,
    from what they still hold and the units of money `proceeds_units` gives each (read before settling)."""
    view = economy.view()
    kept = {}
    for seat_id, (tile, offered) in sorted(offered_by_seat.items()):
        quoted = {good: view.price(good, economy.area_map.area_of(good, tile)) for good in offered}
        prices = {good: price for good, price in quoted.items() if price is not None}     # a good with no price is weighted by units
        results = concern_sales.settle_sales(offered, unsold_units(economy, seat_id), proceeds_units.get(seat_id, 0.0), prices)
        kept[seat_id] = {material: [result.offered, result.sold, result.proceeds * coin]
                         for material, result in results.items()}
    return kept


def dividend_of_takings(dividend_units, coin, takings):
    """The bank dividend in coin a seat's takings hold: what its banks paid it (in the economy's units), never more than
    the takings (both zero when either is not above zero)."""
    return min(max(0.0, dividend_units) * coin, max(0.0, takings))


def settle_seats(sim, economy, offered_by_seat, inputs_by_seat, edge_id):
    """After the clearing: {seat: {material: [offered, sold, proceeds in coin]}} for the seats that offered output.
    Every seat's ledger is credited the dividend its banks paid it (its own posting); a seat that offered output is also
    credited the rest of what the clearing paid it, gross, less what its concerns' inputs cost (`inputs_by_seat`, in
    coin). Every seat's unsold goods and money go back over `edge_id`."""
    coin = economy_api.coin_per_unit(economy)
    book, currency = economy_api.economy_book(economy), economy_api.currency_id(economy)
    seats = sorted(sim.state.seats)
    balances = {seat_id: max(0.0, book.balance(seat_id, currency)) for seat_id in seats}
    paid = {seat_id: economy_api.bank_dividends_to(economy, seat_id) for seat_id in seats}
    proceeds = {seat_id: max(0.0, balances[seat_id] - dividend_of_takings(paid[seat_id], coin, balances[seat_id] * coin) / coin)
                for seat_id in seats}
    sold = record_year(economy, offered_by_seat, proceeds, coin)
    takings = {seat_id: economy_api.settle_agent_takings(economy, seat_id, edge_id) * coin for seat_id in seats}
    for seat_id in seats:
        dividend = dividend_of_takings(paid[seat_id], coin, takings[seat_id])
        with sim.scenario.act_as(seat_id):
            if dividend > 0.0:
                sim.send(ReceiveFromEdge(edges.EDGE_INTEREST, dividend, "bank dividend"))
            if seat_id not in offered_by_seat:
                continue
            sale = takings[seat_id] - dividend
            sim.send(ReceiveFromEdge(edges.EDGE_CUSTOMERS, sale, "concern sales"))
            unpaid = pay_edge_or_log(sim.send, edges.EDGE_SUPPLIERS, inputs_by_seat.get(seat_id, 0.0), "inputs of concerns sold in the book")
            if unpaid is not None and sale > 0.0:   # the inputs stay unpaid, so the sale is not booked either
                if pay_edge_or_log(sim.send, edges.EDGE_CUSTOMERS, sale, "concern sales reversed, inputs unpaid") is None:
                    for figures in sold.get(seat_id, {}).values():   # the units and money of a sale that is not booked
                        figures[1], figures[2] = 0.0, 0.0
    return sold


def outlook(economy, seat_sales, seat_id, material, quantity):
    """The seat's outlook for `quantity` units of a material (concern_sales.outlook): its own last clearing when it
    offered the material, else the units the market's buyers took and still wanted last year."""
    figures = (seat_sales.get(seat_id) or {}).get(material)
    result = concern_sales.SaleResult(*figures) if figures else None
    buyers = None
    if result is None and material in economy.area_map.goods():
        record = economy_api.market_record(economy, material)
        buyers = record["sold"] + record["unmet"]
    return concern_sales.outlook(result, buyers, quantity)
