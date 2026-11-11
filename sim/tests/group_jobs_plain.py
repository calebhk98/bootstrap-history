"""The technique-displacement search as it was before the category shares were kept between calls, kept as plain reference code."""
from typing import Any, Dict, List, Optional


def displacing_technique_by_scanning(trade: str, running: Dict[str, int], nodes: Dict[str, Dict[str, Any]]) -> Optional[str]:
    def share(node: Dict[str, Any]) -> Optional[float]:
        hours = node.get("lab") or {}
        total = sum(hours.values())
        return hours.get(trade, 0.0) / total if total > 0.0 else None

    by_category: Dict[Any, List[float]] = {}
    for node in nodes.values():
        node_share = share(node)
        if node_share is not None:
            by_category.setdefault(node.get("cat"), []).append(node_share)
    candidates = []
    for node_id in sorted(running):
        node = nodes.get(node_id) or {}
        node_share = share(node)
        shares = by_category.get(node.get("cat"), [])
        if node_share is None or not shares:
            continue
        mean_share = sum(shares) / len(shares)
        if mean_share > 0.0 and node_share < mean_share:
            candidates.append((running[node_id], mean_share - node_share, node_id))
    return max(candidates)[2] if candidates else None
