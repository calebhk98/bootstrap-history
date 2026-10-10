# Mining techniques act as generic multipliers, coin has no mint, and mines never close

**Status:** closed - every mining technique now changes the physical term of the works it acts on (`sim/world/mine_technique.py`, `mine_works` mechanic; the generic `mining_tech` multiplier and its bounds are deleted), drainage and hoisting apply in the shaft bill as well as the running cost, mines close and reopen, and the engine's mint hires the minting recipe's labour at the coin standard's fineness and keeps its charge as `mint_charge_share` (`sim/economy/mint_labour.py`).

`mining_tech` applies tree multipliers with defensive bounds (a ceiling of 3, a floor of 0.35) instead of changing the physical works they stand for: the Archimedean screw, the wheel battery, the drainage adit and hydraulic ruina montium do not enter the works formulas in `sim/world/mine_works.py`. Coin is a definitional mass of silver: no mint labour, fineness or seigniorage. Mines have a fixed reserve and never close or reopen, though whole periods of abandonment are attested (Hirt, read qualitatively). What it would take: each technique replaces a term in the works it changes; mint labour, fineness and seigniorage tied to the metal stock; workings close when price falls below cost and reopen when it rises. Source review: `Complaints/reports/silver-mining-and-minting-review.md`. Related: 333, 334, 342.


## Closed

- Pumping (a water-wheel pump), the Newcomen engine and the winding engine lift for attendants and fuel; blasting and
  machine drilling change the breaking term; iron and steel rails and the railway change the load per haulage trip.
  Competing devices take the cheapest, they do not stack. Each node's `mine_works` entry carries its source or a
  labelled heuristic (`python3 sim/constants.py --burndown` lists the engine-side ones).
- The adit's head, the lift device and a hoisting engine change the shaft bill (spoil lift, drainage works, shafts
  needed); the water lifted per tonne by depth is still a labelled heuristic, lifted through the head an adit leaves.
- The mint spends the recipe's hours per kilogram of coin at the standard's fineness, paid by the issuer through a
  mint account; the hours hired set how much metal it strikes. The recipe's alloy metal and fuel are not bought
  (labelled `MINT_ALLOY_AND_FUEL_NOT_BOUGHT`).

## Round four

The agent economy's producers exit after their loss years when they have no variable margin, repaying lenders first (`sim/economy/producers_close.py`, `producer_exit.py`); idle plantless capacity decays toward runs worked; a mine that left can return once wages fall (`python3 -m sim.tests --only economy_exit`). Sites and depletion come from geography through site limits (Complaint 440).
## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 54 (`closed/54-a-shaft-that-costs-nothing-to-sink.md`): a shaft that costs nothing to sink: derive reserve and shaft bill from ore-body volume.
