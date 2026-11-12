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

**Pass 10 (chemistry plant).** Task: use the three rates Pass 9 lacked (lead lining labour, smith labour per tonne, labourer ratio) to clear the 26 D capital rows in `50_chemicals`, `91_`, `92_` and `93_`. One row cleared (acetic acid oven retort, D to C); 25 stay D. The rates found:
- Labourer ratio: bricklayers work in a three-man gang, one labourer to two bricklayers, about 1,200 bricks a day for the gang (self-build.co.uk/guide-working-groundworkers-bricklayers). A US masonry contractors' page argues for 1:1 (masoncontractors.org/2006/05/26/estimating-the-correct-cost-per-unit/, from a search result, not opened).
- Plate work labour: boiler assembly (trimming, forming, punching, caulking, riveting) ran 5 tons a year per man employed, 1831 to 1864, less than one plate per man-day (Piggott, quoted in Broseley Local History Society Journal 15, oldcopper.org/broseley/journals/15.html). At 2000 hours a person-year (`sim/unit_conversions.py`) that is 400 hours a tonne of riveted plate. No per-kilogram figure for a coppersmith or a blacksmith was found: the only coppersmith time opened is about 20 hours for an early 1800s kettle of nearly 1/16 in sheet with no size (historicshepherdstown.com/portfolio-item/copper-kettle, from a search result).
- Lead sheet labour: fixing lead sheet covering by a squad of plumber and mate, 1.15 to 1.25 m2/h for code 5 and 1.35 to 1.45 m2/h for code 6 on flat work (table image on constructiontechnology2015.blogspot.com/2015/08/roof-coverings-part-03-lead-sheet.html). It is roofing, without burned or wiped seams or tinning, so it bounds a tank lining from below only; no lining rate was found (chestofbooks Estimating Sheet Lead Work and Estimating Labor give materials and 8 wiped joints of lead pipe a day only; Fay, The Art of Lead Burning, gutenberg.org/files/52835/52835-h/52835-h.htm, says a small wooden tank takes three to four days to build and line, with no size).
- Hardwood distillation (Brown, The Hardwood Distillation Industry in New York, 1917, distantreader.org/stacks/trust/uc2/uc2_ark+=13960=t2g73883k.txt): oven retort 6 ft 3 in wide, 8 ft 4 in high, 25 to 52 ft long, sides 3/8 in and bottom and back 1/2 in plate, 22 to 24 hour run, 2 to 2.5 cords a car and 2 cars in a 25 ft oven, 199 lb of acetate of lime a cord, cord 3800 lb seasoned, 24,000 cords a year at 80 a day, ovens last 3 to 12 years, lime tubs of wood 12 to 14 ft across and 4 ft high.
- Tar still: usual charge 15 to 20 tons, shell 1/2 in and crown 5/8 in plate (chestofbooks.com Distillation Principles and Processes, Chapter XXXVI Distillation Of Tar). Camphor tub: 112.5 kg of chips per 24 hours, cone 1.15 m high (lenntech.com/chemistry/soda-industries.htm and chestofbooks Volatile Oils vol 2, Camphor Oil parts 3 and 4, for the camphor and Leblanc charge figures).

Row cleared: `acetic_acid_kg` oven retort. One 25 ft oven carries the entry's 1160 cords a year (3.9 a day against 4 to 5), the shell is 6290 kg of plate (77.4 m2, 19.4 m2 at 12.7 mm and 58.1 m2 at 9.525 mm, 7870 kg/m3) against 12000 kg before, so the 12 t was overstated by about half; brickwork 8,770 bricks at 526.7 a m3, mason 175 h at 50 bricks an hour, labourer 88 h, smith 2515 h at 400 h a tonne (the smith figure rose from 1200), life 7.5 years (middle of 3 to 12). Cars and cooling ovens are left out of the bill (stated in the row).

Rows left D, the missing input each: all lead rows (`bleach_kg`, `blue_vitriol_kg`, `phosphoric_acid_kg`, `borax_kg`, `magnesium_fluoride_kg`) lack a vessel size (batch, cycle time and so lead area) and a lining rate that includes burning; the vitriol, red phosphorus and silver nitrate rows lack retort counts, charges and firing times; salt-cake pan, soda ash and caustic pans lack pan area and plate thickness; the HCl tower lacks tower dimensions; the acetic condensers lack tube bank and still copper area; carbide lacks furnace shell and lining dimensions; camphor lacks a yield from chips and the pot size; citrate, glycerol, fulminate and copper-beryllium lack batch sizes; phenol has a still (15 to 20 t charge, 1/2 in shell) but no carbolic oil yield per ton of tar; gunpowder has only a search snippet (50 lb charge, 3 to 5 hours, 100,000 lb a year a pair of runners; the page returned 401); mirror amalgam lacks slab size; flame retardant lacks a blending floor throughput. Each row's `capital_basis` now says so.

D rows left in the four files: 25 (50_chemicals 13, 93 4, 91 5, 92 3).
