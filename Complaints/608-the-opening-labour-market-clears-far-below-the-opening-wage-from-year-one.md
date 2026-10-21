# The opening's labour market clears far below the opening wage from year one

**Status:** open - on the small fixture the stated wage is above the clearing wage whenever hours offered exceed hours hired, and scaling prices with it does not help (473 Update 6); measured cause is the opening's demand for hours (a stock glut, traced in 473 and 545), not the wage anchor the first title named

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

Related: 473 (the labour market clears far below the cost-table wage; the demand-side stock glut measured below is traced there), 545.

**What is wrong.** (The first reading, that the opening wage is anchored on the coin metal's table cost and not on labour's product, was not borne out: see Measured.) The labour market clears at the households' outside option, far below the cost-table wage, from the first year; prices follow slowly, so the wage and price level fall for decades. Rome's unskilled wage ends below its floor.

**Evidence.** `wage_schedule`; `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`. The savings leak was measured not to be the cause of the wage collapse.

**Why it matters.** Every number a player sees depends on when the spin-up stopped (CLAUDE.md 4.2).

**What it would take.** Opening demand for hours that agrees with year one's (545, 473), and an opening wage that is the value of labour's marginal product, consistent with the households' outside option, so the labour market clears near the opening wage in year one.

**Test.** A test: the year-one clearing wage is within a band of the opening wage on Rome and a small fixture; Rome's unskilled wage stays above its floor over the first decade of `spin-up-trace`.

## Measured: the glut is a demand-side stock glut, not a wage-setting gap (branch 473-why-so-few-hours-are-hired)

On the Rome first stage employers' labour bids are close to the hours hired (vacant under 5 per cent of hired); the
unhired hours are those the market has no demand for, because producers sized at the opening hold stock many times their
sales and cut runs to work it off (see 473, "where the unhired hours are"). A higher opening wage would only rescale
prices, as the rescaling branch showed. The test this complaint asks for (year-one clearing wage near the opening wage)
needs the opening's final demand to agree with the own-plot growing of year one (545) first.

## Update: hours offered by choice (473 Update 7)

With households choosing hours against their plot (`households_hours_offered.py`) and the fixture's hours equal to
hired plus kept, the stationary fixture's year-one wage moves by 3 per cent (not a third). The stated fixture still
clears at the survival wage: it has no plot or household work to use the hours. The opening wage is still the cost
table's; seeding it where hours offered equal hours hired is not done.
