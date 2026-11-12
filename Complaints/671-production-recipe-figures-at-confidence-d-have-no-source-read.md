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
