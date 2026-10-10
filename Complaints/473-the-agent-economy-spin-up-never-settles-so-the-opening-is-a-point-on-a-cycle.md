# The agent economy's spin-up never settles, so the opening is a point on a cycle

**Status:** open

Found while tracing why the opening money wage moved several-fold between builds of the same branch (the
fix for that is in `Complaints/closed/470`). The price level in the hidden spin-up cycles with a period of
about twenty-five years (one Rome trace: about 0.94 at the start, 2.7 a dozen years on with the interest rate
over twenty per cent, back near 1 by year twenty-four), the first stage does not meet its convergence tolerance
within its years, and the game opens wherever the cycle stands. Unrelated changes (a producer's expansion rule,
the smoothing bound) moved the opening price level and the money wage by a large factor through that alone.

The cause is not households' opening money: they open at their cash-balance target, the producers' working
capital passes to them in the first year whatever the opening cash was, and scaling households' opening cash
or income up or down on the small fixture (`sim/tests/economy_fixture.py`, which cycles the same way) changes
nothing. The mismatch is between the opening income, which assumes every worker is employed all year at the
opening wage, and producers sized to a much smaller final demand: realised income is a fraction of the opening
figure, and producers' expansion and hiring against idle labour drive the cycle.

Why it matters: every price, wage and purse a player sees at the opening depends on where the cycle stops,
so a small change to any mechanism can move the whole opening economy, and a measurement taken at the opening
says little about the mechanism measured (CLAUDE.md 4.2: the baseline should be a plausible draw, not an
accident of when the warm-up stopped).

Evidence: build a game with `sim.tests.harness.sim(capital=400000.0)` and print `game.capital` (the founder's
purse is repriced by the opening money wage, `sim/engine/opening_money.py`) on two builds that differ only in
an unrelated rule; print the spin-up's price level, households' cash over the wealth they keep, and spending
over income by spin-up year (no committed command prints these).

What it would take: an opening whose producers' capacity, workforce and households' income agree (sized from
the same final demand), and a model of how fast producers expand and hire against idle labour that damps rather
than overshoots; then a spin-up that runs until its tolerance is met, or records plainly when it is not.

Related: 470 (closed), 472 (closed), 464.
