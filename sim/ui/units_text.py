"""Display units on text screens: the chosen unit's values and labels.

A reply already carries `<field>_display` beside every quantity (units.py).
Before a screen is rendered, `for_text` puts those values in place of the base
ones and records the unit symbols, which a renderer reads with `text_label`
for any heading or column label it writes itself.
"""
import re
from typing import Any, Dict, Mapping

from sim.engine.ui_port import units

# Unit symbols of the screen being rendered, by dimension.
TEXT_LABELS: Dict[str, str] = {}


def text_label(dimension: str, default: str) -> str:
    return TEXT_LABELS.get(dimension, default)


def _renamed(key: str, rule: Mapping[str, Any], name: str) -> str:
    word = rule.get("word")
    spelled = name.replace(" ", "_")
    if word and re.search(word, key):
        return re.sub(word, spelled, key, count=1)
    return "%s_in_%s" % (key, spelled)


def for_text(reply: Any, rename: bool) -> Any:
    """A reply as a text screen shows it: each field with a `_display`
    sibling carries the displayed value, the sibling is dropped, and
    TEXT_LABELS records the unit symbols. `rename` also renames the field
    after the unit, for screens that print field names as labels."""
    TEXT_LABELS.clear()
    if not units.PREFERENCES:
        return reply
    reg = units.registry()

    def walk(node):
        if isinstance(node, list):
            return [walk(item) for item in node]
        if not isinstance(node, dict):
            return node
        out = {}
        for key, value in node.items():
            if key.endswith("_display") and key[:-len("_display")] in node:
                continue
            shown = node.get(key + "_display")
            if isinstance(shown, dict) and "value" in shown:
                rule = units.field_rule(reg, key) or {"dimension": "?"}
                TEXT_LABELS[rule["dimension"]] = shown["symbol"]
                out[_renamed(key, rule, shown["unit"]) if rename else key] = shown["value"]
            else:
                out[key] = walk(value) if isinstance(value, (dict, list)) else value
        return out
    return walk(reply)
