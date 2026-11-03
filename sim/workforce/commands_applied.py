"""The commands the workforce module applies."""
from sim.assembly.api import Part
from sim.reporting.api import RecordEvent

from . import rules
from .state import ONCE_COMMISSION


class Applying(Part):

	def set_employed(self, command):
		"""The acting seat's staff in the trade become `headcount` full-time equivalents, and the hour pools follow."""
		self.parts.core.labour.book.set_employed(command.trade, command.headcount)
		self.parts.core.labour.pools.resync_pools()

	def staff_arrived(self, command):
		"""The labour core's clearing filled the seat's places: its staff in the trade are the people hired."""
		employees = self.seat.employees
		if command.people > 0.0:
			employees[command.trade] = command.people
		else:
			employees.pop(command.trade, None)
		self.parts.core.labour.pools.resync_pools()

	def clearing_settled(self, command):
		"""What the clearing charged the seat for its places is the wages it paid, and what it paid for the hours the seat
		offered of its own is its earnings: last year's wage-work summary (the year closed before the clearing) takes it;
		the offers are spent."""
		seat = self.seat
		offered = sum(seat.hours_offered_for_wages.values())
		seat.hours_offered_for_wages = {}
		seat.wages_paid = command.wages_charged
		pay = command.wage_work_pay
		seat.wages_earned = (seat.wages_earned or 0.0) + pay
		if pay > 0.0:
			last = dict(seat.wage_work_last_year or {"hours": round(offered, 1), "wage_income": 0.0})
			last["wage_income"] = round(last.get("wage_income", 0.0) + pay, 1)
			seat.wage_work_last_year = last
			self.needs.send(RecordEvent.of("wage_work_paid", "wage work: the labour market paid %s for the hours of your own you offered"
			                               % self.needs.money_text(pay, grouped=True, short=True), pay=pay))

	def newcomers_placed(self, command):
		"""The seat's newly trained and granted people are in the labour core now."""
		self.seat.newcomers = {}

	def note_cleared_wage(self, command):
		"""The unskilled hour's wage the clearing set: the last reading becomes the one before."""
		self.world.cleared_wage_before = self.world.cleared_wage
		self.world.cleared_wage = command.wage

	def hours_arrived(self, command):
		"""The clearing filled the seat's one-year order of a purpose; the order is spent."""
		seat = self.seat
		seat.hours_wanted_once.pop(command.purpose, None)
		hired = {trade: hours for trade, hours in command.hours_by_trade.items() if hours > 0.0}
		seat.hours_hired_once[command.purpose] = hired
		if command.purpose == ONCE_COMMISSION:
			for trade, hours in hired.items():
				seat.contract_hours[trade] = seat.contract_hours.get(trade, 0.0) + hours
				seat.commissioned[trade] = seat.commissioned.get(trade, 0.0) + hours

	def post_hours_once(self, command):
		orders = self.seat.hours_wanted_once.setdefault(command.purpose, {})
		orders[command.trade] = orders.get(command.trade, 0.0) + command.hours

	def note_trade_spread(self, command):
		if command.introduced_year is not None:
			self.seat.trade_introduced_year[command.trade] = command.introduced_year
		if command.endemic:
			self.seat.trades_endemic.add(command.trade)

	def lose_staff(self, command):
		seat = self.seat
		before = self.parts.core.labour.ledger.staff_snapshot()
		people_before = seat.scholars + seat.artisans + sum(seat.employees.values())
		self.survive_staff(command.survival_share)
		seat.directors_extra *= command.deputies_share
		self.parts.core.labour.ledger.log_staff_reduction(command.cause, before)
		return {"people_before": people_before, "people_after": seat.scholars + seat.artisans + sum(seat.employees.values())}

	def survive_staff(self, survival_share):
		"""Scholars, artisans and each trade's hired people are scaled by the share, fractions kept; a trade left with nobody is dropped."""
		seat = self.seat
		survive = rules.surviving_people
		seat.scholars = survive(seat.scholars, survival_share)
		seat.artisans = survive(seat.artisans, survival_share)
		for trade in sorted(seat.employees):
			survivors = survive(seat.employees[trade], survival_share)
			if survivors > 0:
				seat.employees[trade] = survivors
			else:
				seat.employees.pop(trade)

	def release_staff(self, command):
		with self.needs.act_as(command.seat_id):
			self.parts.core.labour.hiring.fire(command.trade, command.people)

	def grant_staff(self, command):
		self.parts.core.labour.pools.grant_staff(command.scholars, command.artisans)

