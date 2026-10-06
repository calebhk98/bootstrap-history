# Transport and building demand: research and design (Complaint 434)

Branch `transport-and-building-demand-research`. Research only; no code or data changed.
Web search in this session returned snippets and abstracts, rarely full tables. Every figure below
is tagged `read` (seen in a snippet or page this session), `repo` (read from this repository) or
`recalled` (from memory, not re-checked; verify before it goes into data). Confidence letters
follow `data/production/_SCHEMA.md` (A well attested, B probable, C estimate, D guess).

## 1. What the repository does today

Measured with the command in the complaint (rome_100ad, non-farm need shares): miner, artisan and
furnaceman take most of the total; mason and carpenter are small but present; smith, potter,
scribe and glassblower follow. Sailor, plumber and millwright are absent, so they fall to
`NO_DEMAND_TRADE_SHARE`. The registry (`data/world/trades.json`) has no carter, teamster,
bargeman or bricklayer.

Findings from reading the code and data:

- Shelter already exists as a household need (`data/world/needs.json`, `shelter`, unit cubic metres
  of wall or frame). Its floor per person per year is computed in `sim/world/climate_needs.py`
  (`shelter_m3_per_year`) as structure volume divided by `STRUCTURE_SERVICE_LIFE_YEARS`. So the
  depreciation idea is already in the floor. The gap is what satisfies the need: `brick_1000`,
  `timber_m3`, `stone_blocks`, `cement_portland_kg` satisfy shelter directly as raw materials, so
  nobody ever lays them. The labour of putting a wall up is not demand for anyone.
- Mason and carpenter hours appear in only a handful of recipes across `data/production/`, and no
  recipe uses plumber hours, sailor hours or a carting trade.
- Freight is computed (`sim/geography/freight_cost.py`, `sea_freight.py`) from physical inputs: crew,
  crew hours per day at sea, cargo per hull, ground per day. The result is a money cost per
  tonne-km. It is a price, not a labour demand: nothing converts the crew hours of a traded tonne
  into demand for a trade, and the spin-up (`workforce_spinup.need_shares_by_trade`) never sees trade
  flows, only recipe levels.
- The spin-up's equal budget split is a labelled heuristic; this report does not change it. The
  design below needs nothing beyond the existing Leontief walk over recipes.

## 2. Evidence, by consumer of labour

### 2.1 Housing construction and repair

