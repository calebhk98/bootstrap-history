"""Every tile basket a view was asked to price, priced again in one kernel call after the memory is written to.

`priced_reads.kept_need_prices` answers a (tile, basket) the first time it is asked after a write to the memory. The tiles' own baskets
(`TILE_BASKET_KEY`) are asked on the same tiles after every write, so the memory remembers which it was asked (`asked_by`) and, at the first
miss of one after a write, prices all of them together; a cohort's basket key carries figures that change between phases, so a caller that knows
its pass's baskets up front asks `price_asked` for all of them (`cohort_prime.prime_cohort_baskets`): one request per (tile, basket) in a
`NeedBatch`, the tiles' prices as one matrix from the price grid, one `priced_need_kernel.price_needs` call, and for each ask the
`priced_need_list.PricedNeeds` of its rows in the answer (no `PricedNeed` object is made).
The answers equal the one-need-at-a-time path (`need_basket.priced_need`) bit for bit (`test_priced_need_kernel.py`)."""
from typing import Dict, List, Optional

from .priced_need_list import PricedNeeds
from .priced_need_tables import GOODS, NeedBatch
from .priced_needs import PricedBatch

TILE_BASKET_KEY = ("food", True)     # the key of the tile's own basket (a cohort with a hearth and nothing hired) in the kept reads


def asked_by(view) -> Optional[Dict[tuple, object]]:
    """The (tile, key) -> basket asks remembered for the view's memory: shared by every view of the memory, and forgotten when the year or the
    setup (whose `basket_for` a tile's key stands for) changes. None for a view that is not over a memory."""
    memory, setup = getattr(view, "_memory", None), getattr(view, "setup", None)
    if memory is None:
        return None
    kept = memory.__dict__.get("_asked_needs")
    if kept is None or kept[0] is not setup or kept[1] != memory.year:
        kept = memory.__dict__["_asked_needs"] = (setup, memory.year, {})
    return kept[2]


def price_asked(view, reads: dict, pending: List[tuple]) -> bool:
    """Price every (tile, key, basket) of `pending` and keep each basket's `PricedNeeds` in `reads` under ("need_prices", tile, key).
    False, with nothing kept, when the view's grid cannot answer for these tiles."""
    if not pending:
        return True
    tiles = sorted({tile for tile, _key, _basket in pending})
    row_of_tile = {tile: row for row, tile in enumerate(tiles)}
    batch = NeedBatch()
    for tile, _key, basket in pending:
        batch.add(row_of_tile[tile], 1.0 - basket.substitution, basket.needs)
    matrix_of = getattr(view, "offered_price_matrix", None)
    matrix = None if matrix_of is None else matrix_of(tiles, GOODS.names)
    if matrix is None:
        return False
    answer = PricedBatch(batch, matrix)
    for (tile, key, _basket), positions in zip(pending, answer.positions_by_request()):
        reads[("need_prices", tile, key)] = PricedNeeds(answer, positions)
    return True


def pending_asks(asked: Dict[tuple, object], reads: dict) -> Optional[List[tuple]]:
    """(tile, key, basket) of every ask remembered that `reads` does not hold yet."""
    return [(tile, key, basket) for (tile, key), basket in asked.items() if ("need_prices", tile, key) not in reads]
