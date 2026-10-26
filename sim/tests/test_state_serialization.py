"""Automatic state serialization and deserialization, and the save file's validation. Complaint 640: every check builds
its state or save here (a stand-in game holds only the tree and civilisation id the validation reads); a save written
by a played game and loaded back is held by test_complaint_320_save_round_trip and test_save_round_trip_every_year."""
QUICK_TOPIC = True

import collections
import os
import random
import tempfile
import unittest

from sim.agents.api import Business
from sim.tests.harness import check


def _test_automatic_field_persistence():
	"""Verify a complete state object round-trips through serialization without handwritten field lists."""
	from sim.engine.state import (
		ActiveProjectState,
		EconomyState,
		FounderState,
		GovernanceState,
		HoldingsState,
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
		trades_created={"mason", "carpenter"},
		employees={"carpenter": 2.0},
	)
	projects = ProjectsState(
		active={"arch": proj},
		done={"stone_cutting"},
		businesses=[Business.running(["stone_cutting"], opened_year=100)],
	)
	econ = EconomyState()
	holdings = HoldingsState(farm_stock_kg=120.0)
	gov = GovernanceState()
	founder = FounderState(founder_alive=True, life_left=28.0)
	scenario = ScenarioState(year=115)
	pop = PopulationState(pop_children=20e6, pop_working_age=35e6, pop_elderly=10e6)

	state = SimulationState(
		household=hh,
		projects=projects,
		economy=econ,
		holdings=holdings,
		governance=gov,
		founder=founder,
		scenario=scenario,
		population=pop,
		_civ="rome_100ad",
		_fog=False,
	)
	state._goal = "aqueduct"

	blob = serialize_state(state)
	if not isinstance(blob, dict):
		return False, f"serialize_state did not return a dict: {type(blob)}"
	if "_version" in blob:
		return False, "serialized state carries a version stamp"

	restored = deserialize_state(blob)
	if restored.household.capital != 1250.0:
		return False, f"Household capital mismatch: {restored.household.capital}"
	if restored.projects.done != {"stone_cutting"}:
		return False, f"Projects done mismatch: {restored.projects.done}"
	if "arch" not in restored.projects.active:
		return False, f"Projects active missing 'arch': {restored.projects.active}"
	if restored.projects.active["arch"].ph_left != 80.0:
		return False, f"Active project ph_left mismatch: {restored.projects.active['arch'].ph_left}"
	from sim.materials.state import MaterialsSeat
	seat = deserialize_state(serialize_state(MaterialsSeat(shortages=collections.Counter({"charcoal": 3}))), MaterialsSeat)
	if seat.shortages.get("charcoal") != 3:
		return False, f"Shortages mismatch: {seat.shortages}"

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
		HoldingsState,
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
		businesses=[Business.running(["spinning_wheel"], opened_year=90)],
		failed_attempts=collections.defaultdict(int, {"steam_engine": 2}),
	)
	econ = EconomyState()
	holdings = HoldingsState()

	state = SimulationState(
		household=hh,
		projects=projects,
		economy=econ,
		holdings=holdings,
		governance=None,
		founder=None,
		scenario=None,
	)

	blob = serialize_state(state)
	restored = deserialize_state(blob)

	if not isinstance(restored.household.trades_created, set):
		return False, f"trades_created is not set: {type(restored.household.trades_created)}"
	if "spinning_wheel" not in restored.projects.operating or restored.projects.business.opened_year_of("spinning_wheel", 0) != 90:
		return False, f"the business did not round trip: {restored.projects.business}"
	if not isinstance(restored.projects.failed_attempts, collections.defaultdict):
		return False, f"failed_attempts is not defaultdict: {type(restored.projects.failed_attempts)}"
	from sim.materials.state import MaterialsSeat
	seat = deserialize_state(serialize_state(MaterialsSeat(shortages=collections.Counter({"iron": 4}))), MaterialsSeat)
	if not isinstance(seat.shortages, collections.Counter):
		return False, f"shortages is not Counter: {type(seat.shortages)}"
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
	hh_blob = blob["seats"]["founder"]["household"]
	proj_blob = blob["seats"]["founder"]["projects"]

	for transient in ("_done_ver", "_operating_ver", "_active_ver", "_workforce_ver", "_cap_factor"):
		if transient in hh_blob or transient in blob:
			return False, f"Transient field {transient} leaked into serialized blob: {blob}"

	return True, "Transient caches excluded from serialized output"


_ok, _detail = _test_transient_cache_exclusion()
check("Transient cache exclusion in serialization", _ok, _detail)



def _valid_save():
	"""A save blob a state serializes to, with the metadata the writer adds, and the stand-in game that would load it."""
	from types import SimpleNamespace
	from sim.engine.state import (
		EconomyState, FounderState, GovernanceState, HoldingsState, HouseholdState, PopulationState, ProjectsState,
		ScenarioState, SimulationState, serialize_state,
	)
	state = SimulationState(
		household=HouseholdState(capital=1250.0), projects=ProjectsState(done={"stone_cutting"}), economy=EconomyState(),
		holdings=HoldingsState(), governance=GovernanceState(), founder=FounderState(), scenario=ScenarioState(year=115),
		population=PopulationState())
	state._goal = "aqueduct"
	blob = serialize_state(state)
	blob.update({"_civ": "rome_100ad", "_weights": {}, "_fog": False, "_immortal": True,
	             "_rng": [3, list(random.Random(1).getstate()[1]), None]})
	game = SimpleNamespace(nodes={"aqueduct": {}, "stone_cutting": {}}, civ={"id": "rome_100ad"})
	return blob, game


