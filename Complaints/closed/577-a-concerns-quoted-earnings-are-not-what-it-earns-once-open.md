# A concern's quoted earnings are not what it earns once open

**Status:** closed - the quote and the year's takings read `venture_real_earnings`

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, 100 AD). `why`, `ventures` and `available` quoted `pwr_coking` earning a positive
sum a year; once opened it earned nothing, and `state` later showed a small figure. The quote and the takings are
computed in two places (the screens and the engine must read one function, `STATE_OF_THE_PROJECT.md`).

What it would take: the quote reads the same function the year's takings use, at the same prices; test that a
concern opened and stepped one year earns what it was quoted, within the year's price change.

## Resolution

Two gaps. A concern not yet open was quoted without the goods market's price for its output (a running one had it),
so a concern whose market pays nothing was quoted a sum it never earned. And `revenue` summed a separate
`concern_revenue` that lacked the value and learning ratios the screens applied. `venture_real_earnings` now applies
the market whether or not the concern is open, a running scalable concern counts its units, and `concern_revenue`
calls it (without the output factor, which `revenue` applies to its total), so the screens and the takings read one
function. Tests: `sim/tests/test_complaint_577_quote_is_takings.py`; fixtures in
`test_complaint_149_one_earnings_figure.py` and `test_screens_ventures_path_available.py` now pick concerns that earn
at the market's price.
