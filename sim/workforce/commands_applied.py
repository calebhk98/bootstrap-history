"""The commands the workforce module applies."""
from . import rules


class Applying:

	def set_employed(self, command):
		"""The acting seat's staff in the trade become `headcount` full-time equivalents, and the hour pools follow."""
		self.labour.set_employed(command.trade, command.headcount)
		self.labour.resync_pools()

	def note_trade_spread(self, command):
		if command.introduced_year is not None:
			self.seat.trade_introduced_year[command.trade] = command.introduced_year
		if command.endemic:
			self.seat.trades_endemic.add(command.trade)

	def press_labour(self, command):
		self.labour.market.press(command.trade, command.hours)

	def lose_staff(self, command):
		seat = self.seat
		before = self.labour.staff_snapshot()
		people_before = seat.scholars + seat.artisans + sum(seat.employees.values())
		self.survive_staff(command.survival_share)
		seat.directors_extra *= command.deputies_share
		self.labour.log_staff_reduction(command.cause, before)
		return {"people_before": people_before, "people_after": seat.scholars + seat.artisans + sum(seat.employees.values())}

	def survive_staff(self, survival_share):
		"""Each scholar, artisan and hired person survives with the share, rolled one by one; a trade left with nobody is dropped."""
		seat = self.seat
		dice = self.needs.game_random()
		survive = rules.surviving_people
		seat.scholars = survive(dice, seat.scholars, survival_share)
		seat.artisans = survive(dice, seat.artisans, survival_share)
		for trade in sorted(seat.employees):
			survivors = survive(dice, seat.employees[trade], survival_share)
			if survivors > 0:
				seat.employees[trade] = survivors
			else:
				seat.employees.pop(trade)

	def release_staff(self, command):
		with self.needs.act_as(command.seat_id):
			self.labour.fire(command.trade, command.people)

	def grant_staff(self, command):
		self.labour.grant_staff(command.scholars, command.artisans)

	def allocate_farm_workforce(self, command):
		return self.labour.allocate_farm_workforce(command.adult_equivalent_population)

	def apply_land_clearing(self, command):
		self.labour.apply_land_clearing()

	def update_wages(self, command):
		self.labour.update_wages()
