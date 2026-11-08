"""The names the labour core's tables number: labour areas, trades and employers (docs/architecture/COMPILED_YEAR.md, Ids).

Areas and trades are few (hundreds) and change rarely, so `SortedIds` keeps their numbers equal to their place in sorted
name order: a kernel that must visit areas or trades "in sorted order", or break a tie by name, just uses the number. Admitting
a name that sorts into the middle renumbers the later ones; `admit` says so (it returns the old-to-new map) and the state
rebuilds its tables once (`MarketState._regrid`).

Employers are many and arrive every year, so they are numbered once (`sim.compiled_tables.ids.IdTable`: arrival order, never
reused) and `EmployerIds.rank` gives each number's place in sorted name order, for the sorts that must go by name. The seam for
the economy's shared agent numbering is `LabourIds(employers=...)`: hand it the shared `IdTable` and the core numbers its
employers with it. Until then the core owns one.
"""
from typing import Iterable, List, Optional

import numpy

from sim.compiled_tables.ids import IdTable


class SortedIds:
    """Names whose number is their place in sorted order."""

    def __init__(self, kind: str, names: Iterable[str] = ()):
        self.kind = kind
        self.names: List[str] = sorted(set(names))
        self._number_of = {name: number for number, name in enumerate(self.names)}

    def __len__(self) -> int:
        return len(self.names)

    def find(self, name: str) -> Optional[int]:
        return self._number_of.get(name)

    def number(self, name: str) -> int:
        found = self._number_of.get(name)
        if found is None:
            raise KeyError("no %s named %r" % (self.kind, name))
        return found

    def missing(self, names: Iterable[str]) -> List[str]:
        """The names not numbered yet, each once."""
        return sorted({name for name in names if name not in self._number_of})

    def admit(self, names: Iterable[str]) -> Optional[numpy.ndarray]:
        """Number the names not seen before. None when nothing changed; else the map from every old number to its new one."""
        new = self.missing(names)
        if not new:
            return None
        merged = sorted(self.names + new)
        new_number_of = {name: number for number, name in enumerate(merged)}
        old_to_new = numpy.array([new_number_of[name] for name in self.names], dtype=numpy.int64)
        self.names, self._number_of = merged, new_number_of
        return old_to_new


class EmployerIds:
    """Employers numbered in arrival order (`IdTable`), with each number's place in sorted name order."""

    def __init__(self, table: Optional[IdTable] = None):
        self.table = table if table is not None else IdTable("employer")
        self._rank = numpy.zeros(0, dtype=numpy.int64)

    def __len__(self) -> int:
        return len(self.table)

    def admit(self, names: Iterable[str]) -> numpy.ndarray:
        """The employers' numbers, in the given order; names not seen before are numbered (sorted among themselves)."""
        return self.table.admit(names)

    def name(self, number: int) -> str:
        return self.table.name(number)

    @property
    def rank(self) -> numpy.ndarray:
        """rank[number] is the place of the employer's name among all names, sorted: a sort by name is a sort by rank."""
        if len(self._rank) != len(self.table):
            names = self.table.names
            order = sorted(range(len(names)), key=names.__getitem__)
            rank = numpy.empty(len(names), dtype=numpy.int64)
            rank[order] = numpy.arange(len(names), dtype=numpy.int64)
            self._rank = rank
        return self._rank


class LabourIds:
    """The three numberings of the core's state."""

    def __init__(self, employers: Optional[IdTable] = None):
        self.areas = SortedIds("area")
        self.trades = SortedIds("trade")
        self.employers = EmployerIds(employers)

    def copy(self) -> "LabourIds":
        """Independent numberings with the same numbers (an employer table handed in from outside is copied too)."""
        other = LabourIds(IdTable.from_state("employer", self.employers.table.state()))
        other.areas.names, other.areas._number_of = list(self.areas.names), dict(self.areas._number_of)
        other.trades.names, other.trades._number_of = list(self.trades.names), dict(self.trades._number_of)
        return other
