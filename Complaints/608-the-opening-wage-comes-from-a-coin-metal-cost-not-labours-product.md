# The opening wage is anchored on the coin metal's table cost, not on what labour earns at the households' own work

**Status:** open

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

Related: 473 (the labour market clears far below the cost-table wage).

**What is wrong.** The labour market clears at the households' outside option, far below the cost-table wage, from the first year; prices follow slowly, so the wage and price level fall for decades. Rome's unskilled wage ends below its floor.

**Evidence.** `wage_schedule`; `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`. The savings leak was measured not to be the cause of the wage collapse.

**Why it matters.** Every number a player sees depends on when the spin-up stopped (CLAUDE.md 4.2).

**What it would take.** The opening wage is the value of labour's marginal product, consistent with the households' outside option, so the labour market clears near the opening wage in year one.

**Test.** A test: the year-one clearing wage is within a band of the opening wage on Rome and a small fixture; Rome's unskilled wage stays above its floor over the first decade of `spin-up-trace`.
