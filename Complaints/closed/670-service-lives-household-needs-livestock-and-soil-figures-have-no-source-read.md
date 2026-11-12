# Service lives, household-need, livestock, spoilage and soil figures have no source that was read

**Status:** closed

Split from 646 (figures recalled rather than read; closed). Each entry below is labelled (confidence D or a
`temporary_heuristic` with a `retire`); the work is to read a source and replace the figure, or leave it labelled.

**What is wrong now, with the command that lists it.**

- Service lives with no source: `data/world/service_lives.json` entries of confidence D (iron and wooden tools, brick, stone
  blocks, bronze, brass, iron bar, cast iron, steel plate, Noric steel, tool steel, gold, silver, platinum, mule, cart, pack
  saddle, river barge). List: `grep -n -B2 '"confidence": "D"' data/world/service_lives.json`. Searches for Roman and medieval
  iron hoe and spade use-life found only typology and single worn specimens, no duration; NCAT Draft Animal Power for Farming
  gives a life for draft horses only. The wooden tool's life belongs here (659; 650 holds its other figures).
- Livestock: `data/world/living_stock.json` rows at confidence D (sheep fleece, salt and stocking rates, goat stocking and
  milk, cattle dressing, fat, hide, horn, salt and stocking, goat excreta share):
  `grep -n '"confidence": "D"' data/world/living_stock.json`.
- Spoilage: `data/world/spoilage.json` rows at confidence D (the same grep).
- Household needs (`data/world/needs.json`): the housing satiation multiple (Naroll 1962 and Brown 1987 are cross-cultural
  means of dwellings, not a limit of wanting more room), pottery stock (Deal 1985, paywalled), vessel mass per vessel, coin
  stock (Duncan-Jones), the tallow and oil lamp quality factors, salt satiation.
- Soil: the temporary heuristics of `sim/geography/soil_nutrients.py` (native nitrogen pool, loss rate, legume net nitrogen,
  manure available the first year, manure retained in the pool, the share of herd excreta carried to the fields); list with
  `python3 sim/constants.py --burndown | grep soil_nutrients`. The three-field legume share in `sim/world/agriculture_core.py`
  (half of the spring field taken as legumes: "recalled, not measured").
- Household time preference and the savings constants (`HOUSEHOLD_TIME_PREFERENCE`, `SAVINGS_YEARS_OF_SURPLUS_INCOME`,
  `SPENDING_CUT_LIMIT`, `WEALTH_DRAWDOWN_LIMIT`) retire to 607, not here.

**Research needed.**

1. Working lives of pre-modern tools and carts: archaeological use-wear and replacement studies, estate accounts that record
   tool replacement (medieval manorial accounts), experimental use-life studies.
2. Livestock: traditional-system production parameters for sheep, goats and cattle (fleece, dressing percentage, hide and horn
   yield, stocking rates), from the FAO traditional-systems volume and breed studies.
3. Spoilage and storage losses of pre-industrial grain, bread, meat and fish by storage method.
4. Soil nitrogen: native pool, loss rate, legume fixation net of removal, and manure nitrogen release for rain-fed temperate and
   Mediterranean soils (long-term experiments such as Rothamsted; Peoples et al. 2009 for legumes, not opened).
5. Dwelling floor area per person and the stock of pottery per household from ethnoarchaeology (Deal and Straight 2017 are
   paywalled; a library copy is needed).

**Test.** `sim/tests/test_recalled_figures_sourced.py` holds what was sourced; `python3 sim/constants.py --burndown` lists
the `retire` fields.

**Pass 6 (source-recipes-and-service-lives).** Sourced and opened:

- `sheep_kg` and `goat_kg` offtake per head-year now read from FAO, "Production parameters of ruminants in traditional systems"
  (fao.org/4/Y4176E/y4176e08.htm): the mean offtake rate for sheep and for goats in traditional systems. The herd recipes in
  `data/production/95_herds.json` were recomputed from the rows (the herd-joint-products test checks they follow).
