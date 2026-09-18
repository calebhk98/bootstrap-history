# Architecture Review: `bootstrap-history` vs. Generative Historical Simulation Requirements

**Review target:** uploaded `bootstrap-history-main` repository  
**Compared against:** `HISTORICAL_SIM_ARCHITECTURE.md`  
**Review focus:** model architecture and generalization risk, not code style  
**Implementation constraint:** the current simulator remains the active product and is expanded in place

---

# Executive Summary

The current repository is a strong foundation for the requested simulator and should be **expanded rather than replaced, frozen, or forked into a parallel engine**.

The project already contains several important pieces that a more general historical simulation needs:

- a large dependency graph rather than a single technology level,
- capability rungs,
- material prerequisites and substitutions,
- civilization-specific starting state kept in data rather than technology code,
- dynamic labor scarcity,
- dynamic material-price pressure,
- physical stocks for some materials,
- explicit distinctions between knowledge and construction,
- geography-aware access costs,
- a CLI/protocol suitable for both humans and AI agents,
- extensive regression/playtest infrastructure,
- explanations of model limitations and known coupling problems.

Those should remain part of the live simulator.

The main task is **not** to replace the current architecture with a different project. It is to broaden the ontology of the existing simulation so that the founder/family is no longer the only richly represented actor.

The current family focus is reasonable. If an immortal invents a printing press in a private workshop, the state does not automatically own a printing press, know how it works, or gain its benefits. Likewise, the founder can choose to:

- keep knowledge private,
- sell it,
- license it,
- teach it,
- give it to a government,
- create a firm around it,
- use it for political influence,
- conceal it,
- claim divine origin,
- or fail to diffuse it at all.

That is desirable modeling behavior.

The required evolution is therefore:

```text
Current:
World + unusually detailed founder/family

Expand toward:
World containing several first-class actor/state types
    - founder/family
    - households/population cohorts
    - firms/workshops
    - governments
    - armies
    - settlements
    - markets
    - schools/research institutions
    - religious/social organizations
```

All of them should operate inside the **same simulation**, using shared goods, labor, knowledge, geography, institutions, and physical constraints.

The recommended strategy is an **in-place incremental migration**:

1. keep the existing `Sim` and CLI working,
2. add first-class world-state objects inside the existing engine,
3. route new behavior through those objects,
4. progressively convert old scalar shortcuts into derived compatibility values,
5. preserve old interfaces until callers have migrated,
6. remove obsolete shortcuts only after the replacement mechanism is live and tested.

No parallel simulator is required.

---

# 1. What the Current Project Already Models Well

The current simulator is best described as:

> **A detailed intervention simulator centered on an exceptional founder/family operating inside a historical civilization, with a large technology/capability model and increasingly dynamic economic constraints.**

That is a good starting point for the broader assignment.

The founder/family focus should **not** be interpreted as a design error by itself.

Ownership matters.

If the founder has:

- a steam engine,
- a modern rifle,
- a printing press,
- a chemical recipe,
- a book,
- a trained machinist,

then those things belong to the founder or the founder's organization unless transferred.

The government should not receive them automatically.

The important architectural expansion is to make other actors equally capable of owning:

- assets,
- knowledge,
- inventories,
- facilities,
- workers,
- money,
- claims,
- political authority,
- military forces.

The founder then remains special because of scenario inputs, not because only the founder can participate in the detailed simulation.

---

# 2. Core Architectural Direction

The correct target is not:

```text
replace founder simulator with world simulator
```

It is:

```text
grow founder simulator into a world simulator
```

The current object graph and APIs should be evolved so that existing founder behavior continues to work while more state becomes explicit.

A useful mental model is:

```text
Sim
 ├── WorldState
 │    ├── Regions
 │    ├── Settlements
 │    ├── Markets
 │    ├── Resource deposits
 │    ├── Infrastructure
 │    ├── Population cohorts
 │    ├── Organizations
 │    └── Shared event/history state
 │
 ├── Founder/Family organization
 ├── Government organizations
 ├── Firms/workshops
 ├── Armies
 ├── Schools/research organizations
 └── Scenario/intervention state
```

The `Sim` object may remain the orchestration surface for a long time.

There is no need to force a clean-room redesign.

---

# 3. Preserve These Existing Strengths

## 3.1 Technology dependency graph

This is one of the strongest assets in the repository.

The project has moved well beyond:

```text
Steam Engine -> Electricity -> Electronics
```

and instead represents thousands of prerequisites, materials, capability rungs, substitutions, build times, labor requirements, and knowledge references.

That is directly compatible with a capability-based simulation.

Keep it.

### Particularly strong ideas

- `pre` for mandatory prerequisites
- `req_any` for substitutions
- capability nodes for heat / tolerance / purity / power / measurement
- separate starting technologies per civilization
- node-to-knowledge-base links
- checking each node in isolation for whether its prerequisites are sufficient
- explicit distinction between "already exists in this society" and "universal zero-tier technology"

The graph should gradually become more actor-aware rather than be replaced.

---

## 3.2 Knowledge is not the same as ownership or production

The current implementation already captures part of this.

The broader model should make the distinction even sharper:

1. a design exists,
2. an actor knows the design,
3. an actor has the skill to execute it,
4. an actor owns the necessary tools,
5. an actor has access to materials,
6. an actor can produce one example,
7. an actor can maintain it,
8. an actor can reproduce it,
9. an actor can scale production,
10. other actors know or possess it.

