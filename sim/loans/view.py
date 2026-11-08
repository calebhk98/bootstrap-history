"""A loan and the loan list as the readers outside the year's kernels see them: `LoanRow` follows one loan of the table by its number
(reads and writes the columns, so `loan.principal -= part` changes the table), and `LoanList` is the table as a sequence of them.
Neither holds a copy: a `LoanRow` of a loan that has left the table raises `LookupError`. `snapshot()` is the detached `Contract`."""
from typing import Any, Iterator, List, Optional, Union

import numpy

from sim.contract_record import Contract

from .store import LoanStore

_COLUMN_FIELDS = ("principal", "rate", "years_left", "collateral_value", "arrears", "arrears_interest", "collateral_share", "unit_value")


def _float_property(field: str) -> property:
    def read(self) -> float:
        return float(getattr(self.store.table, field)[self._row()])

    def write(self, value: float) -> None:
        getattr(self.store.table, field)[self._row()] = value
        self.store.version += 1
    return property(read, write)


def _name_property(field: str, numbers: str) -> property:
    def read(self) -> str:
        return getattr(self.store, numbers).name_list[getattr(self.store.table, field)[self._row()]]

    def write(self, value: str) -> None:
        getattr(self.store.table, field)[self._row()] = getattr(self.store, numbers).admit([value])[0]
        self.store.version += 1
    return property(read, write)


class LoanRow:
    """The loan with `number` in `store`; the attributes are those of `Contract`."""
    __slots__ = ("store", "number")
    __hash__ = None

    def __init__(self, store: LoanStore, number: int) -> None:
        self.store = store
        self.number = number

    def _row(self) -> int:
        row = self.store.row_of(self.number)
        if row < 0:
            raise LookupError("loan %r is no longer in the loan table" % (self.store.texts[self.number],))
        return row

    def snapshot(self) -> Contract:
        return self.store.snapshot(self._row())

    @property
    def contract_id(self) -> str:
        return self.store.texts[self.number]

    @contract_id.setter
    def contract_id(self, value: str) -> None:
        self.store.texts[self.number] = value
        self.store.version += 1

    @property
    def loan_id(self) -> str:
        return self.store.texts[self.number]

    lender = _name_property("lender", "agents")
    borrower = _name_property("borrower", "agents")
    currency = _name_property("currency", "currencies")
    kind = _name_property("kind", "kinds")
    principal = _float_property("principal")
    rate = _float_property("rate")
    years_left = _float_property("years_left")
    collateral_value = _float_property("collateral_value")
    arrears = _float_property("arrears")
    arrears_interest = _float_property("arrears_interest")
    collateral_share = _float_property("collateral_share")
    unit_value = _float_property("unit_value")

    @property
    def issued_year(self) -> int:
        return int(self.store.table.issued_year[self._row()])

    @issued_year.setter
    def issued_year(self, value: int) -> None:
        self.store.table.issued_year[self._row()] = value
        self.store.version += 1

    @property
    def collateral_tile(self) -> str:
        return self.store.tile_name(self.store.table.collateral_tile[self._row()])

    @collateral_tile.setter
    def collateral_tile(self, value: str) -> None:
        self.store.table.collateral_tile[self._row()] = self.store.tile_number(value)
        self.store.version += 1

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (LoanRow, Contract)):
            mine = self.snapshot()
            return mine == (other.snapshot() if isinstance(other, LoanRow) else other)
        return NotImplemented

    def __repr__(self) -> str:
        row = self.store.row_of(self.number)
        return "LoanRow(%r)" % (self.snapshot() if row >= 0 else "gone: " + self.store.texts[self.number],)


class LoanList:
    """The table's loans in row order as a sequence of `LoanRow`s. Append and extend add loans; to drop or reorder loans use the
    store's `retain`, `gather` or `replace_all`."""

    def __init__(self, store: LoanStore) -> None:
        self.store = store

    def __len__(self) -> int:
        return len(self.store)

    def __bool__(self) -> bool:
        return len(self.store) > 0

    def _numbers(self) -> List[int]:
        return self.store.table.number[:len(self.store)].tolist()

    def __iter__(self) -> Iterator[LoanRow]:
        store = self.store
        return iter([LoanRow(store, number) for number in self._numbers()])

    def __getitem__(self, index: Union[int, slice]):
        numbers = self._numbers()
        if isinstance(index, slice):
            return [LoanRow(self.store, number) for number in numbers[index]]
        return LoanRow(self.store, numbers[index])

    def __add__(self, other) -> list:
        return list(self) + list(other)

    def __radd__(self, other) -> list:
        return list(other) + list(self)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, (list, tuple, LoanList)) and list(self) == list(other)

    __hash__ = None

    def select(self, lender: Optional[str] = None, borrower: Optional[str] = None, currency: Optional[str] = None) -> List[LoanRow]:
        """The loans, in table order, whose lender, borrower and currency are the names given (a name left out matches any)."""
        store = self.store
        return [LoanRow(store, number) for number in store.table.number[store.rows_of(lender, borrower, currency)].tolist()]

    def append(self, loan: Any) -> None:
        self.store.append_contract(loan)

    def remove(self, loan: Any) -> None:
        """The loan leaves the table: the row itself, or for a Contract the first loan with its id."""
        store = self.store
        count = len(store)
        if isinstance(loan, LoanRow) and loan.store is store:
            gone = store.table.number[:count] == loan.number
        else:
            gone = numpy.zeros(count, dtype=numpy.bool_)
            for row in range(count):
                if store.texts[store.table.number[row]] == loan.contract_id:
                    gone[row] = True
                    break
        if not gone.any():
            raise ValueError("the loan is not in the loan table")
        store.retain(~gone)

    def extend(self, loans) -> None:
        self.store.append_contracts(loans)

    def __repr__(self) -> str:
        return "LoanList(%d loans)" % len(self)
