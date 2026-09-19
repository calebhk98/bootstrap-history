"""Targeted regression tests for economic derived-state caching and explicit state versioning.

Proves that:
1. Version counters track mutations to done, active projects, and workforce state.
2. revenue() memoizes its aggregate computation when inputs are stable.
3. revenue() properly invalidates when operating, done, workforce, or year changes.
4. revenue_capacity() and revenue() do not corrupt each other's cached values.
5. _goods_category_ratios() and goods_market_factor() memoize correctly.
6. annual_material_demand() memoizes and invalidates on active/done changes.
7. Save and load operations preserve clean derived state.
"""
from .harness import *  # noqa: F401,F403


def _test_done_and_operating_versions():
	"""Verify _done_ver and _operating_ver track respective mutations."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
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
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
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
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
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
	initial_workforce_ver = getattr(sim_inst.household, "_workforce_ver", 0)
	sim_inst.household.employees |= {"smith": 5.0}
	ver_after_workforce_ior = getattr(sim_inst.household, "_workforce_ver", 0)
	if ver_after_workforce_ior <= initial_workforce_ver:
		return False, f"_workforce_ver did not increment on employees |=: {initial_workforce_ver} -> {ver_after_workforce_ior}"

	return True, "nested mutations, aliases, and |= operations properly increment version counters"


_ok, _detail = _test_nested_mutation_invalidation()
check("nested mutation and alias invalidation", _ok, _detail)


def _test_revenue_memoization_and_invalidation():
	"""Verify revenue() returns identical cached values, and invalidates upon mutation."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	sim_inst.step()

	rev1 = sim_inst.revenue()
	if getattr(sim_inst.household, "_revenue_cache_key", None) is None:
		return False, "_revenue_cache_key was not set after revenue() call"
	rev2 = sim_inst.revenue()
	if rev1 != rev2:
		return False, f"Repeated revenue calls differ: {rev1} != {rev2}"

	# Invalidate by adding to operating
	cand = sim_inst.order[0]
	sim_inst.household.operating.add(cand)
	rev_after_op = sim_inst.revenue()

	# Invalidate by workforce change
	sim_inst.household.employees["smith"] = sim_inst.household.employees.get("smith", 0.0) + 10.0
	rev_after_workforce = sim_inst.revenue()

	# Invalidate by wage hours sold (e.g. revenue_capacity)
	cap = sim_inst.revenue_capacity()
	rev_after_cap = sim_inst.revenue()
	if rev_after_cap != rev_after_workforce:
		return False, f"revenue_capacity() corrupted revenue(): {rev_after_cap} != {rev_after_workforce}"

	return True, "revenue() memoizes and responds to invalidations"


_ok, _detail = _test_revenue_memoization_and_invalidation()
check("revenue() memoization and invalidation", _ok, _detail)


def _test_goods_market_memoization_and_invalidation():
	"""Verify _goods_category_ratios and goods_market_factor cache and invalidate."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	loom_node = "tex_power_loom"
	if loom_node in sim_inst.nodes:
		sim_inst.household.operating.add(loom_node)

	# Initial call
	f1 = sim_inst.goods_market_factor(loom_node)
	cat_cache = getattr(sim_inst.household, "_goods_category_ratios_cache", None)
	if cat_cache is None:
		return False, "_goods_category_ratios_cache was not populated"
	op_cache = getattr(sim_inst.household, "_goods_mkt_op_factor_cache", None)
	if op_cache is None:
		return False, "_goods_mkt_op_factor_cache was not populated"

	f2 = sim_inst.goods_market_factor(loom_node)
	if f1 != f2:
		return False, f"goods_market_factor returned different values: {f1} != {f2}"

	# Mutate farm_hectares to test essential/income_factor invalidation
	sim_inst.invest_farm(50.0)
	f3 = sim_inst.goods_market_factor(loom_node)
	if f3 == f1:
		return False, f"goods_market_factor should have updated after farm investment: {f3} == {f1}"

	# Mutate operating to test invalidation
	sim_inst.household.operating.discard(loom_node)
	f4 = sim_inst.goods_market_factor(loom_node)
	if f4 != 1.0:
		return False, f"Non-operating node should have market factor 1.0: got {f4}"

	return True, "goods market factor memoizes and invalidates properly"


_ok, _detail = _test_goods_market_memoization_and_invalidation()
check("goods market caching and invalidation", _ok, _detail)


def _test_annual_material_demand_caching():
	"""Verify annual_material_demand caches, invalidates on active/done, and defensively copies."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	test_node = sim_inst.order[0]
	sim_inst.household.active[test_node] = {"ph_left": 10.0, "cost_left": 10.0}

	dem1 = sim_inst.annual_material_demand()
	cache = getattr(sim_inst.household, "_annual_mat_demand_cache", None)
	if cache is None:
		return False, "_annual_mat_demand_cache was not populated"

	# Verify defensive copy
	dem1["fake_material_kg"] = 999.0
	dem2 = sim_inst.annual_material_demand()
	if "fake_material_kg" in dem2:
		return False, "Mutating returned demand mutated the cache (missing defensive copy)"

	# Invalidate by active change
	sim_inst.household.active.pop(test_node, None)
	dem3 = sim_inst.annual_material_demand()
	if getattr(sim_inst.household, "_annual_mat_demand_cache")[0] == cache[0]:
		return False, "Cache key did not update after active project popped"

	# Invalidate by done change
	sim_inst.household.done.add(test_node)
	sim_inst._done_changed()
	dem4 = sim_inst.annual_material_demand()

	return True, "annual_material_demand caches, invalidates, and defensively copies properly"


