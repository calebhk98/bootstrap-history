# History of Complaint 646 (as it stood before it was trimmed)

Moved from the complaint file. Figures and line numbers here are as of the time they were written and may be stale; the complaint carries the current state. The wheat-labour figures of pass 5 (150 hours, then 554) are superseded by passes 6 and 7 (Columella read in the primary).


Owner direction (2026-10-20): a figure needs a source someone read; "recalled" is not a source. The data and the
declared constants carry many figures marked as recalled (confidence D), from the herd rows (532) to the savings
constants (606). List them:

    grep -rn "recalled" data sim --include=*.json --include=*.py | wc -l

What it would take: for each, find and read a source and record it (author, work, page or URL, and the passage), or
mark the figure as having none and keep it a labelled heuristic with a `retire`. The rule for new work is in
CLAUDE.md section 6. Research agents follow the same rule: every claim cites a source opened in that session.

## Pass 1

Count of lines containing "recalled" in `data` and `sim` (`.json` and `.py`) after the pass: measure with the
command above (about 102 left, from about 150). Sources were opened as PDFs or pages in the session that wrote
this note; passages are quoted in the files named.

Sourced (opened), with changed values:
- `data/world/living_stock.json` sheep, goat, cattle `dung_and_fodder_source`: USDA NRCS, Agricultural Waste
  Management Field Handbook, Part 651 chapter 4 (rev. July 1996), Table 4-18 lamb 40.00 lb/d/1000 lb (sheep 0.04
  kept); Table 4-8 beef cow 63.00 (cattle `manure_share_of_live_weight_per_day` changed 0.08 to 0.063; the 0.08 was
  the dairy figure of Table 4-5; `manure_kg` of the cattle herd recipe in `data/production/95_herds.json` changed
  from 240900 to 189708.75 to follow). Goat has no row in the handbook: the sheep figure is used, no source found.
- Same rows, winter ration 2 percent of live weight a day: South Australian government fact sheet "Calculating dry
  matter intakes for various classes of stock" ('Animal on dry pasture or poor quality feed: 2%').
- `cattle_kg` source: FAO, Production parameters of ruminants in traditional systems (fao.org/4/Y4176E/y4176e08.htm):
  offtake 9.9 percent mean, mature cow 244 kg mean (median 250), milk 252 kg a lactation. Values kept (10 percent,
  250 kg, 250 kg).
- `sim/geography/soil_nutrients.py`: `MINERALISATION_RATE_PER_YEAR` (Oregon State Extension EM 9281, 1 to 3
  percent, kept 0.02); `HERD_EXCRETA_KG_PER_LIVE_WEIGHT_KG_YEAR` (NRCS Table 4-8 beef cow, changed 29.0 to 23.0, the
  old figure was the dairy cow); `MANURE_NITROGEN_FRACTION` (NRCS Table 4-8, 0.33 / 63.00 = 0.52 percent, kept 0.005).
- `sim/economy/households_orders.py`: `SAVINGS_RATE_RESPONSE_LIMIT` and `SAVINGS_RESPONSE_FLOOR` cite Bernheim,
  Taxation and Saving (NBER Working Paper 7061; the sign of the interest elasticity cannot be given by theory; studies
  put it at or near zero; precautionary saving is insensitive to the return). The sizes remain assumptions.
- `data/world/needs.json`: salt subsistence (National Academies, Dietary Reference Intakes for Water, Potassium,
  Sodium, Chloride, and Sulfate, 2005, Summary: sodium AI 1.5 g a day); water subsistence (Howard and Bartram, WHO
  2003, basic access 20 l/c/d); candle lumen-hours (Wikipedia, Candela: 1 cd, 4 pi lumens).

No source found, now labelled (python ones `kind="temporary_heuristic"` with `retire` naming this complaint or 607):
- `HOUSEHOLD_TIME_PREFERENCE`, `SAVINGS_YEARS_OF_SURPLUS_INCOME`, `SPENDING_CUT_LIMIT`, `WEALTH_DRAWDOWN_LIMIT`
  (retire stays Complaints/607).
