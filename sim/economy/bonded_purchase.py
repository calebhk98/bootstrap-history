"""Paying for the bonded people the labour core bought (Complaint 644): the employers bidding for the trade in the
area pay the price between them, in proportion to their hours wanted and as far as their cash goes. The money leaves
over the exchange edge to the owners, whom the engine pays out of the agents' ledger."""
from typing import Dict, Sequence, Tuple

from sim.constants import declare

from .setup import area_tile
from .types import EDGE_EXCHANGE, LabourBid, Transfer

BONDED_PRICE_YEARS_OF_FLOOR = declare(
    "BONDED_PRICE_YEARS_OF_FLOOR", 10.0, kind="temporary_heuristic", unit="years of the area's ask floor",
    source=None, confidence="D",
    why="A bonded person is priced at some years of what keeping a worker's household costs, not at the "
        "discounted product of the rest of his service or the owner's cost of replacing him.",
    retire="644 owners' sale rule")


def settle(book, currency: str, formed, bids: Sequence[LabourBid], floor_by_area: Dict[str, float],
           ) -> Tuple[Dict[Tuple[str, str], float], float]:
    """Charge the employers for the bonded bought. Returns ({(tile, trade): people}, money paid)."""
    bought: Dict[Tuple[str, str], float] = {}
    paid_total = 0.0
    for area, by_trade in sorted(formed.items()):
        for trade, by_route in sorted(by_trade.items()):
            people = by_route.get("bonded", 0.0)
            if people <= 0.0:
                continue
            bought[(area_tile(area), trade)] = people
            price = people * floor_by_area.get(area, 0.0) * BONDED_PRICE_YEARS_OF_FLOOR
            wanting = [bid for bid in bids if bid.area == area and bid.trade == trade and bid.hours > 0.0]
            hours = sum(bid.hours for bid in wanting)
            if price <= 0.0 or hours <= 0.0:
                continue
            transfers = []
            for bid in wanting:
                share = min(price * bid.hours / hours, max(0.0, book.balance(bid.employer, currency)))
                if share > 0.0:
                    transfers.append(Transfer(bid.employer, EDGE_EXCHANGE, currency, share, "bonded purchase"))
            book.transfer_many(transfers)
            paid_total += sum(transfer.amount for transfer in transfers)
    return bought, paid_total
