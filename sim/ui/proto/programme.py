"""A standing development programme: each year before time passes it starts what its target allows."""

from sim.ui.memory import remembered
from .dispatch_ventures import _cmd_rush
from .programme_draw import remember_starts, standing_draw
from .pursue import CAP_KEYS, route_order, rush_command

TOPIC = "programme"
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
    """Why the programme must not act this year, or None."""
    if programme.get("paused"):
        return "paused by the player"
    if sim.capital < 0:
        return "in debt (capital below zero)"
    floor = programme.get("caps", {}).get("reserve_cash")
    if floor is not None and sim.capital < floor:
        return "cash is below the reserve floor"
    if floor is not None and sim.capital - standing_draw(sim, programme) < floor:
        return "cash after this year's standing draw would fall below the reserve floor"
    return None


def _year_rush(sim, programme):
    """(rush command, why not) for this year's start under the programme's caps."""
    caps = dict(programme.get("caps", {}))
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
    if not row["started"]:
        row["did_nothing_because"] = "nothing fit the caps or exclusions"
    return [row]


def caps_text(programme):
    parts = ["%s %s" % (key, "{:,.0f}".format(programme["caps"][key])) for key in CAP_KEYS
             if programme.get("caps", {}).get(key) is not None]
    if programme.get("limit") is not None:
        parts.append("limit %d per year" % programme["limit"])
    return ", ".join(parts) or "no caps"
