"""The 'compact' reply shape: a short machine summary, separate from full 'json'.

'json' is the whole structured reply; 'compact' is the handful of fields a
turn needs, built from that reply. Builders take the plain reply (and, where
they must look at the tree, the sim) and return a new small dict.
"""
from ..data import closure


def _short(text, limit=160):
    if not isinstance(text, str) or len(text) <= limit:
        return text
    return text[:limit - 3].rstrip() + "..."


def _project_blocker(project):
    """One line for what a running project is waiting on, or None."""
    reason = project.get("why_underfunded") or project.get("waiting_on")
    if project.get("will_be_abandoned_in_years") is not None:
        abandon = "abandoned in %s year(s)" % project["will_be_abandoned_in_years"]
        reason = "%s; %s" % (reason, abandon) if reason else abandon
    return _short(reason)


def _goal_blocker(sim, nodes):
    """The road-to-goal node nearest to startable, with its one-line reason."""
    goal = sim.goal
    if sim.fog or goal not in nodes:
        return None
    road = closure(nodes, goal) - sim.done
    if not road:
        return None
    startable = sorted(node_id for node_id in road if sim.start_reason(node_id)[0])
    if startable:
        return {"id": startable[0], "startable": True}
    nearest = min(sorted(road), key=lambda node_id: len(closure(nodes, node_id) - sim.done))
    return {"id": nearest, "startable": False, "why": _short(sim.start_reason(nearest)[1])}


def compact_state(out, sim=None, nodes=None):
    if not isinstance(out, dict) or not out.get("ok", True):
        return out
    prominence = out.get("prominence") if isinstance(out.get("prominence"), dict) else {}
    stall = out.get("stuck")
    compact = {
        "ok": True,
        "year": out.get("year"),
        "money": out.get("capital"),
        "net_per_year": out.get("net_per_year"),
        "founder_hours_free": out.get("founder_hours_available"),
        "projects": [{"id": node_id, "name": project.get("name"),
                      "blocker": _project_blocker(project)}
                     for node_id, project in sorted((out.get("active") or {}).items())
                     if isinstance(project, dict)],
        "concerns": {"running": out.get("concerns_you_run"),
                     "shut": out.get("you_know_how_to_run_but_have_not_opened")},
        "standing": {"reputation": out.get("reputation"),
                     "eminence": out.get("eminence"),
                     "protection": out.get("protection")},
        "danger": {"prominence": prominence.get("now"),
                   "prominence_dangerous_above": prominence.get("dangerous_above"),
                   "scandal": out.get("scandal_now"),
                   "scandal_dangerous_above": out.get("scandal_danger")},
        "goal": out.get("goal"),
        "goal_reached": out.get("goal_reached"),
        "nearest_goal_blocker": _goal_blocker(sim, nodes) if sim is not None else None,
        "ended": out.get("ended"),
    }
    if isinstance(stall, dict) and stall.get("you_are_stuck"):
        compact["stuck"] = _short(stall["you_are_stuck"])
    if "events" in out:
        compact["completed"] = [row.get("id") for row in out.get("completed") or []]
        compact["lost"] = out.get("lost")
        compact["events"] = [{"year": row.get("year"), "message": _short(row.get("message"))}
                             for row in out.get("events") or []]
    return compact


def _blocked_by(out):
    """Missing prerequisites, then what the other blockers (supply options, power gates) name."""
    ids = list(out.get("missing_prerequisites") or [])
    for blocker in out.get("blockers") or []:
        ids.extend(node_id for node_id in blocker.get("ids") or [] if node_id not in ids)
    return ids


def compact_why(out, sim=None, nodes=None):
    if not isinstance(out, dict) or not out.get("ok", True):
        return out
    status = ("done" if out.get("done") else
              "active" if out.get("active") else
              "startable" if out.get("can_start_now") else "blocked")
    compact = {"ok": True, "id": out.get("id"), "name": out.get("name"),
               "status": status, "blocked": status == "blocked",
               "blocked_by": _blocked_by(out)}
    if out.get("blockers"):
        compact["blocked_kinds"] = list(dict.fromkeys(blocker["kind"] for blocker in out["blockers"]))
    explanation = (out.get("start_blocked_reason") or out.get("waiting_on")
                   or out.get("why_underfunded"))
    if explanation is not None:
        compact["explanation"] = _short(explanation, 300)
    return compact


def compact_stuck(out, sim=None, nodes=None):
    if not isinstance(out, dict) or not out.get("ok", True):
        return out
    reasons = out.get("what_is_holding_you_up")
    if not isinstance(reasons, list):
        return out
    blockers = []
    for reason in reasons:
        if not isinstance(reason, dict):
            continue
        entry = {"reason": reason.get("what")}
        if reason.get("why") is not None:
            entry["explanation"] = _short(reason["why"], 300)
        waiting = reason.get("each_waiting_on")
        if isinstance(waiting, dict):
            entry["projects"] = [{"id": node_id, "explanation": _short(why)}
                                 for node_id, why in sorted(waiting.items())]
        if reason.get("the_nearest_few") is not None:
            entry["nearest"] = reason["the_nearest_few"]
        blockers.append(entry)
    return {"ok": True, "could_begin": out.get("you_could_begin"),
            "could_pay_for": out.get("and_could_pay_for"), "blockers": blockers,
            "cheapest_start": out.get("and_the_cheapest_thing_you_could_start_now")}
