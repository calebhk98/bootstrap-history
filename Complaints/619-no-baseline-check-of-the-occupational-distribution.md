# No check that the occupational distribution of a baseline run is plausible

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Last: depends on 609 to 618.

**What is wrong.** Nothing validates the distribution of trades in a run against the historical shape: most households on the land, textiles and building among the largest non-farm trades. The farm share and non-farm shares are different measures, so the gap is not a defect by itself.

**Evidence.** `python3 -c "from sim.tests.harness import sim; print(sim(civ='rome_100ad').labour.farm_share_of_hours())"`; `lab.population_report()['trades']`.

**Why it matters.** DESIGN 4.2 asks for validation against distributions and relationships, not dated events.

**What it would take.** A slow test of the baseline for each civilisation: the share on the land and the ordering of the largest non-farm trades fall in plausible ranges taken from sources.

**Test.** The test passes on a Rome run after the trades above exist.
