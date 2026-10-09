"""Validation rule: a node that declares how much of its know-how shows to an onlooker says why.

`copy_visibility` is the share (above zero, at most one) of the technique an onlooker can recover from the
finished product or the working yard: one for a device whose whole design is visible, near zero for a
process whose essence (proportions, temperatures, timing) leaves no trace in the product. The reason names
what is or is not visible. A node that declares neither keeps the count of trades and materials."""
from typing import Any, List, Mapping

MINIMUM_REASON_LENGTH = 30


def check_copy_visibility(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    errors = []
    for node_id, node in nodes.items():
        if "copy_visibility" not in node and "copy_visibility_reason" not in node:
            continue
        share = node.get("copy_visibility")
        if isinstance(share, bool) or not isinstance(share, (int, float)) or not 0.0 < share <= 1.0:
            errors.append("%s: copy_visibility must be a number above 0 and at most 1" % node_id)
        elif len(node.get("copy_visibility_reason") or "") < MINIMUM_REASON_LENGTH:
            errors.append("%s: copy_visibility needs a copy_visibility_reason naming what shows and what does not" % node_id)
    return errors


def check_category_table(categories: Mapping[str, Mapping[str, Any]]) -> List[str]:
    """Each category entry states a share above zero and at most one and a reason naming what shows and what does not."""
    errors = []
    for category, entry in sorted(categories.items()):
        share = entry.get("copy_visibility")
        if isinstance(share, bool) or not isinstance(share, (int, float)) or not 0.0 < share <= 1.0:
            errors.append("copy_visibility category %s: the share must be a number above 0 and at most 1" % category)
        elif len(entry.get("reason") or "") < MINIMUM_REASON_LENGTH:
            errors.append("copy_visibility category %s: it needs a reason naming what shows and what does not" % category)
    return errors
