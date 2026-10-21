"""Seeding the labour core with the trades its employers' own runs do not staff.

The opening places people by the hours producers expect to need, so a trade whose work the society's recipes and
carriage need but no producer runs yet (a carter, a sailor, an artisan) would hold nobody. Each such trade gets the
hours its share of the society's need says, in proportion to the hours the staffed trades with a share already
ask: the same ratio between two trades as between their shares. Complaint 556.
"""
from typing import Dict, Iterable, Mapping


def seed_hours(shares: Mapping[str, float], hours_needed: Mapping[str, float],
               available: Iterable[str], left_out: Iterable[str] = ()) -> Dict[str, float]:
    """Yearly hours of each trade in `available` (and not in `left_out`) that `hours_needed` does not ask any of
    but `shares` gives a share of the need. None when no staffed trade has a share to scale from."""
    skipped = set(left_out)
    staffed = [trade for trade, hours in hours_needed.items()
               if hours > 0.0 and shares.get(trade, 0.0) > 0.0 and trade not in skipped]
    staffed_share = sum(shares[trade] for trade in staffed)
    staffed_hours = sum(hours_needed[trade] for trade in staffed)
    if staffed_share <= 0.0 or staffed_hours <= 0.0:
        return {}
    return {trade: shares[trade] / staffed_share * staffed_hours
            for trade in sorted(set(available))
            if trade not in skipped and hours_needed.get(trade, 0.0) <= 0.0 and shares.get(trade, 0.0) > 0.0}
