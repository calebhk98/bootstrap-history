"""The funds lenders offer, the market rate and what the state lends and owes.

The rate and the room a borrower may still be lent are the agent economy's credit market's. What the module adds is who lends
to the actors: once a year, before the actors act, the lenders' offers are fixed from what households save, what the state holds
beyond its need and what each firm holds, and the interest the pool holds is shared among its depositors.
Needs: civilisation, agent_rate, agent_credit_room, cast, cast_state, state_treasury, actor_world, legacy_edge_account,
legacy_seats, seat_party."""
from typing import Any, Dict, Optional, Tuple

from sim.agents.api import EDGE_SAVERS, payroll
from sim.world import capital_market

from . import rules
from .constants import BACKGROUND_BORROWING_SHARE, LENDING_HORIZON_YEARS


class CapitalMarket:

	def market_rate(self) -> float:
		"""The yearly market rate: the agent economy's credit market's, or the civilisation's starting rate while the economy opens."""
		return capital_market.market_rate_answered(float(self.needs.civilisation()["starting_interest_rate"]), self.needs.agent_rate())

	def credit_room(self, actor_id: str) -> Optional[float]:
		"""What lenders will advance one borrower beyond what the others owe; None before they have met (the agent economy's
		credit market answers)."""
		answered, room = self.needs.agent_credit_room(actor_id)
		return room if answered else None

	def market_funds(self, world: Any) -> Dict[str, float]:
		"""Funds lenders hold, by source."""
		government = self.needs.state_treasury()
		firms = sum(max(0.0, firm.money) for firm in self.needs.cast().active_firms())
		spare = rules.state_spare_reserve(government.money, sum(government.record.need.values()), government.cannot_meet_own_need())
		return {
			"households": LENDING_HORIZON_YEARS * world.household_saving(),
			"firms": firms,
			"state": rules.lendable_share_of_reserve(spare),
		}

	def state_lending(self) -> Tuple[float, float]:
		"""(what the state has out on loan, the yearly rate lenders earn): the claims the state holds in the actors' book, and
		the market rate."""
		return self.needs.cast_state().purses.lent(self.needs.state_treasury().actor_id), self.market_rate()

	def households_loanable_funds(self) -> float:
		"""Funds households put into the loanable pool at the last meeting of the capital market; none before it has met."""
		return self.needs.cast_state().purses.offers.get(EDGE_SAVERS, 0.0)

	def lender_offers(self, sources: Dict[str, float]) -> Dict[str, float]:
		"""The funds each lender account offers this year, from the market's sources: the households' savings stand behind the
		savers, the state's reserve behind its account, each firm's purse behind the firm's and the purse of any other actor whose
		class sets `lends_from_purse` behind its own (a mod's institution, say). A player's seat is not a lender: its purse is
		its own."""
		offers = {EDGE_SAVERS: sources["households"], self.needs.state_treasury().actor_id: sources["state"]}
		purses = self.needs.cast_state().purses
		registry = self.needs.cast()
		for firm in registry.active_firms():
			offers[firm.actor_id] = purses.purse(firm.actor_id) + purses.deposit(firm.actor_id)
		for lender in registry.purse_lenders():
			offers[lender.actor_id] = purses.purse(lender.actor_id) + purses.deposit(lender.actor_id)
		return offers

	def refresh_lender_offers(self, command: Any = None) -> None:
		"""The year's meeting of lenders: the pool pays the interest it holds, then who offers what is fixed."""
		self.settle_lender_interest()
		self.needs.cast_state().purses.set_offers(self.lender_offers(self.market_funds(self.needs.actor_world())))

	def settle_lender_interest(self) -> None:
		"""The pool shares the year's interest among its depositors: the actors enter it as income and the savers' part is shared
		among the strata."""
		received = self.needs.cast_state().purses.settle_interest()
		for lender, amount in received.items():
			if lender == EDGE_SAVERS:
				continue
			party = self._lender_party(lender)
			if party is not None:
				party.note_income("interest_on_lending", amount)
		savers = received.get(EDGE_SAVERS, 0.0)
		if savers > 0.0:
			payroll.pay_savers(self.needs.cast(), self.needs.legacy_edge_account[EDGE_SAVERS], savers)

	def note_lender_posting(self, command: Any) -> None:
		"""A lender's cash moved by a loan it made or was repaid: entered in the books the lender keeps."""
		seats = self.needs.legacy_seats()
		if command.account in seats:
			keeper = seats[command.account].household
		else:
			keeper = self.needs.cast().actors.get(command.account)
		if keeper is not None:
			(keeper.note_income if command.signed > 0.0 else keeper.note_outlay)(command.label, abs(command.signed))

	def _lender_party(self, account: str) -> Any:
		"""The actor behind a lender's account, or None for an edge."""
		if account in self.needs.legacy_seats():
			return self.needs.seat_party[account]
		return self.needs.cast().actors.get(account)

	def lent_share(self) -> float:
		"""Share of lenders' funds out on loan: what the actors owe and the economy the simulation does not model actor by actor
		borrows (a share of the households' savings), over the funds on offer."""
		purses = self.needs.cast_state().purses
		supply = sum(purses.offers.values())
		if supply <= 0.0:
			return 0.0
		background = BACKGROUND_BORROWING_SHARE * purses.offers.get(EDGE_SAVERS, 0.0)
		demanded = capital_market.utilisation(background + purses.lent(), supply)
		return min(1.0 - capital_market.LENDER_RESERVE_SHARE, demanded)

	def state_owes(self) -> float:
		"""What the state owes: its claims in the actors' book and the pay it has not paid its army and officials."""
		treasury = self.needs.state_treasury()
		return round(self.needs.cast_state().purses.debt(treasury.actor_id) + treasury.arrears_owed(), 1)

	def capital_market_report(self) -> Dict[str, Any]:
		"""The market as a player sees it: the rate, what lenders hold and will still advance the founder, and what the state owes."""
		purses = self.needs.cast_state().purses
		supply = sum(purses.offers.values())
		if supply <= 0.0:
			return {"market_rate": round(self.market_rate(), 4), "met": False, "the_state_owes": self.state_owes()}
		room = self.credit_room(self.clock.acting_seat)
		return {
			"met": True,
			"market_rate": round(self.market_rate(), 4),
			"funds_lenders_hold": round(supply, 1),
			"lenders_will_still_advance_you": None if room is None else round(room, 1),
			"the_state_owes": self.state_owes(),
			"the_state_has_lent": round(self.state_lending()[0], 1),
			"means": "the yearly rate on loans in your civilisation, set by the funds its households, "
			         "firms and state save against what everyone borrows; your own rate is this plus "
			         "a premium for how much of your limit you use, less your standing",
		}
