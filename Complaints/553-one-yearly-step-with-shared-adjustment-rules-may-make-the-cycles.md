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

## Measured (fixture)

Command (the table below was measured before the check was turned into a measurement; the fixture series is no longer
shipped, and one of the "ask_prices" constants it scaled, `UNSOLD_ASK_MARKDOWN_SHARE`, no longer exists, so a rerun
differs): 250 years of the small fixture, first 60 skipped as the opening transient. The pass or fail test
`spin_up_sensitivity` is deleted (640); the rules under it are `python3 -m sim.tests --only spin_up_sensitivity_rules`. Price level (log): drift per year, amplitude (standard deviation of the log around
its trend), period (best-fitting sinusoid, years).

| variant | drift | amplitude | period |
|---|---|---|---|
| baseline | +0.0035 | 0.228 | 17.5 |
| producer plans x0.5 (expansion, output change, expectation) | +0.0042 | 0.242 | 14.5 |
| producer plans x2 | +0.0022 | 0.147 | 23.8 |
| ask prices x0.5 (markdown, raise, usual-price speed) | +0.0035 | 0.281 | 80.8 (slow wave) |
| ask prices x2 | -0.0051 | 0.225 | 13.8 |
| interest rate speed x0.5 / x2 | +0.0022 / +0.0019 | 0.230 / 0.174 | 18.8 / 23.0 |
| all speeds x0.5 | +0.0017 | 0.226 | 16.5 |
| all speeds x2 | +0.0031 | 0.157 | 34.3 |
| per-producer speed, +-50 per cent, seed 1 / 2 | +0.0012 / +0.0013 | 0.182 / 0.204 | 15.0 / 25.0 |
| wage tightness speeds x0.5 / x2; exit before entry | identical to baseline: no effect on the fixture (no entrants or closures; tightness never binds) | | |

Reading: no variant removes the cycle. The amplitude stays within a factor of two of the baseline (0.15 to
0.28) and heterogeneous producer speeds trim it by only a tenth to a fifth. The period does move with the
speeds (14 to 34 years), as it would for any delayed-feedback loop. So on the fixture the cycle comes from
the economy (lagged expectations, capacity and credit loops), not from the shared yearly step alone. The
fixture has few producers, so per-producer heterogeneity is a weak test there. The Rome opening takes
minutes a variant; run it on demand: `python3 sim/simulator.py spin-up-sensitivity --civ rome_100ad --years 100 --skip 30`
(many minutes; one process at a time; `--variants` picks some).
