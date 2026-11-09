"""What the labour year leaves in the record for next year, written for every cleared market at once: the hours offered and not
hired, and the share of offered hours households expect to sell (smoothed over the years)."""
from typing import Dict, Sequence

import numpy as np

from .households_work import SOLD_SHARE_SMOOTHING
from .market_table_specs import KEY_SEPARATOR


def market_keys(trades: Sequence[str], areas: Sequence[str]) -> list:
    """`market_memory.market_key` of each (trade, area) pair."""
    return np.char.add(np.char.add(np.asarray(trades, dtype=str), KEY_SEPARATOR), np.asarray(areas, dtype=str)).tolist()


def sold_shares(hours_hired: np.ndarray, hours_idle: np.ndarray) -> np.ndarray:
    """`households_work.sold_share` of each market: the share of the hours offered that found a buyer, one when none were offered."""
    hired, idle = np.where(hours_hired > 0.0, hours_hired, 0.0), np.where(hours_idle > 0.0, hours_idle, 0.0)
    offered = hired + idle
    return np.where(offered > 0.0, hired / np.where(offered > 0.0, offered, 1.0), 1.0)


def note_idle_hours(sold_share_expected: Dict[str, float], trades: Sequence[str], areas: Sequence[str], hours_hired: np.ndarray,
                    idle: np.ndarray) -> Dict[str, float]:
    """The idle hours of each market by market key; a market that had any hours offered moves its expected sold share (in
    `sold_share_expected`) `SOLD_SHARE_SMOOTHING` of the way to the year's share (a market new to the record starts from one)."""
    keys = market_keys(trades, areas)
    hours_idle = dict(zip(keys, idle.tolist()))
    offered = np.flatnonzero(hours_hired + idle > 0.0)
    if not len(offered):
        return hours_idle
    kept = [keys[place] for place in offered.tolist()]
    expected = np.fromiter((sold_share_expected.get(key, 1.0) for key in kept), dtype=np.float64, count=len(kept))
    realised = sold_shares(hours_hired[offered], idle[offered])
    sold_share_expected.update(zip(kept, (expected + SOLD_SHARE_SMOOTHING * (realised - expected)).tolist()))
    return hours_idle
