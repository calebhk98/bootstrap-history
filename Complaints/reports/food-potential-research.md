# Food potential gaps: research and build plan (Complaint 411)

Research report only; no code or data changed. Tags on every source: **read** (text of the page or abstract seen this session), **snippet** (seen only as a search-result excerpt), **recalled** (from memory, to be verified before a number is committed). Per CLAUDE.md 4.1 and 4.5, every rule below derives an outcome from geography, physics or biology; no rule reads a historical result. Numbers appear only in tables with a source and tag; measure anything else with the commands given.

## 0. How the current model is built (read from the repo)

- `sim/geography/food_capacity.py` adds tuples from five source modules: `food_crops.py`, `food_pasture.py`, `food_wild.py` (hunting, foraging), `food_fishing.py`.
- Map layers are baked offline by `python3 -m sim.geography.layer_build [--layers a,b] [--cache DIR]` (`sim/geography/layer_build/`). `catalog.py` registers each layer with its source, method and confidence. `cache.py` downloads public datasets once into `~/.cache/bootstrap-history/geography-build`. Layer files in `data/world/geography/layers/*.json` carry `source` and `method` strings. The build needs `numpy`, `rasterio`, `shapely` and `pyhdf`, which are build-only dependencies.
- Existing external sources: WorldClim 2.1 at 10 arc-minutes (temperature, precipitation, elevation, ruggedness), Natural Earth 1:10m (rivers, bathymetry L_0 and K_200, 1:50m land), Oregon State VGPM monthly net primary production (ocean), ESA WorldCover tree fraction (forest).
- Tiles are equal-area grid cells clipped to land (`data/world/geography/tile_grid.json`), carrying `land_area_km2`, `arable_fraction`, `fertility_quality_multiplier` and `koppen_class`. The last three are per-Koppen-class constants from `tools/generate_geography_tiles.py`, not per-tile measurements.

### Measurements taken (command: `api.food_potential(tile)`, shown as people supported = kcal / the `food_kcal_per_person_year` parameter)

| Tile | Class | Land km2 | Crops | Pastoral | Hunting | Marine | Total |
|---|---|---|---|---|---|---|---|
| netherlands_01 (North Sea) | Cfb | 24,218 | 931,896 | 67,772 | 3,928 | 236,863 | 1,248,159 |
| germany_03 (North Sea) | Cfb | 94,545 | 3,373,693 | 217,916 | 15,442 | 241,249 | 3,859,207 |
| canada_44 (subarctic) | Dfc | 113,129 | 0 | 153,657 | 8,908 | 17,332 | 181,664 |
| canada_47 (subarctic) | Dfc | 150,000 | 0 | 121,926 | 12,058 | 0 | 136,236 |
| brazil_44 (rainforest) | Af | 150,000 | 2,961,868 | 7,060 | 39,637 | 0 | 3,026,406 |
| angola_06 (savanna) | Aw | 150,000 | 6,384,152 | 446,507 | 41,288 | 0 | 6,896,139 |

Observations:
- The North Sea tiles get a similar marine total from one shared sea: netherlands_01 and germany_03 each read a shelf zone that covers most of the North Sea. Summing `shelf_area_km2` over all tiles gives a figure well above the physical shelf area (compare with a published world shelf area, not yet sourced), which indicates the overlap (measure: sum the `values` of `data/world/geography/layers/shelf_area_km2.json`). The Netherlands tile, with a land area about a quarter of Germany's, gets almost the same marine total as Germany.
- Subarctic canada_47 supports roughly one person per km2 from pasture alone with no growing-season term.
- Af brazil_44 has an `arable_fraction` of 0.15 and fertility 0.65 (class constants), and 2,715 mm of rain falls on the wet tail of `food_crop_water_envelope` (optimal to 2,000, tolerated to 3,500). Aw angola_06 has 0.30 and 0.80 with 1,027 mm of rain, inside the optimal band. Both factors favour savanna, so the gap is two stacked heuristics, not one.

## 1. Marine fishing: partition the shelf, cap by sustainable yield

