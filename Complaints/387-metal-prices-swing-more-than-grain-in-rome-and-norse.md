# Metal prices swing more than grain in Rome and Norse

**Status:** open - happens in every civilisation (`python3 sim/economy_validate.py --years 30 --seeds 1,2` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`)). Competitive storage by merchants was tried and not merged (Complaints/reports/agent-economy-review.md); the iron price alternates even with large merchant stocks, so check the producer-side cobweb next

On the agent economy, the national prices of iron, copper, lead, bronze and tin swing more from year to year than wheat does in Rome and Norse. In pre-industrial economies grain was the volatile price: harvests moved it, while metals, stored and traded far, moved little.

Evidence: `python3 sim/economy_validate.py --years 40 --seeds 1,2,3 --civs rome_100ad,norse_900ad`, columns `grain_vola` and `metal_vola`. England and Han show metals close to grain.

Likely causes to check: thin metal markets (few producers per area, sporadic trade), the mint's limited metal stock now that it holds only what it bought (`sim/economy/mint.py`), and Norse trading very little metal at all.

Related: 386.
