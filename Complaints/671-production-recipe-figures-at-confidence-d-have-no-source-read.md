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

**Pass 9 (machines, metals, textiles).** The D rows of `10_ferrous`, `20_nonferrous`, `30_fuel_stone`, `60_nitrogen`, `80_machines`, `90_additions`, `95_mesoamerican_stock_and_game` and `96_mesoamerican_fibre_and_silver` (36 rows) were searched again and the pages behind the results were opened (WebFetch, or the raw wikitext and wikisource text fetched with curl and searched). Each row's `yield_basis` or `capital_basis` now says what was opened and which input still has no page. One figure changed; no row reached C, because in every row at least one input (works mass, annual output, a recovery, a rate) is still no page's figure. D left in these files: 36.

- Changed: `zinc_kg` fireclay retorts, `service_life_years` 0.2 -> 0.06. US patent 2447369 (patents.google.com/patent/US2447369) gives an average Belgian retort life of two to three weeks, a 9 in bore and 1 in walls. Retort mass derived: 0.0247 m3 of wall for a 4 ft retort (length range from 1911 Britannica Zinc, wikisource Page:EB1911 - Volume 28.djvu/1009) at 1600 to 2100 kg per m3 (spotmaterial.com earthenware) is 40 to 52 kg, so the 1200 kg of clay is 23 to 30 retorts, consistent with the plant's 40000 kg a year at 7 kg a retort-day. Potter hours and the annual output remain unbounded, so the item stays D.
- Tin washing recovery (0.65): bracketed, not derived. Placer mining (Wikipedia) gives sluice boxes about 40 percent of gold; 911metallurgist gives jigs 70 percent or better; 1911 Britannica Tin gives alluvial gravel of 5 to 60 lb of tinstone a cubic yard (brackets the 2.6 kg of tin a tonne used), a washed tinstone of 65 to 75 percent tin (richer than the 60 percent SnO2 the row assumes) and 5 to 6 hours of reverberatory smelting with one fifth coal. No page gives a stream-tin hand-washing recovery or a smelting recovery.
- Silver collector 0.80 and the lead flux: Wikipedia Cupellation and 911metallurgist silver assaying were opened and give no percentages (their loss tables are images); the Rand Refinery 96 percent and the 1959 Mines Branch 2 percent losses were seen in search summaries only and are assay figures anyway.
- Las Medulas build hours (500000): Wikipedia gives 60,000 workers, 6,560 kg of gold a year and seven aqueducts, no length. One system is 284 kg a year, 4.3 percent of the district, so a proportional share of any network the reports give is an order of magnitude below 500000 hours; the constant lives in `sim/world/deposits.py` and was not changed. No page on Roman excavation rates per person-day was found; the modern norms found are unattributed tables.
- Maguey and backstrap textiles: the lechuguilla paper (ojs.pphouse.org IJBSM 116) gives 1.87 kg of dry fibre an hour for manual shredding, a floor under the 8 hours a kilogram used; tnau gives agave fibre 2.5 to 4.5 percent and plantation leaf yields; gansey.blogspot.com gives a wheel spinning 400 yards an hour at 11,200 yards a pound (62 hours a kilogram). The thread count of Mexican cloth and a backstrap weaving rate are in no opened page (Mexicolore, Smith and Hirth, Nichols not reached).
- Works rows (Newcomen, compound, turbine, dynamo, motor, module line, cast iron foundry, nitre sheds, ammonium nitrate pans): Wikipedia Newcomen and Fairbottom Bobs bound the engine (28 in bore, 8 ft stroke, 11 hp) and the national count, and catalogues bound a motor or a cable per kilogram, but no page gives a works' masses or a plant's yearly output, so these stay D. Nitre bed size (4 x 6 x 15 ft, leached after about a year, Wikipedia Potassium nitrate) was found; kilograms of nitre per bed was not.
- Deer, turkey, dog, fowl: Wikipedia White-tailed deer gives 183 kg dressed from 232 kg alive (0.79); UMaine gives commercial turkey dressing 77 to 81 percent; no page gave deer fat or hide shares, wildfowl yields or dog figures. Turkey and dog species figures are in `living_stock.json` (Complaints/532) and were not touched.

Pages that returned 403/404 or only a PDF dump: bladeforums trade-axe thread, pv-magazine, epj-pv, britannica.com zinc-processing, lakesidepottery.com weights PDF, Heidelberg sherd study (Anubis block). Status stays open.
