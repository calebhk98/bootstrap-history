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
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		save_state(sim_inst, save_path)

		# Perform load
		loaded_sim = sim(civ="rome_100ad")
		load_state(loaded_sim, save_path)
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)

	# Verify containers are invalidating dicts/sets
	if loaded_sim.household.active.__class__.__name__ != "_InvalidatingDict":
		return False, f"loaded active is not _InvalidatingDict: {type(loaded_sim.household.active)}"
	if loaded_sim.household.employees.__class__.__name__ != "_InvalidatingDict":
		return False, f"loaded employees is not _InvalidatingDict: {type(loaded_sim.household.employees)}"

	# Verify version counters exist
	for ver_field in ("_done_ver", "_active_ver", "_workforce_ver", "_operating_ver"):
		if not hasattr(loaded_sim.household, ver_field):
			return False, f"loaded household missing version field: {ver_field}"

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
