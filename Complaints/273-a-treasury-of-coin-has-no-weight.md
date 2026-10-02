# A treasury of coin weighs nothing and needs no vault

**Status:** partly - the hoard's mass and a keeping cost show on the money and state screens; charging the cost, freight on transfers and theft exposure by mass remain

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 5 (physical weight of bronze coinage).

## What is wrong

A fortune held as bronze cash coin is a large mass, yet holding it costs nothing in storage, guarding or transport. The review's arithmetic: a late-game treasury of tens of millions of cash is many tonnes of bronze. Coin mass is physical in the money model (`sim/engine/money_units.py`, 144) and `sim/world/transport.py` prices moving mass, but no screen or rule charges for keeping or moving money.

## Why it matters

A weightless treasury is a hardcoded outcome (`CLAUDE.md` 4.1) and it hides why people held wealth as land, goods or credit instead. It also makes confiscation and banditry (165) cheaper to shrug off.

## What it would take

Compute the mass of the coin held from the coin metal and the amount, charge storage and guarding as an actor cost, and let large transfers pay freight. Measure with a late-game save: held money converted to tonnes of coin metal. Which coin metal a civilisation uses is data.

## Done and remains

`Sim.coin_hoard` (`sim/engine/coin_hoard.py`) gives the money held as tonnes of the civilisation's coin metal and a yearly keeping cost from guard hours per tonne (a labelled heuristic, `COIN_GUARD_HOURS_PER_TONNE_YEAR`); both screens show it (`sim/tests/test_coin_hoard_mass.py`). Remains: the cost is shown, not yet charged to the purse; large transfers pay no freight (`sim/world/transport.py` prices mass, nothing calls it for money); the sack hazard (`SACK_CAPITAL_LOSS` in `sim/engine/society_hazards.py`) takes a fixed share of capital and does not read the mass, so there is no hook yet for a hoard's exposure to depend on how it is kept.
