"""The shares of its price that producers' growth leaves, for the rows the close kernel flagged: every request of the year in one
kernel call (`share_prices`), the few markets the columns cannot hold on `Bid` objects (`expansion_price`)."""
from typing import Dict, Tuple

import numpy as np

from . import expansion_price
from .bid_columns import clearing_order_of, columns_of
from .share_prices import shares_after_additions


def asked_slots(slot_goods: np.ndarray, slot_is_output: np.ndarray, added: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """(rows, slots) of the output slots whose growth is priced: an output with units added, before its row's first empty slot
    (a recipe row's goods end at its first empty slot; a slot after it is not one of the recipe's goods)."""
    filled = np.cumprod(slot_goods >= 0, axis=1).astype(bool)      # true up to the first empty slot of each row
    return np.nonzero(slot_is_output & filled & (added > 0.0))


def share_pricer(arrays, ledger, traded: Dict[Tuple[str, str], float]):
    """`shares_of_rows(rows, added)`: for the producer rows `rows` and the units each adds to each output slot (`added`, rows by slots), the share
    of each output's price that stays; one where nothing is added or the market has no bids or no trade."""
    columns, matrices = arrays.producers, arrays.matrices
    tiles = columns.tile_names()
    area_of = arrays.area_map.area_of

    def shares_of_rows(rows: np.ndarray, added: np.ndarray) -> np.ndarray:
        shares = np.ones(added.shape)
        recipe_rows = columns.recipe_row[rows]
        slot_goods = matrices.slot_goods[recipe_rows]
        asked_row, asked_slot = asked_slots(slot_goods, matrices.slot_is_output[recipe_rows], added)
        market_of: Dict[Tuple[str, str], int] = {}
        markets, request_market, request_where = [], [], []
        for position, slot in zip(asked_row.tolist(), asked_slot.tolist()):
            good = matrices.goods.ids[slot_goods[position, slot]]
            key = (good, area_of(good, tiles[rows[position]]))
            bids = ledger.bids_by_market.get(key, ())
            if not bids:
                continue
            if key not in market_of:
                market_of[key] = len(markets)
                markets.append((key, bids))
            request_market.append(market_of[key])
            request_where.append((position, slot))
        by_market = np.argsort(request_market, kind="stable")
        request_market = [request_market[each] for each in by_market.tolist()]
        request_where = [request_where[each] for each in by_market.tolist()]
        found, needs_objects = shares_after_additions(
            [columns_of(bids) for _key, bids in markets], [clearing_order_of(bids) for _key, bids in markets],
            [traded.get(key, 0.0) for key, _bids in markets], request_market, [added[position, slot] for position, slot in request_where])
        prepared: Dict = {}
        for request, (position, slot) in enumerate(request_where):
            if needs_objects[request]:
                key, bids = markets[request_market[request]]
                pricer = expansion_price.price_share_of(ledger.bids_by_market, traded, area_of, tiles[rows[position]], prepared)
                shares[position, slot] = pricer(matrices.goods.ids[slot_goods[position, slot]], added[position, slot])
            else:
                shares[position, slot] = found[request]
        return shares
    return shares_of_rows
