"""Test state definitions, ActiveProjectState schema, and explicit state ownership."""
import unittest
from sim.tests.harness import check


def _test_active_project_state_schema():
	"""Verify ActiveProjectState dataclass exists and supports typed attribute mutation."""
	from sim.engine.state import ActiveProjectState

	proj = ActiveProjectState(ph_left=100.0, cost_left=500.0, yrs=0.0, spent=0.0)
	proj.ph_left -= 25.0
	proj.spent += 100.0
	proj.cost_left -= 100.0
	proj.yrs += 1.0

	if proj.ph_left != 75.0 or proj.spent != 100.0 or proj.cost_left != 400.0 or proj.yrs != 1.0:
		return False, f"Typed attributes not updated correctly: ph_left={proj.ph_left}, spent={proj.spent}"

	return True, "ActiveProjectState supports typed attribute mutation"


_ok, _detail = _test_active_project_state_schema()
check("ActiveProjectState typed attributes", _ok, _detail)


def _test_active_project_mapping_and_invalidation():
	"""Verify ActiveProjectState supports dict-like access and notifies on_change callback."""
	from sim.engine.state import ActiveProjectState

	events = []
	proj = ActiveProjectState(
		ph_left=100.0,
		cost_left=500.0,
		lab_left={"smith": 20.0},
		_on_change=lambda: events.append(1)
	)

	# 1. Typed mutation triggers invalidation
	proj.ph_left -= 10.0
	if len(events) != 1:
		return False, f"Typed mutation did not trigger on_change: {events}"

	# 2. Dict item mutation triggers invalidation
	proj["spent"] = 50.0
	if len(events) != 2:
		return False, f"Dict item assignment did not trigger on_change: {events}"
	if proj.spent != 50.0 or proj["spent"] != 50.0:
		return False, "Dict item assignment and attribute access out of sync"

	# 3. Deep lab_left mutation triggers invalidation
	proj.lab_left["smith"] -= 5.0
	if len(events) != 3:
		return False, f"Nested lab_left mutation did not trigger on_change: {events}"

	# 4. Canonical dict conversion only outputs non-None set fields
	canon = proj.to_canon_dict()
	if "hours_offered_this_year" in canon:
		return False, f"Unset field hours_offered_this_year found in canon dict: {canon}"
	if canon.get("ph_left") != 90.0 or canon.get("spent") != 50.0:
		return False, f"Canonical dict missing expected values: {canon}"

	return True, "ActiveProjectState mapping and invalidation verified"


_ok, _detail = _test_active_project_mapping_and_invalidation()
check("ActiveProjectState mapping and invalidation", _ok, _detail)


def _test_subsystem_state_owners():
	"""Verify authoritative subsystem state classes exist and have documented ownership."""
	from sim.engine.state import (
		HouseholdState,
		ProjectsState,
		EconomyState,
		GovernanceState,
		FounderState,
		ScenarioState,
		SimulationState,
	)

	h = HouseholdState(capital=1000.0)
	p = ProjectsState()
	e = EconomyState()
	g = GovernanceState()
	f = FounderState(founder_alive=True, life_left=40.0)
	s = ScenarioState(year=100)

	sim_state = SimulationState(
		household=h,
		projects=p,
		economy=e,
		governance=g,
		founder=f,
		scenario=s,
		_civ="rome_100ad",
	)

	if sim_state.household.capital != 1000.0:
		return False, "SimulationState failed to coordinate HouseholdState"
	if sim_state.scenario.year != 100:
		return False, "SimulationState failed to coordinate ScenarioState"
	if sim_state._civ != "rome_100ad":
		return False, "SimulationState failed to coordinate _civ"

	return True, "Subsystem state owners instantiated and coordinated"


_ok, _detail = _test_subsystem_state_owners()
check("Subsystem state owners", _ok, _detail)


def _test_transient_cache_exclusion():
	"""Verify transient caches and counters are not part of persistent state schema."""
	from sim.engine.state import HouseholdState, ProjectsState
	import dataclasses

	h_fields = {f.name for f in dataclasses.fields(HouseholdState)}
	p_fields = {f.name for f in dataclasses.fields(ProjectsState)}

	for transient_name in ("_revenue_cache_key", "_operating_ver", "_done_ver", "_annual_mat_demand_cache"):
		if transient_name in h_fields or transient_name in p_fields:
			return False, f"Transient cache {transient_name} found in state dataclass fields"

	return True, "Transient caches excluded from state dataclass fields"


_ok, _detail = _test_transient_cache_exclusion()
check("Transient cache exclusion", _ok, _detail)


def _test_edge_cases():
	"""Verify edge cases: |=, pop, clear, and missing key handling."""
	from sim.engine.state import ActiveProjectState

	proj = ActiveProjectState(ph_left=50.0, cost_left=100.0)
	proj |= {"yrs": 2.0}
	if proj.yrs != 2.0:
		return False, f"|= failed: {proj.yrs}"

	proj.pop("yrs", None)
	if proj.yrs is not None:
		return False, f"pop failed to clear field: {proj.yrs}"

	proj.clear()
	if proj.ph_left is not None or proj.cost_left is not None:
		return False, f"clear failed to reset fields: {proj}"

	return True, "Edge cases verified"


_ok, _detail = _test_edge_cases()
check("ActiveProjectState edge cases", _ok, _detail)
