"""The actors' money: one account each in a double-entry book, and their debts as claims against it.

A purse is never negative. Lending goes through one pool, a counterparty in the book that owes its depositors and
is owed by its borrowers. An actor that pays more than its purse holds first takes back its deposit, then draws the
shortfall on its facility: the pool puts the money into its purse and holds one claim for the principal, whatever
the number of lenders behind it. Money that comes in repays the claim first. Interest a borrower pays stays in the
pool until the year's settlement shares it among the depositors in proportion to their deposits; a default's loss
falls on the pool and through it on every deposit in proportion, once. So an actor's net position (purse and
deposit less debt) moves by exactly what the transfers move, which is what `net` reports and `Actor.money` shows.

Depositors are the accounts that offered funds (`set_offers`: a state's reserve, a household's savings, a firm's
spare cash) and the household savers the simulation does not model one by one (`EDGE_SAVERS`), who deposit
whatever the pool lacks and are paid back from what it holds beyond its lending.
"""
from typing import Any, Callable, Dict, Optional

from sim.book import ROUNDING_SHARE, Book, Transfer, is_edge
from sim.contracts import DEPOSIT, FACILITY, Contracts
from sim.rekey import rekey

from .bonds import BondBook
from .named_lenders import NamedLenders

COIN = "engine_coin"                          # the currency of the actors' money in the shared book (the engine counts in this coin)
EDGE_SAVERS = "edge:savers"                   # the household savers who lend to actors
EDGE_EXCHANGE = "edge:exchange"                # the actors' coin turned into the economy's unit and back
EDGE_OUTSIDE = "edge:outside the book"        # the other side of a posting whose payer or payee keeps no account here
FACILITY_DRAW = "facility draw"
FACILITY_REPAYMENT = "facility repayment"
BOND_SOLD = "bond sold"
BOND_REDEEMED = "bond redeemed"
INTEREST_PAID = "interest paid"                 # a borrower's interest to its lenders, as the book labels it
DEPOSIT_LOST = "deposit lost in a default"   # a depositor's share of the pool's loss, as the lender's books label it
POOL = "pool:credit"                          # the one lending counterparty: depositors' funds in, borrowers' facilities out
DEPOSIT_PLACED = "deposit placed"
DEPOSIT_TAKEN_BACK = "deposit taken back"
DEPOSIT_INTEREST = "interest on deposit"
DEBT_FLOOR = 1e-9                             # a debt below this is rounding residue


