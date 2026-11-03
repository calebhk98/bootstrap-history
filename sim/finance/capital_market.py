"""The funds lenders offer, the market rate and what the state lends and owes.

The rate and the room a borrower may still be lent are the agent economy's credit market's. What the module adds is who lends
to the actors: the economy's own lenders (cohorts' savings, banks, funds) lend to the pool at their asks when an actor draws
(sim/agents/purses.py); once a year, before the actors act, the state's offer from what it holds beyond its need and each firm's
offer from its cash are fixed, and the interest the pool holds is shared among its depositors.
Needs: civilisation, agent_rate, agent_credit_room, agent_fundable_amount, agent_risk_premium, agent_lender_listing, cast, state_treasury, actor_world, lender_offers_made, cash_and_deposit,
loans_out, debt_owed, send (SetLenderOffers, SettleLenderInterest, NoteHolderBooking)."""
from typing import Any, Dict, Optional, Tuple

from sim.actors.api import SetLenderOffers, SettleLenderInterest
from sim.assembly.api import Part
from sim.economy.api import opening_market_rate
from sim.ledger.api import NoteHolderBooking
from sim.world import capital_market

from . import rules


class CapitalMarket(Part):

	def market_rate(self) -> float:
		"""The yearly market rate: the agent economy's credit market's, or the rate the opening solves while the economy opens."""
		return capital_market.market_rate_answered(opening_market_rate(), self.needs.agent_rate())

	def credit_room(self, actor_id: str) -> Optional[float]:
		"""What lenders will advance one borrower beyond what the others owe; None before they have met (the agent economy's
		credit market answers)."""
		answered, room = self.needs.agent_credit_room(actor_id)
		return room if answered else None

	def fundable_amount(self, amount: float, existing_debt: float, collateral_value: float, arrears: float) -> Optional[float]:
		"""The most of a draw of `amount` the credit market lends an actor that owes `existing_debt` against `collateral_value`
		(the one rule of the clearing, in coin); None before lenders have met or while the economy opens."""
		answered, fundable = self.needs.agent_fundable_amount(amount, existing_debt, collateral_value, arrears)
		return fundable if answered else None

	def risk_premium(self, debt_after: float, collateral_value: float, arrears: float) -> Optional[float]:
		"""The rate the credit market adds to the market rate for an actor owing `debt_after` against `collateral_value`; None
		while the economy opens."""
		answered, premium = self.needs.agent_risk_premium(debt_after, collateral_value, arrears)
		return premium if answered else None

	def market_funds(self, world: Any) -> Dict[str, float]:
		"""Funds the actors offer, by source: the state's lendable reserve (each firm's offer is its own cash, `lender_offers`)."""
		government = self.needs.state_treasury()
		spare = rules.state_spare_reserve(government.money, sum(government.record.need.values()), government.cannot_meet_own_need())
		return {"state": rules.lendable_share_of_reserve(spare)}

	def state_lending(self) -> Tuple[float, float]:
		"""(what the state has out on loan, the yearly rate lenders earn): the claims the state holds in the actors' book, and
		the market rate."""
		return self.needs.loans_out(self.needs.state_treasury().actor_id), self.market_rate()

	def economy_lending(self) -> Tuple[float, float]:
		"""(what the economy's lenders offered at the last lending, what of it is out of their accounts now), in coin; nothing
		before lenders have met."""
		answered, listing = self.needs.agent_lender_listing()
		if not answered:
			return 0.0, 0.0
		offered = sum(row[1] for row in listing["lenders"])
		held = sum(min(row[1], row[2]) for row in listing["lenders"])
		return offered * listing["coin_per_unit"], (offered - held) * listing["coin_per_unit"]

	def economy_pooled(self) -> float:
		"""What the economy's lenders have in the actors' pool, in coin."""
		answered, listing = self.needs.agent_lender_listing()
		return 0.0 if not answered else sum(self.needs.cash_and_deposit[row[0]] for row in listing["lenders"])

	def households_loanable_funds(self) -> float:
		"""Funds the economy's lenders (the households' savings among them) put on offer at the last lending, in coin; none
		before they have met."""
		return self.economy_lending()[0]

	def lender_offers(self, sources: Dict[str, float]) -> Dict[str, float]:
		"""The funds each lender account offers this year, from the market's sources: the households' savings stand behind the
		savers, the state's reserve behind its account, each firm's purse behind the firm's and the purse of any other actor whose
		class sets `lends_from_purse` behind its own (a mod's institution, say). A player's seat is not a lender: its purse is
		its own."""
		offers = {self.needs.state_treasury().actor_id: sources["state"]}
		registry = self.needs.cast()
		for firm in registry.concerns.active_firms():
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
		"""Share of lenders' funds out on loan: what the economy's lenders have lent out of their offers (loans to its borrowers
		and the funds they put in the actors' pool) and what the actors owe out of their own offers, over the funds on offer."""
		actors_offered = sum(self.needs.lender_offers_made().values())
		economy_offered, economy_lent = self.economy_lending()
		supply = actors_offered + economy_offered
		if supply <= 0.0:
			return 0.0
		actors_lent = min(actors_offered, max(0.0, self.needs.loans_out() - self.economy_pooled()))
		demanded = capital_market.utilisation(economy_lent + actors_lent, supply)
		return min(1.0 - capital_market.LENDER_RESERVE_SHARE, demanded)

	def state_owes(self) -> float:
		"""What the state owes: its claims in the actors' book and the pay it has not paid its army and officials."""
		treasury = self.needs.state_treasury()
		return round(self.needs.debt_owed[treasury.actor_id] + treasury.arrears_owed(), 1)

	def capital_market_report(self) -> Dict[str, Any]:
		"""The market as a player sees it: the rate, what lenders hold and will still advance the founder, and what the state owes."""
		supply = sum(self.needs.lender_offers_made().values()) + self.economy_lending()[0]
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
