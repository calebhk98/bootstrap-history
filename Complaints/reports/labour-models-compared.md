# Labour markets of four reference models, run here, against ours

> **Checked against the code (2026-11):** the "Ours, Rome" row first read 92% unsold, a 64-81% people-based rate and 40 years;
> none of these is in the cited `rome-unemployment-audit.md`, which runs 16 years (year 15: 0.888 of hours unsold, person-equivalent
> 0.86). The row now carries the audit's figures. Those figures are from an earlier build, predate the A1/A2 fixes of Complaint 964 and were not re-measured.

Each model was obtained, built and run in this session; its rules were read from the code that ran (file and line in
its own report). Reports: `model-run-bam.md`, `model-run-lengnick.md`, `model-run-mark0.md`, `model-run-jmab.md`.
Ours: `rome-unemployment-audit.md`. Measured unemployment is the run's own, not the paper's.

## Measured unemployment

| Model | From its start | Long run | Run here |
|---|---|---|---|
| BAM (BAM Engine, MIT) | near zero, rising over the burn-in | 5-6% when counted at production; 15-19% when counted after contracts expire | 1000 periods, 3 seeds |
| Lengnick 2013 (newwayland replication, AGPL) | 100% to 0% in about ten months | about 0.4% | 1200 months, 3 seeds |
| Mark-0 (KarlNaumann, MIT) | 50% to about 0.4% when hiring outpaces firing | about 0.4%, but a bankruptcy cascade can tip it to 80-98% | thousands of periods, several seeds and settings |
| Caiani benchmark (JMAB) | exactly 8% by calibration | 5-9%, mean about 7.5% | 400 quarters, seed 1 |
| Ours, Rome | 52% of offered hours unsold | 0.888 of offered hours unsold at year 15; person-equivalent unemployment 0.52 at year 0 to 0.86 at year 15 (`rome-unemployment-audit.md`) | saved opened economy, 16 years |

## How each sizes and fills jobs

| | Labour supply | Labour demand | Matching | Reservation wage |
|---|---|---|---|---|
| BAM | one indivisible unit per household | output wanted from last period, moved by at most a tenth on stock and price; head count ignores the wage | unemployed visit a few firms; fixed-length contracts | none: any offer is taken |
| Lengnick | one unit per household | open a vacancy when stock is below a share of sales, fire one when above; one change a month | households sample firms and take the first open vacancy above their ask | starts at zero, falls while unemployed, rises to the wage paid |
| Mark-0 | one unit, no agents | hire a share of last period's demand gap, fire a share of the excess; hiring faster than firing gives full employment | none: a hiring firm takes its share of the unemployed | none |
| Caiani | one unit per household | expected sales plus an inventory gap, through fixed capital-labour coefficients; wage not in the head count; 5% random dismissals a period | each firm sees ten unemployed and hires the cheapest ask, unconditionally, until filled | moves about 0.7% a quarter; the code's test for cutting it is inverted against the paper |
| Ours | hours a household has after its plot and household work (about 680 a year at the opening on Rome) | planned runs from expected sales and the margin at live wages (`producers.plan`, `share_working`), bid in falling tranches (`labour_bids.py`) | search rounds with bounded applications; offers rise while vacancies stay open (`applications.py`) | subsistence and plot-return floor (`labour_ask_floor.py`) |

## What the comparison says about ours

1. All four reference models have every person in one indivisible unit of labour that is either employed or not, no
   home production, and no wage floor that binds. Their unemployment is a share of people seeking wage work. Ours counts
   hours households offer after their plot and household work, in a society that is nearly fed: on Rome a large part of
   the idle hours are the plot trade's, with no market use (the surplus-selling test in Complaint 961). Part of our
   high figure is a measure of hours with nothing to buy them, which none of the reference models has.
2. In all four, labour demand follows the goods demand gap quickly and nothing stops a firm from making what it hires
   for: one good, or no input chain. Ours has input chains, and on Rome producers' runs fail for missing inputs (heat,
   vegetables, millet, olives, amphorae, lead) while food demand stands unmet; hours wanted then fall 78% while hours
   offered stay flat (the audit). None of the reference models can show that failure.
3. Caiani's and BAM's single-digit figures are partly choices: Caiani's is set by calibration and its labour market
   clears completely each period; BAM's depends on counting after the period's hiring. Lengnick's and Mark-0's near
   zero comes from one unit per person, no floor, and fast demand-driven hiring.
4. What to borrow, and what we tried: demand-gap hiring (merged: sellers see all unmet demand, capacity grows toward
   paying demand, the year's change counts from the runs the hired crew could staff); a people-based rate reported
   beside the hours figure (merged). Not borrowed: a zero reservation wage (a peasant does not sell labour below what
   his plot returns), calibrated unemployment (CLAUDE.md 4.1).
