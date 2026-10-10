"""The actors' money: one account each in a double-entry book, and their debts as loan claims against it.

A purse is never negative. An actor that pays more than its purse holds draws the shortfall on its facility:
lenders put the money into its purse and hold a claim for the principal. Money that comes in repays the claims
first, and interest is paid to the claim holders in proportion to what each lent. So an actor's net position
(purse less debt) moves by exactly what the transfers move, which is what `net` reports and `Actor.money` shows.

Lenders are the accounts that offered funds (`set_offers`: a state's reserve, a household's savings, a firm's
spare cash) and, for whatever they do not cover, the household savers the simulation does not model one by one
(`EDGE_SAVERS`). A lender lends no more than its purse holds.
"""
from typing import Any, Callable, Dict, Iterable, Optional

from sim.book import Book, Transfer, is_edge

COIN = "engine_coin"                          # the currency of the actors' money in the shared book (the engine counts in this coin)
EDGE_SAVERS = "edge:savers"                   # the household savers who lend to actors
EDGE_EXCHANGE = "edge:exchange"                # the actors' coin turned into the economy's unit and back
EDGE_OUTSIDE = "edge:outside the book"        # the other side of a posting whose payer or payee keeps no account here
FACILITY_DRAW = "facility draw"
FACILITY_REPAYMENT = "facility repayment"
INTEREST_PAID = "interest paid"                 # a borrower's interest to its lenders, as the book labels it
LENT = "loans made"
REPAID = "loans repaid to you"
DEBT_FLOOR = 1e-9                             # a debt below this is rounding residue


