# Lenders ask nothing for what their money earns elsewhere or for default, so the rate clears at zero

**Status:** partly - the heuristics are gone (a lost claim's life is the mean term of the claims the lender held at the last close, `claim_terms.py`; the state's bond premium over the going rate is added to the lender's own alternative, no gate); only the opening rate re-measure on a civilisation (the orchestrator's) remains

**What was wrong.** Households lent at `max(0, expected_inflation)`, `credit.clear` (`sim/economy/credit.py`) floored the rate at zero
and dropped it to the lowest ask when funds sat idle, and a bank asked its depositors' rate plus a fixed margin. So a
lender accepted a loan that could not cover its own defaults, which breaks the principle that every price is one both
sides would agree to.

## What is built

- `sim/economy/lender_ask.py`: `lowest_ask` is the lender's time preference plus the inflation it expects, plus its expected loss rate;
  `loss_rate` clamps the lender's remembered yearly loss rate (`loss_memory.py`, fed by `record.credit_losses`). It takes no land-yield or
  public-yield alternative (none exists in the sim: `grep -rn "def land_yield\|public_yield" sim`).
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

- Land yield is fed: titles sell at a price in the title sale market (`title_sales.py`, `title_sales_year.py`, 538), the year's price per tile is kept in `record.land.sale_price_by_tile`, and `rent / price` of the tiles that sold is `CreditRecord.land_yield`, read through `CreditView.land_yield` into `lowest_ask` by households' offers and working-capital lending. Buyers bid the rent over their own alternative rate (time preference plus expected inflation, the state's bonds where in reach), never the lending rate, so the yield is not the rate by construction; it is kept from the last year that sold. Tests: `test_economy_title_sales.py`.
- The public-debt alternative is the state's bond premium: how far the yield it sells at exceeds its coupon (the going rate), zero when it does not
  (`port_public_debt.bond_premium_over_coupon`, `EconomyYearInputs.state_bond_premium`, `CreditRecord.public_premium`). `lowest_ask` adds it to the lender's
  own alternative (time preference plus expected inflation), never the bond's whole yield, which tracks the cleared rate and would ratchet it. A society with no bond market or a state with no bonds offers none.
- A lost claim's life is the claim-weighted mean term (years run plus years left) of the loans the lender held at the last year's close, else of the whole book,
  else one year (`claim_terms.mean_term_years`, `loss_memory.age`, `CreditRecord.claim_lives`); `LOSS_CLAIM_LIFE_YEARS` is deleted.
- The opening rate and the entry of firms in the default game have not been re-measured since the Eurace price, wage,
  credit and finance rules landed, nor since the changes above. Measure: `from sim.tests import harness; game = harness.sim(capital=1e7)` on Rome with the
  full spin-up, then `game.economy._answering_agent().economy().record.memory.rates` and `game.actors.active_firms()`
  (probes: `Complaints/reports/641-rate-probe.md`). Rate level and the price index it reads expected inflation from
  belong to 473. Not run by the agent that built the land yield; the orchestrator runs it, and with the land yield now in the ask a rate that moves is expected where titles sell.

## Built since

- `lender_ask.lowest_ask(time_preference, expected_inflation, expected_loss_rate, land_yield, public_yield)`: the best alternative plus the loss.
- `loss_memory.blend`: a lender's year rate is its loss over its claims plus the lost claim for its life (`LOSS_CLAIM_LIFE_YEARS`), not the whole loss share.
- `CreditRecord.note_clearing` / `average_rate` / `last_clearing_cause`: both of a year's clearings (working capital and the ordinary one) add to the
  loan-weighted average and the cause is kept. `economy.api.market_rate` (`reported_rate.py`) is that average (else the remembered base rate), bounded by
  `bounded_rate` with the expected inflation lenders hold; `market_rate_answered` no longer clamps. The planning base rate (`memory.rates`) stays the
  marginal rate of the last clearing.
- `RATE_FLOOR_SHARE` is the discount floor of equity and secondary trade, not a floor lenders ask; it is kept, with `retire="Complaints/106"`.

## What it would take

Both alternatives are built (titles at a price, a state bond reachable by households) and in `lowest_ask`; left: re-measure the opening rate, and retire
`RATE_FLOOR_SHARE` if the lenders' floor now does its job. Tests call the ask and clearing functions with built offers: a
glut leaves the rate at the lenders' floor, not zero; a lender with past losses asks more.

## Update: requests cut to what the pledge bears

`sim/economy/credit.py` `clear_with_cause`: a request the premium on its whole amount prices out is funded for the most its
  pledge bears (`credit_cap.fundable_amount`, bisection on the premium) instead of refused; the borrower is marked in
  `Clearing.limited` (`collateral_bound`) and the rest stays unmet. A working-capital request pledges the producer's cash, the
  goods it holds and its plant, not the loan itself (`producers_working_capital.pledgeable_assets`, `request`).
  Not re-measured on a civilisation; fixtures: `python3 sim/simulator.py spin-up-trace --fixture small --years 50` (the `rate` column).

## Opening rate re-measured (commit d846ed11, rebuilt openings)

`python3 sim/simulator.py opening-checks` reports `rate_against_history` passing for all five base civilisations, but the solved opening
rate is the same in each: the households' time preference plus the expected inflation they open with
(`sim/economy/opening_rate.py` `opening_market_rate`), since the resting opening has no borrower and no lender with spare cash, so
nothing clears and the rate is the cheapest lender's lowest ask. The land yield and the bond premium cannot enter at the opening
(no title has sold yet, no bond has been priced); whether they move the rate is a reading of later years, not of the opening.
Still open: that later-year reading on a civilisation, and retiring `RATE_FLOOR_SHARE` (`sim/world/capital_market.py`, `retire` 106).