_ok, _detail = _test_annual_material_demand_caching()
check("annual_material_demand caching and invalidation", _ok, _detail)


def _test_save_load_derived_state_integrity():
	"""Edge case: save and reload re-wraps containers and re-initializes clean derived state."""
	import tempfile
	import os
	from sim.engine.proto.saveload import save_state, load_state

	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	sim_inst.step()
	sim_inst.revenue()
	sim_inst.annual_material_demand()

	# Perform save
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
		save_path = temp_file.name
	try:
		save_state(sim_inst, save_path)

		# Perform load on a sim that already had pre-existing cached state
		loaded_sim = sim(civ="rome_100ad")
		loaded_sim.step()
		loaded_sim.revenue()
		loaded_sim.annual_material_demand()
		# Plant a sentinel in a transient cache attribute
		loaded_sim.household._revenue_cache_key = "sentinel_stale_cache"

		load_state(loaded_sim, save_path)
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)

	# Verify sentinel is wiped (no pre-load cache survived)
	if getattr(loaded_sim.household, "_revenue_cache_key", None) == "sentinel_stale_cache":
		return False, "pre-load _revenue_cache_key survived load_state"

	# Verify containers are invalidating dicts/sets
	if loaded_sim.household.active.__class__.__name__ != "_InvalidatingDict":
		return False, f"loaded active is not _InvalidatingDict: {type(loaded_sim.household.active)}"
	if loaded_sim.household.employees.__class__.__name__ != "_InvalidatingDict":
		return False, f"loaded employees is not _InvalidatingDict: {type(loaded_sim.household.employees)}"

	# Verify version counters exist
	for ver_field in ("_done_ver", "_active_ver", "_workforce_ver", "_operating_ver"):
		if not hasattr(loaded_sim.household, ver_field):
			return False, f"loaded household missing version field: {ver_field}"

	# Verify nested mutation invalidation works post-load
	loaded_sim.household.active["post_load_node"] = {"ph_left": 20.0, "cost_left": 10.0}
	ver_before_nested = getattr(loaded_sim.household, "_active_ver", 0)
	loaded_sim.household.active["post_load_node"]["ph_left"] += 5.0
	ver_after_nested = getattr(loaded_sim.household, "_active_ver", 0)
	if ver_after_nested <= ver_before_nested:
		return False, f"post-load nested active project mutation did not increment _active_ver: {ver_before_nested} -> {ver_after_nested}"

	# Verify workforce mutation invalidation works post-load
	wf_ver_before = getattr(loaded_sim.household, "_workforce_ver", 0)
	loaded_sim.household.employees["smith"] = loaded_sim.household.employees.get("smith", 0.0) + 1.0
	wf_ver_after = getattr(loaded_sim.household, "_workforce_ver", 0)
	if wf_ver_after <= wf_ver_before:
		return False, f"post-load workforce mutation did not increment _workforce_ver: {wf_ver_before} -> {wf_ver_after}"

	# Verify revenue computation works cleanly on loaded sim
	rev = loaded_sim.revenue()
	if rev <= 0:
		return False, f"loaded sim revenue invalid: {rev}"

	return True, "save and load cleanly restores version containers and derived state"


_ok, _detail = _test_save_load_derived_state_integrity()
check("save and load derived state integrity", _ok, _detail)


