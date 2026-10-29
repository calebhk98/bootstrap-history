"""What arrears cost the acting seat a year, how they accrue, and the warning that comes before the limit.

Needs: effect_values, standing, acting_balance, cast_state, actor_world, civilisation, money_text, send (NoteSeatCash,
ReviewVentures, RecordEvent)."""
from typing import Any

from sim.agents.api import SeatBorrower, business_review
from sim.ledger.api import NoteSeatCash
from sim.reporting.api import RecordEvent
from sim.world import capital_market

from .affordability import near_limit
from .constants import DEBT_RATE_REPUTATION_DISCOUNT_CAP, DEBT_RATE_REPUTATION_SCALE
from sim.projects.api import ReviewVentures


class Arrears:

	def debt_interest_rate(self) -> float:
		"""What arrears cost the seat a year. It starts from the civilisation's loanable-funds market rate (its own starting rate
		until the market has met), plus a premium for the share of its credit limit it has used. A household with no standing
		borrows from whoever will have it and pays for it: standing is what makes money cheap."""
		needs = self.needs
		discount = sum(discount for _node_id, discount in needs.effect_values("debt_rate_discount"))
		discount += min(DEBT_RATE_REPUTATION_DISCOUNT_CAP, max(0.0, needs.standing()["reputation"]) / DEBT_RATE_REPUTATION_SCALE)
		used = 0.0
		capital = needs.acting_balance()
		if capital < 0:
			limit = self.credit_limit()
			used = -capital / limit if limit > 0 else 1.0
		return capital_market.borrower_rate(self.market_rate(), discount, used)

	def settle_interest(self) -> Any:
		"""The year's interest on the acting seat's debt by the one rule every borrower follows: (the interest owed, the part paid)."""
		needs = self.needs
		seat_id = self.clock.acting_seat
		borrower = SeatBorrower(
			seat_id, needs.cast_state().purses, self.seat, balance=needs.acting_balance,
			note_outlay=lambda purpose, amount: needs.send(NoteSeatCash(seat_id, -1.0, amount, purpose)),
			ceiling=self.credit_limit, rate=self.debt_interest_rate, defaults=lambda: self.default_on_debt(needs.year()))
		return borrower.settle_interest(needs.actor_world())

	def charge_interest(self, year: int) -> float:
		"""Arrears accrue: the household pays its interest by the one rule every borrower follows (`sim/agents/borrowing.py`):
		drawn on its facility within its ceiling, the rest carried as arrears, and a default after too many years of them.
		Answers the interest owed."""
		needs = self.needs
		seat = self.seat
		capital = needs.acting_balance()
		if capital >= 0 and seat.interest_arrears <= 0.0:
			return 0.0
		owed, paid = self.settle_interest()
		seat.interest_paid = (seat.interest_paid or 0.0) + paid
		if owed > 0 and (seat.insolvent_years in (1, 5, 15)):
			rate = self.debt_interest_rate()
			self.needs.send(RecordEvent.of("arrears_interest", "interest on %s of arrears at %.1f%% a year"
				% (needs.money_text(-needs.acting_balance()), rate * 100), rate=rate, unpaid=owed - paid, arrears_years=seat.arrears_years))
		return owed

	def warn_near_the_limit(self, year: int) -> None:
		"""Say it before the creditors do, while there is still a decision left: a limit discovered only by crossing it is an
		ambush. Everything that could still save a household (stop a project, close a loss-maker, let somebody go) has to be on
		offer while there is time to act on it."""
		needs = self.needs
		limit = self.credit_limit()
		seat = self.seat
		capital = needs.acting_balance()
		warn, seat.said_near_limit, used = near_limit(capital, limit, seat.said_near_limit)
		if not warn:
			return
		needs.send(RecordEvent.of("credit_near_limit", "CLOSE TO THE LIMIT: you owe %s of the %s anyone "
			"here will advance you (%d%%). Past it every "
			"project in hand is halted unfinished and nobody "
			"funds new work for some years. 'stop' a project, "
			"'mothball' a loss-maker or 'fire' somebody while "
			"it is still your choice"
			% (needs.money_text(-capital, grouped=True), needs.money_text(limit, grouped=True), used * 100), share_of_limit=used))

	def shed_loss_makers(self, year: int) -> None:
		"""Shut the plants that keep losing money; in arrears with a deficit, stop maintaining anything that costs more than it
		returns (the loss rule of `Business.review`, the same for every owner). A ruined run once held works whose upkeep exceeded
		their revenue, so net income sat near zero for ever: a household lets the loss-makers go the year it notices, and then its
		income is its practice again, which is enough."""
		shed = [closure.entry_key for closure in self.needs.send(ReviewVentures(tuple((business_review.LOSS_MAKING,)), year))]
		if shed:
			in_arrears = self.needs.acting_balance() < 0
			# name them: a bare count tells a player neither which nor how to get it back
			self.needs.send(RecordEvent.of("arrears_closed_concerns", "%sclosed %d concern%s that cost more "
				"than they returned: %s. You still know how; "
				"'restore' reopens one when you can pay for it"
				% ("in arrears, so " if in_arrears else "", len(shed), "" if len(shed) == 1 else "s", ", ".join(shed)), concerns=list(shed)))
