"""How many nodes earn a figure typed into the tree, and how many earn from what they make.

Counts over nodes that carry a revenue, by `_revenue_basis`: `output` (derived from the production
entries the node runs), `knowledge` (a science that makes nothing) and `authored` (a typed figure; the node
names no product). Upkeep and capital are counted by their own basis the same way. Printed by
`simulator.py validate`, with the branch files that still hold typed figures."""
from collections import Counter
from typing import Dict, List, Mapping

BASES = ("output", "knowledge", "authored")
COST_BASES = ("derived", "default", "authored")


def basis_counts(nodes: Mapping[str, dict]) -> Counter:
    counts = Counter({basis: 0 for basis in BASES})
    for node in nodes.values():
        if node.get("_revenue_basis") in BASES:
            counts[node["_revenue_basis"]] += 1
    return counts


def cost_basis_counts(nodes: Mapping[str, dict], basis_field: str) -> Counter:
    """Nodes by how a cost was found: `_upkeep_basis` or `_capital_basis`."""
    counts = Counter({basis: 0 for basis in COST_BASES})
    for node in nodes.values():
        if node.get(basis_field) in COST_BASES:
            counts[node[basis_field]] += 1
    return counts


def typed_figures_by_file(nodes: Mapping[str, dict]) -> Dict[str, Counter]:
    """{branch file: Counter of fields still typed there}: revenue, upkeep or capital whose basis is authored."""
    fields = {"_revenue_basis": "rev_hours", "_upkeep_basis": "up_hours", "_capital_basis": "cap_hours"}
    by_file: Dict[str, Counter] = {}
    for node in nodes.values():
        for basis_field, field in fields.items():
            if node.get(basis_field) == "authored":
                by_file.setdefault(node.get("_src", "?"), Counter())[field] += 1
    return by_file


def format_lines(counts: Counter) -> List[str]:
    total = sum(counts.values())
    return ["  %-10s %5d  (%s of nodes with a revenue)"
            % (basis, counts[basis], "%.0f%%" % (100.0 * counts[basis] / total) if total else "n/a")
            for basis in BASES]


def format_cost_lines(label: str, counts: Counter) -> List[str]:
    return ["  %-10s %-8s %5d" % (label, basis, counts[basis]) for basis in COST_BASES if counts[basis]]


def format_file_lines(by_file: Mapping[str, Counter]) -> List[str]:
    return ["  %-40s %s" % (source, ", ".join("%s %d" % (field, count) for field, count in sorted(counter.items())))
            for source, counter in sorted(by_file.items())]
