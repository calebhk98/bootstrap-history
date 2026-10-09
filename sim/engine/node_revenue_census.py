"""How many nodes earn a figure typed into the tree, and how many earn from what they make.

Counts over nodes that carry a revenue figure, by `_revenue_basis`: `output` (derived from the
production entries the node runs), `knowledge` (a science that makes nothing) and `authored` (a typed
figure; the node names no product). Printed by `simulator.py validate`."""
from collections import Counter
from typing import List, Mapping

BASES = ("output", "knowledge", "authored")


def basis_counts(nodes: Mapping[str, dict]) -> Counter:
    counts = Counter({basis: 0 for basis in BASES})
    for node in nodes.values():
        if node.get("_rev_hours_authored", 0.0) > 0.0:
            counts[node.get("_revenue_basis")] += 1
    return counts


def format_lines(counts: Counter) -> List[str]:
    total = sum(counts.values())
    return ["  %-10s %5d  (%s of nodes with a revenue figure)"
            % (basis, counts[basis], "%.0f%%" % (100.0 * counts[basis] / total) if total else "n/a")
            for basis in BASES]
