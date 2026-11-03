"""`NarrowedWorld`: the world as an actor written by a mod sees it, only the parts and members the `World` protocol names.

The shipped world (`sim/actors/world.py`) also holds the actors module and its registry. A mod's actor runs inside this package
and calls what shipped actors call, so it is handed the protocol's parts, each answering the members of its part protocol and
nothing behind them; any other member is refused with the error the caller supplies (the assembly names the mod there)."""
from typing import Any, Callable, Dict, FrozenSet

from . import protocols


def world_surface() -> Dict[str, FrozenSet[str]]:
	"""The members an actor may ask of each part of its world: those of the part's protocol."""
	surface = {}
	for part, protocol in protocols.World.__annotations__.items():
		protocol_class = getattr(protocols, protocol) if isinstance(protocol, str) else protocol
		surface[part] = frozenset(name for name in vars(protocol_class) if not name.startswith("_"))
	return surface


class NarrowedPart:
	"""`inner`, a part of the world, answering `allowed` names only; `refuse(name)` builds the error raised for any other."""

	def __init__(self, inner: Any, allowed: FrozenSet[str], refuse: Callable[[str], Exception]) -> None:
		self.__dict__.update(_inner=inner, _allowed=allowed, _refuse=refuse)

	def __getattr__(self, name: str) -> Any:
		if name in self.__dict__.get("_allowed", ()):
			return getattr(self.__dict__["_inner"], name)
		raise self.__dict__["_refuse"](name)


class NarrowedWorld:
	"""`inner`, answering the parts of `allowed` (each narrowed to its members); `refuse(name)` builds the error raised for any other."""

	def __init__(self, inner: Any, allowed: Dict[str, FrozenSet[str]], refuse: Callable[[str], Exception]) -> None:
		self.__dict__.update(_inner=inner, _allowed=allowed, _refuse=refuse)

	def __getattr__(self, name: str) -> Any:
		allowed = self.__dict__.get("_allowed", {})
		if name in allowed:
			return NarrowedPart(getattr(self.__dict__["_inner"], name), allowed[name], self.__dict__["_refuse"])
		raise self.__dict__["_refuse"](name)


def narrowed(world: Any, refuse: Callable[[str], Exception]) -> Any:
	"""`world` as a mod's actor sees it; a world already narrowed stays as it is."""
	if isinstance(world, NarrowedWorld):
		return world
	return NarrowedWorld(world, world_surface(), refuse)
