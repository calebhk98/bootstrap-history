"""Version counters and invalidating containers on the founder's household, called on a household built here (no game):
mutating the done set, the operating set, the active projects (nested, aliased, `|=`) or the workforce bumps the
version a cache reads, and a pre-wrapped container keeps its identity. The memoisation that reads these counters through
a game is in test_economic_caching."""
QUICK_TOPIC = True

from .harness import check
from sim.agents.household import Household
from sim.engine.forward_production import ForwardProductionMixin
from sim.engine.state import SimulationState, HouseholdState, ProjectsState
from sim.production.api import RefreshDoneCaches, RefreshOperatingCaches
from sim.tests import module_harness
from sim.workforce.api import WatchStaff, WorkforceSeat
from sim.workforce.module import Workforce


class ContainerGame(ForwardProductionMixin):
	"""A household over a fresh state, with the invalidation hooks a Sim wires to it."""

	def __init__(self):
		self.state = SimulationState(household=HouseholdState(capital=1000), projects=ProjectsState())
		self.household = Household(starting_capital=1000.0, operating_changed=self._operating_changed,
								   active_changed=self._active_changed,
								   state=self.state)

	def send(self, command):
		"""The production module's answer to the hooks: count the change on the household."""
		if isinstance(command, RefreshDoneCaches):
			self.household.bump_done_version()
		elif isinstance(command, RefreshOperatingCaches):
			self.household.bump_operating_version()


def _staff_module():
	"""The workforce module over a fresh seat, its payroll watched."""
	module = module_harness.build(Workforce, seat=WorkforceSeat())
	module.seat_slot_of = lambda seat_id: module.seat
	module.clock.act_as("founder")
	module.watch_staff(WatchStaff("founder"))
	return module


WORKFORCE = _staff_module()

# One household for the container and version-counter tests (each only adds and removes its own entries and compares
# versions relative to its own start).
CONTAINERS = ContainerGame()


def _test_done_and_operating_versions():
	"""Verify _done_ver and _operating_ver track respective mutations."""
	sim_inst = CONTAINERS
	initial_done_ver = getattr(sim_inst.household, "_done_ver", 0)
	initial_op_ver = getattr(sim_inst.household, "_operating_ver", 0)

	# Mutate done
	sim_inst.household.done.add("archaeo_survey")
	sim_inst._done_changed()
	new_done_ver = getattr(sim_inst.household, "_done_ver", 0)
	if new_done_ver <= initial_done_ver:
		return False, f"_done_ver did not increment: {initial_done_ver} -> {new_done_ver}"

	# Mutate operating
	sim_inst.household.operating.add("archaeo_survey")
	new_op_ver = getattr(sim_inst.household, "_operating_ver", 0)
	if new_op_ver <= initial_op_ver:
		return False, f"_operating_ver did not increment: {initial_op_ver} -> {new_op_ver}"

	return True, "done and operating versions incremented as expected"


_ok, _detail = _test_done_and_operating_versions()
check("done and operating version counters increment", _ok, _detail)


def _test_active_project_invalidation_version():
	"""Verify mutating household.active bumps _active_ver automatically."""
	sim_inst = CONTAINERS
	initial_active_ver = getattr(sim_inst.household, "_active_ver", 0)

	# Add project
	sim_inst.household.active["test_proj"] = {"ph_left": 10.0, "cost_left": 10.0}
	ver_after_add = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_add <= initial_active_ver:
		return False, f"_active_ver did not increment on add: {initial_active_ver} -> {ver_after_add}"

	# Remove project
	sim_inst.household.active.pop("test_proj", None)
	ver_after_pop = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_pop <= ver_after_add:
		return False, f"_active_ver did not increment on pop: {ver_after_add} -> {ver_after_pop}"

	return True, "active version counter incremented on add and pop"


_ok, _detail = _test_active_project_invalidation_version()
check("active project version increments on mutation", _ok, _detail)