This is where the current family focus becomes useful.

A founder can personally know a technology while the state does not.

A state can seize a workshop without acquiring all tacit knowledge.

A rival can capture a rifle without knowing how to make ammunition.

A book can spread explicit knowledge without creating skilled machinists.

That is exactly the sort of distinction the eventual simulation needs.

---

## 3.3 Civilization data separated from universal technology data

`data/civilizations/*.json` is a good direction.

Different civilizations explicitly declare starting conditions rather than relying on `if Rome:` style branches.

Preserve the rule:

> Scenario/history data belongs in data. General mechanisms belong in shared engine logic.

---

## 3.4 CLI-first and machine-readable protocol

This is a good architectural choice.

The command/protocol work already supports:

- state inspection,
- project explanation,
- path search,
- save/load,
- machine-readable command handling,
- fog-of-war,
- explicit errors,
- discoverability tests.

That is particularly valuable when AI agents are helping develop and test the simulator.

A GUI can remain an adapter layered over the same commands/state later.

---

## 3.5 Explainability

The repository repeatedly fixes cases where numbers move without enough explanation.

Keep doing that.

For a generalized simulator, explainability should become a first-class debugging interface.

Useful eventual commands include:

```text
why-price iron rome
why-wage smith rome
why-population alexandria
why-output egypt grain
why-war-result war_123
why-tech-blocked rifled_musket founder
why-tech-blocked rifled_musket roman_state
trace-demand copper
trace-knowledge printing_press
trace-event plague_17
```

The actor argument matters.

"Why can't Rome build this?" and "Why can't the founder build this?" may have different answers.

---

## 3.6 Regression and adversarial testing culture

The repository already has a strong habit of:

- recording playtest complaints,
- turning discovered bugs into regression tests,
- preserving deterministic seeds,
- checking performance,
- auditing graph structure,
- testing fog leaks,
- checking affordability and progression assumptions.

That should remain.

The new domains should be introduced with the same pattern: add a small mechanism, then add adversarial tests that try to break its assumptions.

---

# 4. The Main Architectural Gap

The main issue is **not that the founder is too detailed**.

The issue is that many other parts of society are still represented mostly by scalars or tables.

The correct expansion is to make the world contain more explicit things.

For example:

```text
Current:
population = scalar
wage = historical base × multiplier
state capacity = scalar
war = hazard
market supply = aggregate estimate
civilization knowledge = set
```

Gradually becomes:

```text
population = regional cohorts
wages = market outcomes over occupations/skills
state capacity = derived from institutions, officials, revenue, communication, enforcement
war = interaction between military organizations
market supply = production + stocks + imports
knowledge = owned by agents/organizations and diffused through networks
```

During migration, both forms can coexist.

The scalar should increasingly become a **derived summary** rather than the source of truth.

---

# 5. In-Place Expansion Pattern

Use a repeated migration pattern for each domain.

## Step A — Introduce explicit state

Example:

```python
world.population_cohorts
```

while preserving:

```python
sim.population
```

## Step B — Derive the old scalar from the new state

```python
sim.population = sum(c.count for c in world.population_cohorts)
```

or expose it as a property.

## Step C — Route one existing mechanic through the new state

Example:

Plague mortality affects cohorts instead of directly writing `pop_deficit`.

## Step D — Keep compatibility shims

Existing CLI commands/tests can continue reading the old aggregate.

## Step E — Add additional mechanics

Births, age transitions, migration, occupation changes.

## Step F — Remove obsolete direct mutations

Once everything uses cohort state, stop directly modifying `population`.

This lets the simulator improve continuously without a dead period or second engine.

---

# 6. Domain-by-Domain Expansion Plan

---

## 6.1 Geography and terrain

### Current state

The repository already has useful geography and reach calculations.

`GeographyMixin.region_reach()` uses factors such as:

- civilization home regions,
- distance,
- route difficulty,
- coastal access,
- travel capability.

That is a good approximation layer.

### Expand in place

Do not delete `region_reach()`.

Add explicit route/infrastructure state beneath it:

```python
TransportNode
TransportEdge
```

with fields such as:

- mode,
- length,
- capacity,
- travel time,
- seasonal availability,
- condition,
- toll/tax,
- ownership/control.

Initially:

```python
region_reach()
```

can continue returning its current result for locations without explicit routes.

For locations covered by the new network, use the network result.

Eventually the coarse reach formula becomes fallback/setup logic rather than the main freight model.

### Immediate payoff

The same route network can support:

- trade,
- armies,
- migration,
- information,
- disease,
- state administration.

---

## 6.2 Environment and climate

### Current state

Minimal.

### Expand in place

Start small.

Add annual or seasonal regional values:

```python
RegionalEnvironment:
    temperature
    precipitation
    water_availability
    flood_state
    drought_state
```

Do not simulate daily weather.

Initially these values only need to feed agriculture and exceptional events.

Historical climate data can initialize baseline years where available, while generated/scenario conditions can replace it.

---

## 6.3 Resources and raw materials

### Current state

Relatively strong:

- mines,
- material stocks,
- resource access,
- dynamic demand/price pressure,
- substitutions,
- supply-chain relationships.

### Expand in place

Promote resources from civilization availability to physical instances:

```python
ResourceDeposit:
    material
    region
    remaining_quantity
    grade
    extraction_difficulty
```

