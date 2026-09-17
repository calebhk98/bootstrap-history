# Generative Historical Simulation Architecture

**Status:** Architectural design / review document  
**Primary implementation:** Python, CLI-first  
**Primary use case:** Counterfactual and alternate-history simulation with endogenous outcomes  
**Initial temporal resolution:** 1 year, with optional event/substep resolution inside a year

---

## 1. Purpose

The simulator should answer questions of the form:

- What happens if a knowledgeable immortal appears in an ancient society?
- How rapidly can a society climb toward modern technological capability if it receives unusually good information?
- What happens if a state spends much more on research without knowing in advance which research paths are useful?
- How do multiple unusually capable or informed people change the trajectory?
- What happens under arbitrary interventions such as new resources, technologies, populations, disasters, institutions, or military capabilities?
- If no intervention occurs, does the simulated world remain broadly compatible with known historical development?

The simulator should **not** reproduce history by replaying hardcoded historical outcomes. Historical data may initialize and validate the model, but simulated outcomes should emerge from lower-level constraints and interactions.

The central design objective is therefore:

> **Historical data initializes and validates the world. It does not dictate what happens next.**

---

# 2. Core Design Principles

## 2.1 Endogenous outcomes

Quantities that can reasonably emerge from the simulated world should be calculated rather than prescribed.

Examples:

- wages
- prices
- soldier compensation
- city size
- food availability
- migration
- production
- trade volume
- army size
- government revenue
- technological adoption
- research output
- industrial capacity
- wealth distribution
- settlement growth
- military effectiveness

A Roman soldier should not cost a fixed historical number because "that is what a Roman soldier cost." Soldier compensation should emerge from labor supply, military labor demand, alternative employment, provisioning, recruitment institutions, risk, expected loot, coercion, state finances, and local prices.

Likewise, a city should not have a fixed maximum population because history says so. Population should be constrained by food, water, sanitation, mortality, housing, transport, trade access, political stability, and economic opportunity.

## 2.2 Minimal primitives, not zero primitives

A simulation cannot derive reality from nothing.

Some inputs must ultimately be treated as primitive or externally supplied:

- geography
- physical laws
- biological constraints
- material properties
- approximate human caloric requirements
- crop characteristics
- resource deposits
- starting populations
- starting technologies and institutions
- starting infrastructure

The rule should be:

> **Hardcode or import fundamental constraints and initial conditions; do not hardcode the historical consequences that should arise from them.**

This distinction is critical.

## 2.3 Shared world state

Domains must not behave like separate minigames with duplicated state.

The same farmer exists simultaneously as:

- a person
- a worker
- a consumer
- a household member
- a taxpayer
- a possible soldier
- a disease host
- a migrant
- a source of knowledge and skills
- a participant in institutions

The same iron stock can be demanded by:

- farms
- construction
- armies
- workshops
- transport
- mining
- tool production

If the army consumes more iron, that iron must stop being available somewhere else.

## 2.4 Stocks, flows, processes, and constraints

Whenever possible, model the world using:

- **Stocks** — things that exist at a point in time.
- **Flows** — things moving or changing over time.
- **Processes** — transformations of stocks and flows.
- **Constraints** — requirements that limit processes.
- **Agents / organizations** — actors making decisions.
- **Networks** — structures connecting actors and places.

This is preferable to arbitrary modifiers because it gives interventions natural pathways through the simulation.

## 2.5 Knowledge is not capability

Knowing how to build something and being able to build it are separate states.

A modern technical database may give an ancient society:

- designs
- theory
- target materials
- process descriptions
- known failure modes

It does not automatically give them:

- precision machine tools
- pure chemicals
- suitable alloys
- gauges
- skilled labor
- factories
- supply chains
- electrical power
- standardized parts
- tacit craftsmanship

The simulator must preserve this separation.

## 2.6 Capabilities matter more than "tech levels"

Technology should not primarily be represented as a single linear technology level or ordinary game-style tech tree.

Instead, production should depend on a graph of required:

- knowledge
- skills
- materials
- tools
- infrastructure
- energy
- precision
- organization
- scale

The important concept is the society's **capability frontier**: the set of things it can reliably produce, operate, maintain, and scale under current conditions.

## 2.7 Interventions propagate through normal rules

Special scenarios should not require special-case outcome code.

Examples:

- An immortal with Wikipedia is an agent with unusual knowledge access and lifespan.
- A rich research state has increased resources available to research and perhaps different institutions.
- A new gold deposit is a new resource stock at a location.
- Dragons are new agents/species with physical requirements, behavior, damage potential, and perhaps economic uses.
- Modern firearms are physical objects with specific capabilities and supply requirements.

The intervention changes the world state. Existing systems should determine the consequences.

---

# 3. Common World State

All domains should operate on a shared underlying representation.