- `soil_nutrients.py`: `NATIVE_POOL_KG_PER_HECTARE`, `LOSS_RATE_PER_YEAR`, `GRAIN_NITROGEN_FRACTION`,
  `LEGUME_NET_NITROGEN_KG_PER_HECTARE`, `MANURE_AVAILABLE_FIRST_YEAR`, `MANURE_RETAINED_IN_POOL` (kind changed to
  `temporary_heuristic`, confidence D, retire Complaints/646).
- `living_stock.json`: sheep fleece, salt and stocking rates; goat stocking, milk; cattle dressing, fat, hide, horn,
  salt and stocking; goat excreta share.
- `needs.json`: housing satiation multiple, salt satiation (the WHO 2012 sodium guideline was opened and does not
  give a 9 to 12 g mean), pottery stock (Deal), coin stock (Duncan-Jones), tallow and oil lamp quality factors.

Tests: no test needed a bound changed; the byproduct test followed the species row, which is why the herd recipe
value moved. `currency.py` carried no "recalled" line; the 606 constants are those in `households_orders.py`.

Not touched, still open: `data/production` rows (organics, lighting, herds labour), `trades.json`, `spoilage.json`,
`waste_heaps.json`, disease files, civilisation notes, `agriculture.py`, test docstrings.

## Pass 2

Scope: `data/production` rows, `data/world/trades.json`, `spoilage.json`, `waste_heaps.json`. Skipped: disease files,
test docstrings, `95_wine_oil_jars.json` (Complaint 656). Count of "recalled" lines in `data` and `sim` (`.json`,
`.py`) fell from 102 to 34 with the grep above (the rest are disease, civilisation, geography, needs, agriculture,
soil, service-life and wine/oil/jar lines).

Sourced (opened), with changed values:
- `data/production/95_herds.json:23`, `:17`, `:92`, `:98`: Varro, De re rustica 2.2.20 and 2.10.11 (LacusCurtius):
  one shepherd to a hundred rough-fleeced sheep. Head per shepherd changed 150 to 100; sheep herd `herder` hours
  1743.362 to 2543.362 and sheep_kg `herder` 24.0 to 36.0 follow. No test pinned them.
- `data/world/waste_heaps.json:29` (manure, text at `:33`): NRCS Part 651 chapter 4, Table 4-8 beef cow, 63.00 lb/d
  over 1.00 ft3/d = 63 lb/ft3; density changed 750 to 1009 kg/m3. Straw (`:49`): Table 4-3 gives 40 loose and 112
  chopped kg/m3; 60 kept, labelled. Urine (`:57`): Rose et al. 2015 (PMC4500995), specific gravity 1.002 to 1.037;
  1.01 kept.
- `data/production/95_town_excreta_and_gardens.json:12`, `:24`: Rose et al. 2015, urine median 1.4 L a day,
  faeces median 128 g wet a day. Values kept.
- `data/production/95_fish.json:32`: Flick, Global Aquaculture Advocate 2010, p. 43, salt to fish 1:8 to 1:1; 1:5
  kept.
- `data/production/99_water_supply.json:78`: Encyclopaedia Romana "Quinaria" (41.5, 38.0, 32.8 m3 a day) and
  Frontinus De aquis 25; 40 kept.
- `data/production/40_organics.json:94`: Cato 162, half a modius of salt a ham (gives no share by mass).
- `data/production/40_organics.json:983`: Gilbert White, Selborne Letter XXVI via Wikipedia "Rushlight" (burn time
  only).
- `data/world/spoilage.json:11`: Clemson HGIC 3525, bread 3 to 7 days.
- `data/world/trades.json:403`: Statute of Artificers 1563, seven years (via Wikipedia); `:136`, `:433`: Pliny 35.57
  heading and Vitruvius II.5 opened, neither gives a training period.

