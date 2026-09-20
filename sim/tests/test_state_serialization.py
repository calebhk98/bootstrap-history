"""Test suite for automatic state serialization, deserialization, and schema migration."""
import collections
import os
import random
import tempfile
import unittest

from sim.tests.harness import check


def _test_automatic_field_persistence():
	"""Verify a complete state object round-trips through serialization without handwritten field lists."""
	from sim.engine.state import (
		ActiveProjectState,
		EconomyState,
		FounderState,
		GovernanceState,
		HouseholdState,
		PopulationState,
		ProjectsState,
		ScenarioState,
		SimulationState,
		deserialize_state,
		serialize_state,
	)

	proj = ActiveProjectState(ph_left=80.0, cost_left=300.0, yrs=1.0, spent=100.0, lab_left={"mason": 15.0})
	hh = HouseholdState(
		capital=1250.0,
		reputation=7.5,
		trades_created={"mason", "carpenter"},
		employees={"carpenter": 2.0},
	)
	projects = ProjectsState(
		active={"arch": proj},
		done={"stone_cutting"},
		operating={"stone_cutting"},
	)
	econ = EconomyState(
		mines=[{"id": "m1", "ore": "iron", "capex": 500.0}],
		forest_ha=120.0,
		shortages={"charcoal": 3},
	)
	gov = GovernanceState(inst_units={"academy": 1.0}, gov=0.5)
	founder = FounderState(founder_alive=True, life_left=28.0)
	scenario = ScenarioState(year=115)
	pop = PopulationState(pop_children=20e6, pop_working_age=35e6, pop_elderly=10e6)

	state = SimulationState(
		household=hh,
		projects=projects,
		economy=econ,
		governance=gov,
		founder=founder,
		scenario=scenario,
		population=pop,
		_civ="rome_100ad",
		_goal="aqueduct",
		_fog=False,
	)

	blob = serialize_state(state)
	if not isinstance(blob, dict):
		return False, f"serialize_state did not return a dict: {type(blob)}"
	if blob.get("_version") != 3:
		return False, f"Expected _version == 3, got: {blob.get('_version')}"

	restored = deserialize_state(blob)
	if restored.household.capital != 1250.0 or restored.household.reputation != 7.5:
		return False, f"Household capital/reputation mismatch: {restored.household.capital}, {restored.household.reputation}"
	if restored.projects.done != {"stone_cutting"}:
		return False, f"Projects done mismatch: {restored.projects.done}"
	if "arch" not in restored.projects.active:
		return False, f"Projects active missing 'arch': {restored.projects.active}"
	if restored.projects.active["arch"].ph_left != 80.0:
		return False, f"Active project ph_left mismatch: {restored.projects.active['arch'].ph_left}"
	if restored.economy.shortages.get("charcoal") != 3:
		return False, f"Shortages mismatch: {restored.economy.shortages}"

	return True, "Automatic field persistence verified"


_ok, _detail = _test_automatic_field_persistence()
check("Automatic field persistence", _ok, _detail)


def _test_nested_project_state_reconstruction():
	"""Verify ActiveProjectState with nested lab_left requirements reconstructs with typed attribute access."""
	from sim.engine.state import ActiveProjectState, deserialize_state, serialize_state

	proj = ActiveProjectState(
		ph_left=45.0,
		cost_left=120.0,
		yrs=2.0,
		spent=80.0,
		lab_left={"smith": 5.0, "carpenter": 10.0},
		hours_effective_this_year=20.0,
	)
	blob = serialize_state(proj)
	restored = deserialize_state(blob, target_type=ActiveProjectState)

	if not isinstance(restored, ActiveProjectState):
		return False, f"Restored object is not ActiveProjectState: {type(restored)}"
	if restored.ph_left != 45.0 or restored.spent != 80.0 or restored.lab_left.get("smith") != 5.0:
		return False, f"Restored values mismatch: ph_left={restored.ph_left}, lab_left={restored.lab_left}"

	# Test typed mutation on restored object
	restored.ph_left -= 15.0
	restored.spent += 20.0
	if restored.ph_left != 30.0 or restored.spent != 100.0:
		return False, f"Typed mutation on restored object failed: ph_left={restored.ph_left}, spent={restored.spent}"

	return True, "Nested project state reconstruction verified"


_ok, _detail = _test_nested_project_state_reconstruction()
check("Nested project state reconstruction", _ok, _detail)