- A dwelling's structure is a stock that wears out and is repaired in pieces. Service life depends
  on material: earth, wattle and thatch need rebuilding or recovering within a few decades;
  fired-brick and mortared stone last centuries with roof and plaster repair between. Surviving
  cruck and timber-framed houses in the English Midlands date mostly from the later medieval
  period and stood for centuries ([cruck house summary](https://www.designingbuildings.co.uk/wiki/Cruck_house),
  read), which bounds the upper end for good frames. The repo's single `STRUCTURE_SERVICE_LIFE_YEARS`
  is graded D and should become per-material.
- Roman multi-storey housing mixed fired brick and concrete lower storeys with timber and mud brick
  above, and was repeatedly lost to fire and collapse ([overview](https://commonedge.org/high-density-living-2000-years-ago-inside-the-roman-apartment-building/),
  read). Upper-storey timber has a short life and a fire hazard, so it is a repair-demand source.
- Labour per unit built: DeLaine, *The Baths of Caracalla* (1997), tabulates labour constants by
  task and skill, and Bernard, *Building Mid-Republican Rome* (2018, Appendix One) costs ashlar tuff
  masonry in labour. Snippets confirm both exist and what they contain ([BMCR](https://bmcr.brynmawr.edu/1998/1998.11.41/),
  [Bernard review](https://www.ancientworldmagazine.com/reviews/building-mid-republican-rome-book-seth-bernard/),
  read) but not the per-cubic-metre constants. These are the primary sources to pull the table
  from. Salzman, *Building in England down to 1540*, is the medieval equivalent (accounts and day
  rates).
- Occupational evidence: the Ostian guild of beam-working carpenters, who also ran building firms,
  had more than three hundred members by the late second century ([Ostia associations](https://www.cambridge.org/core/books/abs/skilled-labour-and-professionalism-in-ancient-greece-and-rome/perception-of-skills-in-ostia-the-evidence-of-monuments-and-written-sources/C8E8EF72BBA7E82346252FDFA2C3B7F2),
  read). Packer's work on Ostian insulae estimates dwelling floor areas ([housing and population in
  Ostia and Rome](https://www.cambridge.org/core/journals/journal-of-roman-studies/article/housing-and-population-in-imperial-ostia-and-rome/87F332DE0438D675867DBD79DE36C924),
  read) and is the source for floor area per head in an imperial port city.

### 2.2 Urban water, drains, pipes

- Frontinus (97 AD) gives delivery and pipe standards: the unit pipe (quinaria) and the standard
  weights of lead pipe by calibre per ten-foot length ([Vitruvius 8.6.4](https://www.lexundria.com/vitr/8.6.4/mg),
  [Smith's Dictionary, Fistula](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/secondary/SMIGRA*/Fistula.html),
  read). Total delivery of the nine aqueducts is given in quinariae a day ([quinaria](https://penelope.uchicago.edu/~grout/encyclopaedia_romana/romanurbs/quinaria.html),
  read). Lead pipe is physical data: sheet width, mass per length, ten-foot lengths rolled and
  soldered. Plumber hours per metre laid are a recipe; metres of pipe per city follow from delivery
  and the number of connections.
- Pompeii's distribution (three main lines to water towers, then lead branches to fountains and
  houses; fountain flows estimated) is documented in the Lund and Northumbria theses ([Pompeii water
  system](https://www.avhandlingar.se/avhandling/41cf70818b/), read). These give pipes per connection,
  usable as a check on pipe metres per household.
- Wilson's papers on Roman water management (not retrievable this session) are the expected source
  for maintenance labour (cleaning sinter, repairing leaks, the aqueduct workforces Frontinus lists).
  `recalled` only.

### 2.3 Mills

- Barbegal: sixteen overshot wheels, estimated flour output of several tonnes a day, serving a town
  of some tens of thousands at the upper estimates ([overview](https://en.wikipedia.org/wiki/Barbegal_aqueduct_and_mills),
  read). Mill labour has two parts: build and repair of wheel and race (millwright, carpenter,
  mason), and the operating crew. The first is a depreciating capital stock, the second a recipe
  labour term that grain milling recipes already carry.
- The registry note that millwrights are scarce where water milling is absent is right. Demand for
  them should come from wear on mills that exist, which needs the capital stock to exist first
  (see 4.3).

### 2.4 Ships, crews, freight

- Merchant hulls: a typical Roman grain ship on the Rome route is put at a few hundred tonnes with
  large exceptions ([summary](https://weaponsandwarfare.com/?p=12258), [Isis](https://en.wikipedia.org/wiki/Isis_(ship)),
  read). Crew of about eight to ten for a hull of about a hundred tonnes (read, secondary; Casson,
  *Ships and Seamanship in the Ancient World*, is the primary to check). The repo already carries
  hull cargo and crew in `sea_freight.py` and they should be checked against these.
- Rome's imported grain is given as roughly 150,000 tonnes of Egyptian grain a year ([Roman grain
  trade](https://warhistory.org/article/the-roman-grain-trade), read), with larger totals for all
  sources; a figure of four hundred ships in a popular source should be treated as grade D.
  Erdkamp, *The Grain Market in the Roman Empire* (2005), is the scholarly source.
- Freight rates: Scheidel's ORBIS work on the Edict of Diocletian gives wagon haulage at roughly
  fifty times the per-tonne-km cost of sea haulage, with river in between ([Scheidel 2013, ORBIS
  prices](https://www.ancientportsantiques.com/wp-content/uploads/Documents/ETUDESarchivees/MedNavigationRoutes/ORBISprices-Scheidel2013.pdf);
  figures read through a search summary, the PDF text was not extractable). This is a validation
  relation for the freight mechanism, not an input.
- Port labour (stevedores, lightermen, bargemen on the Tiber, towing teams) is the part most often
  forgotten: cargoes were transferred to river craft and hauled upstream by animals or men
  ([annona summary](https://www.worldatlas.com/ancient-world/how-the-romans-supplied-a-city-of-a-million-people.html),
  read).

### 2.5 Occupational structure as distribution checks (not targets)

- England: male agriculture about half of employment in 1710 falling to about a third by 1817;
  secondary (manufacturing and construction together) rising from just over a third to over two
  fifths; tertiary (including transport and dealing) rising from about an eighth to nearly a fifth
  (Shaw-Taylor and Wrigley, via a search summary of the [Cambridge Group project](https://www.campop.geog.cam.ac.uk/research/occupations.171221/);
  the page itself returned 403). The project splits primary, secondary and tertiary with
  construction and transport as sub-branches, so their shares can be extracted from the published
  tables ([publication list](https://www.geog.cam.ac.uk/research/projects/occupations/publications/)).
  A persistently growing transport sector is stated in the abstract of the 1600 to 1850 thesis
  ([Cambridge repository](https://www.repository.cam.ac.uk/handle/1810/263608), read).
- Rome: Scheidel and Friesen (2009) give a small elite, a middling stratum and a large
  near-subsistence majority, and an income total; they do not give trade shares ([summary](https://onwork.edu.au/bibitem/2009-Scheidel,Walter-Friesen,Steven+J-The+Size+of+the+Economy+and+the+Distribution+of+Income+in+the+Roman+Empire),
  read). Trade counts come from inscriptions: Ostian and Pompeian associations (above) and, from
  memory, Joshel's *Work, Identity and Legal Status at Rome* (1992). Inscription counts are biased
  toward those who commemorated themselves, so use rank orders only.
- Han China: the four-occupations scheme is documented; no quantitative trade shares were found.
  Hsu, *Han Agriculture* (1980), and Bielenstein's census studies are the starting points. Any Han
  check will be at the level of farm share only; say so rather than invent more.

## 3. Table of physical figures

Items needing a source are not to be authored until their tag reads `read` against a primary source.

| Figure | Units | Source | Tag | Conf | Target file and field |
|---|---|---|---|---|---|
| Lead pipe, ten-quinaria pipe, one ten-foot length | 120 Roman pounds | Vitruvius 8.6.4 via [lexundria](https://www.lexundria.com/vitr/8.6.4/mg) | read | B | `data/production/20_nonferrous.json`, new entry `lead_pipe_m`: `unit_mass_kg`, `inputs.lead_kg` |
| Pipe sheet width equals circumference in digits; digit | 1.85 cm | [Smith's Dictionary](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/secondary/SMIGRA*/Fistula.html) via search | read | B | `yield_basis` of `lead_pipe_m` |
| Quinaria bore and area | 2.3 cm, 4.15 cm2 | [Encyclopaedia Romana](https://penelope.uchicago.edu/~grout/encyclopaedia_romana/romanurbs/quinaria.html) | read | A | `yield_basis` of `lead_pipe_m` |
| Aqueduct delivery, Rome, 97 AD | 14,018 quinariae per day | Frontinus, same page | read | B | test of water service level, not an input |
| Merchant hull cargo, Rome route | about 100 to 250 t | [summary](https://weaponsandwarfare.com/?p=12258) | read | C | check `MERCHANT_HULL_CARGO_TONNES` in `sim/geography/sea_freight.py` |
| Crew for a hull of about 100 t | 8 to 10 | search summary; Casson | read (secondary) | C | check `MERCHANT_HULL_CREW` |
| Egyptian grain to Rome | about 150,000 t per year | [summary](https://warhistory.org/article/the-roman-grain-trade) | read | C | validation of annona tonne-km, tests only |
| Wagon to sea freight cost ratio per kg-km | about 50 to 1 | Scheidel 2013 via search | read | C | validation relation in `sim/tests` |
| Wagon cost | 0.035 denarii per kg per km | same | read | C | validation only (CLAUDE.md 4.5: not a price input) |
| Sea cost | 0.00067 denarii per kg per km | same | read | C | validation only |
| Household size | 5 persons | `PERSONS_PER_HOUSEHOLD` (Laslett) | repo | C | already declared |
| Dwelling service life | 30 years, one value | `STRUCTURE_SERVICE_LIFE_YEARS` | repo | D | replace by per-material `service_life_years` |
| Ostian carpenters' guild | over 300 members, late 2nd century | [Cambridge chapter abstract](https://www.cambridge.org/core/books/abs/skilled-labour-and-professionalism-in-ancient-greece-and-rome/perception-of-skills-in-ostia-the-evidence-of-monuments-and-written-sources/C8E8EF72BBA7E82346252FDFA2C3B7F2) | read | C | distribution check, test only |
| England male shares (agriculture, secondary, tertiary) 1710 and 1817 | about 50, 37, 12 and 36, 44, 18 percent | Shaw-Taylor and Wrigley via search | read (secondary) | B | distribution check, test only |
| Labour per cubic metre by building task | person-days | DeLaine 1997; Bernard 2018 Appendix One | recalled (not retrieved) | to set | new building-service recipes in `data/production/`, `labour_hours` |
| Service lives by material (earth, timber, brick, stone) | years | needs a source (Salzman; Brunskill; Roman building studies) | not found | to set | `needs.json` goods or a new `service_life_years` field |
| Mill wheel and race wear, repair labour | hours per year per wheel | Wilson; Barbegal studies | not found | to set | upkeep recipe in `data/production/80_machines.json` |
| Lead pipe laid per connection, Pompeii | metres | Pompeii water studies | not found | to set | water service recipe |

Not authored, ever: any trade's share of the workforce, any city's plumber count, any ship count.

## 4. Recommended data design

Principle: every building and transport trade is demanded because some good or service consumes
its hours. Put the hours in recipes and the consumption in the existing need and recipe graph, so
`need_shares_by_trade` picks it up with no new mechanism.

### 4.1 Shelter as a stock with upkeep (building trades)

- Add installed-service goods, each a recipe output in the shelter family, for example wall or roof
  volume in place. Recipe inputs are the raw materials (brick, timber, stone, mortar, tile);
  `labour_hours` are mason, carpenter and labourer hours per cubic metre from the DeLaine and
  Bernard constants. Dimension `volume`, basis stated in words.
- Change the `needs.json` shelter goods so the satisfying good is the installed one, not the raw
  material. Brick and timber still satisfy shelter indirectly through the graph, and keep their
  other uses.
- Per-material service life: add `service_life_years` to a shelter good (or its recipe) and let the
  need floor use the mix's life instead of one constant. Replacement demand then depends on the
  material, so timber upper storeys cost more labour than brick. Until households choose the mix,
  the floor uses the available goods weighted as the budget split already weights them.
- Repair as a separate recipe: a yearly share of the stock (roof and plaster) needing carpenter and
  mason hours. The share comes from service life and material, not a typed value.

Files and fields: `data/world/needs.json` (shelter `satisfies` entries), `data/production/` (new
installed-service entries), `sim/world/climate_needs.py` (the constant becomes a per-good lookup).
`data/production/_SCHEMA.md` gains a documented optional `service_life_years`.

### 4.2 Transport as a service consumed per tonne-km (carters, sailors, bargemen)

- Add freight service goods: sea, river, cart and pack tonne-km. Each is a recipe whose
  `labour_hours` come from the physical inputs in `freight_cost.py` and `sea_freight.py` (crew per
  hull, crew hours per day at sea, cargo per hull, ground per day): hours per tonne-km is crew times
  crew hours per day, divided by cargo times km per day. One source of truth: the recipe field is
  generated from those constants, or a test asserts equality, so the two cannot drift.
- Recipes that move bulk goods gain an input of freight service equal to mass times a mean haul
  distance. The haul distance comes from geography (distance from producing to consuming regions,
  already computed in `sim/geography`), not a typed number. The spin-up has no trade flows, so it
  uses a geography-derived mean per good, tagged `[temporary_heuristic]` until the trade solver feeds
  flows back.
- The mode mix (sea, river, cart) is a cost choice. The existing equal split among producers
  applies and is already labelled. Cost ratios will emerge from the physical inputs, and the
  wagon to sea ratio is the validation test.
- Trades: decide whether `carter` and `bargeman` are new registry trades or whether carting stays
  in `labourer`; see open questions. Registry entries need training years and a hazard rate with a
  source.
- Ships and carts as capital: a hull or cart wears out, so a build and repair recipe consumes
  shipwright (carpenter) hours and timber, iron and cordage per hull-year. This is the bridge from
  freight to carpenter and rope demand.
- Port handling: a loading and unloading service per tonne with labourer hours (stevedores,
  lightermen), consumed once per transshipment.

Schema note: `unit_dimension` allows only `mass`, `volume`, `energy`, `area`, `length` and `count`,
so a tonne-km good needs either an extension (and the check in
`validate_production.check_unit_dimension`) or modelling as a `count` of loaded trips with stated
tonne-km per trip. Extension is cleaner.

### 4.3 Water supply and mills as capital with upkeep (plumber, millwright)

- A household `water` need with a floor per person (drinking, washing; physical data), satisfied by a
  delivered-water service good. Supply routes are recipes: carry from well or river by labour
  (always available), or pipe from a spring (needs laid `lead_pipe_m`, channel and arch masonry,
  plumber hours to lay and repair).
- A piped route has fixed capital (channel, pipe) and a flow, so it fits the recipe `capital`
  field. Upkeep is a recipe too: repair hours per year of capital, with a wear rate from physical
  causes (mineral deposit, root and frost damage), needing Wilson and Frontinus. Whether a city
  uses the pipe route is a result of cost against carrying by hand, not an authored list.
- Mills likewise: `capital` of a wheel and race, plus an upkeep recipe in millwright, carpenter
  and mason hours. Millwright demand then appears only where mills exist, matching the registry's
  note with no typed share.
- The water-works technologies named in the complaint (`cn_siphon`, `cn_water_main`,
  `ben_civic_water_works`) stay as `requires_node` gates.

### 4.4 What must not be authored

- Trade shares or counts of sailors, plumbers, millwrights, carters or masons. (Stating trades
  already established in a civilisation file is allowed by CLAUDE.md 4.1 as an initial condition,
  but is the second choice after demand.)
- A freight price or a pipe price. Prices fall out of wages, hull wear and lead cost.
- A haul distance per good, a mill count per city, or aqueduct and ship numbers from history as
  inputs; keep those as tests.

## 5. Staged build plan with tests

Stage 0 (no behaviour change): source the missing figures. Pull DeLaine labour constants, service
lives by material, lead pipe mass per length, Casson crew and tonnage. Output: the table above with
every tag at `read`. Test: `python3 sim/simulator.py validate` still passes.

Stage 1: pipe and building services.
- Add `lead_pipe_m`, a laid-pipe recipe with plumber hours, and installed wall and roof recipes with
  mason and carpenter hours.
- Tests (written first, CLAUDE.md section 6): plumber appears in `need_shares_by_trade` once a
  pipe-using node is reached and the water need exists; mason and carpenter shares rise against the
  current run and stay within the order of the Cambridge Group construction share, as a bound, not a
  target; every new recipe has `requires_node`; `validate`, `python3 -m sim.tests` and the
  fingerprint check show only intended changes.

Stage 2: shelter stock and upkeep.
- Per-material `service_life_years`; replacement and repair recipes; the shelter floor reads them.
- Tests: a timber-heavy mix needs more labour per household-year than a brick mix; doubling service
  life halves replacement hours; a civilisation without brick technology gets a timber and earth mix.

Stage 3: freight service labour.
- Tonne-km service recipes; a test asserts their labour hours equal those implied by
  `sea_freight_physical_inputs()` and the cart equivalent. Add the schema extension or `count`
  convention.
- Tests: sailor share is positive for a coastal civilisation with a traded bulk recipe and zero for
  an inland one without a river; the solved cost ordering is sea cheapest, river next, wagon
  dearest, as Scheidel's rates imply, checked as a relation.

Stage 4: ships and carts as capital, port handling, mills with upkeep.
- Tests: millwright share is positive only where a mill recipe is available and mills are in the
  starting capital; shipwright and cordage demand rise with sea freight volume.

Stage 5: retire `NO_DEMAND_TRADE_SHARE` for these trades and re-run the measure in Complaint 434.
Distribution checks (tests, not targets): building share and transport share within published
ranges for England; rank order of trades for Ostia; farm share only for Han China.

## 6. Open questions

1. Is carting a separate trade, or does it stay in `labourer`? Roman carters and bargemen are
   attested in inscriptions, but draught animals share the work, so animal feed belongs in the
   recipe either way.
2. Freight volume in the spin-up: it has no trade flows, so the mean haul per good needs a
   geography-derived estimate. Is a labelled first-pass heuristic acceptable, or must the spin-up
   take flows from the trade solver?
3. Schema: extend `unit_dimension` for tonne-km, or model trips as `count`?
4. The need budget is an equal split (labelled heuristic). New shelter and water goods take equal
   weight with other end goods until weights are derived. Acceptable at Stage 1, or does weight
   derivation come first so building shares are not an artefact of the heuristic?
5. Are dwellings a persistent per-region stock with decay in the simulation, or only a yearly flow?
   Only the first gives repair demand a real base; the second is the floor as it stands.
6. The family-median prior was rejected in the complaint because it gave Rome and the Mexica
   millwrights. The capital approach in 4.3 avoids that only if starting capital (mills, pipe) is an
   initial condition in the civilisation files. Which files would state it?
7. Sources not retrievable this session (full DeLaine, Bernard, Wilson, Casson, Erdkamp, and the
   Cambridge Group construction and transport tables) need a library pass before Stage 1 data is
   authored.
