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


def _test_household_mutation_methods():
	"""Verify HouseholdState provides encapsulated getter/setter and mutation methods.
	
	Ensures cost_capital, costCapital, add_capital, add_reputation,
	deduct_reputation, and add_scandal safely update state.
	"""
	s = sim(civ="rome_100ad", capital=1000.0)
	household = s.state.household

	# 1. cost_capital decreases capital and increments total_spend
	household.cost_capital(250.0)
	if household.capital != 750.0:
		return False, f"cost_capital failed: expected 750.0, got {household.capital}"
	if household.total_spend != 250.0:
		return False, f"cost_capital did not update total_spend: {household.total_spend}"

	# 2. costCapital alias
	household.costCapital(150.0)
	if household.capital != 600.0:
		return False, f"costCapital alias failed: expected 600.0, got {household.capital}"
	if household.total_spend != 400.0:
		return False, f"costCapital did not update total_spend: {household.total_spend}"

	# 3. add_capital increases capital
	household.add_capital(500.0)
	if household.capital != 1100.0:
		return False, f"add_capital failed: expected 1100.0, got {household.capital}"

	# 4. Reputation methods
	init_rep = household.reputation
	household.add_reputation(2.5)
	if household.reputation != init_rep + 2.5:
		return False, f"add_reputation failed: expected {init_rep + 2.5}, got {household.reputation}"
	household.deduct_reputation(1.0)
	if household.reputation != init_rep + 1.5:
		return False, f"deduct_reputation failed: expected {init_rep + 1.5}, got {household.reputation}"

	# 5. Scandal methods
	init_scandal = household.scandal
	household.add_scandal(3.0)
	if household.scandal != init_scandal + 3.0:
		return False, f"add_scandal failed: expected {init_scandal + 3.0}, got {household.scandal}"

	# Edge cases (~5 tests):
	# Edge case 1: zero cost
	household.cost_capital(0.0)
	if household.capital != 1100.0 or household.total_spend != 400.0:
		return False, "cost_capital(0.0) modified capital or total_spend"

	# Edge case 2: zero add
	household.add_capital(0.0)
	if household.capital != 1100.0:
		return False, "add_capital(0.0) modified capital"

	# Edge case 3: negative capital cost (e.g. refund/reversal)
	household.cost_capital(-50.0)
	if household.capital != 1150.0 or household.total_spend != 350.0:
		return False, "negative cost_capital refund failed"

	# Edge case 4: reputation flooring / negative delta handling
	household.deduct_reputation(-2.0)
	if household.reputation != init_rep + 3.5:
		return False, f"deduct_reputation with negative delta failed: got {household.reputation}"

	# Edge case 5: synchronisation via compatibility property
	if s.capital != 1150.0:
		return False, f"s.capital compatibility property failed to reflect method mutation: {s.capital}"

	return True, "household mutation methods and edge cases operate correctly"


_ok, _detail = _test_household_mutation_methods()
check("household mutation methods encapsulation", _ok, _detail)


def _test_governance_and_population_bidirectional_sync():
	"""Verify governance and population subsystems sync bidirectionally."""
	s = sim(civ="rome_100ad", capital=1000.0)

	# 1. Governance inst_units synchronization
	s.inst_units = {"senate": 3.0}
	if s.state.governance.inst_units.get("senate") != 3.0:
		return False, f"inst_units via sim failed to sync to state: {s.state.governance.inst_units}"
	if s.household.inst_units.get("senate") != 3.0:
		return False, f"inst_units via sim failed to sync to household proxy: {s.household.inst_units}"

	s.state.governance.inst_units["guild"] = 5.0
	if s.inst_units.get("guild") != 5.0:
		return False, f"inst_units via state failed to sync to sim: {s.inst_units}"

	# 2. Population synchronization across Sim, Population proxy, and PopulationState
	s.pop_children = 12000.0
	if s.population.children != 12000.0 or s.state.population.pop_children != 12000.0:
		return False, f"pop_children failed to sync: sim.pop={s.population.children}, state={s.state.population.pop_children}"

	s.pop_working_age = 25000.0
	if s.population.working_age != 25000.0 or s.state.population.pop_working_age != 25000.0:
		return False, f"pop_working_age failed to sync: sim.pop={s.population.working_age}, state={s.state.population.pop_working_age}"

	s.pop_elderly = 4000.0
	if s.population.elderly != 4000.0 or s.state.population.pop_elderly != 4000.0:
		return False, f"pop_elderly failed to sync: sim.pop={s.population.elderly}, state={s.state.population.pop_elderly}"

	# 3. _food_pop_bonus_applied flag
	s._food_pop_bonus_applied = True
	if s.state.population._food_pop_bonus_applied is not True:
		return False, "s._food_pop_bonus_applied failed to sync to state.population"

	return True, "governance and population subsystems synchronize bidirectionally"


_ok, _detail = _test_governance_and_population_bidirectional_sync()
check("governance and population bidirectional sync", _ok, _detail)


def _test_all_subsystems_full_coverage_sync():
	"""Verify deep bidirectional sync across projects, economy, founder, and scenario."""
	s = sim(civ="rome_100ad", capital=1000.0)

	# 1. ProjectsState additional collections
	s.revealed.add("concrete_vaulting")
	if "concrete_vaulting" not in s.state.projects.revealed:
		return False, "revealed project failed to sync to state.projects"

	s.state.projects.mothballed.add("watermill")
	if "watermill" not in s.mothballed:
		return False, "mothballed project failed to sync from state.projects to sim"

	s.state.projects.paid_towards["aqueduct"] = 150.0
	if s.paid_towards.get("aqueduct") != 150.0:
		return False, "paid_towards failed to sync from state.projects to sim"

	# 2. EconomyState land and resources
	s.farm_hectares = 45.0
	if s.state.economy.farm_hectares != 45.0:
		return False, "farm_hectares failed to sync to state.economy"

	s.forest_ha = 12.5
	if s.state.economy.forest_ha != 12.5:
		return False, "forest_ha failed to sync to state.economy"

	s.money_real = 0.85
	if s.state.economy.money_real != 0.85:
		return False, "money_real failed to sync to state.economy"

	s.output_factor = 1.15
	if s.state.economy.output_factor != 1.15:
		return False, "output_factor failed to sync to state.economy"

	# 3. FounderState policy and lifespan
	s.policy["test_option"] = True
	if s.state.founder.policy.get("test_option") is not True:
		return False, "policy mutation failed to sync to state.founder.policy"

	s.life_left = 22.5
	if s.state.founder.life_left != 22.5:
		return False, "life_left failed to sync to state.founder.life_left"

	# 4. ScenarioState and state root
	s.goal_year = 300
	if s.state.scenario.goal_year != 300:
		return False, "goal_year failed to sync to state.scenario"

	s.fog = False
	if s.state._fog is not False:
		return False, "fog failed to sync to state._fog"

	s.goal = "test_goal"
	if s.state._goal != "test_goal":
		return False, "goal failed to sync to state._goal"

	return True, "deep bidirectional sync verified across all remaining subsystem fields"


_ok, _detail = _test_all_subsystems_full_coverage_sync()
check("all subsystems full coverage sync", _ok, _detail)


