# The lending rate sits at its ceiling for decades because a lender's losses never age

**Status:** closed - an aging loss rate; the Rome trace of 4affa365 leaves the ceiling

A 60-year Rome spin-up trace of b9ccb70b (`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`, run in a
pinned worktree) has the market rate at its ceiling (`bounded_rate`, four times the starting rate) from year 8 to year
60, while the price level and the wage fall every year.

Likely rule, read and not yet tested: 641's lender ask adds `lender_ask.loss_rate(losses, claims)`, which divides the
lender's lifetime `record.credit_losses` (a stock that only grows; `lending.py`, `bank_service.py`, `debt_relief.py`
add to it) by those losses plus the claims it still holds. A lender that lost once and has since been repaid asks a loss
share near one for ever. 653's margin call makes more borrowers default, which feeds the stock. The ask is then above
every borrower's ceiling and the clearing sits at the cap.

What it would take: an expected loss that is a rate per year of exposure and ages, for example losses booked in a year
over what the lender had lent that year, carried as a smoothed figure in the record; test `loss_rate` as a function:
a lender that lost once long ago and has lent cleanly since asks no more than its floor plus a small remembered share;
a lender losing every year asks more. Then re-run the trace.

## Fix

`record.credit_losses` stays the lifetime stock (money audit, accounts; writers in lending, bank_service, debt_relief,
bondage, producer_exit). A new `record.loss_rates` (and `losses_seen`, the stock at the last close) holds each lender's
expected loss per year of exposure: `loss_memory.age`, called at the end of `lending.service`, blends the year's losses
over the year's exposure (lost plus still owed) into the remembered rate by `LOSS_RATE_SMOOTHING_SHARE` (a labelled
heuristic, retire named). `lender_ask.loss_rate`, `CreditView.loss_rate`, `lending.lend_working_capital` and
`banks.spread_of` / `bank_spread.spread` read the smoothed rate. Under the old rule a lender that lost once and was
fully repaid asked a loss share of 1.0; tests in `sim/tests/test_economy_lender_ask.py` (AgingTests) cover fading,
repeated losses, no losses and a clean glut. Still to do: the 60-year trace.


## Confirmed on Rome (4affa365)

`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60` in a worktree pinned at 4affa365: the rate no longer sits at
the ceiling (it moves between about zero and a third of the ceiling); the wage falls more slowly and levels off over the
last decades; hired hours recover to about a third to two fifths of the opening's. The rate still touches zero in
deflating years (the household floor is time preference plus expected inflation, floored at zero), and the opening's
collapse (473, issue #61) remains.