**Rule.** Replace the per-tile overlapping zone with an additive share. Rasterise the fishable shelf (Natural Earth bathymetry L_0 minus K_200, the existing inputs) on an equal-area grid, assign each shelf pixel to the nearest tile land (nearest-coast Voronoi: distance transform over the union of tile land polygons, label of the nearest land pixel), and sum per tile. Ties (equidistant) split evenly. Limit assignment to pixels within a craft reach of land, where reach = hours a day-return trip allows times craft speed under oar or sail, so the access fraction `food_marine_access_fraction` (a heuristic) becomes a derived distance. Pixels beyond reach are unassigned (open shelf nobody works yet, and a later sea-going technique raises the reach). Productivity stays the VGPM mean, now averaged over the tile's own assigned pixels.

Yield: keep the Pauly and Christensen chain (primary production, ten percent transfer per trophic level, nine g wet per g carbon), but make the harvest fraction a bound with a source: sustainable harvest as a share of fish production at maximum sustainable yield (logistic surplus production gives maximum sustainable yield at half the carrying capacity, one quarter of the intrinsic growth rate times carrying capacity). Cross-check totals against catch per shelf area by region.

| Fact | Value or statement | Source | Tag |
|---|---|---|---|
| Primary production required to sustain world catches, share by system | Under 2% of open ocean, above 20% for upwelling, shelf and freshwater | Pauly and Christensen 1995, Nature 374:255, https://fishbase.se/Ecopath/PPRnatur.htm | snippet |
| Energy transfer between trophic levels | Ten percent | same | snippet |
| Shelf catches per area | Range from 0.1 to 30 t/km2/yr, most 1 to 10, modal 3 to 6 | Search excerpt of a shelf-yield-per-area review at https://journal.nafo.int/Volumes/Articles/ID/285/ (Have peak fishery production levels been passed in continental shelf area) | snippet (modern industrial catches, an upper check, not a pre-industrial target) |
| Regional peaks of shelf-dependent resources | Arcto-boreal 2.1 to 2.7 t/km2, south-boreal 0.5 to 2.2, tropical and subtropical 0.4 to 0.9 | same | snippet |
| Ryther world maximum sustainable fish yield from primary production | Order of 100 million t | Ryther 1969 Science 166:72 | snippet |
| Sea Around Us catch by cell and large marine ecosystem | Catch reconstructions, 0.5 degree cells | https://www.seaaroundus.org | recalled |
| Logistic surplus production model | Maximum sustainable yield = rate times carrying capacity over four | Schaefer 1954 | recalled |

**Pre-industrial limits with sail and oar.** The dominant limit is not stock but range, gear and labour: shore-based and day-boat fisheries within sight of land; fish must be preserved (salt, drying) to be traded, which couples to the salt and trade models. Derive reach from craft speed and a daylight working day; derive catch from gear catch per unit effort (hook and line, drift net, weir) times effort days per season, so the harvested share of a stock is an output. Sources to read before committing numbers: Hoffmann, *An Environmental History of Medieval Europe* (herring, cod fisheries), Barrett et al. on the medieval fish event horizon (all recalled, none read).

**Files and fields.**
- New layer `fishing_shelf_km2` in `sim/geography/layer_build/layers_vector.py` (next to `shelf_area_km2`, reusing `sea_zones`) and a new entry in `catalog.py`; `ocean_productivity_gc_m2_yr` in `layers_ocean.py` changed to average over the assigned pixels. Rename or drop `shelf_area_km2` (CLAUDE.md 4.6 allows it); update `extent_layer` in the three `shelf_*` rows of `data/world/geography/resources/animals.json`.
- `food.json`: retire `food_marine_default_shelf_area_km2`, replace `food_marine_access_fraction` with a craft-reach parameter and a derived access rule in `sim/geography/food_fishing.py`.
- Dataset to download: none new. Natural Earth (public domain) and VGPM are already cached. Voronoi on a raster: a few hundred MB of working memory at most at 10 arc-minute equivalent resolution, one pass.

## 2. Cold pasture: season length, snow, winter fodder