class Purses:
    """The accounts of the actors, and the claims against them."""

    def __init__(self, book: Any = None, contracts: Optional[Contracts] = None) -> None:
        self.book = book if book is not None else Book()
        # the debts: each draw on an actor's facility is a contract in the registry the economy shares
        self.contracts: Contracts = contracts if contracts is not None else Contracts()
        # depositor -> funds it offers this year; the savers' offer is the weight of the unmodelled households
        self.offers: Dict[str, float] = {}
        # interest borrowers have paid the pool since the last settlement, owed to the depositors
        self.interest_pending: float = 0.0
        # told (account, signed amount, label) when a lender's net position moves by a draw or a repayment
        self.observer: Optional[Callable[[str, float, str], None]] = None
        # the borrowers (a state) that name their lenders, and who lent each what (named_lenders.py)
        self.named_lenders = NamedLenders()
        # the issuers (a state) that raise cash by bonds, the terms they sell at, and the bonds outstanding (bonds.py)
        self.bonds = BondBook()

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
        """What the account owes, on every kind of contract and at face on its bonds, in the actors' coin."""
        return self.contracts.debt(account, COIN) + self.bonds.debt(account)

    def deposit(self, account: str) -> float:
        """What the pool owes the account."""
        return self.contracts.deposit_of(account)

    def net(self, account: str) -> float:
        """The purse and the deposit less the debt: what the actor is worth in cash."""
        return self.purse(account) + self.deposit(account) - self.debt(account)

    def lent(self, lender: Optional[str] = None) -> float:
        """What the lender has out (its deposit and its loans); every lender's loans when none is named."""
        if lender is not None:
            return self.contracts.exposure(lender, COIN)
        return (sum(contract.principal for contract in self.contracts.all() if contract.kind != DEPOSIT and contract.currency == COIN)
                + self.bonds.total_paid())

    def set_offers(self, offers: Dict[str, float]) -> None:
        """The funds each lender offers from now on: a lender's deposit in the pool moves to what it offers (from its
        purse, or back to it); the savers' offer keeps its weight whatever the others hold."""
        self.offers = {lender: amount for lender, amount in offers.items() if amount > 0.0}
        for account in sorted(set(self.offers) | set(self.contracts.deposits)):
            if is_edge(account):
                continue
            held = self.deposit(account)
            target = self.offers.get(account, 0.0)
            if target > held:
                self._place(account, min(target - held, self.purse(account)))
            elif held > target:
                self._take_back(account, held - target)

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
        """Make the payer's purse hold `amount`: it takes back its deposit first and draws the rest on its facility,
        both in one go (an account that will make several payments covers their sum first)."""
        if not is_edge(payer) and amount > DEBT_FLOOR:
            held = self.purse(payer)
            if held < amount * (1.0 - ROUNDING_SHARE):   # a purse short only by float dust pays as it is
                self._take_back(payer, min(amount - held, self.deposit(payer)))
                held = self.purse(payer)
                if held < amount * (1.0 - ROUNDING_SHARE):
                    self._draw(payer, amount - held)

    def pay_interest(self, borrower: str, owed: float, purpose: str = INTEREST_PAID) -> Dict[str, float]:
        """Pay `owed` to the pool its facility is drawn on; it reaches the depositors at the next settlement."""
        if owed <= 0.0 or (sum(self.contracts.facility_of(borrower).values()) <= 0.0 and self.bonds.debt(borrower) <= 0.0):
            return {}
        self.cover(borrower, owed)
        self.transfer(borrower, POOL, owed, purpose)
        self.interest_pending += owed
        return {POOL: owed}

    def pay_arrears(self, borrower: str, owed: float) -> None:
        """Pay interest that went unpaid in earlier years, from the purse; like any interest it waits in the pool."""
        paid = min(owed, self.purse(borrower))
        if paid > DEBT_FLOOR:
            self.book.transfer(Transfer(borrower, POOL, COIN, paid, INTEREST_PAID))
            self.interest_pending += paid

    def settle_interest(self) -> Dict[str, float]:
        """Share the interest the pool received among its depositors in proportion to their deposits, never more
        than the pool holds (the deposit rate is whatever that comes to; interest lost in a default is not paid),
        then pay the savers back what the pool holds beyond that; what each depositor received."""
        paid: Dict[str, float] = {}
        shares = {depositor: contract.principal for depositor, contract in sorted(self.contracts.deposits.items())}
        total = sum(shares.values())
        owed, self.interest_pending = self.interest_pending, 0.0
        available = min(owed, max(0.0, self.purse(POOL)))
        if available > DEBT_FLOOR and total > 0.0:
            for depositor, principal in shares.items():
                part = min(available * principal / total, max(0.0, self.purse(POOL)))
                if part > DEBT_FLOOR:
                    self.book.transfer(Transfer(POOL, depositor, COIN, part, DEPOSIT_INTEREST))
                    paid[depositor] = part
            for depositor in paid:
                if not is_edge(depositor):
                    self._repay(depositor)
        saved = self.deposit(EDGE_SAVERS)
        back = min(saved, self.purse(POOL))
        if back > DEBT_FLOOR:
            self.book.transfer(Transfer(POOL, EDGE_SAVERS, COIN, back, DEPOSIT_TAKEN_BACK))
            self.contracts.withdraw(EDGE_SAVERS, back, DEBT_FLOOR)
        return paid

    def set_net(self, account: str, value: float, purpose: str) -> None:
        """Bring the account's net position to `value`, the other side being the account outside the book."""
        difference = value - self.net(account)
        if difference > 0.0:
            self.transfer(EDGE_OUTSIDE, account, difference, purpose)
        elif difference < 0.0:
            self.transfer(account, EDGE_OUTSIDE, -difference, purpose)

    def repay_from_purse(self, borrower: str) -> None:
        """The borrower takes back its deposit and pays the pool what its purse holds."""
        self._take_back(borrower, self.deposit(borrower))
        self._repay(borrower)

    def write_off(self, borrower: str) -> Dict[str, float]:
        """The borrower closes owing: the claim against it is dropped and the pool bears the loss, every deposit
        losing in proportion (the cash was booked as an outlay when it left and no repayment follows); the loss."""
        lost = sum(contract.principal for contract in self.contracts.default(borrower, FACILITY)) + self.bonds.write_off(borrower)
        if self.named_lenders.names(borrower):
            deposits = {depositor: contract.principal for depositor, contract in self.contracts.deposits.items()}
            for depositor, part in self.named_lenders.settle_default(borrower, lost, deposits).items():
                self.contracts.withdraw(depositor, part, DEBT_FLOOR)
                self._tell(depositor, -part, DEPOSIT_LOST)
                lost -= part
        total = self.contracts.total_deposits()
        if lost > 0.0 and total > 0.0:
            factor = max(0.0, (total - lost) / total)
            for depositor, contract in sorted(self.contracts.deposits.items()):
                self._tell(depositor, -contract.principal * (1.0 - factor), DEPOSIT_LOST)
            self.contracts.scale_deposits(factor)
        return {POOL: lost} if lost > 0.0 else {}

    def _draw(self, borrower: str, shortfall: float) -> None:
        self._fund_pool(shortfall)
        if self.bonds.issues(borrower):
            # the market buys a bond for the shortfall: the borrower owes its face, the depositors paid the price
            self.book.transfer(Transfer(POOL, borrower, COIN, shortfall, BOND_SOLD))
            self.bonds.sell(borrower, shortfall)
        else:
            self.book.transfer(Transfer(POOL, borrower, COIN, shortfall, FACILITY_DRAW))
            self.contracts.draw(borrower, POOL, COIN, shortfall)
        if self.named_lenders.names(borrower):
            self.named_lenders.drew(borrower, shortfall, {depositor: contract.principal
                                                          for depositor, contract in self.contracts.deposits.items()})

    def _fund_pool(self, amount: float) -> None:
        """The pool can pay out `amount` and still hold the interest it owes its depositors: the savers deposit what
        its depositors' funds leave short."""
        lacking = amount - (self.purse(POOL) - self.interest_pending)
        if lacking > 0.0:
            self.book.transfer(Transfer(EDGE_SAVERS, POOL, COIN, lacking, DEPOSIT_PLACED))
            self.contracts.deposit(EDGE_SAVERS, POOL, COIN, lacking)

    def _place(self, account: str, amount: float) -> None:
        if amount > DEBT_FLOOR:
            self.book.transfer(Transfer(account, POOL, COIN, amount, DEPOSIT_PLACED))
            self.contracts.deposit(account, POOL, COIN, amount)

    def _take_back(self, account: str, amount: float) -> None:
        amount = min(amount, self.deposit(account))
        if amount > DEBT_FLOOR:
            self._fund_pool(amount)
            self.book.transfer(Transfer(POOL, account, COIN, amount, DEPOSIT_TAKEN_BACK))
            self.contracts.withdraw(account, amount, DEBT_FLOOR)

    def redeem_bonds(self, issuer: str) -> float:
        """A year passes for the issuer's bonds: those at their term are paid off at face, the issuer drawing the cash
        (on a new bond when its purse falls short); the face repaid. Call once a year."""
        due = self.bonds.age(issuer)
        if due > DEBT_FLOOR:
            self.cover(issuer, due)
            self.book.transfer(Transfer(issuer, POOL, COIN, due, BOND_REDEEMED))
            if self.named_lenders.names(issuer):
                owed = self.debt(issuer) + due
                self.named_lenders.repaid(issuer, due / owed if owed > 0.0 else 1.0)
        return due

    def _repay(self, borrower: str) -> None:
        held = self.contracts.facilities.get(borrower)
        if not held:
            return
        purse = self.purse(borrower)
        if purse > DEBT_FLOOR:   # a purse of rounding residue repays nothing
            debt = sum([contract.principal for contract in held.values()])
            repaid = min(debt, purse)
            if repaid > DEBT_FLOOR:
                for lender in sorted(held):
                    share = repaid * held[lender].principal / debt
                    if share <= DEBT_FLOOR:   # a lender owed so little takes no part
                        continue
                    part = min(share, max(0.0, purse))   # shares sum to the purse only to rounding
                    if part > DEBT_FLOOR:
                        self.book.transfer(Transfer(borrower, lender, COIN, part, FACILITY_REPAYMENT))
                        purse -= part   # what the book now holds for the borrower
                        self.contracts.repay_facility(borrower, lender, part)
                if self.named_lenders.names(borrower):
                    self.named_lenders.repaid(borrower, repaid / debt)
        self.contracts.tidy_facility(borrower, DEBT_FLOOR)

    def _tell(self, account: str, signed: float, label: str) -> None:
        """A depositor's wealth fell by a default's loss: it is told, so the books it keeps account for it."""
        if self.observer is not None and not is_edge(account) and account != POOL:
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

    def rename_account(self, old: str, new: str) -> None:
        """`old` becomes `new` with all it holds and owes: its purse and goods, its deposit, its facility and term
        loans as borrower and as lender, its bonds, its named lenders and its offer of funds. Nothing is paid, so
        every total in the book and the registry is what it was."""
        self.book.rename_agent(old, new)
        self.contracts.rename(old, new)
        for held in (self.bonds.terms, self.bonds.held, self.named_lenders.borrowers, self.named_lenders.held,
                     self.named_lenders.written_down, self.offers):
            rekey(held, old, new)

    # ---- the save file ----------------------------------------------------------------------
    def to_canon_dict(self) -> Dict[str, Any]:
        return {"book": self.book.to_record(only=(COIN,)),
                "facilities": self.contracts.to_records(facilities=True),
                "offers": dict(sorted(self.offers.items())), "interest_pending": self.interest_pending,
                "named_lenders": self.named_lenders.to_canon_dict(), "bonds": self.bonds.to_canon_dict()}

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "Purses":
        purses = cls(Book.from_record(record["book"]))
        purses.contracts.load_records(record["facilities"])
        purses.offers = dict(record.get("offers") or {})
        purses.interest_pending = float(record.get("interest_pending", 0.0))
        purses.named_lenders = NamedLenders.from_record(record.get("named_lenders") or {})
        purses.bonds = BondBook.from_record(record.get("bonds") or {})
        return purses
