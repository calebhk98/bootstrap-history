"""The wage-work fallback: a household with no work and thin means sells its idle hours for wages."""
from .constants import WAGE_FALLBACK_LIVING_COST_YEARS, WAGE_FALLBACK_MAX_HOURS, WAGE_FALLBACK_MIN_HOURS


class WageFallback:

	def take_wage_fallback(self, command):
		remaining = command.remaining_hours
		# 5b. IF THERE IS NO WORK AND NO MONEY, TAKE A JOB. A man who arrives
		#     with four hundred denarii and a lens does not sit watching his
		#     savings run out; he teaches, or writes, or sets bones for money. It
		#     is in the protocol as `work` for a player and the optimizer had no
		#     equivalent, so a single bad year in the opening decade could end a
		#     run: one Rome seed earned four technologies in five hundred years
		#     because a fire in 103 took a fifth of everything it had.
		household = self.needs.legacy_acting_household()
		if (not self.needs.automation()["manual"] and remaining > WAGE_FALLBACK_MIN_HOURS
				and (household.capital < self.needs.living_cost() * WAGE_FALLBACK_LIVING_COST_YEARS
				     or not self.needs.legacy_projects().active)):
			trade = ("scholar" if self.labour.effective_scholars() >= 1 else "scribe")
			hours = min(remaining, WAGE_FALLBACK_MAX_HOURS)
			# ONLY IF IT PAYS BETTER THAN THE STANDING JOB IT TAKES THE HOURS FROM: a founder who already
			# sells these hours in a trade does not move them to a worse-paid one.
			held_trade = self.needs.held_trade()
			standing_pay = (self.labour.wage_for_hours(held_trade, hours) if held_trade else 0.0)
			if self.labour.wage_for_hours(trade, hours) > standing_pay:
				_, err = self.labour.work_for_wages(trade, hours)
				# Kept in step with `remaining` so hours_this_year does not count hours sold for wages here as
				# still unused.
				if err is None:
					remaining -= hours
		return remaining