Existing mine/investment code can be modified so a mine points to a `ResourceDeposit`.

Then:

```text
deposit -> facility -> inventory -> transport -> buyer
```

gradually replaces generic national availability.

Keep current aggregate supply as a fallback for resources not yet converted.

---

## 6.4 Energy

### Current state

Power capability appears in the technology system and electricity has some explicit machinery.

### Expand in place

Add regional/facility energy accounting:

```python
EnergySource
EnergyProducer
EnergyDemand
```

Start with facilities that obviously need it.

Do not retrofit every tech node at once.

Suggested order:

1. water/wind-powered facilities,
2. steam,
3. electric generation,
4. industrial electrical loads.

Then gradually make production recipes declare energy inputs.

---

## 6.5 Population and demography

### Current state

This is one of the biggest simplifications.

Population is mainly a scalar with:

- shocks,
- `pop_deficit`,
- recovery,
- wage effects.

### Expand in place

Introduce cohorts while keeping the aggregate API.

Example:

```python
PopulationCohort:
    region
    age_band
    sex
    occupation
    skill_profile
    count
```

Start with coarse bands.

For example:

```text
0-14
15-49
50+
```

rather than single-year ages.

### Migration path

**Stage 1**

Initialize cohorts so:

```python
sum(cohorts) == current population
```

Existing code still reads total population.

**Stage 2**

Route deaths through cohorts.

**Stage 3**

Add births.

**Stage 4**

Add aging.

**Stage 5**

Add migration.

**Stage 6**

Use cohorts for labor supply and military recruitment.

At that point `pop_deficit` can become a compatibility statistic or disappear.

### Important change

Population recovery after a plague should eventually emerge from:

- surviving reproductive population,
- fertility,
- mortality,
- food,
- migration,
- household behavior,

rather than a fixed tendency to return to history.

---

## 6.6 Health and disease

### Current state

Disease mainly exists as historical hazards with direct population/staff effects.

### Expand in place

Keep historical hazard records, but reinterpret them.

Instead of:

```text
Antonine plague -> kill X%
```

use:

```text
Antonine plague -> introduce pathogen / epidemic state
```

Then disease mechanics determine the resulting mortality.

A minimal first version can track:

```python
DiseaseState:
    susceptible
    infected
    recovered_or_immune
```

at cohort/region scale.

The existing hazard system remains useful as an event injection framework.

---

## 6.7 Agriculture and food

### Current state

Agriculture is represented through technologies, investments, goods, and broad effects, but not as a full physical food system.

### Expand in place

Add a small number of agricultural processes first.

Example:

```text
land
+ seed
+ labor
+ tools
+ water/environment
-> grain
```

Then:

```text
grain -> storage -> spoilage -> transport -> consumption
```

Do not attempt dozens of crops immediately.

Start with:

- staple grain,
- livestock/animal food if needed,
- generic high-value crop later.

### Integration

Existing farm ventures can become owners/operators of agricultural facilities rather than abstract revenue nodes.

The current `rev` number can remain temporarily as a compatibility fallback until sale of actual output drives revenue.

---

## 6.8 Human capital, skills, and education

### Current state

Already fairly strong:

- trades,
- training,
- schools,
- literacy,
- staff supply,
- trade creation.

### Expand in place

Move skill from founder-only availability toward actor/cohort ownership.

Example:

```python
PopulationCohort.skills
Agent.skills
Organization.training_programs
```

The founder's school can still train founder employees.

A state school trains a different population.

A guild controls access to another skill pool.

This preserves the important fact that knowledge and skill are not automatically civilization-wide.

---

## 6.9 Knowledge, science, and technology

### Current state

Excellent for the immortal-with-database case.

Current assumption:

> RESEARCH IS FREE. BUILDING IS NOT.

is appropriate **for an actor who already has the knowledge source**.

It should not be a universal world rule.

### Expand in place

Introduce actor-specific knowledge state.

Example:

```python
KnowledgeState:
    known_nodes
    partial_nodes
    documented_nodes
    tacit_capabilities
```

Ownership examples:

```text
founder knows printing_press
roman_state does not
guild knows advanced_glassmaking
founder does not
```

### Database scenario

The immortal receives a huge set of explicit knowledge.

### Rich-country research scenario

The country receives:

- researchers,
- funding,
- equipment,
- institutions,

but not future knowledge.

Research then discovers nodes.

### Existing data reuse

Promote:

- `dev_years`
- `dev_people`
- prerequisites
- confidence

into the live research model.

Do not delete current project research behavior.

Make it conditional:

```text
if actor already has explicit knowledge:
    skip discovery cost
else:
    perform research
```

---

## 6.10 Production capability and manufacturing

### Current state

Strong capability prerequisites, trades, materials, and project gating.

### Expand in place

Separate the concept of:

```text
technology/process known
```

from:

```text
facility exists
```

and:

```text
facility is producing
```

Add:

```python
Facility:
    owner
    region
    processes
    workers
    tools
    energy_access
    capacity
    condition
    inventory
```

Current founder projects can produce facility instances.

Existing completed projects need not all be converted immediately.

Prioritize technologies where scale matters:

- metallurgy,
- machine tools,
- chemicals,
- printing,
- firearms,
- power generation.

---

## 6.11 Tools, infrastructure, and capital stock

### Current state

