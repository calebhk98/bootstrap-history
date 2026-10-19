# There is no bread, oven or bakery, and no cooked food at all

**Status:** closed - pinned by sim/tests/test_bread_and_bakery.py

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 611 (miller).

**What is wrong.** Flour is eaten as is (`data/world/needs.json` goods). Without a prepared-food good, town households without hearths are not modelled. Whether cooks and tavern keepers exist is an owner decision recorded in 530.

**Evidence.** `data/world/needs.json`; `data/production/*.json`.

**Why it matters.** Food preparation was a large non-farm employer.

**What it would take.** Add a baker trade, a bread good and a recipe from flour, fuel and an oven. Cook, tavern keeper and prepared-food service wait on the owner decision in 530.

**Test.** `validate` passes; a test: bread is producible from flour, fuel and an oven, and households can buy it.

**Resolution.** `baker` is a trade in `data/world/trades.json`; `data/production/95_bread.json` bakes bread from flour, water and process heat in a brick oven carried as capital; `bread_kg` is a food in `data/world/needs.json` at the flour energy it holds (no calories gained by baking) and spoils in `data/world/spoilage.json`. Open: bread costs more per unit of food energy than the flour it is made from, and the household basket has no taste or convenience premium (that would be a labelled heuristic), so the Rome opening books no baker hours (measure: `_non_farm_need_shares()` on `sim(civ="rome_100ad").labour`). Cook, tavern keeper and prepared-food service wait on the 530 owner decision.
