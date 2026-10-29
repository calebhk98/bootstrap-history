"""The outside-facing compatibility property surface for the authoritative SimulationState.

These properties provide backward-compatibility for external consumers and
integration test assertions. Internal simulation code accesses live state
directly through authoritative subsystem owners:
  - self.state.acting_record (the acting seat's household, founder, holdings and progress)
  - self.state.economy

Properties are categorized strictly by owning subsystem.
"""
from typing import Any, Iterable, Set

from sim.knowledge.api import ReplaceTree
from sim.ledger.api import RestorePurse
from sim.scenario.api import SetEndYear, SetFog, SetYear
from sim.seats.api import EndRun, SetGoal


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
		return self.view("acting_balance")()

	@capital.setter
	def capital(self, value):
		self.send(RestorePurse(value))

	@property
	def spend_last_year(self):
		return self.view("spend_last_year")()

	@property
	def bounties_paid(self):
		return self.view("bounties_paid")()

	@property
	def _said_stack_caution(self):
		return self.__dict__.get("_stack_cautions", {}).get(self.state.acting_seat)

	@_said_stack_caution.setter
	def _said_stack_caution(self, value):
		self.__dict__.setdefault("_stack_cautions", {})[self.state.acting_seat] = value

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
		sub = self.state.acting_record.holdings
		return None if sub is None else sub._dashboard_history   # None until recorded

	@_dashboard_history.setter
	def _dashboard_history(self, value):
		sub = self.state.acting_record.holdings
		if sub is not None:
			setattr(sub, "_dashboard_history", value)

	# =========================================================================
	# FounderState Compatibility Properties
	# =========================================================================

	@property
	def _founder_death_aged(self):
		sub = self.state.acting_record.founder
		return None if sub is None else sub._founder_death_aged   # None until recorded

	@_founder_death_aged.setter
	def _founder_death_aged(self, value):
		sub = self.state.acting_record.founder
		if sub is not None:
			setattr(sub, "_founder_death_aged", value)

	@property
	def _founder_death_year(self):
		sub = self.state.acting_record.founder
		return None if sub is None else sub._founder_death_year   # None until recorded

	@_founder_death_year.setter
	def _founder_death_year(self, value):
		sub = self.state.acting_record.founder
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
		return self.view("founder")()["policy"]

	# =========================================================================
	# ScenarioState Compatibility Properties
	# =========================================================================

	@property
	def _said_command_index(self):
		sub = self.state.acting_record.seat_progress
		return None if sub is None else sub._said_command_index   # None until recorded

	@_said_command_index.setter
	def _said_command_index(self, value):
		sub = self.state.acting_record.seat_progress
		if sub is not None:
			setattr(sub, "_said_command_index", value)

	@property
	def _said_parallelism(self):
		return self.state.acting_record.seat_progress._said_parallelism

	@_said_parallelism.setter
	def _said_parallelism(self, value):
		self.state.acting_record.seat_progress._said_parallelism = value

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
		return self.view("goal")()["node"]

	@goal.setter
	def goal(self, value):
		self.send(SetGoal(value))
