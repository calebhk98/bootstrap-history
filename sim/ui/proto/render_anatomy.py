"""The `anatomy` screen: pure presentation of the reply built in anatomy.py."""

from .render_registry import renders
from .util import _fmt_num


def _percent(fraction):
    return "-" if fraction is None else "%.2f%%" % (100 * fraction)


def _value_text(value, unit):
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    if unit == "fraction":
        return _percent(value)
    return _fmt_num(value) + ((" " + unit) if unit else "")


@renders("anatomy")
def render_anatomy(out):
    if out.get("research_goal"):
        return out["note"]
    if "metrics" in out:
        return "METRICS: %s\nwith a breakdown: %s" % (
            ", ".join(out["metrics"]), ", ".join(out.get("with_breakdown") or []) or "none")
    lines = ["ANATOMY: %s" % out.get("metric")]
    if out.get("description"):
        lines.append("goal: %s" % out["description"])
    target, current = out.get("target") or {}, out.get("current")
    current_text = "unknown" if current is None else _percent(current)
    if target.get("value") is not None:
        gap = target.get("gap")
        state = ("reached" if target.get("met")
                 else "" if gap is None else "%.2f points to go" % (100 * gap))
        lines.append("now %s, target %s %s%s" % (
            current_text, target.get("op") or "", _percent(target["value"]),
            (" (%s)" % state) if state else ""))
    else:
        lines.append("now %s (no target for this metric)" % current_text)
    for row in out.get("rows") or []:
        note = ("  - " + row["note"]) if row.get("note") else ""
        lines.append("  %-30s %s%s" % (row["label"], _value_text(row.get("value"), row.get("unit") or ""), note))
    if out.get("note"):
        lines.append(out["note"])
    return "\n".join(lines)
