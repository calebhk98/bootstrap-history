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

**Pass 8 (source-recipes-chemistry): the D rows of `50_chemicals.json`, `93_chemistry_nuclear_gaps.json`, `91_branch_material_gaps.json`,
`92_metals_components_gaps.json`.** All 32 D rows were `capital` items (the recipe rows themselves were already C or better). Each is now
`conf` C with the source and arithmetic in its `capital_basis`. Only pages opened in the pass are cited; most gave the process and a scale
check, not the equipment mass, so equipment masses are still the author's estimate (C by the schema's own definition). D left in these four files: 0.

Changed figures (old -> new), then rows whose figures stayed (the basis now cites what bounds them):

- `bleach_kg` absorption chambers: lead 3000 -> 9144 kg, capacity 300000 -> 68500 kg a year. St Rollox 1802 sold 151117 lb of bleaching powder
  and installed six lead vessels of 10 x 12 x 10 ft in 1803 (en.wikipedia.org/wiki/St_Rollox_Chemical_Works); 560 sq ft a chamber at 6 lb a sq ft
  of sheet lead (chestofbooks.com/home-improvement/construction/plumbing/Plumbing-Estimates-Contracts/Estimating-Sheet-Lead-Work.html).
  Caveat: the 1803 vessels may have served the vitriol house; the page is ambiguous.
- `bleach_kg` chlorine stills: capacity 300000 -> 68500 kg a year (same St Rollox figure).
- `polyethylene_kg` autoclave: capacity 200000 -> 100000 kg a year, tool steel 3000 -> 5000 kg. ICI Wallerscote 100 t/y from 1 Sep 1939 with 50 litre
  vessels (thechemicalengineer.com/features/cewctw-dermot-manning-and-colleagues-at-ici-plastic-fantastic/); compressor to 1500 kg/cm2
  (collection.sciencemuseumgroup.org.uk/objects/co9978/ethylene-compressor-from-first-full-scale-polyethe); steel density en.wikipedia.org/wiki/Steel;
  vessel length to diameter and outside diameter are assumptions stated in the row.
- Figures kept, with a derivation or process source added: ethanol still (copper still, Pot still page + Ethanol and Copper densities, 263 kg of ethanol a charge,
  about 300 runs a year, 570 kg of copper), ethanol vats; vitriol galley furnace and retorts, red phosphorus furnace and retorts (Britannica 1911 Phosphorus,
  en.wikisource.org/wiki/1911_Encyclopædia_Britannica/Phosphorus); hydrochloric furnace and tower (Leblanc process, en.wikipedia.org/wiki/Leblanc_process, 5.5 t acid to 8 t
  soda ash); sodium carbonate furnace and lixiviation tanks (www.lenntech.com/chemistry/soda-industries.htm, 800 lb hand charge, one furnace carries 42 t/y);
  blue vitriol, phosphoric acid, borax lead vats (6 lb lead, Britannica Borax); acetic retorts and condensers (Britannica Acetic Acid); calcium carbide furnace
  (en.wikipedia.org/wiki/Calcium_carbide, 2000 kWh a tonne theoretical); sodium citrate pan, camphor stills (en.wikipedia.org/wiki/Camphor); glycerol
  (Britannica Glycerin, vacuum 27 to 28 in.); gunpowder mill (Britannica Gunpowder, 4 h incorporation); silicon carbide
  (usgennet.org/usa/topic/preservation/science/inventions/chpt27.htm, 7 t in 1893, 2700 t/y in 1902; en.wikipedia.org/wiki/Acheson_process); mirror silvering
  (Britannica Mirror, 24 h under weights); magnesium fluoride lead retort (lead weight).
- Still estimates (marked in each row, nothing opened bounded the scale): phenol still (no phenol share of tar found), flame-retardant floor, fulminate flasks,
  silver nitrate vessels, caustic soda tanks, copper-beryllium crucible furnace. Open searches for plant outputs in `Albright and Wilson`, gunpowder mills and
  wood distillation found no tonnage.

Searched and not found: Oldbury phosphorus output, edge-runner mill charge and runner mass, galley-furnace vitriol output, wood-distillation retort size,
carbolic oil share of coal tar. Status stays open.

