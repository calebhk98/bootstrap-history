"""The actors' money: one account each in a double-entry book, and their debts as loan claims against it.

A purse is never negative. An actor that pays more than its purse holds draws the shortfall on its facility,
a loan claim the household savers (`EDGE_SAVERS`, the lenders the simulation does not model one by one) hold
against it; money that comes in repays the facility first. So an actor's net position (purse less debt) moves
by exactly what the transfers move, which is what `net` reports and `Actor.money` shows.
"""
from dataclasses import dataclass
from typing import Any, Dict

from sim.book import Book, Transfer, is_edge

COIN = "coin"                                 # the currency of the actors' money in this book
EDGE_SAVERS = "edge:savers"                   # the household savers who lend to actors
EDGE_OUTSIDE = "edge:outside the book"        # the other side of a posting whose payer or payee keeps no account here
FACILITY_DRAW = "facility draw"
FACILITY_REPAYMENT = "facility repayment"
DEBT_FLOOR = 1e-9                             # a debt below this is rounding residue


@dataclass
class Claim:
    """What the savers hold against one borrower: the principal it has drawn and not repaid."""
    lender: str
    borrower: str
    principal: float


class Purses:
    """The accounts of the actors, and the claims against them."""

    def __init__(self, book: Any = None, claims: Any = None) -> None:
        self.book = book if book is not None else Book()
        self.claims: Dict[str, Claim] = claims if claims is not None else {}

    # ---- reads ------------------------------------------------------------------------------
    def purse(self, account: str) -> float:
        """What the account holds; an actor's is never below zero."""
        return self.book.balance(account, COIN)

    def debt(self, account: str) -> float:
        claim = self.claims.get(account)
        return claim.principal if claim is not None else 0.0

    def net(self, account: str) -> float:
        """The purse less the debt: what the actor is worth in cash."""
        return self.purse(account) - self.debt(account)

    def lent(self) -> float:
        """Everything the savers have out on claims."""
        return sum(claim.principal for claim in self.claims.values())

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

    def set_net(self, account: str, value: float, purpose: str) -> None:
        """Bring the account's net position to `value`, the other side being the account outside the book."""
        difference = value - self.net(account)
        if difference > 0.0:
            self.transfer(EDGE_OUTSIDE, account, difference, purpose)
        elif difference < 0.0:
            self.transfer(account, EDGE_OUTSIDE, -difference, purpose)

    def _draw(self, borrower: str, shortfall: float) -> None:
        self.book.transfer(Transfer(EDGE_SAVERS, borrower, COIN, shortfall, FACILITY_DRAW))
        claim = self.claims.get(borrower)
        if claim is None:
            self.claims[borrower] = Claim(EDGE_SAVERS, borrower, shortfall)
        else:
            claim.principal += shortfall

    def _repay(self, borrower: str) -> None:
        claim = self.claims.get(borrower)
        if claim is None:
            return
        repaid = min(claim.principal, self.purse(borrower))
        if repaid > 0.0:
            self.book.transfer(Transfer(borrower, EDGE_SAVERS, COIN, repaid, FACILITY_REPAYMENT))
            claim.principal -= repaid
        if claim.principal <= DEBT_FLOOR:
            del self.claims[borrower]

    # ---- the save file ----------------------------------------------------------------------
    def to_canon_dict(self) -> Dict[str, Any]:
        return {"book": self.book.to_record(),
                "claims": {borrower: [claim.lender, claim.principal] for borrower, claim in sorted(self.claims.items())}}

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "Purses":
        claims = {borrower: Claim(lender, borrower, principal) for borrower, (lender, principal) in record["claims"].items()}
        return cls(Book.from_record(record["book"]), claims)