def _test_nested_mutation_invalidation():
	"""Verify nested mutations and alias modifications inside active projects increment _active_ver."""
	sim_inst = CONTAINERS
	sim_inst.household.active["test_node"] = {
		"ph_left": 100.0,
		"spent": 0.0,
		"yrs": 0.0,
		"cost_left": 500.0,
		"lab_left": {"smith": 20.0},
	}
	ver_baseline = getattr(sim_inst.household, "_active_ver", 0)

	# 1. Direct nested field assignment: active[node][field] += x
	sim_inst.household.active["test_node"]["ph_left"] -= 10.0
	ver_after_field = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_field <= ver_baseline:
		return False, f"_active_ver did not increment on direct nested field mutation: {ver_baseline} -> {ver_after_field}"

	# 2. Mutation through project alias: project = active[node]; project[field] = x
	project_alias = sim_inst.household.active["test_node"]
	project_alias["spent"] += 50.0
	ver_after_alias = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_alias <= ver_after_field:
		return False, f"_active_ver did not increment on alias mutation: {ver_after_field} -> {ver_after_alias}"

	# 3. Deeply nested mutation on lab_left dictionary
	labour_alias = project_alias["lab_left"]
	labour_alias["smith"] = 15.0
	ver_after_deep = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_deep <= ver_after_alias:
		return False, f"_active_ver did not increment on deeply nested dict mutation: {ver_after_alias} -> {ver_after_deep}"

	# 4. In-place dictionary update |= on nested project dict
	project_alias |= {"yrs": 1.0}
	ver_after_nested_ior = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_nested_ior <= ver_after_deep:
		return False, f"_active_ver did not increment on nested dict |=: {ver_after_deep} -> {ver_after_nested_ior}"

	# 5. In-place dictionary update |= on outer active dict
	sim_inst.household.active |= {"second_node": {"ph_left": 50.0}}
	ver_after_outer_ior = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_outer_ior <= ver_after_nested_ior:
		return False, f"_active_ver did not increment on outer active |=: {ver_after_nested_ior} -> {ver_after_outer_ior}"

	# 6. In-place dictionary update |= on workforce employees dict
	initial_workforce_ver = WORKFORCE.staff_version()
	WORKFORCE.seat.employees |= {"smith": 5.0}
	ver_after_workforce_ior = WORKFORCE.staff_version()
	if ver_after_workforce_ior <= initial_workforce_ver:
		return False, f"_workforce_ver did not increment on employees |=: {initial_workforce_ver} -> {ver_after_workforce_ior}"

	return True, "nested mutations, aliases, and |= operations properly increment version counters"


_ok, _detail = _test_nested_mutation_invalidation()
check("nested mutation and alias invalidation", _ok, _detail)


def _test_workforce_container_api_completeness():
	"""Edge case: dictionary mutating APIs on household.employees increment _workforce_ver."""
	sim_inst = CONTAINERS
	WORKFORCE.seat.employees["smith"] = 5.0
	ver0 = WORKFORCE.staff_version()

	# setdefault on existing key should not increment version
	existing_val = WORKFORCE.seat.employees.setdefault("smith", 10.0)
	ver_after_existing = WORKFORCE.staff_version()
	if ver_after_existing != ver0 or existing_val != 5.0:
		return False, f"setdefault on existing key fired invalidation: {ver0} != {ver_after_existing}"

	# setdefault on new key should increment version
	new_val = WORKFORCE.seat.employees.setdefault("carpenter", 8.0)
	ver_after_new = WORKFORCE.staff_version()
	if ver_after_new <= ver_after_existing or new_val != 8.0:
		return False, f"setdefault on new key did not increment version: {ver_after_existing} -> {ver_after_new}"

	# update with non-empty dict should increment version
	WORKFORCE.seat.employees.update({"mason": 4.0})
	ver_after_update = WORKFORCE.staff_version()
	if ver_after_update <= ver_after_new:
		return False, f"update did not increment version: {ver_after_new} -> {ver_after_update}"

	# pop should increment version
	popped_val = WORKFORCE.seat.employees.pop("mason")
	ver_after_pop = WORKFORCE.staff_version()
	if ver_after_pop <= ver_after_update or popped_val != 4.0:
		return False, f"pop did not increment version: {ver_after_update} -> {ver_after_pop}"

	# popitem should increment version
	WORKFORCE.seat.employees.popitem()
	ver_after_popitem = WORKFORCE.staff_version()
	if ver_after_popitem <= ver_after_pop:
		return False, f"popitem did not increment version: {ver_after_pop} -> {ver_after_popitem}"

	# clear should increment version
	WORKFORCE.seat.employees.clear()
	ver_after_clear = WORKFORCE.staff_version()
	if ver_after_clear <= ver_after_popitem or len(WORKFORCE.seat.employees) != 0:
		return False, f"clear did not increment version: {ver_after_popitem} -> {ver_after_clear}"

	return True, "workforce container dictionary APIs comprehensively track invalidation"


_ok, _detail = _test_workforce_container_api_completeness()
check("workforce container dictionary APIs completeness", _ok, _detail)


def _test_nested_active_container_api_completeness():
	"""Edge case: dictionary mutating APIs on nested and deep project sub-dicts increment _active_ver."""
	sim_inst = CONTAINERS
	test_node = "test_node_nested_api"
	sim_inst.household.active[test_node] = {
		"ph_left": 100.0,
		"cost_left": 200.0,
		"lab_left": {"smith": 10.0},
	}
	ver0 = getattr(sim_inst.household, "_active_ver", 0)

	project_alias = sim_inst.household.active[test_node]
	lab_alias = project_alias["lab_left"]

	# Deep setdefault on new trade requirement
	lab_alias.setdefault("mason", 5.0)
	ver1 = getattr(sim_inst.household, "_active_ver", 0)
	if ver1 <= ver0:
		return False, f"Deep setdefault did not increment _active_ver: {ver0} -> {ver1}"

	# Deep update
	lab_alias.update({"weaver": 3.0})
	ver2 = getattr(sim_inst.household, "_active_ver", 0)
	if ver2 <= ver1:
		return False, f"Deep update did not increment _active_ver: {ver1} -> {ver2}"

	# Deep pop
	lab_alias.pop("weaver")
	ver3 = getattr(sim_inst.household, "_active_ver", 0)
	if ver3 <= ver2:
		return False, f"Deep pop did not increment _active_ver: {ver2} -> {ver3}"

	# Deep clear
	lab_alias.clear()
	ver4 = getattr(sim_inst.household, "_active_ver", 0)
	if ver4 <= ver3 or len(lab_alias) != 0:
		return False, f"Deep clear did not increment _active_ver: {ver3} -> {ver4}"

	# Project clear
	project_alias.clear()
	ver5 = getattr(sim_inst.household, "_active_ver", 0)
	if ver5 <= ver4 or len(project_alias) != 0:
		return False, f"Project clear did not increment _active_ver: {ver4} -> {ver5}"

	return True, "nested and deep project sub-dictionaries track mutations reliably"


