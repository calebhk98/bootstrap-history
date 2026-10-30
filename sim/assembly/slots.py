"""Each module's saved state: built fresh for a new game or seat, revived from a save, rebound on load and seat switch.

The engine keeps the slots in its saved state (one dict per game, one per seat, module id -> dataclass); the assembly
only says which modules own which dataclasses and points each module at its own."""
import contextlib
from typing import Any, Callable, Dict, Optional

from .assemble import Assembly
from .errors import AssemblyError

WORLD = "world"
SEAT = "seat"


def _types(assembly: Assembly, scope: str) -> Dict[str, type]:
	attribute = "world_state" if scope == WORLD else "seat_state"
	return {module_id: getattr(spec, attribute) for module_id, spec in assembly.applied.specs.items()
	        if getattr(spec, attribute) is not None}


def new_slots(assembly: Assembly, scope: str) -> Dict[str, Any]:
	"""Fresh state for every module that keeps some at `scope` ("world" or "seat"), in module id order."""
	return {module_id: state_type() for module_id, state_type in sorted(_types(assembly, scope).items())}


def revive_slots(assembly: Assembly, raw: Dict[str, Any], scope: str, deserialize: Callable[[Any, type], Any]) -> Dict[str, Any]:
	"""Saved slots turned back into each module's dataclass; a slot without its module, or a module without its slot,
	is an error naming it (a save loads only into the module set that wrote it)."""
	types = _types(assembly, scope)
	extra = sorted(set(raw) - set(types))
	if extra:
		raise AssemblyError("the save holds %s state for %s, which this game does not assemble" % (scope, ", ".join(extra)))
	missing = sorted(set(types) - set(raw))
	if missing:
		raise AssemblyError("the save holds no %s state for %s" % (scope, ", ".join(missing)))
	return {module_id: deserialize(raw[module_id], types[module_id]) for module_id in sorted(types)}


def bind_world(assembly: Assembly, world_slots: Dict[str, Any]) -> None:
	for module_id, module in assembly.modules.items():
		module.world = world_slots.get(module_id)
	assembly.clock.bump_everything()


def bind_seat(assembly: Assembly, seat_id: Optional[str], seat_slots: Dict[str, Any], notify: bool = True) -> None:
	"""Point every module at `seat_id`'s own state; the clock's acting seat and the engine's follow, then each module forgets
	what it remembers per seat (`Module.seat_bound`). A game being attached binds without notifying."""
	for module_id, module in assembly.modules.items():
		module.seat = seat_slots.get(module_id)
	assembly.clock.act_as(seat_id)
	if assembly.follow is not None:
		assembly.follow(seat_id)
	if notify:
		notify_seat_bound(assembly)


def notify_seat_bound(assembly: Assembly) -> None:
	for module in assembly.modules.values():
		module.seat_bound()


def rebind(assembly: Assembly, seat_id: str, notify: bool = True) -> None:
	"""Bind the registered seat `seat_id` (its slots are the registry's now)."""
	bind_seat(assembly, seat_id, assembly.seat_records()[seat_id].modules, notify)


@contextlib.contextmanager
def act_as(assembly: Assembly, seat_id: str):
	"""Run the body as `seat_id`, then restore the seat that was acting (unless the body removed it)."""
	if seat_id not in assembly.seat_records():
		raise KeyError("no seat %r" % (seat_id,))
	previous = assembly.clock.acting_seat
	if seat_id != previous:
		rebind(assembly, seat_id)
	try:
		yield
	finally:
		if assembly.clock.acting_seat != previous and previous in assembly.seat_records():   # a handover removes a seat
			rebind(assembly, previous)
