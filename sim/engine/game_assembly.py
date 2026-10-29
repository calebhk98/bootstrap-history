"""The engine's side of sim/assembly: which modules ship, which mods changed them, and the one assembly per game.

A shipped module is declared by its package: any `sim/<package>/` with a `module_spec.py` lists its specs in that
file's `MODULE_SPECS`. Mod operations come from the game's mods' code (`mod_code.operations_of`), in mod load order."""
import importlib
import os
import pkgutil
from typing import Any, Dict, List, Optional

from sim.assembly import api as assembly_api

from sim.content.api import get_ordered_mods
from sim.content.api import ancestors

DISCOVERS = "sim.*.module_spec"   # imported by name below; the spin-up cache's source closure follows it (source_closure.py)
_SIM_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHADOW_CHECK_EVERY = 61   # in debug mode, every this-many cached view reads is recomputed and compared
GUARD_READS_SWITCH = "BH_GUARD_VIEW_READS"   # set to 1 (with debug) and a module that changes another module's view answer raises


def shipped_specs() -> List[assembly_api.ModuleSpec]:
	specs: List[assembly_api.ModuleSpec] = []
	for found in sorted(pkgutil.iter_modules([_SIM_DIRECTORY]), key=lambda entry: entry.name):
		if found.ispkg and os.path.isfile(os.path.join(_SIM_DIRECTORY, found.name, "module_spec.py")):
			specs.extend(importlib.import_module("sim.%s.module_spec" % found.name).MODULE_SPECS)
	return specs


def mod_operations(mods_dir: str) -> List[assembly_api.Operations]:
	"""What the mods of `mods_dir` ask of the assembly: their allowed code runs here, once per process."""
	from .mod_code import operations_of, run_mod_code
	run_mod_code(mods_dir)
	return operations_of(mods_dir)


def build(mods_dir: Optional[str], debug: bool) -> assembly_api.Assembly:
	operations = mod_operations(mods_dir) if mods_dir else []
	by_id = {manifest.id: manifest for manifest in get_ordered_mods(mods_dir)} if mods_dir else {}

	def related(earlier: str, later: str) -> bool:
		return later in by_id and earlier in ancestors(by_id[later], by_id)
	assembly = assembly_api.assemble(shipped_specs(), operations, related, SHADOW_CHECK_EVERY if debug else 0,
	                                 guard_reads=debug and os.environ.get(GUARD_READS_SWITCH) == "1")
	from .year_phases import ordered_phases
	ordered_phases(assembly.applied.phases)   # a mod phase that cannot be placed is an error of this game
	return assembly


def check_record(assembly: assembly_api.Assembly, saved: Dict[str, Any]) -> Optional[str]:
	"""Why a save written by another module set cannot load here, or None when the sets agree."""
	current = assembly_api.record(assembly)
	if not saved or saved == current:
		return None
	differing = sorted(key for key in set(saved) | set(current) if saved.get(key) != current.get(key))
	modules = sorted(module_id for module_id in set(saved.get("modules", {})) | set(current["modules"])
	                 if saved.get("modules", {}).get(module_id) != current["modules"].get(module_id))
	kernels = sorted(name for name in set(saved.get("kernels", {})) | set(current["kernels"])
	                 if saved.get("kernels", {}).get(name) != current["kernels"].get(name))
	return "the save was written with a different module set (%s differ%s%s)" % (
		", ".join(differing), "; modules: " + ", ".join(modules) if modules else "",
		"; kernels: " + ", ".join(kernels) if kernels else "")


def attach(sim: Any) -> None:
	"""Point every module at this game's state: the world slots, and the acting seat's. A slot a new game or a new seat
	does not have yet is built fresh; a loaded save already carries all of them (revive checked it)."""
	assembly, state = sim.assembly, sim.state
	from .bridge import BRIDGE_ID
	if BRIDGE_ID in assembly.modules:
		assembly.modules[BRIDGE_ID].sim = sim
	for module_id, slot in assembly_api.new_slots(assembly, assembly_api.WORLD).items():
		state.modules.setdefault(module_id, slot)
	state.attach_purses()   # the actors' book is one of those slots: the households keep their purses in it
	for seat in state.seats.values():
		give_seat_slots(assembly, seat)
	for module_id, module in assembly.modules.items():
		module.seat_slot_of = lambda seat_id, module_id=module_id: sim.state.seats[seat_id].modules[module_id]
	state.assembly_record = assembly_api.record(assembly)
	assembly_api.bind_world(assembly, state.modules)
	switch_seat(sim, state.acting_seat)
	if "stores" in assembly.modules:
		assembly.modules["stores"].declared()   # a store declared twice is an error of building the game
	if "interface" in assembly.modules:
		assembly.modules["interface"].declared()   # a command word or figure declared twice is an error of building the game


def give_seat_slots(assembly: assembly_api.Assembly, seat: Any) -> None:
	"""Build the seat's state for every module that keeps some per seat, for a seat the slots do not cover yet."""
	for module_id, slot in assembly_api.new_slots(assembly, assembly_api.SEAT).items():
		seat.modules.setdefault(module_id, slot)


def switch_seat(sim: Any, seat_id: str) -> None:
	assembly = getattr(sim, "assembly", None)   # a test host built from seat mixins alone has none
	if assembly is not None:
		assembly_api.bind_seat(assembly, seat_id, sim.state.seats[seat_id].modules)


def revive(sim: Any, state: Any, deserialize: Any) -> None:
	"""Turn a loaded state's module slots back into each module's dataclass; ValueError when the module set differs."""
	from sim.refusal import Refusal
	reason = check_record(sim.assembly, state.assembly_record)
	try:
		if reason:
			raise assembly_api.AssemblyError(reason)
		state.modules = assembly_api.revive_slots(sim.assembly, state.modules, assembly_api.WORLD, deserialize)
		for seat in state.seats.values():
			seat.modules = assembly_api.revive_slots(sim.assembly, seat.modules, assembly_api.SEAT, deserialize)
	except assembly_api.AssemblyError as error:
		raise ValueError(Refusal("save_module_set", str(error)))
