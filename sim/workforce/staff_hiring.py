"""What the yearly staff step does to the staff once it knows what was lost or wanted: rehire, grow a trade toward a target,
and let go the part of the payroll the household cannot meet."""
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent

from .payroll_trim import staff_to_let_go
from .staff_phase_rules import hires_needed

MIN_STAFF_GONE_TO_LOG = 0.005


class StaffHiring:

	def replace_lost_staff(self, lost):
		"""Hire each trade back up to the people it lost to attrition this year, through `hire` so every rule a
		player meets applies; a refusal is recorded as a skipped action. `lost` is {trade: people}."""
		household = self.needs.legacy_acting_household()
		workforce = self.seat
		for trade, people in sorted(lost.items()):
			before = household.capital
			have = workforce.employees.get(trade, 0.0)
			hired, refusal = self.labour.hire_buying_room(trade, int(people))
			if not hired:
				self.needs.send(RecordAutomationSkip("auto_hire", "replace %d %s" % (people, trade), "replace-only mode: " + str(refusal)))
				continue
			found = round(workforce.employees.get(trade, 0.0) - have)
			self.needs.send(RecordAutomation("auto_hire", "replace", "%d %s" % (found, trade),
			                                 "replace-only mode: %d lost this year, none hired beyond that" % people, before))

	def grow_trade_toward(self, trade, want, closure_need=0.0):
		"""Hire a trade up to (or release it down to) the whole-person target drawn from `want`, through `hire_buying_room`
		so every rule a player meets applies. A refusal is not an error: it is recorded as a skip when shut concerns need
		the hands. A hire's audit row names the people the market found, which can be fewer than sought."""
		household = self.needs.legacy_acting_household()
		workforce = self.seat
		have = workforce.employees.get(trade, 0.0)
		change = hires_needed(have, self.labour.stochastic_round(want))
		if change > 0:
			before = household.capital
			hired, why = self.labour.hire_buying_room(trade, change)
			if not hired and closure_need >= 1.0:
				self.needs.send(RecordAutomationSkip("auto_hire", "hire %d %s" % (change, trade),
				                                     "concerns shut for want of staff need %.1f more: %s" % (closure_need, why)))
			if hired:
				found = round(workforce.employees.get(trade, 0.0) - have)
				self.needs.send(RecordAutomation("auto_hire", "hire", "%d %s" % (found, trade),
				                                 "staff target %.1f against %.1f held, with %.1f supervision room"
				                                 % (want, have, self.labour.supervision_room()), before))
		elif change < 0:
			before = household.capital
			self.labour.fire(trade, -change)
			self.needs.send(RecordAutomation("auto_hire", "release", "%d %s" % (-change, trade),
			                                 "staff target %.1f is below the %.1f held" % (want, have), before))

	def shed_unpayable_staff(self, payroll, can_pay):
		"""Let go the part of `payroll` that `can_pay` does not cover: whole people, dearest trade first. Logs
		`staff_left_unpaid` with the people gone when any went; returns the people gone."""
		workforce = self.seat
		labour = self.labour
		if payroll <= can_pay or not workforce.employees:
			return 0.0
		gone = 0.0
		staff_before = labour.staff_snapshot()
		for trade_id, cut in staff_to_let_go(payroll, can_pay, dict(workforce.employees), labour.market.quote_annual).items():
			labour.add_employed(trade_id, -cut)
			gone += cut
			if labour.employed(trade_id) < 0.5:
				labour.set_employed(trade_id, 0.0)
		labour.resync_pools()
		labour.log_staff_reduction("a payroll you cannot meet", staff_before)
		if gone > MIN_STAFF_GONE_TO_LOG:
			self.needs.send(RecordEvent.of("staff_left_unpaid",
			                               "you cannot pay everyone: %.1f of your staff leave for work that pays" % gone, staff_gone=gone))
		return gone
