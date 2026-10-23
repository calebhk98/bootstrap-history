"""Share of a society's working hours by occupation group, against plausibility bands (Complaint 619).

The grouping and the bands are data (data/world/occupation_groups.json, with sources); nothing here names a trade."""
import json
import os
from typing import Dict, List, Mapping

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "data", "world", "occupation_groups.json")
_cache: Dict[str, dict] = {}


def groups_data() -> dict:
    if not _cache:
        with open(_PATH, encoding="utf-8") as handle:
            _cache.update(json.load(handle))
    return _cache


def group_of_trade(groups: Mapping) -> Dict[str, str]:
    return {trade: group_id for group_id, group in groups.items() for trade in group["trades"]}


def hours_by_trade(society_hours: Mapping[str, float], held_hours: Mapping[str, float],
                   outside_trades, pool_trade: str) -> Dict[str, float]:
    """Every kind of work in one table: the society's hours (own-plot farming, household and hired work, the
    unskilled pool), plus what employers hold on staff. A trade an employer holds above the society's hours for
    it is people the society's split left in the unskilled `pool_trade`, so those hours move out of the pool
    into the trade (never past what the pool has); the trades in `outside_trades` (the standing army) are
    people the society's total already gave up, so their held hours are added whole. The total is then each
    person's hours once."""
    hours = dict(society_hours)
    for trade in sorted(held_hours):
        held = held_hours[trade]
        if trade in outside_trades:
            hours[trade] = hours.get(trade, 0.0) + held
            continue
        extra = held - hours.get(trade, 0.0)
        if extra <= 0.0 or trade == pool_trade:
            continue
        moved = min(extra, hours.get(pool_trade, 0.0))
        hours[pool_trade] = hours.get(pool_trade, 0.0) - moved
        hours[trade] = hours.get(trade, 0.0) + moved
    return hours


def hours_by_trade_of_all_employers(labour, society_hours: Mapping[str, float]) -> Dict[str, float]:
    """`hours_by_trade` for a running game: what the founder, firms and states keep on staff, by trade."""
    data = groups_data()
    held = {trade: labour.reserved_hours(trade) for group in data["groups"].values() for trade in group["trades"]}
    return hours_by_trade(society_hours, held, frozenset(data["outside_society_trades"]), labour.unskilled_trade())


def people_by_trade_of_all_employers(labour):
    """Working people by main occupation: the labour core's people in each trade, with what employers hold on
    staff counted once as in `hours_by_trade` (the standing army whole). The sources the bands rest on count
    the labour force by occupation, so a household that farms its own plot and spends the rest of its year on
    other work is counted in farming here, as a head count and not by the hours it spent in the field. None
    while the agent economy has not opened."""
    core = labour.core_people_by_trade()
    if core is None:
        return None
    data = groups_data()
    held = {trade: labour.reserved_people(trade) for group in data["groups"].values() for trade in group["trades"]}
    return hours_by_trade(core, held, frozenset(data["outside_society_trades"]), labour.unskilled_trade())


def shares_by_group(hours_by_trade: Mapping[str, float]) -> Dict[str, float]:
    """Each group's share of all hours; a trade in no group raises, so the data cannot silently lag the registry."""
    groups = groups_data()["groups"]
    group_for = group_of_trade(groups)
    totals = {group_id: 0.0 for group_id in groups}
    for trade, hours in hours_by_trade.items():
        totals[group_for[trade]] += hours
    everything = sum(totals.values())
    return {group_id: (total / everything if everything else 0.0) for group_id, total in totals.items()}


def occupational_report(hours_by_trade: Mapping[str, float]) -> List[dict]:
    """One row per group: share, band, and whether the share is inside it."""
    shares = shares_by_group(hours_by_trade)
    rows = []
    for group_id, group in groups_data()["groups"].items():
        low, high = group["band"]
        rows.append({"group": group_id, "share": shares[group_id], "low": low, "high": high,
                     "inside": low <= shares[group_id] <= high})
    return rows


def format_report(rows: List[dict]) -> List[str]:
    return ["  %-16s %6.1f%%  band %4.1f%% to %5.1f%%  %s" % (
        row["group"], 100 * row["share"], 100 * row["low"], 100 * row["high"], "ok" if row["inside"] else "OUTSIDE")
        for row in rows]
