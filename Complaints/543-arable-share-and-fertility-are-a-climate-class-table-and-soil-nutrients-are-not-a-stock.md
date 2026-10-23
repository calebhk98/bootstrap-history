# Arable share and fertility are a climate-class table, and soil nutrients are not a stock

**Status:** partly done: the soil nitrogen stock, arable share and fertility from the water balance, silt as an input and heavy-soil tillage (below). Open: manure bought by farms through the economy; a soil texture layer; sourced constants.

Reference (an outside design note, not code-aware): soil should be derived from the physical inputs a
tile already has, not looked up. Plant growth is limited by the scarcer of heat and water; rain far
beyond evaporation leaches a hot soil (rainforest), rain near evaporation on flat ground builds deep
humus (steppe black earth), river floods lay down silt. Each harvest removes nitrogen from a soil pool
that manure, legumes, silt or rest restore, so fallow becomes a choice rather than a typed share. Heavy
soils resist tillage until the tool and team can pull hard enough.

## What the code does

- Crop yield on a tile already takes the minimum of a temperature and a water suitability built from
  WorldClim layers (`sim/geography/food_crops.py`, `content_rules.suitability`), which is the
  climate half of the note.
- `arable_fraction` and `fertility_quality_multiplier` come from one table keyed by Koppen class
  (`tools/generate_geography_tiles.py`, "THE CLIMATE TABLE"), with the Mediterranean class anchored
  at the Roman wheat yield and the rest set by agronomic judgement (confidence D). The tile has slope,
  ruggedness, precipitation, temperature and river layers (`data/world/geography/layers/`) that the
  table does not read.
- Nitrogen appears only as the reason a rotation's typed fallow share exists (`sim/world/agriculture.py`);
  no tile holds a nutrient pool that harvests draw down.
- No soil resists tillage; the toolkit changes labour per hectare everywhere alike (537).

## What it would take

- Arable share from slope, forest, wetness and the land-cover layer; fertility from the water
  balance (precipitation against evaporation from temperature), slope and river silt, each relation
  sourced and labelled. The outside note's leaching formula has unsourced constants and is not a
  source in itself.
- A soil nitrogen stock per tile: removed by harvests, restored by manure (herds, 532), legumes,
  silt and rest, so fallow share and yield decline under overcropping emerge.
- A tillage resistance per soil and a draught force per toolkit, so heavy clay and prairie sod open
  only to a heavy plough (537).
- The table kept only as a test reference: the derived values should land near it for the classes it
  covers, as a validation under 4.2.

## Done: soil nitrogen stock

