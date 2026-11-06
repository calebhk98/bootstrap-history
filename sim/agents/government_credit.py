"""A state as a borrower with named lenders and a record: the lenders that fund its debt are kept by name, a default
writes their claims down, and the loss it caused raises the rate it pays until lenders forget. It raises cash by selling
bonds (bonds.py) at a price that follows that rate."""
from typing import Any, Dict

from . import borrowing_arrears


class CreditRecord:
	"""A state's lenders and default record, on the government that owns the record and the purse."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def set_bond_terms(self, world: Any) -> None:
		"""The terms the state sells bonds at this year: the going rate as the coupon, and the yield the market asks of
		this state (its borrowing rate, which carries the premium its default record earns) as the price."""
		self.government.purses.bonds.set_terms(self.government.account_id, world.credit.market_rate(), self.government.borrowing_rate(world))

	def creditors(self) -> Dict[str, float]:
		"""Who is owed what by this state: the lenders whose deposits fund its debt, and their claims."""
		return self.government.purses.named_lenders.claims(self.government.account_id)

	def lenders_lost(self) -> Dict[str, float]:
		"""What each lender has had written down on this state's defaults."""
		return self.government.purses.named_lenders.lost(self.government.account_id)

	def fade_default_record(self) -> None:
		self.government.record.remembered_default_loss = borrowing_arrears.faded(self.government.record.remembered_default_loss)

	def default_premium(self, debt_after: float) -> float:
		return borrowing_arrears.record_premium(self.government.record.remembered_default_loss, debt_after)
