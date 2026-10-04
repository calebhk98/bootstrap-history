"""The step screen's lines for what automation did in the years just played (Complaint 91)."""
from collections import Counter


def automation_lines(rows):
    """One line per policy and action with its count and capital; `automation` has the detail."""
    if not rows:
        return []
    counts, costs = Counter(), Counter()
    for row in rows:
        key = (row.get("policy") or "automatic", row.get("action") or "acted")
        counts[key] += 1
        costs[key] += float(row.get("cost") or 0.0)
    parts = []
    for (policy, action), count in sorted(counts.items()):
        cost = costs[(policy, action)]
        parts.append("%s %s x%d%s" % (policy, action, count, ", %s" % format(cost, ",.0f") if cost else ""))
    return ["AUTOMATION: " + "; ".join(parts) + "  ('automation' lists each)"]
