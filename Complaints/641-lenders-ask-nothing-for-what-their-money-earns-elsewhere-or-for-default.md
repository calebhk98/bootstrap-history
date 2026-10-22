# Lenders ask nothing for what their money earns elsewhere or for default, so the rate clears at zero

**Status:** partly - the credit bound is now on the real rate with quantity rationing by risk (see Changes after the probe; re-measured: credit now clears at the opening, at a nominal rate that follows the runaway expected inflation of 473), the lowest ask (time preference plus expected inflation, plus the lender's own loss record) and the bank's spread (loss record plus capital shortfall) are built; still open: the land-yield and public-debt alternatives are computed but have no live input (no title sale price, no state bond sold to households), see Open

**What was wrong.** Households lent at `max(0, expected_inflation)`, `credit.clear` (`sim/economy/credit.py`) floored the rate at zero
and dropped it to the lowest ask when funds sat idle, and a bank asked its depositors' rate plus a fixed margin. So a
lender accepted a loan that could not cover its own defaults, which breaks the principle that every price is one both
sides would agree to.

**What is built.**

- `sim/economy/lender_ask.py`: `lowest_ask` is the best of the lender's alternatives (time preference plus expected
  inflation, land yield, public yield) plus its expected loss rate; `loss_rate` is the share of the lender's credit
  exposure that went bad (`record.credit_losses`); `land_yield` is rent over title price, nothing where the land has no price.
- Households offer at that ask where they lend (`households_orders.py`, `lending.lend_working_capital`).
- `sim/economy/bank_spread.py`: a bank's spread is its loss rate plus `BANK_SPREAD_AT_NO_CAPITAL` times how far its capital
  ratio falls short of `BANK_CAPITAL_SHARE_OF_LOANS` (shape after Caiani et al. 2016 and Lavoie; the size is a labelled
  heuristic with `retire`).
- No loan-running cost and no hoarding floor were added: no source found for either
  (`Complaints/reports/research-pre-modern-interest-rates.md`; pre-modern rates were stable for decades, none near zero).
- Tests: `sim/tests/test_economy_lender_ask.py`, `test_economy_banks.py`.

## Open

- Land yield has no live input: no title is bought or sold at a price (`titles_value` capitalises rent at the live rate, so
  rent over that price is the rate itself, a circle). It needs titles that trade at a price (538, 551).
- Public debt: no state bond reaches the household lender's choice, so `public_yield_available` stays unfed.
- Expected loss reads the loss share of exposure as a yearly rate; a lender that lost and then holds no claims asks the
  whole loss share. `RATE_FLOOR_SHARE` (capital_market) is a separate typed floor that this does not retire.
- The opening rate in the default game reads at the lenders' ceiling, and at that rate `NicheEntry.found` rejected every
  concern tried, so no firm entered in the default game. Two causes were fixed (665: an idle plant's request for more
  plant, and the lender reserve never held), and seats' credit lines now join `credit.clear`. Measured after those: Measured 2026-10-21 on main 3cb9c9a0, an opened Rome game with the full spin-up: from a checkout root, `from sim.tests import harness; import os; os.environ.pop("ROME_SPIN_UP_YEARS", None); game = harness.sim(capital=1e7)`, then the reads named below. `game.economy._answering_agent().economy().record.memory.rates` still reads
  the lenders' ceiling, so the 665 fixes did not bring it down. Cause, measured by wrapping `credit.clear` and stepping that game one year
  (probe: `Complaints/reports/641-rate-probe.md`): every household cohort's `expected_inflation` reads far above the time
  preference, so every lender's lowest ask (`lender_ask.lowest_ask`: time preference plus expected inflation plus remembered
  loss) is above the ceiling (`capital_market.RATE_CEILING_SHARE` times `setup.opening_rate`, a nominal rate). Funds offered
  exceed requests several times over, yet `credit.clear` lends nothing: the rate is clamped to a ceiling no lender accepts, and
  every request is left unmet. Borrowers' caps are also unbounded (the largest caps run to many times a hundred per cent).
  Rule tests of the three shapes (rationed caps above the ceiling, the ask above it, a clamp with no clearing point):
  `sim/tests/test_economy_credit_rate_at_ceiling.py`.

  Two defects meet here. (1) Expected inflation is read from a price level that runs away while the opening does not settle
  (473, GitHub #61), so the opening's lenders expect a large yearly inflation. (2) The ceiling is nominal: under high expected
  inflation it shuts the credit market instead of bounding a rate. Realistic rules (`Complaints/reports/research-reference-economy-models.md`:
  Eurace, Caiani et al.) price the loan rate from the lenders' side (an ask plus a default premium, a spread that widens as
  bank capital thins) and ration by quantity and risk when demand exceeds funds; a bound, if kept, applies to the real rate.
  What it would take: the ceiling on the real rate (or removed, with rationing by quantity), expected inflation read from a
  settled index (473), and borrowers' caps bounded by what a loan can earn. `NicheEntry.found` should compare an entrant's
  return with the lenders' ask plus the loss premium, not the clamped rate. A default game in which no firm can ever enter is a defect, not a setting;
  `test_firm_entry_default_game_scenario` checks placement without a founding.

