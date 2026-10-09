# Epidemic model: research and design proposal (for Complaint 386)

Status: research report, no code changed. Written for the owner's decision on Complaint 386.

Revision 2026-10-09 (review pass): the owner decided on 2026-10-06 to replace the authored fraction with
a population-level model that spreads through trade and geography and responds to technology. This pass
checked the report against the current code, closed research gaps and added Section 11 (build-ready
detail: sub-year stepping, virgin-soil versus endemic parameters, Americas validation range, codebase
hookup, first code step and test). Everything corrected in place is marked "[corrected 2026-10-09]";
Section 11.1 lists every change. Source strength tags: `read` (opened and read, possibly only an
abstract, said so), `summary` (seen only in a search-result summary, page not opened), `recalled`
(standard literature not re-verified), `disputed` (sources disagree).

## 0. Summary

Replace the authored "fraction lost per wave, any year of a window" hazard with a
data-driven, population-level metapopulation epidemic model in a new package
`sim/disease/`. A pathogen is a data file describing a small reaction network
(compartments, transitions, transmission routes, reservoirs, seasonality
drivers, age and nutrition dependent severity). The engine only knows how to
integrate such networks over tiles joined by routes. Technology never touches
the disease engine: tech nodes change tile level public-health state
(sanitation, quarantine capacity, medical care, vector habitat, vaccination
coverage), and pathogen files declare how their routes respond to that state.
Immunity is stored per tile, per age band, per pathogen, so a population that
has never met a pathogen is simply a population whose immune share is zero.
The New World collapse, its size and its recurrence interval then fall out of
reproduction number, susceptible replenishment, nutrition and care collapse.

Why this answers 386: an epidemic wave exhausts susceptibles. A second wave of the
same pathogen cannot recur next year at full strength, and mortality falls as
survivors become immune. Both properties are consequences of the model, not
of authored numbers (CLAUDE.md 4.1, 4.2).

Repository base: re-checked against the real base (PR #36). The walled packages
`sim/economy/`, `sim/labour/`, `sim/geography/`, `sim/agents/` and `sim/ui/` exist,
with the rules in `docs/architecture/PACKAGE_WALLS.md` and the geography contract in
`sim/geography/INTERFACE.md`. The proposed `sim/disease/` is a sixth walled package
following that rule (its own `api.py` with `WALL = "two-way"`, an object on `Sim`,
and an engine adapter), and it reads places and routes only through `sim.geography.api`.

## 1. What exists today

Read from the code (no numbers stated, run the commands to measure).

- `data/civilizations/*.json` carry `hazards` entries with `staff_loss`, `years`
  and a note. `data/civilizations/mexica_1500.json` "Old World epidemics on
  contact" is one such entry.
- `sim/engine/society_hazards.py` rolls these in `_shock_staff_loss`; the chance of
  a wave per year in the window is the declared temporary heuristic
  `STAFF_LOSS_HAZARD_ANNUAL_CHANCE` in the same file (grep it); `sim/engine/fog.py` repeats the same
  number as a literal for the player's forecast (grep `staff_loss_wave_chance_per_year`), so it must
  be removed in two places [corrected 2026-10-09: the earlier text pointed only at fog.py]. Each wave
  removes the authored share: `staff_loss_exposure` applies the relief from technology,
  `apply_staff_survival` thins the founder's household staff, and `_apply_population_mortality_shock`
  in `sim/engine/core.py` cuts the single national `Population` by band, weighted by the starvation
  vulnerability ratios (which core.py itself labels a temporary heuristic, because those ratios were
  sourced for famine, not epidemics).
- The engine holds one national `Population` (`sim.population`), not one per tile. Tile populations
  are derived by multiplying the national total by a share from `sim.geography.api.settlement`
  (`population_share`, from food capacity); see `sim/engine/economy_port_setup.py` and
  `economy_port_year.py` [corrected 2026-10-09: Section 6.2 earlier assumed people by tile and band
  come from demography; they do not, see Section 11.4].
- Technology reduces a wave through `hazard_counters` entries on tree nodes
  (`kind`, `share`, `label`, `order`, optional `requires_running`) combined in
  `sim/engine/hazard_relief.py`, with a residue once an institution is closed
  (`KNOWLEDGE_RESIDUE_AFTER_CLOSURE`, labelled a temporary heuristic).
  `sim/tests/test_plague_mitigation_realism.py` shows the nodes in use
  (`germ_theory`, `med_quarantine_sanitation`, `md2_vaccine_plague`).
- `sim/world/demography.py` has three age bands (children, working age,
  elderly) as float counts, a `nutrition_ratio`, `_excess_mortality_multiplier
  (nutrition_ratio, vulnerability)`, and a scalar `disease_burden` axis (one is
  pre-industrial, zero is fully modern) that scales baseline mortality and the
  fertility ceiling. Its docstring states crisis mortality (famine and epidemic)
  should be routed through `Population.step`.
- The agent economy (`sim/economy/households_cohort.py`) holds one `Cohort` per
  tile and income class with `people` and `working_people`; this is where
  disease deaths and lost working days must land.
- Places and routes: `sim/geography/api.py` per `sim/geography/INTERFACE.md`:
  `tile_ids()`, `tile_facts(tile_id)` (latitude, longitude, land area, coastal,
  `neighbours`, `climate_class`, region), `layer_value(tile_id, layer_id)`,
  `route(...)` (legs with mode, km and days) and `reach(origins, modes,
  days_budget, ...)` (tiles within a travel budget), `freight_links(modes)`;
  monthly temperatures per climate class in `sim/geography/climate_temperatures.py`.
  Geography does not read the tech tree; the caller passes what actors hold.

Three structural problems the model must remove: loss is an authored fraction;
timing is an annual coin flip independent of contact, geography or immunity; and
technology acts as a flat multiplier on the authored fraction instead of on a
mechanism.

## 2. Recommended model

### 2.1 Core: stochastic-where-small, deterministic-where-large metapopulation compartments

Family: age-structured compartmental model (SIR, extended to SEIR and MSEIRS,
Hethcote 2000) on a metapopulation (tiles as subpopulations coupled by
movement), the approach of GLEaM (Balcan et al. 2009) and of the measles
travelling-wave work (Grenfell, Bjornstad and Kappey 2001). Reasons:

- The question is population level (owner's requirement); agents per person are
  unaffordable and unneeded for the effects that matter here (final size,
  timing, recurrence, age pattern).
- Compartment models give the quantities that validate against history:
  reproduction number, final size, inter-epidemic period, critical community
  size.
- Immunity is one number per age band per tile, which is cheap to store and to
  save (CLAUDE.md 4.6 allows free restructuring of saves).
- Metapopulation coupling reproduces the observed hierarchical spread from big
  centres to small towns (Grenfell et al. 2001) and the dominance of the transport
  network over short range contact for large scale spread (Balcan et al. 2009;
  Viboud et al. 2006 found regional spread tracks worker flows, a gravity law,
  better than distance).

Rejected alternatives: agent-based individual models (Covasim style, EpiModel
network models) are too heavy for tens of thousands of tiles-years and need
contact network data the project cannot source for antiquity; they can be a later
"zoom in" for one city. A single national SIR (what the authored fraction
pretends to be) loses geography and the arrival time of a pathogen along trade.

### 2.2 Generic compartment network (what makes the engine content free)

A pathogen file declares named states and transitions; the engine integrates
whatever it is given. Minimum vocabulary:

- Host states per age band: `susceptible`, any number of incubating or infectious
  states, `recovered_immune`, and optionally `waned` flowing back to
  `susceptible`. SEIR is two extra states; waning immunity (SEIRS) is one more
  transition with a rate equal to one over the immunity duration (permanent
  immunity is rate zero). Branching states cover plague (bubonic stage with a
  probability of progressing to a pneumonic stage; Section 3).
- Non-host reservoir states, each belonging to a named reservoir kind: vector
  (human lice, fleas, mosquitoes: a population with its own birth, death and
  infection), animal host (rodents, with their own susceptible and infected
  states and an epizootic that ends when susceptible rodents run out), and
  environment (Vibrio in water, a concentration with growth and decay).
  A reservoir can be a fixed external focus (a wildlife focus at a place that
  exports infection by spillover at a rate), which is how recurrent plague
  introductions are represented (Schmid et al. 2015 trace successive European
  plague waves to repeated climate-driven reintroduction from Asian foci rather
  than to persistence in Europe).
- Force of infection is a sum over named routes. Each route has a kind
  (`person_to_person`, `vector`, `environment`, `zoonotic_spillover`), a
  transmissibility, and an infectiousness profile over the infectious states.
  Route kinds are engine primitives; pathogens are data composed from them.
  This is the Ross-Macdonald structure for vector routes (Smith et al. 2012) and the
  environmental-reservoir structure for cholera (Codeco 2001), generalised.

Formula conventions (spelled out names):

    force_of_infection_in_tile_and_band =
        sum over routes of
            route_transmissibility
            * seasonal_multiplier_of_route
            * exposure_multiplier_from_tile_state_of_route
            * infectious_pressure_of_route_in_tile / effective_population_of_tile

    infectious_pressure_of_person_route =
        sum over bands and infectious_states of
            infectious_count_in_state * relative_infectiousness_of_state
            + imported_infectious_count_from_connected_tiles

    new_infections_in_substep =
        susceptible_count * (1 - exp(-force_of_infection * substep_length))

    basic_reproduction_number =
        route_transmissibility * mean_infectious_duration
        (per route, from the next-generation matrix for multi-state, multi-route pathogens)

The next-generation matrix of the data file lets `simulator.py validate` print
the basic reproduction number the file implies and compare it with the sourced
range declared in the same file. That is the check that the data was entered
correctly and that nothing is hardcoded in the engine.

### 2.3 Spatial coupling

Between tiles i and j the infectious flux is
`travellers_per_year(i,j) * infectious_share_of_origin_tile * survival_in_transit`.

- `travellers_per_year` is read from what the economy already knows: merchant
  and crew movements implied by trade volume on the route (people per tonne
  carried by mode, a derived quantity, not a table of historical flows), plus
  migration, armies and pilgrimages as other actors generate them (the general
  actor rule). A route's days and mode come from `sim.geography.api.route(...)` (legs with mode,
  km and days) and `freight_links`; `reach` bounds which tiles an infectious
  traveller can plausibly arrive in within the infectious period.
- `survival_in_transit` is the chance a traveller who is infectious on departure
  or infected in transit is still infectious on arrival. A fast pathogen with a
  short infectious period only crosses short routes; a pathogen with a long latent
  period can cross a whole sea. This falls out of the infectious duration and
  route days; no per-disease code. The incubation interval is advanced during
  transit, so a ship leaves with a healthy-looking person and arrives with an
  outbreak.
- Goods are a second carrier for vector borne diseases. A pathogen declares
  `carried_by` (`people`, `goods`, or both): fleas and lice ride in grain, cloth
  and ships. The goods channel uses tonnes moved, from the same trade flow the
  price solver already computes. Dean et al. (2018) model human ectoparasites
  spreading with people, clothing and bedding; Benedictow's rodent view puts the
  vector in grain cargoes; the carrier set in data lets both hypotheses be
  tested as data variants (see open questions).
- Local coupling (commuting, neighbouring tiles by adjacency) is a second,
  weaker flux with a gravity or radiation form (Viboud et al. 2006), parameters
  derived from tile population and distance (tile coordinates from `tile_facts`). Large scale
  spread over the transport network dominates (Balcan et al. 2009), so the first
  increment can omit adjacency coupling and keep only route coupling.
- Policy is a multiplier on the flux owned by an actor (a state closing a port,
  a quarantine period). A multiplier changes the route flux and the
  `survival_in_transit` through enforced detention days; the disease engine only
  reads the resulting flux table.

### 2.4 Seasonality and climate

Each route may list `seasonal_drivers`: a driver (`temperature`, `rainfall`,
`absolute_humidity`, `harvest_season`, `gathering_season`) with a response curve
(for example a Briere-type or quadratic thermal response with minimum, optimum
and maximum). The weather model already supplies temperature (monthly
temperatures per climate class; real weather per tile is in the map and weather
design documents). Examples: malaria transmission responds nonlinearly to
temperature, with an optimum near 25 C and limits near 17 C and 34 C in the
Mordecai et al. (2013) synthesis, a much lower optimum than earlier linear models
assumed; cholera follows rainfall and water temperature (Codeco 2001: seasonal
variation of contact rates forces cyclical outbreaks); respiratory infections
follow humidity and crowding indoors in winter. The driver acts on vector density,
vector lifespan, extrinsic incubation and environmental survival, so the same
curve data covers a mosquito, a flea and a bacterium. A "vector climate envelope"
is just the region where the response curve is non-zero.

### 2.5 Density, urbanisation and crowding

Effective person to person contact per person scales sub-linearly with density:
`contact_rate = base_contact_rate * (density / reference_density) ^ density_exponent`
with the exponent between zero (frequency dependent) and one (pure mass action).
Empirical work on crowding finds scaling weaker than linear (Rader et al. 2020,
Nature Medicine, not re-checked here). The exponent lives in each route's data (a
vector route usually near zero, a respiratory route nearer one) and in tile data
as a settlement structure.