No source found, now labelled (file:line): `40_organics.json:43,60,77,94,255,345,360,380,398,732,983,121`;
`95_staple_grains.json:17,34` (Donald and Hamblin 1976 not openable); `94_agri_organics_gaps.json:205`;
`95_bread.json:19`; `95_fish.json:32,51`; `95_grain_milling.json:18,36,54`; `95_herds.json:23,51,79,98,114,130`
(2400-hour year, goat and cattle head per herder); `95_mesoamerican_stock_and_game.json:18`;
`95_leather_goods.json:2,17`; `95_town_excreta_and_gardens.json:36`; `99_carriers.json:19`;
`99_lighting.json` (all rows); `99_ships.json:32,56` (Kyrenia 25 t, Olympias 25 t; Wikipedia gives 47 t displacement
uncited); `spoilage.json:10,12,13,14,15`; `trades.json:30,177,262,393,413,423,443,453`;
`waste_heaps.json:17,41` and all heights.

Still open: 34 lines (disease, civilisation notes, `needs.json`, `agriculture.py`, `soil_nutrients.py`,
`service_lives.json`, deposits, wine/oil/jars). Several "no source found" figures have candidate sources not yet
opened: tallow candle burn rate (Nature 16, 1877, p. 361), Geoponica 20.46 (Owen), King, Farmers of Forty Centuries.

## Pass 3 (needs and soil)

Remaining lines: `grep -rn "recalled" data sim --include=*.json --include=*.py | wc -l` (the rest are disease files,
civilisation notes, deposits, service lives, the three-field legume share in `agriculture.py`, wine/oil/jars, and test
docstrings).

Sourced (opened), with changed values:
- `data/world/needs.json` salt `satiation_per_capita_per_year` 3.65 to 3.67: Powles et al., BMJ Open 2013;3:e003733,
  abstract, 'global mean sodium intake was 3.95 g/day ... equivalent to 10.06 (9.88-10.21) g/day of salt'.
- `sim/geography/soil_nutrients.py` `GRAIN_NITROGEN_FRACTION` 0.02 to 0.025, no longer a heuristic: Clay and Carlson,
  SDSU iGrow Wheat ch. 12 (2019), 'If 1 bushel wheat contains 1.5 lbs of N' with a 60 lb bushel. A modern wheat.
- `needs.json` vessels: Nelson, ch. 8 of Longacre ed., Ceramic Ethnoarchaeology (1991), Tables 8.1 and 8.3: the 4 year
  use-life lies inside the reported range (cooking pots 0.4 to 13 years); values kept, mass per vessel still no source.
Tests: `sim/tests/test_recalled_figures_sourced.py`.

No source found: three-field legume share (searches gave the crops of the spring field, no share); Peoples 2009
legume balance not opened; Deal 1985 and Straight 2017 are paywalled; MSU nutrient removal page blocked.

## Pass 4 (disease files and civilisation starts)

Remaining lines: `grep -rn "recalled" data sim --include=*.json --include=*.py` (the rest are civilisation deposit notes,
deposits, service lives, the three-field legume share in `agriculture.py`, wine/oil/jars, and test docstrings).
No disease source entry is tagged `recalled` now. The civilisation starting figures carry A to D grades, not `recalled`;
only the Mexica and Norse mineral-reach notes contain the word, and those state no figure.

Sourced (opened), with changed values:
- `bubonic_plague.json` `case_fatality` 0.5 to 0.45: WHO plague fact sheet, 'a case-fatality ratio of 30% to 60% for the
  bubonic type' (midpoint). Incubation 4 days kept as the midpoint of WHO 'one to seven days'.
- `malaria.json` temperature envelope tolerated 16-35 to 17-34, optimum upper edge 30 to 28: Mordecai et al. 2013
  (abstract via USGS: optimum 25 C, 'decreases dramatically at temperatures > 28 C'); 17-34 C from Ryan et al.,
  arXiv 1407.7612, quoting Mordecai. Lower optimum edge and rainfall edges: no source found.
- `smallpox.json` infectious stage 21 days kept: CDC overview, scabs fallen 'three weeks after the rash appears'.
- `measles.json`: the unsourced 'higher with malnutrition' clause dropped from the citation.
No source found, now `unsourced`: plague reproduction range (Dean et al. 2018 abstract gives none; full text 403), plague
immunity and infectious stage, smallpox immunity, tsetse range box and climate envelope (the 16 and 32 C of Longbottom
2020 are fitting constants, not limits). Horse loss 0.9 stays `disputed`: Wikivet (secondary) says horses need drugs in
tsetse areas; no magnitude.
Tests: `sim/tests/test_recalled_figures_sourced.py` (`DiseaseFigures`).

