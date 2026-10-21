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

**Carriage inputs (moved from 561 when it closed).** Unsourced in `sim/geography/transport.py` and `foreign_routes.py`: the
cart's structural payload (only the team's pull limits it), river current and towing speed (nothing supplies them to
`routes_rates.rate`), `CART_SERVICE_LIFE_KM` (temporary heuristic) and `BARGE_SELF_MASS_KG` (grade D). Opened: Scheidel,
"ORBISprices" (2013 working paper) pp. 6-7: the Edict's land and river rates take no account of river velocity, so the Edict
cannot validate a current-dependent river rate. Not opened: Raepsaet on Roman carts, the Edict's freight chapters, river towing
studies. The money ratio across modes is validated by `sim/tests/test_freight_money_ratio.py`.

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