| Fundamental object | Examples |
|---|---|
| **Agents** | people, households, rulers, merchants, craftsmen, researchers, soldiers |
| **Organizations** | states, armies, firms, guilds, temples, universities, religious institutions |
| **Places** | settlements, farms, mines, ports, regions, roads, river crossings |
| **Physical stocks** | people, grain, iron, gold, timber, buildings, weapons, tools, machines |
| **Knowledge stocks** | techniques, theories, designs, recipes, procedures, literacy |
| **Capabilities** | smelting quality, machining precision, shipbuilding, administration, surgery |
| **Flows** | goods, migration, money, information, disease, military forces |
| **Networks** | trade, roads, rivers, political ties, communication, social connections |
| **Processes** | farming, mining, manufacturing, teaching, research, construction, warfare |
| **Institutions** | property, taxation, slavery, conscription, contracts, inheritance, guild rules |

These should not necessarily all be represented at individual-person resolution. Aggregation is acceptable where it preserves the causal behavior needed by the model.

---

# 4. Domain Architecture

The following domains overlap with the earlier lists but are reorganized to reduce duplication and clarify ownership.

---

## 4.1 Geography and Terrain

### Owns

- coordinates and spatial relationships
- elevation
- slope
- coastlines
- rivers and watersheds
- navigability
- natural harbors
- soil regions
- arable land
- biome/ecological regions
- travel distances
- geographic barriers

### Does not own

- actual agricultural output
- trade volume
- settlement population
- resource prices

Those should emerge from other domains using geographic constraints.

### Major interactions

- constrains transport and trade
- determines access to water
- influences agriculture
- affects military movement
- constrains settlement location
- affects communication speed
- determines practical access to resources

### Example

Coal 300 km away by navigable river is economically different from coal 300 km away across mountains even if the geological stock is identical.

---

## 4.2 Environment and Climate

### Owns

- temperature patterns
- precipitation
- seasonal variation
- drought
- floods
- storms
- long-run climate trends
- ecosystem productivity
- environmental degradation where modeled

### Major interactions

- agriculture
- water supply
- disease ecology
- migration
- settlement
- transport
- disasters
- military campaigning

### Resolution

Daily weather is unnecessary initially. Annual or seasonal environmental states are probably sufficient, with exceptional events represented separately.

---

## 4.3 Resources and Raw Materials

### Owns

- resource deposits
- deposit size
- ore grade
- extraction difficulty
- depletion
- renewable resource regeneration
- timber
- metals
- stone
- clay
- salts
- coal
- oil
- sulfur
- nitrates
- natural fibers
- other industrial inputs

### Major interactions

- mining and extraction labor
- transport
- industry
- military supply
- construction
- energy
- trade
- prices

A resource existing geographically does not imply that society can identify, extract, refine, transport, or profitably use it.

---

## 4.4 Energy

### Owns

Energy sources and usable conversion pathways:

- human labor
- animal power
- biomass
- water power
- wind
- coal
- steam
- petroleum
- electricity
- other sources where relevant

### Major interactions

Energy constrains:

- production scale
- mining
- metallurgy
- transport
- agriculture
- urbanization
- manufacturing
- communication
- military logistics

Energy should normally be represented physically enough that machines require appropriate power availability rather than simply receiving a productivity bonus.

---

## 4.5 Population and Demography

### Owns

- births
- deaths
- age structure
- sex structure where relevant
- household formation
- dependency ratios
- population growth
- mortality causes
- population distribution

### Closely related but separate

Migration is generated jointly by demography, economy, conflict, environment, and settlement.

### Major interactions

Population provides:

- workers
- consumers
- soldiers
- researchers
- administrators
- taxpayers

Population also generates demand for:

- food
- housing
- sanitation
- clothing
- transport
- services

---

## 4.6 Health and Disease

### Owns

- disease prevalence
- transmission
- immunity where needed
- epidemics
- endemic disease
- injury burden
- health interventions
- mortality and morbidity effects

### Major interactions

- population
- labor supply
- urbanization
- armies
- migration
- trade
- sanitation
- nutrition
- knowledge
- medical production

Disease should not just be a random population penalty. Conditions such as density, mobility, sanitation, immunity, nutrition, and contact networks should influence it.

---

## 4.7 Agriculture and Food

### Owns processes for

- planting
- cultivation
- harvesting
- livestock
- fishing where important
- food preservation
- storage
- spoilage
- food processing

### Inputs

- land
- water
- labor
- animals
- tools
- seeds
- fertilizer
- energy
- knowledge
- climate

### Outputs

- food
- animal products
- fibers
- feed
- agricultural byproducts

### Major interactions

Agricultural surplus is one of the main constraints on:

- urbanization
- specialization
- armies
- research
- administration
- construction

The model should calculate actual food availability and distribution rather than assigning a generic agricultural productivity value.

---

## 4.8 Human Capital, Skills, and Education

### Owns

- literacy
- numeracy
- craft skill
- professional expertise
- apprenticeship
- schooling
- training capacity
- skill acquisition
- skill decay or loss
- distribution of expertise

### Important distinction

A population of one million does not imply one million interchangeable workers.

A precision machinist, farmer, physician, accountant, metallurgist, and untrained laborer provide different capabilities.

### Major interactions

- production
- research
- administration
- military effectiveness
- education
- technological diffusion
- organizational capacity