def _test_runtime_type_reconstruction():
	"""Verify sets, Counters, defaultdicts, and invalidating collections have correct runtime types."""
	from sim.engine.economy import _InvalidatingDict, _InvalidatingSet
	from sim.engine.state import (
		ActiveProjectState,
		EconomyState,
		HouseholdState,
		ProjectsState,
		SimulationState,
		deserialize_state,
		serialize_state,
	)

	hh = HouseholdState(
		capital=500.0,
		trades_created={"tailor", "weaver"},
		employees={"weaver": 3.0},
	)
	projects = ProjectsState(
		active={"loom": ActiveProjectState(ph_left=20.0)},
		operating={"spinning_wheel"},
		failed_attempts=collections.defaultdict(int, {"steam_engine": 2}),
	)
	econ = EconomyState(shortages=collections.Counter({"iron": 4}))

	state = SimulationState(
		household=hh,
		projects=projects,
		economy=econ,
		governance=None,
		founder=None,
		scenario=None,
	)

	blob = serialize_state(state)
	restored = deserialize_state(blob)

	if not isinstance(restored.household.trades_created, set):
		return False, f"trades_created is not set: {type(restored.household.trades_created)}"
	if not isinstance(restored.projects.operating, (set, _InvalidatingSet)):
		return False, f"operating is not set: {type(restored.projects.operating)}"
	if not isinstance(restored.projects.failed_attempts, collections.defaultdict):
		return False, f"failed_attempts is not defaultdict: {type(restored.projects.failed_attempts)}"
	if not isinstance(restored.economy.shortages, collections.Counter):
		return False, f"shortages is not Counter: {type(restored.economy.shortages)}"
	if not isinstance(restored.projects.active["loom"], ActiveProjectState):
		return False, f"active['loom'] is not ActiveProjectState: {type(restored.projects.active['loom'])}"

	return True, "Runtime type reconstruction verified"


_ok, _detail = _test_runtime_type_reconstruction()
check("Runtime type reconstruction", _ok, _detail)


def _test_transient_cache_exclusion():
	"""Verify transient version counters and cache fields are excluded from serialized output."""
	from sim.engine.state import HouseholdState, ProjectsState, SimulationState, serialize_state

	hh = HouseholdState(capital=1000.0)
	projects = ProjectsState()
	state = SimulationState(
		household=hh,
		projects=projects,
		economy=None,
		governance=None,
		founder=None,
		scenario=None,
	)

	blob = serialize_state(state)
	hh_blob = blob.get("household", {})
	proj_blob = blob.get("projects", {})

	for transient in ("_done_ver", "_operating_ver", "_active_ver", "_workforce_ver", "_cap_factor"):
		if transient in hh_blob or transient in blob:
			return False, f"Transient field {transient} leaked into serialized blob: {blob}"

	return True, "Transient caches excluded from serialized output"


_ok, _detail = _test_transient_cache_exclusion()
check("Transient cache exclusion in serialization", _ok, _detail)


def _make_sim(civ_id="rome_100ad", seed=1, events=False, fog=False):
	from sim import simulator as S
	tree, prices, nodes, wages, goods = S.load()
	goal = tree["meta"]["goal_node"]
	_lab, order, _b = S.load_strategy("recommended", nodes, goal)
	sim = S.Sim(nodes, order, random.Random(seed), events=events, manual=False, civ=S.load_civ(civ_id))
	sim.goal = goal
	sim.fog = fog
	return sim


def _test_cache_reset_after_load():
	"""Verify economic caches start clean after load."""
	from sim.engine.proto.saveload import load_state, save_state

	sim = _make_sim("rome_100ad", seed=1, events=False, fog=False)
	# Prime capability factor cache
	cap1 = sim.capability_factor()
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		save_state(sim, save_path)
		# Load into sim and verify caches are clean
		load_state(sim, save_path)
		# capability_factor cache should have been reset (_cap_factor is None)
		if sim.household._cap_factor is not None:
			return False, f"sim.household._cap_factor not None after load: {sim.household._cap_factor}"
		cap2 = sim.capability_factor()
		if cap1 != cap2:
			return False, f"Capability factor mismatch after load: {cap1} != {cap2}"
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)

	return True, "Cache reset after load verified"


_ok, _detail = _test_cache_reset_after_load()
check("Cache reset after load", _ok, _detail)



