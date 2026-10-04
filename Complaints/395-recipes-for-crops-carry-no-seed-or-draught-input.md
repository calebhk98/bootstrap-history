# Crop recipes carry no seed or draught input

**Status:** open

The wheat recipe the agent economy reads (`setup.recipes["wheat_kg"]`, from `data/production/`) yields 577.5 kg per hectare-year for 150 hours of labour with no inputs: no seed corn kept back from the harvest and no draught animals or their fodder. At bare labour cost that is several kilograms of grain per hour of work, far above the 0.1-0.4 kg an unskilled hour buys in `python3 sim/economy_validate.py` (script since removed; recover with `git show 97473f1:sim/economy_validate.py`). Any rule that lets makers enter where price beats cost then drives grain toward that labour cost (Complaint 393). The land rent in `sim/economy/land_market.py` takes part of the gap; the missing inputs are the rest, and they are data.

Evidence: print `setup.recipes["wheat_kg"]` and `setup.land_per_run["wheat_kg"]` for any civilisation's agent economy (`game.economy.agent.economy().setup`).

What it would take: seed as an input of the crop recipes (a share of the yield, a physical fact of the yield ratio), draught animal hours or fodder where the technique uses a plough, in `data/production/`.

Related: 393, 388.