---

## 4.9 Knowledge, Science, and Technology

### Owns

- concepts
- theories
- designs
- known processes
- empirical observations
- experimental knowledge
- explicit knowledge
- discovered relationships
- research questions
- technology diffusion

### Explicit vs tacit knowledge

**Explicit knowledge** can be communicated in text, diagrams, equations, or instructions.

**Tacit knowledge** depends on practice, experience, craftsmanship, and learned judgment.

A database may almost instantly provide explicit knowledge but cannot instantly create tacit skill.

### Research

Research should involve:

- choosing problems
- allocating people/resources
- experimentation
- uncertainty
- failure
- observation
- communication
- replication
- combination of existing knowledge

A society with more research funding but no knowledge of the future should search the knowledge space faster, not simply purchase predetermined technologies.

---

## 4.10 Production Capability and Manufacturing

### Owns

What can actually be produced, at what:

- precision
- quality
- volume
- reliability
- repeatability
- cost

### Represents

- workshop capability
- manufacturing processes
- metallurgy
- chemical processing
- machining
- assembly
- quality control
- standardization

### Critical rule

A known design is manufacturable only if all required production capabilities and inputs are available.

Example:

A firearm may require:

- appropriate steel
- barrel boring/rifling
- springs
- precision fits
- ammunition
- propellant
- primers
- gauges
- repeatable machining

Each requirement recursively depends on other capabilities.

---

## 4.11 Tools, Infrastructure, and Capital Stock

### Owns physical productive assets

- hand tools
- machine tools
- furnaces
- mills
- presses
- pumps
- workshops
- factories
- laboratories
- warehouses
- roads
- bridges
- canals
- ports
- ships
- railways
- power plants
- communication infrastructure

### Major interactions

Capital stock enables processes but:

- takes resources to create
- requires maintenance
- depreciates
- can be destroyed
- may require skilled operators
- can itself require other capital goods to manufacture

Existing tools enable better tools. This recursive accumulation is central to industrial development.

---

## 4.12 Economy, Markets, and Allocation

### Owns

- production decisions
- consumption
- exchange
- prices
- wages
- rents
- profits
- wealth
- labor allocation
- resource allocation
- scarcity
- substitution
- household budgets
- firm/organization budgets

### Core requirement

Prices should emerge from actual scarcity, supply, demand, transport costs, institutions, information, and bargaining rather than from historical price tables.

Historical prices may be used for validation.

### Important behavior

If the army hires more blacksmiths:

- blacksmith wages may rise
- civilian metalworking capacity falls
- tool prices may rise
- farm tool availability may change
- agricultural output may change
- food prices may change

That chain should occur because the same scarce workers and materials participate in all sectors.

---

## 4.13 Finance and Capital

### Owns

- money
- credit
- debt
- lending
- investment
- savings
- state borrowing
- financial intermediation
- liquidity
- capital ownership

### Major interactions

- production expansion
- research funding
- state capacity
- construction
- warfare
- trade
- entrepreneurship

A giant gold discovery should affect the system through extraction, ownership, money supply, trade, demand, labor allocation, taxation, and prices rather than by applying a generic "wealth bonus."

---

## 4.14 Trade, Transport, and Logistics

### Owns

- movement of goods
- movement capacity
- shipping
- caravans
- roads
- rivers
- canals
- ports
- rail
- storage
- handling
- travel time
- transport losses
- transport cost
- military supply chains

### Major interactions

Transport turns geographically local scarcity into regional or global markets.

The delivered cost of a good should incorporate the actual logistics required to move it.

### Military importance

Armies should consume:

- food
- animals/fuel
- ammunition
- equipment
- replacement parts
- transport capacity

Operational reach should therefore be constrained by logistics rather than only troop count.

---

## 4.15 Settlement and Urbanization

### Owns

- settlement locations
- housing
- density
- land use
- city growth
- rural/urban distribution
- local infrastructure
- sanitation capacity

### City growth should depend on

- employment opportunities
- food import capacity
- water
- mortality
- transport links
- housing
- security
- political status
- trade access

A city population should emerge from these conditions rather than from a fixed historical trajectory.

---

## 4.16 Communication and Information Networks

### Owns

- message transmission
- information travel time
- postal systems
- messengers
- printing
- telegraph
- radio
- record keeping
- information reliability
- network reach

### Major interactions

Communication affects:

- government coordination
- military command
- trade
- research diffusion
- education
- markets
- diplomacy
- culture
- organizational scale

Information should have a location and transmission cost unless the scenario explicitly removes that constraint.

---

## 4.17 Social Structure, Culture, Religion, and Incentives

### Owns or represents

- social status
- class/caste
- family norms
- trust
- identity
- religion
- language
- prestige
- social networks
- occupational status
- cultural transmission
- norms affecting behavior

### Important caution

Avoid generic variables such as "innovation resistance" when behavior can instead be explained through incentives, institutions, interests, risk, status, or information.

Culture can matter strongly without becoming an arbitrary civilization modifier.

---

## 4.18 Institutions, Law, and Governance

