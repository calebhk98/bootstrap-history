# Request: things a very rich founder can spend on

**Status:** partly - twenty-two ordinary works in data/branches/56_benefactions.json act through existing mechanics. The fifteen first: schools, library, research foundation, hospital, water works, harbour, telegraph, games, temple, patronage, house bank, underwriting, grain dole, state subsidy, expedition. Added from `Complaints/reports/late-game-spending-research.md` (ready-now list): public museum (schooling flow, standing; no corpus hedge, because the knowledge-risk tests assume exactly two corpus nodes), endowed free press (schooling flow, reach, alarm and eminence factors), electric city lighting (staff-loss counter, protection, standing; its electricity draw comes from its prerequisites, and it carries the upkeep `civ_street_lighting` lacks), fire and flood brigades (output-factor and staff-loss counters), a building-trades school and a machinists' school (`labour_productivity` by trade, staff capacity), and a fortified trading post wrapping `exp_colony_administration` (reach, output-factor counter). Not built, data only but outside this change: gambling house and lottery gating (an edit of `fin_gambling_house` and `fin_lottery` in `data/branches/40_finance_institutions.json`: a `pre`, `alarm_factor`, `protection`); district clinics (`disease_burden` needs a weight in `data/civilizations/_TECH_EFFECTS.json`, which changes every run's burden denominator, so it wants a fingerprint re-record). Still needs engine work: a one-off transfer for paying a state's debt, disaster relief and political settlements (`pay_state` has no command or node field); a per-concern state levy for licensed gambling; coverage targets for rollouts; settled colonies (owned territory, own population); national disaster recovery; newspaper legitimacy effects; a lighting need and working-day length; schooling split by place or group

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
