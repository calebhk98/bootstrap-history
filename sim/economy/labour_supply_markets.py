"""The hours each labour market sells at a wage, read from the `LabourOffers` table's matrix (`labour_offers_kernels.offer_matrix`).

`MarketHours` is the `YearInputs.hours_sold_at` mapping (market -> hours at a wage) of a year whose offers are a table. The
labour core's clearing kernels read `columns` (the matrix and each market's range of columns) and need no per-market
function; the functions this mapping hands out on demand (`MarketSchedule`) are for the plain path, which a mod's replacement
of the fetched-hands kernel (`markets.fetch_wage`) or any other caller of the schedules takes."""
from collections.abc import MutableMapping
from typing import Callable, Dict, Iterator, Optional, Sequence, Tuple

import numpy

from sim.labour.api import sold_hours_range


class MarketSchedule:
    """The hours one market sells at a wage: the kernel over its range of the matrix."""
    __slots__ = ("matrix", "exponent", "first", "last")

    def __init__(self, matrix: numpy.ndarray, exponent: float, first: int, last: int):
        self.matrix, self.exponent, self.first, self.last = matrix, exponent, first, last

    def __call__(self, wage: float) -> float:
        return sold_hours_range(wage, self.matrix, self.exponent, self.first, self.last)

    @property
    def packed(self) -> Tuple[numpy.ndarray, float]:
        """(matrix of this market's columns, exponent): what a caller packing schedules itself reads."""
        return self.matrix[:, self.first:self.last], self.exponent


class MarketHours(MutableMapping):
    """(trade, area) -> hours sold at a wage, for every market that has an offer, keys in sorted order.

    Setting or deleting a market replaces its schedule by a caller's own function: `columns` is then None, the clearing
    kernels do not read the matrix, and the core calls the schedules one at a time (the plain path)."""

    def __init__(self, matrix: numpy.ndarray, exponent: float, markets: Sequence[Tuple[str, str]], first: numpy.ndarray, last: numpy.ndarray):
        self.matrix, self.exponent, self.markets = matrix, exponent, list(markets)
        self.first, self.last = first.tolist(), last.tolist()
        self._position: Dict[Tuple[str, str], int] = {market: position for position, market in enumerate(self.markets)}
        self._replaced: Dict[Tuple[str, str], Callable[[float], float]] = {}
        self._removed = set()

    @property
    def columns(self) -> Optional["MarketHours"]:
        """Self while every schedule is the table's (the labour core's clearing arrays read the matrix from it), else None."""
        return None if self._replaced or self._removed else self

    def __getitem__(self, market: Tuple[str, str]) -> Callable[[float], float]:
        if market in self._replaced:
            return self._replaced[market]
        if market in self._removed:
            raise KeyError(market)
        position = self._position[market]
        return MarketSchedule(self.matrix, self.exponent, self.first[position], self.last[position])

    def __setitem__(self, market: Tuple[str, str], schedule: Callable[[float], float]) -> None:
        self._replaced[market] = schedule
        self._removed.discard(market)

    def __delitem__(self, market: Tuple[str, str]) -> None:
        if market not in self:
            raise KeyError(market)
        self._replaced.pop(market, None)
        self._removed.add(market)

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        if not self._replaced and not self._removed:
            return iter(self.markets)
        return iter(sorted((set(self.markets) | set(self._replaced)) - self._removed))

    def __len__(self) -> int:
        return len(self.markets) if not self._replaced and not self._removed else sum(1 for _ in self)
