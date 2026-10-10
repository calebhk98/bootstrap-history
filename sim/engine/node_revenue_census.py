"""How nodes get their money figures: revenue only from output, upkeep and capital by basis.

`_revenue_basis` is `output` for a node that earns from the entries naming it in `operated_by`; every
other node earns nothing directly. `_upkeep_basis` and `_capital_basis` say how a cost was found
(derived from entries, a programme's stated bill, staff, a labelled share of the build bill, or a figure a
mod states). Printed by `simulator.py validate`."""
from collections import Counter
from typing import List, Mapping

COST_BASES = ("derived", "programme", "staff", "default", "authored")


def basis_counts(nodes: Mapping[str, dict]) -> Counter:
    return Counter({"output": sum(1 for node in nodes.values() if node.get("_revenue_basis") == "output"),
                    "no product": sum(1 for node in nodes.values() if node.get("_revenue_basis") != "output")})


def cost_basis_counts(nodes: Mapping[str, dict], basis_field: str) -> Counter:
    """Nodes by how a cost was found: `_upkeep_basis` or `_capital_basis`."""
    counts = Counter({basis: 0 for basis in COST_BASES})
    for node in nodes.values():
        if node.get(basis_field) in COST_BASES:
            counts[node[basis_field]] += 1
    return counts


def format_lines(counts: Counter) -> List[str]:
    return ["  %-10s %5d" % (basis, counts[basis]) for basis in ("output", "no product")]


def format_cost_lines(label: str, counts: Counter) -> List[str]:
    return ["  %-10s %-10s %5d" % (label, basis, counts[basis]) for basis in COST_BASES if counts[basis]]
