"""How far into arrears anyone will let the acting seat go, what that leaves it to spend and what it costs it to live.

Credit stops long before debt is unbounded, and the moment it stops the household is merely poor, which is recoverable. What it can
borrow depends on who will stand behind it: the standing earning, its name, the land it holds as collateral.
Needs: revenue_capacity, revenue_estimate, upkeep, standing, forest_hectares, effect_sum, effect_values, civilisation, price_index,
acting_balance, money_per_labour_hour, wage_bill, household_bill_per_person, household_dependant_people, committed_cost,
mine_operating_cost, agent_credit_room."""
from typing import Any, Dict, Optional, Tuple

from sim.projects.api import funding as project_funding

from . import rules
from .affordability import appearances_spending, spending_power_of
from .constants import (CREDIT_LINE_EARNING_MULTIPLE, CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE,
                        CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA, CREDIT_LINE_LABOUR_HOURS_PER_REPUTATION_POINT,
                        CREDIT_SURPLUS_YEARS_MULTIPLE, LIVING_COST_APPEARANCES_SHARE_OF_ROOM, LIVING_COST_STATUS_PER_CAPITAL,
                        SPENDING_DRAW_SHARE_ORDINARY)


class CreditLine:

	def priced(self, hours: float) -> float:
		"""A count of labour hours as money in the civilisation's coin."""
		return hours * self.needs.money_per_labour_hour()

	def bearable_part_of(self, amount: float) -> float:
		"""How much of `amount` the purse and the credit line can take without capital ending below the negative of the limit.
		The limit is read at the capital left after paying, because the floor (living cost) carries a status term that shrinks as
		positive capital goes."""
		held = self.needs.acting_balance()
		return rules.bearable_part(amount, held, self.credit_limit(capital=held - amount))

	def credit_line_sought(self, revenue: Optional[float] = None, upkeep: Optional[float] = None,
	                       capital: Optional[float] = None) -> Tuple[float, float, float]:
		"""The credit line the acting seat asks lenders for, before the market's room: (the raw line its name and earning give,
		the running-cost floor, the most its earning can service), in the household's real units.

		`revenue` and `upkeep`: an already-worked-out figure the caller holds, handed to `living_cost` unchanged. The earning
		below is the standing one (this year's wage-selling zeroed out), never the same call `revenue` would have been worked out
		with. `capital`: the capital to read the floor at, instead of what the household holds now."""
		needs = self.needs
		# strangers borrow almost nothing: credit rests on standing income, not on this year's takings
		earning = needs.revenue_capacity()
		base = earning * CREDIT_LINE_EARNING_MULTIPLE
		base = needs.effect_sum("credit_line", base)    # a collegium's credit is linear in its units: collateral, not fame
		base += max(0.0, needs.standing()["reputation"]) * self.priced(CREDIT_LINE_LABOUR_HOURS_PER_REPUTATION_POINT)
		base += needs.forest_hectares() * self.priced(CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA)   # land is real collateral
		upkeep_amount = needs.upkeep() if upkeep is None else upkeep
		# everyone can run a tab for a season: a year's running costs, priced at the standing income
		floor = self.living_cost(revenue=earning if revenue is None else revenue, upkeep=upkeep_amount, capital=capital) \
			+ upkeep_amount * CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE
		# no lender advances more than income can carry. The years of earning a lender will carry are the opening figure, less
		# when money has grown dearer than at the start; cheaper money from society's saving does not enlarge what this borrower
		# can carry.
		market_rate = self.market_rate()
		years = CREDIT_SURPLUS_YEARS_MULTIPLE
		if market_rate > 0:
			years *= min(1.0, needs.civilisation()["starting_interest_rate"] / market_rate)
		# the running tab carries interest too, so only the earning left after that interest backs new advances
		serviceable = floor + max(0.0, earning - floor * market_rate) * years
		return base, floor, serviceable

	def credit_limit(self, revenue: Optional[float] = None, upkeep: Optional[float] = None, capital: Optional[float] = None) -> float:
		"""How far into arrears anyone will actually let the seat go: the line its own standing earns (`credit_line_sought`),
		never more than lenders still hold beyond what everyone else owes them (the room the credit market's clearing granted this
		borrower), never less than a year's running costs."""
		base, floor, serviceable = self.credit_line_sought(revenue, upkeep, capital)
		room = self.credit_room(self.clock.acting_seat)
		price_index = self.needs.price_index()
		return rules.calculate_credit_ceiling(base, floor, serviceable, price_index, None if room is None else room / price_index)

	def funding_capacity(self) -> float:
		"""What the seat can actually expect to have to spend on projects: cash in hand, the drawable half of the credit line
		(the rest stays in reserve against ordinary running costs) and the surplus its standing income can add over the planning
		years once fixed costs and today's arrears interest are paid. It is compared with what work in hand still owes: the
		aggregate question is committed cost within funding capacity, not any one project's cost alone."""
		breakdown = self.funding_breakdown()
		return breakdown["cash_on_hand"] + breakdown["credit_available_now"] + breakdown["surplus_allowance_over_years"]

	def funding_breakdown(self) -> Dict[str, float]:
		"""The parts `funding_capacity` adds, kept apart: cash, the drawable half of the credit line, the surplus allowance (the
		yearly surplus over the planning years), the yearly surplus itself, and what work in hand still owes."""
		needs = self.needs
		revenue = needs.revenue_estimate()
		upkeep_amount = needs.upkeep()
		capital = needs.acting_balance()
		return project_funding.funding_parts(
			capital, revenue, upkeep_amount + self.living_cost(revenue=revenue, upkeep=upkeep_amount) + needs.mine_operating_cost(),
			self.debt_interest_rate() if capital < 0 else 0.0, self.credit_limit(revenue=revenue, upkeep=upkeep_amount),
			SPENDING_DRAW_SHARE_ORDINARY, CREDIT_SURPLUS_YEARS_MULTIPLE, needs.committed_cost())

	def spending_power(self, kind: str = "buy") -> float:
		"""What the seat could actually raise, by what it means to spend it on. The debt it already carries counts against it
		(the credit limit is a floor on capital, not headroom to add to a debt), and the floor belongs on the answer: nothing can
		be raised past the line. The one exception is `open`, a door on a concern already built and earning, which asks only
		what the line could advance."""
		return spending_power_of(kind, self.needs.acting_balance(), self.credit_limit(), SPENDING_DRAW_SHARE_ORDINARY)

	def dependants_cost(self) -> float:
		"""The part of the living cost that keeps the household's dependants: people with the same needs as the founder."""
		return self.needs.household_dependant_people() * self.needs.household_bill_per_person()

	def living_cost(self, revenue: Optional[float] = None, upkeep: Optional[float] = None, capital: Optional[float] = None) -> float:
		"""What the household must pay a year: to eat and sleep, to pay tax, to keep up appearances and to pay its staff. In a
		patronage society a man seeking status must spend on it, and the expense rises with his wealth and his standing; a ruined
		man stops keeping up appearances, so it is capped by what is left after eating.

		`revenue` and `upkeep`: an already-worked-out figure a caller may hand in to skip a second copy of the same call; nothing
		moves between the caller's call and this one. `capital`: the capital the status spending is read at, instead of the
		household's own."""
		needs = self.needs
		price_index = needs.price_index()   # at this society's prices: bread costs what bread costs where you are
		rev = needs.revenue_estimate() if revenue is None else revenue
		wages = needs.wage_bill()
		capital = needs.acting_balance() if capital is None else capital
		base = needs.household_bill_per_person()    # the founder's own needs
		household = self.dependants_cost()
		tax = max(0.0, rev) * needs.civilisation()["starting_tax_share"]
		status = 0.0
		for _node_id, upkeep_of_status in needs.effect_values("living_cost_status"):
			status += upkeep_of_status * price_index
		upkeep_amount = needs.upkeep() if upkeep is None else upkeep
		# appearances come out of what is left after eating, never more than the nominal figure
		room = max(0.0, rev - base - household - tax - upkeep_amount - wages)
		status = appearances_spending(status, capital, room, LIVING_COST_STATUS_PER_CAPITAL, LIVING_COST_APPEARANCES_SHARE_OF_ROOM)
		return rules.living_cost_total(base, household, tax, status, wages)
