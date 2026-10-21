"""Paying for the bonded people the labour core bought (Complaint 644): the employers bidding for the trade in the
area pay the price between them, in proportion to their hours wanted and as far as their cash goes. The price is the
owners' ask plus the carriage (labour/market/bonded_worth.py); the money leaves over the exchange edge, and the engine
pays the owners their ask and the merchants who carried the people the carriage. The people are held bonded by the
employers who bid (`held`), their hours belonging to those employers' works (bondage_hours.place_held)."""
from typing import Dict, List, Sequence, Tuple

from .setup import area_tile
from .types import EDGE_EXCHANGE, LabourBid, Transfer


def settle(book, currency: str, lots: Sequence, bids: Sequence[LabourBid],
           ) -> Tuple[Dict[Tuple[str, str], float], float, List[dict], Dict[Tuple[str, str], Dict[str, float]]]:
    """Charge the employers for the bonded bought. Returns ({(tile, trade): people}, money paid, the lots as paid
    [{origin, destination, trade, people, ask, carriage}: money per lot, scaled to what was paid], and the people
    each employer holds {(tile, trade): {employer: people}})."""
    bought: Dict[Tuple[str, str], float] = {}
    paid_total = 0.0
    paid_lots: List[dict] = []
    held: Dict[Tuple[str, str], Dict[str, float]] = {}
    grouped: Dict[Tuple[str, str], list] = {}
    for lot in lots:
        if lot.people > 0.0:
            grouped.setdefault((lot.destination, lot.trade), []).append(lot)
    for (area, trade), group in sorted(grouped.items()):
        people = sum(lot.people for lot in group)
        key = (area_tile(area), trade)
        bought[key] = bought.get(key, 0.0) + people
        price = sum(lot.people * lot.price for lot in group)
        wanting = [bid for bid in bids if bid.area == area and bid.trade == trade and bid.hours > 0.0]
        hours = sum(bid.hours for bid in wanting)
        if hours <= 0.0:
            continue
        transfers = []
        owned = held.setdefault(key, {})
        for bid in wanting:
            owned[bid.employer] = owned.get(bid.employer, 0.0) + people * bid.hours / hours
            share = min(price * bid.hours / hours, max(0.0, book.balance(bid.employer, currency)))
            if share > 0.0:
                transfers.append(Transfer(bid.employer, EDGE_EXCHANGE, currency, share, "bonded purchase"))
        book.transfer_many(transfers)
        paid = sum(transfer.amount for transfer in transfers)
        paid_total += paid
        scale = paid / price if price > 0.0 else 0.0
        for lot in group:
            paid_lots.append({"origin": area_tile(lot.origin), "destination": key[0], "trade": trade,
                              "people": lot.people, "ask": lot.ask * lot.people * scale,
                              "carriage": lot.carriage * lot.people * scale})
    return bought, paid_total, paid_lots, held
