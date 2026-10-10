"""A standing development programme: each year before time passes it starts what its target allows."""

from sim.engine.ui_port import money_text, plain_number
from sim.ui.memory import remembered
from .dispatch_ventures import _cmd_rush
from .programme_draw import remember_starts, standing_draw
from .programme_pause import tripped
from .pursue import CAP_KEYS, route_order, rush_command

TOPIC = "programme"
ANNUAL_HOURS_KEY = "max_annual_hours"
SKIPPED_SHOWN = 8


def state(sim):
    return remembered(sim, TOPIC)


def is_set(sim):
    return bool(state(sim).get("target"))


def target_text(sim, target):
    if target["kind"] == "goal":
        return "goal %s" % sim.nodes.get(target["value"], {}).get("name", target["value"])
    return "category %s" % target["value"]


def pause_reason(sim, programme):
    """Why the programme must not act this year, or None. Updates the pause when a set condition holds or clears."""
    pauses = programme.get("pauses", {})
    condition = tripped(sim, pauses)
    if programme.get("paused"):
        held = programme.get("paused_by")
        if not held:
            return "paused by the player"
        if condition is None and programme.get("auto_resume"):
            programme["paused"], programme["paused_by"] = False, None
        else:
            return "paused: %s%s" % (condition or held, "" if programme.get("auto_resume")
                                     else " (stays paused until you resume)")
    if condition:
        programme["paused"], programme["paused_by"] = True, condition
        return "paused: %s%s" % (condition, "" if programme.get("auto_resume") else " (stays paused until you resume)")
    if sim.capital < 0 and "pause_debt" not in pauses:
        return "in debt (capital below zero)"
    floor = programme.get("caps", {}).get("reserve_cash")
    if floor is not None and sim.capital < floor:
        return "cash is below the reserve floor"
    if floor is not None and sim.capital - standing_draw(sim, programme) < floor:
        return "cash after this year's standing draw would fall below the reserve floor"
    return None


def hours_started_this_year(sim, programme):
    year, hours = programme.get("hours_year", [None, 0.0])
    return hours if year == sim.year else 0.0


def _hours_room(sim, programme):
    """(founder hours the programme may still commit this year or None, why not when none is left)."""
    caps = programme.get("caps", {})
    room = None
    if caps.get("max_total_hours") is not None:
        room = caps["max_total_hours"] - programme.get("hours", 0.0)
        if room <= 1e-9:
            return room, "founder hour cap reached (total)"
    if caps.get(ANNUAL_HOURS_KEY) is not None:
        yearly = caps[ANNUAL_HOURS_KEY] - hours_started_this_year(sim, programme)
        if yearly <= 1e-9:
            return yearly, "founder hour cap reached (this year)"
        room = yearly if room is None else min(room, yearly)
    return room, None


def _year_rush(sim, programme):
    """(rush command, why not) for this year's start under the programme's caps."""
    caps = dict(programme.get("caps", {}))
    caps.pop(ANNUAL_HOURS_KEY, None)
    hours_room, hours_why = _hours_room(sim, programme)
    if hours_why:
        return None, hours_why
    if hours_room is not None:
        caps["max_total_hours"] = hours_room
    total = caps.get("max_total_cost")
    if total is not None:
        left = total - programme.get("committed", 0.0)
        if left <= 1e-9:
            return None, "total cap reached"
        caps["max_total_cost"] = left
    if caps.get("max_annual_draw") is not None:
        room = caps["max_annual_draw"] - standing_draw(sim, programme)
        if room <= 1e-9:
            return None, "annual draw cap used up by projects it already started"
        caps["max_annual_draw"] = room
    target = programme["target"]
    if target["kind"] == "goal":
        if target["value"] in sim.done:
            return None, "goal reached"
        ids = route_order(sim, target["value"])
        if not ids:
            return None, "nothing on the route is startable this year"
        return rush_command(ids, caps=caps, limit=programme.get("limit")), None
    return rush_command(category=target["value"], caps=caps, limit=programme.get("limit")), None


def programme_before_year(sim, nodes):
    """Rows (zero or one) saying what the programme did this year; called once before each year's step."""
    programme = state(sim)
    if not programme.get("target"):
        return []
    row = {"year": sim.year, "what": "programme for " + target_text(sim, programme["target"]),
           "started": [], "skipped": [], "spent": 0.0}
    reason = pause_reason(sim, programme)
    command, reason = (None, reason) if reason else _year_rush(sim, programme)
    if command is None:
        row["did_nothing_because"] = reason
        return [row]
    result = _cmd_rush(sim, nodes, command, None)
    if not result.get("ok"):
        row["did_nothing_because"] = result.get("error", "refused")
        return [row]
    row["started"] = [{"id": item["id"], "name": item["name"], "cost": item["cost"]}
                      for item in result["started"]]
    row["spent"] = result["total_cost"]
    row["skipped"] = [{"id": item["id"], "why": item["why"]} for item in result["not_started"][:SKIPPED_SHOWN]]
    row["skipped_count"] = result["count_not_started"]
    remember_starts(programme, result["started"])
    programme["committed"] = programme.get("committed", 0.0) + result["total_cost"]
    row["hours"] = result["total_founder_hours"]
    programme["hours"] = programme.get("hours", 0.0) + row["hours"]
    programme["hours_year"] = [sim.year, hours_started_this_year(sim, programme) + row["hours"]]
    if not row["started"]:
        row["did_nothing_because"] = "nothing fit the caps or exclusions"
    return [row]


def caps_text(programme, sim):
    """The caps as written, money caps in the player's chosen money unit and hour caps as hours."""
    hour_keys = (ANNUAL_HOURS_KEY, "max_total_hours")
    parts = ["%s %s" % (key, plain_number(programme["caps"][key]) if key in hour_keys
                        else money_text(programme["caps"][key], sim, grouped=True, short=True))
             for key in CAP_KEYS + (ANNUAL_HOURS_KEY,) if programme.get("caps", {}).get(key) is not None]
    if programme.get("limit") is not None:
        parts.append("limit %d per year" % programme["limit"])
    return ", ".join(parts) or "no caps"
