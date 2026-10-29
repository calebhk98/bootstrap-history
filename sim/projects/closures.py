"""Why a work is shut and since when: the one place a closure is recorded, and what is asked of the record."""
from . import closure_reasons
from sim.ventures.api import ForgetClosureReason, MothballConcern

from .needed_commands import NoteConcernChange


class Closures:
	# Why a work is shut; the only two writers are close_work and clear_closure.
	CLOSED_FOR_STAFF = closure_reasons.CLOSED_FOR_STAFF
	CLOSED_BY_CHOICE = closure_reasons.CLOSED_BY_CHOICE
	CLOSED_LOSS_MAKING = closure_reasons.CLOSED_LOSS_MAKING
	CLOSED_CREDITOR_SEIZURE = closure_reasons.CLOSED_CREDITOR_SEIZURE

	def close_work(self, node_id, reason, year=None, cascade=True):
		"""Shut a work and record why and since when, in one place. Whatever requires it running shuts with it unless
		`cascade` is off."""
		needs = self.needs
		closing_year = needs.year() if year is None else year
		needs.send(MothballConcern(node_id, closing_year, reason))
		if reason == self.CLOSED_FOR_STAFF:
			self.seat.ever_closed_for_staff.add(node_id)
		needs.send(NoteConcernChange("closure", node_id, reason))
		if cascade:
			self.close_lapsed_dependents(closing_year)

	def closure_of(self, node_id):
		"""The closure record of a currently shut work, else None."""
		if node_id not in self.needs.mothballed():
			return None
		return self.needs.closure_records().get(node_id)

	def clear_closure(self, node_id, reason=None):
		"""Drop a closure record. With a reason, only that reason's record goes."""
		return self.needs.send(ForgetClosureReason(node_id, reason))

	def staff_closure_age(self, node_id):
		"""Years since a staffing closure began, or None if not closed for staff."""
		record = self.closure_of(node_id)
		if record is None or record["reason"] != self.CLOSED_FOR_STAFF:
			return None
		return self.needs.year() - record["year"]

	def ever_closed_for_staff(self):
		"""Every work ever shut for want of staff, kept after it reopens (the live set)."""
		return self.seat.ever_closed_for_staff

	def closed_by_choice(self):
		"""The closure reason of a work the founder shut by choice."""
		return self.CLOSED_BY_CHOICE
