"""Build one module for a test with plain values standing in for the views it reads.

    module = module_harness.build(LivingStock, views={"goods_stock": {"goat": 3.0}, "year": 101})
    module.step(...); module_harness.sent(module)  # -> the commands it sent, in order

A table view is given as its value (or a function of no arguments), a keyed view as a dict (or a function of the
key), a quote as a function of its arguments. The module's own views are its own methods, as in a game."""
import types
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from sim.assembly.api import Clock


_ASSEMBLY_NAMES = ("parts", "needs", "world", "seat", "clock", "module_id", "kernels")


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
	module = _calling_its_parts(implementation)()
	module.module_id = module_id
	module.clock = Clock()
	module.kernels = {}
	module.world, module.seat = world, seat
	module.build_parts()
	_install_overrides(module)
	module.wire(_FakeNeeds(views or {}, answers or {}))
	module.setup_parts()
	module.setup()
	return module


def _install_overrides(module: Any) -> None:
	"""A test subclass of a module class may redefine a method its parts hold; the part's callers must meet the redefinition, with the
	module as `self`, so the part takes it as its own."""
	for klass in type(module).__mro__:
		if "PARTS" in vars(klass):
			break
		if "_is_harness_class" in vars(klass):
			continue
		for name, value in vars(klass).items():
			if name.startswith("__") or not callable(value):
				continue
			for part in vars(module.parts).values():
				if hasattr(type(part), name):
					setattr(part, name, types.MethodType(value, module))
					break


def _calling_its_parts(implementation: type) -> type:
	"""The class with every method of its parts callable on the module, so a test calls the behaviour it names on the module it built."""
	def forwarder(part_name: str, method: str) -> Any:
		return lambda self, *arguments, **keywords: getattr(getattr(self.parts, part_name), method)(*arguments, **keywords)
	added: Dict[str, Any] = {}
	for part_name, part_class in implementation.PARTS.items():
		for method, value in vars(part_class).items():
			if method.startswith("__") or hasattr(implementation, method) or method in added:
				continue
			if isinstance(value, property):
				added[method] = property(lambda self, part_name=part_name, method=method: getattr(getattr(self.parts, part_name), method))
			elif callable(value):
				added[method] = forwarder(part_name, method)

	def set_on_the_part(self, name: str, value: Any) -> None:
		"""A test replaces a method or a remembered figure on the module; the part that owns it takes the replacement, so the parts that call it see it."""
		if name not in _ASSEMBLY_NAMES and self.__dict__.get("parts") is not None:
			for part in vars(self.parts).values():
				if name in vars(part) or hasattr(type(part), name):
					setattr(part, name, value)
					return
		object.__setattr__(self, name, value)
	added["__setattr__"] = set_on_the_part
	added["_is_harness_class"] = True
	return type(implementation.__name__, (implementation,), added)


def part(part_class: type, siblings: Optional[Dict[str, Any]] = None, views: Optional[Dict[str, Any]] = None,
         answers: Optional[Dict[type, Any]] = None, world: Any = None, seat: Any = None) -> Any:
	"""One part over a stand-in module: `siblings` are the parts it reaches as `self.parts.<name>` (anything with the methods it calls),
	`views` and `answers` as for `build`. The part's `setup()` is not run."""
	module = SimpleNamespace(parts=SimpleNamespace(**(siblings or {})), clock=Clock(), module_id="under_test", kernels={}, world=world, seat=seat,
	                         needs=_FakeNeeds(views or {}, answers or {}), seat_of=lambda seat_id: None, seat_version=lambda channel: None)
	instance = part_class(module)
	instance.needs = module.needs
	return instance


def sent(module: Any) -> List[Any]:
	return list(module.needs.sent)
