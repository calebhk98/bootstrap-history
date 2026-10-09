"""Validation rule: a garrison, a magazine and a banked output must name things that exist.

A node's `garrison` names trades with wages (people to hire from the labour market); a
`hazard_counters` entry's `magazine` and `draws`, and a `banks_output`, name materials something
makes; sizes are positive numbers; a work that banks output can run, or it would never bank.
"""
from typing import Any, Collection, List, Mapping

from .validate_running_gates import _can_run


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and value > 0


def check_defence_stores(nodes: Mapping[str, Mapping[str, Any]], trades: Collection[str],
                         producible: Collection[str]) -> List[str]:
    errors = []
    for node_id in sorted(nodes):
        node = nodes[node_id]
        for trade, people in (node.get("garrison") or {}).items():
            if trade not in trades:
                errors.append("%s: garrison names %s, which is not a trade with a wage" % (node_id, trade))
            if not _positive(people):
                errors.append("%s: garrison %s needs a positive number of people, not %r" % (node_id, trade, people))
        mechanics = node.get("mechanics") or {}
        for counter in mechanics.get("hazard_counters") or ():
            for field in ("magazine", "draws"):
                for material, units in (counter.get(field) or {}).items():
                    if material not in producible:
                        errors.append("%s: %s of %r names %s, which nothing makes" % (
                            node_id, field, counter["label"], material))
                    if not _positive(units):
                        errors.append("%s: %s of %r needs a positive size for %s" % (
                            node_id, field, counter["label"], material))
        banked = mechanics.get("banks_output")
        if banked:
            if banked["material"] not in producible:
                errors.append("%s: banks_output names %s, which nothing makes" % (node_id, banked["material"]))
            if not _positive(banked.get("per_labour_hour")):
                errors.append("%s: banks_output needs a positive per_labour_hour" % node_id)
            if not _can_run(node):
                errors.append("%s: banks_output on a node that cannot run (no upkeep or revenue)" % node_id)
    return errors
