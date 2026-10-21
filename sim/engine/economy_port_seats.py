"""What each seat's concerns sold in the year's clearing, kept so the next forecast counts only what buyers took.

Part of the port (it imports `sim.economy.api`). A seat's output is offered in the clearing (economy_port_year);
after it the seat's account holds the money the units that sold fetched and the units that did not. The per-material
result is stored with the economy (`stored["seat_sales"]`, in coin) and read back as an outlook (concern_sales.py).
"""
from sim.economy import api as economy_api

from . import concern_sales


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
        prices = {good: view.price(good, economy.area_map.area_of(good, tile)) or 0.0 for good in offered}
        results = concern_sales.settle_sales(offered, unsold_units(economy, seat_id), proceeds_units.get(seat_id, 0.0), prices)
        kept[seat_id] = {material: [result.offered, result.sold, result.proceeds * coin]
                         for material, result in results.items()}
    return kept


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
