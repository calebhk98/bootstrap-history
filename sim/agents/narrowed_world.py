"""`NarrowedWorld`: the world as an actor written by a mod sees it, only the members the `World` protocol names.

The shipped world (`sim/actors/world.py`) also holds the actors module and its registry. A mod's actor runs inside this package
and calls what shipped actors call, so it is handed the protocol's members and nothing behind them; any other member is refused
with the error the caller supplies (the assembly names the mod there)."""
from typing import Any, Callable, FrozenSet

from .protocols import World


# members a shipped actor probes for with a default, because a foreign country's world does not follow them
OPTIONAL_MEMBERS = frozenset({"frontier_disease_loss", "fugitive_share"})


def world_surface() -> FrozenSet[str]:
	"""The names an actor may ask its world: the members of the `World` protocol and the optional ones."""
	return frozenset(name for name in vars(World) if not name.startswith("_")) | OPTIONAL_MEMBERS


class NarrowedWorld:
	"""`inner`, answering `allowed` names only; `refuse(name)` builds the error raised for any other."""

	def __init__(self, inner: Any, allowed: FrozenSet[str], refuse: Callable[[str], Exception]) -> None:
		self.__dict__.update(_inner=inner, _allowed=allowed, _refuse=refuse)

	def __getattr__(self, name: str) -> Any:
		if name in self.__dict__.get("_allowed", ()):
			return getattr(self.__dict__["_inner"], name)
		raise self.__dict__["_refuse"](name)


def narrowed(world: Any, refuse: Callable[[str], Exception]) -> Any:
	"""`world` as a mod's actor sees it; a world already narrowed stays as it is."""
	if isinstance(world, NarrowedWorld):
		return world
	return NarrowedWorld(world, world_surface(), refuse)
