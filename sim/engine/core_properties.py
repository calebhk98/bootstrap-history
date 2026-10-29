"""The outside-facing compatibility property surface for the authoritative SimulationState.

These properties provide backward-compatibility for external consumers and
integration test assertions. Internal simulation code accesses live state
directly through authoritative subsystem owners:
  - self.state.household
  - self.state.economy
  - self.state.founder

Properties are categorized strictly by owning subsystem.
"""
from typing import Any, Iterable, Set

from sim.knowledge.api import ReplaceTree
from sim.scenario.api import SetEndYear, SetFog, SetYear
from sim.seats.api import EndRun


class ForwardingPropertiesMixin:
	"""Composition point: backward-compatibility property facade delegating to
	authoritative subsystem live state.
	"""

	@property
	def nodes(self):
		"""The tech tree, node data by id: the knowledge module's, replaced as a whole when the nodes' money is re-derived."""
		return self.assembly.views["tree_nodes"]()

	@nodes.setter
	def nodes(self, tree):
		self.send(ReplaceTree(tree))

	@property
	def stores(self):
		"""Every declared store of the game (the stores module's book): `sim.stores.<name>.<key>`, `.view(name)`, `.write(...)`."""
		return self.assembly.views["store_book"]()

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
		return self.view("spend_last_year")()

	@property
	def bounties_paid(self):
		return self.view("bounties_paid")()

	@property
	def _said_stack_caution(self):
		return getattr(self.household, "_said_stack_caution", None)

	@_said_stack_caution.setter
	def _said_stack_caution(self, value):
		setattr(self.household, "_said_stack_caution", value)

	# =========================================================================
	# Projects Compatibility Properties (each answers from the view of the module that owns it)
	# =========================================================================

	@property
	def active(self):
		return self.view("active_projects")()

	@property
	def done(self):
		return self.view("techniques_held")()

	@property
	def done_year(self):
		return self.view("done_year")()

	@property
	def revealed(self):
		return self.view("techniques_revealed")()

	@property
	def operating(self):
		return self.view("operating")()

	@property
	def mothballed(self):
		return self.view("mothballed")()

	@property
	def shut_for_staff(self):
		return self.view("shut_for_staff")()

	@property
	def bountied(self):
		return self.view("bountied")()

	@property
	def granted(self):
		return self.view("techniques_granted")()

	@property
	def forgotten(self):
		return self.view("techniques_forgotten")()

	@property
	def failed_attempts(self):
		return self.view("failed_attempts")()

	@property
	def paid_towards(self):
		return self.view("paid_towards")()

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

	# ---- the scenario module's: the clock, the modes and the setup the game was built from ----

	@property
	def year(self):
		return self._scenario.world.year

	@year.setter
	def year(self, value):
		self.send(SetYear(value))

	@property
	def fog(self):
		return self._scenario.world.fog

	@fog.setter
	def fog(self, value):
		self.send(SetFog(bool(value)))

	@property
	def fuzzy_estimates(self):
		return self._scenario.world.fuzzy_estimates

	@fuzzy_estimates.setter
	def fuzzy_estimates(self, value):
		from . import ui_port
		ui_port.set_fuzzy_estimates(self, value)

	@property
	def cfg(self):
		return self._scenario.configuration

	@property
	def civ(self):
		return self._scenario.civilisation

	@property
	def start_civ(self):
		return self._scenario.start_civilisation

	@property
	def manual(self):
		return self._scenario.manual

	@property
	def events(self):
		return self._scenario.events

	@property
	def bounty_set(self):
		return self._scenario.bounty_set

	@property
	def end_year(self):
		"""The year the horizon ends, once a front end has set it (no attribute before)."""
		if self._scenario.end_year is None:
			raise AttributeError("end_year")
		return self._scenario.end_year

	@end_year.setter
	def end_year(self, value):
		self.send(SetEndYear(value))

	@property
	def goal(self):
		return self.state._goal

	@goal.setter
	def goal(self, value):
		self.state._goal = value
		self.forget_goal_caches()
