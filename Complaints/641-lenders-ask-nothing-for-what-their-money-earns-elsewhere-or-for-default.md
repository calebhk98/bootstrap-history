# Lenders ask nothing for what their money earns elsewhere or for default, so the rate clears at zero

**Status:** partly - the lowest ask (time preference plus expected inflation, plus the lender's own loss record) and the bank's spread (loss record plus capital shortfall) are built; still open: the land-yield and public-debt alternatives are computed but have no live input (no title sale price, no state bond sold to households), see Done

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

## Done

- `sim/economy/lender_ask.py`: `lowest_ask` is the best of the lender's alternatives (time preference plus expected
  inflation, land yield, public yield) plus its expected loss rate; `loss_rate` is the share of the lender's credit
  exposure (what it lost plus what it is still owed) that went bad, read from `record.credit_losses`; `land_yield`
  is rent over title price, nothing where the land has no price.
- Households offer at that ask in both places they lend (`households_orders.py`, `lending.lend_working_capital`);
  `CreditView.loss_rate` gives orders the lender's record.
- `sim/economy/bank_spread.py`: a bank's spread is its loss rate plus `BANK_SPREAD_AT_NO_CAPITAL` times how far its
  capital ratio falls short of `BANK_CAPITAL_SHARE_OF_LOANS` (shape after Caiani et al. 2016 and Lavoie; the size is
  a labelled heuristic with `retire`). `BANK_MARGIN_SHARE_OF_OPENING_RATE` and `Bank.margin` are gone.
- No loan-running cost and no hoarding floor were added (no source).

## Open

- Land yield: no title is bought or sold at a price (`titles_value` capitalises rent at the live rate, so rent over
  that price is the rate itself, a circle). The land alternative stays unfed until titles trade (538, 551).
- Public debt: no state bond reaches the household lender's choice; `public_yield_available` stays unfed.
- Expected loss reads the loss share of exposure as a yearly rate; a lender that lost and then holds no claims asks
  the whole loss share. `RATE_FLOOR_SHARE` (capital_market) is a separate typed floor that this does not retire.

## Tests

`sim/tests/test_economy_lender_ask.py`: the floor, past losses, land yield, public yield, a glut leaving the rate at
the floor (`credit.clear`), a thin-capital bank and a bank with losses asking more (`banks.ask_of`), the view's loss
rate. `test_economy_banks.py` holds a bank with capital and no losses asking its depositors' rate.
