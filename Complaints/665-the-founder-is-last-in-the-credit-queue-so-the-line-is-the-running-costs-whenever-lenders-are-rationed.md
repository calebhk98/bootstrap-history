# The founder is last in the credit queue, so the line is only the running costs whenever lenders are rationed

**Status:** partly - items 1 to 3 changed (see Changes); in a full-length game the founder now has a credit line, but the market rate sits at the lenders' ceiling (641)

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

- Measured: Measured 2026-10-21 on main 3cb9c9a0, an opened Rome game with the full spin-up: from a checkout root, `from sim.tests import harness; import os; os.environ.pop("ROME_SPIN_UP_YEARS", None); game = harness.sim(capital=1e7)`, then the reads named below. `game.credit_limit()` is positive (the line is no longer the running costs alone), and
  `record.memory.rates` reads the lenders' ceiling. The founder can borrow, at the ceiling rate; what holds the rate there
  is 641's. The largest request per lending was not measured (a spy on `credit.clear`).
- Firms and the state via purses are unchanged (state deficit requests already join the clearing).
- Related: 641 (the rate sat high because lenders' funds were exhausted).