**Pass 8 correction.** A C row needs an opened figure that bounds its mass or capacity. Only five of the 32 capital rows meet that and stay C (copper pot still, bleach absorption chambers, polyethylene autoclave, black-ash furnace, Acheson furnace; beside the bounded figure some stone, iron or brick masses are still estimates, written in the row). The other 27 are back at D: each cites the process page it was read from and says no opened figure bounds the scale. The paragraph above that lists rows kept with a process source as sourced is superseded by this one. D rows left in the four files: 27 (50_chemicals 15, 93_chemistry_nuclear_gaps 4, 91_branch_material_gaps 5, 92_metals_components_gaps 3).

**Pass 8 follow-up (vendor pages).** Vendor and catalogue pages were tried for the 27 D rows (destillatio.eu alembic, gwkent, genemco, phxequip, exapro, equipt, calderlead, lindbergmph, 3v-tech, Alibaba): each was 403/404, gave no weight, or listed only capacity, so no vessel weight was taken from a vendor. One row was bounded from opened figures instead: `ethanol_kg` mash tuns and vats, timber 60 -> 2.0 m3 (Wikipedia Whisky, two days or longer fermentation, with the still row washes; stave thickness is an assumption stated in the row), now C. Albright and Wilson, Tennant (Grace's Guide) pages have no output or vessel sizes. D rows left in the four files: 26 (50_chemicals 14, 93 4, 91 5, 92 3).
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

**Pass 9 (chemistry plant derivations).** Task: derive the 26 remaining D `capital` rows (50_chemicals 14, 93_chemistry_nuclear_gaps 4, 91_branch_material_gaps 5, 92_metals_components_gaps 3) from cited inputs (vessel volume from yearly output and batch time, wall from a thickness page, mass from area, thickness and density, labour from a trade rate, life from a lining or vessel life page). No row was cleared: every row needs at least one input for which no page could be opened. No data file was edited; all 26 rows stay D and the counts above are unchanged.

Inputs that were opened and could be reused by a later pass:
- Brick unit 215 x 102.5 x 65 mm with a 10 mm joint, so a 225 x 112.5 x 75 mm unit per brick in the wall (Wikipedia Brick, en.wikipedia.org/wiki/Brick); bricks per cubic metre of wall follows by division.
- Bricklayer rate 40 to 60 bricks an hour, 300 to 500 a day (tradewarehouse.co.uk/blogs/bricks-blog/how-many-bricks-can-you-lay-in-an-hour).
- Densities: copper 8.935 g/cm3 (Wikipedia Copper), lead 11.3 and iron 7.87 g/cm3 (Wikipedia Lead, en.wikipedia.org/wiki/Lead).
- Copper still boiler sheet 0.032 in (22 gauge) for 6 to 15 gallon pots, 16 oz roofing copper used for a 24 gallon boiler (homedistiller.org/forum/viewtopic.php?p=7065415).
- Iron boiler plate: 3/8 in plate for small tubes, old iron boilers rolled to about 3/4 in at most (en.wikisource.org/wiki/1911_Encyclopædia_Britannica/Boiler).
- Brick furnace life: a glass furnace campaign lasts up to 16 years before rebuild (Wikipedia Glass melting furnace, en.wikipedia.org/wiki/Glass_melting_furnace).
- Batch fill fraction 0.8 of geometric volume as a design input (processconvert.pages.dev/engineering-guides/batch-vs-continuous-tank-sizing; a calculator guide, not a vessel standard).
- Process times: incorporation of gunpowder about four hours and charring five to seven hours (Britannica 1911 Gunpowder); red phosphorus conversion 24 hours at 230 C (Britannica 1911 Phosphorus); soap pans take a charge of 30 tons or more (Britannica 1911 Soap); old soap boiled in a copper cauldron for several days (Wikipedia Soap); lime kiln one-week turnaround (Wikipedia Lime kiln).
- Riveting 200 to 500 rivets a day (NZ Railway Board 1909 via search result; the page itself was not opened, so it is not a citation).

Inputs for which nothing could be opened, and so what blocks each group:
- Plumber or lead-burning hours per square metre of lead lining (searched: chestofbooks lining chapters, NIOSH lead-burning reports: no hours figure). Blocks every lead row: `bleach_kg` stills, `blue_vitriol_kg`, `phosphoric_acid_kg`, `borax_kg`, `magnesium_fluoride_kg`, and the plumber hours in `acetic_acid_kg` condensers, `phenol_kg`, `glycerol_kg`.
- Coppersmith or smith hours for a vessel of stated mass or area (the only figure found, four men six weeks for a distillery pot still, has no size and the page returned 503). Blocks `sodium_citrate_kg`, `acetic_acid_kg`, `fulminate_kg`, `phenol_kg`, `glycerol_kg`, `camphor_kg`, `sodium_carbonate_kg`, `caustic_soda_kg`, `hydrochloric_acid_kg` pan, `phosphorus_red_kg`, `calcium_carbide_kg`.
- Labourer hours per brick or per tonne handled, carpenter hours for a timber tank (one cooper makes about one barrel a day, rogue.com search result, not opened) and millwright hours: block `sulfuric_acid_vitriol_kg` furnace, `hydrochloric_acid_kg` tower, `flame_retardant_kg`, `silver_nitrate_kg`, `gunpowder_kg`, `mirror_amalgam_kg`, `copper_beryllium_kg`.
- Batch time or batch size for the process itself: no opened page gives one for vitriol galley, wood retort carbonisation (the charcoal-cylinder 5 to 7 hours is the nearest), carbide furnace tapping, coal-tar carbolic fraction, camphor chip steaming, mercury fulminate, silver nitrate, magnesium fluoride, borax, citrate or beryllium master alloy.
- Furnace lining or retort life: clay retort (months), iron pan and acid-attacked vessel lives have no opened page; only the glass furnace 16 year campaign above.
- Clay retort wall thickness and mass per retort (vitriol, red phosphorus): no page opened.

A trial derivation shows how far the present masses may be from a derived figure, offered as a lead and not as a result: a wood retort carrying one day's charge of the acetic row (about 2000 tonnes of wood a year, two charges a day at the 5 to 7 hour charring time, 0.8 fill) is about 8 cubic metres, which at 3/8 in plate is about two tonnes of iron against the row's 12 tonnes. Soap pan: a 30 ton charge at 0.8 fill is about 40 cubic metres, about six tonnes of iron at 3/8 in. The next pass should find one lead-burning labour page, one smith labour-per-tonne page and one labourer ratio page, which together unlock about two thirds of the rows.

D rows left in the four files: 26 (50_chemicals 14, 93 4, 91 5, 92 3).
**Pass 8 (source-recipes-organics-crafts): organics, lighting, writing, building services, carriers, leather goods.**
Every source below was opened in the session; no row was moved to C, because each still has a labour or minor-input figure that
no opened page bounds. Rows whose numbers changed carry the source in their `yield_basis` ("SOURCE READ (Pass 8)").

Changed (old -> new, still D):

- `ink_iron_gall_kg` (40_organics): galls 0.12 -> 0.083, vitriol 0.06 -> 0.056, gum 0.04 -> 0.028, water 0.8 -> 0.84 per kg.
  Science in School issue 6 (scienceinschool.org/wp-content/uploads/2014/11/issue6_galls.pdf): galls 3, water 30, ferrous
  sulphate 2, gum 1 parts by weight; University of Illinois Library "Iron gall ink" (library.illinois.edu/rbx/2021/04/07/iron-gall-ink/):
  80 g galls, 50 g copperas, 25 g gum. Labour unsourced.
- `ink_carbon_gum_kg`: gum 0.1 -> 0.18. Making and Knowing "Carbon ink info and recipes"
  (teaching640.makingandknowing.org/documents/pdf/carbon-ink-info-and-recipes.pdf): 9:1 gum solution to carbon by weight; Atlas of Making
  "Lampblack ink" (atlasofmaking.kenjiliu.com/inks/lampblack): gum solution about 1:4. Tallow burned per kg of soot (10 kg) has no opened
  source (the 7 to 9 percent soot-per-kerosene figure was only seen in a search summary, so only a lower bound is noted).
- `salted_meat_kg`: salt 150 -> 70 kg, cured output 750 -> 710 kg a tonne. scienceinsights.org/how-to-salt-cure-a-ham/: 8 oz salt per
  10 lb ham (5 percent), 11 oz full cure (6.9 percent), ham loses 28 to 30 percent of its weight. Labour unsourced.
- Tallow light rows (`light_tallow_candle`, `_linen`, `_rush`, `_linen_wick`, `light_tallow_rushlight`): tallow 0.53 -> 0.56 kg per
  1000 lumen-hours. Wikipedia "Candle" (about 13 lumens, about 77 W), Wikipedia "Energy density" (body fat 38 MJ/kg): 77 W / 38 MJ/kg =
  7.3 g/h, times 1000/13 = 77 hours. Dipping labour: Smith College "Ancient Inventions" candles page (about two hours of dipping for a batch,
  no count) and Practical Action candle manual (3 to 4 s a dip, 1 to 4 min cooling): no per-candle labour.
- `light_electric_lamp`: electrical_mj 1.2 -> 1.33. lamptech.co.uk Edison New Type spec sheet: 201 lm for about 75 W, 2.7 lm/W.
- `shoes_pair`: shoemaker hours 8 -> 12. bespokyshoes.com/pages/atelier: "10-14 hours of handwork" a pair (one modern workshop). Leather
  0.8 kg unsourced.
- `brick_wall_m3`: mason and labourer hours 24 -> 18. tradewarehouse.co.uk "How many bricks can you lay in an hour": 300 to 500 bricks a
  day, 40 to 60 an hour; low end 40 an hour. Roof tile weight per m3 of wall (100 kg) unsourced.

Source added, value kept (D):

- `cheese_kg`: Cornell small-ruminant dairy "Milk composition and cheese yield" (Table 1 sheep milk fat and protein; revised Van Slyke
  formula) gives 5.6 to 6.0 kg of sheep milk a kg of hard cheese, below the 8 kept for the sheep-and-goat mix (goat milk composition not opened).
- `bread_kg`: Wikipedia "Baker percentage": hydration 58 to 65 percent; 65 is the top. Baking loss, oven efficiency, labour, oven capital unsourced.
- `written_page_papyrus/_parchment/_paper`: Lithub "Writing as spiritual practice: inside the world of medieval scribes": a professional
  scribe copies about three to four pages a day (two to 2.7 hours a page in an eight-hour day; 3 kept). Ink 1.5 g a page and the desk capital unsourced.
- `timber_frame_m3`: Mortise and Tenon Magazine "The Efficiency of Hewing": an 8x8x12 ft post hewn in about three hours (about 20 hours
  a cubic metre of hewing alone); the 30 carpenter hours are not bounded.
- `cart`: Colonial Williamsburg wheelwright (podcast.history.org, "Carriages, Carts and Wagons"): a coach wheel about 100 hours, a wheelbarrow
  wheel 12; two wheels bracket 100 to 200 hours. Remaining timber, iron and labour unsourced.

Left D, tried (search plus fetch, nothing that bounds the numbers):

- `oak_gall_kg`, `gum_kg`: gatherer rates; searches for cherry-gum or gall picking rates returned nothing per hour; Wikipedia "Oak gall" gives no tannin figure.
- `dyed_cloth_kg`, `wick_linen_m`, `wick_rush_m`, `essential_oil_kg` capital, `paper_kg` stamper capital, `leather_kg` tan-yard capital and
  no-iron alternative, `bone_ash_kg` kiln capital and alternative: no page found with plant masses or hours.
- `light_oil_lamp`, `light_oil_lamp_linen_wick`, `light_beeswax_candle`: EXARC Journal "Experiment with Kindling Oil Lamps" (Vaiman, exarc.net/ark:/88735/10527, opened)
  reports replica lamps run 30 to 80 ml an hour in some runs (volume over burn time, ambiguous), far above the 8 g an hour taken, and no light output; beeswax heat
  of combustion not found on Wikipedia "Beeswax" or "Energy density". Heidelberg lamp study blocked. Values kept; the oil figure may be low.
- `gaming_table_hour`, `lottery_chance` and their capital, `water_well_kg` and capital, `water_piped_kg` channel capital, `river_barge`, `pack_saddle`, `stone_wall_m3`
  (a 19th-century ashlar rate of 80 sq ft a day for two masons and a labourer, chestofbooks.com "Estimating the Stonework Continued", suggests the 18.5 mason hours a
  m3 is high, but wall thickness is not given), `urine_kg`, `nightsoil_kg`, `vegetable_kg` (King, Farmers of Forty Centuries, blocked: 401 on the mirror), `harness_set`,
  `scabbard_leather`, `nails_kg`, `roof_tile_kg` (Wikipedia "Tegula" is a disambiguation page), `fish_kg`, `salted_fish_kg`, `garum_kg` (Wikipedia "Garum" gives no
  proportions), `flour_kg*` (Wikipedia "Quern-stone" gives no rate), `domestic_service_hour`, `cooked_meal_kg`, `rubber_planting_stock_kg`, `rice_kg`, `merchant_ship`,
  `warship` (Wikipedia "Kyrenia ship" and "Olympias (trireme)" give no hours or timber), `waste_handling_job`, `waste_haulage_on_foot`, and the Peace Corps well manual
  (403), World Bank hand-dug well manual (compressed PDF unreadable), UGA and Kentucky ham bulletins (404/503) were all tried or unreachable.

Status stays open.

**Pass 9 (machines, metals, textiles).** The D rows of `10_ferrous`, `20_nonferrous`, `30_fuel_stone`, `60_nitrogen`, `80_machines`, `90_additions`, `95_mesoamerican_stock_and_game` and `96_mesoamerican_fibre_and_silver` (36 rows) were searched again and the pages behind the results were opened (WebFetch, or the raw wikitext and wikisource text fetched with curl and searched). Each row's `yield_basis` or `capital_basis` now says what was opened and which input still has no page. One figure changed; no row reached C, because in every row at least one input (works mass, annual output, a recovery, a rate) is still no page's figure. D left in these files: 36.

- Changed: `zinc_kg` fireclay retorts, `service_life_years` 0.2 -> 0.06. US patent 2447369 (patents.google.com/patent/US2447369) gives an average Belgian retort life of two to three weeks, a 9 in bore and 1 in walls. Retort mass derived: 0.0247 m3 of wall for a 4 ft retort (length range from 1911 Britannica Zinc, wikisource Page:EB1911 - Volume 28.djvu/1009) at 1600 to 2100 kg per m3 (spotmaterial.com earthenware) is 40 to 52 kg, so the 1200 kg of clay is 23 to 30 retorts, consistent with the plant's 40000 kg a year at 7 kg a retort-day. Potter hours and the annual output remain unbounded, so the item stays D.
- Tin washing recovery (0.65): bracketed, not derived. Placer mining (Wikipedia) gives sluice boxes about 40 percent of gold; 911metallurgist gives jigs 70 percent or better; 1911 Britannica Tin gives alluvial gravel of 5 to 60 lb of tinstone a cubic yard (brackets the 2.6 kg of tin a tonne used), a washed tinstone of 65 to 75 percent tin (richer than the 60 percent SnO2 the row assumes) and 5 to 6 hours of reverberatory smelting with one fifth coal. No page gives a stream-tin hand-washing recovery or a smelting recovery.
- Silver collector 0.80 and the lead flux: Wikipedia Cupellation and 911metallurgist silver assaying were opened and give no percentages (their loss tables are images); the Rand Refinery 96 percent and the 1959 Mines Branch 2 percent losses were seen in search summaries only and are assay figures anyway.
- Las Medulas build hours (500000): Wikipedia gives 60,000 workers, 6,560 kg of gold a year and seven aqueducts, no length. One system is 284 kg a year, 4.3 percent of the district, so a proportional share of any network the reports give is an order of magnitude below 500000 hours; the constant lives in `sim/world/deposits.py` and was not changed. No page on Roman excavation rates per person-day was found; the modern norms found are unattributed tables.
- Maguey and backstrap textiles: the lechuguilla paper (ojs.pphouse.org IJBSM 116) gives 1.87 kg of dry fibre an hour for manual shredding, a floor under the 8 hours a kilogram used; tnau gives agave fibre 2.5 to 4.5 percent and plantation leaf yields; gansey.blogspot.com gives a wheel spinning 400 yards an hour at 11,200 yards a pound (62 hours a kilogram). The thread count of Mexican cloth and a backstrap weaving rate are in no opened page (Mexicolore, Smith and Hirth, Nichols not reached).
- Works rows (Newcomen, compound, turbine, dynamo, motor, module line, cast iron foundry, nitre sheds, ammonium nitrate pans): Wikipedia Newcomen and Fairbottom Bobs bound the engine (28 in bore, 8 ft stroke, 11 hp) and the national count, and catalogues bound a motor or a cable per kilogram, but no page gives a works' masses or a plant's yearly output, so these stay D. Nitre bed size (4 x 6 x 15 ft, leached after about a year, Wikipedia Potassium nitrate) was found; kilograms of nitre per bed was not.
- Deer, turkey, dog, fowl: Wikipedia White-tailed deer gives 183 kg dressed from 232 kg alive (0.79); UMaine gives commercial turkey dressing 77 to 81 percent; no page gave deer fat or hide shares, wildfowl yields or dog figures. Turkey and dog species figures are in `living_stock.json` (Complaints/532) and were not touched.

Pages that returned 403/404 or only a PDF dump: bladeforums trade-axe thread, pv-magazine, epj-pv, britannica.com zinc-processing, lakesidepottery.com weights PDF, Heidelberg sherd study (Anubis block). Status stays open.

**Pass 10 (chemistry plant).** Task: use the three rates Pass 9 lacked (lead lining labour, smith labour per tonne, labourer ratio) to clear the 26 D capital rows in `50_chemicals`, `91_`, `92_` and `93_`. One row cleared (acetic acid oven retort, D to C); 25 stay D. The rates found:
- Labourer ratio: bricklayers work in a three-man gang, one labourer to two bricklayers, about 1,200 bricks a day for the gang (self-build.co.uk/guide-working-groundworkers-bricklayers). A US masonry contractors' page argues for 1:1 (masoncontractors.org/2006/05/26/estimating-the-correct-cost-per-unit/, from a search result, not opened).
- Plate work labour: boiler assembly (trimming, forming, punching, caulking, riveting) ran 5 tons a year per man employed, 1831 to 1864, less than one plate per man-day (Piggott, quoted in Broseley Local History Society Journal 15, oldcopper.org/broseley/journals/15.html). At 2000 hours a person-year (`sim/unit_conversions.py`) that is 400 hours a tonne of riveted plate. No per-kilogram figure for a coppersmith or a blacksmith was found: the only coppersmith time opened is about 20 hours for an early 1800s kettle of nearly 1/16 in sheet with no size (historicshepherdstown.com/portfolio-item/copper-kettle, from a search result).
- Lead sheet labour: fixing lead sheet covering by a squad of plumber and mate, 1.15 to 1.25 m2/h for code 5 and 1.35 to 1.45 m2/h for code 6 on flat work (table image on constructiontechnology2015.blogspot.com/2015/08/roof-coverings-part-03-lead-sheet.html). It is roofing, without burned or wiped seams or tinning, so it bounds a tank lining from below only; no lining rate was found (chestofbooks Estimating Sheet Lead Work and Estimating Labor give materials and 8 wiped joints of lead pipe a day only; Fay, The Art of Lead Burning, gutenberg.org/files/52835/52835-h/52835-h.htm, says a small wooden tank takes three to four days to build and line, with no size).
- Hardwood distillation (Brown, The Hardwood Distillation Industry in New York, 1917, distantreader.org/stacks/trust/uc2/uc2_ark+=13960=t2g73883k.txt): oven retort 6 ft 3 in wide, 8 ft 4 in high, 25 to 52 ft long, sides 3/8 in and bottom and back 1/2 in plate, 22 to 24 hour run, 2 to 2.5 cords a car and 2 cars in a 25 ft oven, 199 lb of acetate of lime a cord, cord 3800 lb seasoned, 24,000 cords a year at 80 a day, ovens last 3 to 12 years, lime tubs of wood 12 to 14 ft across and 4 ft high.
- Tar still: usual charge 15 to 20 tons, shell 1/2 in and crown 5/8 in plate (chestofbooks.com Distillation Principles and Processes, Chapter XXXVI Distillation Of Tar). Camphor tub: 112.5 kg of chips per 24 hours, cone 1.15 m high (chestofbooks Volatile Oils vol 2, Camphor Oil parts 3 and 4, for the camphor and Leblanc charge figures).

Row cleared: `acetic_acid_kg` oven retort. One 25 ft oven carries the entry's 1160 cords a year (3.9 a day against 4 to 5), the shell is 6290 kg of plate (77.4 m2, 19.4 m2 at 12.7 mm and 58.1 m2 at 9.525 mm, 7870 kg/m3) against 12000 kg before, so the 12 t was overstated by about half; brickwork 8,770 bricks at 526.7 a m3, mason 175 h at 50 bricks an hour, labourer 88 h, smith 2515 h at 400 h a tonne (the smith figure rose from 1200), life 7.5 years (middle of 3 to 12). Cars and cooling ovens are left out of the bill (stated in the row).

Rows left D, the missing input each: all lead rows (`bleach_kg`, `blue_vitriol_kg`, `phosphoric_acid_kg`, `borax_kg`, `magnesium_fluoride_kg`) lack a vessel size (batch, cycle time and so lead area) and a lining rate that includes burning; the vitriol, red phosphorus and silver nitrate rows lack retort counts, charges and firing times; salt-cake pan, soda ash and caustic pans lack pan area and plate thickness; the HCl tower lacks tower dimensions; the acetic condensers lack tube bank and still copper area; carbide lacks furnace shell and lining dimensions; camphor lacks a yield from chips and the pot size; citrate, glycerol, fulminate and copper-beryllium lack batch sizes; phenol has a still (15 to 20 t charge, 1/2 in shell) but no carbolic oil yield per ton of tar; gunpowder has only a search snippet (50 lb charge, 3 to 5 hours, 100,000 lb a year a pair of runners; the page returned 401); mirror amalgam lacks slab size; flame retardant lacks a blending floor throughput. Each row's `capital_basis` now says so.

D rows left in the four files: 25 (50_chemicals 13, 93 4, 91 5, 92 3).

**Pass 11 (any-source bar).** The bar was lowered: any outside page opened in the session (Wikipedia, a blog, a forum, a
shop listing, an old manual) counts, a ballpark within about a factor of three keeps the value, and a figure that follows
from opened figures by stated arithmetic counts as sourced. Each row's basis text now carries its Pass 11 citations and
names the number still unsourced. Count what is left with the command at the top.

- To C: the six tallow, beeswax and rush candle rows, `cheese_kg`, `dyed_cloth_kg`, `written_page_papyrus` and
  `written_page_parchment`; `mat_sugar`, `waste_haulage_on_foot`, `domestic_service_hour` (an identity, not an outside
  source); `fat_kg` (deer), `down_kg` (wildfowl), `ceramic_kg` and the two low-voltage main capital rows.
- Values changed, each more than a factor of three from an opened figure: candle dipping labour (Mount Vernon dipping
  stand); ink per written page (onepenshow.com fountain-pen measurements, a weak analogue for a quill, likely low); lampblack
  ink oil and tallow (Wikipedia India ink); nail smith hours (Mortise and Tenon Magazine, SPACO); smith hours on five
  chemistry vessels (Piggott's boiler-plate assembly rate, oldcopper.org Broseley journal 15, a proxy for simpler pans).
- Chemistry plant: lead lining labour derived from Pass 10's roofing rate times a labelled factor of two for burned seams;
  every row still lacks a vessel size or batch cycle, and brick, stone and timber hours.
- Still stuck, with the reason in each row: engine, dynamo and foundry works (no wall or roof masses), tin and silver
  recoveries, backstrap weaving, wells, leather goods, fish, carts, barges, the aqueduct and the warship (sources blocked
  or giving no figure), and the stock rows whose numbers live in `data/world/living_stock.json`.

**Pass 12 (derive from two sources).** Rows with no direct figure were derived: a documented comparable scaled by
output (Thorpe's phosphorus galley, Lunge's vessels, Fairbanks 1907 machine-tool weights, Gillette's crane and brick
rates), a rate from a trade manual or modern craftsperson times the quantity, or a bracket from two sources. Each row's
basis gives the arithmetic and labels the glue assumptions; every row still at D carries a "tried:" list naming three
approaches. Count what is left with the command at the top.

For the code side, two findings this pass could not apply as data:
- `silver_smelted_native_kg`: Cohen et al., Historical Metallurgy 44(2) 2010 (Cuiza huayrachina) gives about 0.5 kg
  charcoal a kg of charge and 0.4 furnace hours a kg, against 0.3 and 0.113 held. Applying them moves the starting-wage
  metal-cost spread past the limit in `sim/tests/test_opening_wage_anchor.py`. The sourced values are applied and that
  test now fails (1.257 against 1.25); the check or the route needs a look.
- The Las Medulas hydraulic works: opened sources derive about 50,000 build hours against the 500,000 of
  `AQUEDUCT_CONSTRUCTION_HOURS_ALLUVIAL_HYDRAULIC` in `sim/world/deposits.py`. Applied: the constant and both gold
  rows now hold 52,400 hours (channel only, a lower bound); the arithmetic is in the `gold_kg` basis.
