# No check that the occupational distribution of a baseline run is plausible

**Status:** open - check written; it was last measured before the wheat-labour and grain-input changes, so the table below is historical and needs a re-measure (GitHub #64 tracks)

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Last: depends on 609 to 618.

**What is wrong.** Nothing validates the distribution of trades in a run against the historical shape: most households on the land, textiles and building among the largest non-farm trades. The farm share and non-farm shares are different measures, so the gap is not a defect by itself.

**Evidence.** `python3 -c "from sim.tests.harness import sim; print(sim(civ='rome_100ad').labour.farm_share_of_hours())"`; `lab.population_report()['trades']`.

**Why it matters.** DESIGN 4.2 asks for validation against distributions and relationships, not dated events.

**What it would take.** A slow test of the baseline for each civilisation: the share on the land and the ordering of the largest non-farm trades fall in plausible ranges taken from sources.

**Test.** The test passes on a Rome run after the trades above exist.

## Check added, and what it found (historical)

`sim/tests/test_occupational_distribution.py` (slow) groups `economy.society_labour_hours` after a year of a
no-intervention game by `data/world/occupation_groups.json` (groups, wide bands, sources). Print the shares with
`python3 sim/simulator.py economy-check --civs rome_100ad --years 1 --occupations`. When written, the band test failed
honestly (bands unchanged) and the ordering test (textiles or building the largest classified non-farm group) passed; a
later run had services and state leading. Neither has been re-run since the changes below. The measured shares then were:
agriculture about 0.36 for Rome, the generic `labourer` pool about 0.63, every other group near zero, transport and services
zero.

Causes found then: (1) most hours were still the generic `labourer` pool, which the recipes for wool, wine, oil, brick and
the like bill instead of the new trades; (2) soldiers, merchants, scribes and carters booked no hours into
`society_labour_hours`, so transport and services read zero; (3) the new spinner, weaver, miller and baker trades held
hours of a few thousandths. The test closes this complaint once these are fixed, not by moving the bands.

## Changes since that measurement

- Wheat labour is sourced: `wheat_kg` books about 475 farmer-hours a hectare from Columella 2.12.1 (was 150), built in
  `data/world/farm_labour.json` (Complaint 646, passes 6 and 7). The farm share in the undisturbed Rome scenario fell,
  because a worker's cropped area is now set by the farming year, not the harvest window.
- The farm share of Rome's no-intervention run is checked against the agriculture band in `test_farm_edges_scenario`
  (slow), not against recorded values. The inputs of `fraction_of_population_that_must_farm` were re-read (Columella 2.9.1
  and 3.3.4, `data/world/grain_yield.json`); measure it with
  `python3 -c "from sim.world import agriculture as a; print(a.fraction_of_population_that_must_farm())"`.
- Still unsourced: `ANNUAL_LABOUR_HOURS_PER_FARM_WORKER` (a labelled heuristic), grain spoilage, the draught-animal fodder
  taken from the harvest (not modelled), and the single-staple ration.

## Research needed

The bands in `occupation_groups.json` rest on sources the file itself marks "Recalled" (Scheidel and Friesen 2009, Allen
2000, Bairoch 1988, Broadberry et al. 2015, Wilson 2002). A validation band is only as good as its source: open each and
record the figure (page, table) for the share of the labour force in agriculture and in textiles, building and food
processing, for Roman Italy and the provinces and for medieval England. The model aims at realism, so the check
compares hours the model books with what the sources give, and a band the sources cannot support is widened or dropped,
not tuned to the run.
