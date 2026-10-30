"""Reasons a multi-year step stops early beyond the warnings it already stops for."""
from sim.refusal import Refusal

from .event_kinds import is_severe_failure


def newly_startable_goal(sim, was_startable):
    """Name of the goal when it just became startable, else None."""
    if sim.view("goal")()["node"] in sim.view("tree_nodes")() and not was_startable and sim.view("goal")()["node"] not in sim.view("techniques_held")() and sim.view("start_check")(sim.view("goal")()["node"], False, None, False)[0]:
        return sim.view("tree_nodes")()[sim.view("goal")()["node"]]["name"]
    return None


def severe_stop_reason(year_events, closed_for_staff, newly_stalled, new_objectives):
    """One sentence on why the player should see this year before more pass, or None."""
    if closed_for_staff:
        return Refusal("staff_closure", "concerns closed for want of staff (%s)" % ", ".join(closed_for_staff[:3]))
    if newly_stalled:
        return Refusal("project_blocked", "a project is blocked (%s)" % ", ".join(newly_stalled[:3]))
    for event in year_events:
        if is_severe_failure(event):
            return Refusal("project_failed", "a project failed: " + str(event["message"])[:80])
    if new_objectives:
        return Refusal("new_objective", "a new objective is within reach (%s)" % ", ".join(new_objectives[:3]))
    return None
