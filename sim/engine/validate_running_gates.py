"""Validation rule: what a node requires running must be a work that can run.

`running` equals `done` for anything that is not a venture, so a running requirement on such a
node would never bind. A requirement chain that loops could never be met. `requires_ways` lengths
must be positive numbers."""
from typing import Any, List, Mapping

RUNNING_FIELDS = ("up", "rev", "up_hours", "rev_hours")


def _can_run(node: Mapping[str, Any]) -> bool:
    return any((node.get(field) or 0) > 0 for field in RUNNING_FIELDS)


def _cycle_from(nodes: Mapping[str, Mapping[str, Any]], start: str) -> List[str]:
    path: List[str] = []

    def walk(node_id: str) -> List[str]:
        if node_id in path:
            return path[path.index(node_id):] + [node_id]
        path.append(node_id)
        for needed in (nodes.get(node_id) or {}).get("requires_running") or ():
            found = walk(needed)
            if found:
                return found
        path.pop()
        return []
    return walk(start)


def check_running_gates(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    errors = []
    for node_id in sorted(nodes):
        for needed in nodes[node_id].get("requires_running") or ():
            if needed not in nodes:
                errors.append("%s: requires_running names %s, which is not a node" % (node_id, needed))
            elif not _can_run(nodes[needed]):
                errors.append("%s: requires_running names %s, which has no upkeep or revenue so is never "
                              "'running' apart from being built" % (node_id, needed))
    for node_id in sorted(nodes):
        for way, km in (nodes[node_id].get("requires_ways") or {}).items():
            if not isinstance(km, (int, float)) or km <= 0:
                errors.append("%s: requires_ways %s needs a positive number of kilometres, not %r" % (node_id, way, km))
    reported = set()
    for node_id in sorted(nodes):
        loop = _cycle_from(nodes, node_id) if nodes[node_id].get("requires_running") else []
        if loop and frozenset(loop) not in reported:
            reported.add(frozenset(loop))
            errors.append("requires_running cycle: %s" % " -> ".join(loop))
    return errors
