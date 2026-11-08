"""A pack of needs priced at a vector of prices: the tables of `priced_need_tables` filled by `priced_need_kernel.price_needs`, and the
`PricedNeed` objects of them for a reader that wants objects (`need_basket.need_prices` / `priced_need` at the same prices)."""
from typing import List, Tuple

import numpy

from sim.world.need_basket import Basket, PricedNeed

from .priced_need_kernel import price_needs
from .priced_need_tables import NeedPack, priced_needs_of


def price_pack(pack: NeedPack, prices_by_good: numpy.ndarray, exponent: float, quality_reach: float = 0.0) -> Tuple[object, object]:
    """(need rows, good rows) of the pack priced at `prices_by_good` (NaN for none, in the pack's good numbering), mixed for a buyer who
    pays for quality to `quality_reach`; a basket's `exponent` is one minus its substitution elasticity."""
    needs, rows = pack.with_answers()
    price_needs(needs, rows, prices_by_good, exponent, quality_reach, pack.has_limits)
    return needs, rows


def priced_needs(pack: NeedPack, prices_by_good: numpy.ndarray, basket: Basket, quality_reach: float = 0.0) -> List[PricedNeed]:
    """`need_basket.need_prices` for the pack at the prices, as objects (the pack is the basket's needs, `pack_needs(basket.needs)`)."""
    needs, rows = price_pack(pack, prices_by_good, 1.0 - basket.substitution, quality_reach)
    return priced_needs_of(pack, needs, rows)
