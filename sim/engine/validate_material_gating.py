"""Validation rule: a gated material is only used by nodes that can make it.

data/material_gating.json names materials no ancient process makes. A node
that consumes one needs a listed producer node somewhere in its own ancestry,
following both `pre` and `req_any` options, unless it is declared exempt in
the data with a reason."""
import json
import os
from typing import Any, Dict, List, Mapping, Set

MINIMUM_REASON_LENGTH = 20


def load_gating(root: str) -> Dict[str, Any]:
    with open(os.path.join(root, "data", "material_gating.json")) as handle:
        return json.load(handle)["materials"]


def ancestors(node_id: str, nodes: Mapping[str, Mapping[str, Any]]) -> Set[str]:
    seen: Set[str] = set()
    stack = [node_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        node = nodes.get(current)
        if not node:
            continue
        stack.extend(prereq for prereq in node.get("pre") or [] if prereq in nodes)
        for group in node.get("req_any") or []:
            stack.extend(option for option in group.get("options") or {} if option in nodes)
    seen.discard(node_id)
    return seen


def check_material_gating(nodes: Mapping[str, Mapping[str, Any]], gating: Mapping[str, Any]) -> List[str]:
    errors = []
    for material, rule in sorted(gating.items()):
        producers = set(rule["producer_nodes"])
        for node_id in sorted(producers - set(nodes)):
            errors.append("material_gating %s: producer node %s is not in the tree" % (material, node_id))
        exempt = rule.get("ungated_consumers") or {}
        for node_id, reason in exempt.items():
            if len(reason) < MINIMUM_REASON_LENGTH:
                errors.append("material_gating %s: exemption for %s needs a reason" % (material, node_id))
        restricted = rule.get("only_consumers")
        for node_id, node in nodes.items():
            if not (node.get("mat") or {}).get(material):
                continue
            if node_id in exempt or (restricted is not None and node_id not in restricted):
                continue
            if not producers & ancestors(node_id, nodes):
                errors.append("%s consumes %s but has no producer (%s) in its ancestry; add one or declare an "
                              "exemption with a reason in data/material_gating.json"
                              % (node_id, material, ", ".join(sorted(producers))))
        for node_id in restricted or ():
            if node_id not in nodes:
                errors.append("material_gating %s: consumer %s is not in the tree" % (material, node_id))
    return errors
