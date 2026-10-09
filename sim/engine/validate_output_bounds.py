"""Validation rule: a gated maker states what bounds its output.

A node that gates a production entry and still takes an authored revenue
figure (no plant, staff or declared annual_output_t reached it) must say why
in `output_unbounded_reason`, beside the node.

Whether a plant, staff or declared output bounds a node does not depend on prices, so it is tested with
every output priced alike: a node whose goods nobody in reach sells (no price, hence authored revenue)
is still bounded when its data bounds it."""
from typing import Any, List, Mapping

from . import node_output

MINIMUM_REASON_LENGTH = 30


def check_output_bounds(nodes: Mapping[str, Mapping[str, Any]], production: Mapping[str, Any]) -> List[str]:
    errors = []
    for node_id, node in nodes.items():
        if not (node.get("_rev_hours_authored", 0.0) > 0 and node.get("_revenue_basis") == "authored"):
            continue
        gated = node_output.entries_gated_by(node_id, production)
        if not gated:
            continue
        unit_prices = {material: 1.0 for entry in gated for material in entry.get("outputs") or {}}
        if node_output.output_baskets(node, production, unit_prices, entries=gated) is not None:
            continue
        reason = node.get("output_unbounded_reason") or ""
        if len(reason) < MINIMUM_REASON_LENGTH:
            errors.append("%s: gates a production entry but no plant, staff or annual_output_t bounds its output; "
                          "declare one or give output_unbounded_reason" % node_id)
    return errors
