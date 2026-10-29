"""How likely an attempt is to fail, and how many years an attempt of this kind takes.

effective_risk answers how likely THIS attempt is to fail, given how many times it already has; calendar_floor and
expected_calendar_years answer how many years, at best and on average across retries, an attempt takes."""
from sim.production.api import depth_risk_multiplier

from .completion_schedule import (calendar_floor_years, earliest_completion_years, expected_years_to_succeed,
                                  payment_schedule_years)
from .constants import (CALENDAR_FLOOR_MIN_YEARS, CALENDAR_FLOOR_REPUTATION_SCALE, CONTROL_RELIEF_FACTOR,
                        DIFFUSION_LIMITED_YEARS_THRESHOLD, RETRY_CALENDAR_CAP, RETRY_CALENDAR_DECAY)
from .failure_diagnosis import failure_teaches
from .retry_calendar import retry_calendar_retain
from .risk_rules import control_relief_multiplier, effective_risk_of


class Risk:
	def _retry_calendar_retain(self, node_id, attempt_index=None):
		# The real failure count still drives every actual retry; `attempt_index` only lets a projection ask about a
		# hypothetical one.
		if attempt_index is None:
			attempt_index = self.needs.legacy_projects().failed_attempts.get(node_id, 0)
		return retry_calendar_retain(RETRY_CALENDAR_CAP, RETRY_CALENDAR_DECAY, attempt_index)

	def _control_relief_multiplier(self, node_id):
		relief = self.needs.mechanic["failure_relief"]
		done = self.needs.techniques_held()
		in_force = [relief[relief_id]["failure_kind"] for relief_id in tuple(relief) if relief_id in done]
		return control_relief_multiplier(self.needs.tree_nodes()[node_id].get("failure_kind"), in_force, CONTROL_RELIEF_FACTOR)

	def effective_risk(self, node_id, precaution=None):
		"""This node's actual chance of failing on its NEXT attempt, after whatever running the technique, and failing at
		it, has already taught (the industry's depth), whatever control-theory relief a completed process controller has
		earned it and whatever a bought precaution relieves. `precaution` None reads the running project's own choice;
		True or False quotes the node as if it were bought or not. Equal to the bare node risk the first time anything is
		tried, with no controller built."""
		bought = self.precaution_chosen(node_id) if precaution is None else precaution
		# Running the technique and failing at it are one stock of experience.
		learned = depth_risk_multiplier(self.needs.industry_depth[node_id])
		return effective_risk_of(self.needs.tree_nodes()[node_id]["risk"], learned, self._control_relief_multiplier(node_id),
		                         self.precaution_relief(node_id, bought))

	def calendar_floor(self, node_id):
		"""Calendar years THIS attempt needs to elapse before a completion roll can fire at all - the SAME formula the
		year uses to gate `_complete`, not a second copy of it. Diffusion-limited nodes (yrs >= 5) shrink as reputation
		grows: a civilisation that already does a hundred complicated things does not start the social diffusion of the
		hundred-and-first from zero credibility."""
		return calendar_floor_years(
			self.needs.tree_nodes()[node_id]["yrs"], self.needs.standing()["reputation"], self.rebuild_work_factor(node_id),
			DIFFUSION_LIMITED_YEARS_THRESHOLD, CALENDAR_FLOOR_MIN_YEARS, CALENDAR_FLOOR_REPUTATION_SCALE)

	def payment_schedule_years(self, node_id):
		"""Years the bill takes to pay in full: it is paid in equal yearly instalments over the node's nominal years,
		which reputation never shortens."""
		return payment_schedule_years(self.needs.tree_nodes()[node_id]["yrs"], self.rebuild_work_factor(node_id))

	def earliest_completion_years(self, node_id):
		"""The soonest the project can finish, with no failure: the longer of the calendar floor and the payment
		schedule, less what a running attempt has already served."""
		running = self.needs.legacy_projects().active.get(node_id)
		return earliest_completion_years(self.calendar_floor(node_id), self.payment_schedule_years(node_id),
		                                 running.get("yrs", 0.0) if running else None)

	def expected_calendar_years(self, node_id, _max_extra_attempts=500):
		"""Expected calendar years to SUCCEED at node_id, counting every retry the dice force - not the bare
		calendar_floor, and not a plain geometric series on the raw risk field either. A failure does not roll the exact
		same dice again: the per-attempt risk and the per-attempt wait both move on every subsequent attempt, so the true
		expectation is a sum over "the first i attempts all failed" with a shrinking risk and a shrinking wait at each step.

		THE RISK TERM IS READ FROM effective_risk(node_id), NEVER REIMPLEMENTED: to ask "what would attempt i+1's odds be"
		for a hypothetical future i without recording a failure, this stands in for "i failures so far" by briefly setting
		the failure count to i and adding i diagnosed failures to the industry's stock (`failed_attempts_trial`), reads
		effective_risk, and restores both in a `finally`, so a real count is never left clobbered. The calendar term is
		asked the same way, via its own `attempt_index`.

		Three assumptions, stated because a wrong number here is worse than none:
		1. The calendar floor used is TODAY's (today's reputation). It can only shrink as reputation grows, so if anything
		   this slightly OVERSTATES the wait for a civilisation still climbing - never understates it.
		2. Hours and money are assumed never to bind once the floor does. A project still starved of hours or cash will
		   take longer than this says, for reasons this number is not trying to capture.
		3. Attempts keep retrying automatically without the project being manually `stop`ped in between, which is how the
		   engine runs retries: a failure never removes a project from `active`, only shrinks its clock and its odds.
		"""
		floor = max(self.calendar_floor(node_id), self.payment_schedule_years(node_id))
		projects = self.needs.legacy_projects()
		initial_failed_attempts = projects.failed_attempts.get(node_id, 0)
		teaches = failure_teaches(self.needs.mechanic["diagnosis_instrument"].get(node_id), self.needs.techniques_held())
		_had_key = node_id in projects.failed_attempts
		_active = projects.active.get(node_id) if node_id in projects.active else None

		def risk_after(attempt_index):
			# Stand in for i failures, read effective_risk (restored in the finally below).
			projects.failed_attempts[node_id] = attempt_index
			# Failures nobody can diagnose add nothing to the learning.
			with self.needs.failed_attempts_trial(node_id, attempt_index - initial_failed_attempts if teaches else 0):
				return self.effective_risk(node_id)

		try:
			return expected_years_to_succeed(
				floor, _active.get("yrs", 0.0) if _active is not None else None, initial_failed_attempts,
				lambda attempt_index: self._retry_calendar_retain(node_id, attempt_index), risk_after,
				_max_extra_attempts)
		finally:
			if _had_key:
				projects.failed_attempts[node_id] = initial_failed_attempts
			else:
				projects.failed_attempts.pop(node_id, None)
