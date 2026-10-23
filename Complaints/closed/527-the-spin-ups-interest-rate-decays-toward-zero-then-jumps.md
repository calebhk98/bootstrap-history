# The spin-up's interest rate decays toward zero, then jumps

**Status:** closed - superseded by 641 (lenders ask nothing for what their money earns elsewhere or for default); causes 547 and 548 are closed

Found measuring 507 Stage 7: in a spin-up the market interest rate fell by the same share each year toward zero and then
jumped by a large factor in one year, and that jump accounted for most of the spin-up's failure to settle in the last
year (`game.economy.spin_up_result()` gaps; `python3 sim/simulator.py opening-checks`).

Findings: clearing used ceilings below zero from requests that cannot borrow (547, closed). With no requests the rate
still decays by the sticky share toward the lowest ask, which is `HOUSEHOLD_TIME_PREFERENCE` plus the saver's expected
inflation, floored at zero (`households_orders.py`); while the spin-up's price level falls (473, 526) the ask is zero,
so a drift to it is the funds market answering deflation. The jump is the same rate moving off a near-zero base,
large only as a ratio (548, closed).

Remaining work is 641: the lowest ask carries no alternative return and no expected loss, so a glut of funds clears at
zero. Re-measure the rate's path after the opening is fixed (526, 545) and 641 lands.
