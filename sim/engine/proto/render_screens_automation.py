"""The printed `automation` screen: each automatic action with its reason and cost."""

from .util import _fmt_num, _wrap


def render_automation(out):
    lines = ["WHAT AUTOMATION DID"]
    rows = out.get("rows") or []
    if not rows:
        lines.append("  " + str(out.get("note") or "nothing"))
        return "\n".join(lines)
    for row in rows:
        lines.append("")
        lines.append("  %s %s: %s" % (row["year"], row["policy"].upper(), row["what"]))
        lines.append(_wrap("Reason: " + row["reason"], indent="    "))
        lines.append("    Cost: %s" % _fmt_num(row["cost"]))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"], indent="  "))
    return "\n".join(lines)
