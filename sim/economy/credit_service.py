"""The year's service of the loan table: which loans fall due, what the borrowers pay, what each lender receives, what defaults, and the
table afterwards.

`serve` runs `sim/loans/service_kernel.service_loans` over the due rows, sorted by loan id, and returns a `Served` holding the answer as
arrays (a row per loan served); the table is not touched until `apply_served`, so the foreclosures and losses the answer causes read the loans
as they stood. `Served` makes objects (`Transfer`, `Default`, `Receipt`, the updated `Contract`s) only on demand, for callers that
still take them."""
from typing import Dict, List, Mapping, Optional, Sequence

import numpy

from sim.contract_record import Contract
from sim.loans.read_kernels import total_by_agent
from sim.loans.service_kernel import DEFAULTED, KEPT, ServiceOutput, new_output, service_loans
from sim.loans.store import LoanStore

from .credit import DEFAULT_ARREARS_SHARE, Default, Receipt
from .types import Transfer


def due_rows(store: LoanStore, year: int, excluded_borrowers: Sequence[str] = ()) -> numpy.ndarray:
    """The rows, in table order, of loans struck before `year` whose borrower is not one of `excluded_borrowers` (the banks: their
    deposits are served by the bank's own rule)."""
    count = len(store)
    due = store.table.issued_year[:count] < year
    numbers = [store.agents.find(name) for name in excluded_borrowers]
    numbers = [number for number in numbers if number is not None]
    if numbers:
        due &= ~numpy.isin(store.table.borrower[:count], numbers)
    return numpy.nonzero(due)[0]


def by_id(store: LoanStore, rows: numpy.ndarray) -> numpy.ndarray:
    """`rows` sorted by loan id text, rows with one text in table order."""
    texts, numbers = store.texts, store.table.number
    return numpy.array(sorted(rows.tolist(), key=lambda row: texts[numbers[row]]), dtype=numpy.int64)


class Served:
    """What serving `rows` of `store` came to; row `i` of `output` is `rows[i]`."""

    def __init__(self, store: LoanStore, rows: numpy.ndarray, output: ServiceOutput) -> None:
        self.store, self.rows, self.output = store, rows, output

    def _names(self, column: numpy.ndarray) -> List[str]:
        names = self.store.agents.name_list
        return [names[number] for number in column[self.rows].tolist()]

    def paid_places(self) -> numpy.ndarray:
        return numpy.nonzero(self.output.paid > 0)[0]

    def payments(self, year: int):
        """(payers, payees, currencies, amounts, purposes) of the payments made, in the order served."""
        places = self.paid_places()
        rows = self.rows[places]
        store, table = self.store, self.store.table
        names = store.agents.name_list
        currencies = store.currencies.name_list
        return ([names[number] for number in table.borrower[rows].tolist()], [names[number] for number in table.lender[rows].tolist()],
                [currencies[number] for number in table.currency[rows].tolist()], self.output.paid[places].tolist(),
                ["loan_service:%s:%d" % (store.texts[number], year) for number in table.number[rows].tolist()])

    def transfers(self, year: int) -> List[Transfer]:
        return [Transfer(*each) for each in zip(*self.payments(year))]

    def receipts(self) -> Dict[str, Receipt]:
        """Each lender served and what it received, the lenders in the order their first loan was served."""
        output = self.output
        lenders = numpy.nonzero(output.lender_order >= 0)[0]
        names = self.store.agents.name_list
        return {names[number]: Receipt(float(output.receipt_interest[number]), float(output.receipt_principal[number]),
                                       float(output.receipt_arrears[number]))
                for number in lenders[numpy.argsort(output.lender_order[lenders], kind="stable")].tolist()}

    def defaults(self) -> List[Default]:
        places = numpy.nonzero(self.output.status == DEFAULTED)[0]
        rows = self.rows[places]
        store, table = self.store, self.store.table
        names, currencies = store.agents.name_list, store.currencies.name_list
        return [Default(store.texts[number], names[lender], names[borrower], currencies[currency], loss)
                for number, lender, borrower, currency, loss in zip(
                    table.number[rows].tolist(), table.lender[rows].tolist(), table.borrower[rows].tolist(),
                    table.currency[rows].tolist(), self.output.loss[places].tolist())]

    def kept_places(self) -> numpy.ndarray:
        return numpy.nonzero(self.output.status == KEPT)[0]

    def kept_contracts(self) -> List[Contract]:
        """The loans that stay owed, as the service leaves them."""
        store, output = self.store, self.output
        contracts = []
        for place in self.kept_places().tolist():
            contract = store.snapshot(int(self.rows[place]))
            contract.principal, contract.arrears = float(output.principal[place]), float(output.arrears[place])
            contract.arrears_interest, contract.years_left = float(output.arrears_interest[place]), float(output.years_left[place])
            contracts.append(contract)
        return contracts


