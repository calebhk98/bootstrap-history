"""What each seat's concerns sold in the year's clearing, kept so the next forecast counts only what buyers took.

Part of the port (it imports `sim.economy.api`). A seat's output is offered in the clearing (port_year);
after it the seat's account holds the money the units that sold fetched and the units that did not. The per-material
result is stored with the economy (`stored["seat_sales"]`, in coin) and read back as an outlook.
"""
from sim.agents.api import edges
from sim.economy import api as economy_api

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


def settle_seats(sim, economy, offered_by_seat, inputs_by_seat, edge_id):
    """After the clearing: ({seat: {material: [offered, sold, proceeds in coin]}}, {seat: coin its account held}).
    Each seat that offered output has its ledger credited the money the clearing paid it, gross, less what its concerns'
    inputs cost (`inputs_by_seat`, in coin); every seat's unsold goods and money go back over `edge_id`."""
    coin = economy.setup.coin_per_unit
    book, currency = economy_api.economy_book(economy), economy.setup.currency_id
    proceeds = {seat_id: max(0.0, book.balance(seat_id, currency)) for seat_id in sorted(sim.state.seats)}
    sold = record_year(economy, offered_by_seat, proceeds, coin)
    takings = {seat_id: economy_api.settle_agent_takings(economy, seat_id, edge_id) * coin
               for seat_id in sorted(sim.state.seats)}
    for seat_id in sorted(offered_by_seat):
        with sim.act_as(seat_id):
            sim.receive_from_edge(edges.EDGE_CUSTOMERS, takings.get(seat_id, 0.0), "concern sales")
            sim.pay_edge(edges.EDGE_SUPPLIERS, inputs_by_seat.get(seat_id, 0.0), "inputs of concerns sold in the book")
    return sold, takings


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
