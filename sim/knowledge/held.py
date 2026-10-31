"""The containers behind what a seat holds, has heard of and has lost: they refuse a write from outside the knowledge module.

The module writes inside `writing()`, through its one add path and its other commands; anything else that mutates a held
container raises `HeldWriteError`, so a technique cannot enter a seat without its finish year, the version counter and the
caches being kept with it."""
from contextlib import contextmanager
from typing import Any, Iterator

_writing_depth = 0


class HeldWriteError(RuntimeError):
    """A held container was changed from outside the knowledge module; send the module a command instead."""


@contextmanager
def writing() -> Iterator[None]:
    """Inside the block the held containers accept writes. Only the knowledge module's handlers use it."""
    global _writing_depth
    _writing_depth += 1
    try:
        yield
    finally:
        _writing_depth -= 1


def check_writing() -> None:
    if not _writing_depth:
        raise HeldWriteError("a seat's held techniques are changed only by the knowledge module's commands (sim/knowledge/commands.py)")


def _guard(base: type, names: tuple) -> dict:
    def make(name):
        method = getattr(base, name)

        def guarded(self, *arguments, **keywords):
            check_writing()
            return method(self, *arguments, **keywords)
        guarded.__name__ = name
        return guarded
    return {name: make(name) for name in names}


_SET_WRITES = ("add", "update", "discard", "remove", "pop", "clear", "difference_update", "intersection_update",
               "symmetric_difference_update", "__ior__", "__iand__", "__isub__", "__ixor__")
_DICT_WRITES = ("__setitem__", "__delitem__", "update", "pop", "popitem", "clear", "setdefault", "__ior__")

HeldSet = type("HeldSet", (set,), _guard(set, _SET_WRITES))      # a set of node ids only the knowledge module may change
HeldMap = type("HeldMap", (dict,), _guard(dict, _DICT_WRITES))   # a dict keyed by node id only the knowledge module may change


def held_set(value: Any) -> Any:
    return value if isinstance(value, HeldSet) else HeldSet(value)


def held_map(value: Any) -> Any:
    return value if value is None or isinstance(value, HeldMap) else HeldMap(value)
