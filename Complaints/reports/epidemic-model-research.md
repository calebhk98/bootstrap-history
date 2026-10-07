# Epidemic model: research and design proposal (for Complaint 386)

Status: research report, no code changed. Written for the owner's decision on Complaint 386.

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
  a wave per year in the window is a constant (see `sim/engine/fog.py`, grep
  `staff_loss_wave_chance_per_year`); each wave removes the authored share.
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
| Measles | Often cited 12 to 18, but estimates vary more widely than that range (`read`: Guerra et al. 2017, Lancet Infect Dis, abstract via Europe PMC; 58 estimates from 18 studies) | Incubation about two weeks (`read`: Hektoen International summary of Panum, secondary source); infectious period `recalled`, verify | 2.8 percent in the 1846 Faroe epidemic, 6100 of 7864 residents infected, 170 deaths (`read`: Hektoen International summary of Panum, secondary source); higher with malnutrition and in first-contact outbreaks (`recalled`) | Lifelong (`read`: Panum 1846 via Hektoen, no reinfection after 65 years) | Respiratory; needs a population of the order of a few hundred thousand to persist (critical community size `disputed`, range 250 thousand to 1 million: Bartlett 1957 gives 250 to 300 thousand from England and Wales data, Black 1966 island data above 500 thousand, and appropriately parametrised models give 500 thousand to 1 million; `read`: Conlan, Rohani, Lloyd, Keeling and Grenfell 2009, J R Soc Interface, PMC2842776, which also says the value varies with birth rate and social structure; Bartlett and Black read second hand; Keeling and Grenfell 1997, Science 275:65, abstract only, defines the threshold without a number in the abstract; Ferrari et al. 2008 not opened) | `read` for Faroe and R0 range; critical community size `read` second hand, `disputed` |
| Cholera | 2.06 to 2.78 in the 2010 Haiti epidemic with mixed person and water routes (`read`: Tuite et al. 2011, Ann Intern Med, PDF opened: best fit about 2.78, plausible range 2.06 to 2.78; a recalibration to January 2011 data gave 2.90) | Median incubation 1.4 days (95 percent CI 1.3 to 1.6), 95 percent of cases by about 4.4 days (`read`: Azman et al. 2013, J Infect, systematic review, PMC3677557, abstract via Europe PMC); hours to five days (`read`: MSF clinical guidelines) | Up to 50 percent for untreated severe cholera; 1 percent or less when treated (`read`: MSF clinical guidelines; "below one percent" corrected to "1 percent or less") | Estimates range from a few months to 9 years; strong evidence of protection at 3 years in observational and challenge studies, while serological markers return to baseline within 1 year; subclinical infection protects less (`read`: Leung and Matrajt 2021, PLoS Negl Trop Dis, PMC8136710, abstract and text; corrected from "short, months to a few years"; `disputed`, range months to 9 years) | Water, aquatic reservoir, rainfall and temperature forced (Codeco 2001; Rinaldo, Bertuzzo and coworkers' spatially explicit hydrological network models of Haiti) | `read` for R0, incubation, fatality and immunity |
| Malaria (falciparum) | Estimates range from about one to over three thousand, a wide spread driven by mosquito biting rate (`read`: Smith et al. 2007, PLoS Biol 5:e42, PMC1802755, summary via Europe PMC: 121 African populations; the earlier link PMC3128496 was the wrong paper) | Mosquito extrinsic incubation temperature dependent; optimum transmission 25 C and a dramatic decline above 28 C (`read`: Mordecai et al. 2013, Ecol Lett, abstract via Europe PMC); the "17 to 34 C" limits are not in the abstract and stay `recalled` | Concentrated in young children; adults acquire partial immunity with exposure (`read` in part: Doolan, Dobano and Baird 2009, Clin Microbiol Rev, PMC2620631, first 100000 characters only; the Papua transmigrant data show an age-dependent pattern after 18 to 24 months of exposure; the review says the concentration in young children is not settled as exposure alone) | Partial, maintained by repeated exposure, lost without it (`read`: same review, "in the absence of continual exposure, the solid immunity against severe disease is apparently relatively short lived" and adults removed from exposure lose it at least temporarily); genetic resistance in endemic populations: sickle haemoglobin, Duffy negativity, G6PD deficiency, thalassaemia | Anopheles vector, human reservoir; entomological inoculation rate below one to above one thousand bites per person per year across Africa (`recalled`; not found in an opened source) | `read` for R0 range and optimum temperature; thermal limits and EIR range unverified |
| Epidemic typhus | Not sourced; derive from a louse model (the Dean et al. 2018 louse parameters are a starting point; `read`, PMC5819418: body louse carrying capacity 15 per person, louse infectious period 3 days, lice growth rate 0.11 per day, human flea transmission rate 0.05) | Louse borne, Rickettsia prowazekii | 10 to 30 percent of untreated clinical cases, higher in debilitated populations and the elderly, up to 60 percent or more reported in untreated cases in the elderly or debilitated (`read`: CFSPH typhus fact sheet, which summarises the literature; Raoult and Walker chapter not opened); "about 20 percent in healthy adults" is `snippet`: a search result states 20 percent in otherwise healthy individuals and 60 percent in the elderly or debilitated, but the Wikipedia Epidemic typhus page opened (first 100000 characters) gives only about 40 percent overall and 10 to 60 percent, so no opened source confirms it | Long, with recrudescent Brill-Zinsser disease (`read`: CFSPH typhus fact sheet, reactivation years after infection when immunity wanes) | Body louse; crowding, cold, cloth and war and famine drive it | `read` for fatality and recrudescence |
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

- from demography (through the adapter): people by tile and age band; the `nutrition_ratio` by tile;
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
scenario seeding event and delete its `staff_loss`. Tests: items 1, 2, 3 and 5
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
