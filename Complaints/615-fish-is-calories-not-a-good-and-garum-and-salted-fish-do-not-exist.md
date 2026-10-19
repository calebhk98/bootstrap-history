# Fish is calories, not a good, and there is no salted fish or garum

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Moved from 535 (closed, salt is now a need). Depends on 612 (salt worker).

**What is wrong.** The fisher's catch is calories in `sim/labour/food_gathering.py`, not a traded good. Garum does not exist.

**Evidence.** `sim/labour/food_gathering.py`; `data/world/spoilage.json` (`salted_meat_kg` is the model for a keepable good).

**Why it matters.** Preserved fish is a staple of coasts and trade.

**What it would take.** A fish good from the fishery; a salting recipe (fish and salt in, a keepable good out) with a spoilage row far below the fresh fish's; a garum recipe.

**Test.** A test: the fisher's catch appears as a tradable good, and salted fish spoils far slower than fresh.
