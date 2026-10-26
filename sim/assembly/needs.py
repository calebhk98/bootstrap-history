"""What a module is handed: one plain attribute per view or extension point it declared, and `send` for commands."""
from typing import Any, Callable, Dict, FrozenSet, List

from .errors import AssemblyError
from .spec import FIRST, LIST, SUM, Command


class Point:
	"""An extension point at run time: `point(*arguments)` asks every provider and combines the answers."""

	def __init__(self, name: str, combine: str):
		self.name = name
		self.combine = combine
		self.providers: List[Callable] = []

	def __call__(self, *arguments: Any) -> Any:
		if self.combine == SUM:
			return sum(provider(*arguments) for provider in self.providers)
		if self.combine == FIRST:
			for provider in self.providers:
				answer = provider(*arguments)
				if answer is not None:
					return answer
			return None
		if self.combine == LIST:
			return [provider(*arguments) for provider in self.providers]
		raise AssemblyError("extension point %s has an unknown combine rule %r" % (self.name, self.combine))


class Needs:
	"""Attributes are set by the assembly; reading one that was not declared is an AttributeError."""

	def __init__(self, module_id: str, handlers: Dict[type, Callable], allowed: FrozenSet[type]):
		self._module_id = module_id
		self._handlers = handlers
		self._allowed = allowed

	def send(self, command: Command) -> Any:
		"""Apply `command` through its owner now; the answer is the owner's result or a refusal with a cause."""
		kind = type(command)
		if kind not in self._allowed:
			raise AssemblyError("module %s sent %s, which it does not declare in `sends`" % (self._module_id, kind.__name__))
		return self._handlers[kind](command)


