"""The commands the workforce module applies."""
from . import rules


class Applying:

	def set_employed(self, command):
		"""The acting seat's staff in the trade become `headcount` full-time equivalents, and the hour pools follow."""
		self.labour.set_employed(command.trade, command.headcount)
		self.labour.resync_pools()

	def note_trade_spread(self, command):
		household = self.needs.legacy_acting_household()
		if command.introduced_year is not None:
			household.trade_introduced_year[command.trade] = command.introduced_year
		if command.endemic:
			household.trades_endemic.add(command.trade)

	def press_labour(self, command):
		self.labour.market.press(command.trade, command.hours)

	def survive_staff(self, command):
		household = self.needs.legacy_acting_household()
		dice = self.needs.legacy_dice()
		survive = rules.surviving_people
		household.scholars = survive(dice, household.scholars, command.survival_share)
		household.artisans = survive(dice, household.artisans, command.survival_share)
		for trade in sorted(household.employees):
			survivors = survive(dice, household.employees[trade], command.survival_share)
			if survivors > 0:
				household.employees[trade] = survivors
			else:
				household.employees.pop(trade)

	def scale_deputies(self, command):
		self.needs.legacy_acting_household().directors_extra *= command.share

	def report_staff_reduction(self, command):
		self.labour.log_staff_reduction(command.cause, command.before)

	def allocate_farm_workforce(self, command):
		return self.labour.allocate_farm_workforce(command.adult_equivalent_population)

	def apply_land_clearing(self, command):
		self.labour.apply_land_clearing()

	def update_wages(self, command):
		self.labour.update_wages()
