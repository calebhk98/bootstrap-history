# There is no bread, oven or bakery, and no cooked food at all

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Depends on 611 (miller).

**What is wrong.** Flour is eaten as is (`data/world/needs.json` goods). Without a prepared-food good, town households without hearths are not modelled. Whether cooks and tavern keepers exist is an owner decision recorded in 530.

**Evidence.** `data/world/needs.json`; `data/production/*.json`.

**Why it matters.** Food preparation was a large non-farm employer.

**What it would take.** Add a baker trade, a bread good and a recipe from flour, fuel and an oven. Cook, tavern keeper and prepared-food service wait on the owner decision in 530.

**Test.** `validate` passes; a test: bread is producible from flour, fuel and an oven, and households can buy it.
