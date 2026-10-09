"""Validation rules for what a node earns.

- A node states no revenue: it earns from the output of the entries that name it in `operated_by`, or
  not directly at all (its value is what its mechanics change).
- A node named in `operated_by` has a plant, staff or declared `annual_output_t` that bounds its output;
  whether one does not depend on prices, so it is tested with every output priced alike.
"""
from typing import Any, List, Mapping

from . import node_output


def check_no_typed_revenue(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    return ["%s: states rev_hours; a node earns from the output of the entries that name it in operated_by, "
            "never from a typed figure" % node_id
            for node_id, node in nodes.items() if float(node.get("_rev_hours_authored") or 0.0) > 0.0]


def check_operated_nodes_are_bounded(nodes: Mapping[str, Mapping[str, Any]], production: Mapping[str, Any]) -> List[str]:
    errors = []
    for node_id, node in nodes.items():
        gated = [entry for entry in node_output.entries_gated_by(node_id, production)
                 if node_id in (entry.get("operated_by") or [])]
        if not gated:
            continue
        unit_prices = {material: 1.0 for entry in gated for material in entry.get("outputs") or {}}
        if node_output.output_baskets(node, production, unit_prices, entries=gated) is None:
            errors.append("%s: is named in operated_by but no plant, staff or annual_output_t bounds its output; "
                          "declare one" % node_id)
    return errors


def check_node_money(nodes: Mapping[str, Mapping[str, Any]], production: Mapping[str, Any]) -> List[str]:
    return check_no_typed_revenue(nodes) + check_operated_nodes_are_bounded(nodes, production)
