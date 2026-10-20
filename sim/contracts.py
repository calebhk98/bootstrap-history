"""The contract registry: every debt in the simulation, whoever owes it and whichever instrument it came as.

A contract has a lender, a borrower, a currency and a principal; its kind says how it behaves. A facility is
a draw on an actor's standing line (one contract per borrower and lender, repaid pro rata as money comes in);
a term loan has a rate, a term and arrears (struck by the credit market and serviced yearly); state debt is a
kind that joins the same registry; a deposit is what a pooled lender (see `sim/agents/purses.py`) is owed by the
pool that lends its funds on, one contract per depositor. A borrower's debt, a lender's claims and exposure, and a default's loss
are read from here, so a query never depends on which path made the contract. Cash stays in the book
(`sim/book.py`); the registry holds only what is owed.

The registry is shared the way the book is: the economy owns it, and the actors' purses adopt it.
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from sim.rekey import rename_text

FACILITY = "facility"
TERM_LOAN = "term_loan"
STATE_DEBT = "state_debt"
DEPOSIT = "deposit"


@dataclass
class Contract:
    contract_id: str
    lender: str
    borrower: str
    currency: str
    principal: float
    rate: float = 0.0
    years_left: float = 0.0
    collateral_value: float = 0.0
    arrears: float = 0.0
    issued_year: int = 0
    arrears_interest: float = 0.0     # the part of arrears that is unpaid interest
    kind: str = TERM_LOAN
    collateral_tile: str = ""         # the tile whose land title the loan pledges (empty: none)
    collateral_share: float = 0.0     # the share of that tile's land pledged

    @property
    def loan_id(self) -> str:
        return self.contract_id


class Contracts:
    """All contracts. Facilities are indexed by borrower (the purses ask on every posting); the others keep
    their list order, which the credit market's arithmetic follows (term loans and state debt)."""

    def __init__(self) -> None:
        self.facilities: Dict[str, Dict[str, Contract]] = {}      # borrower -> lender -> facility contract
        self.deposits: Dict[str, Contract] = {}                   # depositor -> deposit contract (the pool owes it)
        self.term_loans: List[Contract] = []
        self._term_seen: Any = None                      # (the list, its length, its last contract) the debts below were summed over
        self._term_debts: Dict[Optional[str], Dict[str, float]] = {}   # currency -> borrower -> debt on the term loans

    # ---- reads ------------------------------------------------------------------------------
    def all(self) -> Iterable[Contract]:
        for held in self.facilities.values():
            yield from held.values()
        yield from self.deposits.values()
        yield from self.term_loans

    def debt(self, borrower: str, currency: Optional[str] = None) -> float:
        """What the borrower owes on every kind of contract: principal and unpaid arrears."""
        total = 0.0
        held = self.facilities.get(borrower)
        if held:
            total += sum(contract.principal + contract.arrears for contract in held.values()
                         if currency is None or contract.currency == currency)
        return total + self._term_debt(currency).get(borrower, 0.0)

    def _term_debt(self, currency: Optional[str]) -> Dict[str, float]:
        loans = self.term_loans
        last = loans[-1] if loans else None
        seen = self._term_seen
        if seen is None or seen[0] is not loans or seen[1] != len(loans) or seen[2] is not last:
            self._term_seen, self._term_debts = (loans, len(loans), last), {}
        if currency not in self._term_debts:
            owed: Dict[str, float] = {}
            for contract in loans:
                if currency is None or contract.currency == currency:
                    owed[contract.borrower] = owed.get(contract.borrower, 0.0) + contract.principal + contract.arrears
            self._term_debts[currency] = owed
        return self._term_debts[currency]

    def exposure(self, lender: Optional[str] = None, currency: Optional[str] = None, kind: Optional[str] = None) -> float:
        """The principal the lender (every lender when none is named) has out."""
        return sum(contract.principal for contract in self.all()
                   if (lender is None or contract.lender == lender)
                   and (currency is None or contract.currency == currency)
                   and (kind is None or contract.kind == kind))

    def facility_of(self, borrower: str) -> Dict[str, float]:
        """lender -> principal it has drawn out on the borrower's facility."""
        return {lender: contract.principal for lender, contract in (self.facilities.get(borrower) or {}).items()}

    # ---- facilities -------------------------------------------------------------------------
    def draw(self, borrower: str, lender: str, currency: str, amount: float) -> None:
        held = self.facilities.setdefault(borrower, {})
        contract = held.get(lender)
        if contract is None:
            held[lender] = Contract("facility:%s:%s" % (borrower, lender), lender, borrower, currency, amount, kind=FACILITY)
        else:
            contract.principal += amount

    def set_facility(self, borrower: str, principals: Dict[str, float], currency: str) -> None:
        """Replace the borrower's facility by `principals` (lender -> principal)."""
        self.facilities.pop(borrower, None)
        for lender, principal in principals.items():
            self.draw(borrower, lender, currency, principal)

    def repay_facility(self, borrower: str, lender: str, amount: float) -> None:
        self.facilities[borrower][lender].principal -= amount

    def tidy_facility(self, borrower: str, floor: float) -> None:
        """Drop a facility that is rounding residue, else the lenders whose share is paid off or rounding residue."""
        held = self.facilities.get(borrower)
        if held is None:
            return
        principals = [contract.principal for contract in held.values()]
        if sum(principals) <= floor:
            del self.facilities[borrower]
        elif min(principals) <= floor:
            for lender in [who for who, contract in held.items() if contract.principal <= floor]:
                del held[lender]

    # ---- deposits ---------------------------------------------------------------------------
    def deposit(self, depositor: str, pool: str, currency: str, amount: float) -> None:
        contract = self.deposits.get(depositor)
        if contract is None:
            self.deposits[depositor] = Contract("deposit:%s" % depositor, depositor, pool, currency, amount, kind=DEPOSIT)
        else:
            contract.principal += amount

    def deposit_of(self, depositor: str) -> float:
        contract = self.deposits.get(depositor)
        return contract.principal if contract is not None else 0.0

    def total_deposits(self) -> float:
        return sum(contract.principal for contract in self.deposits.values())

    def withdraw(self, depositor: str, amount: float, floor: float) -> None:
        contract = self.deposits[depositor]
        contract.principal -= amount
        if contract.principal <= floor:
            del self.deposits[depositor]

    def scale_deposits(self, factor: float) -> None:
        """A loss the pool bears: every deposit is worth `factor` of what it was."""
        for contract in self.deposits.values():
            contract.principal *= factor

    # ---- defaults ---------------------------------------------------------------------------
    def default(self, borrower: str, kind: Optional[str] = None) -> List[Contract]:
        """The borrower closes owing: its contracts of `kind` (all kinds when none) end and are returned. No
        money moves: each lender's claim and the borrower's debt go together, so the loss is booked once."""
        ended: List[Contract] = []
        if kind in (None, FACILITY):
            ended.extend((self.facilities.pop(borrower, None) or {}).values())
        if kind != FACILITY:
            ended.extend(c for c in self.term_loans if c.borrower == borrower and (kind is None or c.kind == kind))
            self.term_loans = [c for c in self.term_loans if c not in ended]
        return ended

    # ---- renaming ---------------------------------------------------------------------------
    def rename(self, old: str, new: str) -> None:
        """`old` becomes `new` as borrower, lender and depositor: its contracts join `new`'s (a draw on the same
        lender adds to the one facility). A contract that would then be between `new` and itself ends."""
        for contract in self.all():
            contract.lender = rename_text(contract.lender, old, new)
            contract.borrower = rename_text(contract.borrower, old, new)
            contract.contract_id = rename_text(contract.contract_id, old, new)
        facilities: Dict[str, Dict[str, Contract]] = {}
        for held in self.facilities.values():
            for contract in held.values():
                if contract.lender == contract.borrower:
                    continue
                mine = facilities.setdefault(contract.borrower, {})
                if contract.lender in mine:
                    mine[contract.lender].principal += contract.principal
                    mine[contract.lender].arrears += contract.arrears
                else:
                    mine[contract.lender] = contract
        self.facilities = facilities
        deposits: Dict[str, Contract] = {}
        for contract in self.deposits.values():
            if contract.lender in deposits:
                deposits[contract.lender].principal += contract.principal
            else:
                deposits[contract.lender] = contract
        self.deposits = deposits
        self.term_loans = [contract for contract in self.term_loans if contract.lender != contract.borrower]
        self._term_seen = None

    # ---- sharing and the save file ----------------------------------------------------------
    def adopt(self, other: "Contracts") -> None:
        """Take over the facilities and deposits held by `other` (a purses' own registry before it joins the economy's)."""
        for depositor, contract in other.deposits.items():
            self.deposit(depositor, contract.borrower, contract.currency, contract.principal)
        for borrower, held in other.facilities.items():
            mine = self.facilities.setdefault(borrower, {})
            for lender, contract in held.items():
                if lender in mine:
                    mine[lender].principal += contract.principal
                else:
                    mine[lender] = contract

    def to_records(self, facilities: bool) -> List[Dict[str, Any]]:
        """The facilities (by borrower and lender) and deposits, or every other contract (in list order), as plain
        data; the economy saves the one and the actors' purses the other."""
        if facilities:
            return ([dict(vars(contract)) for _borrower, held in sorted(self.facilities.items())
                     for _lender, contract in sorted(held.items())]
                    + [dict(vars(contract)) for _depositor, contract in sorted(self.deposits.items())])
        return [dict(vars(contract)) for contract in self.term_loans]

    def load_records(self, records: Iterable[Dict[str, Any]]) -> None:
        for record in records:
            contract = Contract(**record)
            if contract.kind == FACILITY:
                self.facilities.setdefault(contract.borrower, {})[contract.lender] = contract
            elif contract.kind == DEPOSIT:
                self.deposits[contract.lender] = contract
            else:
                self.term_loans.append(contract)
