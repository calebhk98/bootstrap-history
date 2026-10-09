"""What a completed action returns besides living stock: knowledge, a route, a trading partner.

A node's `returns` is {kind: [ids]}. A result stands while the action that returned it is held and
running (sim/engine/held_works.py). Knowledge is the named node, held as if it were done; a route or a
partner is the token `kind:id`, which a carriage mode, a sea lane or a partner asks for in
`requires_nodes` in place of a node. Nothing here names a content id.
"""
from typing import AbstractSet, Iterable, Mapping, Set

RESULT_KINDS = ("knowledge", "route", "partner")
KNOWLEDGE = "knowledge"


def token(kind: str, ident: str) -> str:
    """How a result is named among held nodes: knowledge is the node itself, others `kind:id`."""
    return ident if kind == KNOWLEDGE else "%s:%s" % (kind, ident)


def returned_by(node: Mapping) -> Set[str]:
    """The tokens one node returns."""
    returns = node.get("returns") or {}
    return {token(kind, ident) for kind in RESULT_KINDS for ident in returns.get(kind) or ()}


def results_of(nodes: Mapping[str, Mapping], held: Iterable[str]) -> Set[str]:
    """The tokens returned by the held nodes that declare a result."""
    found: Set[str] = set()
    for node_id in held:
        node = nodes.get(node_id)
        if node is not None and node.get("returns"):
            found |= returned_by(node)
    return found


def partner_ids(nodes: Mapping[str, Mapping]) -> Set[str]:
    """Every trading partner some node returns."""
    return {ident for node in nodes.values() for ident in (node.get("returns") or {}).get("partner") or ()}


def expand(nodes: Mapping[str, Mapping], held: AbstractSet[str]) -> frozenset:
    """`held` with the results its nodes return."""
    return frozenset(held) | results_of(nodes, held)