**Rule.** Carrying capacity is set by the scarcest season (Liebig on the year, not on the annual mean):

    heads_supported = minimum(forage_available_in_growing_season / intake_per_head_in_that_season,
                              winter_feed_available / intake_per_head_over_winter_days)

with winter_feed_available = standing forage that survives the winter and is reachable under snow, plus hay or browse the herders store, plus lichen for reindeer. Growing-season forage production = minimum(rain-limited Sala term, temperature-limited term scaled by the share of the year with mean temperature above the grass growth threshold). The current formula uses annual rain only, so a short season costs nothing.

**Data.** A growing-season and snow-month layer needs no new download for the first stage: WorldClim monthly mean temperature is already read by `layers_raster.py` (it takes the monthly minimum and maximum). Add `growing_months` (months with mean temperature above the grass growth threshold, a physical quantity) and `cold_months` (months below the freezing point) and a growing-degree-day sum. For snow itself, an optional second stage reads satellite snow cover.

| Dataset | Content and limits | Source | Tag |
|---|---|---|---|
| WorldClim 2.1 monthly tavg and prec, 10 arc-minute | Already cached; the monthly series gives months above a threshold with no new download | https://worldclim.org/data/worldclim21.html | read (existing layer source) |
| MODIS/Terra snow cover monthly CMG, 0.05 degree (MOD10CM, version 61) | Monthly mean snow cover on a 7200 by 3600 global grid, HDF-EOS; open use with citation; Earthdata login may be needed to download | https://nsidc.org/data/mod10cm | snippet |
| GAEZ v4 reference length of growing period, 5 arc-minute | Module of agro-climatic indicators; portal https://gaez.fao.org; licence believed to restrict commercial use (check) | https://www.fao.org/gaez/gaezv4/en | snippet (portal), licence recalled |
| Fennoscandian reindeer: lichen biomass and animal density | Mean lichen biomass in Finnish herding ranged from 54 to 380 kg dry matter per ha, correlating negatively with animal density per lichen range (1.5 to 14.3 animals/km2); economic carrying capacity of lichen range 900 kg dry matter per ha | Rangifer articles at https://septentrio.uit.no/index.php/rangifer/article/download/840/803/3202 | snippet |
| Winter pasture limits most reindeer populations | Winter lichen pasture is the limiting factor | same family of sources | snippet |
| Mongolian steppe | Lack of winter and spring feed is the major constraint on herd size | https://www.mongoliajol.info/index.php/JASE-A/article/view/3399/3764 and Frontiers in Sustainable Food Systems 2023 article https://www.frontiersin.org/articles/10.3389/fsufs.2023.1186899/full | snippet |
| Non-equilibrium rangelands | Below roughly 300 to 400 mm rain, or above 30% coefficient of variation of rain, herds follow rain, not stock, and are limited by drought crashes | Ellis and Swift 1988, J. Range Manage. 41:450 | snippet |
| Pastoral herd sizes, milk and offtake | Herd sizes and yields per head | Dahl and Hjort 1976, *Having Herds* (already the source for animal rows) | recalled |

**Checks.** Compute herd densities for reindeer on tundra and subarctic tiles and compare to the Fennoscandian range above; for yak on the Tibetan plateau compare to published stocking rates (recalled, to be sourced in stage 2); a subarctic tile with no lichen layer should fall far below the current output.

**Files and fields.**
- New layers `growing_months`, `cold_months`, optionally `snow_months`, added in `layers_raster.py` and `catalog.py` (the same worker that reads WorldClim). Fallbacks from class values go in `data/world/geography/derived_layers/` like the existing climate fallbacks.
- `sim/geography/food_pasture.py` `usable_forage_kg`: apply the season term and the winter-feed minimum. New parameters in `food.json` (grass growth temperature threshold, winter intake days from `cold_months`, snow-reach fraction). Reindeer need a lichen term; either a `lichen_fraction` proxy from land cover (tundra and boreal open forest) or an `if_missing` envelope until a layer exists (open question 2).
- Download: stage 1 none. Optional MODIS snow: about 12 monthly files, each tens of megabytes (recalled size), public domain style open licence with citation, login required.