### Owns

- property systems
- contracts
- inheritance
- taxation
- bureaucracy
- courts
- conscription
- slavery/forced labor where historically relevant
- guild systems
- regulation
- political offices
- administrative capacity
- state legitimacy
- enforcement

### Major interactions

Institutions determine what organizations can coordinate, extract, enforce, and finance.

A technically possible 10,000-person project may still fail if no organization can:

- raise funds
- recruit labor
- enforce contracts
- acquire land
- coordinate supply
- maintain records
- protect the project

---

## 4.19 Politics and Diplomacy

### Owns

- rulers and political actors
- factions
- coalitions
- succession
- state relations
- treaties
- alliances
- tribute
- sanctions
- diplomatic information
- political competition
- rebellion
- legitimacy contests

### Major interactions

- institutions
- economy
- military
- culture
- communication
- taxation
- trade
- succession and inheritance

Politics should react to material changes.

A new technology that makes one group extraordinarily wealthy or militarily powerful should alter political incentives and coalitions.

---

## 4.20 War and Security

### Owns

- military organizations
- recruitment
- training
- doctrine
- command
- campaigns
- battles
- sieges
- occupation
- casualties
- conquest
- security provision
- military learning

### Military capability depends on

- manpower
- weapons
- training
- morale
- doctrine
- command
- communication
- logistics
- transport
- terrain
- fortifications
- health
- finance
- production
- replacement rates

### Firearms example

Giving Rome modern firearms must not translate into a single strength multiplier.

The simulation should separately consider:

- number of weapons
- ammunition stock
- ammunition production
- maintenance
- training
- tactical adaptation
- supply
- capture
- reverse engineering
- enemy response
- production scalability

This allows 100 rifles, 100,000 rifles, and local rifle production to produce radically different outcomes.

---

# 5. Cross-Domain Interaction Map

The model should make these interactions explicit.

## 5.1 Food loop

Geography + climate + land + labor + tools + knowledge  
→ agricultural production  
→ food availability and price  
→ nutrition and mortality  
→ population and labor supply  
→ wages and labor allocation  
→ agricultural labor and investment

## 5.2 Industrialization loop

Knowledge  
→ improved production process  
→ requires tools/materials/skills/energy  
→ capital investment  
→ increased output or precision  
→ cheaper/better capital goods  
→ expanded production capability  
→ new feasible technologies

## 5.3 Urbanization loop

Agricultural surplus + transport  
→ food available to cities  
→ specialization and market density  
→ productivity and knowledge exchange  
→ urban employment  
→ migration  
→ greater density  
→ disease/sanitation pressure  
→ mortality and infrastructure investment

## 5.4 State capacity loop

Economic surplus  
→ taxable activity  
→ state revenue  
→ bureaucracy/infrastructure/security  
→ improved enforcement and trade conditions  
→ greater economic activity  
→ larger taxable base

This can also reverse if extraction becomes destructive.

## 5.5 Military-industrial loop

Security threat  
→ military demand  
→ taxes/borrowing  
→ demand for labor, weapons, animals, metals, transport  
→ industrial expansion or civilian crowding-out  
→ battlefield capability  
→ conquest/loss/security change  
→ new resources, population, obligations, and threats

## 5.6 Research loop

Surplus + institutions + human capital  
→ researchers and experimentation  
→ new knowledge  
→ new production possibilities  
→ productivity / military / health / transport changes  
→ new surplus  
→ further research capacity

## 5.7 Information loop

Communication infrastructure  
→ faster information diffusion  
→ improved market coordination / administration / research  
→ greater organizational scale  
→ more demand and resources for communication infrastructure

## 5.8 Disease loop

Population density + mobility + pathogen ecology  
→ transmission  
→ illness/mortality  
→ reduced labor and military capability  
→ migration / social response / institutional response  
→ altered contact patterns

## 5.9 Resource-price loop

Demand for material  
→ extraction effort  
→ depletion / discovery / investment  
→ supply  
→ price  
→ substitution and technology choice  
→ future demand

---

# 6. Technology Representation

## 6.1 Use a dependency graph, not a simple tech tree

Each technology/process/product should describe requirements such as:

- prerequisite knowledge
- required skills
- materials
- material quality
- tools
- tool precision
- energy
- infrastructure
- environmental conditions
- organizational requirements
- minimum practical scale

A product becomes feasible only when its requirements can be satisfied.

## 6.2 Example: firearm production

A modern firearm might require:

**Weapon**
- barrel
- receiver
- springs
- fasteners
- sights
- stock/grip
- ammunition

**Barrel**
- appropriate steel
- boring
- rifling
- heat treatment
- dimensional measurement

**Cartridge**
- brass/case material
- drawing/forming
- projectile
- propellant
- primer

**Primer**
- suitable chemistry
- purification
- safe manufacturing
- consistent small-scale dosing

This dependency chain eventually reaches capabilities already possessed by the society.

That boundary is the current capability frontier.

## 6.3 Operation, maintenance, replication, and scaling are separate

For any introduced technology, track at least:

