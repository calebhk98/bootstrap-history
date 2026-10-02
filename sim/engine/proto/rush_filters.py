"""Filters a player puts on a bulk start: by subject, per-project cost and founder hours."""


def parse_rush_filters(cmd):
    """The filters given on a rush as (filters, error). Absent ones are left out."""
    filters = {}
    category = cmd.get("category", cmd.get("filter"))
    if category not in (None, ""):
        filters["category"] = str(category).strip().lower()
    for key in ("max_cost", "max_hours"):
        raw = cmd.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None, "%s must be a number" % key
        if value < 0 or value != value:
            return None, "%s cannot be negative" % key
        filters[key] = value
    return filters, None


def passes_rush_filters(sim, nodes, node_id, filters):
    """True when the project fits every filter the player gave."""
    node = nodes[node_id]
    if "category" in filters and str(node.get("cat", "")).lower() != filters["category"]:
        return False
    if "max_hours" in filters and node["ph"] > filters["max_hours"] + 1e-9:
        return False
    if "max_cost" in filters and sim.project_cost(node_id) > filters["max_cost"] + 1e-9:
        return False
    return True
