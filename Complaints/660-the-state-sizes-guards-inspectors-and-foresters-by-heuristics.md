# The state's guards, mine inspectors and foresters are sized by labelled per-head heuristics, and the ceilings keep a scale

**Status:** partly - the per-head sizing of guards, inspectors and foresters is now a sourced ballpark (confidence C); open: the mine and forest ceiling scales (`MINE_CEILING_*`, `FOREST_HA_PER_MILLION_KM2_PER_SC`), sizing from crimes, claims and woodland instead of a per-head time, and a watchman trade

**Done.** The state's budget keeps a `guards`, an `inspectors` and a `foresters` line (`sim/agents/order.py`), staff hired in the
labour market and paid like the administration line. What they reach follows the 620 time rule over the road from the
seat (`CollectionView.order_share`, `inspection_share` in `sim/agents/collection_world.py`; `order_reach` and
`inspection_reach` in `sim/polity/reach.py`). Theft and plunder order (`sim/coin/theft.py`, `sim/coin/theft_exposure.py`) read the guards
employed, and the mine land ceiling (`mine_land_ceiling`) reads the inspectors employed. The forest ceiling (`forest_land_ceiling`) reads the foresters employed (`CollectionView.forest_share`,
`forest_reach` in `sim/polity/reach.py`). Country states keep the same
lines. Tests: `sim/tests/test_state_guards_and_inspectors.py`.

**Still open.**

- The forest ceiling carries the labelled `FOREST_HA_PER_MILLION_KM2_PER_SC` scale per unit of forest reach; it should
  follow the woodland a forester can keep under tenure.
- How many guards and inspectors a state keeps is a labelled per-head time (`PATROL_DAYS_PER_PERSON`,
  `INSPECTION_DAYS_PER_PERSON`, `FORESTER_DAYS_PER_PERSON` in `sim/agents/tuning_order.py`, no source found); guards should follow the crimes a
  district has, inspectors the claims on the registry and foresters the woodland held.
- The mine ceiling still carries the tonnes-per-reach scale (`MINE_CEILING_*_SCALE_*`) per unit of inspection reach;
  the ceiling should follow tonnes an inspector can keep registered.
- Guards and foresters are booked in the unskilled trade and inspectors in the scribe trade; a watchman trade in
  `data/world/trades.json` would let the labour market price them apart.

