"""One-line summary of what a step completed and failed, shown before the detail."""
from sim.engine.ui_port import FAILED_PREFIX, MINOR_MARK, goal_movement

# Waves at least this long lead with the summary line.
SUMMARY_MIN_ITEMS = 5


def wave_summary(completed, events, goal_before, goal_after):
    """Counts by kind, failures by severity, and how far the goal moved;
    None when nothing was completed or failed."""
    failures = [event for event in events if event["message"].startswith(FAILED_PREFIX)]
    if not completed and not failures:
        return None
    by_kind = {}
    for record in completed:
        kind = record.get("kind") or "technology"
        by_kind[kind] = by_kind.get(kind, 0) + 1
    moved, road_gained = goal_movement(goal_before, goal_after)
    summary = {"completed": len(completed), "by_kind": by_kind,
               "failed": len(failures),
               "minor_failures": sum(MINOR_MARK in event["message"] for event in failures)}
    if moved or road_gained:
        summary["goal"] = {"measures": [{"label": label, "before": old, "after": new}
                                        for label, old, new in moved],
                           "road_steps_gained": road_gained}
    return summary


def summary_line(summary):
    """The rendered headline, or None when the wave is too small to need one."""
    if not summary or summary["completed"] + summary["failed"] < SUMMARY_MIN_ITEMS:
        return None
    kinds = ", ".join("%d %s" % (count, kind) for kind, count in sorted(summary["by_kind"].items()))
    parts = ["%d completed (%s)" % (summary["completed"], kinds or "none")]
    if summary["failed"]:
        minor = summary["minor_failures"]
        parts.append("%d failed%s" % (summary["failed"], " (%d minor)" % minor if minor else ""))
    goal = summary.get("goal")
    if goal:
        moves = ["%s %s -> %s" % (row["label"], row["before"], row["after"]) for row in goal["measures"]]
        if goal["road_steps_gained"]:
            moves.append("%+d steps on the road" % goal["road_steps_gained"])
        parts.append("goal: " + "; ".join(moves))
    return "  SUMMARY: " + ". ".join(parts) + "."
