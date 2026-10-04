"""Extra `stuck` advice (Complaints/98): calendar-bound goal path, filler start, live lever figures."""

from sim.engine.ui_port import closure

from .guidance import delay_kinds, leverage_points
from .saving_plan import saving_plan

SHOWN_LEVERS = ("literacy", "labour", "finance", "institutions", "knowledge")
SIDE_WORK = ("coverage: broaden what you can build ('available' lists what could begin; "
             "every item widens the base the goal rests on)",
             "institutions: schools, guilds and standing concerns ('ventures', 'train')",
             "leverage: raise literacy, labour, finance or materials ('leverage' shows the figures)")


def lever_line(sim):
    """One line of live figures for the levers that side work moves."""
    parts = []
    for point in leverage_points(sim):
        if point["lever"] in SHOWN_LEVERS:
            parts.append("%s: %s" % (point["lever"], ", ".join(
                "%s %s" % (name.replace("_", " "), value) for name, value in point["figures"].items()
                if value is not None)))
    return "; ".join(parts)


def calendar_bound_advice(sim, nodes):
    """Say so when nothing on the goal path can be sped up, and suggest side work.

    Under fog the route is hidden, so this reports counts over all running work and names nothing.
    """
    kinds = delay_kinds(sim, nodes)
    running = sum(len(ids) for ids in kinds.values())
    if not running:
        return None
    if sim.fog:
        if len(kinds.get("calendar", ())) != running:
            return None
        return {"every_goal_project_calendar_bound": None,
                "text": ("fog of war hides which running projects are on the route to your goal, so this "
                         "counts all of them: all %d running are only waiting on their calendar floor, "
                         "which nothing you pay can shorten." % running),
                "side_work": list(SIDE_WORK), "lever_figures": lever_line(sim)}
    if sim.goal not in nodes:
        return None
    road = closure(nodes, sim.goal) - sim.done
    on_road = {node_id for ids in kinds.values() for node_id in ids} & road
    if not on_road or any(node_id not in kinds.get("calendar", ()) for node_id in on_road):
        return None
    if any(node_id not in sim.active and sim.start_reason(node_id)[0] for node_id in road):
        return None
    return {"every_goal_project_calendar_bound": True,
            "text": ("every project on the road to your goal (%d running) is only waiting on its calendar "
                     "floor: nothing you pay or allocate speeds it up. Use the wait for side work."
                     % len(on_road)),
            "side_work": list(SIDE_WORK), "lever_figures": lever_line(sim)}


def filler_note(sim, cheapest_id, nodes):
    """Tell the player when the suggested start is off the goal's route, and name a savings target.

    Silent under fog (the route is hidden) and for a start that is on the remaining route.
    """
    if cheapest_id is None or sim.fog or sim.goal not in nodes:
        return None
    if cheapest_id in closure(nodes, sim.goal) - sim.done:
        return None
    note = ("%s is only the cheapest startable thing, not a step toward your goal: filler unless you "
            "want it for its own sake." % cheapest_id)
    plan = saving_plan(sim)
    if plan:
        note += " Your saving target for %s is set ('saving' shows it)." % plan["id"]
    return note
