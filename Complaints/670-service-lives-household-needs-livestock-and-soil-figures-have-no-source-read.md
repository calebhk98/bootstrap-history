# Service lives, household-need, livestock, spoilage and soil figures have no source that was read

**Status:** open

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
  `python3 sim/constants.py --burndown | grep soil_nutrients`. The three-field legume share in `sim/world/agriculture.py`
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

**Test.** `sim/tests/test_recalled_figures_sourced.py` holds what was sourced; `sim/tests/test_constants_retirement.py` keeps
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
