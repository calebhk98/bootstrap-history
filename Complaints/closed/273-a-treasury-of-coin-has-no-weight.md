# A treasury of coin weighs nothing and needs no vault

**Status:** closed - keeping cost (foreign actors at their country's pay, to its guards), coin carriage by mass (foreign routes, and between places of the home country), and theft, sack and banditry all read how wealth is kept (`sim/engine/coin_hoard.py`, `coin_carriage.py`, `holdings_exposure.py`, `theft_exposure.py`, `theft_charge.py`)

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 5 (physical weight of bronze coinage).

## What is wrong

A fortune held as bronze cash coin is a large mass, yet holding it costs nothing in storage, guarding or transport. The review's arithmetic: a late-game treasury of tens of millions of cash is many tonnes of bronze. Coin mass is physical in the money model (`sim/engine/money_units.py`, 144) and `sim/geography/transport.py` prices moving mass, but no screen or rule charges for keeping or moving money.

## Why it matters

A weightless treasury is a hardcoded outcome (`CLAUDE.md` 4.1) and it hides why people held wealth as land, goods or credit instead. It also makes confiscation and banditry (165) cheaper to shrug off.

## What it would take

Compute the mass of the coin held from the coin metal and the amount, charge storage and guarding as an actor cost, and let large transfers pay freight. Measure with a late-game save: held money converted to tonnes of coin metal. Which coin metal a civilisation uses is data.

## Done and remains

`Sim.coin_hoard` (`sim/engine/coin_hoard.py`) gives the money held as tonnes of the civilisation's coin metal and a yearly keeping cost from guard hours per tonne (a labelled heuristic, `COIN_GUARD_HOURS_PER_TONNE_YEAR`); both screens show it (`sim/tests/test_coin_hoard_mass.py`). The founder household's purse is charged the cost each year as its own line in the cash ledger (`keeping coin under guard`, `sim/engine/step_phase_money.py`). Other actors holding money (states, firms) are charged the same keeping cost each year by `charge_actors_for_keeping_coin`, called from `advance_actors`; foreign-country actors are not yet charged, since their wage level is not at hand. Coin that settles foreign trade pays carriage over the route by its mass (`coin_carriage_units`, `sim/engine/coin_hoard.py`), recorded in the partner ledger.

Theft (2026-10-09): `expected_theft_loss` prices each kind of holding by portability (coin and metal high, goods lower, loans and land near nothing), a guarding factor from guard hours per tonne (the keeping cost already charged), a visibility factor from `visible_scale`, and an order factor from state capacity and the holder's protection. Founder, states and firms lose it each year to `edge:thieves`, so money is conserved. Every actor exposes what it keeps by kind (`HoldingsExposureMixin`, `holdings_exposure.py`): the founder his purse, material stock, granary, farm and forest land; a state its purse and stores; a firm its purse and the shares it owns; an actor that holds none of a kind exposes none. The lent share of a purse counts as loans, the rest as coin. Yearly theft charges all of it: money to `edge:thieves`, goods out of the holder's stock to that edge's goods, land untouched. The sack and banditry events (`SACK_TAKE_STRENGTH`, `BANDITRY_TAKE_STRENGTH`) are thefts of larger strength priced by the same exposure (`plunder_founder`), a sack with the state's order failed; their money goes to the thieves, no longer to `edge:destroyed`. All weights are labelled heuristics. The whole-game effect was not run (the pure checks are in `sim/tests/test_theft_all_holdings.py`).

Owner decision (2026-10-09): theft risk must not follow the money held alone: it depends on how and where wealth is kept (coin, goods, land, credit), how it is guarded, how visible it is, and the state's order.

Closing (2026-10-09): foreign-country actors are charged the keeping cost at their own country's pay (`CountryWorld.pay_per_person_year`, the labelled rescale tracked by Complaint 407), paid to `edge:coin guards:<country>`. Coin moved between actors of the home country in different places pays carriage by its mass over the cheapest route (`sim/engine/coin_carriage.py`, hooked at `ledger.transfer` through `ledger.listening` during the actors' year and the founder's payments to the state), paid by the payer to `edge:freight`; one place, credit (interest, loans) and a party with no place (an edge, a body of people, a firm, which has no tile of its own) cost nothing. Checks: `sim/tests/test_coin_carriage_between_places.py`. The whole-game effect was not run.
