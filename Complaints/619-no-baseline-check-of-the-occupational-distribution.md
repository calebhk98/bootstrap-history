# No check that the occupational distribution of a baseline run is plausible

**Status:** open - farm share now read by head count and inside its band for rome, england and han; the non-farm groups are still outside theirs. Check written; it was last measured before the wheat-labour and grain-input changes, so the table below is historical and needs a re-measure (GitHub #64 tracks)

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

## Measure and recipe billing (this pass)

- The measure is `sim/labour/occupational_shares.py` `hours_by_trade`: the society's hours (own-plot and hired farming,
  household work and the unskilled pool are all inside them, since the society's total is every working-age person less
  the army), plus what employers hold on staff. Staff above the society's hours for their trade now come out of the
  unskilled pool (they were added on top, counting the same people twice); the army, which the society's total already
  gave up, is added whole (`outside_society_trades` in `data/world/occupation_groups.json`). Rule tests on built inputs:
  `sim/tests/test_occupational_hours_rule.py` (quick).
- Own-plot farm work was not kept out: farm hours are the society's farm trade. Household work a cohort does itself is not
  persisted as hours, so it is not separately measured (it sits inside the pool); open.
- Recipes: the wool, wine, oil, brick, milling and baking recipes already bill their trade. The ones still on `labourer`
  are mostly crushing, digging, quarrying and hauling, which the trade's own note gives to the labourer. Rebilled now:
  waste haulage (porters on foot, carters for pack and cart) and natron (salt worker, as the recipe's own basis says).
- Not measured: the Rome and England shares after these changes. `economy-check --occupations` does not finish in five
  minutes; the slow topic `occupational_distribution` is still to be run by the orchestrator.

## Ordering rule dropped (2026-10-21)

The check that textiles or building is the largest non-farm group is removed with its `ordering` entry in
`data/world/occupation_groups.json`: no opened source supports it, and the one opened source with a split
(Broadberry, Campbell and van Leeuwen 2013, Explorations in Economic History 50, England's labour force in 1381:
services above industry) contradicts it. See `Complaints/reports/research-occupation-bands-and-porters.md`.

## Farm share measured, cause found (2026-10-22)

Measured on the no-intervention opening plus one year (`python3 -m sim.tests --slow --only occupational_distribution --jobs 1 --topic-seconds 290`).
Rome, hours in the field: the farm share was about a third; the labour core's head count of farmers is
the large majority of working people. Neither side of the model was too productive; the check compared unlike things.

- Farm labour productivity is not too high. The default technique is wheat on an ard with ox at the farm-labour data's
  hours a hectare (`data/world/farm_labour.json`, Columella 2.12.1), four-fold return on seed, two-field rotation. One farm
  worker crops what the farming year allows (`agriculture.hectares_cropped_per_farm_worker`, set by hours, not the harvest
  window) and the year's harvest just covers food need plus seed (shortfall zero); the farm land held is below the arable
  ceiling, so land is not what binds. The sourced per-worker productivity figures for comparison are still missing: the
  research report holds no output per farm worker (it has shares only), so no claim is made that the figure is too high or low.
- The farm hours are the food balance's answer: only so many hands are needed to feed the population. Everyone else's
  working-age hours land in the unskilled pool (`labourer`), which the check reads as "unattributed".
- The labour core seeds the people no employer needs as farmers working their own plots
  (`sim/labour/market/opening.py`, the idle trade). Those people are the farming households; in hours they spend only part of
  their year in the field, the rest sits in the pool. This is the by-employment gap of 645 and 542 (spinning, herding, carting,
  building, household work have no place in a farming household's year).
- The sources count people by main occupation (England 1381 labour force, Broadberry, Campbell and van Leeuwen 2013 Tables 1
  and 2; Erdkamp on the Roman commonplace), not hours. Reading hours against a head-count band was the error in the check.

Fix: `people_by_trade_of_all_employers` (`sim/labour/occupational_shares.py`) reads the band check on the labour core's head
count (staff counted once, the army whole); the hours reading is still printed beside it. Rule tests:
`sim/tests/test_occupational_hours_rule.py` (`PeopleByMainOccupation`, and the part-time household case). The bands are unchanged.

Agriculture by people after: Rome 0.863, England 0.893, Han 0.825 (all inside 0.55 to 0.90). England sits just under
the top edge. The check is still red for the other groups, which are the open work of this complaint: textiles, building,
food processing, transport and other crafts are well below their bands in all three civilisations (trades with no or too
little demand, 609 to 618, 645), services_state is below its band for England and Han, and the unattributed pool is
just over its cap for Rome and Han. Caution: the farmer head count is the residual after the other trades take the people
their work needs, so a high farm share by head count follows from under-built non-farm trades and is weak evidence by itself.
