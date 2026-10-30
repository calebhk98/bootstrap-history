"""Build one module for a test with plain values standing in for the views it reads.

    module = module_harness.build(LivingStock, views={"goods_stock": {"goat": 3.0}, "year": 101})
    module.step(...); module_harness.sent(module)  # -> the commands it sent, in order

A table view is given as its value (or a function of no arguments), a keyed view as a dict (or a function of the
key), a quote as a function of its arguments. The module's own views are its own methods, as in a game."""
from typing import Any, Dict, List, Optional

from sim.assembly.api import Clock


class _FakeView:
	def __init__(self, value: Any):
		self.value = value

	def __call__(self, *arguments: Any, **keywords: Any) -> Any:
		return self.value(*arguments, **keywords) if callable(self.value) else self.value

	def __getitem__(self, key: Any) -> Any:
		return self.value(key) if callable(self.value) else self.value[key]


class _FakeNeeds:
	def __init__(self, views: Dict[str, Any], answers: Dict[type, Any]):
		self.sent: List[Any] = []
		self._answers = answers
		for name, value in views.items():
			setattr(self, name, None if value is None else _FakeView(value))

	def send(self, command: Any) -> Any:
		self.sent.append(command)
		answer = self._answers.get(type(command))
		return answer(command) if callable(answer) else answer


def build(implementation: type, views: Optional[Dict[str, Any]] = None, answers: Optional[Dict[type, Any]] = None,
          world: Any = None, seat: Any = None, module_id: str = "under_test") -> Any:
	"""`implementation` set up as the assembly would, reading `views`; `answers` maps a command class to the reply
	(or a function of the command) the owner would give. A view given as None is an optional view that is absent."""
	module = implementation()
	module.module_id = module_id
	module.clock = Clock()
	module.needs = _FakeNeeds(views or {}, answers or {})
	module.world, module.seat = world, seat
	module.setup()
	return module


def sent(module: Any) -> List[Any]:
	return list(module.needs.sent)
