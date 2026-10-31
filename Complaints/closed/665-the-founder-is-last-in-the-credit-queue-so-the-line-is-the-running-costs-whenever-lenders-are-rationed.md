# The founder is last in the credit queue, so the line is only the running costs whenever lenders are rationed

**Status:** closed - the founder's request is served in the same clearing as every other request (`credit_lines.line_request` into `credit.clear`); what the market rate does is 641's

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
3. The plant's "expand" request (`producers_close._expansion`) is sized by `plant_investment.investment_runs` (Eurace@Unibi's
   investment rule): the gap between the runs planned and the capacity left after wear, no more than `INVESTMENT_INERTIA`
   times the year's wear, so no single large request takes the funds. Tests: `test_economy_producers.py`.

## What is left

Nothing in this complaint. The founder's line is served by risk premium like every request (`credit.risk_premium`,
`bank_credit_risk`), not by cap. The level of the market rate and whether a full-length Rome game has the founder borrowing
at a sensible rate are 641's (`game.credit_limit()` and `record.memory.rates` on an opened game; not re-measured since the
Eurace credit and price rules). Firms and the state via purses are unchanged (state deficit requests already join the
clearing).
