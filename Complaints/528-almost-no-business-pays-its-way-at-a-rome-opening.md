# Almost no business pays its way at a Rome opening

**Status:** open

After 507 Stage 3 (actors pay the economy's prices), a scan of every node at a default Rome opening found one
concern whose takings exceed its wages and rent (`fin_lottery`); coking, which paid before, now takes in about half
its costs because carbon is bought at the economy's price (found fixing `firm_entry_default_game`; no committed
command lists the scan). The state's revenue also fell by about a third. With almost nothing profitable, firms do not
enter, the founder has few ways to earn, and the opening is a stagnant economy.

Likely causes, to measure: input prices far above making cost (519: sited ores and metals open at many times their
cost), the opening's low wages and income (526), and node takings that still come from node fields rather than the
plant's own output at market prices (510/514). What it would take: a committed command (or `opening-checks` row)
that counts the concerns whose takings at opening prices exceed their running cost, per civilisation, and a
relationship check that a plausible share of the technologies a society already holds pay their way at its opening.

**Measure:** `python3 sim/simulator.py opening-checks --civs rome_100ad --concerns-only` (add `--json` for structured rows) counts, per civilisation, the held concerns whose takings exceed their running cost and lists the payers and the biggest losers. It is reported, never a failing check; it reuses the entry test's figures (`SimWorld.entry_gross`, `business_books.yearly_costs`, `firm_entry.carrying_cost`) in `sim/agents/concern_scan.py`. The relationship check (what share should pay) is still to decide.

## Note (2026-10-19)

After opening prices were limited to goods a start can make (566), `fin_lottery` no longer pays at a Rome opening and
only a handful of concerns do. `finery_puddling` pays, with takings several times what `origin/main` shows for it; the
cause is not traced. `sim/tests/test_firm_entry_default_game.py` now uses it. Measure with
`python3 sim/simulator.py opening-checks --civs rome_100ad --concerns-only`.
