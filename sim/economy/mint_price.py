"""The mint buys bullion at the mint price, whatever the market settled the sale at.

A market settles every sale at the market's mean price. A mint is a standing buyer at a fixed price (parity less the
charge), so the metal's sellers get that price for what the mint takes; the gap between it and the settled price is the
top-up, paid by the mint and shared among the market's sellers by what they sold. The charge stays with the mint as
seigniorage (`mint.settle_mint`). This price for metal is the anchor of a commodity money: when other prices fall, metal
at the mint is worth more than it costs to make, so makers expand.
"""
from typing import Dict, Iterable, Optional

from .types import Fill, Transfer, EDGE_MINT, is_edge


def mint_bought(fills: Iterable[Fill]) -> float:
    return sum(fill.quantity for fill in fills if fill.agent == EDGE_MINT and fill.side == "buy")


def top_ups(bought: float, settled_price: float, mint_price: float, fills: Iterable[Fill]) -> Dict[str, float]:
    """Money the mint adds for each seller of a market where it bought `bought` units settled at `settled_price`."""
    if bought <= 0.0 or mint_price <= settled_price:
        return {}
    sold = {}
    for fill in fills:
        if fill.side == "sell" and fill.quantity > 0.0 and not is_edge(fill.agent):
            sold[fill.agent] = sold.get(fill.agent, 0.0) + fill.quantity
    total = sum(sold.values())
    if total <= 0.0:
        return {}
    gap = bought * (mint_price - settled_price)
    return {seller: gap * quantity / total for seller, quantity in sorted(sold.items())}


def received_price(settled_price: float, bought: float, mint_price: float, fills: Iterable[Fill]) -> float:
    """What the sellers of a market where the mint bought `bought` units got per unit sold, top-up included."""
    paid = sum(top_ups(bought, settled_price, mint_price, fills).values())
    sold = sum(fill.quantity for fill in fills if fill.side == "sell" and fill.quantity > 0.0 and not is_edge(fill.agent))
    return settled_price + paid / sold if paid > 0.0 and sold > 0.0 else settled_price


def pay_top_ups(book, ledger, currency_id: str, metal: str, mint_price: float) -> None:
    """After the goods markets: top up the sellers of the metal in every market the mint bought in."""
    transfers = []
    for result in ledger.clearings:
        if result.good != metal:
            continue
        bought = mint_bought(result.fills)
        for seller, amount in top_ups(bought, result.price, mint_price, result.fills).items():
            transfers.append(Transfer(EDGE_MINT, seller, currency_id, amount, "mint price top-up"))
    if transfers:
        book.post(transfers, [])
        ledger.note_postings(transfers, "sales")


def melting_pays(remembered_price: Optional[float], parity: float) -> bool:
    """Whether the mint offers its coin metal for sale: only when bullion fetches at least what the coin is worth in
    metal, so that melting coin loses nothing. With no remembered price, or bullion cheaper than coin, it holds."""
    return remembered_price is not None and remembered_price >= parity
