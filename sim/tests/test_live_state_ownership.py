"""Regression and unit tests for live authoritative SimulationState ownership.

Verifies:
1. sim.state is an authoritative SimulationState containing typed subsystem dataclasses.
2. Subsystems (household, projects, economy, governance, founder, scenario, population)
   are the actual runtime state owners, not save-time snapshots.
3. Compatibility façade (ForwardingPropertiesMixin and Household façade) delegates directly
   to sim.state without duplicate storage.
4. Invalidation version counters (_operating_ver, _done_ver, _active_ver, _workforce_ver)
   are attached to the state subsystems that own the mutated state.
5. Mutations through any path (sim.x, sim.household.x, sim.state.subsystem.x) mutate the
   exact same underlying authoritative state synchronously.
"""
from .harness import *  # noqa: F401,F403
from sim.engine.state import (
	SimulationState,
	HouseholdState,
	ProjectsState,
	EconomyState,
	GovernanceState,
	FounderState,
	ScenarioState,
	PopulationState,
)


def _test_live_simulation_state_structure():
	"""Verify Sim owns a live authoritative SimulationState with typed child objects."""
	s = sim(civ="rome_100ad", capital=1000.0)
	if not hasattr(s, "state") or not isinstance(s.state, SimulationState):
		return False, f"s.state is not SimulationState: {type(getattr(s, 'state', None))}"

	if not isinstance(s.state.household, HouseholdState):
		return False, f"s.state.household is not HouseholdState: {type(s.state.household)}"
	if not isinstance(s.state.projects, ProjectsState):
		return False, f"s.state.projects is not ProjectsState: {type(s.state.projects)}"
	if not isinstance(s.state.economy, EconomyState):
		return False, f"s.state.economy is not EconomyState: {type(s.state.economy)}"
	if not isinstance(s.state.governance, GovernanceState):
		return False, f"s.state.governance is not GovernanceState: {type(s.state.governance)}"
	if not isinstance(s.state.founder, FounderState):
		return False, f"s.state.founder is not FounderState: {type(s.state.founder)}"
	if not isinstance(s.state.scenario, ScenarioState):
		return False, f"s.state.scenario is not ScenarioState: {type(s.state.scenario)}"
	if not isinstance(s.state.population, PopulationState):
		return False, f"s.state.population is not PopulationState: {type(s.state.population)}"

	return True, "sim.state and child subsystem states are typed dataclass instances"


_ok, _detail = _test_live_simulation_state_structure()
check("sim.state live structure", _ok, _detail)


def _test_household_finances_single_storage():
	"""Verify capital and financial fields share single storage across sim, household, and state."""
	s = sim(civ="rome_100ad", capital=1000.0)
	if s.capital != s.state.household.capital or s.household.capital != s.state.household.capital:
		return False, f"Capital mismatch initially: sim={s.capital}, hh={s.household.capital}, state={s.state.household.capital}"

	# Mutate via sim.capital
	s.capital = 1250.0
	if s.state.household.capital != 1250.0 or s.household.capital != 1250.0:
		return False, f"Mutation via sim.capital did not propagate: state={s.state.household.capital}, hh={s.household.capital}"

	# Mutate via s.state.household.capital
	s.state.household.capital = 1500.0
	if s.capital != 1500.0 or s.household.capital != 1500.0:
		return False, f"Mutation via state.household.capital did not propagate: sim={s.capital}, hh={s.household.capital}"

	# Mutate via s.household.capital
	s.household.capital = 1750.0
	if s.capital != 1750.0 or s.state.household.capital != 1750.0:
		return False, f"Mutation via household.capital did not propagate: sim={s.capital}, state={s.state.household.capital}"

	return True, "capital is backed by single authoritative storage on state.household"


_ok, _detail = _test_household_finances_single_storage()
check("household finances single storage", _ok, _detail)


