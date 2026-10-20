# The lending rate sits at its ceiling for decades because a lender's losses never age

**Status:** open

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
