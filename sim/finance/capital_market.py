"""The funds lenders offer, the market rate and what the state lends and owes.

The rate and the room a borrower may still be lent are the agent economy's credit market's. What the module adds is who lends
to the actors: once a year, before the actors act, the lenders' offers are fixed from what households save, what the state holds
beyond its need and what each firm holds, and the interest the pool holds is shared among its depositors.
Needs: civilisation, agent_rate, agent_credit_room, cast, state_treasury, actor_world, lender_offers_made, cash_and_deposit,
loans_out, debt_owed, send (SetLenderOffers, SettleLenderInterest, NoteHolderBooking)."""
from typing import Any, Dict, Optional, Tuple

from sim.actors.api import SetLenderOffers, SettleLenderInterest
from sim.agents.api import EDGE_SAVERS
from sim.economy.api import opening_market_rate
from sim.ledger.api import NoteHolderBooking
from sim.world import capital_market

from . import rules
from .constants import BACKGROUND_BORROWING_SHARE, LENDING_HORIZON_YEARS


class CapitalMarket:

	def market_rate(self) -> float:
		"""The yearly market rate: the agent economy's credit market's, or the rate the opening solves while the economy opens."""
		return capital_market.market_rate_answered(opening_market_rate(), self.needs.agent_rate())

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
		return self.needs.loans_out(self.needs.state_treasury().actor_id), self.market_rate()

	def households_loanable_funds(self) -> float:
		"""Funds households put into the loanable pool at the last meeting of the capital market; none before it has met."""
		return self.needs.lender_offers_made().get(EDGE_SAVERS, 0.0)

	def lender_offers(self, sources: Dict[str, float]) -> Dict[str, float]:
		"""The funds each lender account offers this year, from the market's sources: the households' savings stand behind the
		savers, the state's reserve behind its account, each firm's purse behind the firm's and the purse of any other actor whose
		class sets `lends_from_purse` behind its own (a mod's institution, say). A player's seat is not a lender: its purse is
		its own."""
		offers = {EDGE_SAVERS: sources["households"], self.needs.state_treasury().actor_id: sources["state"]}
		registry = self.needs.cast()
		for firm in registry.active_firms():
			offers[firm.actor_id] = self.needs.cash_and_deposit[firm.actor_id]
		for lender in registry.purse_lenders():
			offers[lender.actor_id] = self.needs.cash_and_deposit[lender.actor_id]
		return offers

	def refresh_lender_offers(self, command: Any = None) -> None:
		"""The year's meeting of lenders: the pool pays the interest it holds, then who offers what is fixed."""
		self.settle_lender_interest()
		offers = self.lender_offers(self.market_funds(self.needs.actor_world()))
		self.needs.send(SetLenderOffers(tuple(offers.items())))

	def settle_lender_interest(self) -> None:
		"""The pool shares the year's interest among its depositors: the actors enter it as income and the savers' part is shared
		among the strata."""
		self.needs.send(SettleLenderInterest())

	def note_lender_posting(self, command: Any) -> None:
		"""A lender's cash moved by a loan it made or was repaid: entered in the books the lender keeps."""
		self.needs.send(NoteHolderBooking(command.account, command.signed, command.label))

	def lent_share(self) -> float:
		"""Share of lenders' funds out on loan: what the actors owe and the economy the simulation does not model actor by actor
		borrows (a share of the households' savings), over the funds on offer."""
		offers = self.needs.lender_offers_made()
		supply = sum(offers.values())
		if supply <= 0.0:
			return 0.0
		background = BACKGROUND_BORROWING_SHARE * offers.get(EDGE_SAVERS, 0.0)
		demanded = capital_market.utilisation(background + self.needs.loans_out(), supply)
		return min(1.0 - capital_market.LENDER_RESERVE_SHARE, demanded)

	def state_owes(self) -> float:
		"""What the state owes: its claims in the actors' book and the pay it has not paid its army and officials."""
		treasury = self.needs.state_treasury()
		return round(self.needs.debt_owed[treasury.actor_id] + treasury.arrears_owed(), 1)

	def capital_market_report(self) -> Dict[str, Any]:
		"""The market as a player sees it: the rate, what lenders hold and will still advance the founder, and what the state owes."""
		supply = sum(self.needs.lender_offers_made().values())
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