- `sim/geography/soil_nutrients.py`: the share of a tile's native nitrogen pool left, saved as `state.economy.soil_nitrogen`
  (a tile with no entry is native). Each year the harvest's grain nitrogen draws it down; a grain legume's net fixation,
  the humus share of applied manure and the natural input (equal to a native soil's loss, so untouched ground holds still)
  build it. A crop's yield against the reference field follows the year's mineral supply (pool mineralisation, plus nitrate
  that the fallow hectares of the holding leave, plus the manure's available share) with a saturating response, normalised
  to native soil under the two-field rotation. Rates are declared with sources (most recalled, marked) in that module.
- Geography only multiplies: `crop_site(..., nutrient_factor)` and `food_potential(..., nutrient_factors)`.
  `sim/engine/soil_nitrogen_year.py` owns the yearly step (phase `soil_nitrogen`) and feeds the factors to the tile food view
  and `Sim.farm_sites()`. `Rotation` gained `legume_share_of_holding` (three-field: half the spring field).
- Manure is a transitional rule (`MANURE_COLLECTED_SHARE`, `sim/geography/soil_nutrients.py`): the society's draught herd's collected
  dung is spread over the held cropland. Dung is made by herd and draught recipes (544, closed: `data/production/95_herds.json`) but the only
  recipe that takes it as an input is the nitre bed (`data/production/60_nitrogen.json`); no farm recipe buys it. The constant's `retire`
  still names 544, which is closed: it should name this complaint (the retirement is a farm recipe with manure as an input).
- Tests: `sim/tests/test_soil_nitrogen.py`, `test_soil_nitrogen_whole_game.py`.

## Done: the farm model reads the stock

- `Sim.refresh_farm_territory()` (`sim/engine/soil_nitrogen_year.py`) rebuilds the farm's ladder, ceiling and the cleared
  ground's quality from `farm_sites()` at the start of each year (and after a load), so national farm yield follows the soil
  nitrogen stock and the society's rotation. `THREE_FIELD_SOIL_FERTILITY_YIELD_MULTIPLIER` is deleted: the three-field
  rotation's edge is its smaller fallow (more cropped hectares) and its legumes' gain to the stock.
- Tests: `sim/tests/test_farm_follows_soil.py` (continuous cropping lowers the ladder's harvest weight and the cleared
  ground's quality over thirty years; three-field with legumes holds a higher stock and harvest than without; the ceiling
  follows a rotation change). The Nile rotation keeps its own silt multiplier until silt is an input.

## Done: arable share, fertility, silt and tillage (this round)

- `sim/geography/soil_water_balance.py`: FAO-56 (Allen et al. 1998, chapter 3, opened at fao.org/4/x0490e/x0490e07.htm) extraterrestrial radiation
  (eq 21 with 23 to 25; checked against Example 8) and Hargreaves evaporation (eq 52) on twelve monthly temperatures from the map's mean, coldest and
  warmest month; the aridity index is rain over that (UNEP classes, en.wikipedia.org/wiki/Aridity_index, opened).
- `sim/geography/soil_derivation.py`: arable share (ceiling times a rainfed moisture ramp over the UNEP bounds times growing months), fertility (humus peaking
  where rain nearly balances evaporation, less leaching of hot wet ground) and a heavy-soil share (flat wet ground; a stand-in for texture). Coefficients are
  `data/world/geography/parameters/soil.json`, each with its source or "no source found". `tools/generate_geography_tiles.py --rederive` writes the three
  tile fields from the layers (no network); `test_soil_derivation` holds the stored values equal to the rule, and checks the rule against the old
  Koppen-keyed table, now only `sim/tests/koppen_soil_reference.py`, by class (CLAUDE.md 4.2). Deviations: tropical savanna and dry steppe come out more fertile than the
  table's judgement, because the rule has no weathering age.
- Silt is a nitrogen input of flooded hectares (`soil_nutrients.SILT_NITROGEN_KG_PER_FLOODED_HECTARE`, from the pre-dam Nile overbank rate seen in a search snippet, page not
  opened, confidence D); `NILE_FLOOD_RECESSION`, its constants and `Rotation.soil_fertility_yield_multiplier` are deleted. Flooded tiles with no rainfed arable ground now
  hold a stock too (`soil_nitrogen.step_year`).
- Tillage: see Complaint 537. `test_tillage_and_silt`.
- The draught herd's dung is the cattle species row's data (`manure_share_of_live_weight_per_day`, `manure_collected_share`); the two invented constants are deleted.
  The free-spread rule is still transitional (`FREE_MANURE_SPREAD_SHARE`, retire: this complaint).

- Open question: the rainforest-against-savanna check (`test_geography_food_gaps`) is an expected failure. Derived savanna fertility sits near the
  Mediterranean reference because the rule has no weathering age; an opened lecture says tropical soils in general are leached and unproductive.
  Decision (PM): the check stays at 0.5, because the rule is the suspect. Savanna soils (Oxisols, Ultisols, Alfisols under
  repeated burning) are old and weathered, so the next step is a weathering term that lowers fertility with heat and time
  under leaching. It comes from soil-science sources (a weathering rate against temperature, as in Arrhenius-type
  chemical weathering), not from fitting the ratio. The term is a labelled heuristic until a soil-age layer exists. The
  expected failure turns green, or stays red, on its own.
  Tried (branch `soil-weathering`, not merged): an Arrhenius times rain weathering index (form and activation energy from
  White and Blum 1995, abstract read at pubs.usgs.gov/publication/70019112) lowering fertility. It made the ratio worse
  (rainforest is both hotter and wetter, so it weathers most), and its strength was set as the largest value that kept the
  Koppen-table tolerances, which is a fit to a test, so it was not merged. What separates savanna from rainforest in the
  soil literature is age, parent material and burning, which a climate index cannot carry. Next step: a soil-age or
  parent-material layer (for example a soil-order map), not another climate coefficient. Until then the 0.5 check stays an
  expected failure; whether its bound is right needs a source on cropping potential by climate (an agro-ecological zones
  study such as FAO GAEZ suitability by Koppen class).

## Left

- **Manure bought by farms.** No crop recipe takes `manure_kg` or `nightsoil_kg` as an input, and a recipe's yield is fixed per run, so a bought input
  cannot raise it. It needs an optional-input yield response in the producers (`sim/economy/producers*`, owned by another agent) that reports the nitrogen
  applied per tile to `state.economy.soil_nitrogen`; then `FREE_MANURE_SPREAD_SHARE` goes. A shortage of manure must lower yield, not stop the farm.
- A soil texture layer (SoilGrids or HWSD) in place of the heavy-soil stand-in and the daily temperature range stand-in; a land-cover layer in place of the arable ceiling.
- Sources: the humus, leaching and heavy-soil constants and the nitrogen pool constants are labelled heuristics (`kind: heuristic` in `soil.json`; `temporary_heuristic` in `soil_nutrients.py`).
- A draught force per toolkit against a tillage resistance per soil texture, in place of `Toolkit.tillage_capacity`.
