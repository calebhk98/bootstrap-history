# The agent economy's spin-up never settles, so the opening is a point on a cycle

**Status:** open

Found while tracing why the opening money wage moved several-fold between builds of the same branch (the
fix for that is in `Complaints/closed/470`). Households open the hidden spin-up holding many years of their
income in cash, well above the wealth they want to keep, so they spend about twice their income each year
while they draw it down. The price level then rises and swings for decades: the first spin-up stage does not
meet its convergence tolerance within its years, with or without the spending smoothing, and the game opens
wherever the swing happens to be. Unrelated changes (a producer's expansion rule, the smoothing bound) moved
the opening price level and the money wage by a large factor through that alone.

Why it matters: every price, wage and purse a player sees at the opening depends on where the cycle stops,
so a small change to any mechanism can move the whole opening economy, and a measurement taken at the opening
says little about the mechanism measured (CLAUDE.md 4.2: the baseline should be a plausible draw, not an
accident of when the warm-up stopped).

Evidence: build a game with `sim.tests.harness.sim(capital=400000.0)` and print `game.capital` (the founder's
purse is repriced by the opening money wage, `sim/engine/opening_money.py`) on two builds that differ only in
an unrelated rule; print the spin-up's price level, households' cash over the wealth they keep, and spending
over income by spin-up year (no committed command prints these).

What it would take: households' opening money set from the wealth they want to keep at the opening's income
and interest rate (an initial condition derived from the model rather than a round multiple of income), so
the spin-up starts near its own steady state; then a spin-up that runs until its tolerance is met, or reports
plainly when it is not.

Related: 470 (closed), 472 (closed), 464.
