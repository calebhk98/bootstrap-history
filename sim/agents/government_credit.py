"""A state as a borrower with named lenders and a record: the lenders that fund its debt are kept by name, a default
writes their claims down, and the loss it caused raises the rate it pays until lenders forget. It raises cash by selling
bonds (bonds.py) at a price that follows that rate."""
from typing import Any, Dict

from . import borrowing_arrears
from .purses import Purses


class CreditRecordMixin:
	"""Mixed into `Government`."""

	def attach(self, purses: Purses) -> None:
		super().attach(purses)  # type: ignore[misc]
		purses.named_lenders.name(self.account_id)  # type: ignore[attr-defined]

	def set_bond_terms(self, world: Any) -> None:
		"""The terms the state sells bonds at this year: the going rate as the coupon, and the yield the market asks of
		this state (its borrowing rate, which carries the premium its default record earns) as the price."""
		self.purses.bonds.set_terms(self.account_id, world.market_rate(), self.borrowing_rate(world))  # type: ignore[attr-defined]

	def creditors(self) -> Dict[str, float]:
		"""Who is owed what by this state: the lenders whose deposits fund its debt, and their claims."""
		return self.purses.named_lenders.claims(self.account_id)  # type: ignore[attr-defined,no-any-return]

	def lenders_lost(self) -> Dict[str, float]:
		"""What each lender has had written down on this state's defaults."""
		return self.purses.named_lenders.lost(self.account_id)  # type: ignore[attr-defined,no-any-return]

	def default(self, world: Any) -> None:
		"""The lenders' claims are written down; the loss goes on the state's record and its next borrowing costs more."""
		owed = self.debt()  # type: ignore[attr-defined]
		super().default(world)  # type: ignore[misc]
		self.record.remembered_default_loss += owed  # type: ignore[attr-defined]
		self.record.defaults += 1  # type: ignore[attr-defined]

	def fade_default_record(self) -> None:
		self.record.remembered_default_loss = borrowing_arrears.faded(self.record.remembered_default_loss)  # type: ignore[attr-defined]

	def rate_on_loan(self, world: Any, amount: float) -> float:
		return super().rate_on_loan(world, amount) + self.default_premium(self.debt() + amount)  # type: ignore[misc,attr-defined,no-any-return]

	def borrowing_rate(self, world: Any) -> float:
		return super().borrowing_rate(world) + self.default_premium(self.debt())  # type: ignore[misc,attr-defined,no-any-return]

	def default_premium(self, debt_after: float) -> float:
		return borrowing_arrears.record_premium(self.record.remembered_default_loss, debt_after)  # type: ignore[attr-defined]
