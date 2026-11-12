# Production recipe figures at confidence D have no source that was read

**Status:** open

Split from 646 (figures recalled rather than read; closed). Many recipe rows in `data/production` carry `"conf": "D"` (a
labelled guess) after passes that sourced what could be found. Count and rank by file:
`grep -rc '"conf": "D"' data/production | grep -v ":0" | sort -t: -k2 -nr`. The largest groups when this was written are
`50_chemicals.json`, `40_organics.json`, `99_lighting.json`, `80_machines.json`, `20_nonferrous.json`, the Mesoamerican stock,
game, fibre and silver files, `95_herds.json` and the gap files (`91_branch_material_gaps.json` and its numbered neighbours).
The wine, oil and jar rows belong to 656 and the stone-tool rows to 650.

**What is known already.** Searched and not found: the 2400-hour year of herders and goat and cattle head per herder
(`95_herds.json`); the Kyrenia and Olympias cargo tonnage (`99_ships.json`; Wikipedia gives a displacement, uncited);
`99_lighting.json` rows (the tallow candle burn rate has a candidate in Nature 16, 1877, p. 361, not opened); Donald and Hamblin
1976 (`95_staple_grains.json`, not openable); the Geoponica 20.46 and King, Farmers of Forty Centuries leads (not opened).

**What it would take.** Per file, read the source for each D row (author, work, page or URL, the passage) and replace the
figure, or keep it a labelled heuristic with a `retire` that names a mechanism or complaint (CLAUDE.md 4.4). A recipe yield is a
physical fact (stoichiometry, ore grade, material property), never tuned to a price (4.5).

**Research needed.** Per recipe family, the physical or experimental source: chemical process yields (an industrial chemistry
handbook for the process, with the pre-industrial route from the historical literature), lighting (candle and lamp burn rates
by fuel: experimental archaeology and photometric studies), machine builds (the hours and mass of the historical machine from
museum or engineering monographs), nonferrous refining recoveries (Craddock, Early Metal Mining and Production; Tylecote, A
History of Metallurgy), and the Mesoamerican stock, game and fibre rows (Sahagun's Florentine Codex with ethnographic yields).

**Carriage inputs (moved from 561 when it closed).** Unsourced in `sim/geography/transport.py` and `sim/geography/routes_carriers.py`: the
cart's structural payload (only the team's pull limits it), river current and towing speed (nothing supplies them to
`routes_rates.rate`), `CART_SERVICE_LIFE_KM` (temporary heuristic) and `BARGE_SELF_MASS_KG` (grade D). Opened: Scheidel,
"ORBISprices" (2013 working paper) pp. 6-7: the Edict's land and river rates take no account of river velocity, so the Edict
cannot validate a current-dependent river rate. Not opened: Raepsaet on Roman carts, the Edict's freight chapters, river towing
studies. The money ratio across modes is validated by `sim/tests/test_freight_mode_cost_ratio.py`.

**Pass 7 (source-recipes-and-service-lives).** Sourced and opened:

- `flour_kg` (wheat) extraction: Khalid, Hameed and Tahir, "Wheat quality: a review ...", Frontiers in Nutrition 2023
  (pmc.ncbi.nlm.nih.gov/articles/PMC9998918/): the kernel is 80 to 85 percent endosperm, 13 to 17 percent bran, 2 to 3 percent
  germ. This bounds the recipe's extraction and bran share; values unchanged, still D because the extraction a pre-industrial
  stone and sieve reached has no source.
- `nails_kg`: the SPACO page "Making Hand Forged Nails" gives 87 and 230 nails an hour for modern demonstrators with no nail size,
  so it cannot fix hours per kilogram; it suggests the recipe's smith hours are high. Value unchanged.

Searched and not sourced: bread hydration and baking loss (forum and bakery-blog sources only), the 1842 Britannica "Candle"
table of Ure's burn experiments (opened but the table is garbled in the transcription, so no burn rate was taken), the Monticello
nailery loss records (403), candle photometry. Left: all other D rows in the list above; the carriage inputs are untouched.
Status stays open.

**Pass 8 (source-recipes-machines-metals).** Rows touched in `10_*`, `20_*`, `30_*`, `60_*`, `80_*`, `90_*`, `95_mesoamerican_*`, `96_*`.

Changed:

- `ceramic_kg` (`30_fuel_stone.json`): potter hours 700 a tonne to 370, conf C to D (the pot mass is assumed). Opened:
  ruralindiaonline.org/en/articles/kummaras-of-kodavatipudi/ (a potter shapes 20 to 30 ten-litre pots a day, about 10 hours a day, a month's
  whole cycle is 200 to 300 pots, so about 1 hour a pot all in); a 10-litre pot taken at 2.7 kg from an assumed 6 mm wall; cross-check
  fishandpeaches.blogspot.com/2012/03 (7 Dressel 20 amphorae a day each). 1 h / 2.7 kg = 370 h a tonne.
- `maguey_fibre_kg` (`96_*`): farmer hours 4800 to 1800 a hectare; yield 500 kg/ha kept, bounded by prosea.prota4u.org/view.aspx?id=6522
  (sisal 0.5 to 2.8 t/ha); scraping 8 h/kg to 2 h/kg from the Mexican government lechuguilla sheet
  (gob.mx/cms/uploads/attachment/file/912100/Lechuguilla.pdf, 4 to 9 kg of fibre a worker-day). The 800 planting and weeding hours are
  unsourced: stays D.

Basis text extended, numbers unchanged, left D (the masses and build hours are unbounded by any opened figure):

- `zinc_kg` capital furnace and retorts: Britannica 1911 "Zinc" (46 retorts a furnace, 1100 lb charge, eleven hours; retorts 3.25 to 4.75 ft
  long, 6 to 10 in bore) bounds capacity and retort clay mass to the order used; retort life and wall thickness not read.
- `heat_engine_modern_steam_unit` capital: Wikipedia C. A. Parsons (up to 50 turbines a year at Heaton) and Newcastle Sitelines SMR 4334
  (1889 works two acres, 48 staff); no masses.

Left D, tried: `iron_tools_kg` (searched smithing times; only axe-line and hobbyist times, no per-kilogram figure); `tin_kg` washing
recovery 0.65 (911metallurgist tin sluicing page opened: no recovery percentage); `silver_jarosite_kg`, `jarosite_ore_kg`,
`silver_smelted_native_kg` (no collector or Mexica furnace figure found); `cast_iron_kg`, charcoal and coal wooden-tool alternatives,
`gold_kg`/`gold_g` Las Medulas works (Wikipedia: seven long aqueducts, no build hours), `caesium_g`, `nitre_kg`, `nitric_acid_kg` capital
(searches gave no shed or furnace dimensions), `ammonium_nitrate_kg`; `80_machines.json` engine and electrical works (Newcomen, compound,
dynamo, motor, photovoltaic line, low-voltage mains: no annual outputs or masses in a page that could be opened); backstrap cotton and
maguey spinning and weaving hours and `cloth_backstrap_kg` (no spinning rate in any opened page); turkey, dog, deer and fowling rows
(their figures come from `data/world/living_stock.json`, owned by another pass). Status stays open.