def _test_projects_state_synchronization():
	"""Verify active, done, and operating projects are backed by ProjectsState."""
	s = sim(civ="rome_100ad", capital=10000.0)

	# Mutate active through sim.state.projects
	s.state.projects.active["test_proj"] = {"ph_left": 42.0, "cost_left": 10.0}
	if "test_proj" not in s.active or "test_proj" not in s.household.active:
		return False, "test_proj not found in s.active or s.household.active"
	if s.active["test_proj"].ph_left != 42.0:
		return False, f"ph_left mismatch: {s.active['test_proj'].ph_left}"

	# Mutate active through s.household.active
	s.household.active["test_proj"]["ph_left"] = 30.0
	if s.state.projects.active["test_proj"].ph_left != 30.0 or s.active["test_proj"].ph_left != 30.0:
		return False, f"Nested mutation failed: state={s.state.projects.active['test_proj'].ph_left}"

	# Mutate done through s.state.projects
	s.state.projects.done.add("archaeo_survey")
	if "archaeo_survey" not in s.done or "archaeo_survey" not in s.household.done:
		return False, "archaeo_survey not found in s.done or s.household.done"

	# Mutate operating through s.household.operating
	s.household.operating.add("archaeo_survey")
	if "archaeo_survey" not in s.operating or "archaeo_survey" not in s.state.projects.operating:
		return False, "archaeo_survey not found in s.operating or s.state.projects.operating"

	return True, "projects collections share single authoritative storage on state.projects"


_ok, _detail = _test_projects_state_synchronization()
check("projects state single storage", _ok, _detail)


def _test_cache_invalidation_attached_to_owners():
	"""Verify invalidation version counters live on the owning state objects."""
	s = sim(civ="rome_100ad", capital=10000.0)

	# ProjectsState owns _active_ver, _done_ver, _operating_ver
	init_active_ver = getattr(s.state.projects, "_active_ver", 0)
	s.active["p1"] = {"ph_left": 10.0}
	new_active_ver = getattr(s.state.projects, "_active_ver", 0)
	if new_active_ver <= init_active_ver:
		return False, f"state.projects._active_ver did not increment: {init_active_ver} -> {new_active_ver}"

	init_done_ver = getattr(s.state.projects, "_done_ver", 0)
	s.done.add("new_done_tech")
	s._done_changed()
	new_done_ver = getattr(s.state.projects, "_done_ver", 0)
	if new_done_ver <= init_done_ver:
		return False, f"state.projects._done_ver did not increment: {init_done_ver} -> {new_done_ver}"

	init_op_ver = getattr(s.state.projects, "_operating_ver", 0)
	s.operating.add("new_done_tech")
	new_op_ver = getattr(s.state.projects, "_operating_ver", 0)
	if new_op_ver <= init_op_ver:
		return False, f"state.projects._operating_ver did not increment: {init_op_ver} -> {new_op_ver}"

	# HouseholdState owns _workforce_ver
	init_wf_ver = getattr(s.state.household, "_workforce_ver", 0)
	s.employees["smith"] = 5.0
	new_wf_ver = getattr(s.state.household, "_workforce_ver", 0)
	if new_wf_ver <= init_wf_ver:
		return False, f"state.household._workforce_ver did not increment: {init_wf_ver} -> {new_wf_ver}"

	return True, "invalidation version counters attached to respective state owners"


_ok, _detail = _test_cache_invalidation_attached_to_owners()
check("cache invalidation version owners", _ok, _detail)


def _test_economy_and_founder_and_scenario_state():
	"""Verify economy, founder, scenario, and population state live on state subsystems."""
	s = sim(civ="rome_100ad", capital=1000.0)

	# ScenarioState
	if s.year != s.state.scenario.year:
		return False, f"year mismatch: sim={s.year}, state={s.state.scenario.year}"
	s.year = 150
	if s.state.scenario.year != 150:
		return False, f"year mutation via sim did not update state.scenario.year: {s.state.scenario.year}"

	# FounderState
	if s.founder_alive != s.state.founder.founder_alive:
		return False, f"founder_alive mismatch: sim={s.founder_alive}, state={s.state.founder.founder_alive}"
	s.founder_alive = False
	if s.state.founder.founder_alive is not False:
		return False, "founder_alive mutation via sim did not update state.founder.founder_alive"

	# EconomyState
	if s.mines != s.state.economy.mines:
		return False, "mines mismatch"
	s.mines.append({"material": "iron", "capacity": 1.0, "opened_year": 100, "capex_paid": 50.0, "intensity_yrs": 0.0})
	if len(s.state.economy.mines) != 1:
		return False, f"mines mutation did not update state.economy.mines: {s.state.economy.mines}"

	return True, "economy, founder, and scenario live on respective typed state objects"


_ok, _detail = _test_economy_and_founder_and_scenario_state()
check("subsystem state synchronization", _ok, _detail)