Many capital items exist as nodes/ventures.

### Expand in place

Convert important binary infrastructure into explicit capacity when useful.

Examples:

```text
road capacity
port throughput
mill capacity
furnace output
machine-tool hours
generator capacity
school seats
```

Continue allowing less important technologies to remain binary until the simulation needs more detail.

---

## 6.12 Economy, markets, and prices

### Current state

The project already has meaningful dynamic mechanisms:

- labor scarcity,
- material supply/demand pressure,
- cross-price effects,
- market saturation,
- credit,
- debt,
- wages,
- trade quotes.

This should be expanded, not replaced.

### Current limitation

Historical/book prices and wage anchors still carry too much weight.

### Expand in place

Create explicit local market state for selected goods first.

Example:

```python
Market:
    region
    good
    inventories_for_sale
    bids
    asks
    last_price
```

You do **not** need to switch every good to a full auction immediately.

A staged approach:

### Tier A goods

Fully endogenous:

- food,
- labor,
- timber,
- iron,
- fuel,
- transport.

### Tier B goods

Cost-derived:

- tools,
- weapons,
- processed materials.

### Tier C goods

Temporary historical/fallback pricing.

As Tier A/B coverage grows, historical prices move from live inputs toward calibration/validation.

### Soldier cost example

Do not create:

```python
ROMAN_SOLDIER_WAGE = ...
```

Instead, soldier cost should increasingly be:

```text
recruitment compensation
+ food
+ equipment
+ transport
+ housing/camp support
+ training
+ command/admin overhead
```

where those pieces come from the same markets as civilian demand.

---

## 6.13 Finance and capital

### Current state

Founder credit/debt already exists.

### Expand in place

Generalize ownership:

```python
Account
Loan
DebtClaim
OrganizationBalanceSheet
```

The founder becomes one account holder.

Governments and firms become others.

Do this after more physical production is explicit; otherwise finance risks becoming detached accounting.

---

## 6.14 Trade, transport, and logistics

### Current state

Reach and transport multipliers exist.

### Expand in place

Add finite route capacity and actual shipment demand.

Initially, only model shipments for important bulk goods:

- food,
- ore,
- coal/fuel,
- timber,
- military supply.

Small/high-value goods can continue using abstract freight calculations until needed.

This avoids exploding complexity.

---

## 6.15 Settlement and urbanization

### Current state

Mostly aggregate.

### Expand in place

Add settlements as world-state objects:

```python
Settlement:
    region
    population_cohorts
    housing
    water_capacity
    food_inventory
    facilities
    market
    institutions
```

Initially, existing cities can be initialized directly from historical data.

Their future growth should increasingly emerge from:

- jobs,
- food access,
- mortality,
- migration,
- housing,
- trade,
- politics.

---

## 6.16 Communication and information

### Current state

Printing and communication technologies exist, but information diffusion is not generally modeled as a network flow.

### Expand in place

Once actor-specific knowledge exists, add diffusion pathways:

```text
speech/contact
messenger
school
book/manuscript
printing
postal network
telegraph
radio
```

Knowledge transfer should have:

- sender,
- receiver,
- medium,
- time,
- reliability,
- literacy/skill requirements.

This directly supports the founder deciding whether to share knowledge.

---

## 6.17 Social structure, culture, religion, and incentives

### Current state

Civilization value vectors are useful shortcuts:

- novelty,
- religion,
- magic fear,
- commerce,
- military interest,
- labor-saving attitudes.

### Expand in place

Do not remove them immediately.

Treat them as aggregated descriptors.

Gradually add social groups with interests:

```text
landowners
farmers
urban laborers
guilds
merchants
military elites
clergy
officials
```

Then some current scalar attitudes can become derived from weighted group behavior.

### Founder example

If the founder calls himself Zeus, reactions should depend on:

- religious institutions,
- political authority,
- observed capabilities,
- social networks,
- elite incentives,
- prior reputation,
- who benefits,
- who is threatened.

Not merely one `magic_fear` scalar.

But the scalar can remain a coarse fallback while the detailed actors are added.

---

## 6.18 Institutions, law, and governance

### Current state

There are meaningful institutional concepts and state-capacity effects.

### Expand in place

Represent major institutions as explicit rules:

```python
TaxRule
PropertyRule
ContractRule
InheritanceRule
ConscriptionRule
GuildRule
SlaveryOrForcedLaborRule
```

The current scalar `state_capacity` should gradually become a derived summary of:

- officials,
- records,
- communication,
- revenue,
- enforcement,
- local compliance,
- institutional reach.

Keep the scalar API during migration.

---

## 6.19 Politics and diplomacy

### Current state

Founder-state interaction is relatively developed.

State-to-state diplomacy is limited.

### Expand in place

Turn governments into actual organizations using the same ownership model.

They should possess:

- treasury,
- tax claims,
- territory,
- officials,
- military units,
- knowledge,
- infrastructure,
- relationships.

Then the founder can:

- sell technology to one state,
- hide it from another,
- become a state contractor,
- found a polity,
- challenge authority,
- remain private.

That supports the existing founder gameplay rather than replacing it.

---

## 6.20 War and security

### Current state

Military technologies exist, and historical hazards represent many wars/invasions.

### Expand in place

The current hazard system can remain as a baseline scenario/event system while war becomes more endogenous.

The key migration is:

```text
historical event says outcome
```

toward:

