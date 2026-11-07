"""Write-offs of borrowers' loans applied in several flushes with the loans indexed once (`LoanWriteOffs`), after Eurace@Unibi,
Firm_bankruptcy_rescale_loans."""
from typing import Dict, List, Mapping, Optional

from . import credit_claims, firm_finance as finance
from .credit import Default


class LoanWriteOffs:
    """Each flush (`apply`) touches only its borrowers' loans. The loans are read once, at the first flush: where each borrower's
    loans sit in the list is kept, and the list is installed again after every flush with the written-down loans in their places
    (a loan written to nothing leaves). If the credit record's loans were changed meanwhile (a different list, or another length or
    last loan), the index is read again from them."""

    def __init__(self, record) -> None:
        self.record = record
        self._slots: List[Optional[object]] = []
        self._positions: Dict[str, List[int]] = {}
        self._installed: Optional[list] = None
        self._last: Optional[object] = None
        self._length = 0

    def _is_current(self) -> bool:
        installed = self._installed
        loans = self.record.credit.loans
        return (installed is not None and loans is installed and len(loans) == self._length
                and (not loans or loans[-1] is self._last))

    def _read(self) -> None:
        loans = self.record.credit.loans
        self._slots = list(loans)
        self._positions = {}
        for position, loan in enumerate(self._slots):
            self._positions.setdefault(loan.borrower, []).append(position)
        self._installed = loans
        self._last = loans[-1] if loans else None
        self._length = len(loans)

    def apply(self, ratios: Mapping[str, float]) -> Dict[str, float]:
        """Every loan of each borrower in `ratios` (borrower to ratio) loses its ratio of principal and arrears; the losses are booked and
        the defaults remembered borrower by borrower, in the mapping's order. Returns the total lost by borrower."""
        ratios = {borrower: ratio for borrower, ratio in ratios.items() if ratio > 0.0}
        if not ratios:
            return {}
        if not self._is_current():
            self._read()
        slots = self._slots
        defaults: Dict[str, List[Default]] = {borrower: [] for borrower in ratios}
        for borrower, ratio in ratios.items():
            for position in self._positions.get(borrower, ()):
                loan = slots[position]
                if loan is None:
                    continue
                written, lost = finance.written_down(loan, ratio)
                defaults[borrower].append(Default(loan.loan_id, loan.lender, loan.borrower, loan.currency, lost))
                keeps = written.principal > finance.ARREARS_EPSILON or written.arrears > finance.ARREARS_EPSILON
                slots[position] = written if keeps else None
        kept = [loan for loan in slots if loan is not None]
        self.record.credit.replace_loans(kept)
        self._installed = self.record.credit.loans
        self._last = kept[-1] if kept else None
        self._length = len(kept)
        for group in defaults.values():
            for lender, lost in credit_claims.losses_by_lender(group).items():
                self.record.credit.add_loss(lender, lost)
            self.record.credit.remember(group)
        return {borrower: sum(default.loss for default in group) for borrower, group in defaults.items()}
