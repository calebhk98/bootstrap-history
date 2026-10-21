# Wine and olive oil have no vine or olive crop, no press and no jar, and no years before trees bear

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

**What is wrong.** `wine_common_kg` and `olive_oil_kg` are `labourer` hours and land, with no inputs and no `holding_years`. Amphorae do not exist as goods.

**Evidence.** `data/production/*.json`.

**Why it matters.** Vines and olives are long-lived capital with years before they bear (CLAUDE.md 4.3).

**What it would take.** Grape and olive crops, presses, jars (amphorae) as goods, and `holding_years` for vines and trees, with a vine and olive tender trade.

**Test.** `validate` passes; a test: a new vineyard produces nothing until its holding years pass, and a press and jars are consumed in making wine.

## Done

**Status:** closed (figures awaiting sources are Complaint 656).

- `data/production/95_wine_oil_jars.json`: `grapes_kg` and `olives_kg` crops; `wine_common_kg` and `olive_oil_kg` now made from them, a press as capital and `amphora_count` jars as an input; `amphora_count` made by potters from `ceramic_kg` (clay and firewood). The `vine_and_olive_tender` trade (`data/world/trades.json`) books the vineyard, grove, press and cellar hours instead of `farmer`.
- Years before bearing: a capital item may state `establishment_years` (`data/production/_SCHEMA.md`). The vineyard stand is two years (Columella 3, LacusCurtius, "the two-year period when the vineyards ... are delayed in bearing"); the olive stand is seven (heuristic, no source found).
- The reader: `holding_years` charges the rate on the inputs bought at the start, which is right for them; it never charged labour and land. The cost of a stand is a build bill spent over the barren years, so it is carried by `establishment_carry_factor` (interest only from when spent) and repaid over the bearing years (`stand_yearly_share`), used by both solver paths. Barren-year land is a `hectare_land` build material. This avoids the PR #60 overstatement of carrying the whole outlay from the start.
- Sources read: Cato, De Agricultura 10 and 11 (5 presses to an oliveyard of 240 iugera, 3 to a vineyard of 100); Varro 1.18 (one man to 8 iugera of olives); Columella 3 (one vinedresser to 7 iugera; the two barren years); Wikipedia, Ancient Roman units (amphora quadrantal about 25.9 L, iugerum 2,523 square metres); Roman Inscriptions of Britain instrumentum 2494 quoting Peacock and Williams (Dressel 20 average 62.83 L). No source found for press build bill and life, jar mass and potter hours, olive years to bear, stand life and planting labour, or jar reuse: labelled heuristics in Complaint 656.
- Found, not changed: Columella's one vinedresser per 7 iugera is about 1.8 hectares to a man, far more hours per hectare than the 200 the vineyard entry carries (Complaint 656).
- Tests: `sim/tests/test_wine_oil_jars.py`.
