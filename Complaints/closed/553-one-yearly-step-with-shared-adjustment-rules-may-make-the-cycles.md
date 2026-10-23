# One yearly step with shared adjustment rules may make the cycles

**Status:** closed - measured: the spin-up's cycle comes from the economy (lagged expectations, capacity and credit loops), not from the shared yearly step; the open work is 473

Found by an outside reviewer reading the repository; checked against the code.

## Question

`Economy.step` (`sim/economy/economy.py`) runs plans, the labour market, orders, the goods markets and every
producer's adjustment once a year with the same rules for all, so many producers could expand and contract in
step and give the spin-up's oscillation (473) its size and period.

## Measured (small fixture)

250 years of the small fixture, first 60 skipped as the opening transient. The table was measured before the check
became a measurement; the fixture series is no longer shipped and one constant it scaled
(`UNSOLD_ASK_MARKDOWN_SHARE`) no longer exists, so a rerun differs. Price level (log): drift per year, amplitude
(standard deviation of the log around its trend), period (best-fitting sinusoid, years).

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

## Where the rest lives

- The cycle and what sets it: 473 (the spin-up never settles).
- Rerun on Rome on demand (many minutes, one process at a time): `python3 sim/simulator.py spin-up-sensitivity --civ rome_100ad --years 100 --skip 30` (`--variants` picks some). The rules behind it: `python3 -m sim.tests --only spin_up_sensitivity_rules`.
- Within-year timing (planting, harvest, delivery) behind the yearly interface is a modelling extension, not a cause found here; the phase registry (494, closed) is where mods add phases.
- Evidence kept from `economy_innovator_pricing`: after an entrant arrives the price alternates up and down a year apart in every variant measured. The alternation is in households (lumpy dividends, a budget set from last year's price). Print the path: `python3 -c "from sim.tests.test_economy_innovator_pricing import rows; [print(r) for r in rows()]"`.
