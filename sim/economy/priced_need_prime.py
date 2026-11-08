"""Every tile basket a view was asked to price, priced again in one kernel call after the memory is written to.

`priced_reads.kept_need_prices` answers a (tile, basket) the first time it is asked after a write to the memory. The tiles' own baskets
(`TILE_BASKET_KEY`) are asked on the same tiles after every write, so the memory remembers which it was asked (`asked_by`) and, at the first
miss of one after a write, prices all of them together; a cohort's basket key carries figures that change between phases, so those are asked one
at a time (`price_asked` takes any list of asks, for a caller that knows its pass's baskets up front): one request per distinct (tile, need, exponent) in a `NeedBatch`, the tiles' prices as one matrix from the
price grid, one `priced_need_kernel.price_needs` call, and the `PricedNeed` objects made from the answer for the readers that take objects.
The answers equal the one-need-at-a-time path (`need_basket.priced_need`) bit for bit (`test_priced_need_kernel.py`)."""
from typing import Dict, List, Optional, Tuple

from sim.world.need_basket import NeedSpec, PricedNeed

from .priced_need_tables import GOODS, NeedBatch
from .priced_needs import PricedBatch

TILE_BASKET_KEY = ("food", True)     # the key of the tile's own basket (a cohort with a hearth and nothing hired) in the kept reads

_ALONE: Dict[int, Tuple[NeedSpec, Tuple[NeedSpec, ...]]] = {}     # id(spec) -> (spec, (spec,)): a need as a basket of one; the spec is held so its id is not reused
_ALONE_LIMIT = 8192


def _alone(spec: NeedSpec) -> Tuple[NeedSpec, ...]:
    found = _ALONE.get(id(spec))
    if found is None:
        if len(_ALONE) >= _ALONE_LIMIT:
            _ALONE.clear()
        found = _ALONE[id(spec)] = (spec, (spec,))
    return found[1]


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


def need_key(tile, spec: NeedSpec, exponent: float) -> tuple:
    """The key a priced need is kept under in the view's reads: shared by every basket that holds the same need on a tile."""
    return ("priced_need", tile, spec, exponent)


def price_asked(view, reads: dict, pending: List[tuple]) -> bool:
    """Price every (tile, key, basket) of `pending` and keep the answers in `reads` (each priced need under `need_key`, each basket's
    list under ("need_prices", tile, key)). False, with nothing kept, when the view's grid cannot answer for these tiles."""
    tiles = sorted({tile for tile, _key, _basket in pending})
    row_of_tile = {tile: row for row, tile in enumerate(tiles)}
    batch = NeedBatch()
    position_of: Dict[tuple, int] = {}
    for tile, _key, basket in pending:
        exponent = 1.0 - basket.substitution
        for spec in basket.needs:
            each = need_key(tile, spec, exponent)
            if each not in reads and each not in position_of:
                position_of[each] = batch.add(row_of_tile[tile], exponent, _alone(spec))
    if position_of:
        matrix = view.offered_price_matrix(tiles, GOODS.names)
        if matrix is None:
            return False
        answer = PricedBatch(batch, matrix)
        names = GOODS.names
        for each, position in position_of.items():
            reads[each] = answer.need(position, names) if answer.priced(position) else None
    for tile, key, basket in pending:
        exponent = 1.0 - basket.substitution
        found: List[PricedNeed] = []
        for spec in basket.needs:
            need = reads[need_key(tile, spec, exponent)]
            if need is not None:
                found.append(need)
        reads[("need_prices", tile, key)] = found
    return True


def pending_asks(asked: Dict[tuple, object], reads: dict) -> Optional[List[tuple]]:
    """(tile, key, basket) of every ask remembered that `reads` does not hold yet."""
    return [(tile, key, basket) for (tile, key), basket in asked.items() if ("need_prices", tile, key) not in reads]