1. **Can use**
2. **Can maintain**
3. **Can repair**
4. **Can reproduce components**
5. **Can reproduce complete system**
6. **Can mass-produce**
7. **Can improve**

These stages should not be collapsed into one boolean.

---

# 7. Research Representation

Research should not be "spend points to unlock technology."

Possible conceptual structure:

**Research effort**
- researchers
- skill
- equipment
- materials
- funding
- time
- communication

acts on:

**Problem space**
- known problems
- hypotheses
- observations
- unexplained failures
- adjacent techniques

producing probabilistically:

- failed experiment
- useful observation
- new empirical relationship
- improved technique
- theoretical insight
- reproducible design
- new research question

## Immortal/database scenario

The intervention mainly changes:

- explicit knowledge available to one or more agents
- ability to identify promising research paths
- ability to diagnose failures
- ability to skip already-solved conceptual discoveries

It does not automatically change:

- physical capital
- workforce skill
- available materials
- production precision
- state capacity
- energy
- logistics

## Wealthy-country research scenario

The intervention mainly changes:

- number of researchers
- research equipment
- experimental throughput
- ability to fund failures
- breadth of simultaneous search

The society must still discover which research directions are useful.

---

# 8. Agent and Organization Representation

Do not assume every human requires an individually simulated object.

Use the lowest resolution necessary for causal fidelity.

Possible layers:

## Individual agents

Use for actors whose identity matters:

- rulers
- inventors
- immortal intervention agents
- senior commanders
- major merchants
- researchers
- political leaders

## Cohorts

Use for large populations:

- age cohort
- occupation
- skill group
- region
- household class
- wealth group

## Organizations

Represent collective actors directly:

- states
- armies
- firms
- guilds
- universities
- religious institutions

Organizations should own assets, employ people, make decisions, and interact with institutions.

This hybrid approach avoids simulating millions of unnecessary individual objects while retaining meaningful agency.

---

# 9. Time Model

## 9.1 Base timestep

Initial target:

**1 simulation year**

This is reasonable for:

- population
- agriculture
- investment
- education
- research
- construction
- broad economic change
- migration
- institutional change

## 9.2 Events and substeps

Some phenomena operate faster and should be allowed internal resolution:

- battles
- military campaigns
- epidemics
- political coups
- market crises
- disasters
- sieges
- harvest failures

The main simulation can remain yearly while event systems internally resolve shorter processes.

## 9.3 Suggested yearly order

Avoid making this a rigid permanent sequence, but an initial annual cycle could be:

1. update environmental conditions
2. agricultural production
3. extraction and raw materials
4. production
5. trade/logistics
6. consumption
7. prices and labor allocation
8. finance/investment
9. public finance/governance
10. research/education/knowledge diffusion
11. health/disease
12. demographic update
13. migration/settlement changes
14. politics/diplomacy
15. conflict/security
16. capital depreciation/construction completion
17. statistics/invariant checks

Where circular dependencies matter, systems may require iteration or staged decision/update passes rather than one irreversible call.

---

# 10. What Should Be Exogenous vs Endogenous?

## Usually exogenous or initialized externally

- terrain
- underlying geology
- basic physical constants
- baseline climate forcing
- material properties
- biological species properties
- initial population
- initial stocks
- initial knowledge
- initial infrastructure
- initial political borders
- initial institutions

## Usually endogenous

- prices
- wages
- employment
- output
- wealth
- trade
- migration
- city growth
- tax revenue
- army size
- military spending
- adoption of technology
- industrial capacity
- research direction
- resource extraction
- infrastructure investment
- state capacity
- literacy growth
- political stability
- diplomatic relations

The exact boundary may move as the model becomes more detailed.

---

# 11. Testing Strategy

A simulation like this can appear convincing while being fundamentally wrong. Testing must therefore go beyond "does it run?" and "does the output look historical?"

Use several different classes of tests.

---

## 11.1 Software unit tests

Test ordinary code behavior:

- serialization/deserialization
- inventory operations
- market transactions
- graph traversal
- route calculation
- births/deaths
- production recipes
- resource depletion
- technology requirement checks
- event scheduling
- random seed reproducibility

These catch implementation bugs but not model-design errors.

---

## 11.2 Conservation and accounting invariants

These are among the most valuable tests.

Examples:

### Material conservation

If 100 kg of iron enters a process, the outputs plus waste/loss must account for it.

The simulation should not create iron because two systems each believed they owned the same stock.

### Population accounting

Starting population  
+ births  
+ immigration  
- deaths  
- emigration  
= ending population

### Money / balance-sheet accounting

Depending on the monetary design, transfers should not arbitrarily create or destroy financial claims.

### Land accounting

Allocated land cannot exceed physically available land.

### Labor accounting

A worker cannot simultaneously provide a full year of labor to a farm, army, and workshop.

### Time/capacity accounting

A machine cannot produce more than its physical capacity unless the model explains overtime, parallel equipment, or changed process efficiency.

These invariants should run automatically every simulated year.

---

## 11.3 Directional sanity tests

Change one cause and verify the model usually moves in the expected direction, while allowing secondary effects.

