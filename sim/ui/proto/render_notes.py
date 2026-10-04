"""Text views of the note and notes replies."""
from .render_registry import renders


def _line(entry):
    where = "  [%s]" % entry["project_name"] if entry.get("project_name") else ""
    return "  #%-3s %4s AD  %s%s" % (entry["n"], entry["year"], entry["text"], where)


@renders("note")
def render_note(out):
    if out.get("dropped"):
        return "dropped note #%s: %s" % (out["dropped"]["n"], out["dropped"]["text"])
    lines = ["noted (#%s, %s AD)%s" % (
        out["added"]["n"], out["added"]["year"],
        " on %s" % out["added"]["project_name"] if out["added"].get("project_name") else "")]
    if out.get("cut"):
        lines.append(out["cut"])
    return "\n".join(lines)


@renders("notes")
def render_notes(out):
    title = "NOTES: %s" % out["count"]
    if out.get("filter"):
        title += " on %s" % out["filter"]
    lines = [title, ""] + [_line(entry) for entry in out.get("entries") or []]
    for key in ("hint", "more"):
        if out.get(key):
            lines += ["", out[key]]
    return "\n".join(lines)
