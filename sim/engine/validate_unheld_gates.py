"""Validation rule: a recipe gate nobody starts with says why.

The frontier is every node a production entry requires that no civilisation
holds at the start while its own prerequisites are held. Each such node
states `unheld_reason` beside itself in the tree data."""
from typing import Any, List, Mapping

MINIMUM_REASON_LENGTH = 20


def frontier_gates(nodes: Mapping[str, Mapping[str, Any]], civilisations: Mapping[str, Mapping[str, Any]],
                   production: Mapping[str, Any]) -> List[str]:
    held = set()
    for civilisation in civilisations.values():
        held |= set(civilisation["starting_techs"])
    gates = {entry["requires_node"] for entry in production.values() if entry.get("requires_node")}
    return sorted(gate for gate in gates - held
                  if gate in nodes and all(prerequisite in held for prerequisite in nodes[gate].get("pre") or ()))


def check_unheld_gates(nodes: Mapping[str, Mapping[str, Any]], civilisations: Mapping[str, Mapping[str, Any]],
                       production: Mapping[str, Any]) -> List[str]:
    return ["%s: a recipe gate no civilisation starts with, whose prerequisites are held; hold it in a "
            "civilisation or give the node unheld_reason" % gate
            for gate in frontier_gates(nodes, civilisations, production)
            if len(nodes[gate].get("unheld_reason") or "") < MINIMUM_REASON_LENGTH]
