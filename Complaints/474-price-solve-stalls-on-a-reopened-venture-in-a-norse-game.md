# A price solve stalls when a Norse game reopens a venture

**Status:** open

`sim/tests/test_arrears_hours.py` plays Norse for twelve years in `_portfolio_run`. In the fourth year's step,
`reopen_restaffed_ventures` -> `open_venture` -> `node_output_market_factor` -> `solved_prices` asks for a node
set not solved before, and the solve sits in `sim/world/need_demand.py` (`clearing_with_glut`, `_polish_root`)
for longer than any test can wait: it was still solving after most of an hour under a sampling profiler, and a
shorter probe of the same run stalled at the same place. The suite now stops the topic at its time limit
(`python3 -m sim.tests --slow --only arrears_hours` reports it timed out).

Why it matters: a game that reaches that node set freezes for the player, and the topic's portfolio checks
(stranded concerns, automatic reopenings) cannot run. The run cannot be shortened to dodge the stall: after
three years most opened concerns are stranded and none has reopened, so the check needs the later years.

What it would take: reproduce the solve outside the game (record the gate nodes, civilisation, farmed area and
rate the stalled call receives, and call `prices.solved_prices` with them), then find why the need-demand
clearing does not converge for that set, and bound or fix its root search.

Related: 464.
