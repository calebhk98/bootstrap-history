"""State's list of profitable concerns held shut by a shortage of people."""

import math

# Staffing resources that are not a trade name, mapped to the trade to hire.
_HIRE_AS = {"scholars": "scholar", "craftsmen": "artisan"}
_MOST_LISTED = 5


def shut_for_want_of_staff(sim, nodes):
    """Rows for shut, profitable concerns that are short of scholars, craftsmen
    or a foreman trade, biggest earners first; None when there are none."""
    rows = []
    held_totals = sim.staffing_held_totals()
    for node_id in sorted(sim.done):
        if (not sim.is_venture(node_id) or node_id in sim.operating
                or nodes[node_id]["rev"] <= nodes[node_id]["up"]):
            continue
        missing = sim.staffing_missing_to_open(node_id, held_totals)
        if not missing:
            continue
        fixes = ["hire %s %d" % (_HIRE_AS.get(resource, resource), max(1, math.ceil(amount - 0.005)))
                 for resource, amount in missing.items()]
        rows.append({"id": node_id, "name": nodes[node_id]["name"],
                     "would_earn_a_year": round(nodes[node_id]["rev"] - nodes[node_id]["up"]),
                     "missing": {resource: round(amount, 2) for resource, amount in missing.items()},
                     "fix": "; ".join(fixes)})
    rows.sort(key=lambda row: (-row["would_earn_a_year"], row["id"]))
    return rows or None


def render_shut_for_want_of_staff(rows):
    """Lines for the state screen, one per concern, the rest counted."""
    lines = []
    for row in rows[:_MOST_LISTED]:
        lines.append("  shut for want of people: %s - missing %s (%s den/yr; '%s')"
                     % (row["name"],
                        ", ".join("%.2f %s" % (amount, resource)
                                  for resource, amount in row["missing"].items()),
                        "{:,.0f}".format(row["would_earn_a_year"]), row["fix"]))
    if len(rows) > _MOST_LISTED:
        lines.append("  ... and %d more shut for want of people" % (len(rows) - _MOST_LISTED))
    return lines
