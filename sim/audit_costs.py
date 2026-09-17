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


# A material key is a priced line item ("iron_bar_kg"), a node id is not
# ("mat_iron_bar"). Stripping the unit suffix is how the two vocabularies are
# related today - which is to say, by convention and nothing else. When the
# production side is authored properly this guesswork should be replaced by an
# explicit `produces` field on the producing node.
_UNIT_SUFFIX = re.compile(r"_(kg|t|m3|m2|l|unit|units|ea|1000)$")


def producer_of(material_key, nodes):
    base = _UNIT_SUFFIX.sub("", material_key)
    for candidate in (base, "mat_" + base):
        if candidate in nodes:
            return nodes[candidate]
    return None


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


def audit():
    tree, prices, nodes, _wages, _goods = S.load()
    if not isinstance(nodes, dict):
        nodes = {node["id"]: node for node in nodes}
    wages = wage_table(prices)
    mat_price = {material_key: float(value["p"])
                 for material_key, value in (prices.get("purchase_prices_denarii") or {}).items()
                 if isinstance(value, dict) and "p" in value}

    consumers = collections.Counter()
    for node in nodes.values():
        for key in (node.get("mat") or {}):
            consumers[key] += 1

    materials = []
    for key, used_by in consumers.most_common():
        producer = producer_of(key, nodes)
        materials.append({
            "material": key,
            "consumed_by_nodes": used_by,
            "producer": producer["id"] if producer else None,
            "producer_has_recipe": bool(producer and (producer.get("mat") or producer.get("lab"))),
            "producer_declares_output": bool(producer and producer.get("annual_output_t")),
            "book_price_denarii": mat_price.get(key),
        })

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

    conf = collections.Counter()
    for section in ("purchase_prices_denarii", "wage_rates_denarii_per_hour",
                    "transport_multipliers", "starting_kit_options"):
        for value in (prices.get(section) or {}).values():
            if isinstance(value, dict) and "conf" in value:
                conf[value["conf"]] += 1

    def populated(field):
        return sum(1 for node in nodes.values()
                   if node.get(field) not in (None, 0, 0.0, "", {}, []))

    return {
        "nodes": len(nodes),
        "fields_populated": {field: populated(field)
                             for field in ("lab", "mat", "ph", "cap", "rev", "up")},
        "cost_base_denarii": dict(totals),
        "price_confidence": dict(conf),
        "materials": materials,
    }


def _bar(share, width=28):
    filled = int(round(share * width))
    return "#" * filled + "." * (width - filled)


def report(a, show_materials=False):
    node_count = a["nodes"]
    print("TECH TREE COST AUDIT")
    print("=" * 72)
    print("%d nodes\n" % node_count)

    print("INPUT SIDE - what every process consumes. Already physical:")
    for field, unit in (("lab", "hours by trade"), ("mat", "kg / units"),
                    ("ph", "founder hours")):
        c = a["fields_populated"][field]
        print("  %-4s %-16s %5d nodes  %5.1f%%  %s"
              % (field, unit, c, 100.0 * c / node_count, _bar(c / node_count)))
    print()

    print("OUTPUT SIDE - what anything produces. This is the gap:")
    mats = a["materials"]
    with_producer = [material for material in mats if material["producer"]]
    with_recipe = [material for material in with_producer if material["producer_has_recipe"]]
    with_output = [material for material in with_producer if material["producer_declares_output"]]
    print("  materials consumed somewhere in the tree      %5d" % len(mats))
    print("  ...with a node that plausibly produces them   %5d  %5.1f%%"
          % (len(with_producer), 100.0 * len(with_producer) / max(1, len(mats))))
    print("  ...where that node has a recipe of its own    %5d  %5.1f%%"
          % (len(with_recipe), 100.0 * len(with_recipe) / max(1, len(mats))))
    print("  ...where that node says how much it YIELDS    %5d  %5.1f%%"
          % (len(with_output), 100.0 * len(with_output) / max(1, len(mats))))
    print()
    print("  A price cannot be solved out of a matrix with no outputs in it.")
    print("  The most-consumed materials with no producer at all:")
    for material in [material for material in mats if not material["producer"]][:6]:
        print("      %-18s consumed by %4d nodes" % (material["material"],
                                                     material["consumed_by_nodes"]))
    print()

    print("STILL PRICED FROM A BOOK - where the denarii come from today:")
    cb = a["cost_base_denarii"]
    total = sum(cb.values()) or 1.0
    for cost_key, label in (("materials", "materials (mat, physical)"),
                     ("capital_lump", "capital lump (cap, denarii)"),
                     ("labour", "hired labour (lab, physical)")):
        print("  %-28s %14s  %5.1f%%  %s"
              % (label, format(cb[cost_key], ",.0f"), 100.0 * cb[cost_key] / total,
                 _bar(cb[cost_key] / total)))
    print("  %-28s %14s" % ("TOTAL", format(total, ",.0f")))
    print()
    print("  Materials and labour are already physical quantities, so pricing")
    print("  them endogenously converts %.1f%% of the cost base without editing"
          % (100.0 * (cb["materials"] + cb["labour"]) / total))
    print("  a single node. The capital lump is %.1f%% and needs converting to a"
          % (100.0 * cb["capital_lump"] / total))
    print("  bill of buildings, tools and land.")
    print()

    c = a["price_confidence"]
    confidence_total = sum(c.values()) or 1
    print("CONFIDENCE IN THE BOOK ITSELF (data/prices.json):")
    for grade, meaning in (("A", "well attested"),
                           ("B", "probable, contested in detail"),
                           ("C", "the author's own estimate")):
        print("  %s  %-32s %4d  %5.1f%%"
              % (grade, meaning, c.get(grade, 0), 100.0 * c.get(grade, 0) / confidence_total))
    print()

    if show_materials:
        print("EVERY MATERIAL")
        print("-" * 72)
        print("  %-22s %6s  %-22s %s" % ("material", "used", "producer", "state"))
        for material in mats:
            if not material["producer"]:
                state = "NO PRODUCER"
            elif not material["producer_has_recipe"]:
                state = "producer is an empty marker"
            elif not material["producer_declares_output"]:
                state = "recipe but no yield"
            else:
                state = "complete"
            print("  %-22s %6d  %-22s %s"
                  % (material["material"], material["consumed_by_nodes"],
                     material["producer"] or "-", state))


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
