"""How the founder's household borrows: the shared arrears-and-default rule (`borrowing.py`), with the household's
own ceiling, rate and way of defaulting, which the simulation answers (its standing, collateral and living costs)."""
from typing import Any


class FounderBorrowing:
	"""Mixed into `Household`."""

	@property
	def arrears_book(self) -> Any:
		"""Where the arrears are kept: the household's finances."""
		return self._state.household  # type: ignore[attr-defined]

	def credit_ceiling(self, world: Any) -> float:
		return world.founder_credit_limit()

	def borrowing_rate(self, world: Any) -> float:
		return world.founder_debt_rate()

	def default(self, world: Any) -> None:
		"""The founder answers the lenders' default by stopping what it cannot fund, then settling or entering service."""
		world.founder_defaults()
		self.arrears_book.interest_arrears = 0.0
		self.arrears_book.arrears_years = 0
