# Metal prices swing more than grain in Rome and Norse

**Status:** closed - folded into 442

On the agent economy, the national prices of iron, copper, lead, bronze and tin swing more from year to year than wheat does in Rome and Norse. In pre-industrial economies grain was the volatile price: harvests moved it, while metals, stored and traded far, moved little.

Evidence: `python3 sim/economy_validate.py --years 40 --seeds 1,2,3 --civs rome_100ad,norse_900ad`, columns `grain_vola` and `metal_vola`. England and Han show metals close to grain.

Likely causes to check: thin metal markets (few producers per area, sporadic trade), the mint's limited metal stock now that it holds only what it bought (`sim/economy/mint.py`), and Norse trading very little metal at all.

Related: 386.


## Round four

Measured over 30 years, seeds 1-2 (scratch driver; no command yet, Complaint 445): iron volatility fell in England, Norse and Rome (the Norse outliers above one are gone) to about 0.24-0.38, and stayed about the same in Han. See `Complaints/reports/agent-economy-review-round-four.md`. Gold's price is set on a thin ornament flow with gold valued like silver per kg (442) and no durable goods (443).