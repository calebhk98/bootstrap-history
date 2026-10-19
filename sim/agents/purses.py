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

from sim.book import ROUNDING_SHARE, Book, Transfer, is_edge
from sim.constants import declare
from sim.contracts import FACILITY, Contracts

COIN = "engine_coin"                          # the currency of the actors' money in the shared book (the engine counts in this coin)
EDGE_SAVERS = "edge:savers"                   # the household savers who lend to actors
EDGE_EXCHANGE = "edge:exchange"                # the actors' coin turned into the economy's unit and back
EDGE_OUTSIDE = "edge:outside the book"        # the other side of a posting whose payer or payee keeps no account here
FACILITY_DRAW = "facility draw"
FACILITY_REPAYMENT = "facility repayment"
INTEREST_PAID = "interest paid"                 # a borrower's interest to its lenders, as the book labels it
LENT = "loans made"
REPAID = "loans repaid to you"
LENDER_MATERIALITY = declare(
    "LENDER_MATERIALITY", 1e-4, kind="temporary_heuristic",
    unit="share of all funds on offer", source=None, confidence="D",
    retire="Complaints/580: small lenders pool through an intermediary instead of each holding a claim on every borrower",
    why="A lender offering less than this share of the funds on offer takes no part in a draw; the savers' pool "
        "covers its part. Every small lender holding a claim on every borrower makes the claims grow with the "
        "square of the firms and a year's postings with them.")
DEBT_FLOOR = 1e-9                             # a debt below this is rounding residue


class Purses:
    """The accounts of the actors, and the claims against them."""

    def __init__(self, book: Any = None, contracts: Optional[Contracts] = None) -> None:
        self.book = book if book is not None else Book()
        # the debts: each draw on an actor's facility is a contract in the registry the economy shares
        self.contracts: Contracts = contracts if contracts is not None else Contracts()
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

    @property
    def claims(self) -> Dict[str, Dict[str, float]]:
        """borrower -> lender -> principal the lender has out to it on a facility (a read of the registry)."""
        return {borrower: self.contracts.facility_of(borrower) for borrower in sorted(self.contracts.facilities)}

    def debt(self, account: str) -> float:
        """What the account owes, on every kind of contract, in the actors' coin."""
        return self.contracts.debt(account, COIN)

    def net(self, account: str) -> float:
        """The purse less the debt: what the actor is worth in cash."""
        return self.purse(account) - self.debt(account)

    def lent(self, lender: Optional[str] = None) -> float:
        """What the lender (every lender when none is named) has out on claims."""
        return self.contracts.exposure(lender, COIN)

    def set_offers(self, offers: Dict[str, float]) -> None:
        """The funds each lender offers from now on; the savers' offer keeps its weight whatever the others hold."""
        self.offers = {lender: amount for lender, amount in offers.items() if amount > 0.0}

    # ---- postings ---------------------------------------------------------------------------
    def transfer(self, payer: str, payee: str, amount: float, purpose: str) -> None:
        """Move `amount`; a payer short of it draws the rest on its facility first, and a payee in debt repays."""
        if not amount > DEBT_FLOOR:
            return   # rounding residue: the books carry noise larger than this
        self.cover(payer, amount)
        self.book.transfer(Transfer(payer, payee, COIN, amount, purpose))
        if not is_edge(payee):
            self._repay(payee)

    def cover(self, payer: str, amount: float) -> None:
        """Make the payer's purse hold `amount`, drawing the shortfall on its facility in one go (an account that
        will make several payments covers their sum first, so the lenders are asked once)."""
        if not is_edge(payer) and amount > DEBT_FLOOR:
            held = self.purse(payer)
            if held < amount * (1.0 - ROUNDING_SHARE):   # a purse short only by float dust pays as it is
                self._draw(payer, amount - held)

    def pay_interest(self, borrower: str, owed: float, purpose: str = INTEREST_PAID) -> Dict[str, float]:
        """Pay `owed` to the borrower's lenders in proportion to what each has lent it; what each received."""
        held = self.contracts.facility_of(borrower)
        total = sum(held.values())
        if owed <= 0.0 or total <= 0.0:
            return {}
        received: Dict[str, float] = {}
        self.cover(borrower, owed)
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

    def repay_from_purse(self, borrower: str) -> None:
        """The borrower pays its lenders what its purse holds, as a normal repayment (pro rata to what each lent)."""
        self._repay(borrower)

    def write_off(self, borrower: str) -> Dict[str, float]:
        """The borrower closes owing: the claims against it are dropped and each lender bears its loss (the cash
        it lent was booked as an outlay when it left and no repayment follows); the principal each lost."""
        return {contract.lender: contract.principal for contract in self.contracts.default(borrower, FACILITY)}

    def _draw(self, borrower: str, shortfall: float) -> None:
        for lender, part in self._shares_of(borrower, shortfall):
            self.book.transfer(Transfer(lender, borrower, COIN, part, FACILITY_DRAW))
            self.contracts.draw(borrower, lender, COIN, part)
            self._tell(lender, -part, LENT)

    def _shares_of(self, borrower: str, amount: float) -> Iterable:
        """(lender, part of `amount`) pairs: in proportion to the offers, each limited to its purse, the rest the savers'."""
        weights = {lender: offer for lender, offer in self.offers.items() if lender != borrower and offer > 0.0}
        weights.setdefault(EDGE_SAVERS, 0.0)
        total = sum(weights.values())
        weights = {lender: weight for lender, weight in weights.items() if weight >= LENDER_MATERIALITY * total}
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
        held = self.contracts.facility_of(borrower)
        if not held:
            return
        debt = sum(held.values())
        repaid = min(debt, self.purse(borrower))
        if repaid > DEBT_FLOOR:   # a purse of rounding residue repays nothing
            for lender, principal in sorted(held.items()):
                part = min(repaid * principal / debt, max(0.0, self.purse(borrower)))   # shares sum to the purse only to rounding
                if part > DEBT_FLOOR:
                    self.book.transfer(Transfer(borrower, lender, COIN, part, FACILITY_REPAYMENT))
                    self.contracts.repay_facility(borrower, lender, part)
                    self._tell(lender, part, REPAID)
        self.contracts.tidy_facility(borrower, DEBT_FLOOR)

    def _tell(self, account: str, signed: float, label: str) -> None:
        """A lender's cash moved by a loan: it is told, so the cash it keeps books account for it."""
        if self.observer is not None and not is_edge(account):
            self.observer(account, signed, label)

    def adopt_book(self, book: Any, contracts: Optional[Contracts] = None) -> None:
        """Keep the accounts in `book` and the contracts in `contracts` from now on (the economy's own, so purses
        and markets share one book and one registry); what this book holds in the actors' currency, and the
        facilities drawn so far, move over."""
        if contracts is not None and contracts is not self.contracts:
            contracts.adopt(self.contracts)
            self.contracts = contracts
        if book is self.book:
            return
        book.absorb(Book.from_record(self.book.to_record(only=(COIN,))))
        self.book = book

    # ---- the save file ----------------------------------------------------------------------
    def to_canon_dict(self) -> Dict[str, Any]:
        return {"book": self.book.to_record(only=(COIN,)),
                "facilities": self.contracts.to_records(facilities=True),
                "offers": dict(sorted(self.offers.items()))}

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "Purses":
        purses = cls(Book.from_record(record["book"]))
        purses.contracts.load_records(record["facilities"])
        purses.offers = dict(record.get("offers") or {})
        return purses