**Validation against staff-per-head anchors** (`sim/tests/test_guard_staff_per_head_anchors.py`, rule called on Rome's opening
population): the sized guards come to 0.0001 staff per head, below every sourced anchor (a nome capital 0.0017, Egyptian villages
0.0077 to 0.020, Rome's capital watch 0.0085). The anchors are settled places with an organised watch, not province-wide
averages, so a state-wide figure under them is expected, but the gap is about a factor of seventeen below the lowest, and
the test pins only that the figure is positive, under the densest anchor and under the lowest. It does not show the value is
right. `PATROL_DAYS_PER_PERSON` stays labelled.

**Research done** (`Complaints/reports/research-state-staffing.md`): the capital's standing watch (vigiles plus urban cohorts) gives an
upper bound on guard density, tested in `sim/tests/test_order_staffing_sourced.py`. No source was found for a state-wide guard
ratio, inspectors per tonne or claim, or foresters per hectare, so those stay labelled heuristics (the `MINE_CEILING_*` scales
gained `retire`).

**Research needed.** How pre-modern states kept order and enforced ceilings, from what the staff did rather than a ratio:
(a) the district watch or patrol cost per head of population for a province (Roman provincial police: the stationarii and
beneficiarii, Egyptian nome police; medieval England's hundred and shire constables), to size guards from the crimes a
district has; (b) how many claims or tonnes a mining procurator's staff registered (Vipasca regulations, Spanish mining
districts); (c) woodland a forester or warden held (medieval forest eyres and the royal forests' verderers). Each answer
cites the page opened.

## Sourced (2026-11, ballpark standard)

Values are guard-, inspector- and forester-days per person per year; a working year is 200 days.

- `PATROL_DAYS_PER_PERSON` 0.02 -> 0.34 (0.0001 -> 0.0017 staff per head). Oxyrhynchus 60 phylakes for 36,000 (0.00167); Rome 0.0085; modern median 300 police per 100,000, India 155, Bangladesh 127 (https://en.wikipedia.org/wiki/List_of_countries_by_number_of_police_officers); Qing county yamen about 500 staff for 100,000 to 200,000, runners a part of it (https://en.wikipedia.org/wiki/County_magistrate). `test_guard_staff_per_head_anchors` range check is no longer an expected failure.
- `INSPECTION_DAYS_PER_PERSON` 0.005 -> 0.002. GAO-03-945 (https://www.govinfo.gov/content/pkg/GAOREPORTS-GAO-03-945/html/GAOREPORTS-GAO-03-945.htm): 350 inspectors for 107,500 coal miners = 0.0033 per miner; miners per head 0.003 from Las Medulas (60,000 workers, Wikipedia) against 59 to 76 million Romans (Wikipedia 'Demography of the Roman Empire') times an assumed three such districts. The miner share is the loose input.
- `FORESTER_DAYS_PER_PERSON` 0.01 -> 0.28. Woodland 15 per cent of England at Domesday (https://rfs.org.uk/wp-content/uploads/2021/05/7.-A-Brief-History-of-British-Woodlands.pdf), England 132,932 km2, 1.2 to 1.6 million people (Wikipedia 'Domesday Book'): 1.42 ha per head; a third under forest law (Wikipedia 'Royal forest'); one guard per 340 ha (Bangladesh, https://www.tbsnews.net/environment/green-coverage-grows-not-enough-guards-protect-it-88987): 0.0014 per head.
- All three are now `engineering_estimate`, confidence C, no `retire`. Left unsourced: the four `MINE_CEILING_*` scales and `FOREST_HA_PER_MILLION_KM2_PER_SC` (tonnes and hectares per unit of reach); mechanism work (sizing from crimes, claims, woodland held; a watchman trade) is not a sourcing task and stays open.

## Pass (2026-11, any-source bar)

- `MINE_CEILING_BASE_IMPERIAL` and `MINE_CEILING_STATE_SCALE_IMPERIAL` (20,000 and 60,000 t a year): Wikipedia 'Roman metallurgy' (opened) gives lead 80,000 t a year across the Empire (copper 15,000, iron 82,500); Wikipedia 'Mining in Roman Britain' (opened) gives about 100,000 tons of lead and 15,000 of copper (Fleming 2012). Base plus scale at full reach is 80,000, so the pair is now confidence C (values kept); the split between base and scale is unsourced.
- `MINE_CEILING_BASE_STRANGER` (3,000) and `MINE_CEILING_STATE_SCALE_STRANGER` (4,000): no source found. 'Laurium' and 'Mining in ancient Rome' (opened) say the state owned and leased mines to private operators but give no tonnage for either side. Needed: tonnes a year a private lessee or foreign operator ran against the state's own (for example Vipasca lease terms with output, or Rio Tinto lead output per lessee).
- `FOREST_HA_PER_MILLION_KM2_PER_SC` (and its base): Wikipedia 'Royal forest' (opened) gives one third of southern England under forest law and no forester count or hectares. The constant's note says Rome's ceiling is about 667,000 ha, but the ceiling the code gives Rome is about 11,000 ha at no reach and 37,000 at full reach (area 10.0 million km2, read through the helpers in `sim/tests/test_complaint_45_forest_area_not_region_count.py`), about eighteen times under. The Domesday woodland share (15 per cent of England, in the foresters entry above) is about 15 million ha per million km2, far above either. Left unchanged: what is needed is the coppice share of woodland an actor holds under tenure, and a decision whether the ceiling is per actor or per state.

## Pass 12 (round 2, any-source bar)

- `MINE_CEILING_*_STRANGER` (3,000 and 4,000): now `engineering_estimate`, confidence C, derived. Xenophon, Poroi 4.14-4.15 (https://stuff.mit.edu/afs/athena/course/21/21h.401/www/local/xenophon_poroi.html, opened): Nicias leased out a thousand men in the mines; Wikipedia 'Mines of Laurion' (opened): almost 20,000 slaves, so the largest named lessee held 5 percent of the workforce; 5 percent of 80,000 t (the imperial total) is 4,000 t against 7,000 here, within 3x. Assumes output proportional to miners. No tonnes per lessee found (Vipasca, Laurium, Free miner and Stannary pages opened or 404; none gives tonnage). The base/scale split is still unsourced.
- `FOREST_HA_PER_MILLION_KM2_PER_SC`: 2,575 -> 69,000. The constant's note put the empire-wide coppice at 667,000 ha over 9.5175 million km2, 70,100 ha per million km2 at full reach, but base 1,100 plus 2,575 gave 3,675 (about 19x under). Check of the 667,000 ha from opened figures: iron 82,500 t a year (Wikipedia 'Roman metallurgy'), at least 2 t of charcoal per t of iron (Cleere thesis, wealdeniron.org.uk), charcoal 25 percent of wood by weight (Wikipedia 'Charcoal'), coppice 2.5 dry t per ha per year (conservationhandbooks.com): at least 264,000 ha for iron alone. The old value gave 35,000 ha empire-wide, 7.5x under that floor, so the value was wrong and the note was right. The base (1,100) was not edited here and is now 1.6 percent of the full-reach total; whether it should scale with it is open. The 500,000 t empire-wide charcoal figure was not opened.
