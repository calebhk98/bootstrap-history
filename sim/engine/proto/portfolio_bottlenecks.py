"""Running work grouped by what blocks it (Complaints/88).

The kind of each project is the shared blocker vocabulary (blockers.py),
translated from the constraint `portfolio` already reads off `waiting_on`; the
pools are the engine's own demand and supply figures.
"""

from ..blockers import BLOCKER_MEANING, RUNNING_CONSTRAINT_KIND

# Triage order: what only the player can fix first, pace last.
KIND_ORDER = ("specialists", "supply", "money", "hours", "calendar", "idle")


def blocker_kind_of(constraint):
    return RUNNING_CONSTRAINT_KIND.get(constraint, "idle")


def _pools(sim, kind, rows, trade_rows, pool_total, throttle, binding):
    """The resource pools behind one group: demand against supply, from the engine."""
    members = {row["id"] for row in rows}
    if kind == "specialists":
        return [{"pool": row["trade"], "trade": row["trade"],
                 "demand_hours_this_year": row["demand_hours_this_year"],
                 "supply_hours_this_year": row["supply_hours_this_year"],
                 "oversubscribed": row["oversubscribed"],
                 "projects_affected": len(members & set(row["projects_drawing_on_it"]))}
                for row in trade_rows if members & set(row["projects_drawing_on_it"])]
    if kind == "money":
        return [{"pool": "capital", "demand": round(sum(row["still_to_pay"] or 0.0 for row in rows), 1),
                 "supply": round(sim.spending_power("start"), 1)}]
    if kind == "hours":
        return [{"pool": "directed hours",
                 "demand_hours_this_year": round(sum(row["founder_hours_left"] or 0.0 for row in rows), 1),
                 "supply_hours_this_year": pool_total}]
    if kind == "supply" and binding:
        return [{"pool": binding, "work_runs_at_share_of_plan": throttle}]
    return []


def bottleneck_groups(sim, rows, trade_rows, pool_total, throttle, binding):
    """One group per blocker kind present among the running projects."""
    groups = []
    for kind in KIND_ORDER:
        members = [row for row in rows if row["blocker_kind"] == kind]
        if not members:
            continue
        pools = _pools(sim, kind, members, trade_rows, pool_total, throttle, binding)
        groups.append({"kind": kind, "count": len(members),
                       "projects": [row["id"] for row in members],
                       "hours_still_to_work": round(sum(row["founder_hours_left"] or 0.0 for row in members), 1),
                       "what_it_means": BLOCKER_MEANING[kind], "pools": pools})
    return groups
