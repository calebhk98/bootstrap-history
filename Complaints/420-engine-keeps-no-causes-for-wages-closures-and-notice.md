# The engine keeps no causes for wage changes, venture closures or state notice

**Status:** open

Complaint 95 asks "why did this number change?" for wages, state notice, epidemic severity, project throughput and venture shutdowns. The UI can show the value, last year's value and the live drivers for each (`sim/ui/figures*.py`), but for three of them the cause is not recorded anywhere it can read:

- **Wages:** `sim.wage_index` and `sim.wage_per_hour(trade)` give the level, but nothing records which pressure moved it (a famine, the price index, the labour market).
- **Venture shutdowns:** the step snapshots hold `concerns_closed`, but not why each one closed (a staffing departure, a refusal, a price change). `staffing_closure_summary()` covers only staffing.
- **State notice:** `sim.state_notice()` and `eminence_report()` give the level, not what moved it this year.

What it would take: where each is computed, append `(cause, signed amount)` rows for the year, in the style of `sim/engine/cash_book.py`, and expose them through `ui_port`. The UI side then needs only a `since=` function on the figure, as the cash figure already has.

Related: 95.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 95 (`closed/95-why-did-number-change-inspector.md`): the why-did-this-number-change inspector needs the cause rows here, plus an open/mothball effect line.
- 117 (`closed/117-prefer-explicit-state-causes-over-overloaded-flags.md`): prefer explicit state causes over overloaded flags; remaining instance is 54.
