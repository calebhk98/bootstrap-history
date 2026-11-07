"""The mint buys bullion at the mint price, whatever the sellers it was paired with asked.

A market settles each sale at the seller's own ask, and the mint pays the ask of each seller it bought from. A mint is a
standing buyer at a fixed price (parity less the charge), so the metal's sellers get that price for what the mint takes:
each seller the mint bought from is topped up from its own ask to the mint price, and not at all when it asked more. The
charge stays with the mint as seigniorage (`mint.settle_mint`). This price for metal is the anchor of a commodity money:
when other prices fall, metal at the mint is worth more than it costs to make, so makers expand.
"""
from typing import Dict, List, Optional, Tuple

from .goods_year_results import ArrayClearing
from .types import ClearingResult, Transfer, EDGE_MINT, is_edge


def _taken_by_mint(result: ClearingResult) -> List[Tuple[str, str, float, float]]:
    """(seller, tile, quantity, ask) for each non-edge seller the mint bought from, as the result's pairing says. A year's
    goods result that traded carries one; one that did not trade has nothing taken."""
    if isinstance(result, ArrayClearing):
        return [(seller, tile, quantity, ask) for seller, tile, quantity, ask in result.taken_by(EDGE_MINT)
                if not is_edge(seller)]
    pairing = result.pairing
    if pairing is None:
        return []
    return [(pairing.sellers[seller][0], pairing.sellers[seller][1], quantity, pairing.asks[seller])
            for buyer, seller, quantity in zip(pairing.buyer_index, pairing.seller_index, pairing.quantity)
            if pairing.buyers[buyer][0] == EDGE_MINT and not is_edge(pairing.sellers[seller][0])]


def _settled_takes(result: ClearingResult, settled: Optional[Dict[Tuple[str, str], float]]) -> List[Tuple[str, float, float]]:
    """(seller, quantity, ask) of what the mint took: the matched quantities, cut to what the settlement delivered to the
    mint from each seller's tile when `settled` ((seller, tile) -> units delivered) is given."""
    left = dict(settled) if settled is not None else None
    taken = []
    for seller, tile, quantity, ask in _taken_by_mint(result):
        if left is not None:
            quantity = min(quantity, left.get((seller, tile), 0.0))
            left[(seller, tile)] = left.get((seller, tile), 0.0) - quantity
        taken.append((seller, quantity, ask))
    return taken


def top_ups(mint_price: float, result: ClearingResult, settled: Optional[Dict[Tuple[str, str], float]] = None) -> Dict[str, float]:
    """Money the mint adds for each seller of a market: what the mint took from it (what settled, when `settled` says
    what each seller's tile delivered to the mint), times the gap from the seller's ask up to the mint price (nothing
    where the ask is at or above it)."""
    added: Dict[str, float] = {}
    for seller, quantity, ask in _settled_takes(result, settled):
        if ask < mint_price and quantity > 0.0:
            added[seller] = added.get(seller, 0.0) + quantity * (mint_price - ask)
    return dict(sorted(added.items()))


def received_price(mint_price: float, result: ClearingResult, settled: Optional[Dict[Tuple[str, str], float]] = None) -> float:
    """What the sellers of a market got per unit sold, on average: the market's mean price plus the top-ups spread over
    the units the non-edge sellers sold (less the mint's units that did not settle, when `settled` is given). Called for results that traded only
    (`year_goods._received_price` skips a clearing with no quantity)."""
    paid = sum(top_ups(mint_price, result, settled).values())
    sold = (result.sold_by_producers() if isinstance(result, ArrayClearing) else
            sum(fill.quantity for fill in result.fills if fill.side == "sell" and fill.quantity > 0.0 and not is_edge(fill.agent)))
    if settled is not None:
        sold -= sum(quantity for _seller, _tile, quantity, _ask in _taken_by_mint(result)) - \
            sum(quantity for _seller, quantity, _ask in _settled_takes(result, settled))
    return result.price + paid / sold if paid > 0.0 and sold > 0.0 else result.price


def pay_top_ups(book, ledger, currency_id: str, metal: str, mint_price: float) -> None:
    """After the goods markets: top up the sellers of the metal in every market the mint bought in, on the units the
    settlement delivered to it."""
    transfers = []
    for result, settled in ledger.mint_takes:
        if result.good != metal:
            continue
        for seller, amount in top_ups(mint_price, result, settled).items():
            transfers.append(Transfer(EDGE_MINT, seller, currency_id, amount, "mint price top-up"))
    if transfers:
        book.post(transfers, [])
        ledger.note_postings(transfers, "sales")


def melting_pays(remembered_price: Optional[float], parity: float) -> bool:
    """Whether the mint offers its coin metal for sale: only when bullion fetches at least what the coin is worth in
    metal, so that melting coin loses nothing. With no remembered price, or bullion cheaper than coin, it holds."""
    return remembered_price is not None and remembered_price >= parity