## 3. Slope

**Rule.** The terrain-limited share of land is the share of the tile's land below a slope threshold, from a slope class distribution, not from `elevation_std_m`. `arable_fraction_effective = arable_fraction_by_climate_and_soil * share_of_land_with_slope_below_cultivation_limit(technique)`. Terracing is a technique that raises the limit and costs labour per hectare (construction plus maintenance), so the same actor-neutral mechanism serves any country. Grazing: stocking falls with slope because animals avoid steep ground and erosion risk rises; a use-factor multiplier by slope class.

| Fact | Statement | Source | Tag |
|---|---|---|---|
| GAEZ integrates terrain slope classes with soil and climate into suitability, with extents of soil units tallied by slope class | | https://www.gaez.iiasa.ac.at/docs/GAEZ_MD_02.02.2012.pdf, https://pure.iiasa.ac.at/id/eprint/6667/1/RR-02-002.pdf | snippet |
| GAEZ slope class breakpoints and their reduction factors (rainfed arable limit about 8 to 16 percent; above about 30 percent not cultivable without terraces) | | Fischer, van Velthuizen, Nachtergaele 2002 (the IIASA report above), Table of slope classes | recalled, must be read from the report before use |
| Grazing slope adjustments (use falls on slopes above about 10 to 30 percent) | | Holechek et al., *Range Management: Principles and Practices* | recalled |
| Terrace construction labour per hectare | | Ethnographic and engineering studies of Andean, Chinese and Mediterranean terraces | recalled, no source found yet |

**Data.** The existing `ruggedness_index` is a 10 arc-minute neighbour difference, far too coarse to make slope classes; a slope-class share needs a finer elevation model. Options: GMTED2010 (USGS, public domain, 30 arc-second, global; tile size from a few hundred megabytes), SRTM 90 m (public domain), or GAEZ's own slope layer (licence to check). Recommend a baked layer set `slope_share_below_<class>` (fractions of land under each class breakpoint) so the technique can read the cumulative share at its limit. Build in `layers_raster.py` with a new cache entry in `cache.py`.

