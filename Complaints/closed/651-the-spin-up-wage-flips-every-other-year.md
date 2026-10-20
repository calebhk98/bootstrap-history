# The spin-up's wage flips every other year

**Status:** closed - the wage step scales with the market's imbalance; a 60-year Rome trace of b9ccb70b shows no alternation

A 60-year Rome spin-up trace (`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`) shows the unskilled
wage alternating year by year from about year 18: a low year, then a year several to many times higher, then low again,
for decades. A two-year alternation means a yearly adjustment that reacts to last year's value with a gain above one
(a cobweb), not a slow cycle.

Candidates, each a rule to test as a function on built inputs: the labour market's wage step against last year's
vacancies or unhired hours (`sim/labour/market/clearing.py`); households holding back hours for their own plots by last
year's wage (`sim/economy/households_own.py`, `withhold_hours`, now limited to held land, 551); producers' hiring sized
by last year's prices and sales (`sim/economy/producers*.py`, `labour_bids.py`).

What it would take: reproduce the alternation on the small economy fixture (`sim/tests/economy_fixture.py`) or a built
two-market case, find the rule whose response to its own last value overshoots, and damp or derive it. Test: under a
constant setting the rule's year-on-year response has gain below one, and the fixture's wage does not alternate.

## Finding

Reproduced on the small economy fixture (`economy_fixture.run(small_setup(), years=70)`, under a second): the
labourer wage in one area saw-toothed (more than a quarter of year-on-year changes flipped sign) and another fell by
nearly a third in a year, with nothing changing in the setting. The rule was the wage step in
`sim/labour/market/clearing.py` (`market_wage`). Its target (`clearing_target`) is discontinuous in the hours wanted:
with supply at the ask, wanted hours just under the offered give the ask, and just over give about the bids' maxima,
which sit far above the wage. A step that closes a fixed share of the gap to that target therefore moves the wage by
a share of the whole jump for a sliver of imbalance, and the hours wanted (producers plan from last year's wage)
cross the offered hours back and forth. The other candidates were not the cause: asks stayed at one in the trace of
the fixture, and own-plot withholding did not move.

Fix: the share of the gap closed is scaled by the imbalance at last year's wage (`pressure`: the share of offered
hours unwanted or wanted beyond them, capped at one), so the step is continuous across balance. Test:
`sim/tests/test_complaint_651_wage_step_gain.py` (continuity of the step, gain of next wage on last wage below one
when demand follows the wage, no saw-tooth in the fixture). The scaling stands in the same temporary heuristic as
`WAGE_SHARE_CLOSED_PER_YEAR`; the derived response is a supply curve that slopes (workers' asks spread), not built.


## Confirmed on Rome (b9ccb70b)

`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60` in a worktree pinned at b9ccb70b: the unskilled wage falls
smoothly every year (no year-on-year alternation). The trace shows a different defect, filed as 655.