class Purses:
    """The accounts of the actors, and the claims against them."""

    def __init__(self, book: Any = None, claims: Any = None) -> None:
        self.book = book if book is not None else Book()
        # borrower -> lender -> principal the lender has out to it
        self.claims: Dict[str, Dict[str, float]] = claims if claims is not None else {}
        # lender -> funds it offers this year; the savers' offer is the weight of the unmodelled households
        self.offers: Dict[str, float] = {}
        # told (account, signed amount, label) when a lender's net position moves by a draw or a repayment
        self.observer: Optional[Callable[[str, float, str], None]] = None

    # ---- reads ------------------------------------------------------------------------------
    def purse(self, account: str) -> float:
        """What the account holds; an actor's is never below zero."""
        return self.book.balance(account, COIN)

    def has_account(self, account: str) -> bool:
        return self.book.knows(account)

    def debt(self, account: str) -> float:
        held = self.claims.get(account)
        return sum(held.values()) if held else 0.0

    def net(self, account: str) -> float:
        """The purse less the debt: what the actor is worth in cash."""
        return self.purse(account) - self.debt(account)

    def lent(self, lender: Optional[str] = None) -> float:
        """What the lender (every lender when none is named) has out on claims."""
        return sum(principal for held in self.claims.values() for who, principal in held.items()
                   if lender is None or who == lender)

    def set_offers(self, offers: Dict[str, float]) -> None:
        """The funds each lender offers from now on; the savers' offer keeps its weight whatever the others hold."""
        self.offers = {lender: amount for lender, amount in offers.items() if amount > 0.0}

    # ---- postings ---------------------------------------------------------------------------
    def transfer(self, payer: str, payee: str, amount: float, purpose: str) -> None:
        """Move `amount`; a payer short of it draws the rest on its facility first, and a payee in debt repays."""
        if not amount > 0.0:
            return
        if not is_edge(payer):
            shortfall = amount - self.purse(payer)
            if shortfall > 0.0:
                self._draw(payer, shortfall)
        self.book.transfer(Transfer(payer, payee, COIN, amount, purpose))
        if not is_edge(payee):
            self._repay(payee)

    def pay_interest(self, borrower: str, owed: float, purpose: str = INTEREST_PAID) -> Dict[str, float]:
        """Pay `owed` to the borrower's lenders in proportion to what each has lent it; what each received."""
        held = dict(self.claims.get(borrower) or {})
        total = sum(held.values())
        if owed <= 0.0 or total <= 0.0:
            return {}
        received: Dict[str, float] = {}
        for lender, principal in sorted(held.items()):
            part = owed * principal / total
            if part > 0.0:
                self.transfer(borrower, lender, part, purpose)
                received[lender] = part
        return received

    def set_net(self, account: str, value: float, purpose: str) -> None:
        """Bring the account's net position to `value`, the other side being the account outside the book."""
        difference = value - self.net(account)
        if difference > 0.0:
            self.transfer(EDGE_OUTSIDE, account, difference, purpose)
        elif difference < 0.0:
            self.transfer(account, EDGE_OUTSIDE, -difference, purpose)

    def _draw(self, borrower: str, shortfall: float) -> None:
        for lender, part in self._shares_of(borrower, shortfall):
            self.book.transfer(Transfer(lender, borrower, COIN, part, FACILITY_DRAW))
            held = self.claims.setdefault(borrower, {})
            held[lender] = held.get(lender, 0.0) + part
            self._tell(lender, -part, LENT)

    def _shares_of(self, borrower: str, amount: float) -> Iterable:
        """(lender, part of `amount`) pairs: in proportion to the offers, each limited to its purse, the rest the savers'."""
        weights = {lender: offer for lender, offer in self.offers.items() if lender != borrower and offer > 0.0}
        weights.setdefault(EDGE_SAVERS, 0.0)
        total = sum(weights.values())
        parts: Dict[str, float] = {}
        for lender, weight in sorted(weights.items()):
            part = amount * weight / total if total > 0.0 else 0.0
            if not is_edge(lender):
                part = min(part, max(0.0, self.purse(lender)))
            parts[lender] = part
        parts[EDGE_SAVERS] = parts.get(EDGE_SAVERS, 0.0) + (amount - sum(parts.values()))
        return [(lender, part) for lender, part in sorted(parts.items()) if part > 0.0]

    def _repay(self, borrower: str) -> None:
        held = self.claims.get(borrower)
        if not held:
            return
        debt = sum(held.values())
        repaid = min(debt, self.purse(borrower))
        if repaid > 0.0:
            for lender, principal in sorted(held.items()):
                part = min(repaid * principal / debt, max(0.0, self.purse(borrower)))   # shares sum to the purse only to rounding
                if part > 0.0:
                    self.book.transfer(Transfer(borrower, lender, COIN, part, FACILITY_REPAYMENT))
                    held[lender] = principal - part
                    self._tell(lender, part, REPAID)
        if sum(held.values()) <= DEBT_FLOOR:
            del self.claims[borrower]
        else:
            for lender in [who for who, principal in held.items() if principal <= 0.0]:
                del held[lender]

    def _tell(self, account: str, signed: float, label: str) -> None:
        """A lender's cash moved by a loan: it is told, so the cash it keeps books account for it."""
        if self.observer is not None and not is_edge(account):
            self.observer(account, signed, label)

    def adopt_book(self, book: Any) -> None:
        """Keep the accounts in `book` from now on (the economy's own, so purses and markets share one book);
        what this book holds in the actors' currency moves over."""
        if book is self.book:
            return
        book.absorb(Book.from_record(self.book.to_record(only=(COIN,))))
        self.book = book

    # ---- the save file ----------------------------------------------------------------------
    def to_canon_dict(self) -> Dict[str, Any]:
        return {"book": self.book.to_record(only=(COIN,)),
                "claims": {borrower: dict(sorted(held.items())) for borrower, held in sorted(self.claims.items())},
                "offers": dict(sorted(self.offers.items()))}

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "Purses":
        purses = cls(Book.from_record(record["book"]),
                     {borrower: dict(held) for borrower, held in record["claims"].items()})
        purses.offers = dict(record.get("offers") or {})
        return purses
