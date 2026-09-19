#!/usr/bin/env python3
"""How much of this simulation's cost base is calculated, and how much is read.

    python3 sim/audit_costs.py                 the summary
    python3 sim/audit_costs.py --materials     every material, and who makes it
    python3 sim/audit_costs.py --json          machine-readable, for CI

THE POINT OF THIS SCRIPT. The project's standing requirement is that costs are
calculated from physical structure rather than looked up: a Roman soldier does
not cost a hundred denarii because history says so, he costs what his food,
equipment, transport and forgone wages cost. Progress toward that is easy to
claim and hard to see, because replacing a book price with a hand-tuned curve
over a book price looks like progress and is not. This script exists so the
claim has a number attached, and so the number is measured from the tree as it
stands rather than remembered from the last time somebody looked.

WHAT IT FOUND THE FIRST TIME IT RAN, which is the reason it exists in this
shape rather than as a price-coverage counter:

    The tech tree records what every process CONSUMES and almost never what
    anything PRODUCES.

`mat` and `lab` are already physical - kilograms and hours - on 65% and 89% of
2,864 nodes, with no material and no trade that the price tables do not know.
That is a complete, authored input-output matrix on the consumption side. But
of the 162 distinct materials those recipes consume, only 47 have a node whose
id matches, only 7 of those carry a recipe of their own, and NOT ONE declares
how much of the material it yields. `iron_bar_kg`, consumed by 590 nodes, has
no producing node at all. `mat_copper` knows it needs 1,200 t of ore and 480 t
of charcoal and does not say how much copper comes out the other end.

A price cannot be solved out of a matrix with no outputs in it. That, and not
the existence of `data/prices.json`, is the actual reason every cost in this
engine bottoms out in a book value - and 190 of the 207 confidence-tagged
entries in that book are marked `C`, the author's own estimate.

So the measurement that matters is production-side coverage, and it is what
this script leads with.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import simulator as S
# Guarded, idempotent - see sim/engine/commodities.py's own comment at the
# identical snippet for why this needs adding explicitly rather than
# trusting a caller to have put the repository root on sys.path already.
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
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
    from validate_production import load_production
    entries, _duplicates = load_production()
    index = collections.defaultdict(list)
    for recipe_id, entry in entries.items():
        for material_key in (entry.get("outputs") or {}):
            index[material_key].append(recipe_id)
    return {key: sorted(value) for key, value in index.items()}


def wage_table(prices):
    """Hourly wage per trade, as data.py derives it from prices.json."""
    out = {}
    for trade, value in (prices.get("wage_rates_denarii_per_hour") or {}).items():
        if not isinstance(value, dict):
            continue
        if "rate" in value:
            out[trade] = float(value["rate"])
        elif "day_hs" in value:
            out[trade] = float(value["day_hs"]) / 4.0 / 10.0
    return out


def _audit_materials_table(nodes, mat_price):
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
            "book_price_denarii": mat_price.get(key),
        })
    return materials


def _audit_cost_totals(nodes, wages, mat_price):
    # Where the denarii actually are. `cap` is documented as capital BEYOND
    # labour and materials, so these three are additive, not overlapping.
    totals = collections.Counter()
    for node in nodes.values():
        totals["labour"] += sum(wages[trade] * float(hours)
                                for trade, hours in (node.get("lab") or {}).items()
                                if trade in wages)
        totals["materials"] += sum(mat_price[material_key] * float(quantity)
                                   for material_key, quantity in (node.get("mat") or {}).items()
                                   if material_key in mat_price)
        totals["capital_lump"] += float(node.get("cap") or 0.0)
    return totals


def _audit_price_confidence(prices):
    conf = collections.Counter()
    for section in ("purchase_prices_denarii", "wage_rates_denarii_per_hour",
                    "transport_multipliers", "starting_kit_options"):
        for value in (prices.get(section) or {}).values():
            if isinstance(value, dict) and "conf" in value:
                conf[value["conf"]] += 1
    return conf


def _audit_fields_populated(nodes):
    def populated(field):
        return sum(1 for node in nodes.values()
                   if node.get(field) not in (None, 0, 0.0, "", {}, []))
    return {field: populated(field)
            for field in ("lab", "mat", "ph", "cap", "rev", "up")}


def audit():
    tree, prices, nodes, _wages, _goods = S.load()
    if not isinstance(nodes, dict):
        nodes = {node["id"]: node for node in nodes}
    wages = wage_table(prices)
    mat_price = {material_key: float(value["p"])
                 for material_key, value in (prices.get("purchase_prices_denarii") or {}).items()
                 if isinstance(value, dict) and "p" in value}

    return {
        "nodes": len(nodes),
        "fields_populated": _audit_fields_populated(nodes),
        "cost_base_denarii": dict(_audit_cost_totals(nodes, wages, mat_price)),
        "price_confidence": dict(_audit_price_confidence(prices)),
        "materials": _audit_materials_table(nodes, mat_price),
    }


def _bar(share, width=AUDIT_BAR_WIDTH_CHARS):
    filled = int(round(share * width))
    return "#" * filled + "." * (width - filled)


def _report_header_and_input_side(a):
    """Title, node count, and the INPUT SIDE block: what every process consumes,
    already physical."""
    node_count = a["nodes"]
    lines = ["TECH TREE COST AUDIT", "=" * 72, "%d nodes\n" % node_count,
             "INPUT SIDE - what every process consumes. Already physical:"]
    for field, unit in (("lab", "hours by trade"), ("mat", "kg / units"),
                    ("ph", "founder hours")):
        count = a["fields_populated"][field]
        lines.append("  %-4s %-16s %5d nodes  %5.1f%%  %s"
              % (field, unit, count, 100.0 * count / node_count, _bar(count / node_count)))
    lines.append("")
    return lines


def _report_output_side(a):
    """OUTPUT SIDE block: what anything produces, and (if any) what still has
    no recipe at all."""
    mats = a["materials"]
    made = [material for material in mats if material["made_by_recipes"]]
    lines = ["OUTPUT SIDE - what anything produces:",
             "  materials consumed somewhere in the tree      %5d" % len(mats),
             "  ...that data/production/ states a recipe for  %5d  %5.1f%%"
                  % (len(made), 100.0 * len(made) / max(1, len(mats))),
             "",
             "  This used to read 'no producer at all' for iron, timber, coal and",
             "  most of the rest, because it asked the TREE, which records what a",
             "  node consumes and never what anything makes. data/production/ does",
             "  state it, so the question is now answered rather than guessed.",
             ""]
    unmade = [material for material in mats if not material["made_by_recipes"]]
    if unmade:
        lines.append("  Still nothing makes these, worst first:")
        for material in unmade[:AUDIT_UNPRICED_MATERIALS_SHOWN]:
            lines.append("      %-18s consumed by %4d nodes" % (material["material"],
                                                         material["consumed_by_nodes"]))
        lines.append("")
    return lines


def _report_tree_side_question(a):
    # THE TREE-SIDE QUESTION, WHICH IS STILL OPEN AND IS NOT THE SAME ONE.
    # Knowing that something makes iron does not say WHICH TECHNOLOGY lets you
    # make it, and that is what a recipe has to be gated on - see
    # Complaints/39 and `requires_node` in data/production/_SCHEMA.md.
    mats = a["materials"]
    with_producer = [material for material in mats if material["producer"]]
    return ["  Separately: does the TREE name a node for the material? This is",
            "  the suffix-stripping guess, and it is the link `requires_node`",
            "  now replaces with something explicit (Complaints/39).",
            "  ...a node id that plausibly matches the key   %5d  %5.1f%%"
                  % (len(with_producer), 100.0 * len(with_producer) / max(1, len(mats))),
            ""]


def _report_cost_base(a):
    """STILL PRICED FROM A BOOK block: where the denarii come from today."""
    cost_base = a["cost_base_denarii"]
    total = sum(cost_base.values()) or 1.0
    lines = ["STILL PRICED FROM A BOOK - where the denarii come from today:"]
    for cost_key, label in (("materials", "materials (mat, physical)"),
                     ("capital_lump", "capital lump (cap, denarii)"),
                     ("labour", "hired labour (lab, physical)")):
        lines.append("  %-28s %14s  %5.1f%%  %s"
              % (label, format(cost_base[cost_key], ",.0f"), 100.0 * cost_base[cost_key] / total,
                 _bar(cost_base[cost_key] / total)))
    lines.append("  %-28s %14s" % ("TOTAL", format(total, ",.0f")))
    lines.append("")
    lines.append("  Materials and labour are already physical quantities, so pricing")
    lines.append("  them endogenously converts %.1f%% of the cost base without editing"
          % (100.0 * (cost_base["materials"] + cost_base["labour"]) / total))
    lines.append("  a single node. The capital lump is %.1f%% and needs converting to a"
          % (100.0 * cost_base["capital_lump"] / total))
    lines.append("  bill of buildings, tools and land.")
    lines.append("")
    return lines


def _report_price_confidence(a):
    confidence = a["price_confidence"]
    confidence_total = sum(confidence.values()) or 1
    lines = ["CONFIDENCE IN THE BOOK ITSELF (data/prices.json):"]
    for grade, meaning in (("A", "well attested"),
                           ("B", "probable, contested in detail"),
                           ("C", "the author's own estimate")):
        lines.append("  %s  %-32s %4d  %5.1f%%"
              % (grade, meaning, confidence.get(grade, 0), 100.0 * confidence.get(grade, 0) / confidence_total))
    lines.append("")
    return lines


def _report_every_material(a):
    """`--materials`: every material, who consumes it, and what makes it."""
    lines = ["EVERY MATERIAL", "-" * 72,
             "  %-22s %6s  %-30s %s" % ("material", "used", "made by", "state")]
    for material in a["materials"]:
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


def report(a, show_materials=False):
    for line in _report_header_and_input_side(a):
        print(line)
    for line in _report_output_side(a):
        print(line)
    for line in _report_tree_side_question(a):
        print(line)
    for line in _report_cost_base(a):
        print(line)
    for line in _report_price_confidence(a):
        print(line)
    if show_materials:
        for line in _report_every_material(a):
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
