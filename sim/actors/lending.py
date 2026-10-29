"""The actors' purse book as lenders use it: who offers what, what is lent out and owed, and the year's sharing of interest."""
from typing import Any, Dict, Optional

from sim.agents.api import EDGE_SAVERS, payroll


class Lending:
	"""Mixed into `Actors`."""

	needs: Any
	world: Any

	def lender_offers_made(self) -> Dict[str, float]:
		"""The funds each lender account offers this year, by account, in the order the pool keeps them."""
		return dict(self.world.purses.offers)

	def cash_and_deposit(self, account: str) -> float:
		"""What the account holds in its purse and has deposited with the pool."""
		purses = self.world.purses
		return purses.purse(account) + purses.deposit(account)

	def loans_out(self, lender: Optional[str] = None) -> float:
		"""What the lender has out on loan (every lender's when none is named)."""
		return self.world.purses.lent(lender)

	def debt_owed(self, account: str) -> float:
		"""What the account owes, on every kind of contract."""
		return self.world.purses.debt(account)

	def set_lender_offers(self, command: Any) -> None:
		self.world.purses.set_offers(dict(command.offers))

	def settle_lender_interest(self, command: Any = None) -> None:
		received = self.world.purses.settle_interest()
		for lender, amount in received.items():
			if lender == EDGE_SAVERS:
				continue
			party = self._lender_party(lender)
			if party is not None:
				party.note_income("interest_on_lending", amount)
		savers = received.get(EDGE_SAVERS, 0.0)
		if savers > 0.0:
			payroll.pay_savers(self.cast(), self.edge(EDGE_SAVERS), savers)

	def _lender_party(self, account: str) -> Any:
		"""The actor behind a lender's account, or None for an edge."""
		if account in self.needs.seat_list()["joined"]:
			return self.seat_party(account)   # type: ignore[attr-defined]
		return self.cast().actors.get(account)
