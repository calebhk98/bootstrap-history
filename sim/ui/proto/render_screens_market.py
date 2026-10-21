"""Text screen for `market`."""

from sim.ui import units_text
from .util import _fmt_num, _pct

PRICE_BASIS_NOTE = {"gated": "priced at a technique you do not have",
                    "imported": "bought from a trading partner, delivered"}
# what the shown price is when nothing traded: a bid, an ask or an estimate, never read as a trade
NO_TRADE_CAUSE = {"best_unfilled_bid": "buyers bid but no seller took it",
                  "lowest_unfilled_ask": "sellers asked but no buyer bid",
                  "cost_covering": "no buyer or seller; a maker's cost",
                  "opening_estimate": "no year has traded it yet",
                  "making_cost_estimate": "not traded lately; its cost to make",
                  "thin_trade_blend": "trades a sliver; blended toward its cost to make",
                  "remembered_price": "not traded lately; the last price"}


def price_note(row):
    """The note on a price row: what a price is when nothing traded (its cause), and the basis it is priced at."""
    cause = NO_TRADE_CAUSE.get(row.get("price_kind"))
    notes = (["no trade: " + cause] if cause else []) + [PRICE_BASIS_NOTE.get(row.get("price_basis"), "")]
    return "; ".join(note for note in notes if note)


def render_market(out):
    lines = []
    materials = out.get("materials") or {}
    rows = materials.get("rows") or []
    lines += ["MATERIAL PRICES  (%s-%s of %s; own = you supply it)"
              % (materials.get("offset", 0) + 1, materials.get("offset", 0) + len(rows),
                 materials.get("total")),
              "  %-26s %10s %10s %14s  %-4s %s" % ("MATERIAL", units_text.per_mass_heading("BUY"), units_text.per_mass_heading("SELL"), "MARKET " + units_text.rate_label("mass", "yr", "t/yr").upper(), "OWN", "NOTE")]
    for row in rows:
        lines.append(("  %-26s %10s %10s %14s  %-4s %s"
                      % (row["material"], _fmt_num(row["buy_per_tonne"]),
                         _fmt_num(row["sell_per_tonne"]),
                         _fmt_num(row["market_available_tonnes_per_year"]),
                         "own" if row["own_supply"] else "",
                         price_note(row))).rstrip())
    if materials.get("offset", 0) + len(rows) < materials.get("total", 0):
        lines.append("  more: market offset %d" % (materials["offset"] + len(rows)))
    if not out.get("wages"):
        return "\n".join(lines)
    lines += ["", "WAGES  (a year of one person; 'labour <trade>' for detail)",
              "  %-18s %10s %6s %9s" % ("TRADE", "PER YEAR", "HERE", "YOU HIRE")]
    for row in out.get("wages") or []:
        lines.append("  %-18s %10s %6s %9s"
                     % (row["trade"], _fmt_num(row["a_year_of_one"]),
                        "yes" if row["available_here"] else "no",
                        _fmt_num(row["you_employ"]) if row["you_employ"] else ""))
    return "\n".join(lines)
