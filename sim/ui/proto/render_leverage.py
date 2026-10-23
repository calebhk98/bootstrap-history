"""The `leverage` and `quit` screens: pure presentation of their replies."""

from .render_registry import renders
from .util import _fmt_num


def _figure_text(value):
    if value is None:
        return "unknown"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _fmt_num(value)
    return str(value)


@renders("leverage")
def render_leverage(out):
    lines = ["LEVERAGE: " + (out.get("note") or "")]
    for point in out.get("leverage_points") or []:
        lines.append("%s - %s" % (point["lever"], point.get("why_it_matters", "")))
        for name, value in (point.get("figures") or {}).items():
            lines.append("    %-28s %s" % (name.replace("_", " "), _figure_text(value)))
    return "\n".join(lines)


@renders("quit")
def render_quit(out):
    return out.get("message") or "Goodbye."
