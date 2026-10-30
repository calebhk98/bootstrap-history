"""The rules automation follows when it starts projects as a plain function (Complaint 421)."""

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