Examples:

- Increase accessible food with everything else unchanged → famine mortality should usually fall.
- Destroy a road → delivered prices along dependent routes should usually rise.
- Add skilled machinists → precision manufacturing capacity should not fall for no reason.
- Increase labor demand with fixed labor supply → wages should generally face upward pressure.
- Reduce mortality → long-run population should generally increase unless counteracted elsewhere.
- Add a nearby ore deposit → local extraction should become more attractive than a distant equivalent deposit.

These are not tests for exact numerical answers. They test causal direction.

---

## 11.4 Counterfactual metamorphic tests

A metamorphic test asks whether transforming the input produces a logically related transformation in the output.

Examples:

### Population scaling

Clone a region's population while also proportionally cloning its land, capital, resources, and infrastructure.

Many per-capita outcomes should remain approximately similar.

If wages collapse merely because the population integer doubled, something is probably wrong.

### Currency denomination

Rename or rescale currency units.

Real outcomes should not change merely because 1 old unit becomes 100 new units.

### Entity renaming

Rename Rome to "City A."

Nothing should change.

This catches accidental historical-name special cases.

### Geographic translation

Move an otherwise identical synthetic test region without changing physical properties.

Results should remain identical unless latitude, neighbors, climate, etc. are intentionally position-dependent.

### Duplicate agents

Two identical workers should behave like two workers, not unlock a special threshold tied to identity.

---

## 11.5 Anti-hardcoding tests

Create deliberately absurd worlds.

Examples:

- Rome with ten times the population
- Rome with one tenth the population
- giant gold deposit beneath Rome
- no Mediterranean iron deposits
- unusually cheap transport
- no horses
- doubled human lifespan
- modern rifles with no ammunition manufacturing capability
- abundant coal but no steam-engine knowledge
- steam-engine knowledge but no suitable metallurgy
- perfect literacy but no paper/printing
- dragons consuming livestock
- a region with modern machine tools but no trained operators

The model should produce different consequences through normal mechanisms.

If outputs stubbornly return to historical values, hidden hardcoding is probably present.

---

## 11.6 Capability-chain tests

Choose a complex product and verify why it cannot yet be produced.

The system should return a dependency explanation such as:

> Rifle production blocked by primer chemistry, spring steel, barrel rifling precision, and brass cartridge-forming capability.

Then satisfy one missing prerequisite.

The blocker report should change appropriately.

This is extremely useful for both debugging and AI-agent interaction.

---

## 11.7 Baseline historical validation

Run the model without interventions.

Do **not** validate only against one headline outcome such as "Rome fell."

Validate many observables:

- regional population
- urbanization
- city-size distributions
- agricultural share of labor
- trade intensity
- travel/transport cost
- wages where evidence exists
- commodity price ratios
- tax extraction
- army sizes
- mortality
- life expectancy ranges
- literacy
- known technology appearance windows
- infrastructure growth
- state territorial extent
- conflict frequency
- settlement density

The goal is not exact replay.

The goal is that baseline runs inhabit a historically plausible region of outcome space.

---

## 11.8 Out-of-sample historical validation

This is essential to avoid tuning the model to one period.

Examples:

- calibrate mechanisms using one region/time period
- test them in another
- calibrate on early Roman data
- test later Roman behavior
- calibrate transport mechanics in Mediterranean routes
- test comparable routes elsewhere

A rule that only works in the dataset used to invent it is not general.

---

## 11.9 Distributional validation

Because the model contains stochastic processes, do not validate only one seeded run.

Run ensembles.

Measure distributions such as:

- median population
- variance in state survival
- city-size distribution
- frequency of wars
- technology timing distribution
- famine incidence
- wealth distribution

Historical outcomes should be plausible draws from the model, not necessarily the model's exact median path.

---

## 11.10 Sensitivity tests

Vary uncertain primitive parameters over defensible ranges.

Watch for:

- parameters that barely matter
- parameters that dominate everything
- discontinuities
- unstable feedback loops
- accidental thresholds

If a 1% change to an obscure parameter causes civilization to alternate between utopia and extinction, investigate.

Some real systems have thresholds, but they need a causal reason.

---

## 11.11 Intervention isolation tests

Before testing complicated scenarios, isolate interventions.

Example sequence for firearms:

1. give one rifle, no ammunition replacement
2. give one rifle plus ammunition
3. give 100 rifles
4. give manufacturing knowledge
5. give manufacturing knowledge plus machine tools
6. give complete supply chain
7. give a local state the ability to mass-produce

The model should show qualitatively different effects at each stage.

If all seven scenarios collapse to the same "+military power" behavior, the representation is too coarse.

---

## 11.12 Interaction tests

Test cross-domain propagation deliberately.

Example:

1. conscript 20% more workers
2. observe agricultural labor decline
3. observe food production
4. observe food prices
5. observe wages
6. observe tax revenue
7. observe military provisioning cost
8. observe future recruitment

Another:

1. open a canal
2. transport cost falls
3. trade volume changes
4. local prices converge
5. settlements shift
6. industry relocates or expands
7. tax base changes

