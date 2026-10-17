# Reported output is market turnover, not production, consumption or welfare

**Status:** open

Found by an outside reviewer reading the repository; checked against the code.

- `sim/engine/real_output.py` values the quantity markets sell at fixed opening prices. A household that
  stops growing its food and buys the same amount raises real output without eating better; one that
  goes back to its plot lowers it.
- The live economy reaches it partly: the agent-volume bridge in `sim/engine/economy_port_year.py`
  tracks goods from techniques introduced after the opening.
- No report separates physical production, intermediate use, final consumption, investment,
  inventories and self-consumption, or shows food adequacy and purchasing power by cohort.

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
