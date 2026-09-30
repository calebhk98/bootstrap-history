"""The priority command: which active projects get an actor's hours first."""

from .command_registry import command


def _ranked_active(sim):
    """Active projects in the order the hours allocator serves them:
    standing `allocate` orders first, then the master order."""
    rank = {node_id: place for place, node_id in enumerate(sim.order)}
    return sorted(sim.active, key=lambda node_id: (
        0 if sim.hour_allocations.get(node_id, 0.0) > 0 else 1,
        rank.get(node_id, len(rank)), node_id))


def move_in_priority(sim, node_id, position):
    """Place an active project at a 1-based rank among the active ones.

    Only the master-order slots active projects already hold are reshuffled,
    so inactive nodes keep their place. Returns the new ranking.
    """
    rank = {other: place for place, other in enumerate(sim.order)}
    others = sorted((other for other in sim.active if other != node_id),
                    key=lambda other: (rank.get(other, len(rank)), other))
    index = max(0, min(len(others), position - 1))
    sequence = others[:index] + [node_id] + others[index:]
    slots = [place for place, other in enumerate(sim.order) if other in sim.active]
    missing = [other for other in sequence if other not in sim.order]
    sim.order.extend(missing)
    slots += list(range(len(sim.order) - len(missing), len(sim.order)))
    for slot, other in zip(sorted(slots), sequence):
        sim.order[slot] = other
    return _ranked_active(sim)


@command("priority", group="projects", aliases=("prioritise", "prioritize"),
         summary="choose which active projects get your hours first",
         usage=["priority", "priority <id> first", "priority <id> last",
                "priority <id> <rank>"],
         options={"<id>": "an active project",
                  "first|last|<rank>": "where it goes among active projects; 1 is served first"},
         description="Hours nobody directs are shared out in this order, so under a "
                     "short pool the first project is filled before the next. A project "
                     "with an 'allocate' order is served ahead of all of them. Bare "
                     "priority lists the order.")
def _cmd_priority(sim, nodes, cmd, ended):
    target_id = cmd.get("id")
    if target_id is not None:
        if target_id not in nodes:
            return {"ok": False, "error": "unknown node id %r. 'portfolio' lists what is active" % target_id}
        if target_id not in sim.active:
            return {"ok": False, "error": "%s is not active, so it has no place in the queue. "
                                          "'start' it first" % target_id}
        position = cmd.get("position", "first")
        count = len(sim.active)
        if position == "first":
            position = 1
        elif position == "last":
            position = count
        elif isinstance(position, bool) or not isinstance(position, (int, float)) or position < 1:
            return {"ok": False, "error": "say first, last, or a rank from 1 to %d" % count}
        move_in_priority(sim, target_id, int(position))
    ranking = _ranked_active(sim)
    projects = []
    for place, node_id in enumerate(ranking, 1):
        row = {"rank": place, "id": node_id, "name": nodes[node_id]["name"]}
        if sim.hour_allocations.get(node_id, 0.0) > 0:
            row["allocate_hours_a_year"] = sim.hour_allocations[node_id]
        projects.append(row)
    out = {"ok": True, "order": ranking, "projects": projects or "none"}
    if target_id is not None:
        out["set"] = target_id
    out["note"] = ("hours are served in this order; a project with an 'allocate' "
                   "order is served ahead of the rest whatever its rank. "
                   "'priority <id> first|last|<rank>' moves one.")
    return out
