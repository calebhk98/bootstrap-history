"""Filters a player puts on a bulk start: by subject, per-project cost and founder hours."""


def parse_rush_filters(cmd, nodes):
    """The filters given on a rush as (filters, error). Absent ones are left out."""
    filters = {}
    raw_ids = cmd.get("ids")
    if raw_ids not in (None, ""):
        listed = raw_ids if isinstance(raw_ids, (list, tuple)) else str(raw_ids).replace(" ", ",").split(",")
        wanted = [node_id.strip() for node_id in listed if str(node_id).strip()]
        unknown = [node_id for node_id in wanted if node_id not in nodes]
        if unknown:
            return None, "unknown node id(s) in ids: %s" % ", ".join(unknown)
        filters["ids"] = wanted
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
    if "ids" in filters and node_id not in filters["ids"]:
        return False
    if "category" in filters and str(node.get("cat", "")).lower() != filters["category"]:
        return False
    if "max_hours" in filters and node["ph"] > filters["max_hours"] + 1e-9:
        return False
    if "max_cost" in filters and sim.project_cost(node_id) > filters["max_cost"] + 1e-9:
        return False
    return True


def rush_exposure(sim, nodes, started):
    """Founder-hours and failure exposure of what a rush began, and the trades it oversubscribes."""
    bottlenecks = [{"trade": trade, "demand_hours_this_year": row["demand_hours_this_year"],
                    "supply_hours_this_year": row["supply_hours_this_year"]}
                   for trade, row in sim.trade_demand_vs_supply().items() if row["oversubscribed"]]
    risks = [nodes[row["id"]].get("risk", 0.0) or 0.0 for row in started]
    return bottlenecks, {"expected_failures": round(sum(risks), 3),
                         "riskiest": max(started, key=lambda row: nodes[row["id"]].get("risk", 0.0) or 0.0)["id"]
                         if started else None}
