"""Printed forms of the pursue and programme replies and of the step reply's `programme` rows."""

from .render_registry import renders
from .util import _fmt_num, _wrap


def render_programme_rows(rows):
    """Lines for the step reply's `programme` key: what the standing programme did each year."""
    lines = []
    for row in rows:
        started = row.get("started") or []
        head = "%s: %s" % (row["year"], row["what"])
        if row.get("did_nothing_because"):
            lines.append("%s did nothing: %s" % (head, row["did_nothing_because"]))
            continue
        lines.append("%s started %d, spent %s, founder hours %s" % (
            head, len(started), _fmt_num(row.get("spent", 0.0)), _fmt_num(row.get("hours", 0.0))))
        lines.extend("  - %s (%s)" % (item["name"], _fmt_num(item["cost"])) for item in started)
        for item in row.get("skipped") or []:
            lines.append("  skipped %s: %s" % (item["id"], item["why"]))
    return lines


@renders("programme")
def render_programme(out):
    if not out.get("ok"):
        return out.get("error", "")
    programme = out.get("programme")
    if not programme:
        return out.get("note", "no programme set")
    lines = ["PROGRAMME: %s%s" % (programme["target"], " (paused)" if programme["paused"] else ""),
             "  caps: %s" % programme["caps"],
             "  committed so far: %s, founder hours %s" % (
                 _fmt_num(programme["committed_so_far"]), _fmt_num(programme.get("hours_committed_so_far", 0))),
             "  pauses on: %s" % programme.get("pauses", "none"),
             _wrap(programme["runs"], indent="  ")]
    if out.get("note"):
        lines.append(_wrap(out["note"], indent="  "))
    return "\n".join(lines)


@renders("pursue")
def render_pursue(out):
    if not out.get("ok"):
        return out.get("error", "")
    pursuit = out.get("pursue", {})
    lines = ["PURSUE %s (%d startable on the route; order: %s)" % (
        pursuit.get("name", ""), pursuit.get("startable_on_route", 0), pursuit.get("order", ""))]
    if out.get("note"):
        lines.append(_wrap(out["note"], indent="  "))
    started = out.get("would_start") if out.get("preview") else out.get("started")
    verb = "would start" if out.get("preview") else "started"
    for item in started or []:
        lines.append("  %s %s (%s)" % (verb, item["name"], _fmt_num(item["cost"])))
    for item in (out.get("not_started") or [])[:8]:
        lines.append("  not begun %s: %s" % (item.get("name") or item["id"], item["why"]))
    return "\n".join(lines)