def _test_cache_reset_after_load():
	"""Verify the caches a game derives from its state are wiped, and its containers re-wrapped, on save and load."""
	from types import SimpleNamespace
	from sim.engine.economy import EconomyMixin

	from sim.materials.api import ForgetReadings

	caches = ("_done_seq", "_cap_factor", "_revenue_cache_key", "_revenue_cache_val",
	          "_rev_up_candidates_cache", "_practice_cache", "_goods_cat_state_cache", "_goods_category_ratios_cache",
	          "_income_factor_cache", "_goods_mkt_op_factor_cache")
	household = SimpleNamespace(**{name: 1.7 for name in caches})
	rewrapped = []
	sent = []
	game = SimpleNamespace(household=household, send=sent.append, _done_changed=lambda: rewrapped.append("done"),
	                       _reset_operating=lambda: rewrapped.append("operating"),
	                       _reset_active=lambda: rewrapped.append("active"),
	                       _reset_workforce=lambda: rewrapped.append("workforce"))
	EconomyMixin._reset_economic_caches(game)
	held = [name for name in caches if getattr(household, name) is not None]
	if held:
		return False, f"caches still held after the reset: {held}"
	if rewrapped != ["done", "operating", "active", "workforce"]:
		return False, f"containers not re-wrapped: {rewrapped}"
	if sent != [ForgetReadings()]:
		return False, f"the materials module was not told to forget its demand tables: {sent}"
	return True, "Cache reset after load verified"


_ok, _detail = _test_cache_reset_after_load()
check("Cache reset after load", _ok, _detail)


def _test_v3_save_shape_validation():
	"""Verify _validate_save accepts valid v3 saves and rejects structurally incomplete ones for exact reasons."""
	from sim.engine.saveload import _validate_save

	valid_blob, game = _valid_save()
	err = _validate_save(valid_blob, game)
	if err is not None:
		return False, f"Valid v3 save was rejected: {err}"

	bad_missing_section = dict(valid_blob)
	bad_missing_section["seats"] = {"founder": {k: v for k, v in valid_blob["seats"]["founder"].items() if k != "projects"}}
	err = _validate_save(bad_missing_section, game)
	if not err or "projects" not in err:
		return False, f"Missing section was not rejected properly: {err}"

	bad_missing_meta = dict(valid_blob)
	del bad_missing_meta["_civ"]
	err = _validate_save(bad_missing_meta, game)
	if not err or "_civ" not in err:
		return False, f"Missing _civ was not rejected properly: {err}"

	bad_section_type = dict(valid_blob)
	bad_section_type["seats"] = {"founder": dict(valid_blob["seats"]["founder"], household="corrupt_string")}
	err = _validate_save(bad_section_type, game)
	if not err or "household" not in err or "object" not in err:
		return False, f"Corrupt section type was not rejected properly: {err}"

	return True, "v3 save shape validation and rejection verified"


_ok, _detail = _test_v3_save_shape_validation()
check("v3 save shape validation and rejection", _ok, _detail)


def _test_save_from_another_civilisation_or_tree_is_refused():
	"""Verify a save of another civilisation, or naming nodes the tree lacks, is refused with its cause."""
	from sim.engine.saveload import _validate_save
	from sim.refusal import cause_of

	valid_blob, game = _valid_save()
	err = _validate_save(dict(valid_blob, _civ="han_china_100ad"), game)
	if cause_of(err) != "save_wrong_civilisation":
		return False, f"a save of another civilisation was not refused for that cause: {err}"
	game.nodes.pop("stone_cutting")
	err = _validate_save(valid_blob, game)
	if cause_of(err) != "save_unknown_nodes" or err.facts.get("nodes") != ["stone_cutting"]:
		return False, f"a save naming a node the tree lacks was not refused with the node: {err}"
	return True, "wrong civilisation and unknown nodes refused"


_ok, _detail = _test_save_from_another_civilisation_or_tree_is_refused()
check("a save of another civilisation or tree is refused with its cause", _ok, _detail)


def _test_flat_legacy_v2_save_rejected_by_load_state():
	"""Verify loading a legacy flat save raises ValueError and leaves the game untouched."""
	import json
	from types import SimpleNamespace
	from sim.engine.saveload import load_state
	state = SimpleNamespace(household=SimpleNamespace(capital=1250.0))
	game = SimpleNamespace(nodes={"printing_press": {}}, civ={"id": "rome_100ad"}, state=state, fog=False)
	flat_v2_blob = {
		"_civ": "rome_100ad",
		"_goal": "printing_press",
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
			load_state(game, save_path)
		except ValueError as err:
			raised_err = str(err)
		if raised_err is None:
			return False, "load_state unexpectedly succeeded on flat v2 save file"
		if game.state is not state or state.household.capital != 1250.0:
			return False, "the game was changed despite the load failing"
	finally:
		if os.path.exists(save_path):
			os.remove(save_path)
	return True, "load_state rejects flat legacy v2 save and preserves the game"


_ok, _detail = _test_flat_legacy_v2_save_rejected_by_load_state()
check("load_state rejects flat legacy v2 save and preserves state", _ok, _detail)
