# Fish is calories, not a good, and there is no salted fish or garum

**Status:** closed - pinned by sim/tests/test_fish_is_a_good.py

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Moved from 535 (closed, salt is now a need). Depends on 612 (salt worker).

**What is wrong.** The fisher's catch is calories in `sim/labour/food_gathering.py`, not a traded good. Garum does not exist.

**Evidence.** `sim/labour/food_gathering.py`; `data/world/spoilage.json` (`salted_meat_kg` is the model for a keepable good).

**Why it matters.** Preserved fish is a staple of coasts and trade.

**What it would take.** A fish good from the fishery; a salting recipe (fish and salt in, a keepable good out) with a spoilage row far below the fresh fish's; a garum recipe.

**Test.** A test: the fisher's catch appears as a tradable good, and salted fish spoils far slower than fresh.

**Resolution.** `fish_kg`, `salted_fish_kg` and `garum_kg` are recipes in `data/production/95_fish.json`, booked to the fisher trade; fish and salted fish are foods in `data/world/needs.json` at the energy the fisher's hours return (a test checks it, and that curing conserves energy); all three have spoilage rows far below fresh fish for the cured ones. The hours cap in `sim/labour/food_gathering.py` stays as the ceiling on the good, not a second supply (nothing in the engine consumed it as food). Open: the production schema has no siting field for a non-crop recipe, so coast and river siting is carried by the geography fishery rows only; garum counts no food energy and no seasoning need ranks it; curing hours are booked to the fisher because no fish-curer trade exists.
