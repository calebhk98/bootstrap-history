# Lenders ask nothing for what their money earns elsewhere or for default, so the rate clears at zero

**Status:** open

- Households lend their working-capital funds at `max(0, expected_inflation)` (`sim/economy/lending.py`, the
  `FundsOffer` built in the offers list): no time preference, no expected loss, no return of the alternative asset.
- `credit.clear` (`sim/economy/credit.py`) moves the rate to the clearing point and floors it at zero, and drops it to
  the target at once when funds sit idle (`_funds_idle_above_clearing_rate`). With funds offered far above loans asked,
  the clearing point is the lowest ask, so the rate is zero (PR #60's decision 1; 527).
- A bank asks its depositors' rate plus a fixed margin (`BANK_MARGIN_SHARE_OF_OPENING_RATE`, `sim/economy/banks.py`),
  with no link to its capital or its losses.

So a lender accepts a loan that cannot cover its own defaults, and no rule makes it refuse. That breaks the principle
that every price is one both sides would agree to (here the lender would not).

Sources (`Complaints/reports/research-pre-modern-interest-rates.md`, every claim with its URL): pre-modern rates were
stable for decades (Roman Egypt at the usual rate over a century and more; England's rent charges by Clark) and no case
near zero was found; the floor is the return on the alternative asset (land rent over its price, or public debt where
it exists); default risk is priced (crown against private lending). No source was found for a loan-running cost or for
hoarding as a floor, so those are not to be added as sourced terms. Model designs (`research-agent-based-economy-design.md`):
Caiani et al. 2016 tie the bank's rate to its capital ratio, Lavoie raises the spread after defaults; none lets a glut
of savings clear the rate to zero.

What it would take: a lender's lowest ask is the best return of its alternatives (its own time preference, the land
yield of the tiles it can buy in, public debt where a state sells it) plus its expected loss from the defaults it has
seen; a bank's spread follows its capital ratio and its loss record. Needs land buyable at a price (538, 551) for the
land yield. Tests call the ask and clearing functions with built offers: a glut leaves the rate at the lenders' floor,
not zero; a lender with past losses asks more.
