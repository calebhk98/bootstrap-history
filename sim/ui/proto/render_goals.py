"""Text view of the goals reply."""
from .render_registry import renders

HIDDEN_NAME = "a goal you have not learned the name of"


def _row(row, label=None):
    state = "reached" if row.get("reached") else "%s of %s done" % (row["done"], row["total"])
    return "  %-44s %s" % ((label or row.get("name") or HIDDEN_NAME)[:44], state)


@renders("goals")
def render_goals(out):
    lines = []
    if out.get("changed"):
        lines += [out["changed"], ""]
    formal = out["formal"]
    lines += ["FORMAL GOAL", _row(formal, formal.get("name") or "the formal goal (name withheld)")]
    if formal.get("year_reached"):
        lines.append("  reached in %s" % formal["year_reached"])
    lines += ["", "WATCHED"] + ([_row(row) for row in out.get("watched") or []] or ["  none; 'goals watch <goal>'"])
    if out.get("choices"):
        lines += ["", "YOU COULD WATCH"] + [
            "%s  (%s)" % (_row(row), row["id"]) for row in out["choices"]]
    if out.get("unknown_goals"):
        lines.append("  and %s more you have not heard of yet" % out["unknown_goals"])
    lines += ["", out["note"]]
    return "\n".join(lines)
