"""What debt costs against what the household earns every year, and how to tell a run that has stopped.

The formal credit ceiling (`credit_limit`) says how much anyone will lend; this says how much debt the recurring surplus can carry.
Needs: revenue_capacity, upkeep, mine_operating_cost, acting_balance, held_trade, wage_bill, tree_nodes, operating, money_text,
hours_for_sale, best_wage_trade, work_for_wages_dry_run, standing_job_pay."""
from typing import Any, Dict, Optional

from . import rules
from .constants import DEBT_SERVICE_SHARE_OF_SURPLUS
from .credit_freeze import STALL_MINIMUM_INSOLVENT_YEARS, is_stalled, loss_makers, standing_net


class DebtService:

	def recurring_net_before_interest(self) -> float:
		"""Standing revenue less every standing cost, for an ordinary next year: wages count in full, so a hiring advance paid this
		year does not flatter it."""
		revenue = self.needs.revenue_capacity()
		upkeep = self.needs.upkeep()
		return revenue - upkeep - self.recurring_living_cost(revenue, upkeep) - self.needs.mine_operating_cost()

	def dependants_beyond_means(self, living: float, revenue: float, upkeep: float, mine_cost: float = 0.0) -> float:
		"""The part of the dependants' cost the household cannot carry this year: what its income leaves after upkeep, mine costs,
		the rest of its living cost and the interest on any arrears. A household with savings keeps all that surplus for its
		dependants (its savings are not spent on them); one in arrears also pays the creditors their share of it
		(DEBT_SERVICE_SHARE_OF_SURPLUS). Either way it lives within its income, as a society household of the same income does."""
		return rules.dependants_beyond_means_of(
			self.needs.acting_balance(), self.dependants_cost(), living, revenue, upkeep, mine_cost,
			self.debt_interest_rate(), DEBT_SERVICE_SHARE_OF_SURPLUS)

	def recurring_living_cost(self, revenue: float, upkeep: float) -> float:
		"""The living cost of an ordinary next year: what is paid once the dependants the income cannot carry are shed."""
		living = self.living_cost(revenue=revenue, upkeep=upkeep)
		return living - self.dependants_beyond_means(living, revenue, upkeep, self.needs.mine_operating_cost())

	def recurring_net(self) -> float:
		"""Recurring net after the interest the arrears cost now."""
		return rules.net_after_interest(self.recurring_net_before_interest(), self.needs.acting_balance(), self.debt_interest_rate())

	def interest_on_arrears(self) -> float:
		"""This year's interest on the household's debt at the rate it pays."""
		return rules.interest_on_arrears(self.needs.acting_balance(), self.debt_interest_rate())

	def debt_service_share_of_surplus(self) -> float:
		"""How much of the yearly surplus may go on arrears interest before a debt is called unsustainable."""
		return DEBT_SERVICE_SHARE_OF_SURPLUS

	def sustainable_debt(self) -> float:
		"""The largest debt whose yearly interest stays within the allowed share of the recurring surplus (zero when there is no
		surplus)."""
		rate = self.debt_interest_rate()
		surplus = self.recurring_net_before_interest()
		if rate <= 0:
			return 0.0
		return max(0.0, surplus * DEBT_SERVICE_SHARE_OF_SURPLUS / rate)

	def debt_service_forecast(self, draw: float) -> Dict[str, Any]:
		"""Interest on a debt of `draw`, against the surplus, beside the formal ceiling."""
		surplus = self.recurring_net_before_interest()
		interest = draw * self.debt_interest_rate()
		return {
			"interest_per_year_at_that_draw": round(interest, 1),
			"recurring_surplus_before_interest": round(surplus, 1),
			"interest_as_share_of_recurring_surplus": round(interest / surplus, 2) if surplus > 0 else None,
			"sustainable_debt": round(self.sustainable_debt(), 1),
			"sustainable_debt_means": (
				"the largest debt whose yearly interest stays within %d%% of "
				"your recurring surplus; the credit limit is only what "
				"lenders will allow, not a safe level"
				% round(DEBT_SERVICE_SHARE_OF_SURPLUS * 100)),
		}

	def stall_diagnosis(self) -> Optional[Dict[str, Any]]:
		"""None if the run is going somewhere; otherwise what is wrong and what would actually change it. A bad purchase early
		can lock a player out of the goal for the rest of the game while the game goes on accepting commands; the state is not a
		dead end (working for wages is among the ways out) but nothing says so, and a game that has effectively stopped has to say
		so and say what would restart it."""
		needs = self.needs
		seat = self.seat
		capital = needs.acting_balance()
		insolvent_years = seat.insolvent_years
		if capital >= 0 or insolvent_years < STALL_MINIMUM_INSOLVENT_YEARS:
			return None
		# interest on the arrears counts; the standing revenue matches the ledger
		interest = max(0.0, -capital) * self.debt_interest_rate()
		standing_revenue = needs.revenue_capacity()
		standing_upkeep = needs.upkeep()
		standing_living = self.living_cost(revenue=standing_revenue, upkeep=standing_upkeep)
		net = standing_net(standing_revenue, standing_upkeep, standing_living, needs.mine_operating_cost(), interest)
		if not is_stalled(capital, insolvent_years, net):
			return None
		ways = []
		hours = needs.hours_for_sale()
		if hours > 100:
			# only suggest work that pays more than the standing job already sells these hours for: the best-paying open trade,
			# quoted by running the sale itself
			best_trade = needs.best_wage_trade()
			if best_trade:
				would_earn, _refusal = needs.work_for_wages_dry_run(best_trade, hours)
				standing = needs.standing_job_pay[needs.held_trade()]
				if would_earn > standing:
					ways.append("work as a %s: %.0f of your own hours are left "
					            "this year and would bring in about %s%s. "
					            "Nobody has to lend you anything for that"
					            % (best_trade, hours, needs.money_text(would_earn, grouped=True),
					               (" against the %s your standing job pays for them, so you are up %s"
					                % (needs.money_text(standing, grouped=True), needs.money_text(would_earn - standing, grouped=True)))
					               if standing > 0.5 else ""))
		nodes = needs.tree_nodes()
		operating = needs.operating()
		losers = loss_makers(operating, {node_id: nodes[node_id]["rev"] for node_id in operating},
		                     {node_id: nodes[node_id]["up"] for node_id in operating})
		if losers:
			ways.append("close what costs more than it brings in: %s"
			            % ", ".join("%s (%+.0f a year)" % (node_id, nodes[node_id]["rev"] - nodes[node_id]["up"]) for node_id in losers[:3]))
		if needs.wage_bill() > 0:
			ways.append("let people go: your payroll is %s a year" % needs.money_text(needs.wage_bill(), grouped=True))
		if needs.mine_operating_cost() > 0:
			ways.append("close a mine: they cost %s a year whether you use them "
			            "or not" % needs.money_text(needs.mine_operating_cost(), grouped=True))
		if not ways:
			ways.append("there is nothing left to cut; your living costs alone "
			            "exceed what you earn, and only new income will move it")
		if interest > 0.5:
			ways.append("%s of that %s is interest on the arrears themselves, "
			            "which is the one cost that goes away as the balance "
			            "comes back up" % (needs.money_text(interest, grouped=True), needs.money_text(-net, grouped=True)))
		return {"you_are_stuck": ("you have been in arrears %d years and you "
		                          "lose %s a year, so nothing you start "
		                          "will ever be paid for" % (seat.insolvent_years, needs.money_text(-net, grouped=True))),
		        "this_is_not_the_end_of_the_run": ("it is escapable, and none of "
		                                           "these need anybody to lend "
		                                           "you a denarius"),
		        "what_would_change_it": ways}
