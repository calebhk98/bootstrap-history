"""Baskets priced at tiles' prices in one kernel call (`priced_need_kernel.price_needs` over the tables of `priced_need_tables`), the answer
kept as columns (`PricedBatch`) and read as `priced_need_list.PricedNeeds`; a `PricedNeed` object (`need_basket.need_prices` / `priced_need` at
the same prices) is made only for a reader that wants objects."""
from typing import List

import numpy

from sim.world.need_basket import Basket, PricedNeed

from .priced_need_kernel import price_needs
from .priced_need_list import ColumnArrays, PricedNeeds
from .priced_need_tables import GOODS, NeedBatch, price_matrix


class PricedBatch:
    """A batch of requests answered, as columns over the priced goods only: need `position` has its goods in rows `start[position]` to
    `stop[position]` of `names`, `price`, `effect`, `share` and `ceiling` (Python lists, made once), and its figure in `index[position]`."""

    def __init__(self, batch: NeedBatch, matrix: numpy.ndarray, quality_reach: float = 0.0) -> None:
        needs, rows = batch.tables()
        price_needs(needs, rows, matrix, quality_reach, batch.has_limits)
        self.batch = batch
        self.owners = batch.owners
        self.specs = batch.specs
        kept = numpy.flatnonzero(rows.priced)
        before = numpy.concatenate(([0], numpy.cumsum(rows.priced, dtype=numpy.int64)))      # before[row] = priced goods ahead of the row
        self.start, self.stop = before[needs.first_row].tolist(), before[needs.end_row].tolist()
        self.names = GOODS.name_array()[rows.good[kept]].tolist()
        self.price, self.effect, self.share, self.ceiling = (column[kept].tolist() for column in (rows.price, rows.effect, rows.share, rows.ceiling))
        self.arrays = ColumnArrays(rows.good[kept], rows.price[kept], rows.effect[kept], rows.share[kept], rows.ceiling[kept], rows.quality[kept],
                                   rows.limit[kept], before[needs.first_row], before[needs.end_row])
        self.index, self.need_priced = needs.price_index.tolist(), needs.need_priced.tolist()
        self._need_priced = needs.need_priced

    def priced(self, position: int) -> bool:
        return bool(self.need_priced[position])

    def positions_by_request(self) -> List[List[int]]:
        """For each request in the order added: the need rows it priced (those with a priced good), in the request's order."""
        priced = numpy.flatnonzero(self._need_priced)
        owner = numpy.array(self.owners, dtype=numpy.int64)[priced]
        bounds = numpy.searchsorted(owner, numpy.arange(self.batch.requests + 1)).tolist()
        listed = priced.tolist()
        return [listed[bounds[request]:bounds[request + 1]] for request in range(self.batch.requests)]

    def need(self, position: int, with_ceilings: bool = True) -> PricedNeed:
        """The `PricedNeed` of the priced need at need row `position`."""
        first, end = self.start[position], self.stop[position]
        return PricedNeed(self.specs[position], self.index[position],
                          tuple(zip(self.names[first:end], self.price[first:end], self.effect[first:end], self.share[first:end])),
                          tuple(self.ceiling[first:end]) if with_ceilings else ())


def priced_needs_at(basket: Basket, prices: dict, quality_reach: float = 0.0) -> PricedNeeds:
    """The needs of `basket` that have a priced good at the prices (good -> price; a good absent has none), through the tables."""
    batch = NeedBatch()
    batch.add(0, 1.0 - basket.substitution, basket.needs)
    answer = PricedBatch(batch, price_matrix([prices]), quality_reach)
    return PricedNeeds(answer, answer.positions_by_request()[0])


def priced_needs(basket: Basket, prices: dict, quality_reach: float = 0.0) -> List[PricedNeed]:
    """`need_basket.need_prices` for `basket` at the prices, as `PricedNeed` objects."""
    return list(priced_needs_at(basket, prices, quality_reach))
