"""The engine as a module while the migration runs: the views engine and UI code still read through the game.

No module reads a bridge view and the bridge applies no command. A view it publishes is asked of the engine (never cached:
legacy code writes the state behind it directly) and is deleted when its last reader reads the owner. Each
`bridge_<topic>.py` declares its entries with `@bridge_view`; this module is emptied by the end of the migration
(docs/architecture/MODULE_MIGRATION_TASKS.md)."""
from typing import Any, Callable, List

from sim.assembly.api import TABLE, Module, ModuleSpec, ViewSpec

BRIDGE_ID = "engine"
DISCOVERS = "sim.engine.bridge_*"   # imported by name in bridge_spec; the source closure follows it


class EngineBridge(Module):
	sim: Any = None   # the game, set by game_assembly.attach


VIEWS: List[ViewSpec] = []


def bridge_view(name: str, kind: str = TABLE, seat_scoped: bool = False) -> Callable:
	"""Publish `function(sim, *key_or_arguments)` as the view `name`."""
	def register(function: Callable) -> Callable:
		method = "view_" + name
		setattr(EngineBridge, method, lambda bridge, *arguments, **keywords: function(bridge.sim, *arguments, **keywords))
		VIEWS.append(ViewSpec(name, method, kind=kind, seat_scoped=seat_scoped, cached=False))
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
	return ModuleSpec(BRIDGE_ID, EngineBridge, publishes=tuple(VIEWS))
