# Mining techniques act as generic multipliers, coin has no mint, and mines never close

**Status:** partly - on the agent economy loss-making producers, mines included, now exit and plantless workings shrink to what is worked (round four); techniques as physical terms and mint labour remain

`mining_tech` applies tree multipliers with defensive bounds (a ceiling of 3, a floor of 0.35) instead of changing the physical works they stand for: the Archimedean screw, the wheel battery, the drainage adit and hydraulic ruina montium do not enter the works formulas in `sim/world/mine_works.py`. Coin is a definitional mass of silver: no mint labour, fineness or seigniorage. Mines have a fixed reserve and never close or reopen, though whole periods of abandonment are attested (Hirt, read qualitatively). What it would take: each technique replaces a term in the works it changes; mint labour, fineness and seigniorage tied to the metal stock; workings close when price falls below cost and reopen when it rises. Source review: `Complaints/reports/silver-mining-and-minting-review.md`. Related: 333, 334, 342.


## Round four

The agent economy's producers exit after their loss years when they have no variable margin, repaying lenders first (`sim/economy/producers_close.py`, `producer_exit.py`); idle plantless capacity decays toward runs worked; a mine that left can return once wages fall (`python3 -m sim.tests --only economy_exit`). Sites and depletion come from geography through site limits (Complaint 440).