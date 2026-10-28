"""A view another module reads cannot be changed through its answer: in guarded games a dict, list or set answer (of any
subclass: a Counter, a defaultdict, an owner's ledger) comes back as a guarded copy of its own class whose writing methods
raise, naming the view and the reader. Nested values are guarded as they are read.

The copy keeps the answer's class, so isinstance, its own read methods and json behave as before. A reader that needs a
copy it can change makes one (`dict(answer)`, `list(answer)`). Other objects pass unguarded: a view that hands out a live
object is a `legacy_*` debt, counted by tools/measure/module_graph.py."""
from collections import defaultdict
from typing import Any, Callable, Dict

from .errors import ViewWrite

DICT_WRITES = ("__setitem__", "__delitem__", "update", "pop", "popitem", "clear", "setdefault", "__ior__", "subtract")
LIST_WRITES = ("__setitem__", "__delitem__", "append", "extend", "insert", "pop", "remove", "clear", "sort", "reverse", "__iadd__",
               "__imul__")
SET_WRITES = ("add", "discard", "remove", "pop", "clear", "update", "intersection_update", "difference_update",
              "symmetric_difference_update", "__ior__", "__iand__", "__isub__", "__ixor__")

_GUARDED_CLASSES: Dict[type, type] = {}


def guarded(value: Any, view_name: str, reader: str) -> Any:
	if getattr(value, "_guard_view", None) is not None or not isinstance(value, (dict, list, set)):
		return value
	guarded_class = _GUARDED_CLASSES.get(type(value)) or _guarded_class(type(value))
	copy = guarded_class.__new__(guarded_class)
	if isinstance(value, dict):
		dict.update(copy, value)
	elif isinstance(value, list):
		list.extend(copy, value)
	else:
		set.update(copy, value)
	if isinstance(value, defaultdict):
		copy.default_factory = value.default_factory
	copy.__dict__.update(getattr(value, "__dict__", {}))
	copy.__dict__["_guard_view"], copy.__dict__["_guard_reader"] = view_name, reader
	return copy


def _refusal(container: str) -> Callable:
	def refuse(self, *arguments: Any, **keywords: Any) -> None:
		raise ViewWrite("module %s changed the %s answered by view %s; an owner's state changes only through its commands" % (
			self._guard_reader, container, self._guard_view))
	return refuse


def _guarded_class(base: type) -> type:
	if issubclass(base, dict):
		container, writes, reads = "dict", DICT_WRITES, _dict_reads(base)
	elif issubclass(base, list):
		container, writes, reads = "list", LIST_WRITES, _list_reads(base)
	else:
		container, writes, reads = "set", SET_WRITES, {}
	members = dict(reads)
	members.update({name: _refusal(container) for name in writes if hasattr(base, name)})
	guarded_class = type("Guarded" + base.__name__, (base,), members)
	_GUARDED_CLASSES[base] = guarded_class
	return guarded_class


def _dict_reads(base: type) -> Dict[str, Callable]:
	def __getitem__(self, key):
		return guarded(base.__getitem__(self, key), self._guard_view, self._guard_reader)

	def get(self, key, default=None):
		return guarded(base.get(self, key, default), self._guard_view, self._guard_reader)

	def values(self):
		return [guarded(value, self._guard_view, self._guard_reader) for value in base.values(self)]

	def items(self):
		return [(key, guarded(value, self._guard_view, self._guard_reader)) for key, value in base.items(self)]
	return {"__getitem__": __getitem__, "get": get, "values": values, "items": items}


def _list_reads(base: type) -> Dict[str, Callable]:
	def __getitem__(self, index):
		item = base.__getitem__(self, index)
		if isinstance(index, slice):
			return guarded(item, self._guard_view, self._guard_reader)
		return guarded(item, self._guard_view, self._guard_reader)

	def __iter__(self):
		for item in base.__iter__(self):
			yield guarded(item, self._guard_view, self._guard_reader)
	return {"__getitem__": __getitem__, "__iter__": __iter__}


class GuardedView:
	"""A view as one reader sees it: the same calls, the answers guarded."""

	def __init__(self, view: Any, reader: str):
		self._view, self._reader = view, reader

	def __call__(self, *arguments: Any, **keywords: Any) -> Any:
		return guarded(self._view(*arguments, **keywords), self._view.spec.name, self._reader)

	def __getitem__(self, key: Any) -> Any:
		return guarded(self._view[key], self._view.spec.name, self._reader)

	def __getattr__(self, name: str) -> Any:
		return getattr(self._view, name)
