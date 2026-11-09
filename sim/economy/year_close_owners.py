"""Who is paid a producer's dividend, as tables built once for the close: the tiles' owner cohorts with their ownership shares,
and each producer's holders of shares.

The close pays names (cohorts, share holders, owners). The dividend kernel works over small numbers instead, so every name it may
pay is a *participant*: a position in `Participants.names`, in the order the names were first met. The book's own agent numbers
are not used here, because a name the book has not met must not be numbered until a posting pays it (the book numbers agents in
the order postings meet them; `year_close_dividends.py` does that).

    OwnerTable    tile_start / member_participant / member_share   the cohorts of each tile, sorted by id, as `ownership.spread` lists
                  tile_total                                        their ownership shares added with `sum`, as `distribute_property_income`
    ShareHolders  start / participant / share                       per producer row, its eligible holders in name order
                                                                     (`shares.split_dividend`'s filter), and whether it has any shares at all
"""
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from . import shares as producer_shares
from .cohort_store import table_of


class Participants:
    """Names in the order they were first asked for; a name's position is its participant number."""

    def __init__(self) -> None:
        self.names: List[str] = []
        self.number: Dict[str, int] = {}

    def of(self, name: str) -> int:
        found = self.number.get(name)
        if found is None:
            found = self.number[name] = len(self.names)
            self.names.append(name)
        return found


@dataclass
class OwnerTable:
    tile_start: np.ndarray            # tile -> first member; tile + 1 is one past the last (int64)
    member_participant: np.ndarray    # the cohort, as a participant (int64)
    member_share: np.ndarray          # its ownership share (float64)
    tile_total: np.ndarray            # the tile's shares added with `sum` (float64)
    tile_of_cohort: Dict[str, int]    # cohort id -> the tile's position in this table


def owner_table(record, participants: Participants) -> OwnerTable:
    """The cohorts grouped by tile; within a tile in id order, as `ownership.spread` sorts them."""
    store = table_of(record.cohorts)
    order = store.order()
    owned = store.floats("ownership_share", order)
    by_tile: Dict[str, list] = {}
    for row, tile, share in zip(order.tolist(), store.tile_names(order), owned):
        by_tile.setdefault(tile, []).append((store.ids[row], share))
    tile_start, members, shares, totals, tile_of_cohort = [0], [], [], [], {}
    for position, tile_cohorts in enumerate(by_tile.values()):
        for agent_id, share in tile_cohorts:
            members.append(participants.of(agent_id))
            shares.append(share)
            tile_of_cohort[agent_id] = position
        tile_start.append(len(members))
        totals.append(sum(share for _agent_id, share in tile_cohorts))
    return OwnerTable(np.array(tile_start, dtype=np.int64), np.array(members, dtype=np.int64), np.array(shares, dtype=np.float64),
                      np.array(totals, dtype=np.float64), tile_of_cohort)


@dataclass
class ShareHolders:
    has_shares: np.ndarray        # per producer row: the producer has a non-empty record of share holders (uint8)
    start: np.ndarray             # per producer row: first entry; row + 1 is one past the last (int64)
    participant: np.ndarray       # the holder, as a participant (int64)
    share: np.ndarray             # its part of the producer's equity (float64)


def share_holders(record, row_of: Dict[str, int], count: int, participants: Participants) -> ShareHolders:
    """The holders `shares.split_dividend` pays, for each producer row: sorted by holder name, share above the epsilon, and a cohort
    or a fund. `row_of` maps producer id to row; a producer that is not in it (it is not in the table) holds nothing here."""
    funds = record.capital_markets.capital.funds
    entries: Dict[int, list] = {}
    for producer_id, held in record.capital_markets.shares.items():
        row = row_of.get(producer_id)
        if row is None or not held:
            continue
        entries[row] = [(participants.of(holder), share) for holder, share in sorted(held.items())
                        if share > producer_shares.EPSILON and (holder in record.cohorts or holder in funds)]
    has_shares = np.zeros(count, dtype=np.uint8)
    counts = np.zeros(count, dtype=np.int64)
    for row, eligible in entries.items():
        has_shares[row] = 1
        counts[row] = len(eligible)
    start = np.zeros(count + 1, dtype=np.int64)
    np.cumsum(counts, out=start[1:])
    participant = np.zeros(int(start[-1]), dtype=np.int64)
    share = np.zeros(int(start[-1]), dtype=np.float64)
    for row, eligible in entries.items():
        first = start[row]
        for offset, (holder, part) in enumerate(eligible):
            participant[first + offset] = holder
            share[first + offset] = part
    return ShareHolders(has_shares, start, participant, share)