def serve(store: LoanStore, rows: numpy.ndarray, cash_by_borrower: Mapping[str, float]) -> Served:
    """Serve the loans in `rows` in loan-id order from the borrowers' cash (a figure per borrower name; a borrower named has its cash
    drawn down loan by loan)."""
    ordered = by_id(store, rows)
    cash = numpy.zeros(len(store.agents))
    for name, amount in cash_by_borrower.items():
        number = store.agents.find(name)
        if number is not None:
            cash[number] = amount
    output = new_output(len(ordered), len(store.agents))
    service_loans(store.table, ordered, cash, DEFAULT_ARREARS_SHARE, output)
    return Served(store, ordered, output)


def write_served(store: LoanStore, served: Served) -> numpy.ndarray:
    """The loans still owed take their new principal, arrears and term in the table; returns their rows in the order served."""
    table, output = store.table, served.output
    kept = served.kept_places()
    kept_rows = served.rows[kept]
    table.principal[kept_rows] = output.principal[kept]
    table.arrears[kept_rows] = output.arrears[kept]
    table.arrears_interest[kept_rows] = output.arrears_interest[kept]
    table.years_left[kept_rows] = output.years_left[kept]
    store.changed()
    return kept_rows


def apply_served(store: LoanStore, served: Served, serving: numpy.ndarray) -> None:
    """The table after the service: loans not served stay where they were, then the loans still owed in the order served with
    their new principal, arrears and term; loans paid off or defaulted leave."""
    kept_rows = write_served(store, served)
    untouched = numpy.ones(len(store), dtype=numpy.bool_)
    untouched[serving] = False
    store.gather(numpy.concatenate((numpy.nonzero(untouched)[0], kept_rows)))


def principal_changes(store: LoanStore, served: Served, rows: numpy.ndarray) -> Dict[str, float]:
    """For each borrower of the due `rows` (in table order of first appearance) the change in what it owes in principal over the
    service: the principal after (added in the order served) less the principal before (added in table order)."""
    table = store.table
    count = len(store)
    names = store.agents.name_list
    zero = numpy.zeros(len(names))
    selected = numpy.zeros(count, dtype=numpy.bool_)
    selected[rows] = True
    before, first_row = total_by_agent(table.borrower, table.principal, selected, count, zero)
    kept = served.kept_places()
    after, _first = total_by_agent(table.borrower[served.rows[kept]], served.output.principal[kept],
                                   numpy.ones(len(kept), dtype=numpy.bool_), len(kept), zero)
    appearing = numpy.nonzero(first_row >= 0)[0]
    return {names[number]: float(after[number]) - float(before[number])
            for number in appearing[numpy.argsort(first_row[appearing], kind="stable")].tolist()}


def service_split(loans: Sequence[Contract], cash_by_borrower: Mapping[str, float], year: int):
    """`credit.service_split` over a list of loans: (transfers, loans still owed, defaults, receipts by lender). The loans are copied
    into a table of their own, served, and made into objects again."""
    store = LoanStore()
    store.append_contracts(loans)
    served = serve(store, numpy.arange(len(store), dtype=numpy.int64), cash_by_borrower)
    return served.transfers(year), served.kept_contracts(), served.defaults(), served.receipts()