Historical cities killed more than they bred: the urban mortality penalty and the
"urban graveyard effect" (Woods 2003; Voigtlander and Voth 2013 model plague,
war and urbanisation jointly) is an emergent target: urban tiles with high density,
poor sanitation and constant immigration of susceptibles should carry a higher
endemic burden than the hinterland, and sustain a pathogen without reintroduction
(critical community size). A tile that is a city plus a hinterland has two
sub-populations with different density (Section 5 open question).

### 2.6 Nutrition, age and care

Case fatality is not a constant. For each infectious state the data gives a base
case fatality per age band, and the engine applies:

    case_fatality_of_band_in_tile =
        base_case_fatality_of_band
        * nutrition_severity_multiplier(nutrition_ratio, vulnerability_of_pathogen)
        * care_collapse_multiplier(share_of_working_adults_ill)
        * (1 - medical_care_relief_of_tile * efficacy_of_care_for_pathogen)

- The nutrition term reuses the demography module's
  `_excess_mortality_multiplier(nutrition_ratio, vulnerability)` so one function
  governs famine and epidemic mortality.
- The care collapse term is what separates a virgin population from a merely
  susceptible one. When most adults fall ill at once no one fetches water, feeds
  the sick, or tends the harvest, and deaths from dehydration, starvation and
  neglect rise. This is the mechanism Neel (1970) emphasised for the Yanomami
  measles epidemic (the "sociocultural" factors over strictly biological ones; the
  episode is controversial and should be treated as hypothesis), and it is why a
  slow-burn epidemic in a society with caregivers kills far fewer than a
  simultaneous one. It needs only the infected share of working age people and a
  declared sensitivity.
- Age patterns are data: for example measles falls most heavily on children in
  endemic settings, and in a first time epidemic hits adults too; this is a
  consequence of immune shares by age, not of the severity table.
- A sick working adult is also lost labour for the infectious and recovery period
  (reads `working_people` from the cohort and returns days lost).

## 3. A pathogen as data

### 3.1 File shape

One file per pathogen under `data/disease/` (new), validated by
`simulator.py validate`, with a `_SCHEMA.md` next to it like
`data/production/_SCHEMA.md`.

    id, name, tags                      free tags: "respiratory", "waterborne",
                                        "vector_borne", "zoonotic", "crowd"
    compartments                        host and reservoir states, per-state
                                        infectiousness and mortality hazard
    transitions                         [{from, to, rate | mean_duration +
                                        shape, probability for branching}]
    routes                              [{kind, transmissibility, density_exponent,
                                        carried_by, seasonal_drivers,
                                        sensitivities}]
    reservoirs                          [{kind, dynamics, climate_envelope,
                                        spillover_rate, home_tiles}]
    severity                            per band base case fatality, nutrition
                                        vulnerability, care sensitivity, labour
                                        days lost
    immunity                            {duration | permanent, cross_protection
                                        with other pathogen ids, maternal
                                        protection duration}
    sources                             citation per numeric field, and the
                                        sourced basic reproduction number range
                                        used by validate

`sensitivities` are the response of each route to tile state variables
(Section 4): for example `{"sanitation": exponent, "ectoparasite_habitat":
exponent, "water_safety": exponent}`. They are the only coupling between
content (techs, buildings) and pathogens, so a new pathogen reuses existing state
variables and a new state variable can be added without touching pathogens that
do not read it.

### 3.2 Candidate values from the literature

Values below are the sourced starting points for the data files. Tags: `read`
means the figure was read in a source actually opened (citation given);
`snippet` means seen only in a search result, source not opened; `recalled`
means standard literature not re-verified; `disputed` means sources disagree
(range given); "corrected" in a row means the earlier value was wrong and has
been replaced. Anything not `read` must be re-checked before it goes in
a data file (CLAUDE.md: every number in prose carries its provenance). Each data file
cites its source per field; ranges, not points, go in the `validate` check.

