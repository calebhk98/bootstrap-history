"""The outside-facing compatibility property surface for the authoritative SimulationState.

These properties provide backward-compatibility for external consumers and
integration test assertions. Internal simulation code accesses live state
directly through authoritative subsystem owners:
  - self.state.household
  - self.state.projects
  - self.state.economy
  - self.state.founder
  - self.state.scenario

Properties are categorized strictly by owning subsystem.
"""
from typing import Any, Iterable, Set

from sim.seats.api import EndRun


class ForwardingPropertiesMixin:
	"""Composition point: backward-compatibility property facade delegating to
	authoritative subsystem live state.
	"""
	# =========================================================================
	# HouseholdState Compatibility Properties
	# =========================================================================

	@property
	def capital(self):
		return getattr(self.state.household, "capital")

	@capital.setter
	def capital(self, value):
		setattr(self.state.household, "capital", value)

	@property
	def spend_last_year(self):
		sub = getattr(self.state, "household", None)
		if sub is None:
			raise AttributeError("spend_last_year")
		val = getattr(sub, "spend_last_year", None)
		if val is None:
			raise AttributeError("spend_last_year")
		return val

	@spend_last_year.setter
	def spend_last_year(self, value):
		sub = getattr(self.state, "household", None)
		if sub is not None:
			setattr(sub, "spend_last_year", value)

	@property

	@property
	def bounties_paid(self):
		return getattr(self.state.household, "bounties_paid")

	@bounties_paid.setter
	def bounties_paid(self, value):
		setattr(self.state.household, "bounties_paid", value)

	@property

	@property
	def _last_buy_refusal(self):
		return getattr(self.household, "_last_buy_refusal", None)

	@_last_buy_refusal.setter
	def _last_buy_refusal(self, value):
		setattr(self.household, "_last_buy_refusal", value)

	@property
	def _said_stack_caution(self):
		return getattr(self.household, "_said_stack_caution", None)

	@_said_stack_caution.setter
	def _said_stack_caution(self, value):
		setattr(self.household, "_said_stack_caution", value)

	# =========================================================================
	# ProjectsState Compatibility Properties
	# =========================================================================

	@property
	def active(self):
		return getattr(self.state.projects, "active")

	@active.setter
	def active(self, value):
		setattr(self.state.projects, "active", value)

	@property
	def done(self):
		return getattr(self.state.projects, "done")

	@done.setter
	def done(self, value):
		setattr(self.state.projects, "done", value)

	@property
	def done_year(self):
		sub = getattr(self.state, "projects", None)
		if sub is None:
			raise AttributeError("done_year")
		val = getattr(sub, "done_year", None)
		if val is None:
			raise AttributeError("done_year")
		return val

	@done_year.setter
	def done_year(self, value):
		sub = getattr(self.state, "projects", None)
		if sub is not None:
			setattr(sub, "done_year", value)

	@property
	def revealed(self) -> Set[str]:
		return self.state.projects.revealed

	@revealed.setter
	def revealed(self, value: Iterable[str]) -> None:
		cur = self.state.projects.revealed
		self.state.projects.revealed = (set(value) if cur is None else set(cur) | set(value))

	@property
	def operating(self):
		return getattr(self.state.projects, "operating")

	@operating.setter
	def operating(self, value):
		setattr(self.state.projects, "operating", value)

	@property
	def mothballed(self):
		return getattr(self.state.projects, "mothballed")

	@mothballed.setter
	def mothballed(self, value):
		setattr(self.state.projects, "mothballed", value)

	@property
	def shut_for_staff(self):
		# Read-only {work id: year} view of the staffing closures.
		return {node_id: record["year"]
				for node_id, record in self.state.projects.closures.items()
				if record["reason"] == "staff"}

	@property
	def bountied(self):
		return getattr(self.state.projects, "bountied")

	@bountied.setter
	def bountied(self, value):
		setattr(self.state.projects, "bountied", value)

	@property
	def granted(self):
		return getattr(self.state.projects, "granted")

	@granted.setter
	def granted(self, value):
		setattr(self.state.projects, "granted", value)

	@property
	def forgotten(self):
		return self.view("techniques_forgotten")()

	@property
	def failed_attempts(self):
		return getattr(self.state.projects, "failed_attempts")

	@failed_attempts.setter
	def failed_attempts(self, value):
		setattr(self.state.projects, "failed_attempts", value)

	@property
	def paid_towards(self):
		return getattr(self.state.projects, "paid_towards")

	@paid_towards.setter
	def paid_towards(self, value):
		setattr(self.state.projects, "paid_towards", value)

	# =========================================================================
	# EconomyState Compatibility Properties
	# =========================================================================

	@property
	def _dashboard_history(self):
		sub = getattr(self.state, "holdings", None)
		if sub is None:
			raise AttributeError("_dashboard_history")
		val = getattr(sub, "_dashboard_history", None)
		if val is None:
			raise AttributeError("_dashboard_history")
		return val

	@_dashboard_history.setter
	def _dashboard_history(self, value):
		sub = getattr(self.state, "holdings", None)
		if sub is not None:
			setattr(sub, "_dashboard_history", value)

	@property

	# =========================================================================
	# FounderState Compatibility Properties
	# =========================================================================

	@property
	def _founder_death_aged(self):
		sub = getattr(self.state, "founder", None)
		if sub is None:
			raise AttributeError("_founder_death_aged")
		val = getattr(sub, "_founder_death_aged", None)
		if val is None:
			raise AttributeError("_founder_death_aged")
		return val

	@_founder_death_aged.setter
	def _founder_death_aged(self, value):
		sub = getattr(self.state, "founder", None)
		if sub is not None:
			setattr(sub, "_founder_death_aged", value)

	@property
	def _founder_death_year(self):
		sub = getattr(self.state, "founder", None)
		if sub is None:
			raise AttributeError("_founder_death_year")
		val = getattr(sub, "_founder_death_year", None)
		if val is None:
			raise AttributeError("_founder_death_year")
		return val

	@_founder_death_year.setter
	def _founder_death_year(self, value):
		sub = getattr(self.state, "founder", None)
		if sub is not None:
			setattr(sub, "_founder_death_year", value)

	@property
	def dead_reason(self):
		return self.view("founder")()["dead_reason"]

	@dead_reason.setter
	def dead_reason(self, value):
		self.send(EndRun(value, announce=False))

	@property
	def founder_alive(self):
		return self.view("founder")()["alive"]

	@property
	def life_left(self):
		return self.view("founder")()["life_left"]

	@property
	def policy(self):
		return getattr(self.state.founder, "policy")

	@policy.setter
	def policy(self, value):
		setattr(self.state.founder, "policy", value)

	# =========================================================================
	# ScenarioState Compatibility Properties
	# =========================================================================

	@property
	def _said_command_index(self):
		sub = getattr(self.state, "seat_progress", None)
		if sub is None:
			raise AttributeError("_said_command_index")
		val = getattr(sub, "_said_command_index", None)
		if val is None:
			raise AttributeError("_said_command_index")
		return val

	@_said_command_index.setter
	def _said_command_index(self, value):
		sub = getattr(self.state, "seat_progress", None)
		if sub is not None:
			setattr(sub, "_said_command_index", value)

	@property
	def _said_parallelism(self):
		return self.state.seat_progress._said_parallelism

	@_said_parallelism.setter
	def _said_parallelism(self, value):
		self.state.seat_progress._said_parallelism = value

	@property
	def goal_year(self):
		return self.view("goal")()["year"]

	@property
	def year(self):
		return getattr(self.state.scenario, "year")

	@year.setter
	def year(self, value):
		setattr(self.state.scenario, "year", value)

	@property
	def fog(self):
		return self.state._fog

	@fog.setter
	def fog(self, value):
		self.state._fog = bool(value)

	@property
	def fuzzy_estimates(self):
		return self.state._fuzzy_estimates

	@fuzzy_estimates.setter
	def fuzzy_estimates(self, value):
		self.state._fuzzy_estimates = bool(value)
		if value and not self.state._fuzzy_salt:
			self.state._fuzzy_salt = self.rng.getrandbits(30) + 1

	@property
	def goal(self):
		return self.state._goal

	@goal.setter
	def goal(self, value):
		self.state._goal = value
		self.forget_goal_caches()
