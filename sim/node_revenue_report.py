#!/usr/bin/env python3
"""How much of node revenue and upkeep is derived, and what is left authored.

    python3 sim/node_revenue_report.py [--civ <civilisation id>] [--list]

Counts nodes by the basis of their revenue and upkeep, the nodes still held under the payback
floor, the payback distribution (build cost over yearly revenue, and over revenue less upkeep),
and the nodes that earn less than they cost to keep. `--list` names them. Figures are for the
civilisation's own prices and wages.
"""
import argparse
import collections
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from sim.engine import data  # noqa: E402


def distribution(values):
    values = sorted(values)
    if not values:
        return "none"
    pick = lambda share: round(values[int(share * (len(values) - 1))], 2)
    return "n=%d min %s p5 %s p25 %s median %s p75 %s p95 %s max %s" % (
        len(values), pick(0), pick(.05), pick(.25), pick(.5), pick(.75), pick(.95), pick(1))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--civ", default=None, help="civilisation id (default: the reference one)")
    parser.add_argument("--list", action="store_true", help="name the nodes in each short list")
    args = parser.parse_args()
    _tree, _document, nodes, _wages, _goods = data.load(civilization_id=args.civ)
    earners = [node for node in nodes.values() if node["_rev_hours_authored"] > 0]
    with_upkeep = [node for node in nodes.values() if node["_up_hours_authored"] > 0]
    capped = [node["id"] for node in earners if node["_revenue_basis"] == "authored"
              and node["rev_hours"] < node["_rev_hours_authored"] * (1 - 1e-6)]
    losing = [node["id"] for node in nodes.values()
              if node["rev"] > 0 and node["rev"] < node["up"] * (1 - 1e-9)]
    print("nodes %d; earn something by authored figure %d" % (len(nodes), len(earners)))
    print("revenue basis", dict(collections.Counter(node["_revenue_basis"] for node in earners)))
    print("upkeep basis ", dict(collections.Counter(node["_upkeep_basis"] for node in with_upkeep)))
    print("held under the payback floor: %d" % len(capped))
    print("payback, build cost / revenue:", distribution(
        [node["_total_cost"] / node["rev"] for node in nodes.values() if node["rev"] > 0 and node["_total_cost"] > 0]))
    net = [node for node in nodes.values() if node["rev"] > 0 and node["_total_cost"] > 0]
    print("payback, build cost / (revenue - upkeep):", distribution(
        [node["_total_cost"] / (node["rev"] - node["up"]) for node in net
         if node["rev"] - node["up"] > 1e-9 * node["rev"]]))
    print("earning exactly their upkeep (the price pays staff and nothing more): %d" % sum(
        1 for node in net if abs(node["rev"] - node["up"]) <= 1e-9 * node["rev"]))
    print("earn less than upkeep: %d (%d of them derived)" % (
        len(losing), sum(1 for node_id in losing if nodes[node_id]["_revenue_basis"] == "output")))
    if args.list:
        print("held under the floor:", " ".join(sorted(capped)))
        print("earn less than upkeep:", " ".join(sorted(losing)))


if __name__ == "__main__":
    main()
