"""The serial floor still ahead of an actor, as opposed to data.critical_path,
which is the floor from scratch.
"""
from .data import closure, hard_pre, topo_order


def remaining_critical_path_years(nodes, goal, done, active_years_left=None):
    """Longest chain of not-yet-finished nodes ending at `goal`, by the same
    per-node time critical_path uses. A finished node contributes nothing; an
    active one contributes its remaining time when `active_years_left`
    (node id to years) has it, else its full floor.
    """
    active_years_left = active_years_left or {}
    order = topo_order(nodes, closure(nodes, goal))
    best = {}
    for node_id in order:
        node = nodes[node_id]
        if node_id in done:
            own = 0.0
        else:
            full = max(node["yrs"], node["ph"] / 2000.0)
            own = min(full, active_years_left.get(node_id, full))
        best[node_id] = own + max(
            (best[prereq_id] for prereq_id in hard_pre(nodes, node_id) if prereq_id in best),
            default=0.0)
    return best[goal]


def active_years_left(nodes, active):
    """Remaining years for each active project, from its banked calendar
    time and remaining founder hours.
    """
    left = {}
    for node_id, project_state in active.items():
        node = nodes.get(node_id)
        if node is None:
            continue
        floor_left = max(0.0, node["yrs"] - project_state.get("yrs", 0.0))
        hours_left = project_state.get("ph_left", node["ph"]) / 2000.0
        left[node_id] = max(floor_left, hours_left)
    return left
