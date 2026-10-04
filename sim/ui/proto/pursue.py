"""Pursue a goal: begin what is startable on its route, through the rush machinery and its guards."""

from sim.engine.ui_port import closure, hard_pre, topo_order
from .nodes import _resolve_by_name

FOG_REFUSAL = ("route planning is switched off under fog of war: nobody can lay out a road to somewhere "
               "they have not been. Use 'available' to see what you could begin now.")
ORDER_TEXT = "longest remaining chain to the goal first (critical path), cheaper first on ties"
CAP_KEYS = ("max_total_cost", "max_annual_draw", "reserve_cash")


def resolve_goal(sim, raw):
    """(goal id, error). No word means the current goal; a name resolves when it is unique."""
    nodes = sim.nodes
    if raw in (None, ""):
        return (sim.goal, None) if sim.goal in nodes else (None, "there is no current goal; name one")
    text = str(raw).strip()
    if text in nodes:
        return text, None
    candidates = _resolve_by_name(text)
    if len(candidates) == 1:
        return candidates[0], None
    return None, ("more than one thing is called %r; say which by id" % text if candidates
                  else "unknown node id %r" % text)


def route_order(sim, goal):
    """Startable, unfinished route members: longest remaining chain first, cheaper first on ties."""
    nodes = sim.nodes
    route = closure(nodes, goal)
    tail = {}
    for node_id in reversed(topo_order(nodes, route)):
        tail[node_id] = tail.get(node_id, 0.0) + nodes[node_id]["yrs"]
        for before in hard_pre(nodes, node_id):
            if before in route:
                tail[before] = max(tail.get(before, 0.0), tail[node_id])
    memo = {}
    startable = [node_id for node_id in route
                 if node_id not in sim.done and node_id not in sim.active
                 and sim.can_start(node_id, _memo=memo)]
    return sorted(startable, key=lambda node_id: (-tail.get(node_id, 0.0), sim.project_cost(node_id), node_id))


def rush_command(ids=None, category=None, caps=None, limit=None, preview=False):
    """The rush a pursuit makes: only the given ids (or category), in the order given."""
    command = {"cmd": "rush", "preview": bool(preview)}
    if ids is not None:
        command.update(ids=list(ids), in_given_order=True)
    if category:
        command["category"] = category
    for key, value in (caps or {}).items():
        if value is not None:
            command[key] = value
    if limit is not None:
        command["limit"] = limit
    return command
