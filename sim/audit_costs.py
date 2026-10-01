#!/usr/bin/env python3
"""How much of this simulation's cost base is calculated, and how much is missing.

    python3 sim/audit_costs.py                 the summary
    python3 sim/audit_costs.py --materials     every material, and who makes it
    python3 sim/audit_costs.py --json          machine-readable, for CI

Costs must come from physical structure, not a lookup. This report measures
production-side coverage from data/production/ (what makes each material the
tree consumes) and prices the tree's cost base with the same solver the runtime
uses. Materials the solver cannot resolve are counted as missing, and when the
wage provider or solver cannot be reached the cost section says it is
unavailable rather than falling back to a book value.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from sim import tool_costs
from sim.presentation import (
    AUDIT_BAR_WIDTH_CHARS, AUDIT_UNPRICED_MATERIALS_SHOWN,
    AUDIT_RECIPE_LIST_TRUNCATE_CHARS)


# A material key is a priced line item ("iron_bar_kg"), a node id is not
# ("mat_iron_bar"). Stripping the unit suffix is a GUESS at which node
# produces a material, related only by convention - it answers "does the
# TREE know which node makes this", not "does anything make this".
# `data/production/` answers the second question directly: it states
# `outputs` explicitly for 196 recipes, so asking it is not a guess.
# CLAUDE.md points agents here to see where the cost base is, so a stale
# answer here is a stale answer for everyone.
#
# The node guess is KEPT rather than deleted, because the two questions are
# different and both worth an answer: "does anything make this" is now settled
# by the production data, while "does the TREE know which node makes this" is
# still unsettled and still the thing that has to be true before a recipe can
# be gated on a technology. The report prints both.
_UNIT_SUFFIX = re.compile(r"_(kg|t|m3|m2|l|unit|units|ea|1000)$")


def guessed_producer_node(material_key, nodes):
    """The old suffix-stripping guess, kept for the tree-side question only."""
    base = _UNIT_SUFFIX.sub("", material_key)
    for candidate in (base, "mat_" + base):
        if candidate in nodes:
            return nodes[candidate]
    return None


def recipes_by_output_material():
    """{material_key: [recipe_id, ...]} straight from `data/production/`.

    Not a guess. An entry's `outputs` says what it makes, which is exactly
    the question, and this is the same index `sim/solve_prices.py` builds.
    """
    from sim.validate_production import load_production
    entries, _duplicates = load_production()
    index = collections.defaultdict(list)
    for recipe_id, entry in entries.items():
        for material_key in (entry.get("outputs") or {}):
            index[material_key].append(recipe_id)
    return {key: sorted(value) for key, value in index.items()}


def _audit_materials_table(nodes, solved_price):
    """{material -> consumption/production facts}, one entry per material any
    node consumes. The OUTPUT SIDE the module docstring is about: what makes it
    (from data/production/, not a guess) and whether the TREE names a node for
    it (still a guess, see guessed_producer_node)."""
    consumers = collections.Counter()
    for node in nodes.values():
        for key in (node.get("mat") or {}):
            consumers[key] += 1

    made_by = recipes_by_output_material()

    materials = []
    for key, used_by in consumers.most_common():
        producer = guessed_producer_node(key, nodes)
        recipes = made_by.get(key) or []
        materials.append({
            "material": key,
            "consumed_by_nodes": used_by,
            # What actually makes it, from data/production/ - the real answer.
            "made_by_recipes": recipes,
            # Whether the TREE names a node for it, which is a separate and
            # still-open question; see the comment on guessed_producer_node.
            "producer": producer["id"] if producer else None,
            "producer_has_recipe": bool(producer and (producer.get("mat") or producer.get("lab"))),
            "producer_declares_output": bool(producer and producer.get("annual_output_t")),
            "solved_price_denarii": solved_price.get(key),
        })
    return materials


def _audit_cost_totals(nodes):
    """Where the money is at solved prices; `cap` is capital beyond labour and materials."""
    from sim.engine import data
    totals = collections.Counter()
    for node in nodes.values():
        totals["labour"] += node["_labour_cost"] or 0.0
        totals["materials"] += node["_material_cost"] or 0.0
        totals["capital_lump"] += float(node.get("cap_hours") or 0.0) * data.MONEY_PER_LABOUR_HOUR
    return totals


def _audit_fields_populated(nodes):
    def populated(field):
        return sum(1 for node in nodes.values()
                   if node.get(field) not in (None, 0, 0.0, "", {}, []))
    return {field: populated(field)
            for field in ("lab", "mat", "ph", "cap_hours", "rev_hours", "up_hours")}


def audit():
    nodes = tool_costs.load_tree_nodes()
    cost_report = tool_costs.price_nodes(nodes)
    solved_price = {}
    if cost_report.available:
        solved_price = tool_costs.solved_material_prices(nodes, tool_costs.runtime_wages())

    return {
        "nodes": len(nodes),
        "fields_populated": _audit_fields_populated(nodes),
        "costs_available": cost_report.available,
        "costs_unavailable_reason": cost_report.reason,
        "nodes_with_unresolved_costs": cost_report.incomplete_nodes,
        "cost_base_denarii": dict(_audit_cost_totals(nodes)) if cost_report.available else {},
        "materials": _audit_materials_table(nodes, solved_price),
    }


def _bar(share, width=AUDIT_BAR_WIDTH_CHARS):
    filled = int(round(share * width))
    return "#" * filled + "." * (width - filled)


def _report_header_and_input_side(audit):
    """Title, node count, and the INPUT SIDE block: what every process consumes,
    already physical."""
    node_count = audit["nodes"]
    lines = ["TECH TREE COST AUDIT", "=" * 72, "%d nodes\n" % node_count,
             "INPUT SIDE - what every process consumes. Already physical:"]
    for field, unit in (("lab", "hours by trade"), ("mat", "kg / units"),
                    ("ph", "founder hours")):
        count = audit["fields_populated"][field]
        lines.append("  %-4s %-16s %5d nodes  %5.1f%%  %s"
              % (field, unit, count, 100.0 * count / node_count, _bar(count / node_count)))
    lines.append("")
    return lines


def _report_output_side(audit):
    """OUTPUT SIDE block: what anything produces, and (if any) what still has
    no recipe at all."""
    mats = audit["materials"]
    made = [material for material in mats if material["made_by_recipes"]]
    lines = ["OUTPUT SIDE - what anything produces:",
             "  materials consumed somewhere in the tree      %5d" % len(mats),
             "  ...that data/production/ states a recipe for  %5d  %5.1f%%"
                  % (len(made), 100.0 * len(made) / max(1, len(mats))),
             "",
             "  Counted from data/production/, not from the tree. The tree",
             "  records what each node CONSUMES and never what anything makes,",
             "  so asking it this question can only ever return 'no producer at",
             "  all' for iron, timber, coal and most of the rest.",
             ""]
    unmade = [material for material in mats if not material["made_by_recipes"]]
    if unmade:
        lines.append("  Still nothing makes these, worst first:")
        for material in unmade[:AUDIT_UNPRICED_MATERIALS_SHOWN]:
            lines.append("      %-18s consumed by %4d nodes" % (material["material"],
                                                         material["consumed_by_nodes"]))
        lines.append("")
    return lines


def _report_tree_side_question(audit):
    # THE TREE-SIDE QUESTION, WHICH IS STILL OPEN AND IS NOT THE SAME ONE.
    # Knowing that something makes iron does not say WHICH TECHNOLOGY lets you
    # make it, and that is what a recipe has to be gated on - see
    # Complaints/39 and `requires_node` in data/production/_SCHEMA.md.
    mats = audit["materials"]
    with_producer = [material for material in mats if material["producer"]]
    return ["  Separately: does the TREE name a node for the material? This is",
            "  the suffix-stripping guess, and it is the link `requires_node`",
            "  now replaces with something explicit (Complaints/39).",
            "  ...a node id that plausibly matches the key   %5d  %5.1f%%"
                  % (len(with_producer), 100.0 * len(with_producer) / max(1, len(mats))),
            ""]


def _report_cost_base(audit):
    """COST BASE block: where the denarii come from at solved prices, or why they cannot be shown."""
    if not audit["costs_available"]:
        return ["COST BASE - unavailable: %s" % audit["costs_unavailable_reason"], ""]
    cost_base = audit["cost_base_denarii"]
    total = sum(cost_base.values()) or 1.0
    lines = ["COST BASE - at solved prices; %d nodes need a material or trade the "
             "solver cannot resolve, so their materials count as a lower bound:"
             % audit["nodes_with_unresolved_costs"]]
    for cost_key, label in (("materials", "materials (mat, physical)"),
                     ("capital_lump", "capital lump (cap, denarii)"),
                     ("labour", "hired labour (lab, physical)")):
        lines.append("  %-28s %14s  %5.1f%%  %s"
              % (label, format(cost_base[cost_key], ",.0f"), 100.0 * cost_base[cost_key] / total,
                 _bar(cost_base[cost_key] / total)))
    lines.append("  %-28s %14s" % ("TOTAL", format(total, ",.0f")))
    lines.append("")
    return lines


def _report_every_material(audit):
    """`--materials`: every material, who consumes it, and what makes it."""
    lines = ["EVERY MATERIAL", "-" * 72,
             "  %-22s %6s  %-30s %s" % ("material", "used", "made by", "state")]
    for material in audit["materials"]:
        recipes = material["made_by_recipes"]
        if not recipes:
            state = "NOTHING MAKES IT"
        elif len(recipes) > 1:
            state = "%d techniques compete" % len(recipes)
        else:
            state = "one technique"
        lines.append("  %-22s %6d  %-30s %s"
                  % (material["material"], material["consumed_by_nodes"],
                     ", ".join(recipes)[:AUDIT_RECIPE_LIST_TRUNCATE_CHARS] or "-", state))
    return lines


def report(audit, show_materials=False):
    for line in _report_header_and_input_side(audit):
        print(line)
    for line in _report_output_side(audit):
        print(line)
    for line in _report_tree_side_question(audit):
        print(line)
    for line in _report_cost_base(audit):
        print(line)
    if show_materials:
        for line in _report_every_material(audit):
            print(line)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--materials", action="store_true",
                    help="list every material and whether anything makes it")
    parser.add_argument("--json", action="store_true",
                    help="machine-readable output")
    args = parser.parse_args(argv)
    audit_result = audit()
    if args.json:
        json.dump(audit_result, sys.stdout, indent=1)
        print()
    else:
        report(audit_result, show_materials=args.materials)
    return 0


if __name__ == "__main__":
    sys.exit(main())
