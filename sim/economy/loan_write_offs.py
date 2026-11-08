"""Write-offs of borrowers' loans applied in several flushes (`LoanWriteOffs`), after Eurace@Unibi, Firm_bankruptcy_rescale_loans.

Each flush writes the named borrowers' loans down in the loan table (`sim/loans/write_down_kernel.py`) and drops the loans written to
nothing; the losses are booked and the defaults remembered borrower by borrower."""
from typing import Dict, List, Mapping

import numpy

from sim.loans.write_down_kernel import new_outputs, write_down

from . import credit_claims, firm_finance as finance
from .credit import Default


class LoanWriteOffs:
    """Each flush (`apply`) touches only its borrowers' loans, in the table as it stands at the flush."""

    def __init__(self, record) -> None:
        self.record = record

    def apply(self, ratios: Mapping[str, float]) -> Dict[str, float]:
        """Every loan of each borrower in `ratios` (borrower to ratio) loses its ratio of principal and arrears; the losses are booked and
        the defaults remembered borrower by borrower, in the mapping's order. Returns the total lost by borrower."""
        ratios = {borrower: ratio for borrower, ratio in ratios.items() if ratio > 0.0}
        if not ratios:
            return {}
        store = self.record.credit.contracts.loan_store
        numbers = [store.agents.find(borrower) for borrower in ratios]
        count = len(store)
        wanted = numpy.isin(store.table.borrower[:count], [number for number in numbers if number is not None])
        by_borrower = store.group_rows(numpy.nonzero(wanted)[0])
        rows = numpy.concatenate([by_borrower[borrower] for borrower in ratios if borrower in by_borrower] or [numpy.zeros(0, dtype=numpy.int64)])
        per_row = numpy.array([ratios[borrower] for borrower in ratios if borrower in by_borrower for _row in by_borrower[borrower]])
        defaults: Dict[str, List[Default]] = {borrower: [] for borrower in ratios}
        if len(rows):
            lost, remains = new_outputs(len(rows))
            write_down(store.table, rows, per_row, finance.ARREARS_EPSILON, lost, remains)
            self._book(store, rows, lost.tolist(), defaults)
            keep = numpy.ones(count, dtype=numpy.bool_)
            keep[rows[~remains]] = False
            store.changed()
            store.retain(keep)
        for group in defaults.values():
            for lender, lost_by_lender in credit_claims.losses_by_lender(group).items():
                self.record.credit.add_loss(lender, lost_by_lender)
            self.record.credit.remember(group)
        return {borrower: sum(default.loss for default in group) for borrower, group in defaults.items()}

    @staticmethod
    def _book(store, rows: numpy.ndarray, lost: List[float], defaults: Dict[str, List[Default]]) -> None:
        """The default of each written-down loan, under its borrower."""
        table = store.table
        names, currencies = store.agents.name_list, store.currencies.name_list
        for number, lender, borrower, currency, amount in zip(table.number[rows].tolist(), table.lender[rows].tolist(),
                                                              table.borrower[rows].tolist(), table.currency[rows].tolist(), lost):
            defaults[names[borrower]].append(Default(store.texts[number], names[lender], names[borrower], currencies[currency], amount))
