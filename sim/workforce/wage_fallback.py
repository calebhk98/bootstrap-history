"""The wage-work fallback: a household with no work and thin means sells its idle hours for wages."""
from sim.assembly.api import Part
from sim.refusal import Refusal

from .constants import WAGE_FALLBACK_LIVING_COST_YEARS, WAGE_FALLBACK_MAX_HOURS, WAGE_FALLBACK_MIN_HOURS


class WageFallback(Part):

	def take_wage_fallback(self, command):
		remaining = command.remaining_hours
		# with no work and thin means the household sells its idle hours for wages, as a player does with `work`
		if (not self.needs.automation()["manual"] and remaining > WAGE_FALLBACK_MIN_HOURS
				and (self.needs.acting_balance() < self.needs.living_cost() * WAGE_FALLBACK_LIVING_COST_YEARS
				     or not self.needs.active_projects())):
			trade = self.parts.core.labour.hands.wage_fallback_trade()
			hours = min(remaining, WAGE_FALLBACK_MAX_HOURS)
			# ONLY IF IT PAYS BETTER THAN THE STANDING JOB IT TAKES THE HOURS FROM: a founder who already
			# sells these hours in a trade does not move them to a worse-paid one.
			held_trade = self.needs.held_trade()
			standing_pay = (self.parts.core.labour.wages.wage_for_hours(held_trade, hours) if held_trade else 0.0)
			if self.parts.core.labour.wages.wage_for_hours(trade, hours) > standing_pay:
				_, answer = self.parts.core.labour.wages.work_for_wages(trade, hours)
				# Kept in step with `remaining` so hours_this_year does not count hours sold for wages here as
				# still unused. A refusal has a cause; any other answer is a warning on a sale that happened.
				if not isinstance(answer, Refusal):
					remaining -= hours
		return remaining
