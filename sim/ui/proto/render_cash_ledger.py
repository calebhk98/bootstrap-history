"""The `cashbook` screen."""
from .render_registry import renders
from .util import _fmt_num


def _signed(amount):
    return ("+" + _fmt_num(amount)) if amount >= 0 else _fmt_num(amount)


@renders("cashbook", "cashflow", "cashyears")
def render_cash_ledger(out):
    lines = []
    for row in out.get("years") or []:
        lines.append("%s%s" % (row["year"], " (open, so far)" if row.get("open_year") else ""))
        lines.append("  %-50s %s" % ("opening cash", _fmt_num(row["opening"])))
        for cause in row["causes"]:
            lines.append("    %-48s %s" % (cause["cause"], _signed(cause["amount"])))
        if row.get("not_itemised"):
            lines.append("    %-48s %s" % ("not itemised", _signed(row["not_itemised"])))
        lines.append("  %-50s %s" % ("cash now" if row.get("open_year") else "closing cash",
                                     _fmt_num(row["closing"])))
    if out.get("note"):
        lines.append(out["note"])
    return "\n".join(lines)