If effects stop at the first system boundary, coupling is incomplete.

---

## 11.13 Adversarial scenario tests

Ask AI agents to propose interventions designed to break assumptions.

Examples:

- immortal monopolizes a key technology
- ruler bans ironworking
- city receives unlimited gold but no extra food
- epidemic kills only skilled artisans
- teleportation exists but only for information, not matter
- perfect map knowledge but no improved navigation instruments
- extremely fertile land with no navigable transport
- universal literacy under authoritarian information control

These tests are valuable because they expose hidden assumptions that normal historical scenarios do not.

---

## 11.14 Regression tests

Once a bug is fixed, save the smallest scenario that reproduced it.

Maintain a suite of miniature worlds:

- single farm
- one mine and one town
- two towns connected by one road
- island economy
- one state and one army
- two-state trade system
- simple research economy

These should run rapidly and deterministically.

Large historical-world simulations are too slow and noisy to serve as the only regression tests.

---

# 12. Observability and Explainability

The CLI should make the simulation inspectable.

AI coding agents will be much more useful if they can query **why** something happened.

Recommended commands/concepts:

```text
world status YEAR
region show REGION
agent show AGENT
org show ORGANIZATION
market show REGION GOOD
good trace GOOD
price explain REGION GOOD
production explain PRODUCT REGION
capability explain CAPABILITY REGION
technology explain TECHNOLOGY REGION
route explain ORIGIN DESTINATION
population explain REGION
war explain WAR_ID
event trace EVENT_ID
diff YEAR_A YEAR_B
```

Useful explanation output:

> Iron price rose 38% because military demand increased 22%, Mine A lost 16% of its workforce, and the eastern road disruption raised delivered transport cost 41%.

or:

> Local steam-engine construction is currently infeasible because cylinder boring precision, boiler plate quality, and high-pressure sealing capability are insufficient.

The exact percentages above are examples of output format only; the simulation should compute its own values.

Explainability is not cosmetic. It is necessary for detecting whether outcomes are generated for the right reasons.

---

# 13. Recommended Internal Interfaces

Avoid domain modules reaching into one another's private state arbitrarily.

Prefer shared typed objects and explicit requests/events.

Possible abstractions:

```python
Agent
Household
Organization
Region
Settlement
ResourceDeposit
Inventory
Good
KnowledgeItem
Skill
Capability
ProductionProcess
Facility
InfrastructureEdge
Route
Market
Institution
Event
```

Possible process APIs:

```python
estimate_requirements(process, quantity, location)
can_execute(process, actor, location)
execute_process(process, quantity, actor, location)
find_route(origin, destination, cargo)
quote_transport(route, cargo, quantity)
explain_price(good, market)
explain_capability(product, region)
```

The exact implementation may differ, but the architecture should make ownership and causality explicit.

---

# 14. Data vs Logic

Keep these separate.

## Data

- map geometry
- resource distributions
- crop characteristics
- material properties
- initial populations
- known historical infrastructure
- initial institutions
- initial knowledge

## Logic

- market clearing or bargaining
- production transformations
- migration decisions
- demographic processes
- research
- institutional decisions
- military operations
- knowledge diffusion

Historical observations should ideally live in validation datasets rather than production logic.

Bad:

```python
if year == 476:
    western_rome.collapse()
```

Better:

The political, fiscal, military, demographic, and external-pressure systems create conditions under which states may fragment.

Then compare the baseline ensemble with the historical record.

---

# 15. Scenario Representation

Scenarios should modify initial conditions or inject events, not replace system logic.

Example conceptual format:

```yaml
scenario:
  start_year: 100
  interventions:
    - type: add_agent
      location: Rome
      attributes:
        lifespan: immortal
        language_access: local_fluent
        knowledge_source: modern_technical_database
        initial_capital: scenario_defined
```

Another:

```yaml
scenario:
  interventions:
    - type: add_resource_deposit
      resource: gold
      location: Rome
      size: scenario_defined
      accessibility: scenario_defined
```

Another:

```yaml
scenario:
  interventions:
    - type: research_funding_change
      organization: state_x
      budget_change: scenario_defined
```

Scenario files should contain the changed facts, not predicted consequences.

---

# 16. Baseline Calibration Philosophy

Calibration is necessary, but dangerous.

Do not tune directly to desired macro outcomes.

Prefer calibrating lower-level mechanisms against multiple independent observations.

For example:

- crop processes against plausible yields
- transport against observed journey times/carrying costs
- demographic processes against mortality/fertility evidence
- manufacturing against known production constraints
- military logistics against plausible provisioning requirements

Then evaluate whether macro patterns emerge.

Whenever possible:

1. calibrate on one dataset
2. validate on another
3. test counterfactual behavior
4. run sensitivity analysis

A model that perfectly reproduces the past but behaves absurdly under small counterfactual changes is overfit.

---

# 17. Priority Tiers

Building every domain at full fidelity immediately is likely to fail.

## Tier 0 — Shared foundations

Must be trustworthy first:

