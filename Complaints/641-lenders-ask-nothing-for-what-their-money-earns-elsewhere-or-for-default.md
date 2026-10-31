# Lenders ask nothing for what their money earns elsewhere or for default, so the rate clears at zero

**Status:** partly - lenders' lowest ask (time preference plus expected inflation plus loss record), the bank spread and Eurace's default-probability markup with a value-at-risk cap are built; open: the land-yield and public-debt alternatives have no live input, `market_rate()` is not re-measured since the Eurace changes, the engine-facing rate still clamps nominally

**What was wrong.** Households lent at `max(0, expected_inflation)`, `credit.clear` (`sim/economy/credit.py`) floored the rate at zero
and dropped it to the lowest ask when funds sat idle, and a bank asked its depositors' rate plus a fixed margin. So a
lender accepted a loan that could not cover its own defaults, which breaks the principle that every price is one both
sides would agree to.

## What is built

- `sim/economy/lender_ask.py`: `lowest_ask` is the best of the lender's alternatives (time preference plus expected
  inflation, land yield, public yield) plus its expected loss rate; `loss_rate` is the share of the lender's credit
  exposure that went bad (`record.credit_losses`); `land_yield` is rent over title price, nothing where the land has no price.
- Households offer at that ask where they lend (`households_orders.py`, `lending.lend_working_capital`).
- `sim/economy/bank_spread.py`: a bank's spread is its loss rate plus `BANK_SPREAD_AT_NO_CAPITAL` times how far its capital
  ratio falls short of `BANK_CAPITAL_SHARE_OF_LOANS` (shape after Caiani et al. 2016 and Lavoie; labelled heuristic with `retire`).
- `sim/economy/bank_credit_risk.py` (after Eurace@Unibi `Bank_Credit_Functions.c`): a borrower's default probability from its
  leverage; the rate markup on it (`credit.risk_premium`, plus a term in unpaid arrears); a bank's value at risk against a
  multiple of its equity (`banks.py`), which `credit.clear_with_cause` enforces per piece through `FundsOffer.risk_capacity`.
  Its constants retire to 106.
- `credit.clear_with_cause` bounds the real rate (`rate_ceiling` plus `expected_inflation`); a bound that holds the rate below the
  clearing point sends funds to the least risky borrower first and returns the rest as unmet. When every offer asks more than the
  bound it returns `cause == no_offer_at_rate`, no loans and the held rate. With no offers or no borrower able to pay the
  cheapest ask it returns the held rate (`no_offers`, `no_borrower_at_ask`) and `_lend` leaves memory at the last cleared rate.
  A rate that was held below the clearing point while borrowers who would pay more were rationed lifts to the clearing point
  (`credit._borrowers_rationed_below_clearing_rate`).
- Borrowers' caps (`credit.earnable_rate`) are what the loan earns on their own figures; a missing or non-finite figure is a
  zero cap. `NicheEntry.found` prices the stake with `entry_round.capital_cost`.
- No loan-running cost and no hoarding floor: no source found for either (`Complaints/reports/research-pre-modern-interest-rates.md`).
- Tests: `test_economy_lender_ask.py`, `test_economy_banks.py`, `test_economy_credit.py`, `test_economy_credit_real_rate.py`,
  `test_economy_credit_rate_at_ceiling.py`, `test_economy_credit_rate_below_asks.py`, `test_economy_credit_eurace.py`.

- `sim/economy/credit_rate.py`: where borrowers queue for scarce funds the base rate is the dearest ask among the
  lenders who lend (those holding `MATERIAL_LENDER_SHARE` of the funds or more), not the cap of the last borrower in
  the queue; the queue is rationed by quantity. Before it, a few units of lendable money set the market rate at
  whichever borrower's affordability cap stood last, so the fixture's rate swung between its floor and the ceiling and
  Rome's sat at the ceiling (473). Probe: `Complaints/reports/641-rate-probe.md` style, fixtures `small` and `stationary`.

## What is wrong now

- Land yield has no live input: no title is bought or sold at a price (`titles_value` capitalises rent at the live rate, so
  rent over that price is the rate itself, a circle). It needs titles that trade at a price (538, 551).
- Public debt: no state bond reaches the household lender's choice, so `public_yield_available` stays unfed.
- Expected loss reads the loss share of exposure as a yearly rate; a lender that lost and then holds no claims asks the
  whole loss share. `RATE_FLOOR_SHARE` (capital_market) is a separate typed floor that this does not retire.
- `capital_market.market_rate_answered` still bounds the engine-facing rate nominally (`bounded_rate` takes `expected_inflation`
  but `economy_capital_market.market_rate` does not pass it), and the clearing's cause is not stored on the record.
- `market_rate()` reports `record.memory.rates[currency]`: the base rate of the last `_lend` clearing of the spin-up, the
  year's second and smaller clearing (the first, `lending.lend_working_capital`, writes nothing to memory). It is a marginal
  rate, not a loan-weighted average and not a real rate, so it sits below the median ask where the cheapest lender's funds
  cover the request. Whether this is what a caller wants is undecided.
- The opening rate and the entry of firms in the default game have not been re-measured since the Eurace price, wage,
  credit and finance rules landed. Measure: `from sim.tests import harness; game = harness.sim(capital=1e7)` on Rome with the
  full spin-up, then `game.economy._answering_agent().economy().record.memory.rates` and `game.actors.active_firms()`
  (probes: `Complaints/reports/641-rate-probe.md`). Rate level and the price index it reads expected inflation from
  belong to 473.

## What it would take

Feed the two alternatives (titles at a price, a state bond reachable by households), re-measure the opening rate, and retire
`RATE_FLOOR_SHARE` if the lenders' floor now does its job. Tests call the ask and clearing functions with built offers: a
glut leaves the rate at the lenders' floor, not zero; a lender with past losses asks more.
