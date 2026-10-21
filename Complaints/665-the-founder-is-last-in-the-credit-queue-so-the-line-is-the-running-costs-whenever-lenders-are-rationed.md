# The founder is last in the credit queue, so the line is only the running costs whenever lenders are rationed

**Status:** fixed in part: items 1 to 3 changed (see Changes); the rate and the founder's line in a full-length game are not re-measured

**What was wrong.** A founder is an actor, and "every mechanism usable by any actor" (CLAUDE.md section 2) needs its credit
request to enter the same clearing as everyone's. It did not: `credit.clear` served it from the remainder, which was zero
whenever lenders were rationed, so the founder's line sat at the floor (`living_cost` at the standing income plus half the
upkeep, `CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE`) whatever its income or name.

**Evidence (historical, before the changes).** Measured on `rome_100ad`, default kit (`poor_scholar`), seed 1, with the
tests' short spin-up (`ROME_SPIN_UP_YEARS=3,2`): `printf '{"cmd":"state"}\n{"cmd":"available","limit":40}\n' | python3 sim/simulator.py agent --civ rome_100ad`.
The room was zero because the funds offered were all lent (`economy_api.credit_room`, `sim/economy/api.py`): one olive plant
(`producer:olives_kg@libya_13`, 80-year term loans) took over nine tenths of the empire's household savings. The purse
(kit capital times the economy's wage, `kit_capital` in `sim/engine/data.py`, `reprice_opening_money`) is consistent and is
an initial condition of the scenario, not a modelled outcome; the kit size was not changed.

## Changes

1. The founder joins the clearing: `YearInputs.credit_asks` carries each playing seat's line (`credit_line_sought`, the
   engine's raw line and serviceable bound) into `credit.clear` as a `LoanRequest` (`credit_lines.line_request`); the grant is
   in `record.credit_granted` and is the seat's room (`api.credit_room`); no money moves in the economy's book for it.
   Tests: `test_economy_credit_lines.py`.
2. `credit_lines.hold_reserve` holds `LENDER_RESERVE_SHARE` out of every offer except a bank's (a bank keeps its own reserve
   against deposits), so no borrower is lent from the reserve.
3. The plant's "expand" request (`producers_close._expansion`) was a tenth of standing capacity times the plant's value
   whatever the producer worked, and the plant value swung with the price of `hectare_land` its own bids moved. Plant is now
   sized to the runs next year can work beyond the capacity left after wear, capped at the old growth share. Tests:
   `test_economy_producers.py`. No per-borrower share bound was added: sizing from need removed the single large request.

## What is left

- Re-measure in a full-length game (no short spin-up): the founder's line
  (`printf '{"cmd":"state"}\n' | python3 sim/simulator.py agent --civ rome_100ad`), the market rate, and the largest request
  per lending (a spy on `credit.clear`). The orchestrator's measurement is pending; do not change the status before it.
- Firms and the state via purses are unchanged (state deficit requests already join the clearing).
- Related: 641 (the rate sat high because lenders' funds were exhausted).
