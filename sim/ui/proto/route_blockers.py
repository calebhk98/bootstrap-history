"""The nodes of an unstartable goal route nearest to being startable, shared by the stuck and path commands."""

from sim.engine.ui_port import closure


def route_blockers(sim, nodes, road, count):
    """The nodes of an unstartable route nearest to being startable, each
    with the reason start_reason gives; shared by `stuck` and `path`.
    """
    held = sim.view("techniques_held")()
    near = sorted(road, key=lambda node_id: (len(closure(nodes, node_id) - held), node_id))
    rows = []
    for node_id in near[:count]:
        blockers = sim.view("start_blockers")(node_id)
        rows.append({"id": node_id, "why": blockers[0]["text"] if blockers else sim.view("start_check")(node_id)[1],
                     "kind": blockers[0]["kind"] if blockers else None,
                     "kinds": list(dict.fromkeys(blocker["kind"] for blocker in blockers))})
    return rows
