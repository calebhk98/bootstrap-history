"""Turn a market's clearing result into postings on the book.

A clearing that records who bought from whom (`ClearingResult.pairing`) is settled pair by pair, each at its seller's
ask; a labour result has its aggregate fills walked in order of (agent, tile) and matched greedily. When a payer cannot
cover what it owes, or a seller no longer holds what it sold, the affected pairs settle for the part that can be met: the
undelivered quantity stays with the seller and the unpaid money stays with the payer. A negative price (a waste someone is
paid to take) reverses who pays.

The pairs are packed once, settled by `settlement_kernel.settle_pairs` (several markets of one good in one call,
`settlement_batch.settle_many`), and posted summed per agent (`Book.post_settled`); the Transfers and GoodsMoves of the old
per-pair settlement are rebuilt only when asked (`Settlement.postings`).
"""
from operator import attrgetter
from typing import FrozenSet, List, Optional, Sequence

from sim.book import Book
from .settlement_arrays import settle_results
from .settlement_batch import settle_many
from .settlement_limits import pair_fills
from .settlement_record import Settlement
from .types import AgentId, ClearingResult, CurrencyId, Fill, LabourResult, Pairing

NO_ACCOUNTS: FrozenSet[AgentId] = frozenset()


def settle_goods(book: Book, result: ClearingResult, import_accounts: FrozenSet[AgentId] = NO_ACCOUNTS,
                 export_accounts: FrozenSet[AgentId] = NO_ACCOUNTS) -> Settlement:
    """The result's pairing settled on the book. The accounts are the year ledger's customs accounts
    (`YearLedger.import_accounts`, `export_accounts`), which decide the settlement's import and export figures."""
    return _settle(book, result.fills, result.currency, result.good,
                   "sale of %s" % result.good, delivers_goods=True, pairing=result.pairing,
                   import_accounts=import_accounts, export_accounts=export_accounts)


def settle_labour(book: Book, result: LabourResult) -> Settlement:
    """Wages employer to worker; hours the employer cannot pay for are not settled."""
    return _settle(book, result.fills, result.currency, result.trade,
                   "wages for %s" % result.trade, delivers_goods=False)


def settle_goods_many(book: Book, results: Sequence[ClearingResult], import_accounts: FrozenSet[AgentId] = NO_ACCOUNTS,
                      export_accounts: FrozenSet[AgentId] = NO_ACCOUNTS) -> List[Settlement]:
    """`settle_goods` of several results of one good, in order, each on what the earlier ones left, the book posted once."""
    if not results:
        return []
    good, currency = results[0].good, results[0].currency
    return settle_results(book, results, currency, good, "sale of %s" % good, import_accounts, export_accounts)


def _settle(book: Book, fills: Sequence[Fill], currency: CurrencyId, item: str,
            purpose: str, delivers_goods: bool, pairing: Optional[Pairing] = None,
            import_accounts: FrozenSet[AgentId] = NO_ACCOUNTS, export_accounts: FrozenSet[AgentId] = NO_ACCOUNTS
            ) -> Settlement:
    """Each pair of a buyer and a seller moves money at the seller's own price: a seller receives its ask and a buyer pays
    the asks of the sellers it bought from. A clearing that says who bought from whom (`pairing`) settles those pairs; any
    other is paired by walking buyers and sellers in order of (agent, tile), each seller's fill price being its ask."""
    if pairing is None:
        pairing = _paired_by_walking(fills)
    return settle_many(book, [pairing], currency, item, purpose, delivers_goods, import_accounts, export_accounts)[0]


def _paired_by_walking(fills: Sequence[Fill]) -> Pairing:
    """Labour only: goods results always carry a pairing. Buyers and sellers walked in order of (agent, tile) and matched
    until one side runs out; a seller's ask is its fill price."""
    order = attrgetter("agent", "tile")
    buys = sorted((fill for fill in fills if fill.side == "buy" and fill.quantity > 0.0), key=order)
    sells = sorted((fill for fill in fills if fill.side == "sell" and fill.quantity > 0.0), key=order)
    buyer_index, seller_index, quantity = pair_fills(buys, sells)
    return Pairing(tuple((fill.agent, fill.tile) for fill in buys), tuple((fill.agent, fill.tile) for fill in sells),
                   tuple(fill.price for fill in sells), tuple(buyer_index), tuple(seller_index), tuple(quantity))
