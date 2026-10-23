"""Paying for the bonded people the labour core bought (Complaint 644): the employers the core named for each lot
(those with a vacancy and room in their plans, labour/market/bonded_room.py) pay the price between them, in the
shares it named. The price is the
owners' ask plus the carriage (labour/market/bonded_worth.py); the money leaves over the exchange edge, and the engine
pays the owners their ask and the merchants who carried the people the carriage. The people are held bonded by the
employers who paid (`held`), their hours belonging to those employers' works (bondage_hours.place_held)."""
from typing import Dict, List, Sequence, Tuple

from .setup import area_tile
from .types import EDGE_EXCHANGE, Transfer


def settle(book, currency: str, lots: Sequence,
           ) -> Tuple[Dict[Tuple[str, str], float], float, List[dict], Dict[Tuple[str, str], Dict[str, float]]]:
    """Charge the employers named in the lots for the bonded bought. Returns ({(tile, trade): people}, money paid, the lots as paid
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
        transfers = []
        owned = held.setdefault(key, {})
        for lot in group:
            for employer, share in lot.payers:
                owned[employer] = owned.get(employer, 0.0) + lot.people * share
        for employer, share in _payers(group):
            amount = min(price * share, max(0.0, book.balance(employer, currency)))
            if amount > 0.0:
                transfers.append(Transfer(employer, EDGE_EXCHANGE, currency, amount, "bonded purchase"))
        book.transfer_many(transfers)
        paid = sum(transfer.amount for transfer in transfers)
        paid_total += paid
        scale = paid / price if price > 0.0 else 0.0
        for lot in group:
            paid_lots.append({"origin": area_tile(lot.origin), "destination": key[0], "trade": trade,
                              "people": lot.people, "ask": lot.ask * lot.people * scale,
                              "carriage": lot.carriage * lot.people * scale})
    return bought, paid_total, paid_lots, held


def _payers(group) -> List[Tuple[str, float]]:
    """Each employer's share of the group's price, weighted by what each lot costs."""
    price = sum(lot.people * lot.price for lot in group)
    shares: Dict[str, float] = {}
    for lot in group:
        for employer, share in lot.payers:
            shares[employer] = shares.get(employer, 0.0) + lot.people * lot.price * share / price
    return sorted(shares.items())
