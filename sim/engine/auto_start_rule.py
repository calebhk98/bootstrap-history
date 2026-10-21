"""The rules automation follows when it starts projects and orders mines, as plain functions (Complaint 421)."""

MINE_CAPITAL_SHARE = 0.25


def judge_start_candidate(non_bountied_active, max_active, can_start, project_cost, room):
    """What the automatic start does with one candidate: "cap" (stop, the active
    cap is reached), "blocked" (cannot start), "too_dear" (costs more than the
    room left to commit) or "start". `can_start()` and `project_cost()` are
    read only when reached."""
    if non_bountied_active >= max_active:
        return "cap"
    if not can_start():
        return "blocked"
    if project_cost() > room:
        return "too_dear"
    return "start"


def size_mine_order(shortfall, active_capacity, pending_capacity, capital, capex_per_unit):
    """(wanted, ordered) mine capacity: the shortfall beyond what is active or
    already sinking, and that capped by a share of capital at the capex per unit."""
    wanted = max(0.0, shortfall - active_capacity - pending_capacity)
    affordable = capital * MINE_CAPITAL_SHARE / max(1.0, capex_per_unit)
    return wanted, min(wanted, affordable)
