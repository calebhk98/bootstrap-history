# No check that the occupational distribution of a baseline run is plausible

**Status:** open - check written (fails on the measured shares below)

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Last: depends on 609 to 618.

**What is wrong.** Nothing validates the distribution of trades in a run against the historical shape: most households on the land, textiles and building among the largest non-farm trades. The farm share and non-farm shares are different measures, so the gap is not a defect by itself.

**Evidence.** `python3 -c "from sim.tests.harness import sim; print(sim(civ='rome_100ad').labour.farm_share_of_hours())"`; `lab.population_report()['trades']`.

**Why it matters.** DESIGN 4.2 asks for validation against distributions and relationships, not dated events.

**What it would take.** A slow test of the baseline for each civilisation: the share on the land and the ordering of the largest non-farm trades fall in plausible ranges taken from sources.

**Test.** The test passes on a Rome run after the trades above exist.

## Check added, and what it finds

`sim/tests/test_occupational_distribution.py` (slow) groups `economy.society_labour_hours` after a year of a
no-intervention game by `data/world/occupation_groups.json` (groups, wide bands, sources; the figures are marked
recalled there, not looked up). Print the shares with
`python3 sim/simulator.py economy-check --civs rome_100ad --years 1 --occupations`. The ordering test (textiles or
building the largest classified non-farm group) passes; the band test fails honestly, bands unchanged.

Measured (one year, seed 1, `python3 -m sim.tests --slow --only occupational_distribution --jobs 1`), share of hours:

| group | rome_100ad | england_1300 |
|---|---|---|
| agriculture (farmer, herder, fisher) | 0.361 | 0.397 |
| unattributed (`labourer`) | 0.625 | 0.580 |
| textiles | 0.003 | 0.004 |
| building | 0.007 | 0.012 |
| food processing | 0.0001 | 0.001 |
| other crafts | 0.004 | 0.007 |
| transport | 0 | 0 |
| services and state | 0 | 0 |

Causes: (1) most hours are still the generic `labourer` pool, which the recipes for wool, wine, oil, brick and the
like bill instead of the new trades, so the farm group reads low and nothing is attributed; (2) soldiers, merchants,
scribes and carters book no hours into `society_labour_hours`, so transport and services read zero; (3) the new
spinner, weaver, miller and baker trades hold hours of a few thousandths. The test closes this complaint once these
are fixed, not by moving the bands.
