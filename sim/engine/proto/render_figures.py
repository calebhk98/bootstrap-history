"""The `figures` screen: last year, this year and the causes of the change."""

from .util import _fmt_num


def _signed(value, digits):
    if value is None:
        return "n/a"
    return ("%+" + (",.%df" % digits)) % value


def _digits_of(out):
    return 4 if abs(out.get("current") or 0.0) < 10 else 0


def render_figures(out):
    if out.get("figures"):
        lines = ["FIGURES  (figures <name> says what moved one)"]
        lines += ["  %-18s %s" % (row["name"], row["label"]) for row in out["figures"]]
        return "\n".join(lines)
    digits = _digits_of(out)
    lines = ["%s: %s" % (out.get("label", out.get("name")), _fmt_num(out.get("current")))]
    if out.get("previous") is None:
        lines.append("  no earlier year recorded yet")
    else:
        lines.append("  %s in %s, %s now (%s)" % (_fmt_num(out["previous"]), out.get("previous_year"),
                                                  _fmt_num(out["current"]), _signed(out.get("change"), digits)))
    for cause in out.get("causes") or []:
        lines.append("    %-52s %s" % (cause["cause"], _signed(cause["contribution"], digits)
                                      if cause["contribution"] is not None else _fmt_num(cause["current"])))
    for driver in out.get("drivers") or []:
        lines.append("    driver %-45s %s -> %s" % (driver["driver"], _fmt_num(driver["previous"]),
                                                    _fmt_num(driver["current"])))
    if out.get("note"):
        lines.append("  " + out["note"])
    return "\n".join(lines)
