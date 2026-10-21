# The founder is last in the credit queue, so the line is only the running costs whenever lenders are rationed

**Status:** open

Measured on a fresh `rome_100ad` game, default kit (`poor_scholar`), seed 1, opened with the tests' short spin-up
(`ROME_SPIN_UP_YEARS=3,2`, a full cold spin-up is minutes; re-measure with the full one):
`printf '{"cmd":"state"}\n{"cmd":"available","limit":40}\n' | python3 sim/simulator.py agent --civ rome_100ad`.

## What the founder has in year one

- Cash 648 (`capital`). Rule: `kit_capital` (`sim/engine/data.py`) is `labourer_years` (4.033 for the default kit)
  times the opening schedule's labourer year; `reprice_opening_money` (`sim/engine/opening_money.py`) then moves the
  purse by the ratio of the economy's settled wage to that opening wage when the economy first opens. The purse thus
  holds 4.033 labourer-years at the economy's wage (about 160 denarii a year here). The rule is consistent (it keeps
  the purse's hours of work, tested in `test_opening_purse_and_credit_floor.py`); the small figure is the kit size and
  the economy's wage, not a mis-sized rule. The kit is a design choice and was not changed.
- Credit line 107 (`credit_limit`). It is the floor: `living_cost` at the standing income plus half the upkeep
  (`CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE`). The founder's own inputs would give more: the name (reputation 5 at
  `CREDIT_LINE_PER_REPUTATION_POINT`) and half the standing earning make a raw line of about 2,150, and the
  years-of-earning bound (`serviceable`) about 750. Both lose to the third bound, `market_credit_room`, which is 0.
- Market rate 0.2257 against the starting 0.12 (`debt_interest_rate`); it is the credit market's sticky base rate
  moved toward the clearing point (`credit.clear`), under the ceiling of 4 times the opening rate.
- Startable: 123 projects, cheapest paid one 6.8 (`pwr_oil_shale`), then 8.5, 13.4, ...; two cost nothing. Cash plus
  line (`you_could_raise_for_a_project`) is 755.6. So projects are affordable; people are not (a hired hand is a
  labourer-year, a fifth of the purse), which is the "almost nothing" the agents met.

## Why the room is 0

`economy_api.credit_room` (`sim/economy/api.py`) is the lendable capacity of the funds offered, less what every other
borrower was lent at the last lending. Here the funds offered are about 2.0e9 and the loans of that lending sum to
exactly that: demand exceeded supply, so `credit.clear` lent every unit of every offer. One producer plant
(`producer:olives_kg@libya_13`, 80-year term loans, collateral equal to principal) took about 1.8e9, over nine tenths of
the empire's household savings; the founder is not a borrower in `clear` and only ever sees what is left, which is
nothing whenever lenders are rationed.

## Defects found

1. The founder (an actor) does not compete in `credit.clear` at its own ceiling and premium; it is served from the
   remainder. Any rationed market leaves it at the floor, whatever its income or name. "Every mechanism usable by any
   actor" (CLAUDE.md section 2) needs the founder's request to enter the same clearing.
2. `LENDER_RESERVE_SHARE` is held back from the founder's room (`lendable_capacity`) but not from the loans `clear`
   makes to the others, so the market lends the whole offer and the reserve it names is never held.
3. One plant request of 80-year loans can absorb almost all savings: look at how plant loan requests are sized
   (`record.loan_requests`, `lending.py`) against the savings on offer; no per-borrower share bound is visible.

Not changed: the kit size, the starting numbers, `sim/labour/market/clearing.py`, household work (645), the fiscal
code (657). Related: 641 (the rate sits high because lenders' funds are exhausted), 528.

What it would take: put a seat's borrowing request into `credit.clear` (through `FundsOffer`/`LoanRequest`, with the
seat's collateral and arrears history), hold the reserve out of the offers, bound one borrower's share of the funds;
tests call `clear` with the founder's request among others and assert the founder gets a share ordered by its
ceiling, and that total lent never passes the lendable capacity.
