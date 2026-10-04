"""`portfolio` at scale: per-project readouts, severity paging and group drill-down (Complaints/88)."""

import math

from .portfolio_bottlenecks import KIND_ORDER

DEFAULT_ROWS = 8
CONSTRAINTS = ("staffing", "trade_hours", "materials", "money", "founder_hours", "calendar", "unclear")


def add_readouts(sim, nodes, rows):
    """The four per-project readouts, each computed from the row and the node, never a second ledger.

    Absorption is the money still to pay spread over the project's own years, as `rush` sizes a
    draw; the completion estimate is the slowest of the calendar, the hours and the money.
    """
    for row in rows:
        node = nodes[row["id"]]
        left = row.get("still_to_pay") or 0.0
        draw = left / max(1.0, float(node["yrs"]))
        effective = row.get("hours_effective_this_year") or 0.0
        hours_left = row.get("founder_hours_left") or 0.0
        years = [row["calendar_years_left"], left / draw if draw > 0 else 0.0]
        if hours_left > 0:
            years.append(hours_left / effective if effective > 0 else math.inf)
        slowest = max(years)
        row["remaining_investment"] = round(left, 1)
        row["annual_absorption"] = round(draw, 1)
        row["years_to_finish_at_last_allocation"] = None if math.isinf(slowest) else round(slowest, 1)
        row["earliest_completion_year"] = None if math.isinf(slowest) else int(sim.year + math.ceil(slowest))
    return rows


def _severity(row):
    kind = row["blocker_kind"]
    return (KIND_ORDER.index(kind) if kind in KIND_ORDER else len(KIND_ORDER),
            row.get("pool_rank_this_year") or 10 ** 6, row["id"])


def group_members(rows, trade_rows, word):
    """Rows behind one named group (a blocker kind, a constraint, or a trade), or None if unknown."""
    if word in KIND_ORDER:
        return [row for row in rows if row["blocker_kind"] == word]
    if word in CONSTRAINTS:
        return [row for row in rows if row["constraint"] == word]
    for trade_row in trade_rows:
        if trade_row["trade"].lower() == word:
            drawing = set(trade_row["projects_drawing_on_it"])
            return [row for row in rows if row["id"] in drawing]
    return None


def group_names(trade_rows):
    return list(KIND_ORDER) + sorted(trade_row["trade"] for trade_row in trade_rows)


def page_rows(rows, trade_rows, cmd):
    """(shown rows, paging dict, error or None) for the arguments the command carried."""
    cmd = cmd or {}
    group = cmd.get("group")
    pool = rows
    if group:
        pool = group_members(rows, trade_rows, group)
        if pool is None:
            return [], {}, ("no portfolio group %r. Try one of: %s" % (group, ", ".join(group_names(trade_rows))))
    pool = sorted(pool, key=_severity)
    offset = max(0, int(cmd.get("offset") or 0))
    limit = len(pool) if cmd.get("all") else max(1, int(cmd.get("limit") or DEFAULT_ROWS))
    shown = pool[offset:offset + limit]
    more = len(pool) - offset - len(shown)
    prefix = "portfolio %s " % group if group else "portfolio "
    paging = {"group": group, "total": len(pool), "shown": len(shown), "offset": offset,
              "more": max(0, more), "all_command": prefix + "all",
              "next_command": prefix + "offset:%d" % (offset + len(shown)) if more > 0 else None}
    return shown, paging, None
