"""The end of the seat's year of hours: where they went is kept, and the tallies reset for the next year."""


class HoursYear:

	def close_hours_year(self, command):
		workforce = self.seat
		# WHERE THE YEAR'S HOURS WENT: captured here, before the tallies below reset for the next year, the same way
		# spend_last_year already captures the year's spending, so a player can see the breakdown as `hours_this_year` in
		# `state` rather than only a final hours-left figure with no way to tell where the rest went.
		workforce.hours_this_year = {
			"available": round(self.labour.director_pool(), 1),
			"wage_work": round(workforce.wage_hours_this_year, 1),
			"teaching": round(workforce.teaching_hours_this_year, 1),
			"moving": round(workforce.relocation_hours_this_year or 0.0, 1),
			"supervising": round(workforce.supervision_hours_this_year, 1),
			"offered_to_projects": round(max(0.0, command.pool - command.remaining_after_projects), 1),
			# OFFERED is what projects were given a shot at; EFFECTIVE is what actually reduced their founder_hours_left. The
			# gap between the two is hours that went in and came straight back out again because a trade or the money to
			# pay for it fell short that year - see hours_offered_this_year / hours_effective_this_year on each project in
			# `active`, and underfunded_this_year.
			"effective_on_projects": round(command.hours_effective_total, 1),
			"unused": round(max(0.0, command.remaining), 1),
		}
		# Reset AFTER the progress pass, which is where the hours you sold are subtracted from the hours you have left to
		# direct.
		self.labour.close_wage_year()
		# Contracted work is bought for a year and expires with it: hours you paid a shop for in 142 are not still sitting
		# there in 143.
		workforce.contract_hours = {}
		workforce.teaching_hours_this_year = 0.0
		workforce.relocation_hours_this_year = 0.0
		workforce.supervision_hours_this_year = 0.0