def _test_save_load_continuation_parity():
	"""Verify saving a simulation, loading into a fresh instance, and stepping both produces identical states."""
	from sim.engine.proto.saveload import load_state, save_state
	from sim.perf_fingerprint import digest, state_of

	sim1 = _make_sim("rome_100ad", seed=42, events=True, fog=False)
	sim1.goal = "printing_press"
	sim1.done_year = {}
	for _ in range(5):
		sim1.step()

	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		save_state(sim1, save_path)
		sim2 = _make_sim("rome_100ad", seed=42, events=True, fog=False)
		load_state(sim2, save_path)

		# Step both simulations for 5 more years and compare fingerprints at each step
		for year in range(5):
			sim1.step()
			sim2.step()
			d1 = digest(state_of(sim1))
			d2 = digest(state_of(sim2))
			if d1 != d2:
				return False, f"Continuation diverged at continuation year {year}: {d1} != {d2}"
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)

	return True, "Save/load continuation parity verified"


_ok, _detail = _test_save_load_continuation_parity()
check("Save/load continuation parity", _ok, _detail)


def _test_v3_save_shape_validation():
	"""Verify _validate_save accepts valid v3 saves and rejects structurally incomplete ones for exact reasons."""
	from sim.engine.proto.saveload import _validate_save, save_state, load_state
	import json

	sim = _make_sim("rome_100ad", seed=10, events=False, fog=False)
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		save_state(sim, save_path)
		with open(save_path) as handle:
			valid_blob = json.load(handle)

		# 1. Valid save passes validation
		err = _validate_save(valid_blob, sim)
		if err is not None:
			return False, f"Valid v3 save was rejected: {err}"

		# 2. Missing top-level section (e.g. projects)
		bad_missing_section = dict(valid_blob)
		del bad_missing_section["projects"]
		err = _validate_save(bad_missing_section, sim)
		if not err or "projects" not in err:
			return False, f"Missing section was not rejected properly: {err}"

		# 3. Missing metadata field (e.g. _civ)
		bad_missing_meta = dict(valid_blob)
		del bad_missing_meta["_civ"]
		err = _validate_save(bad_missing_meta, sim)
		if not err or "_civ" not in err:
			return False, f"Missing _civ was not rejected properly: {err}"

		# 4. Corrupt section shape (section is not an object)
		bad_section_type = dict(valid_blob)
		bad_section_type["household"] = "corrupt_string"
		err = _validate_save(bad_section_type, sim)
		if not err or "household" not in err or "object" not in err:
			return False, f"Corrupt section type was not rejected properly: {err}"

		# 5. Missing _version
		bad_no_version = dict(valid_blob)
		del bad_no_version["_version"]
		err = _validate_save(bad_no_version, sim)
		if not err or "_version" not in err:
			return False, f"Missing _version was not rejected properly: {err}"

		# 6. Wrong _version
		bad_version = dict(valid_blob)
		bad_version["_version"] = 999
		err = _validate_save(bad_version, sim)
		if not err or "version 999" not in err:
			return False, f"Wrong _version was not rejected properly: {err}"

	finally:
		if os.path.exists(save_path):
			os.remove(save_path)

	return True, "v3 save shape validation and rejection verified"


_ok, _detail = _test_v3_save_shape_validation()
check("v3 save shape validation and rejection", _ok, _detail)


def _test_no_v2_migration():
	"""Verify _migrate_v2_to_v3 does not exist in proto.saveload per CLAUDE.md §3.5."""
	from sim.engine.proto import saveload as S
	if hasattr(S, "_migrate_v2_to_v3"):
		return False, "_migrate_v2_to_v3 still exists in sim.engine.proto.saveload"
	return True, "No _migrate_v2_to_v3 function verified"


_ok, _detail = _test_no_v2_migration()
check("No _migrate_v2_to_v3 migration helper", _ok, _detail)


def _test_flat_legacy_v2_save_rejected_by_validate():
	"""Verify a legacy flat v2 save is rejected by _validate_save without migration."""
	from sim.engine.proto.saveload import _validate_save
	sim = _make_sim("rome_100ad", seed=10, events=False, fog=False)
	flat_v2_blob = {
		"_version": 2,
		"_civ": "rome_100ad",
		"_goal": "printing_press",
		"_civ_live": {},
		"_weights": {},
		"_rng": [3, [0] * 624, 0],
		"capital": 500.0,
		"active": {},
		"done": {"__set__": []},
	}
	err = _validate_save(flat_v2_blob, sim)
	if not err:
		return False, "Flat v2 save was unexpectedly accepted by _validate_save"
	return True, "Flat legacy v2 save rejected by _validate_save"


