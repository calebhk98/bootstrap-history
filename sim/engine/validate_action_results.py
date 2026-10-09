"""Validation rule: an action's declared results are of a known kind, and what a lane asks for can be returned.

`returns` on a node is {kind: [ids]} with kind one of knowledge, route, partner. Knowledge names a
node. A `route:` or `partner:` token in a mode's or lane's `requires_nodes` must be returned by some node."""
from typing import Any, Iterable, List, Mapping

from . import action_results


def check_action_results(nodes: Mapping[str, Mapping[str, Any]], gated_entries: Iterable[Mapping[str, Any]]) -> List[str]:
    problems = []
    returned = set()
    for node_id in sorted(nodes):
        returns = nodes[node_id].get("returns")
        if not returns:
            continue
        for kind, idents in sorted(returns.items()):
            if kind not in action_results.RESULT_KINDS:
                problems.append("%s: returns kind %r is not one of %s" % (node_id, kind, ", ".join(action_results.RESULT_KINDS)))
                continue
            for ident in idents:
                if kind == action_results.KNOWLEDGE and ident not in nodes:
                    problems.append("%s: returns knowledge %s, which is not a node" % (node_id, ident))
        returned |= action_results.returned_by(nodes[node_id])
    for entry in gated_entries:
        for needed in entry.get("requires_nodes") or ():
            is_token = needed.split(":", 1)[0] in ("route", "partner") and ":" in needed
            if is_token and needed not in returned:
                problems.append("%s: requires_nodes asks for %s, which no node returns" % (entry.get("id"), needed))
    return problems


def check_risks(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    """A node's `risks` names crew, hull or cargo, each a share above nothing and at most everything."""
    problems = []
    for node_id in sorted(nodes):
        for kind, shares in sorted((nodes[node_id].get("risks") or {}).items()):
            if kind not in ("crew", "hull", "cargo"):
                problems.append("%s: risks kind %r is not crew, hull or cargo" % (node_id, kind))
                continue
            for name, share in sorted(shares.items()):
                if not isinstance(share, (int, float)) or not 0.0 < share <= 1.0:
                    problems.append("%s: risks %s %s needs a share above nothing and at most one, not %r"
                                    % (node_id, kind, name, share))
    return problems
