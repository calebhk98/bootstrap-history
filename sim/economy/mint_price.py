"""The mint buys bullion at the mint price, whatever the sellers it was paired with asked.

A market settles each sale at the seller's own ask, and the mint pays the ask of each seller it bought from. A mint is a
standing buyer at a fixed price (parity less the charge), so the metal's sellers get that price for what the mint takes:
each seller the mint bought from is topped up from its own ask to the mint price, and not at all when it asked more. The
charge stays with the mint as seigniorage (`mint.settle_mint`). This price for metal is the anchor of a commodity money:
when other prices fall, metal at the mint is worth more than it costs to make, so makers expand.
"""
from typing import Dict, Iterable, List, Optional, Tuple

from .types import ClearingResult, Fill, Transfer, EDGE_MINT, is_edge


def mint_bought(fills: Iterable[Fill]) -> float:
    return sum(fill.quantity for fill in fills if fill.agent == EDGE_MINT and fill.side == "buy")


def _taken_by_mint(result: ClearingResult) -> List[Tuple[str, float, float]]:
    """(seller, quantity, ask) for each non-edge seller the mint bought from. A result that says who bought from whom
    gives it exactly; any other has the mint's purchase shared among the sellers by what they sold, each at its fill price."""
    pairing = result.pairing
    if pairing is not None:
        return [(pairing.sellers[seller][0], quantity, pairing.asks[seller])
                for buyer, seller, quantity in zip(pairing.buyer_index, pairing.seller_index, pairing.quantity)
                if pairing.buyers[buyer][0] == EDGE_MINT and not is_edge(pairing.sellers[seller][0])]
    bought = mint_bought(result.fills)
    sells = [fill for fill in result.fills if fill.side == "sell" and fill.quantity > 0.0 and not is_edge(fill.agent)]
    total = sum(fill.quantity for fill in sells)
    if bought <= 0.0 or total <= 0.0:
        return []
    return [(fill.agent, bought * fill.quantity / total, fill.price) for fill in sells]


def top_ups(mint_price: float, result: ClearingResult) -> Dict[str, float]:
    """Money the mint adds for each seller of a market: what the mint took from it, times the gap from the seller's ask
    up to the mint price (nothing where the ask is at or above it)."""
    added: Dict[str, float] = {}
    for seller, quantity, ask in _taken_by_mint(result):
        if ask < mint_price and quantity > 0.0:
            added[seller] = added.get(seller, 0.0) + quantity * (mint_price - ask)
    return dict(sorted(added.items()))


def received_price(mint_price: float, result: ClearingResult) -> float:
    """What the sellers of a market got per unit sold, on average: the market's mean price plus the top-ups spread over
    the units the non-edge sellers sold."""
    paid = sum(top_ups(mint_price, result).values())
    sold = sum(fill.quantity for fill in result.fills if fill.side == "sell" and fill.quantity > 0.0 and not is_edge(fill.agent))
    return result.price + paid / sold if paid > 0.0 and sold > 0.0 else result.price


def pay_top_ups(book, ledger, currency_id: str, metal: str, mint_price: float) -> None:
    """After the goods markets: top up the sellers of the metal in every market the mint bought in."""
    transfers = []
    for result in ledger.clearings:
        if result.good != metal:
            continue
        for seller, amount in top_ups(mint_price, result).items():
            transfers.append(Transfer(EDGE_MINT, seller, currency_id, amount, "mint price top-up"))
    if transfers:
        book.post(transfers, [])
        ledger.note_postings(transfers, "sales")


def melting_pays(remembered_price: Optional[float], parity: float) -> bool:
    """Whether the mint offers its coin metal for sale: only when bullion fetches at least what the coin is worth in
    metal, so that melting coin loses nothing. With no remembered price, or bullion cheaper than coin, it holds."""
    return remembered_price is not None and remembered_price >= parity