_ok, _detail = _test_flat_legacy_v2_save_rejected_by_validate()
check("Flat legacy v2 save rejected by _validate_save", _ok, _detail)


def _test_flat_legacy_v2_save_rejected_by_load_state():
	"""Verify load_state raises ValueError on legacy v2 save and leaves sim untouched."""
	import json
	from sim.engine.proto.saveload import load_state
	sim = _make_sim("rome_100ad", seed=10, events=False, fog=False)
	initial_capital = sim.household.capital
	flat_v2_blob = {
		"_version": 2,
		"_civ": "rome_100ad",
		"_goal": "printing_press",
		"_civ_live": {},
		"_weights": {},
		"_rng": [3, [0] * 624, 0],
		"capital": 999999.0,
		"active": {},
		"done": {"__set__": []},
	}
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		with open(save_path, "w") as handle:
			json.dump(flat_v2_blob, handle)
		raised_err = None
		try:
			load_state(sim, save_path)
		except ValueError as err:
			raised_err = str(err)
		if raised_err is None:
			return False, "load_state unexpectedly succeeded on flat v2 save file"
		# Verify sim state was left completely untouched
		if sim.household.capital != initial_capital:
			return False, f"sim capital was mutated despite load failure: {sim.household.capital} != {initial_capital}"
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)
	return True, "load_state rejects flat legacy v2 save and preserves sim state"


_ok, _detail = _test_flat_legacy_v2_save_rejected_by_load_state()
check("load_state rejects flat legacy v2 save and preserves state", _ok, _detail)


def _test_v2_stamped_v3_structure_rejected():
	"""Verify a v3-structured save with _version == 2 is rejected with the non-migrated message."""
	import json
	from sim.engine.proto.saveload import _validate_save, save_state
	sim = _make_sim("rome_100ad", seed=10, events=False, fog=False)
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		save_state(sim, save_path)
		with open(save_path) as handle:
			blob = json.load(handle)
		blob["_version"] = 2
		err = _validate_save(blob, sim)
		if not err or "not migrated" not in err:
			return False, f"Expected 'not migrated' in refusal error, got: {err}"
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)
	return True, "v2-stamped v3 save rejected with non-migrated message"


_ok, _detail = _test_v2_stamped_v3_structure_rejected()
check("v2-stamped v3 save rejected with non-migrated message", _ok, _detail)


def _test_older_version_v1_rejected():
	"""Verify a save with _version == 1 is rejected rather than migrated."""
	import json
	from sim.engine.proto.saveload import _validate_save, save_state
	sim = _make_sim("rome_100ad", seed=10, events=False, fog=False)
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		save_state(sim, save_path)
		with open(save_path) as handle:
			blob = json.load(handle)
		blob["_version"] = 1
		err = _validate_save(blob, sim)
		if not err or "Saved runs are not migrated" not in err:
			return False, f"Expected 'Saved runs are not migrated' in error, got: {err}"
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)
	return True, "Older format version 1 rejected properly"


_ok, _detail = _test_older_version_v1_rejected()
check("Older format version 1 rejected properly", _ok, _detail)


def _test_non_integer_version_rejected():
	"""Verify saves with non-integer versions (string, float) are rejected as corrupt."""
	import json
	from sim.engine.proto.saveload import _validate_save, save_state
	sim = _make_sim("rome_100ad", seed=10, events=False, fog=False)
	with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
		save_path = f.name
	try:
		save_state(sim, save_path)
		with open(save_path) as handle:
			valid_blob = json.load(handle)
		for bad_ver in ("2", 2.0):
			blob = dict(valid_blob)
			blob["_version"] = bad_ver
			err = _validate_save(blob, sim)
			if not err or "whole number" not in err:
				return False, f"Non-integer _version={bad_ver!r} was not rejected with 'whole number': {err}"
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)
	return True, "Non-integer version values rejected as corrupt"


_ok, _detail = _test_non_integer_version_rejected()
check("Non-integer version values rejected as corrupt", _ok, _detail)