**What it would take.** Feed the two alternatives (titles at a price, a state bond reachable by households), re-measure the
opening rate, and retire `RATE_FLOOR_SHARE` if the lenders' floor now does its job. Tests call the ask and clearing
functions with built offers: a glut leaves the rate at the lenders' floor, not zero; a lender with past losses asks more.

## Changes after the probe (credit-real-rate-and-rationing)

- `credit.clear` (`sim/economy/credit.py`) bounds the real rate: `rate_ceiling` plus the `expected_inflation` the economy passes
  (`lending.expected_inflation_of`, people-weighted cohort expectations). Where the bound holds the rate below the clearing point,
  funds go to the least risky borrower first (premium: leverage, collateral, arrears), the rest is left unmet. When every offer
  asks more than the bound, `credit.clear_with_cause` returns `cause == no_offer_at_rate`, no loans and the held rate (the lowest
  ask when there is none), never the bound.
- Caps (`credit.earnable_rate`): producers' working capital and plant, entrants, merchants, carriage and households ask at most
  what the loan earns on their own figures; a missing or non-finite figure is a zero cap, not an unbounded one. The typed
  `HOUSEHOLD_RATE_CEILING` is retired. The state's cap (`STATE_BORROWING_RATE_CEILING_MULTIPLE`) and credit lines are unchanged.
- `NicheEntry.found` prices the stake with `entry_round.capital_cost` (a loan costs at least the market rate).
- Tests: `test_economy_credit_rate_at_ceiling.py`, `test_economy_credit_real_rate.py`, `test_economy_credit.py`.
- Still open: re-measure the opening rate on an opened Rome game (snippet in the hand-off; the expected inflation read from the
  unsettled price level is 473's). `capital_market.market_rate_answered` still bounds the engine-facing rate nominally
  (`bounded_rate` takes `expected_inflation` but `economy_capital_market.market_rate` does not pass it); `no_offer_at_rate` is
  returned but not stored on the record.

## Re-measured after the real-rate bound (2026-10-21)

Probe: `Complaints/reports/641-rate-probe.md`, with the spy on `credit.clear_with_cause` and loans summed by `principal`, on an
opened Rome game with the full spin-up at the merge of the real-rate change. The working-capital clearing now lends a large share
of the funds offered (before: nothing), with borrowers rationed by risk; the second clearing still returns `no_offer_at_rate`
when its few lenders ask above what borrowers can pay. The nominal rate is above one hundred per cent a year because cohorts
expect inflation of that order: the credit rules now pass expected inflation through as they should, and the level itself is
473's runaway price index. Borrowers' caps are still very large because revenue over cost is, at runaway prices. No firm had
entered in the measured year (`game.actors.active_firms()`). What is left here: the land-yield and public-debt inputs; the
engine-facing `economy_capital_market.market_rate` still clamps nominally; the clearing's cause is not yet stored on the record
or shown. The rate's level closes with 473.

## Rome's opening rate at the ceiling: cause found (2026-10-22)

The ceiling was not the lenders' ask: households had no savings to offer, because the hire rule priced household work at the
servant's wage while they paid the service's price (645, last section), so the second clearing had funds of about a millionth of
requests. With the rule reading the price, Rome's households offer savings and the opening rate is 0.016 (command in 645). The
scarcity wage (8e354ebe) moved the rate only from 0.126 to 0.147; the wage bound in `sim/labour/market/scarcity.py` is not the cause.

## Open after the household-service fix (PM, 2026-10-22)

- Rome's `market_rate()` reads 0.016 after the fix, while the trace's own credit clearing showed rates of about 0.07 with
  lenders asking a median of about 0.17. Which figure `market_rate()` reports (which clearing, nominal or real) and why it
  sits below the lenders' ask is not yet checked.
- The domestic service good priced at several times the servant's wage (about nine at 1cd50f79, about three at the tip,
  against a wage under one half) is a seller's markup the ask band (643) or the opening (473) should explain.

