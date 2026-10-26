"""The engine as a module while the migration runs: views and commands that still answer through `Sim`'s mixins.

A moved module reads a fact by its view name whether its owner has moved yet or not. Until it has, the bridge
publishes that view by asking the engine (never cached: legacy code writes the state behind it directly). When the
owner moves, its module publishes the same name and the bridge entry is deleted; the readers do not change. Each
`bridge_<topic>.py` declares its entries with `@bridge_view` and `@bridge_command`; this module is emptied by the
end of the migration (docs/architecture/MODULE_MIGRATION_TASKS.md)."""
from typing import Any, Callable, List, Tuple

from sim.assembly.api import TABLE, Module, ModuleSpec, ViewSpec

BRIDGE_ID = "engine"


class EngineBridge(Module):
	sim: Any = None   # the game, set by game_assembly.attach


VIEWS: List[ViewSpec] = []
COMMANDS: List[Tuple[type, str]] = []


def bridge_view(name: str, kind: str = TABLE, seat_scoped: bool = False) -> Callable:
	"""Publish `function(sim, *key_or_arguments)` as the view `name`."""
	def register(function: Callable) -> Callable:
		method = "view_" + name
		setattr(EngineBridge, method, lambda bridge, *arguments: function(bridge.sim, *arguments))
		VIEWS.append(ViewSpec(name, method, kind=kind, seat_scoped=seat_scoped, cached=False))
		return function
	return register


def bridge_command(command: type) -> Callable:
	"""Apply `command` through `function(sim, command)` until its owner module exists."""
	def register(function: Callable) -> Callable:
		method = "apply_" + command.__name__
		setattr(EngineBridge, method, lambda bridge, sent: function(bridge.sim, sent))
		COMMANDS.append((command, method))
		return function
	return register


def bridge_spec() -> ModuleSpec:
	import importlib
	import os
	import pkgutil
	here = os.path.dirname(os.path.abspath(__file__))
	for found in sorted(pkgutil.iter_modules([here]), key=lambda entry: entry.name):
		if found.name.startswith("bridge_"):
			importlib.import_module("sim.engine." + found.name)
	return ModuleSpec(BRIDGE_ID, EngineBridge, publishes=tuple(VIEWS), applies=tuple(COMMANDS))
