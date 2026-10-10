# Request: things a very rich founder can spend on

**Status:** closed - works for every kind of spending named, and the engine mechanics they needed, are built

Late in a run the founder holds tens to hundreds of millions of denarii with little to buy: research is paced by prerequisites and calendar floors, so idle cash only raises confiscation risk. The surplus itself is intended (advancing the whole society earns far more than working for yourself); what is missing is uses for it.

Stakeholder request: add what very wealthy people and companies have actually done with money through history, as ordinary data-driven works (nodes or purchasable works using the node `mechanics` field, see data/branches/MECHANICS.md), each acting through the normal rules (literacy, health, reputation, protection, state favour, society values, demand, labour), not through special cases. Examples to choose from:

- Endowments: schools, universities, libraries, museums, hospitals, observatories, research prizes and foundations.
- Public works: aqueducts, baths, roads, bridges, ports, lighthouses, canals, railways, telegraph and telephone networks, electric lighting for a city.
- Patronage and display: public games and festivals, theatres, sports arenas, temples, monuments, patronage of artists and scholars.
- Commerce and finance: banks, insurance, joint-stock companies, gambling houses, newspapers.
- Grants to the state: grain doles, funding the army or navy, paying off public debt (buying protection and favour).
- Expeditions: exploration, colonies, trade missions.

Many should be repeatable or scalable, cost upkeep, and be at risk from the same hazards as the rest of the household. Keep content in data so mods can add more.

**Also reported (England 1300 fog playtest, `Complaints/reports/playtest-england-1300-fog-triage.md`):** things the tester would spend late money on: intermediate education institutions (208), partial knowledge hedges such as deposited copies and paid scribes (209), opening ventures in other towns (211), patronage of translations and university chairs, and relief from debt-service pressure (210). Lead metallurgy at 1375 was the one project money could not yet pay for, and the tester asked whether costs keep scaling faster than income in the second half. The "rich" lifestyle cost was praised as wealth having a running cost.

Also reported (Han China 100 AD fog playtest, tester item(s) 53, 157, 167, 172, 180; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): with cash at 140 billion and more, the tester's list of money sinks: fleet hulls and charter (223), nationwide school and clinic rollout with coverage targets, disaster reconstruction and relief, safety upgrades, endowments with chosen beneficiaries, branches and provincial expansion (see 211), political settlements, and a hydro station (research bill 5 million, 3 MW, opening 0.8 million against net 8.7 billion, which read as pocket change). `buy housing` was praised as the one simple, useful sink but does not involve site or commute choices.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 208 (`closed/208-request-intermediate-education-institutions.md`): intermediate education institutions (scriptorium, cathedral school, guild school, tutor) do not exist as nodes.
- 209 (`closed/209-request-intermediate-knowledge-hedges.md`): intermediate knowledge hedges: only corpus_written and corpus_dispersal exist; lower-rank hedges would use the existing tiers.
- 211 (`closed/211-request-open-a-venture-in-another-town.md`): open a venture in another town: needs location on concerns and per-location demand.
- 223 (`closed/223-large-merchant-ships-cost-nothing-and-pay-most.md`): large merchant ships: bills done; needs a hull, route and port asset model.

## How it was closed

Every kind of spending the request names is an ordinary work in `data/branches/56_benefactions.json` (or an existing concern that gained a mechanic), and each acts through a mechanic named in `data/branches/MECHANICS.md`. Sizes are `temporary_heuristic` values; run `why <id>` for a work's current bill.

- Paying a state's debt, disaster relief and political settlements: the node mechanic `transfer` (`sim/engine/transfers.py`) pays the state once when a work is finished, sized by the state's debt, by the claims it owes interest groups, or by a stated sum of labour hours; the `pay` command does the same by hand. Works: `ben_state_debt_redemption`, `ben_political_settlement`, `ben_disaster_relief_grant`. A smaller debt costs the state less interest, and a funded claim is not raised from taxpayers.
- A state's share of one concern's takings: the node mechanic `state_levy` (`sim/engine/concern_levy.py`). The gambling house and the lottery now earn from the play households spend on (the `amusement` need, `data/production/99_gaming.json`) and pay the state a share.
- Coverage targets: the node mechanic `coverage` and the `rollout` command (`sim/engine/coverage.py`) repeat a work until a share of the people who can use it is served, and a work that declares it is bounded by serving everyone, not by a few towns. District clinics (`ben_district_clinics`) lower the disease burden by the share they reach (`data/civilizations/_TECH_EFFECTS.json`).
- Settled colonies: the node mechanic `settlement` and the `settle` and `colonies` commands (`sim/engine/colonies.py`, `sim/geography/settlement.py`). A colony is a tile held beyond the country's own with a people of its own, stepped by the same demography and fed by the share of the tile its people can hold.
- National disaster recovery: the node mechanic `food_relief` (`sim/engine/food_relief.py`) puts the grain a running dole buys into the nation's nutrition, which sets how many die and are born.
- Newspaper legitimacy: the node mechanic `state_legitimacy` (`sim/engine/legitimacy.py`) scales the state's authority; the free press lowers it.
- A lighting need and the working day: `light` is its own need, met by candles, lamps and electric lamps (`data/production/99_lighting.json`), apart from `warmth`; the node mechanic `working_day` (`sim/engine/working_day.py`) lengthens the working year for the people lit streets reach.
- Schooling split by group: a `schooling_flow` can name the literacy figures it teaches (`reaches`); `ben_village_schools` teaches the many and `ben_endowed_college` the lettered.

Tests: `sim/tests/test_complaint_190_transfers.py`, `test_complaint_190_public_works.py`, `test_complaint_190_colonies.py` and `test_complaint_190_benefactions.py`.
