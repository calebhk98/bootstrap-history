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


def hours_by_trade_of_all_employers(labour, society_hours: Mapping[str, float]) -> Dict[str, float]:
    """The society's hours by trade, plus what the other employers hold that the society's split leaves out:
    a trade's hours are the larger of the society's and those of the people the founder, firms and states keep
    on staff (the army counted whole, which the society's hours have already given up), so a trade the state
    or a merchant house hires reads at its hours, and nothing the society already counts is counted twice."""
    hours = dict(society_hours)
    for group in groups_data()["groups"].values():
        for trade in group["trades"]:
            held = labour.reserved_hours(trade)
            if held > hours.get(trade, 0.0):
                hours[trade] = held
    return hours


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
