"""What the yearly staff step does to the household's standing bid in the labour core: grow a trade's places toward a target.
The people arrive at the year's clearing (sim/markets/port_staff.py)."""
from sim.reporting.api import RecordAutomation, RecordAutomationSkip

from sim.labour.api import stochastic_round

from .staff_phase_rules import hires_needed

MIN_STAFF_GONE_TO_LOG = 0.005


class StaffHiring:

	def grow_trade_toward(self, trade, want, closure_need=0.0):
		"""Post places for a trade up to (or release it down to) the whole-person target drawn from `want`, through
		`hire_buying_room` so every rule a player meets applies. A refusal is not an error: it is recorded as a skip when
		shut concerns need the hands."""
		workforce = self.seat
		have = max(workforce.employees.get(trade, 0.0), workforce.staff_wanted.get(trade, 0.0))
		change = hires_needed(have, stochastic_round(self.needs.game_random(), want))
		if change > 0:
			before = self.needs.acting_balance()
			hired, why = self.labour.controls.hire_buying_room(trade, change)
			if not hired and closure_need >= 1.0:
				self.needs.send(RecordAutomationSkip("auto_hire", "hire %d %s" % (change, trade),
				                                     "concerns shut for want of staff need %.1f more: %s" % (closure_need, why)))
			if hired:
				self.needs.send(RecordAutomation("auto_hire", "hire", "%d %s" % (change, trade),
				                                 "staff target %.1f against %.1f held, with %.1f supervision room"
				                                 % (want, have, self.labour.capacity.supervision_room()), before))
		elif change < 0:
			before = self.needs.acting_balance()
			self.labour.hiring.fire(trade, -change)
			self.needs.send(RecordAutomation("auto_hire", "release", "%d %s" % (-change, trade),
			                                 "staff target %.1f is below the %.1f held" % (want, have), before))