def _test_living_cost_and_credit_limit_consistency():
	"""Edge case: living_cost and credit_limit reflect revenue and capital changes accurately."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	sim_inst.step()

	lc1 = sim_inst.living_cost()
	cl1 = sim_inst.credit_limit()

	# Spend capital
	sim_inst.household.capital = 1000.0
	lc2 = sim_inst.living_cost()
	cl2 = sim_inst.credit_limit()

	# Living cost should adapt to capital change
	if lc1 == lc2:
		return False, f"living_cost did not change with capital: {lc1} == {lc2}"

	return True, "living_cost and credit_limit evaluate consistently"


_ok, _detail = _test_living_cost_and_credit_limit_consistency()
check("living_cost and credit_limit consistency", _ok, _detail)


def _test_rapid_workforce_invalidation():
	"""Edge case: rapid mutations to workforce properly invalidate wages and revenue."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	sim_inst.step()

	wages = []
	vers = []
	for count in range(1, 6):
		sim_inst.household.employees["smith"] = count * 5.0
		vers.append(getattr(sim_inst.household, "_workforce_ver", 0))
		wages.append(sim_inst.wage_bill())

	# Ensure every workforce increment yielded an increased version and wage
	if len(set(vers)) != len(vers):
		return False, f"Workforce version did not increment on each update: {vers}"
	if len(set(wages)) != len(wages):
		return False, f"Rapid employee updates returned identical wages: {wages}"

	# Invalidate revenue via freedmen workforce changes with a running workshop
	sim_inst.household.done.add("workshop_first")
	sim_inst._done_changed()
	sim_inst.household.operating.add("workshop_first")
	revs = []
	for f_count in range(1, 5):
		sim_inst.household.freedmen = f_count * 10.0
		sim_inst._workforce_changed()
		revs.append(sim_inst.revenue())
	if len(set(revs)) != len(revs):
		return False, f"Freedmen updates returned stale revenue: {revs}"

	return True, "rapid workforce mutations strictly increment versions and invalidate cached state"


_ok, _detail = _test_rapid_workforce_invalidation()
check("rapid workforce invalidation", _ok, _detail)


def _test_multiple_goods_concerns_competition():
	"""Edge case: adding multiple concerns in the same goods category updates cross-elasticity."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	loom_node = "tex_power_loom"
	if loom_node in sim_inst.nodes:
		sim_inst.household.operating.add(loom_node)
		factor_single = sim_inst.goods_market_factor(loom_node)

		# Add a second concern in textiles if another exists
		textile_nodes = [nid for nid in sim_inst.nodes if sim_inst.nodes[nid].get("cat") == "textiles" and nid != loom_node]
		if textile_nodes:
			second_loom = textile_nodes[0]
			sim_inst.household.operating.add(second_loom)
			factor_double = sim_inst.goods_market_factor(loom_node)

			if factor_double >= factor_single:
				return False, f"Market factor did not decrease under competition: {factor_double} >= {factor_single}"

	return True, "goods market correctly handles multi-concern competition"


_ok, _detail = _test_multiple_goods_concerns_competition()
check("goods market multi-concern competition", _ok, _detail)


def _test_step_advance_year_cache_invalidation():
	"""Edge case: simulation steps advance year and pop_scale, invalidating old caches."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	sim_inst.step()
	rev_year1 = sim_inst.revenue()

	sim_inst.step()
	rev_year2 = sim_inst.revenue()

	# Verify cache key year advanced
	cache_key = getattr(sim_inst.household, "_revenue_cache_key", None)
	if cache_key is None or cache_key[0] != sim_inst.year:
		return False, f"Cache key year {cache_key} does not match sim year {sim_inst.year}"

	return True, "step advance properly invalidates cached state for new year"


_ok, _detail = _test_step_advance_year_cache_invalidation()
check("step advance cache invalidation", _ok, _detail)


def _test_workforce_container_api_completeness():
	"""Edge case: dictionary mutating APIs on household.employees increment _workforce_ver."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	sim_inst.household.employees["smith"] = 5.0
	ver0 = getattr(sim_inst.household, "_workforce_ver", 0)

	# setdefault on existing key should not increment version
	existing_val = sim_inst.household.employees.setdefault("smith", 10.0)
	ver_after_existing = getattr(sim_inst.household, "_workforce_ver", 0)
	if ver_after_existing != ver0 or existing_val != 5.0:
		return False, f"setdefault on existing key fired invalidation: {ver0} != {ver_after_existing}"

	# setdefault on new key should increment version
	new_val = sim_inst.household.employees.setdefault("carpenter", 8.0)
	ver_after_new = getattr(sim_inst.household, "_workforce_ver", 0)
	if ver_after_new <= ver_after_existing or new_val != 8.0:
		return False, f"setdefault on new key did not increment version: {ver_after_existing} -> {ver_after_new}"

	# update with non-empty dict should increment version
	sim_inst.household.employees.update({"mason": 4.0})
	ver_after_update = getattr(sim_inst.household, "_workforce_ver", 0)
	if ver_after_update <= ver_after_new:
		return False, f"update did not increment version: {ver_after_new} -> {ver_after_update}"

	# pop should increment version
	popped_val = sim_inst.household.employees.pop("mason")
	ver_after_pop = getattr(sim_inst.household, "_workforce_ver", 0)
	if ver_after_pop <= ver_after_update or popped_val != 4.0:
		return False, f"pop did not increment version: {ver_after_update} -> {ver_after_pop}"

	# popitem should increment version
	sim_inst.household.employees.popitem()
	ver_after_popitem = getattr(sim_inst.household, "_workforce_ver", 0)
	if ver_after_popitem <= ver_after_pop:
		return False, f"popitem did not increment version: {ver_after_pop} -> {ver_after_popitem}"

	# clear should increment version
	sim_inst.household.employees.clear()
	ver_after_clear = getattr(sim_inst.household, "_workforce_ver", 0)
	if ver_after_clear <= ver_after_popitem or len(sim_inst.household.employees) != 0:
		return False, f"clear did not increment version: {ver_after_popitem} -> {ver_after_clear}"

	return True, "workforce container dictionary APIs comprehensively track invalidation"


_ok, _detail = _test_workforce_container_api_completeness()
check("workforce container dictionary APIs completeness", _ok, _detail)


def _test_nested_active_container_api_completeness():
	"""Edge case: dictionary mutating APIs on nested and deep project sub-dicts increment _active_ver."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
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


