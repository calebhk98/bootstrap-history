# A foreign economy's output and demand are the home society's, scaled by population

**Status:** closed - a foreign economy's capacity comes from its own regions, techniques and households; what still limits it is filed as 482

A foreign economy named in `data/world/foreign_economies.json` opens each
commodity at the home society's reference output times the population ratio,
with its household demand equal to that capacity (labelled
`FOREIGN_CAPACITY_PER_HEAD_OF_HOME` in `sim/engine/foreign_economies.py`). Its
own mines, farmland and workshops are not read from its regions, so the
partner cannot be rich in what its geology holds and poor in what it lacks.

## Evidence

Run `python3 sim/test_regressions.py --only foreign_economy_trade` for the
rules, and read `foreign_trade_summary()` after some years of a Rome game for
the tonnages. The flows of goods such as platinum and wool follow the home
reference tonnes, which are generic estimates for materials the resource table
does not name.

## What it would take

Give a foreign economy the same mineral and land inputs the home society has
(`sim/engine/geography.py`, `sim/world/land.py`) from its own `home_regions`,
and its own household demand from its population and income (`Complaints/102`).

## Resolved

`sim/engine/foreign_capacity.py`: a mined commodity's capacity is the national
output times the partner's own regions' mineral shares (`data/world/geography.json`);
any other good is made only where the partner holds a technique for every step
of its chain and every ore deposit on the chain lies in its regions, and then
opens in balance with its households' demand (their population and income at
the partner's own solved prices, held to the income they have). A material it
cannot make has no capacity and is only bought. `FOREIGN_CAPACITY_PER_HEAD_OF_HOME`
is gone. Tests: `python3 sim/test_regressions.py --only credible_foreign_trade`.
Measure: `python3 sim/foreign_trade_report.py`.
