"""The itemised ledger of where the money comes from, kept in parts that add up to the stated revenue. Plain
arithmetic on the numbers handed in."""

LEDGER_ROWS_SHOWN = 15
SMALL_ROW_FLOOR = 0.5
GAP_SHOWN_ABOVE = 1.0
ROUNDING_RESIDUE_FLOOR = 0.049


def assemble_ledger(concern_rows, workshop_total, wage_total, state_funding_total, revenue):
    """Rows of `{label: yearly money}` that sum to `revenue` at one decimal. The largest concerns are listed, the rest
    summed into one row, then the workshop's output, the founder's wages and state funding (None when there is none); what the market will not
    absorb takes the whole gap, and a gap too small to show is pushed into the largest row so the rounded rows still
    add up."""
    ranked = sorted(concern_rows.items(), key=lambda entry: -entry[1])
    out = dict(ranked[:LEDGER_ROWS_SHOWN])
    rest = sum(value for _node_id, value in ranked[LEDGER_ROWS_SHOWN:])
    if rest > SMALL_ROW_FLOOR:
        out["_and_%d_smaller_concerns" % len(ranked[LEDGER_ROWS_SHOWN:])] = round(rest, 1)
    if workshop_total > SMALL_ROW_FLOOR:
        out["_what_your_own_workshop_sells"] = round(workshop_total, 1)
    if wage_total > SMALL_ROW_FLOOR:
        out["_wages_for_your_own_work"] = round(wage_total, 1)
    if state_funding_total is not None:
        out["_state_funding"] = round(state_funding_total, 1)
    gap = round(revenue - sum(out.values()), 1)
    if abs(gap) > GAP_SHOWN_ABOVE:
        out["_what_the_market_will_not_absorb"] = gap
        return out
    residue = round(round(revenue, 1) - sum(out.values()), 1)
    if out and abs(residue) > ROUNDING_RESIDUE_FLOOR:
        # sorted(): a tie in max() over a dict falls back to insertion order
        largest = max(sorted(out), key=lambda key: abs(out[key]))
        out[largest] = round(out[largest] + residue, 1)
    return out
