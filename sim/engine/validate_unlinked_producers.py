"""Which nodes carry a running cost but run no production entry, so opening them earns nothing.

A node earns only through the production entries it gates or operates (`node_output.entries_gated_by`).
This lists the nodes with upkeep that run none, counted by category. Report only: some of them make no
good at all (a school, a law), so the list is the worklist for linking a twin node or authoring a recipe.
Run with `python3 -m sim.engine.validate_unlinked_producers`.
"""
import os
import sys
from collections import Counter
from typing import Any, Iterable, List, Mapping, Set, Tuple

from sim.engine.node_output import entries_gated_by

ALLOWED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                            "data", "unlinked_upkeep_nodes.txt")


def load_allowed(path: str = ALLOWED_PATH) -> List[str]:
    """The nodes still allowed to charge upkeep with no plant (Complaint 510), one id per line, sorted."""
    with open(path, encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def check_unlinked_upkeep(nodes: Mapping[str, Mapping[str, Any]], production: Mapping[str, Any],
                          allowed: Iterable[str]) -> Tuple[List[str], List[str]]:
    """(errors, stale): a node that charges upkeep, gates or operates no entry and is not allowed is an error; an allowed
    node that no longer offends is stale, to be pruned from the list. Upkeep belongs to plants, not to knowledge."""
    allowed_ids: Set[str] = set(allowed)
    offenders = {node["id"] for node in unlinked_nodes(nodes, production)}
    errors = ["%s: charges upkeep but gates or operates no production entry (a node is knowledge; upkeep belongs to the "
              "plant of an entry that names it in operated_by; Complaint 510)" % node_id
              for node_id in sorted(offenders - allowed_ids)]
    return errors, sorted(allowed_ids - offenders)


def unlinked_nodes(nodes: Mapping[str, Mapping[str, Any]], production: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """Nodes with upkeep hours that gate or operate no production entry, in id order."""
    return [node for node_id, node in sorted(nodes.items())
            if (node.get("up_hours") or 0) > 0 and not entries_gated_by(node_id, production)]


def report_lines(nodes: Mapping[str, Mapping[str, Any]], production: Mapping[str, Any]) -> List[str]:
    costly = [node for node in nodes.values() if (node.get("up_hours") or 0) > 0]
    unlinked = unlinked_nodes(nodes, production)
    by_category = Counter(node.get("cat") or "(none)" for node in unlinked)
    lines = ["nodes with upkeep: %d; running no production entry: %d" % (len(costly), len(unlinked))]
    staffed = [node for node in unlinked if (node.get("art") or 0) + (node.get("sch") or 0) > 0]
    lines.append("  of those, staffed by artisans or scholars: %d; by kind: %s" % (
        len(staffed), ", ".join("%s %d" % pair for pair in sorted(Counter(node.get("kind") for node in unlinked).items(),
                                                                  key=lambda pair: str(pair[0])))))
    lines += ["  %s: %d" % (category, count) for category, count in sorted(by_category.items(), key=lambda pair: (-pair[1], pair[0]))]
    return lines


def main() -> None:
    root = os.getcwd()
    sys.path.insert(0, root)
    from sim.engine.catalog import load_production_catalog
    from sim.engine import data
    production = load_production_catalog(root, os.path.join(root, "mods"))
    nodes = {node["id"]: node for node in data.load()[0]["nodes"]}
    print("\n".join(report_lines(nodes, production)))


if __name__ == "__main__":
    main()