```text
historical event introduces actors/pressure/conditions
simulation resolves outcome
```

Example migration:

Old:

```text
Spanish invasion occurs on date X and causes predefined effects
```

Intermediate:

```text
Spanish expedition appears on/around historical date with ships, troops,
weapons, objectives, disease exposure, and logistical state
```

Simulation then determines:

- landing success,
- alliances,
- battles,
- disease spread,
- conquest,
- retreat,
- reinforcement.

Later, even expedition timing can become more endogenous if the simulation scope includes the relevant foreign state and exploration system.

This staged interpretation is compatible with maintaining the current game throughout development.

---

# 7. Ownership Must Become a Core Concept

The founder/family scenario makes this especially important.

Every important asset should increasingly have an owner or controller.

Examples:

```text
knowledge
tools
facility
inventory
land
money
road
ship
army
book
patent/license if applicable
```

Possible owners:

```text
individual
household
firm
guild
state
army
temple/church
school
community
```

This solves many future problems cleanly.

A printing press built in the founder's workshop does not automatically alter the whole civilization.

Effects depend on what the founder does:

```text
keep private
sell books
train printers
license the process
give plans to government
publish plans openly
state seizes workshop
workers leave and copy technique
rival spies steal design
```

That is a much richer simulation than either:

```text
printing_press = civilization_unlocked
```

or:

```text
printing_press = founder_only forever
```

---

# 8. Knowledge Diffusion Should Be Explicit

The current tech tree mostly answers whether technology is available/complete.

The expanded engine should ask:

```text
Who knows it?
Who can teach it?
Who can understand the documentation?
Who has practiced it?
Who owns the required facility?
Who can copy it?
Who has seen the output?
```

A useful staged knowledge model could be:

```text
unknown
heard_of
documented
understood
practiced
mastered
standardized
```

Not every technology must literally use every state.

The point is that technology can spread independently of ownership of finished goods.

This also gives multiple future agents something meaningful to do.

---

# 9. Historical Data: Use It Without Letting It Dictate Outcomes

The current repository contains many historical inputs.

That is fine.

The important distinction is between:

## Initialization data

Examples:

- population around 100 AD,
- existing roads,
- known mines,
- institutions,
- known technologies,
- settlement locations.

These are legitimate starting state.

## Calibration data

Examples:

- plausible yields,
- travel times,
- mortality ranges,
- historical wage ratios,
- material prices,
- army provisioning costs.

These help tune mechanisms.

## Validation data

Examples:

- city sizes not used during calibration,
- later population estimates,
- observed price relationships,
- trade patterns,
- state revenue,
- technology timing.

These should test the model.

## Scenario events

Examples:

- earthquake,
- volcanic eruption,
- introduction of a pathogen,
- arrival of an external group not otherwise simulated.

These may be legitimate event inputs.

## Outcomes that should increasingly become endogenous

Examples:

- conquest,
- state collapse,
- urban decline,
- army success,
- fiscal collapse,
- industrialization,
- political revolution.

The current historical hazards can remain during migration, but more of their consequences should be resolved through normal systems over time.

---

# 10. Hardcoded Numbers: Practical Rule

The assignment's "no hard inputs" requirement should be interpreted as:

> Do not hardcode a historical result when the result can be generated from lower-level state.

Some numbers are unavoidable and desirable.

## Good fixed/empirical inputs

- geographic distance,
- material density,
- melting point,
- human calorie requirements,
- crop growth characteristics,
- tool material requirements,
- initial population,
- historical starting inventories,
- physical efficiencies.

## Transitional heuristics

These are acceptable while the deeper system is not yet implemented, but should be marked:

- price index,
- wage index,
- broad state-capacity scalar,
- generic market output,
- direct social-attitude weights,
- fixed population recovery rate.

## Values that should ultimately become outputs

- soldier compensation,
- city population,
- industrial output,
- state revenue,
- market wages,
- army size,
- technology adoption,
- trade volume,
- infrastructure growth,
- famine severity.

The project does not need to eliminate every heuristic immediately.

It needs to **label them and progressively replace the important ones**.

---

# 11. Add Parameter Provenance Metadata

The existing confidence metadata is a strong start.

Extend it.

Every important numeric parameter should ideally declare its provenance class:

```text
physical_constant
biological_parameter
historical_initial_condition
historical_observation
calibration_parameter
scenario_parameter
engineering_estimate
temporary_heuristic
derived_value
```

This will make review much easier.

Example:

```json
{
  "value": 0.35,
  "type": "temporary_heuristic",
  "note": "Population recovery approximation pending cohort model",
  "confidence": "low"
}
```

Then scripts can report how much of a scenario still depends on temporary heuristics.

---

# 12. Update the Tech-Tree Schema Gradually

Do not redesign all 2,800+ nodes in one pass.

Use compatibility.

| Current field | Direction |
|---|---|
| `id`, `name`, `kb` | Keep |
| `pre` | Keep |
| `req_any` | Keep |
| capability requirements | Keep strongly |
| `mat` | Keep; increasingly attach to explicit production/process definitions |
| `lab` | Keep concept; price/availability becomes more endogenous |
| `build_yrs` | Keep as a baseline engineering estimate |
| `adopt_yrs` | Gradually replace with diffusion behavior |
| `dev_years`, `dev_people` | Promote into live research mechanics |
| `ph` | Keep where relevant to founder/scenario interaction |
| `cap` | Transitional; gradually derive from inputs, labor, facilities, finance |
| `up` | Gradually convert to explicit maintenance consumption |
| `rev` | Transitional; gradually derive from output sold |
| `risk` | Gradually derive from skill, tooling, maturity, environment, quality |
| `sch`, `art` | Map toward explicit workforce/skill requirements |
| `traits` | Keep as tags; avoid permanent direct civilization modifiers |
| `conf` | Keep strongly |

