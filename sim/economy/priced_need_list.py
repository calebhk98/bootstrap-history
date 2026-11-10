"""The priced needs of one basket as rows of an answered batch (`priced_needs.PricedBatch`), read as columns.

A reader that loops needs and their goods takes `PricedNeeds.blocks()` and the column lists of `PricedNeeds.columns` (good names, prices,
effects, shares and ceilings of the priced goods of the whole batch, a need's goods being rows `start` to `stop`). A `PricedNeed` object is made
only when something indexes or iterates the list (a screen, a mod, a test, the reference rules), and then once per need.
`PricedNeeds.of` wraps a list of `PricedNeed` objects the same way, for a caller that holds objects."""
import math
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

import numpy

from sim.world.need_basket import NeedSpec, PricedNeed, price_ceilings

from .priced_need_tables import GOODS


@dataclass(frozen=True)
class ColumnArrays:
    """The columns of the priced goods of a batch as numpy arrays (one entry per priced good, then `start` and `stop` per need row)."""
    good: numpy.ndarray          # number of the good in GOODS
    price: numpy.ndarray
    effect: numpy.ndarray
    share: numpy.ndarray
    ceiling: numpy.ndarray
    quality: numpy.ndarray       # the quality factor the buyer values (1 when the good declares none)
    limit: numpy.ndarray         # largest share of the need's units the good can meet (NaN when none)
    start: numpy.ndarray
    stop: numpy.ndarray


class ListedColumns:
    """The columns of a list of `PricedNeed` objects, with the attributes of an answered `PricedBatch` that a reader of columns takes."""

    def __init__(self, needs: Sequence[PricedNeed]) -> None:
        self.specs: List[NeedSpec] = [need.spec for need in needs]
        self.index: List[float] = [need.price_index for need in needs]
        self.start: List[int] = []
        self.stop: List[int] = []
        self.names: List[str] = []
        self.price: List[float] = []
        self.effect: List[float] = []
        self.share: List[float] = []
        self.ceiling: List[float] = []
        self._objects: Dict[int, PricedNeed] = {}
        for position, need in enumerate(needs):
            self.start.append(len(self.names))
            for good, price, effect, share in need.goods:
                self.names.append(good)
                self.price.append(price)
                self.effect.append(effect)
                self.share.append(share)
            self.ceiling.extend(need.ceilings or price_ceilings(need.goods))
            self.stop.append(len(self.names))
            self._objects[position] = need

    def need(self, position: int) -> PricedNeed:
        return self._objects[position]

    @property
    def arrays(self) -> ColumnArrays:
        """The columns as numpy arrays, made on first use."""
        found = self.__dict__.get("_arrays")
        if found is None:
            quality, limit = [], []
            for position, spec in enumerate(self.specs):
                qualities, limits = dict(spec.qualities), dict(spec.share_limits)
                for good in self.names[self.start[position]:self.stop[position]]:
                    quality.append(qualities.get(good, 1.0))
                    limit.append(limits.get(good, numpy.nan))
            found = self.__dict__["_arrays"] = ColumnArrays(
                numpy.array([GOODS.of(good) for good in self.names], dtype=numpy.int64), numpy.array(self.price, dtype=numpy.float64),
                numpy.array(self.effect, dtype=numpy.float64), numpy.array(self.share, dtype=numpy.float64),
                numpy.array(self.ceiling, dtype=numpy.float64), numpy.array(quality, dtype=numpy.float64), numpy.array(limit, dtype=numpy.float64),
                numpy.array(self.start, dtype=numpy.int64), numpy.array(self.stop, dtype=numpy.int64))
        return found


class PricedNeeds:
    """The priced needs of a basket (those with a priced good, in the basket's order): `positions` are need rows of `columns`."""
    __slots__ = ("columns", "positions", "_objects")

    def __init__(self, columns, positions: List[int]) -> None:
        self.columns = columns
        self.positions = positions
        self._objects: Optional[List[PricedNeed]] = None

    @classmethod
    def of(cls, needs: Sequence[PricedNeed]) -> "PricedNeeds":
        """The list of `PricedNeed` objects as columns (the objects are the ones given)."""
        columns = ListedColumns(needs)
        return cls(columns, list(range(len(needs))))

    def blocks(self) -> Iterator[Tuple[NeedSpec, float, int, int]]:
        """(spec, price index, first row, end row) of each priced need; its goods are those rows of the `columns` lists."""
        columns = self.columns
        specs, index, start, stop = columns.specs, columns.index, columns.start, columns.stop
        for position in self.positions:
            yield specs[position], index[position], start[position], stop[position]

    def subsistence_cost_per_person(self) -> float:
        """`need_basket.subsistence_cost_per_person`: what one person's floors cost a year at these prices."""
        specs, index = self.columns.specs, self.columns.index
        return math.fsum(index[position] * specs[position].subsistence_per_person for position in self.positions)

    def objects(self) -> List[PricedNeed]:
        """The needs as `PricedNeed` objects, made on first use and kept."""
        if self._objects is None:
            need = self.columns.need
            self._objects = [need(position) for position in self.positions]
        return self._objects

    def __len__(self) -> int:
        return len(self.positions)

    def __iter__(self) -> Iterator[PricedNeed]:
        return iter(self.objects())

    def __getitem__(self, place):
        return self.objects()[place]

    def __eq__(self, other) -> bool:
        return isinstance(other, (PricedNeeds, list, tuple)) and self.objects() == (other.objects() if isinstance(other, PricedNeeds) else list(other))

    __hash__ = None


def priced_needs_of(priced) -> PricedNeeds:
    """`priced` as `PricedNeeds`: itself when it is one, else the columns of a list of `PricedNeed` objects."""
    return priced if isinstance(priced, PricedNeeds) else PricedNeeds.of(priced)