## Pass 5 (widened to heuristics and unsourced D entries that shape the opening and labour)

Worklists: `python3 sim/constants.py --burndown` (declared temporary heuristics); data entries with confidence D and no
source: `grep -n '"confidence": "D"' data/world/service_lives.json` and the `conf` D rows of `data/production`.
Tests: `python3 -m sim.tests --only recalled_figures_sourced,shelter_satiation`.

Sourced (opened), with changed values:
- `data/world/needs.json` shelter `satiation_multiple_of_floor` 3.0 to 2.857: Naroll, Floor Area and Settlement
  Population, American Antiquity 27(4), 1962, abstract: population 'very roughly estimated as of the order of one-tenth
  the floor area in square meters' (10 square metres a head); 10 / 3.5 (Sphere floor) = 2.857. Brown, Cross-Cultural
  Research 21 (1987), via the HRAF summary: 6 square metres a head, 38 culture sample (a mean occupancy, lower bound).
  Both are cross-cultural means of settlement dwellings, not a measured limit of wanting more room: still confidence D.
  The Sphere 3.5 itself was not re-opened (spherestandards.org PDF returned 403; shelterprojects PDF unreadable).
- `data/world/service_lives.json` ox 5 years kept: the Medievalists.net page on Langdon was opened ('roughly the same
  life expectancy (a little over 5 years)'; cart horse about 7). Mule 10 years: no source found (NCAT Draft Animal Power
  for Farming gives 15 years for draft horses only); now a labelled heuristic retiring to this complaint.

