"""Plain data that tells its owner what changed.

A seat's patents, shares and offers are kept by the seats module. The exchange changes a party's record in place, as it does for every actor,
so the seat's party hands it a copy of the stored figure that reports each change (also a change deep inside) to a function, and the party
sends the owner the new figure as a command. `tracked` makes the copy and `plain` strips one back to dicts, lists and values.
"""
import copy
from typing import Any, Callable

Report = Callable[[], None]


def plain(value: Any) -> Any:
	"""`value` as dicts, lists and values only, copied."""
	if isinstance(value, dict):
		return {key: plain(item) for key, item in value.items()}
	if isinstance(value, list):
		return [plain(item) for item in value]
	return copy.deepcopy(value)


def tracked(value: Any, report: Report) -> Any:
	"""A copy of `value` in which every dict and list calls `report()` after it changes."""
	if isinstance(value, dict):
		return TrackedDict({key: tracked(item, report) for key, item in value.items()}, report)
	if isinstance(value, list):
		return TrackedList([tracked(item, report) for item in value], report)
	return copy.deepcopy(value)


class TrackedDict(dict):
	def __init__(self, items: dict, report: Report) -> None:
		super().__init__(items)
		self._report = report

	def __setitem__(self, key: Any, value: Any) -> None:
		super().__setitem__(key, tracked(value, self._report))
		self._report()

	def __delitem__(self, key: Any) -> None:
		super().__delitem__(key)
		self._report()

	def setdefault(self, key: Any, default: Any = None) -> Any:
		if key not in self:
			self[key] = default
		return self[key]

	def update(self, *arguments: Any, **keywords: Any) -> None:
		for key, value in dict(*arguments, **keywords).items():
			super().__setitem__(key, tracked(value, self._report))
		self._report()

	def pop(self, key: Any, *default: Any) -> Any:
		held = plain(super().pop(key, *default))
		self._report()
		return held

	def popitem(self) -> Any:
		key, value = super().popitem()
		self._report()
		return key, plain(value)

	def clear(self) -> None:
		super().clear()
		self._report()

	def copy(self) -> dict:
		return plain(self)

	def __copy__(self) -> dict:
		return plain(self)

	def __deepcopy__(self, memo: Any) -> dict:
		return plain(self)


class TrackedList(list):
	def __init__(self, items: list, report: Report) -> None:
		super().__init__(items)
		self._report = report

	def __setitem__(self, index: Any, value: Any) -> None:
		if isinstance(index, slice):
			super().__setitem__(index, [tracked(item, self._report) for item in value])
		else:
			super().__setitem__(index, tracked(value, self._report))
		self._report()

	def __delitem__(self, index: Any) -> None:
		super().__delitem__(index)
		self._report()

	def __iadd__(self, other: Any) -> "TrackedList":
		self.extend(other)
		return self

	def append(self, value: Any) -> None:
		super().append(tracked(value, self._report))
		self._report()

	def extend(self, values: Any) -> None:
		super().extend(tracked(value, self._report) for value in values)
		self._report()

	def insert(self, index: int, value: Any) -> None:
		super().insert(index, tracked(value, self._report))
		self._report()

	def remove(self, value: Any) -> None:
		super().remove(value)
		self._report()

	def pop(self, *index: Any) -> Any:
		held = plain(super().pop(*index))
		self._report()
		return held

	def clear(self) -> None:
		super().clear()
		self._report()

	def sort(self, *arguments: Any, **keywords: Any) -> None:
		super().sort(*arguments, **keywords)
		self._report()

	def reverse(self) -> None:
		super().reverse()
		self._report()

	def copy(self) -> list:
		return plain(self)

	def __copy__(self) -> list:
		return plain(self)

	def __deepcopy__(self, memo: Any) -> list:
		return plain(self)
