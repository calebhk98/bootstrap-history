"""Text screen for `market`."""

from sim.ui import units_text
from .util import _fmt_num, _pct


def render_market(out):
    lines = ["GOODS YOUR CONCERNS SELL INTO  (share of the quoted figure being earned)"]
    goods = out.get("goods") or []
    if not goods:
        lines.append("  none yet: nothing you run sells into a goods market")
    for row in goods:
        lines.append("  %-14s %5s of %s/yr quoted   competing: %s"
                     % (row["category"], _pct(row["share_of_quoted_earned"]),
                        _fmt_num(row["quoted_per_year"]), ", ".join(row["concerns"])))
    demand = out.get("demand") or []
    if demand:
        lines += ["", "DEMAND BY GOODS CATEGORY  (sale price and quantity against the day you first sold; "
                      "NEW = what one more concern would earn of its quoted figure)",
                  "  %-14s %6s %9s %9s %6s" % ("CATEGORY", "YOURS", "PRICE", "QUANTITY", "NEW")]
        for row in demand:
            lines.append("  %-14s %6d %9s %9s %6s"
                         % (row["category"], row["concerns_of_yours"],
                            _pct(row["sale_price_vs_opening"]) if row["sale_price_vs_opening"] is not None else "-",
                            _pct(row["quantity_vs_opening"]) if row["quantity_vs_opening"] is not None else "-",
                            _pct(row["new_concern_earns_share"])))
    materials = out.get("materials") or {}
    rows = materials.get("rows") or []
    lines += ["", "MATERIAL PRICES  (%s-%s of %s; own = you supply it)"
              % (materials.get("offset", 0) + 1, materials.get("offset", 0) + len(rows),
                 materials.get("total")),
              "  %-26s %10s %10s %14s  %-4s %s" % ("MATERIAL", units_text.per_mass_heading("BUY"), units_text.per_mass_heading("SELL"), "MARKET " + units_text.rate_label("mass", "yr", "t/yr").upper(), "OWN", "NOTE")]
    for row in rows:
        lines.append(("  %-26s %10s %10s %14s  %-4s %s"
                      % (row["material"], _fmt_num(row["buy_per_tonne"]),
                         _fmt_num(row["sell_per_tonne"]),
                         _fmt_num(row["market_available_tonnes_per_year"]),
                         "own" if row["own_supply"] else "",
                         "priced at a technique you do not have"
                         if row.get("price_basis") in ("gated", "mature") else "")).rstrip())
    if materials.get("offset", 0) + len(rows) < materials.get("total", 0):
        lines.append("  more: market offset %d" % (materials["offset"] + len(rows)))
    lines += ["", "WAGES  (a year of one person; 'labour <trade>' for detail)",
              "  %-18s %10s %6s %9s" % ("TRADE", "PER YEAR", "HERE", "YOU HIRE")]
    for row in out.get("wages") or []:
        lines.append("  %-18s %10s %6s %9s"
                     % (row["trade"], _fmt_num(row["a_year_of_one"]),
                        "yes" if row["available_here"] else "no",
                        _fmt_num(row["you_employ"]) if row["you_employ"] else ""))
    return "\n".join(lines)


def why_goods_market_lines(out):
    """The `why` section naming a concern's goods market."""
    lines = [out["goods_market_line"]] if out.get("goods_market_line") else []
    effect = out.get("opening_effect")
    if effect:
        lines.append("Opening it: earns about %s a year at maturity; your existing concerns in %s "
                     "change by %s a year; net %s. (%s)"
                     % (_fmt_num(effect["new_concern_earns_per_year"]), effect["category"],
                        _fmt_num(effect["existing_concerns_change_per_year"]),
                        _fmt_num(effect["net_change_per_year"]), effect["basis"]))
    return lines