Found, NOT changed (the value is built into code and tests): `wheat_kg` labour (`data/production/40_organics.json`),
the biggest recipe by volume, carries 150 hours a hectare with no source. Shukurov et al., arXiv 1505.05121 section 8.1
(opened as PDF; secondary), quoting White 1965 on Columella: 44 person-days a hectare for the cycle without harvest and
5.7 for reaping, and Halstead and Jones 1989: threshing takes about as much as reaping. (44 + 5.7 + 5.7) x 10 hour
day = 554 hours; hand tilling 400 h/ha against 65 with oxen (Ellen 1982, same paper) puts `wheat_hoe_kg` at 554 + 335 = 889
against 350 now. Setting 554 (and the `REFERENCE_LABOUR_HOURS_PER_HECTARE` declaration in
`sim/world/shared_constants.py`, which the farm-year model, `land.py` and the labour market share) was tried: the quick
tier then failed in `agriculture` (three tests built on 150 hours, including the reaping window and the land cap) and
`demand_at_scale` (wheat's price rose). Follow-up: re-derive the farm-year model and those tests from the sub-task
hours, then apply 554 and 889. The yield_basis text now cites the opened source and says the value is unchanged.

No source found: iron tool 4 years, wooden tool 2 years, bronze, brass, iron, steel lives, brick, stone, cart,
pack saddle, barge (searched for Roman and medieval iron hoe and spade use-life: only typology and single worn
specimens, no duration; the Swedish 100 g of share iron per hectare of ard ploughing, gupea thesis, was a search
summary, not opened); household time preference and savings constants were not re-searched.

## Pass 6 (wheat labour built from sub-tasks)

Re-opened Shukurov et al., arXiv 1505.05121 (PDF text extracted), section 8.1; the passages quoted in pass 5 are
there as written (White 1965 on Columella: 44 person-day/ha for the cycle excluding harvest, 5.7 for reaping;
Halstead and Jones 1989: processing about the same labour as reaping, reaping 10-30 person-days/ha; Ellen 1982 p. 137:
1 ha in 400 hours by hand tools, in 65 with a pair of oxen). All secondary; White, Columella, Halstead and Jones and
Ellen were not opened.

Done:
- `data/world/farm_labour.json` holds the sub-tasks (cultivation cycle, reaping, threshing as a share of reaping, hand
  tilling) with the quotes; `sim/world/farm_labour.py` builds the hours (person-days at the model's day,
  `HOURS_PER_PERSON_YEAR` over the new declared `WORKING_DAYS_PER_YEAR` in `sim/unit_conversions.py`), the hoe extra
  hours, and the reaping rate (inverse of the reaping sub-task). `REFERENCE_LABOUR_HOURS_PER_HECTARE` is declared there
  (it left `shared_constants.py`, which may import only the registry) and `HECTARES_REAPED_PER_WORKER_DAY` in
  `agriculture.py` follows the same sub-task, so the window ceiling and the hours cannot disagree.
- `wheat_kg` farmer hours 150 to 554, `wheat_hoe_kg` 350 to 889 (`sim/tests/test_farm_labour.py` holds the recipes
  equal to the build).
- Effect on the farm-year model: the annual-hours ceiling is now the smaller one, not the harvest window, so the area
  one worker crops rose and `fraction_of_population_that_must_farm` fell (compute: `python3 -c "from sim.world import
  agriculture; print(agriculture.fraction_of_population_that_must_farm())"`; before 0.2118). The game's farm share fell
  with it: the undisturbed Rome scenario (`_undisturbed_run` in `test_farm_edges_scenario`) read 0.340 / 0.342 / 0.346
  at year index 9 / 19 / 29 and now reads 0.280 / 0.287 / 0.292. So the change moves the farm share further from the
  sourced band (issue 64, Complaint 619), not toward it: more hours per hectare did not raise the share because the
  model's worker was previously window-limited and is now year-limited at a larger area.
- Tests re-derived from rules (never loosened): the pinned headline value is computed from its parts; the "window
  binds" tests build a window-bound crop (`_replace` of the hours) and a year-bound one; the land-cap tests use
  labour built from the reference hours; the demand continuity bound follows the fixture's wheat price; the rescue
  scenario doubles both ceilings; the baseline scenario was re-recorded.
- Halstead and Jones's higher reaping figure (10-30 person-days/ha) is recorded as a range in the data and not used.

Long command for the occupational shares (did not finish inside 4 minutes on this loaded machine, before or after):
`python3 sim/simulator.py economy-check --civs rome_100ad --years 1 --occupations`.

## Pass 7 (Columella read in the primary)

Opened Columella, De Re Rustica 2.12.1 and 2.9.1 (LacusCurtius, Thayer, Loeb translation). 2.12.1: "four or five
modii of common wheat take up four days' work of the ploughmen, one of the harrower, two of the hoer for the first
hoeing and one for the second, one of the weeder, and one and a half of the reaper - a total of ten and one-half days
of labour. Five modii of winter wheat require the same number of days." 2.9.1 gives four modii of wheat to the
iugerum on rich land and five on medium land, so the days are per iugerum. The chapter counts to the threshing-floor
and gives no threshing days.
- `data/world/farm_labour.json` now holds those tasks per iugerum (ploughing 4, harrowing 1, hoeing 2 and 1,
  weeding 1, reaping 1.5) and the iugerum in hectares (0.2523, the 2,523 square metres the wine and press entries of
  `data/production/95_wine_oil_jars.json` cite from Wikipedia); `sim/world/farm_labour.py` converts to a hectare.
- Differs from the secondary figures: cycle excluding reaping is about 35.7 person-days/ha (White as relayed by
  Shukurov et al.: 44) and reaping about 5.9 (White as relayed: 5.7). Columella's are used. Halstead and Jones
  (reaping 10-30 person-days/ha, modern sickle) stay recorded as a modern comparison; their "processing about the same
  as reaping" still sets threshing.
- `wheat_kg` farmer hours 554 to about 475.6; `wheat_hoe_kg` 889 to about 810.6 (`python3 -c "from sim.world import
  farm_labour; print(farm_labour.WHEAT_HOURS_PER_HECTARE, farm_labour.WHEAT_HOE_HOURS_PER_HECTARE)"`). The reaping rate
  rose slightly (about 0.168 ha/day).
- Tests: `test_farm_labour.py` builds data per iugerum, checks the iugerum-to-hectare rule and that the conversion
  matches the one the wine file cites; `test_recalled_figures_sourced.py` restated with Columella's per-iugerum days.
- Not run (long): the farm-share scenario `test_farm_edges_scenario` baseline was recorded at the old hours.
