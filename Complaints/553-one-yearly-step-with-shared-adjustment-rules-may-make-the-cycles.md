# One yearly step with shared adjustment rules may make the cycles

**Status:** open

Found by an outside reviewer reading the repository; checked against the code.

`Economy.step` (`sim/economy/economy.py`) runs producers' plans, the labour market, households' orders,
the goods markets and then every producer's adjustment, once a year, with the same rules for all.
A chain can buy inputs and sell downstream output within the year, while merchants deliver into the
next. Many producers can expand after the same good year and contract together after the glut, which
may be where the spin-up's oscillation (473) gets its size and period, rather than from the economy.

## What it would take

- A sensitivity test before reading cycles as findings: run the controlled Rome spin-up (fixed
  population and technology, no shocks) with adjustment speeds and the phase order changed modestly,
  and report whether the period and amplitude change a lot.
- Explicit timing inside the year where it matters: planting and harvest, production, sale, payment,
  construction, delivery. A few seasonal phases behind the yearly interface may be enough (494 covers
  mods adding phases).
- Different adjustment speeds or expectations per producer, so reactions are not all in step.

Evidence (`economy_innovator_pricing`): after an entrant arrives the price alternates up and down a year
apart, and the largest year-to-year rise sits close to the test's limit in every variant measured,
including the code before 546 and with the sellers' strategic pricing turned off. The alternation is in
households: lumpy dividends and a budget set from last year's price swing the year's spending. Print the
path with `python3 -c "from sim.tests.test_economy_innovator_pricing import rows; [print(r) for r in rows()]"`.
