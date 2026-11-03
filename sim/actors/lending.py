"""The actors' purse book as lenders use it: who offers what, what is lent out and owed, and the year's sharing of interest."""
from typing import Any, Dict, List, Optional, Tuple

from sim.assembly.api import Part


class Lending(Part):

	def connect_purses(self) -> None:
		"""The purses ask this module what an account may be lent and who lends to the pool (never saved, set whenever the
		registry is built over a state)."""
		purses = self.world.purses
		purses.limit = self.draw_limit
		purses.lenders_for = self.lenders_for_draw

	def draw_limit(self, account: str, amount: float) -> float:
		"""The most of a draw of `amount` the account may be lent: its actor's or seat household's own limit; all of it for an account
		no borrower stands behind (an edge, the pool), which the lenders' supply still bounds."""
		return self.parts.cast.actor_world().credit.limit(account, amount)

	def lenders_for_draw(self, account: str, amount: float) -> Optional[Tuple[str, float, List[Tuple[str, float, float, float]]]]:
		"""(the economy's unit, coin per unit, [(lender, capacity, balance, ask)] cheapest first) of the lenders whose ask is no
		more than the rate the account would pay on a draw of `amount` (`Credit.rate_ceiling`: the market rate for the pool refilling a
		depositor's take-back); None before lenders have met or while the economy opens."""
		answered, listing = self.needs.agent_lender_listing()
		if not answered or not listing["lenders"]:
			return None
		ceiling = self.parts.cast.actor_world().credit.rate_ceiling(account, amount)
		lenders = [row for row in listing["lenders"] if row[4] <= ceiling]
		return listing["currency"], listing["coin_per_unit"], [(row[0], row[2], row[3], row[4]) for row in lenders]

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
			party = self._lender_party(lender)   # the economy's lenders were paid in units in the book: no actor behind them
			if party is not None:
				party.payments.note_income("interest_on_lending", amount)

	def _lender_party(self, account: str) -> Any:
		"""The actor behind a lender's account, or None for an edge."""
		if account in self.needs.seat_list()["joined"]:
			return self.parts.seat_parties.seat_party(account) 
		return self.parts.cast.cast().actors.get(account)
