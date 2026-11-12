# Wine, oil and jar figures: press, jar and stand numbers have no source

**Status:** closed - every figure it named now cites a source someone opened (third pass, below); the earlier searches are kept for the record

**Sourced and cited in the data.** Vineyard labour (Columella 3.8, about 1130 hours a hectare, cross-checked against Cato's 10 labourers to 100 iugera, about 790); grove labour (Cato's 5 labourers to 240 iugera as Varro 1.18.1 reports it, the lower bound; all 13 slaves would give a higher figure); the wine yield range (Columella 3.7 and 3.11, 2700 kg of wine sits inside it); oil density; oil jars used once (Aguilera Martin, Dressel 20 tituli picti, p. 15); Dressel 20 empty mass (about 30 kg, another type). The earlier worry that vine hours looked low is resolved by the first of these.

**Press timber and stone (sourced as a lower bound).** Read from Cato 18 and 19 post and foundation dimensions at 296 mm to the Roman foot and 2650 kg per cubic metre of hard stone; the press-beam, windlass, levers, pavement and mill stones have no stated section and are not counted.

**Searched in the 656 second pass (opened, nothing usable).** Columella book 5 chapters 8 and 9 were read in the Loeb scan (archive.org onagriculturewit02coluuoft, vol. II): they give pruning every eighth year and alternate-year bearing, but no years-to-bear, tree life or planting labour. Cato 18 to 22 (LacusCurtius) give mill and press-iron costs in sesterces (ch. 21 and 22), not carpenter or mason hours. Pliny 15.6 (Perseus, Bostock and Riley) says "Four men, working at two presses day and night, ought to be able to press out three factuses of olives" (a factus is 100 modii), which needs an olive bulk density no opened source gives, so the 30 pressing hours stay a heuristic. No refill count for wine jars was found (de Graauw only says wine amphorae "one might think they have been reused"). Volume III of Columella (books 10 to 12) was not reachable.

**Searched and not found.** Columella book 5 is not on LacusCurtius (every book 5 to 9 address returns not-found; only books 3 and 4 open). The Southampton amphora pages sit behind a bot check and did not open. Wikipedia pages for Amphora, Monte Testaccio and Dressel 20 carry no empty mass for a 26-litre jar. Columella 3.3 gives costs in sesterces (planting 2000 per iugerum, a culleus of 40 urns at 300), not labour days, so planting hours stay a heuristic.

**Sourced in the third pass (each opened in that session; arithmetic is in `data/production/95_wine_oil_jars.json`).** Old value, new value, source:

| Figure | Old | New | Source |
|---|---|---|---|
| Olive yield, traditional rainfed | 1700 kg olives, 300 kg oil per ha | 1922 kg olives, 370 kg oil | International Olive Council, International olive oil production costs study 2015, system S1: "370 kg/ha" (https://www.internationaloliveoil.org/wp-content/uploads/2019/11/INTERNATIONAL-OLIVE-OIL-PRODUCTION-COSTS-STUDY-.pdf) |
| Press recovery (olive) | 17.6 percent | 19.25 percent | same study: "Processing oil yields average 19.25 per cent" |
| Oil jars per hectare | 12.67 | 15.62 | 370 kg over 26 litres at density 0.911 |
| Wine recovery | 0.675 kg per kg (unsourced) | unchanged, now inside the sourced range | Cornell CALS Grapes 101, 130 to 180 gallons a ton (https://cals.cornell.edu/news/2021/05/grapes-101-grapes-bottle-of-wine) |
| Olive years to bear | 7 | 5 | Hunker, fifth year and full yield at seven to eight (https://www.hunker.com/13428601/how-long-does-it-take-for-an-olive-tree-to-produce-fruit/); growables.org 3 to 4 years for light crops (https://growables.org/information/TropicalFruit/OliveArcRFC.htm); Olive Oil Times 3 to 5 (https://www.oliveoiltimes.com/production/iucn-studies-the-tradeoffs-between-intensive-and-traditional-olive-groves/135545) |
| Olive tree life | 80 years | 300 years | Wikipedia, Olive: productive for centuries, maximum ages 300 to 500 (https://en.wikipedia.org/wiki/Olive) |
| Olive planting labour | 300 h/ha | 50 h/ha | 100 trees (Olive Oil Times, 80 to 120 a hectare) at half an hour a tree (growingfruit.org forum, https://growingfruit.org/t/scared-of-all-the-holes-we-have-to-dig-are-we-crazy-to-take-on-12-trees-at-once/31622?page=2); a lower bound |
| Vine planting labour | 400 h/ha | 128.5 h/ha | Oregon State EM 8974-E (2009) Table 7, 52 h an acre (https://agsci.oregonstate.edu/sites/agscid7/files/oaeb/pdf/EM8974-E.pdf); a lower bound |
| Vineyard life | 30 years | 25 years | same publication, "productive life of 25 years"; yield decline accelerates after about 15 years (https://lodigrowers.com/vineyard-longevity/) |
| Oil press-room hours | 30 h/ha | 114 h/ha | Pliny 15.6 (Perseus, https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.02.0137%3Abook%3D15%3Achapter%3D6): four men, day and night, three factuses; modius 8.73 L (Wikipedia, Ancient Roman units of measurement); olive bulk density 591 to 647 kg/m3 (CIGR Journal, https://cigrjournal.org/index.php/Ejounral/article/view/2308) |
| Wine cellar hours | 30 h/ha | 24 h/ha | WineMaker magazine, Scaling up grapes: a crusher handles a ton an hour with one or two helpers (https://winemakermag.com/technique/scaling-up-grapes); pressing taken as equal (an assumption) |
| Wine jar reuse | 1 use (heuristic) | 1 use (sourced baseline) | Pena (2021) judges the evidence for reuse "scattered, uneven, and less than substantial" (https://www.ancientportsantiques.com/ancient-trade/ancient-containers/); Pecci et al. 2017 finds reuse at Oplontis with no count |
| Press carpenter hours | 200 (both) | 127.6 wine, 105.4 oil | permies.com, about 4 hours per 12 foot beam (https://permies.com/t/58723/Hand-hewing-beams); 7.5 inch section; hewing only, a lower bound |
| Press mason hours | 60 wine, 100 oil | 45.5 both | Building Construction Vol. IV, Data on Rubble Masonry, 1/3 mason day and 1/4 helper day per 25 cubic feet (https://chestofbooks.com/architecture/Building-Construction-V4/Data-On-Rubble-Masonry.html) over Cato 18's 266 cubic feet of foundations |
| Press life | 30 years | 100 years | Wine Berserkers, a 19th century oak vertical press pressing in 2013 after its staves were replaced (https://www.wineberserkers.com/t/renovating-old-burgundian-winery-vertical-press/82956) |
| Jar potter hours (extra) | 40 per hundred | 0 | a Dressel 20 workshop at "7 pots a day each" (https://fishandpeaches.blogspot.com/2012/03), about 114 h per hundred, already inside the ceramic recipe's 1750 h |

Tender training years had no separate figure in the data. The grape yield of 4000 kg/ha is inside the Columella range already cited and far below the modern Cornell average of four tons an acre.

**Found in the third pass, left for the ceramic recipe.** `ceramic_kg` books 700 potter hours a tonne (30_fuel_stone.json), 1750 hours for 100 jars, about fifteen times the 114 hours the 7 pots a day source implies. That overstatement is the likely reason the jar costs so much of the wine it holds. It is outside this complaint's files; revise the `ceramic_kg` hours (and restate any test that pins them) as a new complaint.

Follow-up to Complaint 616. `data/production/95_wine_oil_jars.json` and the `vine_and_olive_tender` trade carry the labelled heuristics above (now conf C with sources).

**Also.** The wine and oil yields (4000 kg grapes, 1700 kg olives) are older unsourced estimates. The Rome jar costs about
0.8 of the wine it holds (measure: `sim(civ='rome_100ad')._material_prices()`), which looks high against jar cost in the
sources.

**Research needed.** Press-room and cellar hours, press timber and stone (Cato 18 and 19), olive stand years to bear and life (Columella 5), grape and olive yields and press recovery (Columella 3 and 5, with modern traditional-orchard figures as a cross-check), jar empty mass, potter hours and wine-jar reuse count (Peacock and Williams, the Southampton amphora archive, Monte Testaccio studies).

**What it would take.** Open Columella 5 (olives), Cato 18 and 19 (press room and posts), Peacock and Williams or the Southampton amphora archive for empty mass and reuse, and a Monte Testaccio study; replace each figure with a quote.

**Test.** `sim/tests/test_wine_oil_jars.py` keeps the structure; replace each heuristic with a quoted figure.