_ok, _detail = _test_nested_active_container_api_completeness()
check("nested and deep project dictionary APIs completeness", _ok, _detail)


def _test_pre_insertion_alias_and_invalidating_dict_identity():
	"""Regression: pre-insertion alias mutation vs already-_InvalidatingDict identity preservation."""
	sim_inst = CONTAINERS
	_InvalidatingDict = sim_inst.household.active.__class__

	# 1. Plain dictionary insertion: wraps in a new _InvalidatingDict, decoupling pre-insertion alias
	plain_project = {
		"ph_left": 100.0,
		"cost_left": 50.0,
		"lab_left": {"smith": 10.0},
	}
	sim_inst.household.active["plain_node"] = plain_project

	if sim_inst.household.active["plain_node"] is plain_project:
		return False, "Plain dict should have been wrapped in a new _InvalidatingDict instance"
	if not isinstance(sim_inst.household.active["plain_node"], _InvalidatingDict):
		return False, "Inserted plain dict was not wrapped in _InvalidatingDict"

	# Mutating plain_project affects only the pre-insertion object, not active
	plain_project["ph_left"] = 999.0
	if sim_inst.household.active["plain_node"]["ph_left"] != 100.0:
		return False, f"Mutating decoupled plain_project affected active: {sim_inst.household.active['plain_node']['ph_left']}"

	# 2. Pre-wrapped _InvalidatingDict insertion: preserves identity (no copy/rewrap)
	pre_wrapped = _InvalidatingDict({
		"ph_left": 200.0,
		"cost_left": 80.0,
		"lab_left": {"mason": 8.0},
	})
	sim_inst.household.active["wrapped_node"] = pre_wrapped

	if sim_inst.household.active["wrapped_node"] is not pre_wrapped:
		return False, "Inserting already _InvalidatingDict created an unnecessary copy"
	if sim_inst.household.active["wrapped_node"]["lab_left"] is not pre_wrapped["lab_left"]:
		return False, "Nested _InvalidatingDict inside pre-wrapped project was unnecessarily copied"

	# Pre-insertion alias mutation on _InvalidatingDict MUST trigger invalidation
	ver_before_alias = getattr(sim_inst.household, "_active_ver", 0)
	pre_wrapped["ph_left"] -= 20.0
	ver_after_alias = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_alias <= ver_before_alias:
		return False, f"Mutating pre-insertion _InvalidatingDict alias did not increment _active_ver: {ver_before_alias} -> {ver_after_alias}"

	# Pre-insertion alias nested mutation MUST trigger invalidation
	pre_wrapped["lab_left"]["mason"] -= 2.0
	ver_after_nested_alias = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_nested_alias <= ver_after_alias:
		return False, f"Mutating pre-insertion nested dict alias did not increment _active_ver: {ver_after_alias} -> {ver_after_nested_alias}"

	# 3. Resetting active container preserves wrapped child identities
	sim_inst._reset_active()
	if sim_inst.household.active["wrapped_node"] is not pre_wrapped:
		return False, "_reset_active() reallocated or copied existing _InvalidatingDict child"

	# Post-reset mutation through pre_wrapped alias still invalidates
	pre_wrapped["cost_left"] += 10.0
	ver_after_reset_mut = getattr(sim_inst.household, "_active_ver", 0)
	if ver_after_reset_mut <= ver_after_nested_alias:
		return False, f"Mutation through pre_wrapped alias after _reset_active did not increment _active_ver: {ver_after_nested_alias} -> {ver_after_reset_mut}"

	# 4. Identity preservation on update() and setdefault()
	update_wrapped = _InvalidatingDict({"ph_left": 30.0})
	sim_inst.household.active.update({"update_node": update_wrapped})
	if sim_inst.household.active["update_node"] is not update_wrapped:
		return False, "update() with _InvalidatingDict created unnecessary copy"

	setdefault_wrapped = _InvalidatingDict({"ph_left": 40.0})
	returned_val = sim_inst.household.active.setdefault("setdefault_node", setdefault_wrapped)
	if returned_val is not setdefault_wrapped or sim_inst.household.active["setdefault_node"] is not setdefault_wrapped:
		return False, "setdefault() with _InvalidatingDict created unnecessary copy"

	return True, "pre-insertion alias identity and _InvalidatingDict no-copy semantics verified"


_ok, _detail = _test_pre_insertion_alias_and_invalidating_dict_identity()
check("pre-insertion alias identity and no-copy semantics", _ok, _detail)
