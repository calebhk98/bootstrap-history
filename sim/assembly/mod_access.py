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
	"""A mod asked for a view it did not declare in `api.reads(...)`; `mod_id` and `view` say who and what."""

	def __init__(self, mod_id: str, view: str):
		super().__init__("mod %s reads the view %s, which it did not declare; add it to api.reads(...)" % (mod_id, view))
		self.mod_id, self.view = mod_id, view


class UndeclaredWorldMember(UndeclaredRead, AttributeError):
	"""A mod's actor asked its world for a member actors do not ask (sim/agents/protocols.py); `mod_id` and `view` (the member) say
	who and what. An AttributeError too, so a shipped actor's `hasattr` probe of the narrowed world answers no."""

	def __init__(self, mod_id: str, member: str):
		AssemblyError.__init__(self, "mod %s's actor asked its world for %s, which is not among the members actors ask "
		                       "(sim/agents/protocols.py)" % (mod_id, member))
		self.mod_id, self.view = mod_id, member


class UndeclaredSend(AssemblyError):
	"""A mod sent a command it did not declare in `api.sends(...)`; `mod_id` and `command` say who and what."""

	def __init__(self, mod_id: str, command: str):
		super().__init__("mod %s sent %s, which it did not declare; add it to api.sends(...)" % (mod_id, command))
		self.mod_id, self.command = mod_id, command


class ModAccess:
	"""The game as one mod sees it."""

	def __init__(self, assembly: Any, mod_id: str, reads: FrozenSet[str], sends: FrozenSet[type]):
		self._assembly = assembly
		self.mod_id = mod_id
		self.reads = reads
		self.sends = sends

	def view(self, name: str) -> Any:
		"""The published view `name`, if the mod declared it: call it, or index a keyed one."""
		if name not in self.reads:
			raise UndeclaredRead(self.mod_id, name)
		return GuardedView(self._assembly.views[name], "mod %s" % self.mod_id)

	def send(self, command: Any) -> Any:
		"""Apply a command of a kind the mod declared; the answer is the owner's."""
		kind = type(command)
		if kind not in self.sends:
			raise UndeclaredSend(self.mod_id, kind.__name__)
		return self._assembly.handlers[kind](command)

	def memory(self) -> dict:
		"""The mod's own JSON dict inside the saved game."""
		return self._assembly.mod_memory().setdefault("mod_state", {}).setdefault(self.mod_id, {})


@dataclass(frozen=True)
class NeedsAccess:
	"""A function a mod provides to an extension point that wants the mod's access as its first argument; the assembly binds it."""
	function: Callable
