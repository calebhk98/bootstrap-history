"""Regression tests for canonical package identity throughout the repository.

Verifies that:
1. `sim` is the sole canonical Python package identity.
2. Core modules (constants, world, engine, proto) resolve only under `sim.*`.
3. Bare module names ('constants', 'engine', 'world', 'simulator') are not in sys.modules.
4. Shared registries and singletons (such as `sim.constants._REGISTRY`) have a single identity.
"""
import sys
from .harness import *  # noqa: F401,F403


def _test_canonical_module_identities():
	"""Verify core modules are imported under sim.* and bare names are absent from sys.modules."""
	import sim.constants as sim_constants
	import sim.engine.core as sim_core
	import sim.world.demography as sim_demography
	import sim.engine.proto.saveload as sim_saveload

	# Disallowed bare top-level identities
	disallowed_bare_names = ("constants", "engine", "world", "simulator", "data")
	present_bare = [name for name in disallowed_bare_names if name in sys.modules]
	if present_bare:
		return False, f"Disallowed bare module identities found in sys.modules: {present_bare}"

	# Ensure expected canonical package paths exist in sys.modules
	expected_canonical = (
		"sim.constants",
		"sim.engine.core",
		"sim.world.demography",
		"sim.engine.proto.saveload",
	)
	missing_canonical = [name for name in expected_canonical if name not in sys.modules]
	if missing_canonical:
		return False, f"Canonical module identities missing from sys.modules: {missing_canonical}"

	return True, "Core modules have single canonical identity under sim.*"


_ok, _detail = _test_canonical_module_identities()
check("canonical package root sim.* in sys.modules", _ok, _detail)


def _test_constants_registry_single_identity():
	"""Verify sim.constants._REGISTRY has exactly one identity and is not duplicated."""
	import sim.constants as sim_constants

	# Ensure REGISTRY is non-empty after engine imports
	if not hasattr(sim_constants, "REGISTRY"):
		return False, "sim.constants has no REGISTRY attribute"
	if len(sim_constants.REGISTRY) == 0:
		return False, "sim.constants.REGISTRY is empty"

	# If 'constants' were in sys.modules, its REGISTRY must not be a distinct dictionary
	if "constants" in sys.modules:
		bare_constants = sys.modules["constants"]
		if getattr(bare_constants, "REGISTRY", None) is not sim_constants.REGISTRY:
			return False, "Dual REGISTRY dictionaries detected between bare constants and sim.constants"

	return True, "constants registry has single authoritative identity"


_ok, _detail = _test_constants_registry_single_identity()
check("constants registry has single authoritative identity", _ok, _detail)


def _test_simulator_reexport_class_identity():
	"""Verify Sim class re-exported by simulator is identical to sim.engine.core.Sim."""
	import sim.simulator as sim_simulator
	import sim.engine.core as sim_core

	if sim_simulator.Sim is not sim_core.Sim:
		return False, f"Sim class mismatch: {sim_simulator.Sim} is not {sim_core.Sim}"

	return True, "Sim class identity preserved across re-exports"


_ok, _detail = _test_simulator_reexport_class_identity()
check("Sim class identity preserved across re-exports", _ok, _detail)


def _test_subprocess_clean_package_identity():
	"""Verify fresh Python process loading sim.simulator does not inject bare module identities."""
	cmd = [
		sys.executable,
		"-c",
		"import sys, sim.simulator; bare = [m for m in ('constants', 'engine', 'world') if m in sys.modules]; sys.exit(len(bare))"
	]
	res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
	if res.returncode != 0:
		return False, f"Subprocess reported bare module identities in sys.modules: returncode={res.returncode}"

	return True, "Subprocess has clean package identity without bare module leakage"


_ok, _detail = _test_subprocess_clean_package_identity()
check("subprocess has clean package identity without bare module leakage", _ok, _detail)


def _test_no_sys_path_leak_of_sim_directory():
	"""Verify sim/ directory itself is not inserted into sys.path."""
	import sim.simulator

	here_normalized = os.path.normcase(os.path.abspath(HERE))
	sim_paths = [p for p in sys.path if os.path.normcase(os.path.abspath(p)) == here_normalized]
	if sim_paths:
		return False, f"sim/ directory found in sys.path: {sim_paths}"

	return True, "sim/ directory is not on sys.path"


_ok, _detail = _test_no_sys_path_leak_of_sim_directory()
check("sim/ directory is not on sys.path", _ok, _detail)
