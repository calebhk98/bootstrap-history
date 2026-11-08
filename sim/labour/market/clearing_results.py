"""The year's clearing of every market as columns, and `LabourClearing` objects built from them when a reader outside wants them.

`Clearings` holds, per market that had a stated outside option, the figures a `LabourClearing` carries; the employers' hours
and the demand schedule stay in the kernels' arrays and are read only if asked for. It is a sequence of clearings in (trade,
area) order, so a caller written for a list of `LabourClearing`s works unchanged."""
import dataclasses
from collections.abc import Sequence as SequenceBase
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import clearing_kernel as kernel
from .records import LabourClearing


class Clearings(SequenceBase):
    """Columns of one year's clearings; row `i` is the `i`th cleared market."""

    def __init__(self, names, employers, market_area, market_trade, heads, wage, hours_offered, hours_wanted, hours_hired, bid_offsets,
                 caps, bid_hours, slot_offsets, slot_employer, slot_hired):
        self.names, self.employers = names, employers                   # (area names, trade names), employer names by number
        cleared = np.flatnonzero(heads[:, kernel.STATUS])
        self.markets = cleared                                          # packed market of each cleared row
        self.area, self.trade = market_area[cleared], market_trade[cleared]
        self.wage, self.hours_offered, self.hours_wanted, self.hours_hired = wage[cleared], hours_offered[cleared], hours_wanted[cleared], hours_hired[cleared]
        self.target_wage = heads[cleared, kernel.HEAD_TARGET]           # NaN where the market has no heading wage
        self.hours_held = heads[cleared, kernel.HEAD_FULL]
        self.bid_offsets, self.caps, self.bid_hours = bid_offsets, caps, bid_hours
        self.slot_offsets, self.slot_employer, self.slot_hired = slot_offsets, slot_employer, slot_hired
        self._objects: Optional[List[LabourClearing]] = None
        self._rows: Optional[dict] = None

    def __len__(self) -> int:
        return len(self.markets)

    def _scalars(self) -> dict:
        if self._rows is None:
            self._rows = {name: getattr(self, name).tolist() for name in
                          ("area", "trade", "wage", "hours_offered", "hours_wanted", "hours_hired", "target_wage", "hours_held")}
        return self._rows

    def clearing(self, row: int) -> LabourClearing:
        return TableClearing(self, row)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self.clearing(row) for row in range(*index.indices(len(self)))]
        return self.clearing(range(len(self))[index])

    def __iter__(self):
        if self._objects is None:
            self._objects = [self.clearing(row) for row in range(len(self))]
        return iter(self._objects)

    def __eq__(self, other) -> bool:
        if not isinstance(other, (list, tuple, Clearings)) or len(other) != len(self):
            return NotImplemented if not isinstance(other, (list, tuple, Clearings)) else False
        return all(dataclasses.asdict(mine) == dataclasses.asdict(theirs) for mine, theirs in zip(self, other))

    __hash__ = None

    def hired_by_employer(self, row: int) -> Dict[str, float]:
        market = int(self.markets[row])
        low, high = int(self.slot_offsets[market]), int(self.slot_offsets[market + 1])
        hired = self.slot_hired[low:high].tolist()
        return {self.employers[employer]: amount for employer, amount in zip(self.slot_employer[low:high].tolist(), hired) if amount > 0.0}

    def demand(self, row: int) -> Tuple[Tuple[float, float], ...]:
        market = int(self.markets[row])
        low, high = int(self.bid_offsets[market]), int(self.bid_offsets[market + 1])
        return tuple(zip(self.caps[low:high].tolist(), self.bid_hours[low:high].tolist()))


class TableClearing(LabourClearing):
    """A `LabourClearing` read off a `Clearings` row: the figures at once, the employers' hours and the demand schedule when asked."""

    def __init__(self, source: Clearings, row: int):       # the dataclass initialiser would need every field
        scalars = source._scalars()
        self.trade, self.area = source.names[1][scalars["trade"][row]], source.names[0][scalars["area"][row]]
        self.wage, self.hours_offered, self.hours_wanted, self.hours_hired = (scalars[name][row] for name in (
            "wage", "hours_offered", "hours_wanted", "hours_hired"))
        target = scalars["target_wage"][row]
        self.target_wage = None if target != target else target
        self.hours_held = scalars["hours_held"][row]
        self._source, self._row = source, row

    @property
    def hired_by_employer(self) -> Dict[str, float]:
        return self._source.hired_by_employer(self._row)

    @property
    def demand(self) -> Tuple[Tuple[float, float], ...]:
        return self._source.demand(self._row)