**Files and fields.** `sim/geography/food_crops.py` (`arable_hectares` times the cumulative slope share at the actor's limit; limit read from `technique_factors`, parameter `food_slope_limit_without_terracing`), `sim/geography/food_pasture.py` (slope use factor), new layers in `catalog.py`, and a terracing labour entry in the labour model (open question 4). Do not use the class-constant `arable_fraction` for slope; it is generated by `tools/generate_geography_tiles.py` from the Koppen table.

## 4. Competition: grass shared with wild grazers, depleted hunting stocks, forest off cropland

**Rule A, grass.** Compute the wild herbivore biomass the grass can carry (Coe, Cumming and Phillipson 1976: large herbivore biomass increases with rainfall and primary production in African reserves; read the regression coefficients before use). Herds and wild grazers draw on one forage pool: forage_for_herds = usable_forage minus wild_grazer_consumption, where wild consumption = wild stock (at its current fraction of carrying capacity) times intake. Hunting then removes stock, so hunting and herding trade off through the same pool. Because this couples sources, state it in `food_capacity.py` as an ordered allocation (wild first, then herds, then residual) with the order a parameter, not a code branch.

**Rule B, hunting stock.** The current Robinson and Redford production model gives yield at the peak production stock fraction. Make stock a state variable (logistic harvest: surplus production = growth rate times stock times one minus stock over carrying capacity; maximum sustainable yield at half the carrying capacity) so harvest above surplus depletes stock over time. Static food potential reports the sustainable yield; the dynamics belong to the world sim.

**Rule C, forest.** Subtract forest from cropland: arable land = arable_fraction times (land minus forest area not yet cleared), with clearing a labour cost. `forest_fraction` is present-day cover, not potential vegetation (its layer doc says so), so cropland already reads as partly cleared today; the correct input is potential forest from climate, with clearing a technique-and-labour mechanism. This ties to rainforest (section 5).

| Fact | Source | Tag |
|---|---|---|
| Large herbivore biomass against rainfall and primary production | Coe, Cumming and Phillipson 1976, Oecologia 22:341, https://link.springer.com/article/10.1007/BF00317566 | snippet (exists, regression not read) |
| Equilibrium and non-equilibrium rangelands | Ellis and Swift 1988 | snippet |
| Maximum production at 0.6 of carrying capacity, growth rate 1.5 times mass to the minus 0.36 | Robinson and Redford 1986, 1991 (already in `food.json`) | recalled |
| Logistic surplus production, maximum sustainable yield at half carrying capacity | Schaefer 1954; Hilborn and Walters 1992 | recalled |

Files: `sim/geography/food_pasture.py`, `food_wild.py`, `food_crops.py`, parameters in `food.json`.

## 5. Tropical rainforest against savanna

**Rule.** Replace the Af arable fraction constant with shifting-cultivation geometry. A plot is cropped for a few years then fallowed until the secondary forest rebuilds the nutrient stock. Cropped share of land = crop_years / (crop_years + fallow_years); fallow_years = years of regrowth to restore the cleared nutrient stock, which falls as net primary production and soil nutrient supply rise (read from the existing `net_primary_production`). Yield per cropped hectare in the first years is high (ash from burnt biomass), so the rainforest result is a modest density per km2 from a low cropped share, not a poor yield. Add a temperature-dependent leaching and weed pressure as a function of rainfall to the wet side of the water envelope, instead of the arbitrary tolerated cutoff. Fallow ratio classes: cropped share below one third is shifting cultivation, one third to two thirds short fallow, above two thirds permanent (from the Ruthenberg R-value, snippet).

| Fact | Source | Tag |
|---|---|---|
| Critical population density: the highest density a given system carries without degradation (Allan 1965) | https://www.fao.org/4/r1340e/r1340e04.htm (FAO shifting cultivation text) and search excerpts | snippet |
| Fallow ratio R = cultivation years times 100 over total cycle; R below 33 shifting, 33 to 66 short fallow, above 66 permanent | search excerpts of Ruthenberg-based literature | snippet |
| Amazonian uplands: fallow usually several decades after one to two years of farming; low carrying capacity | Fearnside, https://repositorio.inpa.gov.br/handle/1/19656 and https://philip.inpa.gov.br/publ_livres/Preprints/1997/Human%20Carrying%20capacity-EC-preprint.pdf (page returned 503, not read) | snippet |
| Nutrient and fallow dynamics | Nye and Greenland 1960, *The Soil under Shifting Cultivation*; Conklin 1957; Ruthenberg 1980 *Farming Systems in the Tropics* | recalled |

Files and fields: `tools/generate_geography_tiles.py` (the `KOPPEN_ARABLE_AND_FERTILITY` table is the class constant to retire; its Af and Aw lines are the only per-class numbers involved), `sim/geography/food_crops.py` (cropped-share rule), `food_crop_water_envelope` in `food.json`. No download. Calibration test: Af density should land inside a published range for shifting cultivators on a similar soil (extract from Fearnside and Allan before building).

## 6. Labour caps

**Rule.** A producer feeds a bounded number of people: people_fed_per_worker = worker_kcal_output_per_year / kcal_per_person_year, with kcal output = effort_days * catch_per_unit_effort * edible kcal. Derive effort days from the labour model (`sim/labour/`), catch rate from gear, boat capacity and stock density. The food potential (a ceiling from geography) then becomes `min(ecological_potential, labour_applied * output_per_worker)`, per source. Hunters: return rates in kcal per hour from the optimal foraging literature. Herders: animals one household can tend, from herd management (milking labour, watering, guarding). Fishers: boat crew, trips per season, catch per trip.

| Fact | Source | Tag |
|---|---|---|
| Hunter-gatherer diet breadth, return rates in kcal per hour, and ethnographic densities | Kelly 2013, *The Lifeways of Hunter-Gatherers: The Foraging Spectrum*, Cambridge UP; Binford 2001 *Constructing Frames of Reference* | snippet (catalogue entries found, tables not read) |
| Foraging return rates | Winterhalder and Smith 2000, Evolutionary Anthropology 9:51 | recalled |
| Pastoral labour and herd size per household | Dahl and Hjort 1976 | recalled |
| Fishing effort and catch per man-day | Historical North Sea and Norwegian fishery records; ethnography of the Northwest Coast | recalled, no source yet |

These belong to the labour package behind `sim/labour/api.py`; geography exposes the ceiling and a per-source energy per worker-day parameter, per the package walls (`docs/architecture/PACKAGE_WALLS.md`).

## Staged build plan

| Stage | Change | Data | Tests (smallest regression) | Fingerprint |
|---|---|---|---|---|
| 0 | Measure: add the overlap factor to a test (sum of shelf zones against the physical shelf) and record the six measurements above in a test fixture | none | Assert North Sea tiles' marine share per land km2 exceeds their crop share (documents the bug) | records baseline |
| 1 | Season layers `growing_months`, `cold_months`, growing degree days from cached WorldClim monthly data; season term in `usable_forage_kg` | none new | Subarctic tile pasture falls far below a temperate tile of equal rain; monotonic in season length | moves |
| 2 | Partitioned shelf `fishing_shelf_km2` and per-tile productivity; reach derived from craft speed; retire `food_marine_access_fraction` | none new | Sum of tile shelves not greater than the physical shelf; two neighbouring tiles share a sea without exceeding it; a landlocked tile gets zero | moves |
| 3 | Slope classes from a finer elevation model; slope share in crops and pasture; terracing technique factor | GMTED2010 or SRTM, public domain, size to be measured | A flat tile unchanged; a mountainous tile loses arable share; terracing restores it at a labour cost | moves |
| 4 | Shared forage pool and ordered allocation; hunting stock logistic term | none | Adding wild grazers reduces herd output on the same tile; hunting at maximum sustainable yield is stable | moves |
| 5 | Shifting cultivation rule for Af and Am; forest as potential, with clearing labour | none | Af density falls in the shifting-cultivation range; Af no longer below Aw in kcal per km2 by an unexplained margin | moves |
| 6 | Labour caps per source through the labour api | none | Fisher count scales food output linearly up to the ecological ceiling | moves |
| 7 | Optional snow-cover month layer from MODIS; reindeer lichen term | MODIS MOD10CM, login | Lichen tiles carry reindeer within published density range | moves |

Run `python3 sim/simulator.py validate` after any `data/` edit, `python3 -m sim.tests --slow` before a pull request, and record and check the fingerprint around every stage (`python3 -m sim.tests.fingerprint record before.json`, then `check`). Heuristic count: re-measure with the `parameters.heuristics` command from the complaint after each stage; stages 1, 2 and 5 should remove heuristics (`food_marine_access_fraction`, `food_marine_default_shelf_area_km2`, the Af arable constant), not add them.

## Ready to build now

- Stage 0, stage 1 (no download, uses cached WorldClim monthly data), stage 2 (no download, uses cached Natural Earth and VGPM), stage 4 (pure code and parameters), stage 5 (needs a source read first but no download).

## Open questions

1. Reach rule for fishing: derive from the freight and route-mode craft speeds in `sim/geography` (check `data/world/geography/route_modes`) or from a new fishing parameter? Which authority owns craft range?
2. Reindeer winter feed: no lichen layer exists. Use a land-cover proxy (tundra and open boreal forest) or bake a lichen cover layer? None found with open licence.
3. Which slope source: GMTED2010 versus SRTM, and does the GAEZ licence allow redistribution of derived values (believed non-commercial; unverified).
4. Terracing labour per hectare: no source found; needs an agricultural engineering reference.
5. Potential versus present forest: `forest_fraction` is 2020 land cover; a potential vegetation layer (for example from climate class or a published potential natural vegetation map) is needed before forest can be subtracted from cropland without double counting modern clearing.
6. Whether stock depletion (stage 4, hunting) belongs in this static model or in the world simulation that steps time; the static function can report only sustainable yield.
7. Facts marked recalled (GAEZ slope breakpoints, Holechek slope factors, Coe regression, labour figures) must be read from the originals before any value is committed to `data/`.
