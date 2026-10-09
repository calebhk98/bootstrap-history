# A treasury of coin weighs nothing and needs no vault

**Status:** partly - keeping cost charged to the household, states and firms, and coin carriage by mass (see below); theft now follows how wealth is kept (`sim/engine/theft_exposure.py`, `theft_charge.py`, `sim/tests/test_theft_follows_how_wealth_is_kept.py`): expected loss by kind of holding, guarding, visibility and the state's order, paid to `edge:thieves`. Remains: only coin is wired from the actors (goods, land and loans are priced by the function but no actor exposes them yet); sack and banditry still take fixed shares

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 5 (physical weight of bronze coinage).

## What is wrong

A fortune held as bronze cash coin is a large mass, yet holding it costs nothing in storage, guarding or transport. The review's arithmetic: a late-game treasury of tens of millions of cash is many tonnes of bronze. Coin mass is physical in the money model (`sim/engine/money_units.py`, 144) and `sim/geography/transport.py` prices moving mass, but no screen or rule charges for keeping or moving money.

## Why it matters

A weightless treasury is a hardcoded outcome (`CLAUDE.md` 4.1) and it hides why people held wealth as land, goods or credit instead. It also makes confiscation and banditry (165) cheaper to shrug off.

## What it would take

Compute the mass of the coin held from the coin metal and the amount, charge storage and guarding as an actor cost, and let large transfers pay freight. Measure with a late-game save: held money converted to tonnes of coin metal. Which coin metal a civilisation uses is data.

## Done and remains

`Sim.coin_hoard` (`sim/engine/coin_hoard.py`) gives the money held as tonnes of the civilisation's coin metal and a yearly keeping cost from guard hours per tonne (a labelled heuristic, `COIN_GUARD_HOURS_PER_TONNE_YEAR`); both screens show it (`sim/tests/test_coin_hoard_mass.py`). The founder household's purse is charged the cost each year as its own line in the cash ledger (`keeping coin under guard`, `sim/engine/step_phase_money.py`). Other actors holding money (states, firms) are charged the same keeping cost each year by `charge_actors_for_keeping_coin`, called from `advance_actors`; foreign-country actors are not yet charged, since their wage level is not at hand. Coin that settles foreign trade pays carriage over the route by its mass (`coin_carriage_units`, `sim/engine/coin_hoard.py`), recorded in the partner ledger. Remains: the sack hazard (`SACK_CAPITAL_LOSS` in `sim/engine/society_hazards.py`) takes a fixed share of capital and does not read the mass, so there is no hook yet for a hoard's exposure to depend on how it is kept (a new hazard design); transfers between actors of the same country pay no carriage.

Theft (2026-10-09): `expected_theft_loss` prices each kind of holding by portability (coin and metal high, goods lower, loans and land near nothing), a guarding factor from guard hours per tonne (the keeping cost already charged), a visibility factor from `visible_scale`, and an order factor from state capacity and the holder's protection. Founder, states and firms lose it each year to `edge:thieves`, so money is conserved. It is a standing small loss; the sack and banditry events stay as the large wartime and frontier events and do not read it. All its weights are labelled heuristics. The whole-game effect was not run.

Owner decision (2026-10-09): theft risk must not follow the money held alone: it depends on how and where wealth is kept (coin, goods, land, credit), how it is guarded, how visible it is, and the state's order.