---

# 13. The Existing `Sim` Object Can Stay

The current `sim/ARCHITECTURE.md` correctly notices substantial shared-state coupling.

Do not refactor merely to produce small files.

The existing `Sim` can continue to orchestrate the system.

The useful changes are additions like:

```python
class Sim:
    world: WorldState
    family: FamilyState
    organizations: OrganizationRegistry
    ...
```

or equivalent composition.

Existing methods can delegate gradually.

For example:

```python
def current_population(self):
    if self.world.population_cohorts:
        return self.world.population_total()
    return self._legacy_population
```

Later the fallback disappears.

This is a far safer path than either:

- freezing the simulator,
- creating a second engine,
- or doing a giant one-shot refactor.

---

# 14. Concrete Incremental Development Plan

This plan assumes the simulator must remain usable after every step.

---

## Phase 1 — Add world-object foundations without changing behavior

Add:

```text
WorldState
RegionState
Organization
Inventory
Facility
PopulationCohort
Settlement
```

Initially, many objects can simply mirror current values.

Acceptance criterion:

> Existing tests remain green and normal gameplay behaves the same.

No major mechanic needs to change yet.

---

## Phase 2 — Generalize ownership

Make founder/family one organization/owner type.

Add government ownership.

Allow technologies/assets to distinguish:

```text
known_by
owned_by
operated_by
controlled_by
```

Start with a few important assets.

Acceptance tests:

- founder builds printing press; state does not automatically get it,
- founder transfers press to state; ownership changes,
- founder teaches process; knowledge transfers separately from machine ownership.

This directly strengthens the current requested scenario.

---

## Phase 3 — Move inventory and production toward actor/facility ownership

Start with a narrow set:

- food,
- timber,
- iron,
- fuel,
- tools.

Existing founder inventory code can be generalized rather than discarded.

Facilities consume inputs and create outputs.

Acceptance criterion:

> No converted facility can produce goods without required physical inputs.

---

## Phase 4 — Add local markets for core goods

Make core goods use local supply/demand.

Recommended first goods:

1. staple food,
2. general labor,
3. timber,
4. iron,
5. fuel,
6. transport.

Keep historical/fallback prices for unconverted goods.

Acceptance criterion:

> Soldier provisioning, farm operation, and workshop costs begin responding to the same food/labor/iron markets.

---

## Phase 5 — Add population cohorts

Keep aggregate population APIs.

Move:

- mortality,
- labor supply,
- military recruitment,

onto cohorts first.

Then add:

- births,
- aging,
- migration.

Acceptance criterion:

> Population shocks recover because of demographic processes, not because a deficit scalar automatically decays.

---

## Phase 6 — Add agriculture as a physical production system

Convert farm ventures first.

Inputs:

- land,
- labor,
- seed,
- tools,
- environment.

Outputs:

- food stocks.

Connect food to:

- consumption,
- price,
- mortality,
- army supply,
- settlement support.

Acceptance criterion:

> A food shortage raises food scarcity and has cross-domain consequences without a direct famine modifier being required.

---

## Phase 7 — Add explicit knowledge ownership and research

Current founder:

```text
has database -> explicit knowledge available
```

Other actors:

```text
must discover or receive knowledge
```

Introduce:

- research organizations,
- experiments,
- knowledge transfer,
- teaching.

Acceptance tests:

- rich state without future knowledge,
- founder with database,
- founder teaches state,
- state steals/captures technology,
- knowledge spreads without physical asset transfer.

---

## Phase 8 — Add transport capacity and settlements

Turn important roads/rivers/ports into capacity-bearing infrastructure.

Add settlements containing:

- population,
- market,
- facilities,
- food stocks.

Acceptance criterion:

> Bulk industry prefers locations for physically understandable reasons such as nearby inputs, transport, markets, and labor.

---

## Phase 9 — Generalize state finance and institutions

Government becomes a full organization.

Add:

- tax collection,
- treasury,
- spending,
- officials,
- borrowing,
- conscription,
- enforcement.

Existing `state_capacity` remains as a summary/compatibility property.

Acceptance criterion:

> A government cannot field armies or fund projects beyond its ability to acquire resources, credit, labor, and administrative reach.

---

## Phase 10 — Make war increasingly endogenous

Keep current hazard/event framework.

Replace predefined effects with actor/state interactions.

First:

```text
historical war event -> instantiate forces and objectives
```

Then normal war/logistics rules resolve the result.

Later:

```text
political/diplomatic system -> decides whether war happens
```

Acceptance criterion:

> Giving Rome rifles can alter battles, casualties, finances, territorial control, enemy adaptation, and politics without a single `military_strength_bonus` deciding the outcome.

---

## Phase 11 — Add deeper culture/social structure only where needed

Do this after economic, organizational, and institutional incentives are explicit.

Many currently "cultural" effects may turn out to be explainable through:

- income,
- status,
- elite power,
- religion,
- institutions,
- risk,
- information.