| Pathogen | Basic reproduction number | Latent / incubation, infectious | Case fatality (untreated, historical) | Immunity | Reservoir, vector, route | Status |
|---|---|---|---|---|---|---|
| Plague, bubonic | Depends on the vector route; Dean et al. (2018) fit a human ectoparasite model to nine European outbreaks better than pneumonic or rodent models (Park et al. 2018 dispute the inference; `read`: Dean et al. 2018, PMC5819418, the ectoparasite model had the lowest BIC for all outbreaks except Eyam and Givry, so "better" holds for seven of nine; ectoparasite R0 1.48 to 1.91 across the nine cities) | One to seven days incubation (`read`: WHO plague fact sheet) | Thirty to sixty percent for the bubonic type (`read`: WHO plague fact sheet) | Partial, duration poorly constrained (open) | Rodent and flea epizootic, human lice and fleas, goods and people carry vectors | `read` for WHO figures and Dean outbreak count; Park critique `read` second hand: Dean et al. 2018 reply, PNAS 115(34):E7894-E7895, PMC6112737, which summarises Park et al.'s three objections (a mixed pneumonic and rat-flea model is not excluded; omitted incubation periods and questioned priors; uncertainty possibly understated); Park et al.'s own letter not opened |
| Plague, pneumonic (secondary) | About 1.3 before control, variance about 3.1, geometric offspring distribution (`read`: Gani and Leach 2004, EID, PMC3323083) | Latent mean 4.3 days (SD 1.8) and infectious mean 2.5 days (SD 1.2), lognormal (`read`: same paper) | Close to 100 percent in the Gani and Leach review; always fatal untreated for pneumonic and septicaemic forms (`read`: WHO plague fact sheet) | n/a | Respiratory, only from a pneumonic case | `read` |
| Smallpox (variola major) | 3.5 to 6 in isolated pre-twentieth century populations with negligible herd immunity (`read`: Gani and Leach 2001, Nature, abstract via Europe PMC; the same abstract says earlier applied estimates ranged from 1.5 to above 20, so older estimates are `disputed`) | Incubation averages about 12 to 14 days, range 7 to 17 (corrected from "about 12"; `read`: CDC smallpox overview, stacks.cdc.gov/view/cdc/26503); contagious from fever onset, most from rash, until the last scab falls off (`read`: same CDC document) | About 30 percent overall; variola minor 1 percent or less (`read`: same CDC document) | Lifelong after recovery (`recalled`, not found in the CDC document and not found in a source on infection-derived immunity). Vaccination: antibody stable 1 to 75 years, T-cell half-life 8 to 15 years, over 90 percent of those vaccinated 25 to 75 years earlier kept humoral or cellular immunity (`read`: Hammarlund et al. 2003, Nature Medicine 9:1131, nm1273, abstract via CIDRAP summary https://www.cidrap.umn.edu/smallpox/protective-effect-smallpox-vaccine-may-last-decades and a search abstract; this is vaccinia, not variola) | Respiratory and fomites; no animal reservoir (`recalled`) | `read` except immunity duration after infection |
| Measles | Often cited 12 to 18, but estimates vary more widely than that range (`read`: Guerra et al. 2017, Lancet Infect Dis, abstract via Europe PMC; 58 estimates from 18 studies) | Incubation about two weeks (`read`: Hektoen International summary of Panum, secondary source); infectious from about four days before to four days after rash onset, rash about 14 days after exposure with a range of 7 to 21 (`summary`: CDC clinician measles materials and Pink Book chapter 13 as reported by search results, https://www.cdc.gov/vaccines/pubs/pinkbook/meas.html, page text not opened; incubation 10 to 12 days appears in a CDC slide deck, so the sources differ by a day or two) [filled 2026-10-09] | 2.8 percent in the 1846 Faroe epidemic, 6100 of 7864 residents infected, 170 deaths (`read`: Hektoen International summary of Panum, secondary source); higher with malnutrition and in first-contact outbreaks (`recalled`) | Lifelong (`read`: Panum 1846 via Hektoen, no reinfection after 65 years) | Respiratory; needs a population of the order of a few hundred thousand to persist (critical community size `disputed`, range 250 thousand to 1 million: Bartlett 1957 gives 250 to 300 thousand from England and Wales data, Black 1966 island data above 500 thousand, and appropriately parametrised models give 500 thousand to 1 million; `read`: Conlan, Rohani, Lloyd, Keeling and Grenfell 2009, J R Soc Interface, PMC2842776, which also says the value varies with birth rate and social structure; Bartlett and Black read second hand; Keeling and Grenfell 1997, Science 275:65, abstract only, defines the threshold without a number in the abstract; Ferrari et al. 2008 not opened) | `read` for Faroe and R0 range; critical community size `read` second hand, `disputed` |
| Cholera | 2.06 to 2.78 in the 2010 Haiti epidemic with mixed person and water routes (`read`: Tuite et al. 2011, Ann Intern Med, PDF opened: best fit about 2.78, plausible range 2.06 to 2.78; a recalibration to January 2011 data gave 2.90) | Median incubation 1.4 days (95 percent CI 1.3 to 1.6), 95 percent of cases by about 4.4 days (`read`: Azman et al. 2013, J Infect, systematic review, PMC3677557, abstract via Europe PMC); hours to five days (`read`: MSF clinical guidelines) | Up to 50 percent for untreated severe cholera; 1 percent or less when treated (`read`: MSF clinical guidelines; "below one percent" corrected to "1 percent or less") | Estimates range from a few months to 9 years; strong evidence of protection at 3 years in observational and challenge studies, while serological markers return to baseline within 1 year; subclinical infection protects less (`read`: Leung and Matrajt 2021, PLoS Negl Trop Dis, PMC8136710, abstract and text; corrected from "short, months to a few years"; `disputed`, range months to 9 years) | Water, aquatic reservoir, rainfall and temperature forced (Codeco 2001; Rinaldo, Bertuzzo and coworkers' spatially explicit hydrological network models of Haiti) | `read` for R0, incubation, fatality and immunity |
| Malaria (falciparum) | Estimates range from about one to over three thousand, a wide spread driven by mosquito biting rate (`read`: Smith et al. 2007, PLoS Biol 5:e42, PMC1802755, summary via Europe PMC: 121 African populations; the earlier link PMC3128496 was the wrong paper) | Mosquito extrinsic incubation temperature dependent; optimum transmission 25 C and a dramatic decline above 28 C (`read`: Mordecai et al. 2013, Ecol Lett, abstract via Europe PMC); the "17 to 34 C" limits are not in the abstract and stay `recalled` | Concentrated in young children; adults acquire partial immunity with exposure (`read` in part: Doolan, Dobano and Baird 2009, Clin Microbiol Rev, PMC2620631, first 100000 characters only; the Papua transmigrant data show an age-dependent pattern after 18 to 24 months of exposure; the review says the concentration in young children is not settled as exposure alone) | Partial, maintained by repeated exposure, lost without it (`read`: same review, "in the absence of continual exposure, the solid immunity against severe disease is apparently relatively short lived" and adults removed from exposure lose it at least temporarily); genetic resistance in endemic populations: sickle haemoglobin, Duffy negativity, G6PD deficiency, thalassaemia | Anopheles vector, human reservoir; entomological inoculation rate below one to above one thousand bites per person per year across Africa (`recalled`; not found in an opened source) | `read` for R0 range and optimum temperature; thermal limits and EIR range unverified |
| Epidemic typhus | Not sourced; a 2026-10-09 search found no published R0 for epidemic typhus, so the file must derive it from a louse model and carry no sourced R0 range (validate then checks only that the implied value is finite and above one for crowded louse-infested tiles). Louse becomes infective 2 to 6 days after an infected meal, patients infect lice during fever and perhaps 2 to 3 days after (`summary`: search result quoting a Public Health Agency of Canada pathogen safety data sheet, page not opened); derive from a louse model (the Dean et al. 2018 louse parameters are a starting point; `read`, PMC5819418: body louse carrying capacity 15 per person, louse infectious period 3 days, lice growth rate 0.11 per day, human flea transmission rate 0.05) | Louse borne, Rickettsia prowazekii | 10 to 30 percent of untreated clinical cases, higher in debilitated populations and the elderly, up to 60 percent or more reported in untreated cases in the elderly or debilitated (`read`: CFSPH typhus fact sheet, which summarises the literature; Raoult and Walker chapter not opened); "about 20 percent in healthy adults" is `snippet`: a search result states 20 percent in otherwise healthy individuals and 60 percent in the elderly or debilitated, but the Wikipedia Epidemic typhus page opened (first 100000 characters) gives only about 40 percent overall and 10 to 60 percent, so no opened source confirms it | Long, with recrudescent Brill-Zinsser disease (`read`: CFSPH typhus fact sheet, reactivation years after infection when immunity wanes) | Body louse; crowding, cold, cloth and war and famine drive it | `read` for fatality and recrudescence |
| Influenza (pandemic) | 1918 strain: median 2 (interquartile range 1.7 to 2.3) over 45 US cities from early data, 2.7 (2.3 to 3.4) over the period of fastest growth (`read`: Mills et al. 2004, PMC7095078; corrected: the earlier "1.9 to 4.1" were the assumed latent and infectious periods in days, not R); Biggerstaff et al. 2014 medians: 1918 1.80 (IQR 1.47 to 2.27), 1957 1.65, 1968 1.80, 2009 1.46, seasonal 1.28 (IQR 1.19 to 1.37) (`read`: abstract via Europe PMC; seasonal corrected from "close to one and a third"); 1918 is `disputed` between the two reviews, medians 1.8 to 2.7 | Mean latent period 1.9 days and infectious period 4.1 days (`read`: Mills et al. 2004, assumed values) | Strongly strain dependent; 1918 was far more lethal than other pandemics and age distinct (`recalled`) | Short to long, antigenic drift handled by waning to susceptible | Respiratory; humidity forced; animal reservoir spillover | `read` for R and periods |

Two points for the data design, from the table:

1. Plague is three transmission processes under one name (rodent epizootic,
   human ectoparasite, pneumonic). The composite structure of Section 2.2
   (routes plus a branching infectious state) represents it without engine code
   for plague. Which route carried the Black Death is a live scholarly dispute
   (Dean et al. 2018 versus Park et al. 2018 and the rodent tradition), so the
   plague file should ship the variants as parameter sets and let ensemble runs
   span them, consistent with CLAUDE.md 4.2.
2. Several rows have a wide or missing sourced range. That is the point of
   carrying ranges and an ensemble: the engine does not select the answer.

## 4. How technology acts

### 4.1 Principle

Tech nodes do not name pathogens, and pathogens do not name tech nodes (CLAUDE.md
4.7). Instead there is a small vocabulary of tile and institution state
variables that techs and buildings write to, and pathogen routes read through
`sensitivities`. Direct per pathogen effects exist only where the technology is
itself pathogen specific (a vaccine), and even then it targets a tag or
an id declared in the node's data, not engine branches.

### 4.2 Tile public health state (written by techs, buildings, actors)

Each is a derived value in the range zero to one, computed per tile as coverage
times quality of the relevant installed capacity, so the effect needs people,
materials and upkeep, not just a research flag (the node mechanics already
distinguish "knowledge" from "running concern"; see `requires_running` and the
closure residue):

- `sanitation`: clean water supply and waste removal (aqueducts, latrines,
  sewers, filtration, chlorination). Reduces environmental and fecal-oral routes
  and lice habitat through washing.
- `hygiene_and_laundry`: soap, boiled clothes, delousing. Reduces louse and
  flea routes.
- `vector_habitat`: standing water drained, marsh reclaimed, nets, screens.
  Reduces mosquito density.
- `quarantine_capacity`: lazarets, port inspection, isolation hospitals, a state
  able to enforce detention. Multiplies route flux and transit survival
  (Section 2.3), and isolates a share of infectious people at home.
- `medical_care`: nursing, rehydration, antibiotics, hospitals. Reduces case
  fatality per pathogen by an `efficacy_of_care_for_pathogen` the pathogen file
  declares (oral rehydration is very effective against cholera deaths, almost
  irrelevant to a smallpox death; antibiotics matter for plague and typhus).
- `housing_crowding` and `food_security`: read from the economy and from the
  nutrition ratio, not set by techs directly.
- `surveillance_and_knowledge`: the actor's knowledge of the cause (germ theory,
  statistical bills of mortality). Lets policy actors act earlier. It does not
  change the epidemic by itself.

### 4.3 Declaring effects on a node

Extend the existing node `mechanics` block (which already carries
`hazard_counters`) with a `disease_effects` list. Each entry sets a target and
an operation, and says how coverage is obtained:

    {
      "target": "tile_state.sanitation",         // or "pathogen:<id>" or "pathogen_tag:<tag>"
      "parameter": "water_supply_quality",        // or case_fatality, contact_rate,
                                                  // vector_density, susceptibility,
                                                  // infectious_period, route_flux
      "operation": "raise_toward",                // or multiply, add
      "value": ...,
      "coverage_from": "operating_capacity",      // from building/institution stock, not a flag
      "requires_running": ["..."]                 // same convention as hazard_counters
    }

Effects combine multiplicatively across nodes on the same parameter (as
`hazard_relief` combines shares today), with a floor from the physical minimum
(a pathogen never becomes more transmissible than its biology). This replaces the
`staff_loss` entries in `hazard_counters`; the test file
`test_plague_mitigation_realism.py` would be rewritten to assert the effects
through the model (a quarantined port delays the arrival date; a sanitation
build lowers an environmental route's reproduction number below one in the
affected tile), per CLAUDE.md section 6 TDD.

### 4.4 Vaccination, variolation and immunity

Immunising technologies move people between compartments, not scale a parameter:

- A vaccination program is an institution actor with a target pathogen or tag,
  a coverage per year (limited by doses, trained staff, cold chain or live
  arm to arm chains, and trust), an `efficacy` and a `duration_of_protection`.
  It moves a share of susceptibles of the targeted bands to `recovered_immune`
  (leaky or all-or-nothing as declared).
- Variolation (inoculation with live smallpox) is the same transition with a
  small fatality probability on the way, which makes it a risk trade off the
  actor can weigh rather than a flag.
- Vaccination coverage, plus the pathogen's reproduction number, then
  reproduces herd immunity as an emergent threshold (one minus one over the
  reproduction number), which is a validation target (Section 8).
- Antibiotics and antivirals act through `medical_care` and can also change
  infectious duration and transitions (a `parameter` such as
  `infectious_period` in the effect list).
- Pasteurisation, water chlorination and refrigeration act through
  `sanitation` and `food_security`; pesticides and insecticide nets through
  `vector_habitat`.

### 4.5 Knowledge is not capacity

Germ theory by itself should change what actors try, not the force of infection
on day one. This matches the existing `KNOWLEDGE_RESIDUE_AFTER_CLOSURE` idea, but
the residue stops being a flat 0.3: a closed hospital loses its capacity (state
variable decays), the knowledge stays, and re-opening costs less. Keep that
heuristic labelled until a decay model replaces it (CLAUDE.md 4.4).

## 5. Naive populations and immunity

### 5.1 Representation

Per tile, per pathogen id, per age band: the shares susceptible, in each infectious
state, and immune. Immunity is a state of the population, not a flag of the
civilisation. Births enter susceptible (after a maternal protection window if
declared), aging moves shares between bands (the existing `Population.step` ages
cohorts), waning moves immune shares back to susceptible, and deaths remove from
each state in proportion. An epidemic that kills mostly children leaves a
different immune structure from one that kills adults, and the model records
that.

### 5.2 Initial conditions are allowed; outcomes are not

CLAUDE.md 4.1 allows initial conditions: "what is already known". The initial
immune state of a civilisation is derived, not authored as a loss fraction: a
region data entry lists which pathogens are endemic there at the start date
(a set of ids, a physical fact about the world in the sense of geography). A
spin up step runs the endemic equilibrium for those pathogens (the analogue
of `Population.stationary`) so the age profile of immunity is consistent with the
reproduction number and the birth rate. Pathogens not listed start with zero
immune share. In 1500 the Mexica region lists the endemic set of the pre-contact
Americas; Old World diseases are absent from it. In Rome 100 AD the endemic set
includes measles-like childhood infections, malaria in marshy tiles and so on;
what each pathogen's file says about persistence (critical community size) then
decides whether it is truly endemic or reintroduced, and a validation test
checks that the declared endemic set is dynamically consistent.

This keeps scenario files free of epidemic sizes: they say who has met what, not
what happens next.

### 5.3 How the collapse emerges

For a pathogen entering a population with no immunity the engine produces, with
no special case:

- early exponential growth at the reproduction number, high because contact in a
  dense, travelling population meets no immune fraction;
- a large final size, close to the whole population for a high reproduction
  number pathogen (final size of a closed epidemic is determined by the
  reproduction number);
- high attack rates in all age bands (the age pattern of endemic measles
  disappears), so many adults are ill simultaneously and the care collapse
  multiplier raises case fatality, and harvest labour is lost, which feeds the
  nutrition ratio, which raises case fatality again (a feedback through existing
  demography and agriculture, not a script);
- successive waves of the same pathogen at intervals set by the time
  susceptibles are replenished by births, roughly the inter-epidemic period
  `2 * pi * sqrt(average_age_at_infection * (latent_period + infectious_period))`
  (`read`: Bauch and Earn 2003, Fields Institute Communications 36, equation 2.2, natural period of damped oscillations of the unforced SEIR model = 2 pi sqrt(mean age at infection * (1/latent rate + 1/recovery rate)), attributed there to Anderson and May; mean age at infection is about 1/(birth rate * (R0 - 1)); the paper notes rough agreement with observed intervals for most diseases except chickenpox and rubella; Anderson and May books not opened), with each wave
  smaller as the immune share stays high;
- different Old World pathogens arriving at different times (smallpox, measles,
  typhus, influenza, in any order the trade and seeding produce) so the declining
  population sees several different first contacts, which is why the
  long run decline is far larger than any one wave;
- a bounded total: the population ends where it does because the pathogen set has
  been exhausted for survivors, not because a data file ran out of years.

Historical scholarship says virgin-soil immunity is only part of the story:
Alchon (2003) and Jones (2003, "Virgin Soils Revisited") argue conquest violence,
forced labour, displacement and famine explain a large part of the decline;
Livi-Bacci (2006) lays out the contemporary and modern arguments for multiple
causes. This is consistent with the model above, where disease acts through
the same nutrition, labour and care channels that war and forced labour
act through: the decline is the product of all of them, which the mexica file's
separate "Spanish invasion" hazard can supply as ordinary state changes. The
model should therefore not need a "genetic susceptibility" parameter to produce a
catastrophe; if a scenario wants to test one, it is a labelled optional
`susceptibility_modifier` per population group (a hypothesis, tagged per
CLAUDE.md 4.4), off by default.

### 5.4 How a pathogen reaches a population

There is no wave chance per year. A pathogen is seeded by an event the
simulation produces or the scenario declares as initial conditions: an infected
traveller on a route (the flux of Section 2.3 reaching a tile with zero
infectious count, a stochastic import with probability proportional to the
infectious pressure), a spillover from a reservoir focus (rate by climate and
focus state), or a scenario-declared initial infection in a tile (an
intervention such as a founder arriving, or the player's or another actor's
action). An external region that is not simulated tile by tile (Eurasia while the
player is in the Americas) holds a coarse endemic compartment and exports
infectious travellers on its route to the simulated world at a rate set by its
own population and prevalence; the first contact between worlds is then the
first route flux that carries an infected traveller, not a dated trigger. This is
the one point where there is a real design choice about how much of the outside
world to simulate (open question 3).

## 6. Where it lives

### 6.1 New package `sim/disease/`

A sixth walled package under `docs/architecture/PACKAGE_WALLS.md`: `sim/disease/api.py`
is the only door and declares `WALL = "two-way"`; nothing inside imports
`sim.engine`, `sim.ui` or another package except through its `api`; the object
lives on `Sim` as `sim.disease` (built on first use, never saved; saved state stays
in `SimulationState`). What it needs from the engine comes through a `DiseaseWorld`
adapter in `sim/engine/disease_port.py` with one explicit member per input (people
by tile and band, nutrition ratio, route flux, tile public health state), no
`__getattr__` forwarding. It reads places and routes through `sim.geography.api`
only. Short files by topic, per CLAUDE.md section 5:

    sim/disease/api.py            the only import surface
    sim/disease/types.py          Pathogen, Compartments, TileDiseaseState, YearInputs, YearResult
    sim/disease/loader.py         reads data/disease/*.json, builds and validates reaction networks
    sim/disease/network.py        the next-generation matrix and reproduction number check
    sim/disease/force.py          force of infection by route kind
    sim/disease/coupling.py       route flux, transit survival, imports
    sim/disease/seasonal.py       driver response curves
    sim/disease/severity.py       case fatality by band, nutrition, care collapse
    sim/disease/immunity.py       aging, births, waning, vaccination transitions
    sim/disease/endemic.py        equilibrium spin up and mean field mode
    sim/disease/step.py           the sub-stepping loop
    data/disease/*.json           pathogens, with _SCHEMA.md and sources
    sim/engine/disease_port.py    DiseaseWorld: builds inputs from engine and economy, applies outputs

Demography (`sim/world/demography.py`) is still a standalone domain model under
`sim/world/`, so the disease package receives its cohort counts and nutrition
ratio as plain data through the adapter rather than importing it.

### 6.2 What it reads, what it returns

Inputs per year (a `YearInputs` record, plain data):

- from demography (through the adapter): the national people by age band, split to tiles by the settlement share (Section 11.4) [corrected 2026-10-09]; the `nutrition_ratio` (national today, per tile once agriculture reports it);
  births and deaths already computed (so there is no double counting);
- from `sim.geography.api`: tile facts (area, coastal, neighbours, climate class),
  per-tile layers (precipitation, forest), monthly temperature by climate class;
  density comes from people divided by land area;
- from the route and trade layers: the route table (origin tile, destination
  tile, days and mode from `route(...)`), persons per year and tonnes per year per route
  (derived from last year's trade flows and the military and migration actors);
- from the economy and tech: the tile public health state variables of Section
  4.2, derived from installed capacity and from the `disease_effects` of known
  nodes; actor policies as flux multipliers and vaccination programs;
- from scenario data: endemic sets per region, external focus records.

Outputs (`YearResult`):

- deaths by tile, band and pathogen (the demography module subtracts them from
  its cohorts; the accounting identity in `Population.step` must stay exact);
- labour days lost by tile (the agent economy lowers `working_people` supply
  for the year, and the existing labour market handles wages);
- the immune state, readable for the player interface and for fog of war (a
  founder with germ theory can see what a society cannot);
- for audit, `_internal` diagnostics: reproduction number realised, route
  arrival dates, final sizes (never player-facing text, per CLAUDE.md section 5).

### 6.3 Time step: yearly world, sub-yearly epidemic

The engine steps a year; epidemics unfold over days to months. Inside
`step_year` the disease package sub-steps with a length chosen per pathogen as a
fraction of its shortest compartment duration, clamped to a day and a week (an
explicit, labelled numerical heuristic, with a convergence test against a
finer step). Smallpox and plague with duration of days need weekly or finer
steps in the epidemic season; endemic malaria and immune dynamics need only a
monthly step. Seasonal forcing evaluates at the sub-step's month. Inside a year the
population is fixed except for disease deaths; births, aging and migration apply
at year end, after which the immune state is aged. This is the standard
operator splitting between slow demographic and fast epidemic processes.

Small numbers matter for two behaviours the model must get right, fade-out and
importation: when a tile's infectious count is below a threshold, switch from the
deterministic flow to a chain-binomial draw so an epidemic can die out, and
persistence requires a critical community size. The random draws come from a
per-package `random.Random` seeded once (the pattern in `Population`), so save,
load and the fingerprint tests reproduce byte for byte.

### 6.4 Performance on many tiles

- Only tiles with non-zero infection or a live reservoir are simulated in detail
  (an active set). A pathogen absent from the world costs nothing.
- Endemic equilibrium mode: when a pathogen is endemic and unperturbed in a
  tile (immune fraction near its equilibrium), keep a mean field update at yearly
  resolution (equilibrium susceptible fraction one over reproduction number, force
  of infection annual), and only switch to detailed sub-steps when a shock
  (a new strain, a migration surge, a famine, an intervention) leaves the
  equilibrium. This is how endemic malaria across a continent stays cheap.
- Coupling is a sparse edge list from the route graph, not an all pairs matrix.
  Cost per year is about active tiles times pathogens times bands times states
  times sub-steps, plus edges times sub-steps. State per tile and pathogen is a
  few dozen floats. The cost then scales with the epidemic front, not the map.
- Pathogen counts are small in any scenario (a dozen), so the pathogen axis is
  not the limit.

The package should ship a measurement: a `simulator.py` subcommand reporting
time per year and active-set size, no loose script (CLAUDE.md section 5).

### 6.5 Interaction with existing demography and hazards

- `disease_burden` in demography is a scalar from pre-industrial to modern.
  It scales baseline mortality and the fertility ceiling and was calibrated to
  total historical mortality, which already includes endemic disease. If
  `sim/disease/` also generated endemic deaths, they would be counted twice.
  Proposal: stage 1 keeps baseline mortality as is and the disease package
  adds only epidemic excess over baseline. A later stage derives baseline
  endemic mortality from the endemic pathogens (malaria, diarrhoeal, childhood
  infections) and replaces `disease_burden`, with a validation that life
  expectancy and age patterns still match (Section 8). Decision for the owner
  (open question 2).
- `staff_loss` hazards in civilisation files that stand for disease are
  deleted as the corresponding pathogen files arrive (for example "Old World
  epidemics on contact", the Antonine, Justinian, Black Death and 1665 entries).
  Their notes survive as documentation of the plausible record, not as inputs
  (CLAUDE.md 4.2: the record is a possible draw, never the script). War,
  famine, sack and output hazards remain as they are.
- The household founder's staff loss (`apply_staff_survival`) becomes a draw
  from the tile's realised age and class specific death rate in the disease
  result, so the founder is exposed like anyone else (general actors).

## 7. Validation

Validate against distributions and relationships over an ensemble of seeded
runs, never against a dated event (CLAUDE.md 4.2). Suggested checks, in test
form (`python3 -m sim.tests`, plus the slow tier for ensembles):

1. Unit properties of the engine, without data: population conserved apart from
   deaths; with zero reproduction number nothing spreads; final size of a closed
   epidemic agrees with the analytic final size relation for the declared
   reproduction number; the herd immunity threshold is one minus one over the
   reproduction number; the equilibrium susceptible share equals one over the
   reproduction number in an endemic mean field.
2. Next-generation matrix agrees with a long simulation of the same file; the
   implied reproduction number of every pathogen file lies within its sourced
   range (checked by `simulator.py validate`).
3. Recurrence: the inter-epidemic period of an endemic childhood infection in a
   large closed population matches the formula in 5.3 within a tolerance;
   persistence requires a tile (or connected set of tiles) above a critical
   community size, and fade-out occurs below it (measles critical community
   size of the order of a few hundred thousand, Bartlett 1957 and Ferrari et al.
   2008).
4. Pandemic mortality ranges: across ensemble runs, the share of population
   lost to a plague-like pandemic in a naive, dense, connected population
   falls within a published envelope, for example the scholarly range for the
   Black Death in Europe, from about a third or more to about three fifths
   (Benedictow's estimate is about 60 percent of Europe's population, about 50 million of about 80 million (`read`: reviewer's summary of The Black Death 1346-1353, michaeljournal.no, 2005, secondary source); the 65 percent in his later work, the traditional third and Aberth's half stay `snippet`: search results only; a search result also gives conventional opinion as 25 to 30 percent; `disputed`, range about a quarter to 65 percent),
   with high variance across seeds and dependence on region density and route
   access. Smallpox: untreated case fatality near the sourced value; attack
   rate and age pattern consistent with endemic versus first contact.
5. Virgin soil: the same pathogen introduced into a tile with zero immune share
   versus one with an equilibrium immune share produces several times the death
   toll, with adult mortality much higher in the former; the cumulative decline
   across the full pathogen set for a New World start falls in the range
   discussed in the literature (decline of the order of ninety percent over about a
   century is commonly cited, `read`: Koch, Brierley, Maslin and Lewis 2019, Quaternary Science Reviews 207:13-36, abstract via https://eprints.whiterose.ac.uk/id/eprint/154711/: European epidemics removed 90 percent (interquartile range 87 to 92 percent) of the indigenous population over the next century, from a pre-1492 population of 60.5 million (interquartile range 44.8 to 78.2 million); the abstract attributes it to epidemics, and the paper's own estimate carries that uncertainty; `read`: Livi-Bacci 2006 abstract argues against single-cause disease explanations and gives no single figure there), as a distribution over ensemble seeds, and the
   endpoint has to include the contribution of famine, forced labour and war the
   scenario applies, not disease alone.
6. Spatial: arrival time of an infection at a tile increases with route time
   from the source; ports and hubs are reached before inland tiles; a closed route
   (quarantine) delays but does not prevent arrival (a rank correlation test, not
   a date).
7. Seasonality: a vector route's incidence by month follows its declared thermal
   response; malaria transmission vanishes outside the thermal limits.
8. Endemic burden (stage 3): the life expectancy and child survival of a
   tile with and without malaria, with and without clean water, differ in the
   direction and rough size reported in historical demography (urban
   penalty, Woods 2003; Voigtlander and Voth 2013), evaluated as ranges.
9. Technology: raising `sanitation` lowers environmental route reproduction
   number monotonically; raising `medical_care` lowers case fatality for the
   pathogens whose files say care helps, and not for the ones whose files say
   it does not; vaccination coverage above the herd threshold stops spread.
10. No wave per year: in 100 ensemble runs, no pathogen recurs at full strength
    in consecutive years once immunity is high, and the 386 reproduction (a
    five million population Mexica game, seed 2) no longer collapses to a few
    hundred inside twenty years. The 386 evidence command stays the regression.
11. Determinism and save/load round trip, and `python3 -m sim.tests.fingerprint`
    checks for everything the disease package should not change in games where
    no pathogen is active.

## 8. Staged build plan

Smallest useful first, each stage independently shippable, each starts with a
regression test showing current behaviour (CLAUDE.md section 6).

Stage 0 (a day or two, no engine change): write the Complaint 386 reproduction
as a test of the current total over a window, and record how fast the
authored loss compounds. Add the `data/disease/_SCHEMA.md` draft.

Stage 1 (first increment): `sim/disease/` with one tile, no space, one pathogen
network, SEIR with the generic compartment loader, immune state by band, aging,
births, nutrition and care dependent case fatality, deterministic plus
chain-binomial at small counts, deaths by band returned to demography. Ship
smallpox and measles files (best sourced, respiratory person to person, no
vector). Replace the Mexica "Old World epidemics on contact" hazard with a
scenario seeding event and delete its `staff_loss`. [corrected 2026-10-09: a seeding event with a year
is a dated trigger, which CLAUDE.md 4.2 warns against. Declare it with `declare(..., kind="temporary_heuristic")`
so `python3 sim/constants.py --burndown` counts it, retire it in stage 2 when the outside world exports
infected travellers along routes, and delete the duplicate literal in `sim/engine/fog.py`.] Tests: items 1, 2, 3 and 5
of Section 7 for a single tile; the 386 reproduction passes.

Stage 2: spatial coupling over routes. Route flux from trade volumes and
route days, infection import, active set, quarantine multiplier from a state
actor. Test item 6. Seasonal drivers and the thermal curves. Add cholera
(environmental reservoir) as the first non person to person pathogen and
validate item 7.

Stage 3: vectors and reservoirs: plague (rodent focus, ectoparasite vector,
pneumonic branch), typhus, malaria (vector with temperature envelope and
partial immunity, genetic resistance as an immune carrier). Replace the Antonine,
Justinian, Black Death and later plague `staff_loss` hazards by seeding from
external foci. Ensemble tests, item 4.

Stage 4: technology effects. Define the tile public health state, add
`disease_effects` to the medicine nodes, retire the `staff_loss` entries from
`hazard_counters`, vaccination and variolation programs as actors. Rewrite
`test_plague_mitigation_realism.py` through the model. Item 9.

Stage 5: endemic burden. Derive baseline mortality from endemic pathogens,
retire the `disease_burden` scalar, validate item 8, measure with
`python3 sim/constants.py --burndown` that the declared heuristics fell.

Stage 6 (later): city plus hinterland subpopulations, adjacency coupling,
a coarse outside world model for the other players' regions.

## 9. Open questions for the owner

1. Plague mechanism: ship the human ectoparasite variant (Dean et al. 2018), the
   rodent variant, or both as ensemble variants? The model supports all three
   routes; the choice affects what technologies protect (delousing and clothing
   hygiene versus rat control).
2. Endemic disease: keep `disease_burden` and the existing calibration (stage 1
   to 4) and add only epidemic excess, or move to derived endemic mortality in
   stage 5? The second is more consistent with CLAUDE.md 4.1 and also the bigger
   change; double counting must be avoided in the meantime.
3. Outside world: how much of Eurasia and the Americas is simulated tile by tile
   when the player starts in one place? A coarse external compartment per world
   region exporting infectious travellers is cheap but is an authored boundary
   condition; full simulation is expensive. The contact event between worlds
   should come out of trade and exploration, not a date.
4. Resolution of settlement: is a tile one patch, or a city plus hinterland?
   Critical community size, urban graveyard effects and plague in cities depend on
   urban density, and the tile data may not have it.
5. Genetic or population specific susceptibility: default off (the literature
   attributes much of the New World decline to social factors, Alchon 2003;
   Jones 2003); do you want an optional labelled hypothesis switch for
   scenarios?
6. How much knowledge must the player have to see the disease? Fog of war
   currently hides hazards. An epidemic should be visible as deaths, but its cause,
   route and immunity state are knowledge a society without germ theory does not
   have. Which fields are public, and which require tech?
7. Vaccination and variolation as actor programs: who may run them (any state,
   the founder, a church), what do they cost in staff and goods, and does the
   player or an AI actor choose coverage? This follows the general-actor rule but
   needs an actor-policy decision.
8. Performance budget: how many tiles and what per-year time is acceptable with
   the agent economy on? The active-set and mean-field modes make the cost track
   the epidemic, but the budget decides the sub-step floor.
9. Ensemble expectations: the owner's note that history is a plausible draw
   needs a quantitative statement of acceptable spread. Section 7 proposes
   envelopes from the literature; who signs off the envelope per scenario?

## 10. Sources

Model methodology
- Hethcote, H. W. (2000), The mathematics of infectious diseases, SIAM Review.
  https://www.stat.cmu.edu/~kass/covid/HethcoteReview2000.pdf
- Keeling, M. J. and Rohani, P. (2008), Modeling Infectious Diseases in Humans and
  Animals, Princeton University Press. https://press.princeton.edu/isbn/9781400841035
- Anderson, R. M. and May, R. M. (1991), Infectious Diseases of Humans, Oxford
  University Press (inter-epidemic period, herd immunity; book not opened; the period formula is `read` in Bauch and Earn 2003, Fields Institute Communications 36).
- Balcan, D. et al. (2009), Multiscale mobility networks and the spatial spreading of
  infectious diseases, PNAS (GLEaM). https://pmc.ncbi.nlm.nih.gov/articles/PMC2793313/
  and the model description https://ifisc.uib-csic.es/jramasco/text/jocs10.html
- Viboud, C. et al. (2006), Synchrony, waves and spatial hierarchies in the spread of
  influenza, Science. https://ento.psu.edu/files/viboudetal2006.pdf
- Grenfell, B. T., Bjornstad, O. N. and Kappey, J. (2001), Travelling waves and
  spatial hierarchies in measles epidemics, Nature.
  https://ideas.repec.org/a/nat/nature/v414y2001i6865d10.1038_414716a.html
- Smith, D. L. et al. (2012), Ross, Macdonald, and a theory for the dynamics and
  control of mosquito-transmitted pathogens, PLoS Pathogens.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3320609
- Codeco, C. T. (2001), Endemic and epidemic dynamics of cholera: the role of the
  aquatic reservoir, BMC Infectious Diseases. https://pmc.ncbi.nlm.nih.gov/articles/PMC29087
- Rinaldo, Bertuzzo, Mari and coworkers, spatially explicit cholera models for Haiti
  (hydrological transport and human mobility on a network).
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4345467
- Bartlett (1957) critical community size; Ferrari et al. (2008), Nature, measles
  persistence (Ferrari: not opened; Bartlett: `read` second hand in Conlan et al. 2009, PMC2842776). Overview with references:
  https://en.wikipedia.org/wiki/Critical_community_size (secondary source only)
- Rader, B. et al. (2020), Crowding and the shape of COVID-19 epidemics, Nature
  Medicine (`read`: abstract via Europe PMC; crowded cities have longer, more spread epidemics and larger attack rates).

Pathogen parameters
- Dean, K. R. et al. (2018), Human ectoparasites and the spread of plague in Europe
  during the Second Pandemic, PNAS. https://pmc.ncbi.nlm.nih.gov/articles/PMC5819418
  (preprint https://www.biorxiv.org/content/10.1101/340547v2.full.pdf). Critique:
  Park, S. W. et al. (2018), PNAS, https://ms.mcmaster.ca/earn/pdfs/Park+2018_PNAS_PlagueEctoparasites.pdf
- Gani, R. and Leach, S. (2004), Epidemiologic determinants for modeling pneumonic
  plague outbreaks, Emerging Infectious Diseases. https://pmc.ncbi.nlm.nih.gov/articles/PMC3323083
- Schmid, B. V. et al. (2015), Climate-driven introduction of the Black Death and
  successive plague reintroductions into Europe, PNAS 112(10) 3020-3025, https://pmc.ncbi.nlm.nih.gov/articles/PMC4364181 (`read`: 7711 georeferenced outbreaks, 15 plus or minus 1 year lag between Asian climate fluctuation and European arrival).
- WHO, Plague fact sheet. https://who.int/news-room/fact-sheets/detail/plague
- Benedictow, O. J. (2021), The Complete History of the Black Death, Boydell.
  https://boydellandbrewer.com/?p=51131 ; overview of the range of estimates:
  https://www.historytoday.com/archive/black-death-greatest-catastrophe-ever
- Gani, R. and Leach, S. (2001), Transmission potential of smallpox in contemporary
  populations, Nature. https://www.nature.com/articles/414748a
- CDC, Smallpox disease overview (incubation, fatality):
  https://stacks.cdc.gov/view/cdc/26503/cdc_26503_DS1.pdf
- Guerra, F. M. et al. (2017), The basic reproduction number (R0) of measles: a
  systematic review, Lancet Infectious Diseases.
  https://em-consulte.com/article/1179164/the-basic-reproduction-number-r-0-of-measles-a-sys
- Panum, P. L. (1846), Faroe Islands measles; summary https://hekint.org/2021/08/18/peter-panum-and-the-geography-of-disease/
- Tuite, A. R. et al. (2011), Cholera epidemic in Haiti, 2010: using a transmission
  model to explain spatial spread, Annals of Internal Medicine.
  https://ms.mcmaster.ca/earn/pdfs/Tuit+2011_AIM_CholeraHaiti.pdf
- MSF Clinical guidelines, cholera clinical features:
  https://medicalguidelines.msf.org/en/viewport/CHOL/english/1-2-disease-presentation-and-clinical-course-23448679.html
- Mordecai, E. A. et al. (2013), Optimal temperature for malaria transmission is
  dramatically lower than previously predicted, Ecology Letters.
  https://pubs.usgs.gov/publication/70125667
- Smith, D. L. et al. (2007), Revisiting the basic reproductive number for malaria,
  PLoS Biology. https://pmc.ncbi.nlm.nih.gov/articles/PMC1802755 (R0 range; link corrected)
- Raoult, D. and Walker, D. H., Rickettsia prowazekii (epidemic typhus), in
  Principles and Practice of Infectious Diseases (fatality figures);
  summaries https://www.cfsph.iastate.edu/Factsheets/pdfs/typhus_fever.pdf
- Mills, C. E., Robins, J. M. and Lipsitch, M. (2004), Transmissibility of 1918
  pandemic influenza, Nature. https://pmc.ncbi.nlm.nih.gov/articles/PMC7095078
- Biggerstaff, M. et al. (2014), Estimates of the reproduction number for seasonal,
  pandemic, and zoonotic influenza, BMC Infectious Diseases.
  https://www.biomedcentral.com/1471-2334/14/480

Historical epidemiology and demography
- Alchon, S. A. (2003), A Pest in the Land: New World Epidemics in a Global
  Perspective, University of New Mexico Press. https://page158books.com/book/9780826328717
- Jones, D. S. (2003), Virgin soils revisited, William and Mary Quarterly 60(4).
  https://oieahc.wm.edu/publications/wmq/browse/volume-60-2003/october-2003/
- Livi-Bacci, M. (2006), The depopulation of Hispanic America after the Conquest,
  Population and Development Review 32(2). https://ideas.repec.org/a/bla/popdev/v32y2006i2p199-232.html
- Koch, A. et al. (2019), Earth system impacts of the European arrival and Great
  Dying in the Americas after 1492, Quaternary Science Reviews.
  https://discovery.ucl.ac.uk/id/eprint/10068488/
- Neel, J. V. et al. (1970), Notes on the effect of measles and measles vaccine in a
  virgin-soil population of South American Indians, American Journal of
  Epidemiology (controversial; cited as a hypothesis for care collapse).
- Woods, R. (2003), Urban-rural mortality differentials: an unresolved debate,
  Population and Development Review; Voigtlander, N. and Voth, H.-J. (2013), The
  three horsemen of riches: plague, war, and urbanization in early modern Europe,
  Review of Economic Studies. https://www.jvoth.com/papers/three-horsemen-of-riches.html

Items still marked recalled or snippet were not re-read during this research and must be checked
against the paper before a number goes into a data file.

## 11. Review pass 2026-10-09: what is build-ready

### 11.1 What this pass changed

Kept: the model family (Section 2), pathogen-as-data (Section 3), the technology vocabulary (Section 4),
the package layout (Section 6.1) and the staged plan (Section 8). They hold up against the code and the
owner's decision. Changed or added:

1. Section 1: the wave-chance constant lives in `sim/engine/society_hazards.py`
   (`STAFF_LOSS_HAZARD_ANNUAL_CHANCE`), with a duplicated literal in `sim/engine/fog.py`; the removal
   path of a cut is listed; the engine has one national `Population`, not per-tile ones.
2. Section 6.2: people by tile and band is derived, not supplied (11.4).
3. Section 3.2: measles infectious period filled (`summary`); a search for a typhus R0 found none, now stated.
4. Section 8 stage 1: the dated seeding event is labelled a temporary heuristic with a retirement stage.
5. New 11.2 (stepping inside a year), 11.3 (virgin-soil versus endemic parameters and modifiers),
   11.4 (hookup to this codebase), 11.5 (Americas validation range), 11.6 (first code step and test),
   11.7 (remaining gaps), and new sources at the end of Section 10 material (11.8).
6. Arithmetic behind the Complaint 386 collapse (11.5) so the baseline failure is explained, not just reported.

### 11.2 Stepping a year at sub-year resolution, cheaply

Recommendation: a discrete-time chain-binomial metapopulation, with one fixed step per pathogen,
not an ordinary differential equation solver and not an event-by-event simulation.

- Each transition out of a state with mean sojourn time `mean_duration_in_days` over a step of
  `step_length_in_days` fires for each person with probability
  `1 - exp(-step_length_in_days / mean_duration_in_days)`; infection fires with probability
  `1 - exp(-force_of_infection_per_day * step_length_in_days)`. The number moving is a binomial draw
  whose size is the count in the source state, so counts never go negative and never exceed the source.
  `recalled` (standard construction; Reed-Frost is the one-generation case, summary:
  https://en.wikipedia.org/wiki/Reed%E2%80%93Frost_model; the binomial tau-leap is Chatterjee, Vlachos
  and Katsoulakis 2005, named in https://en.wikipedia.org/wiki/Tau-leaping, paper not opened). The
  plain Poisson tau-leap can drive populations negative, which Cao, Gillespie and Petzold 2005 address
  (same Wikipedia page, `summary`); the binomial form avoids the problem by construction.
- Fitted measles work uses the same idea: the time-series SIR model of Finkenstadt and Grenfell 2000 is a
  discrete-time SEIR-type model fitted to biweekly case counts (`summary`:
  https://ideas.repec.org/a/bla/jorssc/v49y2000i2p187-205.html and the Bjornstad, Finkenstadt and
  Grenfell 2002 abstract, https://ento.psu.edu/research/labs/ottar-bjornstad/ottar-lab-abstracts/endemic-and-epidemic-dynamics-of-measles-i-estimating-transmission-rates-and-their-scaling-using-a-time-series-sir-model;
  the abstract states transmission rates scale with community size and seasonal terms, but gives no
  generation time or exponent, which I did not find). So a fixed step of about one generation is an
  established, validated pattern for exactly the measles case this game needs.
- Step length per pathogen: `step_length_in_days = clamp(shortest_mean_duration_in_days / divisor,
  1 day, 7 days)`. The divisor is a labelled numerical heuristic (CLAUDE.md 4.4), set by a convergence test
  (halve the step, final size and arrival time must agree within a tolerance) and printed by
  `python3 sim/constants.py --burndown`. Why a floor of a day: the shortest durations sourced in Section 3.2
  are cholera incubation (median 1.4 days) and the pneumonic plague infectious period (mean 2.5 days), both
  `read`. Slow processes (aging, births, waning, endemic malaria) run once a year at year end.
- Non-exponential durations (smallpox incubation 7 to 17 days, a bell-shaped period, not a decay) need a
  chain of equal exponential stages (Erlang approximation, `recalled`: Wearing, Rohani and Keeling 2005,
  PLoS Medicine, not opened): the data file gives `mean_duration` and `shape` (stage count), as Section 3.1
  already allows. Gani and Leach 2004 used lognormal periods for pneumonic plague (`read`), which a
  small stage chain approximates.
- Three tiers per tile and pathogen, so the cost tracks the epidemic, not the map (extends 6.4):
  (a) dormant: no infectious and no reservoir; cost is one import test per incoming route per step,
  `1 - exp(-imported_pressure * step_length_in_days)`; (b) epidemic: the stepping above, with chain-binomial
  draws, so small outbreaks can die out; (c) endemic mean field, once a year, only for pathogens the tile
  sustains. A tile drops from (b) to (a) when infectious and exposed counts reach zero, and a reservoir
  tile never drops below (c).
- Closed-form shortcut for a tile whose whole epidemic fits inside one step is not needed; use the
  final size relation below only as a test oracle and as the mean-field year update:
  `final_fraction_infected = 1 - initial_susceptible_fraction * exp(-reproduction_number * final_fraction_infected)`
  (closed SIR, standard; `recalled`, Hethcote 2000 and Keeling and Rohani 2008). Computed here by iterating the
  relation for a fully susceptible population: reproduction number 3.5 gives 0.966, 6 gives 0.9975, 15
  gives 1.0 to four places, 1.5 gives 0.583. These are mathematical consequences of the relation, not data.
- Determinism: draw from a per-package `random.Random` seeded once, in a fixed order (tiles sorted, then
  pathogens sorted, then states in file order), so save, load and fingerprint reproduce (CLAUDE.md 6).
  Hazard rolls on `Sim.rng` today are order sensitive (`_shocks` documents it), so the disease package
  must not draw from `Sim.rng`.

### 11.3 Parameters: virgin soil versus endemic, and what moves them

The mapping to data is: a transmissibility and durations (which give the reproduction number), a base case
fatality per age band, and modifiers. Never store "mortality of the epidemic". Section 3.2 has the table;
what this pass adds is the contrast and the modifiers.

Virgin-soil versus endemic. The difference is not a parameter of the pathogen; it is the immune share at
introduction (Section 5.1) plus the age at first infection:

| Pathogen | Endemic setting | First contact setting | Strength |
|---|---|---|---|
| Smallpox | Case fatality about 30 percent overall in variola major (`read`: CDC overview). R0 3.5 to 6 in isolated populations with negligible herd immunity (`read`: Gani and Leach 2001 abstract, matches a second search). Press coverage of the same paper says 10 to 12 can occur transiently in poor, crowded settings and hospitals (`summary`: CIDRAP, https://www.cidrap.umn.edu/measles/early-smallpox-outbreak-each-patient-could-infect-10-12-more) | Population mortality of the 1520 Mexican epidemic is `disputed`: McCaa's reassessment says the fraction lay between one tenth and one half of the population, "perhaps near the mid-point", and several times Europe's impact (`read`: https://users.pop.umn.edu/~rmccaa/vircatas/, page summary); Acuna-Soto et al. 2002 give 5 to 8 million deaths with no inline citation (`read`: https://wwwnc.cdc.gov/eid/article/8/4/01-0175_article). A university lecture page gives 80 to 90 percent case fatality in Native American epidemics; weak source, no primary data (`summary`: https://sites.pitt.edu/~super1/lecture/lec38681/022.htm), treat as an upper bound to test, not a parameter | Case fatality: `read`; first contact fatality: `disputed` |
| Measles | Faroe 1846: 2.8 percent of the infected died in a well-nourished, isolated, first-contact-in-65-years island (`read` second hand, Panum via Hektoen). Sub-Saharan endemic settings often 5 to 10 percent, developed countries under one in a thousand (`summary`: PLoS Medicine 2007 article found via search, https://www.plosmedicine.org/article/info:doi/10.1371/journal.pmed.0040024); a review of community studies reports a median case fatality of 0.039 and a range 0 to 0.40, and that most community-based studies found no link to nutritional status while hospital-based ones did (`summary`: https://pubmed.ncbi.nlm.nih.gov/19188207/) | Adults infected too, so the age pattern shifts (consequence of immune share, not a parameter). Care collapse (2.6) is the mechanism for excess | Mixed; the nutrition effect on measles fatality is contested, so the nutrition sensitivity in the measles file should be small and ensemble-varied |
| Plague | Reintroduced from foci rather than endemic in Europe (`read`: Schmid et al. 2015) | Black Death mortality is `disputed` between a quarter and 65 percent (Section 7 item 4) | `disputed` |
| Cholera, malaria, typhus | Immunity and recrudescence as in Section 3.2 | Not asserted; no source read for first-contact case fatality | open |

Modifiers (each is a multiplier or a transition in the pathogen file, with its own source and an ensemble
range; the engine has no per-disease code):

- Crowding and density: contact scales sublinearly with density (Rader et al. 2020, `read` abstract: crowded
  cities see longer epidemics with larger attack rates). The exponent per route is data. Measles
  persistence needs a large population (critical community size 250 thousand to 1 million, `disputed`,
  `read` in Conlan et al. 2009), which sets which tiles are reservoirs for which pathogens.
- Urban share: urban tiles use their own density; the tile layer must say how many people live on the city
  part (open question 4 still stands, and 11.4 notes the settlement module gives a capacity share per tile,
  not a city share).
- Nutrition: reuse `_excess_mortality_multiplier(nutrition_ratio, vulnerability)` from demography as in 2.6;
  the vulnerability is per pathogen data. Source strength is weak for infections (see measles above),
  so label the default heuristic and vary it across the ensemble.
- Sanitation: acts on environmental routes (cholera, Codeco 2001, `read` abstract) and on louse routes
  through washing; a tile state variable, 4.2.
- Quarantine: a flux multiplier plus detention days (2.3). Historical form: Ragusa's 1377 order of a month's
  isolation, later forty days for land travellers (`summary`: https://brewminate.com/the-concept-of-quarantine-in-history/
  and Gensini et al., https://library.alnap.org/system/files/content/resource/files/main/gensini%2C-g-the-concept-of-quarantine-in-history.pdf,
  neither opened); the sources I saw say effectiveness is unknown, so the model must derive it (detention days
  against incubation and infectious durations), and a test confirms detention shorter than the incubation does
  not prevent arrival.
- Variolation: Boston 1721 recorded about 2 to 2.5 percent deaths among about 240 to 300 inoculated against
  about 14 to 15 percent of naturally infected (844 deaths among 5759 infected of about 10600) (`summary`:
  https://en.wikipedia.org/wiki/1721_Boston_smallpox_outbreak, https://historyofvaccines.org/history/vaccine-timeline/timeline,
  https://www.jameslindlibrary.org/articles/zabdiel-boylstons-evaluation-of-inoculation-against-smallpox/).
  The groups were not randomised, so use the ratio only to check the direction and the order of the
  variolation transition's fatality (Section 4.4), not as the parameter.
- Vaccination: vaccinia immunity lasts decades (`read`, Hammarlund et al. 2003, Section 3.2).

### 11.4 How the model plugs into this codebase

Verified by reading the code on 2026-10-09; commands to re-verify are given.

Data it needs (a data file, never engine code, CLAUDE.md 4.7):

- `data/disease/<pathogen_id>.json` with a `_SCHEMA.md`, fields as Section 3.1. Add the loader check to
  `python3 sim/simulator.py validate`: schema, next-generation reproduction number inside the sourced range,
  compartments connected, every numeric field carries a source tag.
- Scenario data: per region the list of endemic pathogen ids (initial conditions, 5.2), and the external
  reservoirs. A civilisation file lists no epidemic sizes. Remove the "Old World epidemics on contact"
  `staff_loss` entry from `data/civilizations/mexica_1500.json` when stage 1 lands; keep the note as history.
- Technology: a `disease_effects` list on node `mechanics` beside `hazard_counters` (4.3). Check how
  `hazard_counters` nodes are read with `grep -rn hazard_counters sim data`.

State saved: the save file is the model (CLAUDE.md 5), fields detected automatically. The disease state is one
`DiseaseState` on `SimulationState`: per tile, per pathogen id, per age band, the counts in each compartment
(floats for tiers b and c, integers inside a step), the tier, the per-package random generator state, and
immunity by band. Exclusions only for derived caches. No migration shim (CLAUDE.md 4.6). A round-trip test
(save, load, continue) must equal a straight run.

Population is national, tiles are derived. Today `sim.population` is one `Population` (three bands). The
economy port derives tile people as national total times `settlement.population_share(held_tiles, tile)`
(`sim/engine/economy_port_setup.py`, `sim/engine/economy_port_year.py`, `sim/labour` `settlement_tiles()`),
a share of food-supported capacity. Consequences:

- Stage 1 treats the whole nation as one patch: no geography needed, `Population` bands in and deaths by
  band out. This is the smallest change that fixes Complaint 386.
- Stage 2 (spatial) needs a tile population. Two honest options: (a) assume the national age mix on every tile
  (a labelled heuristic: tiles do not own bands today) and apportion deaths back by the same shares, which
  keeps the accounting identity exact; (b) give `Population` a per-tile split, which is a demography change and
  belongs to its own plan. Pick (a) first.
- Deaths come back to the cohorts the agent economy already follows through the engine population (the
  complaint reports this link; the economy port reads `sim.population`, confirmed above). Do not cut cohorts
  from inside the disease package.

Contact through trade and geography, from the real surface (`sim/geography/INTERFACE.md`, `sim/geography/api.py`):

- Edges: `freight_links(modes)` returns `(tile_a, tile_b, mode, km)` for every edge a mode uses; `route(origins,
  destinations, modes, ..., fastest=True)` returns legs with `days`, and `fastest` is the people-travel
  option the contract describes ("how people travel, not goods"); `reach(origins, modes, days_budget)` gives
  tiles within a travel budget. So the days an infected traveller spends in transit come from geography, and
  the route modes come from `usable_modes`, which depends on technology held by the parties, so a ship tech
  node opens sea contact with no disease edits.
- Traveller volume does not exist yet. I grepped `sim` for traveller and per-route person counts and found none,
  and `sim/economy/api.py` exposes no flow table. The disease adapter must derive persons per year per edge
  from tonnes carried on that edge (the economy computes haul costs through `route_costs`; the tonnage
  per edge needs a new read-only member on the economy port) times a crew-and-merchant factor. That factor
  is a new labelled heuristic until a mechanism (crew hours per tonne-km from the freight data, which
  `sim/geography/freight_cost.py` already prices in labour hours) replaces it. Check: `grep -n labour_hours
  sim/geography/freight_cost.py`.
- A comparable empirical check exists for the gravity-type coupling: Boerner and Severgnini 2012 fit a
  gravity model to Black Death arrival times and report that speed depends on distance, political borders,
  rivers, sea and the importance of the city, with Florence-to-Bologna (about 110 km) within the same months
  and Florence-to-Siena (about 70 km) almost two months (`summary`: https://research.cbs.dk/en/publications/epidemic-trade/
  and https://www.medievalists.net/2012/09/epidemic-trade-2/, paper not opened). Use it for the rank-order
  test (Section 7 item 6), not as a speed to match.
- Geography does not read the tech tree; the caller passes held nodes. The disease adapter therefore builds
  `held_nodes` per party and passes it, as other callers do.

Technology to parameters: tile public health state (4.2) is computed by the adapter from installed capacity
and the `disease_effects` of the nodes the actor knows and runs (the `requires_running` convention); the
pathogen file's `sensitivities` read it. Existing mitigations (`germ_theory`, `med_quarantine_sanitation`,
`md2_vaccine_plague` in `sim/tests/test_plague_mitigation_realism.py`) migrate by turning their
`hazard_counters` into `disease_effects`. Until then the old `staff_loss` path stays for hazards not yet
replaced (famine, war), so the two systems can coexist during stages 1 to 3.

Sequencing within `step_year`: epidemic runs after agriculture sets the nutrition ratio and before
`Population.step`, so deaths are subtracted and demography's accounting identity (births, deaths,
aging) stays exact; the adapter passes the pre-step cohort counts and receives deaths by band. Do not
double count: stage 1 adds epidemic excess only over the baseline mortality (6.5).

### 11.5 Validation range for the Americas (a range for an ensemble, never a target)

Why the authored hazard fails, as arithmetic. The Mexica hazard declares a loss of 0.8 per wave, a wave chance
of 0.32 per year (the declared heuristic), over the years 1520 to 1600. Expected waves in 20 years: 0.32 times
20 = 6.4. Surviving share per wave is 0.2, so after 6.4 waves 0.2 to the power 6.4 is about 3.4e-5, and 5
million people become about 170, matching the complaint's "a few hundred". This is mine, derived from the
numbers in the complaint, `data/civilizations/mexica_1500.json` and `society_hazards.py`; it ignores the
technology relief and the re-growth between waves. The fault is structural: a wave has no memory of who is
immune.

What the record offers (all contested, which is the point):

| Source | Region and dates | Figures | Strength |
|---|---|---|---|
| McCaa's table of published estimates | Indian population of Mexico, 1519 to 1595 | Rosenblat 4.5 to 3.5 million (22 percent decline); Aguirre-Beltran 4.5 to 2.0 (56); Zambardino 5 to 10 to 1.1 to 1.7 (64 to 89); Mendizabal 8.2 to 2.4 (71); Cook and Simpson 10.5 to 2.1 to 3.0 (71 to 80); Cook and Borah 18 to 30 to 1.4 (78 to 95); Sanders (central Mexico, extrapolated) 2.6 to 3.1 to 0.4 (85 to 87); Whitmore (Valley of Mexico) 1.3 to 2.7 to 0.1 to 0.4 (69 to 96) | `read`: https://users.pop.umn.edu/~rmccaa/vircatas/virtab3.htm |
| Cook and Borah time series, central Mexico including Nueva Galicia | 1518 to 1605 | 25.2 million (1518), 16.8 (1532), 6.3 (1548), 2.65 (1568), 1.9 (1585), 1.375 (1595), 1.075 (1605). By the figures the 1605 value is 4.3 percent of 1518 (1.075 divided by 25.2); the source text says about 3 percent, an inconsistency I note without resolving | `summary`: search result quoting their volume's summary table, https://publishing.cdlib.org/ucpressebooks/public/book/essays-in-population-history-vol-iii-mexico-and-california.html, page not opened. Rosenblat accepted the base count (about 1.37 million) but rejected the adjustments to the 1548 figure (`summary`) |
| Acuna-Soto et al. 2002 | Mexican highlands | 1519 to 1520 smallpox 5 to 8 million deaths; 1545 cocoliztli 5 to 15 million deaths or up to 80 percent of the native population; 1576 an additional 2 to 2.5 million or about 50 percent of those remaining. Tree rings show a sustained megadrought, "the most severe and sustained drought to impact north central Mexico in the past 600 years"; the cocoliztli were not matched to a known Old World disease and the authors suggest an indigenous rodent-borne haemorrhagic fever. The population numbers are uncited inline. | `read`: https://wwwnc.cdc.gov/eid/article/8/4/01-0175_article. The rodent hypothesis is a hypothesis; the pathogen identity is not settled in what I read |
| Koch et al. 2019 | Whole Americas | 90 percent (IQR 87 to 92) decline over the next century from 60.5 million (IQR 44.8 to 78.2 million) before 1492 | `read` abstract, already in Section 7 item 5 |
| McCaa 1995 | 1520 smallpox in Mexico | Smallpox deaths between one tenth and one half of the population, probably near the middle; "several times" Europe's impact | `read`: summary page |

Validation envelope proposed (ensemble level, distributions; no dated event):

1. Long run: over 75 years after first contact, the ensemble median native-population decline for a Mexican
   start (disease plus the scenario's war, forced labour and famine hazards, which stay authored for now)
   lies inside the span of published estimates, that is between the lowest and highest rows of McCaa's table
   (22 to 96 percent), and the interquartile range of the ensemble overlaps the cluster of 64 to 95 percent.
   A simulator that always lands at one value is also wrong: the ensemble spread should be comparable to the
   spread among authors, since the same uncertainty (R0, first-contact fatality, social collapse) exists in the
   model inputs.
2. Short run (the Complaint 386 criterion): within 20 years of first contact no seed falls to near
   extinction. Cook and Borah's own maximalist series loses about a third of the people in the first 14 years
   and about three quarters in 30 (16.8 and 6.3 million against 25.2, my arithmetic on `summary` numbers), so
   an ensemble whose 20-year decline sits far above that series is out of range, and one far below is less
   alarming than the declared hazard but not forbidden. State the exact numerical gates in the test as
   ensemble quantiles from the sourced series; do not tune the model to hit them.
3. Multi-cause: disease alone must not be asked to produce the whole decline. Run ablations (disease only,
   disease plus labour demand shock, disease plus famine from lost harvest labour) and report the share of
   deaths by cause. Livi-Bacci 2006 and Jones 2003 argue multiple causes (`read` abstracts, Section 5.3).
4. Several pathogens in sequence: at least smallpox, measles, typhus and an influenza, in an order the contact
   structure produces. Waves of different pathogens should be able to arrive within the same decade (the
   record shows 1520, 1545 and 1576 as separate large events; the model need not reproduce those years).
5. Famine-and-drought coupling as an optional variant: the 1545 and 1576 events coincide with a megadrought
   (Acuna-Soto et al. 2002). A reservoir route driven by a rainfall seasonal driver (Section 2.4) with a rodent
   focus lets the ensemble include this hypothesis and its absence. Weather in the sim is the source of
   drought; the engine must not read a dated drought table.

The arithmetic check below also constrains the model: with only the sourced inputs, one first-contact smallpox
wave with reproduction number 3.5 to 6 infects 0.966 to 0.9975 of a fully susceptible closed population
(final size relation above) and, at the sourced overall case fatality of about 30 percent, kills about 29 to
30 percent. One wave cannot give nine tenths; several pathogens, care collapse and famine feedback are
required, which is the model's designed route to the century-scale decline (Section 5.3). If an ensemble
shows a 90 percent loss from smallpox alone, the case fatality inputs are over-tuned.

### 11.6 Minimal first code step and its regression test

Scope (stage 1, one patch, no geography). Nothing runs inside a whole game for the test; the test fixture is a
patch of plain numbers.

- `sim/disease/api.py` (with `WALL = "two-way"`, per Section 6.1), `sim/disease/network.py` (compartments
  and transitions as plain data, next-generation reproduction number), `sim/disease/step.py` (one chain-binomial
  step of one patch). `sim/disease/api.py` exports `Pathogen`, `Patch`, `step_patch`, `reproduction_number`.
  Data file `data/disease/smallpox.json` is not needed for the first test: the test builds the `Pathogen`
  from a literal dict, so data and engine are separable.
- Do not wire into `Sim` in this step. The adapter (`sim/engine/disease_port.py`) and the Complaint 386
  reproduction come next.

Test file `sim/tests/test_disease_patch.py`, `QUICK_TOPIC = True` (functions and a tiny fixture, one patch of
a few thousand people, a few hundred weekly steps; well under a second; the same unittest style as
`sim/tests/test_demography.py`). Properties, no outcomes:

1. Conservation: people in all compartments plus cumulative deaths equals the start every step.
2. No spread when reproduction number is below one: the infectious count dies out and the final infected
   share is small; with zero infectious people nothing happens.
3. Final size: with births and deaths off and all people susceptible, the mean final infected share over a
   modest number of seeds agrees with the closed final size relation for the declared reproduction number
   within a tolerance (reproduction number 3.5 gives 0.966 by the relation above; check by iterating, not by
   copying the number).
4. Step convergence: halving `step_length_in_days` changes the mean final size by less than the tolerance.
5. Memory (the Complaint 386 property, in miniature): with births on, introduce the same pathogen a second
   time soon after the first wave; the second wave's deaths are a small fraction of the first's, and the
   immune share is above the herd threshold `1 - 1 / reproduction_number`. This is the failing behaviour of the
   authored hazard, shown as a model property.
6. Determinism: same seed gives the same trajectory; a saved and restored `Patch` continues identically.
7. Virgin versus endemic: the same pathogen into a patch with an equilibrium immune share kills several times
   fewer people than into a naive patch (direction test, not a number).

Run: `python3 -m sim.tests --only disease_patch`, then `python3 -m sim.tests` and
`python3 -m sim.tests.fingerprint check before.json` (must be unchanged because nothing is wired). Per
CLAUDE.md 6, write the test first. Per CLAUDE.md section 1, name the branch for what it does, for example `disease-patch-model`.

Next steps after this: `disease_port.py` adapter and the `YearResult` (deaths by band into `Population`), the
Mexica scenario seeding as a labelled temporary heuristic, the 386 evidence command as an ensemble check
in the slow tier (not quick, it builds a whole game), then stage 2.

### 11.7 Gaps that remain after this pass

- Not found: a sourced R0 for epidemic typhus; first-contact case fatality for any Old World disease in an
  American population from a primary source (only reviews and secondary summaries were seen); immunity
  duration after smallpox infection (`recalled`); the generation-time and exponent values in the
  time-series SIR papers (abstracts give none); a traveller-volume mechanism in the repo.
- Opened only as search summaries: McCaa's body text beyond the pages cited, Cook and Borah's volume,
  Boerner and Severgnini, the 1721 Boston papers, the PLoS Medicine measles article, the Gensini quarantine paper.
  Re-read each before its number goes into a data file.
- Plague-route dispute (open question 1), endemic-burden double counting (open question 2) and the
  city-versus-hinterland structure (open question 4) are not settled by evidence found here; the code
  hookup above does not depend on them for stages 1 and 2.

### 11.8 Sources added in this pass

- McCaa, R., table of published estimates, Indian population of Mexico 1519 to 1595 (`read`):
  https://users.pop.umn.edu/~rmccaa/vircatas/virtab3.htm ; McCaa, R. (1995), Spanish and Nahuatl views on
  smallpox and demographic catastrophe in the conquest of Mexico, Journal of Interdisciplinary History
  (`read` summary page): https://users.pop.umn.edu/~rmccaa/vircatas/
- Acuna-Soto, R., Stahle, D. W., Cleaveland, M. K. and Therrell, M. D. (2002), Megadrought and megadeath in
  16th century Mexico, Emerging Infectious Diseases 8(4):360-362 (`read`):
  https://wwwnc.cdc.gov/eid/article/8/4/01-0175_article
- Cook, S. F. and Borah, W. (1960s to 1970s), Essays in Population History vol. III, University of California
  Press (`summary`): https://publishing.cdlib.org/ucpressebooks/public/book/essays-in-population-history-vol-iii-mexico-and-california.html
- Finkenstadt, B. F. and Grenfell, B. T. (2000), Time series modelling of childhood diseases, J R Stat Soc C
  49:187-205 (`summary`): https://ideas.repec.org/a/bla/jorssc/v49y2000i2p187-205.html ; Bjornstad, O. N.,
  Finkenstadt, B. F. and Grenfell, B. T. (2002), Dynamics of measles epidemics: estimating scaling of
  transmission rates using a time series SIR model, Ecological Monographs (`read` abstract):
  https://ento.psu.edu/research/labs/ottar-bjornstad/ottar-lab-abstracts/endemic-and-epidemic-dynamics-of-measles-i-estimating-transmission-rates-and-their-scaling-using-a-time-series-sir-model
- Chatterjee, A., Vlachos, D. G. and Katsoulakis, M. A. (2005), Binomial distribution based tau-leap
  accelerated stochastic simulation, J Chem Phys; Cao, Y., Gillespie, D. T. and Petzold, L. R. (2005),
  Avoiding negative populations in explicit Poisson tau-leaping, J Chem Phys (both named in
  https://en.wikipedia.org/wiki/Tau-leaping, `summary`, papers not opened)
- CDC, Measles (Pink Book chapter 13), https://www.cdc.gov/vaccines/pubs/pinkbook/meas.html (`summary`)
- Perry, R. T. and Halsey, N. A. (2004), The clinical significance of measles: a review, J Infect Dis 189:S4-16
  (named in a search result, not opened); measles case fatality review of community-based studies,
  https://pubmed.ncbi.nlm.nih.gov/19188207/ and PLoS Medicine 2007 (`summary`)
- Boerner, L. and Severgnini, B. (2012), Epidemic trade, EHES Working Paper 24 (`summary`):
  https://research.cbs.dk/en/publications/epidemic-trade/
- Gensini, G. F. et al., The concept of quarantine in history (`summary`, not opened):
  https://library.alnap.org/system/files/content/resource/files/main/gensini%2C-g-the-concept-of-quarantine-in-history.pdf
- 1721 Boston inoculation figures (`summary`, uncontrolled comparison): https://en.wikipedia.org/wiki/1721_Boston_smallpox_outbreak ,
  https://www.jameslindlibrary.org/articles/zabdiel-boylstons-evaluation-of-inoculation-against-smallpox/
- Gani, R. and Leach, S. (2001), re-checked via search abstract and CIDRAP coverage (`summary` for the
  10 to 12 transient figure): https://www.cidrap.umn.edu/measles/early-smallpox-outbreak-each-patient-could-infect-10-12-more
