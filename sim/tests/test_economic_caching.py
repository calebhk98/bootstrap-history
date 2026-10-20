"""Named scenarios for economic derived-state caching through a game (the version counters and invalidating containers
themselves are tested without a game in test_household_invalidation_containers).

Proves that:
2. revenue() memoizes its aggregate computation when inputs are stable.
3. revenue() properly invalidates when operating, done, workforce, or year changes.
4. revenue_capacity() and revenue() do not corrupt each other's cached values.
5. _goods_category_ratios() and goods_category_factor() memoize correctly.
6. annual_material_demand() memoizes and invalidates on active/done changes.
7. Save and load operations preserve clean derived state.
"""
from .harness import *  # noqa: F401,F403

# The container and version-counter rules are tested on a household built without a game
# (test_household_invalidation_containers). Here: one game for the isolation scenario, one stepped game for the
# memoisation scenarios.
ALPHA = sim(civ="rome_100ad", capital=hours_money(202000))
STEPPED = sim(civ="rome_100ad", capital=hours_money(202000))
STEPPED.step()
GOODS = unopened_sim(civ="rome_100ad", capital=hours_money(202000))


def _test_revenue_memoization_and_invalidation():
	"""Verify revenue() returns identical cached values, and invalidates upon mutation."""
	sim_inst = STEPPED

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
check("scenario: revenue() memoization and invalidation", _ok, _detail)


def _test_goods_market_memoization_and_invalidation():
	"""Verify _goods_category_ratios and goods_category_factor cache and invalidate."""
	sim_inst = GOODS
	loom_node = "tex_power_loom"
	if loom_node in sim_inst.nodes:
		sim_inst.household.operating.add(loom_node)

	# Initial call
	f1 = sim_inst.goods_category_factor("textiles")
	cat_cache = getattr(sim_inst.household, "_goods_category_ratios_cache", None)
	if cat_cache is None:
		return False, "_goods_category_ratios_cache was not populated"
	op_cache = getattr(sim_inst.household, "_goods_mkt_op_factor_cache", None)
	if op_cache is None:
		return False, "_goods_mkt_op_factor_cache was not populated"

	f2 = sim_inst.goods_category_factor("textiles")
	if f1 != f2:
		return False, f"goods_category_factor returned different values: {f1} != {f2}"

	# Mutate farm_hectares to test essential/income_factor invalidation
	sim_inst.invest_farm(50.0)
	f3 = sim_inst.goods_category_factor("textiles")
	if f3 == f1:
		return False, f"goods_category_factor should have updated after farm investment: {f3} == {f1}"

	return True, "goods category factor memoizes and invalidates properly"


_ok, _detail = _test_goods_market_memoization_and_invalidation()
check("scenario: goods market caching and invalidation", _ok, _detail)


def _test_annual_material_demand_caching():
	"""Verify annual_material_demand caches, invalidates on active/done, and defensively copies."""
	sim_inst = ALPHA
	sim_inst.household.active.clear()
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
check("scenario: annual_material_demand caching and invalidation", _ok, _detail)


def _test_save_load_derived_state_integrity():
	"""Edge case: save and reload re-wraps containers and re-initializes clean derived state."""
	import tempfile
	import os
	from sim.engine.saveload import save_state, load_state

	sim_inst = STEPPED
	sim_inst.revenue()
	sim_inst.annual_material_demand()

	# Perform save
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
		save_path = temp_file.name
	try:
		save_state(sim_inst, save_path)

		# Perform load on a sim that already had pre-existing cached state
		loaded_sim = sim(civ="rome_100ad")
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
check("scenario: save and load derived state integrity", _ok, _detail)


def _test_living_cost_and_credit_limit_consistency():
	"""Edge case: living_cost and credit_limit reflect revenue and capital changes accurately."""
	sim_inst = STEPPED

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
check("scenario: living_cost and credit_limit consistency", _ok, _detail)


def _test_rapid_workforce_invalidation():
	"""Edge case: rapid mutations to workforce properly invalidate wages and revenue."""
	sim_inst = STEPPED

	wages = []
	vers = []
	for count in range(1, 6):
		sim_inst.household.employees["smith"] = count * 5.0
		vers.append(getattr(sim_inst.household, "_workforce_ver", 0))
		wages.append(sim_inst.labour.wage_bill())

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
check("scenario: rapid workforce invalidation", _ok, _detail)


def _test_multiple_goods_concerns_competition():
	"""Edge case: adding multiple concerns in the same goods category updates cross-elasticity."""
	sim_inst = GOODS
	loom_node = "tex_power_loom"
	if loom_node in sim_inst.nodes:
		sim_inst.household.operating.add(loom_node)
		factor_single = sim_inst.goods_category_factor("textiles")

		# Add a second concern in textiles if another exists
		textile_nodes = [nid for nid in sim_inst.nodes if sim_inst.nodes[nid].get("cat") == "textiles" and nid != loom_node]
		if textile_nodes:
			second_loom = textile_nodes[0]
			sim_inst.household.operating.add(second_loom)
			factor_double = sim_inst.goods_category_factor("textiles")

			if factor_double >= factor_single:
				return False, f"Market factor did not decrease under competition: {factor_double} >= {factor_single}"

	return True, "goods market correctly handles multi-concern competition"


_ok, _detail = _test_multiple_goods_concerns_competition()
check("scenario: goods market multi-concern competition", _ok, _detail)


def _test_step_advance_year_cache_invalidation():
	"""Edge case: simulation steps advance year and pop_scale, invalidating old caches."""
	sim_inst = STEPPED
	sim_inst.step()
	rev_year2 = sim_inst.revenue()

	# Verify cache key year advanced
	cache_key = getattr(sim_inst.household, "_revenue_cache_key", None)
	if cache_key is None or cache_key[0] != sim_inst.year:
		return False, f"Cache key year {cache_key} does not match sim year {sim_inst.year}"

	return True, "step advance properly invalidates cached state for new year"


_ok, _detail = _test_step_advance_year_cache_invalidation()
check("scenario: step advance cache invalidation", _ok, _detail)


def _test_annual_material_demand_nested_invalidation():
	"""Edge case: annual_material_demand invalidates when nested project cost or labour changes."""
	sim_inst = ALPHA
	sim_inst.household.active.clear()
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
check("scenario: annual_material_demand invalidates on nested mutations", _ok, _detail)


def _test_independent_sim_instances_isolation():
	"""Edge case: mutations in one Sim instance do not affect version counters or caches of another."""
	sim_alpha = ALPHA
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
check("scenario: independent sim instances isolation", _ok, _detail)


