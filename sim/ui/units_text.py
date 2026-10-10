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


def rate_label(dimension: str, per: str, default: str) -> str:
    """The unit label of a quantity per `per` (a field rule's time word or a dimension), such as mass per year or money per mass."""
    return TEXT_LABELS.get("%s/%s" % (dimension, per), default)


def per_mass_heading(word: str) -> str:
    """Column heading of a money-per-mass price: BUY/T by default, BUY h/lb for another choice."""
    label = TEXT_LABELS.get("money/mass")
    return "%s %s" % (word, label) if label else "%s/T" % word


def _renamed(key: str, rule: Mapping[str, Any], name: str) -> str:
    word = rule.get("word")
    spelled = name.replace(" ", "_")
    if word and re.search(word, key):
        return re.sub(word, spelled, key, count=1)
    return "%s_in_%s" % (key, spelled)


def _without_tags(node: Any) -> Any:
    """The reply without the `field_units` tags producers add for scripts; a text screen never prints them."""
    if isinstance(node, list):
        return [_without_tags(item) for item in node]
    if isinstance(node, dict):
        return {key: _without_tags(value) for key, value in node.items() if key != "field_units"}
    return node


def for_text(reply: Any, rename: bool) -> Any:
    """A reply as a text screen shows it: each field with a `_display`
    sibling carries the displayed value, the sibling is dropped, and
    TEXT_LABELS records the unit symbols. `rename` also renames the field
    after the unit, for screens that print field names as labels."""
    TEXT_LABELS.clear()
    reply = _without_tags(reply)
    if not units.chosen_units():
        return reply
    reg = units.registry()

    def walk(node, parent=None):
        if isinstance(node, list):
            return [walk(item, parent) for item in node]
        if not isinstance(node, dict):
            return node
        out = {}
        for key, value in node.items():
            if key.endswith("_display") and key[:-len("_display")] in node:
                continue
            shown = node.get(key + "_display")
            if isinstance(shown, dict) and "value" in shown:
                rule = units.rule_for(reg, node, key, parent) or {"dimension": "?"}
                if rule.get("per_dimension"):
                    TEXT_LABELS["%s/%s" % (rule["dimension"], rule["per_dimension"])] = shown["symbol"]
                elif rule.get("per"):
                    TEXT_LABELS["%s/%s" % (rule["dimension"], rule["per"])] = "%s/%s" % (shown["symbol"], rule["per"])
                else:
                    TEXT_LABELS[rule["dimension"]] = shown["symbol"]
                out[_renamed(key, rule, shown["unit"]) if rename else key] = shown["value"]
            else:
                out[key] = walk(value, key) if isinstance(value, (dict, list)) else value
        return out
    return walk(reply)
