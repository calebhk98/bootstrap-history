"""A seat's household as a borrower in the actors' book: the one rule every borrower follows (`borrowing.py`), with the seat's
own ceiling, rate and way of defaulting, which its owner answers (the founder's standing, collateral and living costs).

The borrower holds nothing of the seat's: its purse is the seat's account (`balance` reads it, `note_outlay` enters a payment in
the seat's cash book), and the arrears are the record its owner keeps (`arrears`: `interest_arrears`, `arrears_years`)."""
from typing import Any, Callable

from .borrowing import Borrower


class SeatBorrower(Borrower):
	kind = "household"

	def __init__(self, account_id: str, purses: Any, arrears: Any, *, balance: Callable[[], float], note_outlay: Callable[[Any, float], None],
	             ceiling: Callable[[], float], rate: Callable[[], float], defaults: Callable[[], None]) -> None:
		"""`balance()` is the seat's purse, `ceiling()` the most it may owe, `rate()` what it pays a year on its debt and
		`defaults()` what the lenders' default does to the household."""
		self.account_id, self.purses, self._arrears = account_id, purses, arrears
		self._balance, self._note_outlay = balance, note_outlay
		self._ceiling, self._rate, self._defaults = ceiling, rate, defaults

	@property
	def money(self) -> float:
		return self._balance()

	@property
	def arrears_book(self) -> Any:
		return self._arrears

	def note_outlay(self, purpose: Any, amount: float) -> None:
		self._note_outlay(purpose, amount)

	def credit_ceiling(self, world: Any) -> float:
		return self._ceiling()

	def borrowing_rate(self, world: Any) -> float:
		return self._rate()

	def default(self, world: Any) -> None:
		"""The lenders' default: the owner stops what it cannot fund, then the arrears are cleared."""
		self._defaults()
		self._arrears.interest_arrears = 0.0
		self._arrears.arrears_years = 0
