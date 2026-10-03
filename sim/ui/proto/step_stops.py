"""Reasons a multi-year step stops early beyond the warnings it already stops for."""
from sim.engine.ui_port import FAILED_PREFIX, MINOR_MARK


def newly_startable_goal(sim, was_startable):
    """Name of the goal when it just became startable, else None."""
    if sim.goal in sim.nodes and not was_startable and sim.goal not in sim.done and sim.can_start(sim.goal):
        return sim.nodes[sim.goal]["name"]
    return None


def severe_stop_reason(year_events, closed_for_staff, newly_stalled, new_objectives):
    """One sentence on why the player should see this year before more pass, or None."""
    if closed_for_staff:
        return "concerns closed for want of staff (%s)" % ", ".join(closed_for_staff[:3])
    if newly_stalled:
        return "a project is blocked (%s)" % ", ".join(newly_stalled[:3])
    for event in year_events:
        message = event["message"]
        if message.startswith(FAILED_PREFIX) and MINOR_MARK not in message:
            return "a project failed: " + message[:80]
    if new_objectives:
        return "a new objective is within reach (%s)" % ", ".join(new_objectives[:3])
    return None