## What `market_rate()` reports, and why it sat below the asks (2026-10-22)

Probe: `Complaints/reports/641-rate-probe.md` (probe 3, a spy on `credit.clear_with_cause` and on the no-request drift, run with
`ROME_CACHE_DIR` pointing at an empty directory so the cached spin-up does not hide the clearings).

What it reports: `Sim.market_rate` -> `economy_port.agent_rate` -> `api.interest_rate` -> `record.memory.rates[currency]`. That is the
economy's memory, the nominal base rate (before each borrower's risk premium) of the last `_lend` clearing of the spin-up, the
year's second clearing. The first clearing (`lending.lend_working_capital`) discards its rate and writes nothing to memory, so the
rate comes from the smaller clearing: a year's few plant and entry requests, not the bulk of the year's loans. It is a marginal
rate (the clearing point, moved by `RATE_ADJUSTMENT_SHARE_PER_YEAR`), not a loan-weighted average, and not a real rate.

Why it sat below the median ask: the median ask is not the clearing price; the marginal lender's is. Three causes, measured:

1. Glut: where the cheapest lender's funds cover the whole request (England: the cheapest ask funds many times the demand), the
   rate is that lender's ask, far under the median. This is a clearing price. (Households that expect deflation ask only their
   loss rate, since the ask is floored at zero nominal.)
2. Stickiness one way only: a rate falls to the clearing point at once when funds sit idle, but rose only by a share of the gap.
   Rome's final clearing, before the change, stood at 0.0255 after a last rate of nil: the lenders asking no more than that held a
   small share of the request (the probe's `funds_at_rate` against `asked`), so borrowers who would pay more were rationed. Fixed: the rate lifts to the clearing point when
   borrowers who would pay it ask for more than the lenders at or under the held rate hold
   (`credit._borrowers_rationed_below_clearing_rate`).
3. A bid or an ask reported as a rate where nothing cleared: with no offers the clearing returned the keenest borrower's cap moved
   a step (the opening year's 0.8, and the small fixture's whole run), and `_lend` wrote it to memory; with offers but no borrower
   able to pay the cheapest ask the rate crept toward that ask. Fixed: `credit.clear_with_cause` returns the held rate with cause
   `no_offers` or `no_borrower_at_ask` (`None` when there was none), and `_lend` leaves memory at the last cleared rate then.
   `no_offer_at_rate` leaves memory alone too.

Tests: `sim/tests/test_economy_credit_rate_below_asks.py` (built offers and requests); three tests that asserted the old rule
("borrowers with no lenders pull the rate up") now assert the held rate. 

Left open: the late-run labourer wage in `test_complaint_651_wage_step_gain.SmallEconomy` now flips sign more often (the fixture
has no lenders, so its rate is now held at the opening rate instead of drifting to the borrowers' bid); the amplitudes are small
and no fall nears the test's bound, but the count passes its limit. Not retuned. The rate and the lenders' asks after the change are
in the report of this commit.
