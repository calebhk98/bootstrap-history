# Wine and olive oil have no vine or olive crop, no press and no jar, and no years before trees bear

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

**What is wrong.** `wine_common_kg` and `olive_oil_kg` are `labourer` hours and land, with no inputs and no `holding_years`. Amphorae do not exist as goods.

**Evidence.** `data/production/*.json`.

**Why it matters.** Vines and olives are long-lived capital with years before they bear (CLAUDE.md 4.3).

**What it would take.** Grape and olive crops, presses, jars (amphorae) as goods, and `holding_years` for vines and trees, with a vine and olive tender trade.

**Test.** `validate` passes; a test: a new vineyard produces nothing until its holding years pass, and a press and jars are consumed in making wine.