Keep existing civilization values until the replacement behavior is working.

---

# 15. Recommended Compatibility Strategy

Every converted subsystem should expose old summary properties.

Examples:

```python
sim.population
sim.population_deficit
sim.state_capacity
sim.price_index
sim.wage_index
```

can remain temporarily.

But their implementation should change from:

```text
authoritative input
```

to:

```text
derived summary of richer state
```

This is the key to evolving the live project without breaking every caller at once.

---

# 16. Testing Strategy for the In-Place Upgrade

Keep all current tests.

Add new tests as each subsystem becomes richer.

---

## 16.1 Ownership tests

### Private invention

Founder builds a printing press.

Expected:

- founder owns it,
- state does not,
- civilization-wide literacy/printing does not jump automatically.

### Gift

Founder transfers press to state.

Expected:

- ownership changes,
- state can operate it only if it has suitable workers/materials/knowledge.

### Knowledge without asset

Founder teaches printing but keeps the press.

Expected:

- recipient can potentially build another press if prerequisites exist.

---

## 16.2 Currency denomination invariance

Rescale all nominal currency by 100.

Real outcomes should remain unchanged.

This detects accidental dependence on nominal historical values.

---

## 16.3 Civilization renaming

Rename Rome to a synthetic identifier.

Behavior should not change.

---

## 16.4 Closed-world conservation

Create an isolated region.

No imports.

Track:

- food,
- timber,
- metal,
- people,
- tools.

Physical goods must come from inventories/processes.

---

## 16.5 Population scaling

Scale:

- population,
- land,
- housing,
- resources,
- tools,
- infrastructure

together.

Many per-capita outcomes should remain broadly similar.

---

## 16.6 Labor competition

Increase army recruitment.

Expected:

- military labor rises,
- civilian labor becomes scarcer,
- wages/prices respond,
- production changes,
- food/logistics demand changes.

No special bridge should be required between military and economy.

---

## 16.7 Gold deposit

Add a large gold deposit.

Do not specify an effect.

Observe:

- mining employment,
- migration,
- ownership,
- tax effects,
- money/finance,
- imports,
- political competition.

---

## 16.8 Gun scenarios

Test separately:

1. one rifle, little ammunition,
2. 100 rifles, no replacement ammunition,
3. rifles plus ammunition,
4. firearm knowledge only,
5. knowledge plus machine tools,
6. full supply chain.

They should not collapse to the same military outcome.

---

## 16.9 Rich-research-state scenario

Give a state more:

- researchers,
- equipment,
- money,
- institutions,

but no future database.

Expected:

- faster/broader experimentation,
- more discoveries,
- no guaranteed predetermined sequence.

---

## 16.10 Knowledge-only scenario

Give perfect explicit instructions but no physical capability.

Expected:

- knowledge blockers disappear,
- material/tool/skill blockers remain.

---

## 16.11 Geography substitution

Create comparable regions where one has cheap navigable transport and one does not.

Bulk prices, industrial location, and viable scale should diverge.

---

## 16.12 Baseline historical validation

Continue running historical baseline scenarios.

But increasingly validate:

- distributions,
- ranges,
- relationships,
- plausible timing windows,

rather than exact scripted outcomes.

Examples:

- population ranges,
- urbanization,
- wage ratios,
- army scale,
- trade intensity,
- technology availability windows,
- disease burden,
- state revenue.

---

# 17. Historical Hazards: Do Not Delete Them

The existing hazard timeline is useful infrastructure.

The change is to make hazards increasingly **less prescriptive**.

A useful progression is:

### Level 0 — current

```text
event -> predefined effect
```

### Level 1

```text
event -> shock value calculated from current conditions
```

### Level 2

```text
event -> introduce pathogen/army/disaster actor
```

### Level 3

```text
normal simulation resolves consequences
```

### Level 4

For events inside the modeled causal scope:

```text
normal simulation determines whether event occurs at all
```

This allows continuous improvement while keeping scenarios playable.

---

# 18. Changes to `HISTORICAL_SIM_ARCHITECTURE.md`

The earlier architecture document remains broadly useful but should be amended.

---

## Change 1 — Replace "world, not protagonist" with a more precise rule

The previous wording could imply that foregrounding the founder is inherently wrong.

Better:

> **The protagonist may receive high simulation detail, but the protagonist must operate inside shared world rules. Ownership, knowledge, production, markets, institutions, and physical constraints must not become protagonist-only mechanics.**

This reflects the actual requirement better.

---

## Change 2 — Add ownership/control as a fundamental world concept

The common world-state table should include:

| Fundamental thing | Examples |
|---|---|
| **Ownership/control** | who owns a machine, mine, road, book, workshop, army, inventory, or financial claim |

This is especially important for the founder scenario.

---

## Change 3 — Distinguish definitions from instances

### Definitions

- technology,
- recipe/process,
- skill type,
- commodity,
- institution type.

### Instances

- this press,
- this mine,
- this road,
- this organization,
- this book,
- this stockpile.

The current repository is rich in definitions and needs more instances.

---

## Change 4 — Make epistemic state actor-specific

Knowledge should be held by:

- people,
- households,
- firms,
- schools,
- states,
- guilds.

Not only by "civilization."

---

## Change 5 — Add historical-data provenance

Keep separate conceptual categories:

