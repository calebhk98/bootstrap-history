"""The workforce module applies the commands that change the acting seat's people, hours and base."""
from sim.assembly.api import Part


class ApplyingPeople(Part):

	def hire_staff(self, command):
		return self.parts.core.labour.hiring.hire(command.trade, command.count)

	def fire_staff(self, command):
		return self.parts.core.labour.hiring.fire(command.trade, command.count)

	def train_staff(self, command):
		return self.parts.core.labour.training.train(command.trade, command.count, command.source)

	def commission_hours(self, command):
		return self.parts.core.labour.commissions.commission(command.trade, command.hours)

	def work_for_wages(self, command):
		return self.parts.core.labour.wages.work_for_wages(command.trade, command.hours)

	def buy_slaves(self, command):
		return self.parts.core.labour.bondage.buy_slaves(command.people)

	def manumit(self, command):
		return self.parts.core.labour.bondage.manumit(command.people)

	def found_trade_school(self, command):
		return self.parts.core.labour.training.found_trade_school(command.trade, command.seats)

	def move_base(self, command):
		return self.parts.core.labour.relocation.move_base(command.tile)
