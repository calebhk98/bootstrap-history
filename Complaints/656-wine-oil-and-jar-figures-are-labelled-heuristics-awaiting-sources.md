# Wine, oil and jar figures: press, jar and stand numbers have no source, and vine hours look low

**Status:** open

Follow-up to Complaint 616. `data/production/95_wine_oil_jars.json` and the `vine_and_olive_tender` trade carry labelled heuristics (conf D, `retire` naming this complaint): press timber, stone, labour and life; amphora empty mass and potter hours; jar reuse (each jar used once); the olive stand's years to bear, life and planting labour; the vineyard's planting labour and life; the split of hours between grove or vineyard and press or cellar; tender training years; olive oil density.

**Also.** Columella 3.8 gives one vinedresser to 7 iugera (about 1.8 hectares) and Varro 1.18 one man to 8 iugera of olives; the entries carry roughly 200 hours a hectare, far below a working year for that. The wine and oil yields (4000 kg grapes, 1700 kg olives) are older unsourced estimates. The Rome jar costs about 0.8 of the wine it holds (measure: `sim(civ='rome_100ad')._material_prices()`), which looks high against jar cost in the sources.

**What it would take.** Open Columella 5 (olives), Cato 18 and 19 (press room and posts), Peacock and Williams or the Southampton amphora archive for empty mass and reuse, and a Monte Testaccio study; replace each figure with a quote.

**Test.** `sim/tests/test_wine_oil_jars.py` keeps the structure; replace each heuristic with a quoted figure.