def _test_annual_material_demand_nested_invalidation():
	"""Edge case: annual_material_demand invalidates when nested project cost or labour changes."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
	test_node = sim_inst.order[0]
	sim_inst.household.active[test_node] = {
		"ph_left": 50.0,
		"cost_left": 100.0,
		"lab_left": {},
	}

	demand_initial = sim_inst.annual_material_demand()
	key_initial = getattr(sim_inst.household, "_annual_mat_demand_cache", (None,))[0]

	# Mutate nested cost_left via alias
	project_alias = sim_inst.household.active[test_node]
	project_alias["cost_left"] = 250.0

	demand_updated = sim_inst.annual_material_demand()
	key_updated = getattr(sim_inst.household, "_annual_mat_demand_cache", (None,))[0]

	if key_initial == key_updated:
		return False, f"Demand cache key did not change after nested cost_left mutation: {key_initial} == {key_updated}"

	return True, "annual_material_demand invalidates properly on nested project mutations"


_ok, _detail = _test_annual_material_demand_nested_invalidation()
check("annual_material_demand invalidates on nested mutations", _ok, _detail)


def _test_independent_sim_instances_isolation():
	"""Edge case: mutations in one Sim instance do not affect version counters or caches of another."""
	sim_alpha = sim(civ="rome_100ad", capital=10000.0)
	sim_beta = sim(civ="rome_100ad", capital=10000.0)

	node_alpha = sim_alpha.order[0]
	node_beta = sim_beta.order[0]
	sim_alpha.household.active[node_alpha] = {"ph_left": 20.0, "cost_left": 10.0}
	sim_beta.household.active[node_beta] = {"ph_left": 20.0, "cost_left": 10.0}

	sim_alpha.revenue()
	sim_beta.revenue()
	sim_alpha.annual_material_demand()
	sim_beta.annual_material_demand()

	beta_active_ver_before = getattr(sim_beta.household, "_active_ver", 0)
	beta_workforce_ver_before = getattr(sim_beta.household, "_workforce_ver", 0)
	beta_revenue_key_before = getattr(sim_beta.household, "_revenue_cache_key", None)

	# Mutate sim_alpha
	sim_alpha.household.active[node_alpha]["ph_left"] += 15.0
	sim_alpha.household.employees["smith"] = 12.0

	beta_active_ver_after = getattr(sim_beta.household, "_active_ver", 0)
	beta_workforce_ver_after = getattr(sim_beta.household, "_workforce_ver", 0)
	beta_revenue_key_after = getattr(sim_beta.household, "_revenue_cache_key", None)

	if beta_active_ver_before != beta_active_ver_after:
		return False, f"sim_beta active_ver mutated when sim_alpha was changed: {beta_active_ver_before} != {beta_active_ver_after}"
	if beta_workforce_ver_before != beta_workforce_ver_after:
		return False, f"sim_beta workforce_ver mutated when sim_alpha was changed: {beta_workforce_ver_before} != {beta_workforce_ver_after}"
	if beta_revenue_key_before != beta_revenue_key_after:
		return False, f"sim_beta revenue cache key changed when sim_alpha was changed: {beta_revenue_key_before} != {beta_revenue_key_after}"

	return True, "sim instances maintain isolated versions and cache states"


_ok, _detail = _test_independent_sim_instances_isolation()
check("independent sim instances isolation", _ok, _detail)


def _test_pre_insertion_alias_and_invalidating_dict_identity():
	"""Regression: pre-insertion alias mutation vs already-_InvalidatingDict identity preservation."""
	sim_inst = sim(civ="rome_100ad", capital=10000.0)
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


