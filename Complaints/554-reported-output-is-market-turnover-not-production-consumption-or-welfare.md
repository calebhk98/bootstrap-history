# Reported output is market turnover, not production, consumption or welfare

**Status:** partly (the yearly accounts exist; baseline checks for feasibility and food eaten over need exist; bounded dynamics is checked only by the opening check `spin_up_settled`, which fails on main, see 970 and 473; responses and historical fit do not)

Found by an outside reviewer reading the repository; checked against the code.

- `sim/reporting/output.py` values the quantity markets sell at fixed opening prices. A household that
  stops growing its food and buys the same amount raises real output without eating better; one that
  goes back to its plot lowers it.
- The live economy reaches it partly: the volume baseline and traded volumes (`sim/reporting/output.py`, fed by the economy's `traded_volumes`)
  track goods from techniques introduced after the opening.
- No report separates physical production, intermediate use, final consumption, investment,
  inventories and self-consumption, or shows food adequacy and purchasing power by cohort.

## What exists

- `sim/economy/year_accounts.py` builds `YearOutcome.accounts` each year from the year's own book flows, the
  agents' stocks at the start and end, and the ledger (not from `sim/reporting/output.py`): per good, production (and the
  part households grew for themselves), intermediate use, final consumption split bought and grown, household
  durable wear, state use, plant built, spoilage, other edges (border, mint), stock change, the quantity the
  markets cleared, and `residual()`, which is zero when the flows explain the stock change. Plant that wore out
  is listed in the goods it is made of. Food eaten per head against the hunger need's floor (bought and own plot)
  by cohort and by tile, and each trade's real wage against the opening's basket, are included.
- Print it: `python3 sim/simulator.py economy-check --accounts --years N [--civs ID] [--session SAVE]`.
  The first run of a civilisation builds its spin-up (cached on disk afterwards).
- Tests: `python3 -m unittest sim.tests.test_year_accounts` (the fixture's identity, self-grown food outside market
  turnover, calories by cohort).

- Baseline checks on a controlled run (`sim/tests/baseline_checks.py`): `feasibility` of every year's accounts (uses within
  production plus inflow plus stock, flows closing, no negative stock) and `food_eaten_over_need` per tile. Tests:
  `sim/tests/test_baseline_checks_rules.py`. The earlier settling report (`sim/economy/settling.py`) and its topics
  `baseline_fixture` and `baseline_rome` no longer exist. What can be checked now for bounded dynamics (price level, unskilled wage,
  money stock, interest rate not drifting): `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60` and the opening
  check `spin_up_settled` (`sim/engine/opening_checks.py`, run by `python3 sim/simulator.py opening-checks`), which fails today (473, 970).
  Reproduction (stocks not eaten through, the mint replacing the coin that wears) has no check of its own now.
  Not built: sensible responses (harvest loss, blocked route, productivity gain) and historical fit.

## What it would take

- Accounts per year: production, intermediate use, final consumption (bought and grown), investment
  and depreciation, inventory change.
- By cohort and tile: calories eaten against need, real wage against a consumption basket.
- Baseline checks on a controlled run (fixed technology and population, no shocks), each a
  validation, not a target:
  - physical feasibility: production and carriage within land, labour, equipment and inputs;
  - reproduction: investment covers depreciation, food stocks and consumption are sustainable;
  - bounded dynamics: inventories, debt and real consumption have no unexplained trend;
  - sensible responses: a harvest loss, a blocked route, a productivity gain have explainable effects;
  - historical fit: several independent outcomes in defensible ranges, for example the real wage
    against a consumption basket (Allen's Roman wage work, matched to period and evidence).
- Related: 548 (the settled test checks prices only).
