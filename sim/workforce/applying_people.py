"""The workforce module applies the commands that change the acting seat's people, hours and base."""


class ApplyingPeople:

	def hire_staff(self, command):
		return self.labour.hiring.hire(command.trade, command.count)

	def fire_staff(self, command):
		return self.labour.hiring.fire(command.trade, command.count)

	def train_staff(self, command):
		return self.labour.training.train(command.trade, command.count, command.source)

	def commission_hours(self, command):
		return self.labour.commissions.commission(command.trade, command.hours)

	def work_for_wages(self, command):
		return self.labour.wages.work_for_wages(command.trade, command.hours)

	def buy_slaves(self, command):
		return self.labour.bondage.buy_slaves(command.people)

	def manumit(self, command):
		return self.labour.bondage.manumit(command.people)

	def found_trade_school(self, command):
		return self.labour.training.found_trade_school(command.trade, command.seats)

	def move_base(self, command):
		return self.labour.relocation.move_base(command.tile)
