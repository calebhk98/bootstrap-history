"""What a mod's code is handed in place of the game: the views and commands the mod declared, and its own saved memory.

A mod declares what it reads (`api.reads(...)`, views by name) and what it sends (`api.sends(...)`, command classes); the
assembly builds one `ModAccess` per mod and game. Asking for a view or sending a command the mod did not declare raises
`UndeclaredRead` or `UndeclaredSend`, naming the mod and the name. Answers are guarded like another module's: a dict, list
or set answer cannot be written through. The access holds no `Sim`."""
from dataclasses import dataclass
from typing import Any, Callable, FrozenSet

from .errors import AssemblyError
from .read_guard import GuardedView


class UndeclaredRead(AssemblyError):
	"""A mod asked for a view it did not declare in `api.reads(...)`."""


class UndeclaredSend(AssemblyError):
	"""A mod sent a command it did not declare in `api.sends(...)`."""


class FrameworkDoor:
	"""Unchecked views and commands, for the framework's own helpers (the effects, the stores) acting for a mod after
	checking the mod's request themselves. Mod code does not use it."""

	def __init__(self, assembly: Any):
		self._assembly = assembly

	def view(self, name: str) -> Any:
		return self._assembly.views[name]

	def send(self, command: Any) -> Any:
		return self._assembly.handlers[type(command)](command)


class ModAccess:
	"""The game as one mod sees it."""

	def __init__(self, assembly: Any, mod_id: str, reads: FrozenSet[str], sends: FrozenSet[type]):
		self._assembly = assembly
		self.mod_id = mod_id
		self.reads = reads
		self.sends = sends
		self.framework = FrameworkDoor(assembly)

	def view(self, name: str) -> Any:
		"""The published view `name`, if the mod declared it: call it, or index a keyed one."""
		if name not in self.reads:
			raise UndeclaredRead("mod %s reads the view %s, which it did not declare; add it to api.reads(...)" % (self.mod_id, name))
		return GuardedView(self._assembly.views[name], "mod %s" % self.mod_id)

	def send(self, command: Any) -> Any:
		"""Apply a command of a kind the mod declared; the answer is the owner's."""
		kind = type(command)
		if kind not in self.sends:
			raise UndeclaredSend("mod %s sent %s, which it did not declare; add it to api.sends(...)" % (self.mod_id, kind.__name__))
		return self.framework.send(command)

	def memory(self) -> dict:
		"""The mod's own JSON dict inside the saved game."""
		return self._assembly.mod_memory().setdefault("mod_state", {}).setdefault(self.mod_id, {})


def door_of(game: Any) -> Any:
	"""The object the framework's helpers act through: a mod's access gives its framework door, a game itself."""
	return game.framework if isinstance(game, ModAccess) else game


@dataclass(frozen=True)
class NeedsAccess:
	"""A function a mod provides to an extension point that wants the mod's access as its first argument; the assembly binds it."""
	function: Callable