- spatial world
- time/event engine
- inventory/stocks
- agents/organizations
- accounting
- process/recipe system
- networks/routes
- serialization
- deterministic random seeds
- logging/explainability

## Tier 1 — Core technological-development loop

Highest priority for the immortal scenario:

- resources
- energy
- agriculture/food
- population/labor
- human capital
- knowledge/research
- production capability
- tools/capital
- economy/prices
- transport/logistics

## Tier 2 — State and society

Needed for realistic scaling:

- settlements
- finance
- institutions/governance
- politics
- communication
- social structure/culture
- education

## Tier 3 — Historical disruption systems

Needed for robust alternate history:

- diplomacy
- conflict/war
- disease
- environmental variability
- disasters

This ordering is about implementation priority, not importance in history.

---

# 18. Minimum Viable Vertical Slice

Before building the entire Roman world, create a tiny synthetic world containing:

- 2 settlements
- farms
- 1 forest
- 1 iron deposit
- 1 river or road
- workers with different skills
- food
- timber
- iron
- simple tools
- one government
- one workshop
- one market
- one knowledge/research mechanism

Require it to demonstrate:

1. food production
2. labor allocation
3. endogenous prices
4. resource extraction
5. transport
6. tool production
7. capital investment
8. knowledge acquisition
9. capability unlocking
10. demographic response

Then inject an immortal with advanced knowledge.

The immortal should accelerate development only where the physical economy can exploit that knowledge.

This small world will reveal architectural flaws far faster than debugging the whole Mediterranean.

---

# 19. Acceptance Tests for the Project

The architecture is on the right track if all of these can eventually pass.

## A. Historical-name independence

Replacing all historical names with synthetic identifiers does not change outcomes.

## B. No intervention baseline

The model generates trajectories broadly compatible with known historical constraints without scripted historical events.

## C. Resource shock

Adding a major gold deposit alters labor, extraction, wealth, prices, trade, and politics through ordinary mechanisms.

## D. Population shock

Increasing population changes scarcity, wages, food demand, settlement, and military potential without relying on historical constants.

## E. Knowledge shock

An immortal with a technical database knows much more immediately but cannot manufacture technologies whose physical prerequisites are absent.

## F. Research shock

A wealthy research state discovers useful knowledge faster on average without knowing the future technology graph in advance.

## G. Military technology shock

Modern weapons strongly affect conflict when supplied, but their long-term effect depends on ammunition, maintenance, production, logistics, doctrine, capture, and adaptation.

## H. Geography matters naturally

Changing rivers, resource placement, terrain, or transport access changes development without a manually assigned regional bonus.

## I. Cross-domain propagation

A large intervention produces second- and third-order effects outside its originating domain.

## J. Explainability

For any important outcome, the CLI can expose the major causal contributors and resource constraints.

---

# 20. Architectural Warning Signs

Treat these as code-review red flags.

- `technology_level`
- `civilization_score`
- `military_strength_modifier`
- `agricultural_productivity_modifier`
- `innovation_bonus`
- hardcoded historical prices
- hardcoded historical city populations
- scripted collapses
- scripted invention dates
- country-specific hidden bonuses
- direct "wealth → technology" conversion
- direct "knowledge → production" conversion
- duplicated inventories across systems
- unlimited transport
- infinite substitution between skilled and unskilled labor
- goods appearing without production inputs
- firms or governments spending resources they do not possess
- armies operating without logistics
- research producing predetermined technologies solely from accumulated points

Not every scalar abstraction is wrong. A scalar is acceptable when it summarizes a real modeled state and can be derived from underlying conditions.

---

# 21. Practical Definition of Success

The simulator does not need to predict the one true alternate history.

That is not realistically knowable.

A successful simulator should instead:

1. obey physical and accounting constraints
2. produce internally coherent causal chains
3. reproduce broad historical behavior in baseline ensembles
4. respond sensibly to novel interventions
5. avoid secretly steering the world toward historical outcomes
6. make important outcomes explainable
7. expose uncertainty rather than hiding it
8. behave consistently across synthetic and historical test worlds

The strongest question to ask during development is:

> **If I changed this input in a world whose historical name I did not know, would the same code still produce a defensible result?**

If the answer is yes, the model is probably becoming genuinely general.

---

# 22. Concise System Inventory

For planning purposes, the current top-level domain list is:

1. Geography and terrain
2. Environment and climate
3. Resources and raw materials
4. Energy
5. Population and demography
6. Health and disease
7. Agriculture and food
8. Human capital, skills, and education
9. Knowledge, science, and technology
10. Production capability and manufacturing
11. Tools, infrastructure, and capital stock
12. Economy, markets, and allocation
13. Finance and capital
14. Trade, transport, and logistics
15. Settlement and urbanization
16. Communication and information
17. Social structure, culture, and religion
18. Institutions, law, and governance
19. Politics and diplomacy
20. War and security

These are **domains**, not necessarily 20 separate Python packages. Several may share infrastructure or eventually be implemented as interacting processes over the same world-state objects.

The number of modules in the codebase should follow clean ownership boundaries, not this list mechanically.
