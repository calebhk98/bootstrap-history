# Lenders ask nothing for what their money earns elsewhere or for default, so the rate clears at zero

**Status:** partly - the lowest ask (time preference plus expected inflation, plus the lender's own loss record) and the bank's spread (loss record plus capital shortfall) are built; still open: the land-yield and public-debt alternatives are computed but have no live input (no title sale price, no state bond sold to households), see Open

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
  plant, and the lender reserve never held), and seats' credit lines now join `credit.clear`. The cleared rate was not
  re-measured in a full-length game: `game.economy._answering_agent().economy().record.memory.rates` on a default Rome game
  (the orchestrator's measurement is pending). A default game in which no firm can ever enter is a defect, not a setting;
  `test_firm_entry_default_game_scenario` checks placement without a founding.

**What it would take.** Feed the two alternatives (titles at a price, a state bond reachable by households), re-measure the
opening rate, and retire `RATE_FLOOR_SHARE` if the lenders' floor now does its job. Tests call the ask and clearing
functions with built offers: a glut leaves the rate at the lenders' floor, not zero; a lender with past losses asks more.
