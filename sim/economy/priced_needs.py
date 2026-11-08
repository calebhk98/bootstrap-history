"""Baskets priced at tiles' prices in one kernel call (`priced_need_kernel.price_needs` over the tables of `priced_need_tables`), and the
`PricedNeed` objects of the answer for a reader that wants objects (`need_basket.need_prices` / `priced_need` at the same prices)."""
from typing import List, Optional, Sequence

import numpy

from sim.world.need_basket import Basket, PricedNeed

from .priced_need_kernel import price_needs
from .priced_need_tables import NeedBatch, price_matrix


class PricedBatch:
    """A batch of requests answered: the tables as Python lists (made once), read need by need."""

    def __init__(self, batch: NeedBatch, matrix: numpy.ndarray, quality_reach: float = 0.0) -> None:
        needs, rows = batch.tables()
        price_needs(needs, rows, matrix, quality_reach, batch.has_limits)
        self.batch = batch
        self.owners = batch.owners
        self.price, self.effect, self.share, self.ceiling = rows.price.tolist(), rows.effect.tolist(), rows.share.tolist(), rows.ceiling.tolist()
        self.good, self.row_priced = rows.good.tolist(), rows.priced.tolist()
        self.first, self.end = needs.first_row.tolist(), needs.end_row.tolist()
        self.index, self.need_priced = needs.price_index.tolist(), needs.need_priced.tolist()

    def priced(self, position: int) -> bool:
        return bool(self.need_priced[position])

    def need(self, position: int, names: Sequence[str], with_ceilings: bool = True) -> PricedNeed:
        """The `PricedNeed` of the priced need at need row `position`; `names` is `GOODS.names`."""
        kept = [row for row in range(self.first[position], self.end[position]) if self.row_priced[row]]
        return PricedNeed(self.batch.specs[position], self.index[position],
                          tuple((names[self.good[row]], self.price[row], self.effect[row], self.share[row]) for row in kept),
                          tuple(self.ceiling[row] for row in kept) if with_ceilings else ())


def priced_needs(basket: Basket, prices: dict, quality_reach: float = 0.0) -> List[PricedNeed]:
    """`need_basket.need_prices` for `basket` at the prices (good -> price; a good absent has none), through the tables."""
    from .priced_need_tables import GOODS
    batch = NeedBatch()
    batch.add(0, 1.0 - basket.substitution, basket.needs)
    answer = PricedBatch(batch, price_matrix([prices]), quality_reach)
    return [answer.need(position, GOODS.names) for position in range(len(basket.needs)) if answer.priced(position)]
