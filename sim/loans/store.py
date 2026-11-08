"""The loan store: the table of every term loan, the numbering of the names it holds, and the operations that change it as a whole.

The table (`loan_columns.Loans`) is the only copy of the loans. A loan is a row; its number (the `number` column) is its place in
`texts`, the id strings, and is never reused, so a `LoanRow` (loan_view.py) can follow a loan through the compactions that move its
row. Writers either call a kernel on `store.table` and then `changed()`, or use the methods here: `append_contract`, `retain`
(drop rows, keeping the order of the rest), `gather` (keep and reorder), `replace_all` and `rename`. Every change bumps `version`,
which the readers that keep a figure (the claims, the debts) compare. Contract objects are made only on demand (`snapshot`), for the
UI, the protocol, mods and tests."""
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.compiled_tables.ids import IdTable
from sim.contract_record import TERM_LOAN, Contract
from sim.rekey import rename_text

from .columns import FLOAT_FIELDS, LOAN_TABLE, NO_TILE, RECORD_ORDER, Loans

INITIAL_ROWS = 8


class LoanStore:
    """The loan table with its name numbering. See the module docstring."""

    def __init__(self) -> None:
        self.agents = IdTable("agent")
        self.currencies = IdTable("currency")
        self.tiles = IdTable("tile")
        self.kinds = IdTable("kind")
        self.table = LOAN_TABLE.new_table(Loans, INITIAL_ROWS)
        self.texts: List[str] = []                   # the id string of each loan number
        self.row_of_number = numpy.full(INITIAL_ROWS, -1, dtype=numpy.int64)    # the row of each loan number, -1 once it has left
        self.version = 0

    def __len__(self) -> int:
        return int(self.table.row_count[0])

    def changed(self) -> None:
        """A kernel wrote the table: readers that kept a figure must read again."""
        self.version += 1

    # ---- names ----------------------------------------------------------------------------------
    def agent_name(self, number: int) -> str:
        return self.agents.name_list[number]

    def tile_name(self, number: int) -> str:
        return "" if number == NO_TILE else self.tiles.name_list[number]

    def tile_number(self, name: str) -> int:
        return NO_TILE if not name else int(self.tiles.admit([name])[0])

    def agent_ranks(self) -> numpy.ndarray:
        """For each agent number, its place when all agent names are sorted: the order the rules sort by name."""
        names = self.agents.name_list
        ranks = numpy.empty(len(names), dtype=numpy.int64)
        for place, number in enumerate(sorted(range(len(names)), key=names.__getitem__)):
            ranks[number] = place
        return ranks

    def text_ranks(self) -> numpy.ndarray:
        """For each row, its place when the rows are sorted by id text (rows with the same text keep their row order)."""
        count = len(self)
        texts = self.texts
        numbers = self.table.number
        ranks = numpy.empty(count, dtype=numpy.int64)
        for place, row in enumerate(sorted(range(count), key=lambda each: texts[numbers[each]])):
            ranks[row] = place
        return ranks

    # ---- rows -----------------------------------------------------------------------------------
    def _room(self, extra: int) -> None:
        self.table = reserve_rows(self.table, extra)

    def _new_number(self, text: str) -> int:
        number = len(self.texts)
        self.texts.append(text)
        if number >= len(self.row_of_number):
            grown = numpy.full(max(number + 1, 2 * len(self.row_of_number)), -1, dtype=numpy.int64)
            grown[:len(self.row_of_number)] = self.row_of_number
            self.row_of_number = grown
        return number

    def number_of_row(self, row: int) -> int:
        return int(self.table.number[row])

    def row_of(self, number: int) -> int:
        """The row of loan `number`, or -1 when the loan has left."""
        return int(self.row_of_number[number]) if 0 <= number < len(self.texts) else -1

    def _reindex(self) -> None:
        count = len(self)
        self.row_of_number[:] = -1
        self.row_of_number[self.table.number[:count]] = numpy.arange(count, dtype=numpy.int64)
        self.version += 1

    def append_contract(self, item: Any, number: Optional[int] = None) -> int:
        """A loan with the fields of `item` (a Contract or anything with its attributes) struck last; its number is a new one unless
        `number` is given. Returns the row."""
        self._room(1)
        row = len(self)
        table = self.table
        number = self._new_number(item.contract_id) if number is None else number
        table.number[row] = number
        table.lender[row] = self.agents.admit([item.lender])[0]
        table.borrower[row] = self.agents.admit([item.borrower])[0]
        table.currency[row] = self.currencies.admit([item.currency])[0]
        table.kind[row] = self.kinds.admit([item.kind])[0]
        table.collateral_tile[row] = self.tile_number(item.collateral_tile)
        table.issued_year[row] = item.issued_year
        for field in FLOAT_FIELDS:
            getattr(table, field)[row] = getattr(item, field)
        table.row_count[0] = row + 1
        self.row_of_number[number] = row
        self.version += 1
        return row

    def append_contracts(self, items: Iterable[Any]) -> None:
        items = list(items)
        self._room(len(items))
        for item in items:
            self.append_contract(item)

    def retain(self, keep: numpy.ndarray) -> None:
        """Only the rows where `keep` (a boolean per row) is true stay, in their order."""
        count = len(self)
        kept = int(keep.sum())
        if kept == count:
            return
        for column in self.table[2:]:
            column[:kept] = column[:count][keep]
        self.table.row_count[0] = kept
        self._reindex()

    def gather(self, order: numpy.ndarray) -> None:
        """The loans are the rows `order` names, in that order (a row may be left out; none may repeat)."""
        count = len(self)
        for column in self.table[2:]:
            column[:len(order)] = column[:count][order]
        self.table.row_count[0] = len(order)
        self._reindex()

    def replace_all(self, items: Sequence[Any]) -> None:
        """The loans are `items`, in that order. An item that is a row of this store keeps its number (and a loan not named leaves);
        any other item (a Contract) is a new loan."""
        from .view import LoanRow     # loan_view needs this module
        kept = []
        for item in items:
            if isinstance(item, LoanRow) and item.store is self and self.row_of(item.number) >= 0:
                kept.append((item.number, item.snapshot()))
            else:
                kept.append((None, item))
        self.table.row_count[0] = 0
        self.row_of_number[:] = -1
        self._room(len(kept))
        for number, item in kept:
            self.append_contract(item, number)
        self.version += 1

    def clear(self) -> None:
        self.table.row_count[0] = 0
        self.row_of_number[:] = -1
        self.version += 1

    # ---- objects, on demand ---------------------------------------------------------------------
    def snapshot(self, row: int) -> Contract:
        """A Contract with the fields of the loan in `row`: a copy, which later changes to the table do not reach."""
        table = self.table
        return Contract(
            contract_id=self.texts[table.number[row]], lender=self.agent_name(table.lender[row]),
            borrower=self.agent_name(table.borrower[row]), currency=self.currencies.name_list[table.currency[row]],
            principal=float(table.principal[row]), rate=float(table.rate[row]), years_left=float(table.years_left[row]),
            collateral_value=float(table.collateral_value[row]), arrears=float(table.arrears[row]),
            issued_year=int(table.issued_year[row]), arrears_interest=float(table.arrears_interest[row]),
            kind=self.kinds.name_list[table.kind[row]], collateral_tile=self.tile_name(table.collateral_tile[row]),
            collateral_share=float(table.collateral_share[row]), unit_value=float(table.unit_value[row]))

    def snapshots(self, rows: Optional[Iterable[int]] = None) -> List[Contract]:
        return [self.snapshot(row) for row in (range(len(self)) if rows is None else rows)]

    def records(self) -> List[Dict[str, Any]]:
        """The loans as plain data in row order, the keys in `Contract`'s field order (the save file)."""
        count = len(self)
        table = self.table
        columns = {
            "contract_id": [self.texts[number] for number in table.number[:count].tolist()],
            "lender": [self.agents.name_list[each] for each in table.lender[:count].tolist()],
            "borrower": [self.agents.name_list[each] for each in table.borrower[:count].tolist()],
            "currency": [self.currencies.name_list[each] for each in table.currency[:count].tolist()],
            "kind": [self.kinds.name_list[each] for each in table.kind[:count].tolist()],
            "collateral_tile": [self.tile_name(each) for each in table.collateral_tile[:count].tolist()],
            "issued_year": table.issued_year[:count].tolist()}
        for field in FLOAT_FIELDS:
            columns[field] = getattr(table, field)[:count].tolist()
        return [dict(zip(RECORD_ORDER, values)) for values in zip(*(columns[name] for name in RECORD_ORDER))]

    def load(self, records: Iterable[Dict[str, Any]]) -> None:
        for record in records:
            self.append_contract(Contract(**record))

    def rows_of(self, lender: Optional[str] = None, borrower: Optional[str] = None, currency: Optional[str] = None) -> numpy.ndarray:
        """The rows (in order) whose lender, borrower and currency are the names given (a name left out matches any)."""
        count = len(self)
        keep = numpy.ones(count, dtype=numpy.bool_)
        for name, column, names in ((lender, self.table.lender, self.agents), (borrower, self.table.borrower, self.agents),
                                    (currency, self.table.currency, self.currencies)):
            if name is not None:
                number = names.find(name)
                if number is None:
                    return numpy.zeros(0, dtype=numpy.int64)
                keep &= column[:count] == number
        return numpy.nonzero(keep)[0]

    def principals_of(self, lender: Optional[str] = None, currency: Optional[str] = None) -> List[float]:
        """The principal of each loan of `lender` in `currency` (any when left out), in loan order, as Python floats."""
        return self.table.principal[self.rows_of(lender=lender, currency=currency)].tolist()

    def split_off(self, number: int, buyer: str, part: float, parcel_id: str) -> None:
        """`buyer` takes `part` of loan `number`: a new loan (last in the table, under `parcel_id`) with that share of the principal,
        arrears, interest arrears and collateral, which the loan gives up."""
        row = self.row_of(number)
        table = self.table
        bought = self.snapshot(row)
        bought.contract_id, bought.lender = parcel_id, buyer
        for field in ("principal", "arrears", "arrears_interest", "collateral_value", "collateral_share"):
            setattr(bought, field, getattr(bought, field) * part)
        self.append_contract(bought)
        row = self.row_of(number)
        table = self.table
        for field in ("principal", "arrears", "arrears_interest", "collateral_value", "collateral_share"):
            column = getattr(table, field)
            column[row] = column[row] - getattr(bought, field)

    def shrink_collateral(self, tile: str, keep: float) -> None:
        """Every loan pledged on `tile` is secured by `keep` of the share it was."""
        number = self.tiles.find(tile)
        count = len(self)
        if number is None or count == 0:
            return
        pledged = self.table.collateral_tile[:count] == number
        shares = self.table.collateral_share
        shares[:count][pledged] = shares[:count][pledged] * keep
        self.version += 1

    def drop_settled_deposits(self, bank: str, floor: float) -> None:
        """The bank's deposits (loans it borrows) with no principal and no arrears above `floor` leave the table."""
        count = len(self)
        number = self.agents.find(bank)
        if number is None:
            return
        table = self.table
        self.retain(~((table.borrower[:count] == number) & ~((table.principal[:count] > floor) | (table.arrears[:count] > floor))))

    def group_rows(self, rows: Optional[numpy.ndarray] = None) -> Dict[str, numpy.ndarray]:
        """{borrower: its rows in table order} for the borrowers of `rows` (all rows when none are given)."""
        count = len(self)
        rows = numpy.arange(count, dtype=numpy.int64) if rows is None else rows
        order = numpy.argsort(self.table.borrower[rows], kind="stable")
        sorted_rows = rows[order]
        borrowers = self.table.borrower[sorted_rows]
        starts = numpy.nonzero(numpy.concatenate(([True], borrowers[1:] != borrowers[:-1])))[0].tolist() + [len(sorted_rows)]
        names = self.agents.name_list
        return {names[int(borrowers[start])]: sorted_rows[start:stop] for start, stop in zip(starts[:-1], starts[1:])} if len(rows) else {}

    # ---- renaming -------------------------------------------------------------------------------
    def rename(self, old: str, new: str) -> None:
        """`old` becomes `new` as lender and borrower and in the id texts; a loan that would then be between `new` and itself ends."""
        names = self.agents.name_list
        renamed = [rename_text(name, old, new) for name in names]
        self.texts = [rename_text(text, old, new) for text in self.texts]
        if renamed != names:
            table = self.table
            count = len(self)
            fresh = IdTable("agent")
            fresh.admit(renamed)
            to_new = numpy.array([fresh.numbers[name] for name in renamed], dtype=numpy.int64)
            table.lender[:count] = to_new[table.lender[:count]]
            table.borrower[:count] = to_new[table.borrower[:count]]
            self.agents = fresh
        count = len(self)
        self.retain(self.table.lender[:count] != self.table.borrower[:count])
        self.version += 1

    def has_kind(self, name: str) -> bool:
        return self.kinds.find(name) is not None

    @property
    def term_kind(self) -> int:
        return int(self.kinds.admit([TERM_LOAN])[0])