```text
initial condition
physical/biological data
calibration observation
validation holdout
scenario event
temporary heuristic
```

No need to physically reorganize every data file immediately.

Start by tagging new/modified values.

---

## Change 6 — Make physical accounting a stronger invariant

For converted goods:

> Every physical output must be traceable to inventories, production, imports, or an explicit exogenous source.

Allow temporary fallback markets for unconverted goods.

---

## Change 7 — Emphasize incremental migration

The architecture document should explicitly state:

> Existing aggregate/scalar mechanisms may remain during development. As richer subsystems are added, old values should become derived compatibility outputs and be removed only when no longer needed.

This better matches the active development constraint.

---

# 19. Existing Tests That Need Reinterpretation, Not Immediate Removal

Some current regression tests encode the old abstraction.

Do not delete them immediately.

Classify them.

Example:

> Spanish invasion arrives on the historical date.

For the current simulator, that protects expected scenario behavior.

As war/diplomacy become richer, change the test in stages.

Possible progression:

1. expedition is still introduced historically,
2. expedition's outcome becomes endogenous,
3. expedition timing gets a historical window,
4. expedition itself becomes endogenous if Spain is fully modeled.

This is safer than simply removing historical tests before replacement mechanics exist.

---

# 20. What to Keep Nearly Unchanged

Preserve as much as practical:

1. tech IDs and dependency graph,
2. capability rung definitions,
3. `req_any` substitutions,
4. knowledge-base documents,
5. confidence metadata,
6. material vocabulary,
7. civilization starting-tech data,
8. CLI philosophy,
9. JSON protocol,
10. deterministic seed behavior,
11. save/load discipline,
12. complaint/regression workflow,
13. path/explanation tooling,
14. static graph audits,
15. performance fingerprints,
16. founder/family gameplay and ownership.

---

# 21. What Should Gradually Become Derived

Do not rip these out at once.

Treat them as migration targets:

1. `price_index`
2. `wage_index`
3. `pop_deficit`
4. broad `state_capacity`
5. generic national supply
6. fixed revenue fields
7. direct population effects
8. direct military relief multipliers
9. generic culture reaction weights
10. fixed adoption delays
11. historical hazard outcome magnitudes

Each should remain until its replacement is working.

---

# 22. Immediate Next Work

Given the current repository and the requirement to keep it live, I would prioritize the following.

## 1. Add generalized ownership

This strengthens the current founder scenario immediately and is foundational for everything else.

Represent at least:

```text
founder/family
government
other organization
```

as owners.

## 2. Add actor-specific knowledge

Let founder and government know different things.

This immediately supports:

- secrecy,
- technology transfer,
- sale,
- theft,
- education,
- state research.

## 3. Add `WorldState` containers without changing current behavior

Start introducing:

```text
regions
organizations
settlements
population cohorts
facilities
```

even if many initially mirror current aggregate data.

## 4. Convert one narrow physical chain end-to-end

Recommended:

```text
forest -> timber -> charcoal -> iron -> tools
```

or:

```text
farm -> grain -> transport -> city consumption
```

Use actual inventories, labor, facilities, and local markets.

Do not convert the whole economy at once.

## 5. Generalize the current family production code

Where possible, let:

```python
owner = founder
```

become a parameter rather than an assumption.

Then the same project/facility mechanics can later be used by:

- state workshops,
- private firms,
- guilds,
- armies.

## 6. Start tagging temporary heuristics

Make it easy to answer:

> What parts of this simulation still depend directly on historical/scalar shortcuts?

That gives you a measurable migration queue.

---

# 23. Overall Assessment

## What is good

The repository is already a strong prototype for the requested work.

It has substantial reusable machinery and a much better testing culture than most early simulation projects.

The technology/capability graph is especially valuable.

The founder/family focus is not inherently a mistake. It is appropriate to the current intervention scenario and correctly preserves private ownership and control.

## What needs to change

The rest of the world needs to gain more of the same explicit state that the founder already has.

The biggest future additions are:

- generalized ownership,
- actor-specific knowledge,
- organizations,
- physical facilities,
- population cohorts,
- agriculture,
- settlements,
- local markets,
- transport capacity,
- state finance,
- endogenous research,
- military organizations,
- increasingly endogenous historical events.

## Most important architectural rule

Do not solve generalization by making the founder less detailed.

Solve it by making the founder's mechanisms **general enough that other actors can participate in them**.

For example:

```text
Bad direction:
remove founder workshop system and create abstract civilization production

Better direction:
make workshop ownership generic so founder, firm, guild, or state can own one
```

Likewise:

```text
Bad direction:
civilization unlocks printing because founder built a press

Better direction:
founder owns press
founder knows process
knowledge and machines diffuse only through explicit transfer, copying,
teaching, sale, capture, spying, or independent discovery
```

That supports both the current scenario and the broader simulator.

## Bottom line

**Keep developing the existing simulator. Do not freeze it. Do not create a parallel engine. Do not throw away the founder/family model.**

Expand the same engine outward.

The migration target is:

```text
Current:
detailed founder/family + aggregate surrounding world

Next:
detailed founder/family
+ explicit government
+ explicit organizations
+ explicit population/settlements
+ explicit facilities/markets
+ shared geography/resources/institutions

Eventually:
all important actors interacting through the same world rules
```

That path keeps the project usable at every step and turns the current implementation into the requested general historical simulator rather than replacing it.
