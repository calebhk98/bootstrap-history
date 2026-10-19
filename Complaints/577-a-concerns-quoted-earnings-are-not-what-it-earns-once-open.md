# A concern's quoted earnings are not what it earns once open

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, 100 AD). `why`, `ventures` and `available` quoted `pwr_coking` earning a positive
sum a year; once opened it earned nothing, and `state` later showed a small figure. The quote and the takings are
computed in two places (the screens and the engine must read one function, `STATE_OF_THE_PROJECT.md`).

What it would take: the quote reads the same function the year's takings use, at the same prices; test that a
concern opened and stepped one year earns what it was quoted, within the year's price change.
