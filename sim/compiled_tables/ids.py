"""Dense whole-number ids for names (agents, goods, areas), growable and the same live and after a load.

Rules:
- A name's number is its place in `names`; numbers are never reused or changed while a game runs (a row keeps its meaning).
- New names are admitted in batches and a batch is numbered in sorted name order, so the numbering does not depend on the
  order a dict or set happened to be iterated in.
- The numbering is saved as the ordered list of names (`state`) and restored by `from_state`, so a loaded game numbers
  exactly as the live one did and kernels sum in the same row order. Never renumber by re-sorting at load.
- A name that leaves keeps its number (its row is marked dead by a column of the table that uses it); `compacted` drops the
  dead at a year boundary and returns the old-to-new map to apply to every table that holds those ids.
- A missing name is `None` from `find` and a `KeyError` from `number`, never a number that looks real."""
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy

DROPPED = -1       # compacted's old-to-new entry for a number that was dropped


class IdTable:
    """Names and their numbers."""

    def __init__(self, kind: str, names: Iterable[str] = ()):
        self.kind = kind
        self._names: List[str] = []
        self._number_of = {}
        self.admit(names)

    def __len__(self) -> int:
        return len(self._names)

    @property
    def names(self) -> Tuple[str, ...]:
        return tuple(self._names)

    @property
    def numbers(self):
        """The name-to-number dict itself, for a hot read (`numbers.get(name)`); callers must not change it."""
        return self._number_of

    def admit(self, names: Iterable[str]) -> numpy.ndarray:
        """Number the names not seen before (sorted among themselves), and give every given name's number, in the given order."""
        given = list(names)
        for name in sorted({name for name in given if name not in self._number_of}):
            self._number_of[name] = len(self._names)
            self._names.append(name)
        return numpy.array([self._number_of[name] for name in given], dtype=numpy.int64)

    def find(self, name: str) -> Optional[int]:
        return self._number_of.get(name)

    def number(self, name: str) -> int:
        found = self._number_of.get(name)
        if found is None:
            raise KeyError("no %s named %r" % (self.kind, name))
        return found

    def name(self, number: int) -> str:
        if not 0 <= number < len(self._names):
            raise IndexError("no %s numbered %d (there are %d)" % (self.kind, number, len(self._names)))
        return self._names[number]

    def describe(self, number: int) -> str:
        """The name for a log line or an error: the number is kept beside it, and a bad number is shown, not raised."""
        if 0 <= number < len(self._names):
            return "%s#%d" % (self._names[number], number)
        return "<%s #%d not in the %d known>" % (self.kind, number, len(self._names))

    def state(self) -> List[str]:
        """What a save stores: the names in number order."""
        return list(self._names)

    @classmethod
    def from_state(cls, kind: str, names: Sequence[str]) -> "IdTable":
        """The table a save's names describe, with the numbers the live game had (not re-sorted)."""
        restored = cls(kind)
        restored._names = list(names)
        restored._number_of = {name: number for number, name in enumerate(restored._names)}
        if len(restored._number_of) != len(restored._names):
            raise ValueError("a saved %s numbering repeats a name" % kind)
        return restored

    def compacted(self, keep: numpy.ndarray) -> Tuple["IdTable", numpy.ndarray]:
        """The table without the numbers whose `keep` entry is false, and the map from old number to new (DROPPED if gone)."""
        old_to_new = numpy.full(len(self._names), DROPPED, dtype=numpy.int64)
        kept = [name for number, name in enumerate(self._names) if keep[number]]
        for new_number, name in enumerate(kept):
            old_to_new[self._number_of[name]] = new_number
        return IdTable.from_state(self.kind, kept), old_to_new
