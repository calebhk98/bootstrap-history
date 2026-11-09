"""What each cohort owns of the producers: the split of the producers' net worths by ownership share (`equity.share_out`) in one kernel.

`share_out(record, worths)` gives what `equity.share_out_by_producer` gives, the very same floats and the same order of keys: each producer's
worth is split over the cohorts of its owner's tile by ownership share, after the part holders of its shares own is taken out at the share
price factor, the contributions to one agent added in the producers' order (`worths` is in the order the producers were taken) and, within a
producer, the share holders' before the tile's cohorts'.

Columns the kernel reads (one row per cohort, in sorted id order, then one per outside share holder that is no cohort):
    cohort_tile        row of the cohort's tile
    cohort_share       its ownership share
    tile_start, tile_cohorts   the cohorts of each tile (rows, in id order) as runs
Per producer in `worths` order: owner cohort row, worth; the outside holders as runs (`outside_start`) of (holder row, part) and the
sum of the parts (added in the dict's order, as `sum` does)."""
from typing import Dict, List

import numpy as np

from sim.jit import njit


@njit
def share_out_kernel(owner_cohort, worth, outside_start, outside_holder, outside_part, outside_sum, cohort_tile, cohort_share,
                     tile_start, tile_cohorts, tile_total, factor, agent_count):
    """(held by agent row, agents in the order they were first given something, how many). A tile whose shares total nothing gives its
    cohorts a worth share of zero."""
    held = np.zeros(agent_count)
    seen = np.zeros(agent_count, dtype=np.bool_)
    first_seen = np.full(agent_count, -1, dtype=np.int64)
    appeared = 0
    for producer in range(len(worth)):
        own_worth = worth[producer]
        for entry in range(outside_start[producer], outside_start[producer + 1]):
            agent = outside_holder[entry]
            if not seen[agent]:
                seen[agent] = True
                first_seen[appeared] = agent
                appeared += 1
            held[agent] += outside_part[entry] * own_worth * factor
        if outside_start[producer + 1] > outside_start[producer]:
            own_worth *= max(0.0, 1.0 - outside_sum[producer])
        tile = cohort_tile[owner_cohort[producer]]
        total = tile_total[tile]
        for place in range(tile_start[tile], tile_start[tile + 1]):
            agent = tile_cohorts[place]
            if not seen[agent]:
                seen[agent] = True
                first_seen[appeared] = agent
                appeared += 1
            held[agent] += own_worth * cohort_share[agent] / total if total > 0.0 else 0.0
    return held, first_seen, appeared


@njit
def tile_share_totals(cohort_tile, cohort_share, tile_count):
    """Per tile row: its cohorts' ownership shares added in the cohorts' order."""
    totals = np.zeros(tile_count)
    for cohort in range(len(cohort_tile)):
        totals[cohort_tile[cohort]] += cohort_share[cohort]
    return totals


def share_out(record, worths: Dict[str, float]) -> Dict[str, float]:
    """Each agent's share of the producers' `worths`: the cohorts' by ownership share on the owner's tile, and what holders of a producer's
    shares own at the share price factor."""
    cohorts = sorted(record.cohorts.values(), key=lambda each: each.agent_id)
    names: List[str] = [each.agent_id for each in cohorts]
    row_of_agent = {name: row for row, name in enumerate(names)}
    tile_names = sorted({each.tile for each in cohorts})
    row_of_tile = {tile: row for row, tile in enumerate(tile_names)}
    cohort_tile = np.fromiter((row_of_tile[each.tile] for each in cohorts), dtype=np.int64, count=len(cohorts))
    cohort_share = np.fromiter((each.ownership_share for each in cohorts), dtype=np.float64, count=len(cohorts))
    by_tile = np.argsort(cohort_tile, kind="stable")
    tile_start = np.concatenate(([0], np.cumsum(np.bincount(cohort_tile, minlength=len(tile_names)))))
    ids = list(worths)
    producers = record.producers
    owner_cohort = np.fromiter((row_of_agent[owner] for owner in producers.owners_of(ids)), dtype=np.int64, count=len(ids))
    outside_start = np.zeros(len(ids) + 1, dtype=np.int64)
    holders: List[int] = []
    parts: List[float] = []
    sums = np.zeros(len(ids))
    outside_shares = record.capital_markets.shares
    position = {each: place for place, each in enumerate(ids)}
    grouped = sorted((position[each], held_by) for each, held_by in outside_shares.items() if held_by and each in position)
    counts = np.zeros(len(ids), dtype=np.int64)
    for place, held_by in grouped:
        counts[place] = len(held_by)
        for holder, part in held_by.items():
            row = row_of_agent.get(holder)
            if row is None:
                row = row_of_agent[holder] = len(names)
                names.append(holder)
            holders.append(row)
            parts.append(part)
        sums[place] = sum(held_by.values())
    outside_start[1:] = np.cumsum(counts)
    held, first_seen, appeared = share_out_kernel(
        owner_cohort, np.fromiter(worths.values(), dtype=np.float64, count=len(ids)), outside_start, np.array(holders, dtype=np.int64),
        np.array(parts, dtype=np.float64), sums, cohort_tile, cohort_share, tile_start, by_tile,
        tile_share_totals(cohort_tile, cohort_share, len(tile_names)), record.capital_markets.capital.share_price_factor, len(names))
    return {names[agent]: float(held[agent]) for agent in first_seen[:appeared].tolist()}
