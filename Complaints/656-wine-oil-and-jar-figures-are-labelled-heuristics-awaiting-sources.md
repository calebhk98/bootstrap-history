# Wine, oil and jar figures: press, jar and stand numbers have no source

**Status:** open - partly done: labour, the wine yield range, oil density, jar reuse and the press timber and stone (Cato 18 and 19, lower bound) are sourced; the figures listed under "Still heuristics" are not

**Sourced and cited in the data.** Vineyard labour (Columella 3.8, about 1130 hours a hectare, cross-checked against Cato's 10 labourers to 100 iugera, about 790); grove labour (Cato's 5 labourers to 240 iugera as Varro 1.18.1 reports it, the lower bound; all 13 slaves would give a higher figure); the wine yield range (Columella 3.7 and 3.11, 2700 kg of wine sits inside it); oil density; oil jars used once (Aguilera Martin, Dressel 20 tituli picti, p. 15); Dressel 20 empty mass (about 30 kg, another type). The earlier worry that vine hours looked low is resolved by the first of these.

**Press timber and stone (sourced as a lower bound).** Read from Cato 18 and 19 post and foundation dimensions at 296 mm to the Roman foot and 2650 kg per cubic metre of hard stone; the press-beam, windlass, levers, pavement and mill stones have no stated section and are not counted.

**Searched and not found.** Columella book 5 is not on LacusCurtius (every book 5 to 9 address returns not-found; only books 3 and 4 open). The Southampton amphora pages sit behind a bot check and did not open. Wikipedia pages for Amphora, Monte Testaccio and Dressel 20 carry no empty mass for a 26-litre jar. Columella 3.3 gives costs in sesterces (planting 2000 per iugerum, a culleus of 40 urns at 300), not labour days, so planting hours stay a heuristic.

**Still heuristics with `retire` here.** Press build labour (carpenter, mason) and life; the 26-litre jar's empty mass and potter hours; wine jar reuse count (sources say wine jars were reused, no count found); stand years to bear (olive), life and planting labour; the cellar and press hours; tender training years; grape and olive yields and press recovery. Columella book 5 and Cato 18 and 19 totals were not reachable or not totalled (the LacusCurtius book 5 URL returned 404).

Follow-up to Complaint 616. `data/production/95_wine_oil_jars.json` and the `vine_and_olive_tender` trade carry the labelled heuristics above (conf D, `retire` naming this complaint).

**Also.** The wine and oil yields (4000 kg grapes, 1700 kg olives) are older unsourced estimates. The Rome jar costs about
0.8 of the wine it holds (measure: `sim(civ='rome_100ad')._material_prices()`), which looks high against jar cost in the
sources.

**Research needed.** Press-room and cellar hours, press timber and stone (Cato 18 and 19), olive stand years to bear and life (Columella 5), grape and olive yields and press recovery (Columella 3 and 5, with modern traditional-orchard figures as a cross-check), jar empty mass, potter hours and wine-jar reuse count (Peacock and Williams, the Southampton amphora archive, Monte Testaccio studies).

**What it would take.** Open Columella 5 (olives), Cato 18 and 19 (press room and posts), Peacock and Williams or the Southampton amphora archive for empty mass and reuse, and a Monte Testaccio study; replace each figure with a quote.

**Test.** `sim/tests/test_wine_oil_jars.py` keeps the structure; replace each heuristic with a quoted figure.