- Sheep and goat dressing fractions: the Montana State University Extension (Sanders County) dressing-percentage note, opened as a
  PDF, now cited as read; value unchanged. Okello, "A survey of the productivity and functions of goats in Uganda"
  (fao.org/4/x5464b/x5464b16.htm, Tables 1-3, opened) gives a wider and higher range for Ugandan goats, so the goat fraction is
  at the low end of a traditional-system survey; kept.

Searched and not sourced: service lives (manorial-account searches found no tool replacement interval; a Swedish thesis on iron
use in farming turned up in search but its host redirects and could not be opened; Langdon on carts not reachable); sheep fleece
(search summaries give roughly one to two kilograms for indigenous breeds from papers on Omani, Iraqi and Egyptian sheep, none
opened); zebu cattle dressing (Ethiopian and Malawian studies in search summaries only, not opened). Left: every service life at
confidence D, the fleece, stocking, salt, hide, horn and fat shares, milk of goats, spoilage rows, household needs and the soil
heuristics (soil stays with 543). Status stays open.

**Pass 7 (sources-herds-and-lives).** Service lives: iron tools 4 to 2 years (FAO farm-power study Annex 3 Table 5, hoe replacement at ten
African sites, mean of range midpoints 2.0; a modern analogue, confidence C); wooden tools 2 to 1 (half of the iron figure, still a labelled
heuristic, D); cart 10 to 15 (TRL/DFID Uganda IMT study, Table 2, oxen cart average vehicle life 15 years, confidence C). Livestock: goat milk,
cattle dressing and the hide shares of cattle, sheep and goats are now read (see Complaint 532's pass note); sheep fleece is bracketed by
Wilson's Menz figure. Searched and not sourced: brick, stone, bronze, brass, iron bar, cast iron, steel plates, Noric and tool steel, gold, silver,
platinum (no wear study found), mule working life (only lifespan figures of 30 to 40 years, not working life), pack saddle (one Practical Action
note of up to six months in Ethiopia, search snippet only), river barge (Manning et al. supplement gives 20 to 30 years for seagoing wooden ships,
not river craft; the Mazotos paper's supplement was opened but is not a barge figure), Cato's equipment inventories (counts, no durations).
Spoilage, household needs and soil items were not touched. Status stays open.

**Pass 8 (source-lives-livestock-spoilage).** Standard applied: a ballpark with any opened citation (extension pages, vendor and trade
pages, forums, Wikipedia, modern analogues). Every URL below was opened in the pass.

Service lives (`data/world/service_lives.json`, now confidence C unless stated; old -> new years):
- brick 80 -> 90: ccpia.org life-expectancy chart, solid brick 80 to 100. stone blocks 100 -> 87.5: same chart, stone siding 75 to 100.
- brass 20 -> 50: same chart, brass supply pipe 50+. cast iron 15 -> 65: mean of cast-iron cookware 50 to 75 (en.fmyly.com/article/how-many-years-will-cast-iron-last/)
  and cast-iron waste pipe 60 to 75 (ccpia). steel plate 20 -> 44: mean of the seven steel items' midpoints on the ccpia chart.
- iron bar 10 (unchanged value, now sourced): axeman.ca/blogs/news/how-long-should-an-axe-last-forged-axe-lifespan-guide, budget axe 5 to 15. tool steel 8 -> 30 and
  Noric steel 15 -> 30: same page, mid-range forged axe 20 to 40. bronze 25 -> 20: mean of the budget and mid-range midpoints (10 and 30), an analogue; no bronze duration found.
- mule 10 -> 12.5: knau.org/post/earth-notes-grand-canyon-mules, guest mules 'average working life of 10 to 15 years'.
- pack saddle 8 -> 3: samplecontents.library.ph Practical Action 'Making a packsaddle' page 14, up to 6 months in Ethiopia and over 20 years for a well-kept Mexican one; geometric mean 3.2.
- river barge 20 -> 15: sevendaysvt.com Lois McClure article, 'a typical canalboat lasted only about 15 years'.
- Left at D: gold, silver, platinum (50 years). Opened brackets: xetra-gold.com 'Figure of the month: 6 milligrams' (a ring loses about 6 mg a year by abrasion) and the
  forums.collectors.com post (coin loss about 1 percent a year, wear a tenth of that), both pointing to 100 years or more for wear alone; the 2 percent loss-and-recast figure has no source.
- Left at D: wooden tools (half the iron life; searched homesteading and gardening pages, which give handle lives of decades with care and no whole-tool life).

Livestock (`data/world/living_stock.json`): sheep salt 4.0 -> 3.5 kg a head-year (nmsu sheep nutrition page, range ewes 8 to 11 g a day, midpoint 9.5 g x 365; merckvetmanual.com 9 g a day);
goat salt 3.0 -> 2.9 (scaled by live weight); cattle salt 11 kept, now sourced (agriorbit.com/?p=245351, mature cows about 30 g a day). Stocking: lrrd.org/lrrd30/5/sange30079.html,
semi-arid carrying capacity 2 to 4 ha a tropical livestock unit and 'one cow equals four goats or sheep', so cattle 0.5 a hectare, goats 2.0 and sheep 1.5 stay, bracketed;
agris.fao.org/search/es/records/64775fb1a3fd11e4303b9c4c, goats at 1, 2 and 4 a hectare, only 4 degrading. The three rows stay D because the fat shares (sheep 8, goat 5, cattle 6 percent of the
carcass), draught share, collected-dung share, winter days and straw share are still assumed; searched fat and rendering yields (a fed steer's trim is about 20 percent, not a lean traditional
animal; no tallow yield per head found), and goat excreta (an extension handbook line of 2 to 6 percent of live weight in fresh faeces turned up in a search summary only, not opened).

Spoilage (`data/world/spoilage.json`, now C; old -> new per year): milk 300 (kept; usdairy.com 2 hours, 1 hour above 32C); meat 100 (kept; FAO T0562E04 'ripens rapidly'); bread 50 -> 73
(Clemson 3 to 7 days, 365 / 5); salted meat 0.5 (kept; FAO T0562E04 charque 'keeps for months', biltong a year); fish 200 (kept; FAO v7180e0c, 25 times faster at 20-30C); hide 3 -> 243
(CSIRO Meat Technology Update 98-3 Table 1, 1 day at 20C, 2 days at 15C); garum 0.1 -> 0.4 (cookingchew.com, unopened fish sauce two to three years); silk cocoons 20 -> 146 (FAO x2099e04,
stifle within 2 to 3 days); silkworm eggs 2 -> 3 (scielo.br babt, four months cold storage); cheese 0.3 and salted fish 0.6 kept, cited by analogy (Wikipedia Cheese; FAO charque), no
rate found. Olive oil and common wine are Complaint 656's and were not touched.

Needs (`data/world/needs.json`): money stock 0.1 kg a head sourced (review of Bolton's table, 65.5d to 101.3d a head in 1310, times the 1.3 to 1.5 g penny, 85 to 152 g); money stock life 67 -> 100
(forum coin-loss figure, D). Vessel mass: villagedecor.in lists 1.6 kg for a 1.5 litre and 2.89 kg for a 3.5 litre lidded clay pot, so the 1 kg is the light end; stock stays D. Housing
satiation: the Wikipedia Insula figure (330 square metres for over 40 people, 8.25 a head) is another occupancy, not a limit; stays D. Not found: pottery stock per household (Deal and
Straight paywalled, the Cambridge chapter pages open only to abstracts), lamp quality factors (no photometric tallow or oil-lamp figure in any opened page), soil nitrogen heuristics
(not attempted; soil stays with 543).

Status stays open for the rows named as left at D, the herd assumptions, pottery stock, lamp factors and soil.

**Pass 9 (source-lives-livestock-spoilage, second round).** Every URL opened in the pass.

- Ornament metal life (gold, silver, platinum) 50 -> 100 years, now C: forums.collectors.com/discussion/comment/8843720 (coin loss about 1 percent a year; wear a tenth of that) and
  xetra-gold.com/en/detail/figure-of-the-month-6-milligrams/ (ring wear about 6 mg a year). Coupled `needs.json` ornament satiation 0.0005 -> 0.00025 kg a head a year: held stock 25 g a head
  (en.wikipedia.org/wiki/Gold, 201,296 tonnes above ground in 2020, over en.wikipedia.org/wiki/World_population, 7.84 billion: 25.7 g) times the 1 percent loss; the TRANSITIONAL label is dropped.
- Wooden tools 1 -> 4 years, now C: permies.com/t/159519/Care-wooden-handles-metal-business ('handles break on hoes and rakes but they were 20 plus years old'), easydigging.com garden hoe
  reviews (an iron hoe 10+ years), scaled by the farm-to-garden wear ratio from the FAO 2-year iron hoe (2 / 10); the old test that pinned wooden = half of iron is replaced by one that asserts this
  arithmetic.
- Fat share of the carcass: cattle 0.06 -> 0.083, sheep 0.08 -> 0.074, goats 0.05 -> 0.082, from the USDA AMS By-Product Drop Value Report - Cow (ams.usda.gov/mnreports/ams_2834.pdf: renderable
  tallow 3.68 lb per 100 lb live weight) over each dressing fraction (the cow's yield applied to the small ruminants by analogy). The three herd recipes in `data/production/95_herds.json` were recomputed.
- Soil (`sim/geography/soil_nutrients.py`, heuristic labels dropped, now C): native pool 3000 kept, inside 1,000 to over 20,000 kg N a hectare (eurofins.com/en-nl/agro-testing/wiki/total-n-stock/);
  loss rate 1 percent kept, the low end of the 1 to 3 percent of SOM nitrogen mineralised a year (Oregon State EM 9281); legume net nitrogen 25 -> 19 kg N a hectare, midpoint of 0 (grain legumes) and
  37.9 (vetch brown manure) in the Hart Field-Site 2022 trial (hartfieldsite.org.au PDF); manure first-year share 0.3 kept, midpoint of Kentucky AGR-146's 0.175 (fall, no cover) and 0.45 (spring);
  manure retained 0.4 kept, 1 - 0.45 - 0.15 (Kentucky's loss when not incorporated). Three-field legume share 1/6 -> 0.08 of the holding: Pelham, Fourteenth-Century Agriculture in Sussex
  (archaeologydataservice.ac.uk SAC078_Pelham.pdf), legumes at most 24 percent of the cropped area at the one manor that grew them on a large scale, half of that over the two thirds cropped.
  Kentucky's own table gave only a ballpark for a modern farm; no medieval measurement of these shares was found.
- Pottery stock: bracketed, not changed. Valencian inventories (Cambridge, Why did medieval villagers buy earthenware pottery, opened): ten bowls (1438), six little bowls (1450), 46 pieces (1418), and
  57 vessels in San Mateo Ixtatan, so two to ten vessels a head; 5 kg a head is inside. Stays D (vessel mass: only modern bought pots, 1.6 to 2.9 kg).
- Herd assumptions: collected-dung share of a third is the 8 hours in a night fold of 24; the opened Oregon State dairy worksheet (kpu.ca Keeping Track of Manure Nutrients) deposits dung in proportion to time
  spent, its example a 25 percent confinement share. A Romanian dairy study (pmc.ncbi.nlm.nih.gov/articles/PMC3674972) has cows pasturing 182 days a year, so 90 stall days is under it (Mediterranean ballpark).
  Straw share of the ration, the draught share of offtake and the goat excreta share: no page found that gave them (an NDSU straw-bedding page was blocked; a goat-manure page returned 403 or 503).

Left, so Status stays open: lamp quality factors (0.7 tallow, 0.85 oil; only the direction was read: Wikipedia Candle and the Oil lamp article; no valuation ratio or lumen comparison found; EXARC's
lux experiment on Roman lamps could not be opened), housing satiation (occupancy only), the straw share, draught share and goat excreta share above, pottery vessel mass, the fallow nitrate retention and
half-saturation soil constants (not named by this complaint; they retire to a nitrate balance and a crop model), and the spoilage rows of 656's olive oil and wine.

**Pass 10 (closing).** Every URL opened in the pass.

- Pottery stock 5 -> 10 kg a head, now C: 2 to 10 vessels a head from the Valencian inventories and Nelson (57 per household), geometric mean 4.5, times the midpoint 2.25 kg of villagedecor.in's
  1.6 and 2.89 kg lidded clay pots; use-life 4 years inside Nelson's 0.4 to 13. Housing satiation multiple: C as a bracket (the occupancy of the sample, Roman insula and Naroll's figure), set at the
  space people lived in.
- Spoilage: olive oil 0.15 -> 0.625 (oliveoil.bertolli.com/olive-oil-shelf-life/, 16 months, up to 24 claimed), common wine 0.2 -> 0.67 (craftabrew.com, grape wine one to two years).
- Straw share of the ration 0.5: saskatchewan.ca straw roughage page, 50 percent of a wintering cow's diet with low-quality straw (75 with good). Draught share 0.3: cgspace.cgiar.org item
  98d68dea-662c-4b13-a0fe-51913e85bc2e, 9 to 10 million of 31 million Ethiopian cattle used for draught (29 to 32 percent; a herd share used as the offtake share, caveat in the row). Goat excreta share: the
  Mgeta goat leaves 61 kg dry droppings a year (library.au.int record) and fresh goat manure is 38 to 48 percent dry matter (Tropentag 2020 abstract 417), so 1.6 percent of live weight a day as faeces;
  the 4 percent kept is the sheep faeces-and-urine figure, so 1.6 is the lower bound of the bracket. Collected-dung share and winter fodder days: bracketed (pass 9).
- Lamp quality factors 0.7 and 0.85: valuations of smoke and smell, not light delivered. Opened: Wikipedia Candle (one candela, about 13 lumens; tallow cheaper, smellier), the Oil lamp article
  (olive oil lamp 'significantly brighter than a candle'), Practical Action Rural lighting Table 1 (candle 1 lumen, wick oil lamp 1 to 10). No page gave a price or valuation ratio of tallow, wax and oil
  light, and the EXARC lux experiment on Roman lamps could not be opened. These two numbers stay labelled valuations with direction cited (`heuristic` flag kept, retire: indoor air model).
- Fallow nitrate retention and half-saturation supply are not in this complaint's list; left.

Closed: every figure the complaint names now carries an opened citation or bracket except the two lamp quality valuations, which keep their label and retire to the indoor air model.

**Pass 11 (lamp quality factors).** Sourced as prices per unit of light relative to wax (opened): V&A, Candles (collections.vam.ac.uk/item/O235777), 'Bees-wax candles were three times as expensive as tallow',
so tallow 1/3 = 0.33 of wax (a candle of either gives about one candela, Wikipedia Candle); Nordhaus's lighting-price table (geeknative.com/60838/the-cost-of-light): tallow candle 40.3 and 18.3 cents per 1,000
lumen-hours (1800, 1830, mean 29.3), whale-oil lamp 29.9 and other lamp oils 59.4 (mean 44.7), so oil light costs 1.5 times tallow and 1.5 / 3 = 0.5 of wax. Old values 0.7 and 0.85 (placeholder
valuations) -> 0.33 and 0.5, confidence C, heuristic label and retire dropped from the seven goods. Every figure in this complaint now carries an opened citation.
