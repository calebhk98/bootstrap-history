# Plan: per-actor state, then partner countries as economies

Note: names below are as they were when the plan was written, except section 4, which says where each result lives now. Re-find a name with `grep -rn <name> sim`.

**Status:** built; the stage statuses below say what each stage holds and what was not run. Written 2026-10-06 as a design; the end rule for several seats is the owner's decision of 2026-10-09 (a founder's death ends that seat only).
**Covers:** Complaint 382 step 3 (per-actor household, project and knowledge state, so a second player can exist), Complaint 382 step 4 and Complaint 407 (partner countries as economies with their own labour market and output).
**Comes after:** 382 step 1 (every money posting names a counterparty), 382 step 2 (households as cohort actors) and 428 (the labour core sets the agent economy's wages). Those are in flight; this plan says where it must wait for each.

Sections 1 to 3 are the design as written on 2026-10-06; they name state classes and helpers that no longer exist (`ProjectsState`, `GovernanceState`, `SeatParty`, `FounderParty`, `SimWorld`, `_relative`, `_home_profile`, the root `state.household`, `state.projects` and `state.founder` aliases). Section 4 says what was built and where it lives. The counts in section 1 are a dated record and are not reproduced by the commands beside them today.

---

## 1. Where the single founder is wired in today

The saved state is one dataclass per subsystem, and `SimulationState` holds exactly one of each. So "one founder" is not a class problem, it is that the root holds one `household`, one `projects`, one `founder`, and the engine reads them through the root.

Four facts decide the design:

1. **The root fields are read directly almost everywhere.** `self.state.household.x`, `self.state.projects.x` and `self.state.founder.x` are called from the engine, the packages and the UI. Rewriting those to take a seat argument is the largest possible diff and the one `HOUSEHOLD_EXTRACTION.md` already measured as costly (an indirection per access on the hot path, and every call site touched).
2. **`EconomyState` mixes two things.** Market books, foreign ledgers and the agent economy's record are world state. Mines, forest, nitre beds, farm hectares, the material stock ledger, `throttle`, `binding` and `shortages` are what one holder owns. Today the holder is the founder.
3. **A second kind of player already exists, but a thin one.** `Player` (`sim/agents/player.py`, `ActorRecord`) has a purse, knowledge, concerns and works, and queues orders. It has no staff hours, no project engine, no fog, no standing, no log. It is a copy-research actor, not a founder. Giving a human a thin record would make the second seat a different game from the first.
4. **The party id is a string constant in several places** (`FOUNDER` in `goods_market_api.py`, `FOUNDER_AGENT` in `economy_port_year.py`, `FOUNDER_ACTOR_ID` in `household_party.py`, `FOUNDER_LOAN` in the capital market). They are the same idea spelled four times.

`SIM_STATE_INVENTORY.md` was measured before the typed state existed. Its field names are right and its category column (HOUSEHOLD, WORLD, SCENARIO, INTERNAL) is still the classification used here, but its "first set" and "file count" columns describe `Sim` attributes that are now state fields. The fields to move are listed from the dataclasses below, not from that table.

### Measurements (a dated record of 2026-10-06, branch `structural-dedupe-and-owner-decisions`, test files excluded unless stated; the commands run today give other counts)

| What | Command | Count |
|---|---|---|
| Reads and writes of `state.household` | `grep -rn "state\.household" sim --include=*.py \| grep -v sim/tests \| wc -l` | 472 across 60 files (`grep -rln` for the file count) |
| Reads and writes of `state.projects` | `grep -rn "state\.projects" sim --include=*.py \| grep -v sim/tests \| wc -l` | 292 |
| Reads and writes of `state.founder` | `grep -rn "state\.founder\b" sim --include=*.py \| grep -v sim/tests \| wc -l` | 56 |
| `sim.household` / `self.household` / `s.household` | `grep -rnE "\b(self\|sim\|s)\.household\b" sim --include=*.py \| grep -v sim/tests \| wc -l` | 197 across 38 files |
| Whole-word `FOUNDER` (the goods-market party) | `grep -rnw FOUNDER sim --include=*.py \| grep -v sim/tests` | 22, in 11 files (`cli.py`, `dispatch.py`, `step_alerts.py`, `render_screen_state.py`, `society_adoption.py`, `core_step_phases.py`, `goods_market_api.py`, `core.py`, `society_diffusion.py`, `market_clearing.py`, `agents_port_groups.py`); only `goods_market_api.py`, `market_clearing.py` and `agents_port_groups.py` use it as a party id, the rest are prose or the `FOUNDER_*` constants |
| `FounderParty` uses | `grep -rn FounderParty sim --include=*.py` | 3 |
| Other party-id constants | `grep -rn "FOUNDER_ACTOR_ID\|FOUNDER_AGENT\|FOUNDER_LOAN" sim --include=*.py \| grep -v sim/tests` | `household_party.py`, `founder_sales.py`, `economy_port_year.py`, `economy_capital_market.py`, `economy_credit.py` |
| `founder_alive` | `grep -rn founder_alive sim --include=*.py \| grep -v sim/tests \| wc -l` | 42 |
| `.capital` | `grep -rnE "\.capital\b" sim --include=*.py \| grep -v sim/tests \| wc -l` | 202 |
| `.done` | `grep -rnE "\.done\b" sim --include=*.py \| grep -v sim/tests \| wc -l` | 207 |
| `revealed` | `grep -rnw revealed sim --include=*.py \| grep -v sim/tests \| wc -l` | 43 |
| Files touching fog or `revealed` | `grep -rln "sim\.fog\|self\.fog\b\|\.revealed" sim --include=*.py \| grep -v sim/tests \| wc -l` | 40 |
| `goal` / `_goal` uses | `grep -rn "_goal\b\|sim\.goal\b\|self\.goal\b" sim --include=*.py \| grep -v sim/tests \| wc -l` | 150 |
| Owner-held `EconomyState` fields read as `state.economy.<field>` (see section 2.2 for the list) | the `grep -rnE` in section 2.2 | 49 across 14 files in `sim/`, 30 more in `sim/tests/` |
| Warn-once `_said_*` fields read through the household or scenario | `grep -rn "state\.scenario\._said\|state\.household\._said" sim --include=*.py \| grep -v tests \| wc -l` | 21 |
| Lines in test files naming `household` | `grep -rn household sim/tests \| wc -l` | 1185 |

Fields per state class: `python3 -c "import dataclasses; from sim.engine import state as s; [print(c.__name__, len(dataclasses.fields(c))) for c in s.ALL_STATE_CLASSES]"` (the counts on the date above are not kept).

---

## 2. Step 3: per-actor state

### 2.1 The shape: a seat record, with the root fields as the acting seat's alias

Introduce one record per human, LLM or later AI player, called a **seat**. It owns, in one dataclass, everything that belongs to whoever holds a purse and a tree:

- `household: HouseholdState`
- `projects: ProjectsState` (including `revealed` and `disclosures`, so fog and secrecy come with it)
- `founder: FounderState` (renamed `person` or kept; see open questions)
- `holdings`: the owner-held part of `EconomyState` (section 2.2)
- `governance`: `inst_units` and `gov` (standing with the state, accrued from the seat's own institutions)
- `goal`, `goal_year`, `goal_years`, and the seat's warn-once markers (`_said_*`)
- `country`: which country the seat belongs to (home by default); `location`: its base tile (`base_tile` already exists on the household and is the seed)

`SimulationState` gains `seats: Dict[str, SeatState]` and `acting_seat: str`. The id of the first seat is the one string the party-id constants already agree on (`"founder"`), kept as the single source `FOUNDER_ACTOR_ID`.

**The root fields stay, as the acting seat's live objects.** `state.household`, `state.projects`, `state.founder` and the new `state.holdings` are plain attributes that point at the objects inside `seats[acting_seat]`. A context manager, `with sim.act_as(seat_id):`, rebinds those root attributes and the `Household` facade, then restores them. No call site changes, no per-access cost (the table in `HOUSEHOLD_EXTRACTION.md` section 2 is why a property or `__getattr__` forward is rejected), and the engine's mixins keep saying `self.state.household.capital`.

What this costs, and how to contain it:

- **Aliases must not be saved twice.** The save is derived from the dataclass fields (`get_save_fields`, `serialize_state`). Mark the aliased root fields with `field(metadata={"alias": True})` and have `serialize_state` and `get_save_fields` skip them: that is one exclusion rule, consistent with "fields are detected automatically and only exclusions are listed". Load builds `seats`, then binds the aliases to `seats[acting_seat]`.
- **No reference may outlive a switch.** A function that stores `state.household` in a local across a call that calls `act_as` would write to the wrong seat. Rule: `act_as` is only entered by the year loop and the protocol dispatcher (the two places that choose a seat), never by mechanism code. A test (section 4, stage A) walks every `state.household` capture in a switch and asserts identity.
- **Caches are per seat.** `Household` holds transient caches and version counters (`_done_seq`, `_cap_factor`, `_revenue_cache_key`, `_material_demand_cache` and the like, set in `Household.__init__`). One `Household` facade per seat, created with the seat and swapped by `act_as`, keeps them separate. A shared facade would serve one seat's capability factor to another.
- **Generation is by data.** Seat creation is a function from a seat template (`starting_capital`, `country`, `location`, `starting_techs`, `goal`) to a `SeatState`, the same way `CastEntry` seeds actors from data (`sim/agents/cast.py`). No seat id is named in engine code (CLAUDE.md 4.7).

Rejected alternatives:

- *Rewrite call sites to `state.seat(seat_id).household`.* Every site the table counts, plus most of the test lines that name the household, for no behaviour. It also makes every mixin method take a seat argument, which is the decomposition `sim/ARCHITECTURE.md` rejected.
- *One `Sim` per player.* Players would not share a market, a rng, a population or a year. The point is one world.
- *Make every second player a `Player` record.* Cheapest to start, but it leaves two player models (founder with projects and staff hours, others without) and every future mechanism would need both. Section 5 keeps `Player` for lightweight NPC-like actors and AI rivals, and this plan makes seats the human and LLM path. Whether to retire `Player` later is an open question.

### 2.2 Which fields move

The authoritative lists are the dataclasses in `sim/engine/state.py` and `sim/engine/state_seat.py`. The rule, from `SIM_STATE_INVENTORY.md`: HOUSEHOLD moves, WORLD, SCENARIO stay.

| State class | Goes onto the seat | Stays world or scenario |
|---|---|---|
| `HouseholdState` | all of it: purse, cash book, cause book, staff pools, `employees`, trades taught, contract hours, standing (`reputation`, `scandal`, `eminence`, `familiarity`, `protection`), slaves and freedmen, bondage, credit freeze, saving target, log, `base_tile`, hour allocations, training queue, `labour_pressure_records`, and the `_said_*` markers | nothing, with one exception below |
| `ProjectsState` (gone: its fields live in the seat's `SeatProgressState` and the module slots of `SeatState`) | all of it: `active`, `done`, `done_year`, `operating`, `failed_attempts`, `mothballed`, `bountied`, `granted` (a copy made at seat creation from the seat's country), `revealed`, `disclosures`, `keep_staffed`, `excluded`, `closures`, staffing tallies | nothing |
| `FounderState` | all of it: `founder_alive`, `life_left`, `dead_reason`, `policy`, living cost, director hours | nothing |
| `EconomyState` | the owner-held part: `mines`, `mine_pending`, `mine_ready`, `mine_cost_paid`, `mine_tranches`, `shortages`, `throttle`, `binding`, `shortage_condition`, `forest_ha`, `nitre_bed_m2`, `market_pressure`, `_material_stock_ledger`, `_material_stock_opening`, the `farm_*` fields, `material_demand_at_last_throttle`, `_dashboard_history` | `agent_economy`, `output_factor`, `output_per_head`, `introduction_prices`, `money_real`, `market_book`, `market_flows`, `foreign_market_book`, `foreign_actor_trade`, `home_actor_trade`, `foreign_ledger`, `foreign_trade_by_year`, `capacity_pool`, `society_labour_hours` |
| `GovernanceState` (gone) | `inst_units`, `gov` | none |
| `ScenarioState` | `goal_year`, `goal_years`, the `_said_*` markers about one seat's own state (`_said_scandal`, `_said_parallelism`, `_said_command_index`, `_said_explanations`), `score_last_seen`, `dashboard_history_years` | `year`, `weather_salt`, and the markers about the whole society (`_said_debasement`, `_said_output`, `_said_wage_cascade`, `_literacy_said`, `_said_condition`) |
| `PopulationState` | none | all of it |
| root fields | `_goal` (the seat's chosen win node) | `_civ`, `_civ_live`, `_weights`, `_fog` (the switch for the whole game), `_fuzzy_*`, `_immortal`, `_rng`, `_seed`, `interface` |

Judgement calls (the inventory flagged each as ambiguous):

- `granted` is a civilisation fact. It stays a per-seat field, seeded from the seat's country profile (`CountryProfile.starting_techs`) and checked by a test against that profile, because every capability, practice and node-visibility read already goes through `projects.granted` and the alternative is another indirection on the hottest set.
- `trades_created`, `trades_endemic`, `trade_introduced_year` stay on the seat that taught the trade. What is world-level is the fact "this society now supplies the trade on its own", which `society_adoption.py` already derives; a second seat reads the world fact, not the first seat's list. Whether a second seat inherits a taught trade is a rule in the labour market (a trade a society has endemic is hirable by anyone), not a stored copy.
- `goal`: a win condition is the seat's. The CLI's session-wide `--goal` seeds the first seat's goal. Game end with several seats is an open question.
- `shortages` is a diagnostic for the holder; it moves with the holdings.
- `dead_reason` and `founder_alive` become per seat. The run ends when the policy chosen for the game says so (open question), not when the first seat dies.

The one `HouseholdState` exception: `labour_pressure_records` and the wage ledgers belong to the labour core's employer record once 428 lands (an employer named by seat id). They stay on the seat as the seat's side of that record. The core's `Bid.employer` is the seat id.

### 2.3 How commands address a seat

- The protocol line gains an optional `"as": "<seat_id>"`. Absent means the session's seat, which is the first seat for every existing script, so every current protocol test passes unchanged.
- `agent --seat <id>` and `play --seat <id>` fix the session's seat for a whole process. Two LLM players are two processes, or one process using `"as"`, in turn.
- Dispatch wraps the handler in `with sim.act_as(seat)`. One place: `sim/ui/proto/dispatch.py` (its command registry in `command_registry.py`). Handlers keep reading `sim.household`.
- Reads that are about a seat (`state`, `status`, `available`, `log`, the dashboard) show the addressed seat. Reads that are about the world (`market`, `population`, `society`) are the same for every seat. Render code that says "the founder" says the seat's name.
- Unknown seat id, or a command from a dead seat that needs a living holder, is `{"ok": false, "error": ...}` like any refusal.
- Turn order: stage E is hot seat. The year advances when `step` is called, and `step` advances every seat. A shared-file multiplayer (several processes against one save) needs a lock and a "ready" set; that is a server problem and is not in this plan (open question).

`save/load` with `--session`: every command is a save then a load. `seats` is part of the saved state, so a session file holds all seats; `acting_seat` is saved so a resume binds the aliases. Per CLAUDE.md 4.6, old saves simply do not load; no shim, no version stamp.

### 2.4 Fog and knowledge become per seat

What is per seat already, by living in `ProjectsState`: `revealed` (the ratchet set, `fog.py`), `done`, `done_year`, `failed_attempts`, `disclosures`. Moving `projects` onto the seat makes fog and knowledge per seat with no change to `fog.py`'s reads (it is a mixin reading `self.state.projects.revealed`).

What needs real work, in `sim/knowledge/` and `sim/diffusion/`:

- **Visibility between seats.** Today the founder's work reaches observers through `world.exposure(node, location)` and actors copy under fog. A seat is an observer of other seats exactly as a firm is: what seat B can learn of seat A's concern is `exposure(node, B.location)`. Seat A's `disclosures` (secret, license, publish) already say who may copy; licensing to another seat uses `licensable_actor_ids()`, which must list seats.
- **Diffusion counts all seats.** `society_diffusion.py` counts "founder-built done nodes" when it measures what the society could imitate. It must count the union of seats' built nodes (excluding `granted`), so a second seat's invention can spread. This is the only world mechanism whose meaning changes.
- **Hazards read the seat.** Confiscation, notice and denunciation risks scale with a holder's wealth and standing (`society_hazards.py`, `society_state_pressure.py`). They loop over seats, each against its own household. World hazards (plague, war, output factor) roll once.
- **`fog` the switch is a game option** (`_fog` stays root). What each seat sees is its own `revealed`.

### 2.5 What stays world state

Calendar, population and demography, price and wage levels of the economy, the goods market (its book is keyed by party id already, so several seats are several parties, not several books), the agent economy's record, foreign ledgers, the rng, the dated shocks, the tree (`nodes`, `order`) and configuration. Mods and scenario data stay in `sim/engine/mods*.py` and the civilisation file. The principle: if a rule is about who holds a thing, it moves; if it is about what everyone faces, it stays.

---

## 3. Steps 4 and 407: partner countries as economies

### 3.1 What exists

`CountryWorld` (`sim/agents/country_view.py`) answers `pay_per_person_year`, `society_output`, `subsistence_cost_per_person_year` and `housing_cost_per_person_year` by multiplying the home answer by a ratio of `CountryProfile` fields (`wage_index`, `price_index`, `population`). `sim/economy/foreign.py` treats partners as external sellers and buyers booked against `EDGE_EXTERNAL`, with an `external_orders` function; its own docstring says partner economies are not agents yet. `foreign_economies.py` and `foreign_payments.py` keep partner market books and a dict ledger. `data/world/foreign_economies.json` enables an economy per civilisation file and keeps its technology frozen.

### 3.2 One labour market, quoting per area, not one market per country

The labour core (`sim/labour/market/`) is keyed by **labour area** throughout: people per area x trade x ability band, per-area subsistence (`YearInputs.subsistence_per_worker_year`), per-area entrants and attrition, `Bid.area`, `School.area`, and `Route(destination, moving_cost)` between areas. A country is a set of areas. So:

- Each country's labour areas are prefixed by the country id (the agent economy already prefixes areas with `LABOUR_AREA_PREFIX` in `sim/economy/setup.py`). The one market instance stays.
- Migration between countries is the core's existing migration over routes, with a moving cost that includes the border and the freight leg. No second mechanism.
- Training, trade specs and the aptitude model are shared (a trade means the same thing everywhere), which a market per country would duplicate and let drift.
- Pay is quoted per area: `quote(trade, area)` instead of the single-area `quote_annual(trade)`. This is the one new surface on `sim/labour/api.py` and on the `sim.labour.market` object. It belongs in a change to `sim/labour/`, not in `country_view.py`, and it needs 428 first, because 428 is what makes the running game call the core at all (`DESIGN.md` still says "Nothing in the running game calls it yet").

Money: the core says "Money is whatever unit the caller's wages and subsistence costs are given in". Each area's subsistence is stated in the area's own coin, and the choice of a worker to migrate compares log of expected wage over subsistence, which is unit-free. The moving cost is the only place a conversion appears, converted once at the route. This matches `sim/economy/currency.py` (`CurrencySpec` per money) and `Complaints/reports/agent-economy-several-moneys.md`, which this plan does not re-decide. The scalar conversion stays until a currency per country exists.

### 3.3 Output measure per country

`society_output()` for a country becomes the sum of what its own producers and households make at its own prices, from its own record in the agent economy, using the same real-output measure the home economy uses (`sim/reporting/output.py`, `EconomyState.output_per_head`). It is not home output times a ratio. The partner's producers are the economy's `Producer` records for the country's tiles; the data for that is what Complaints 324 and 350 already ask for (sourced output per region). Until a country has them, `society_output()` for that country answers `None` and its callers (revenue of the foreign government, strata incomes) fall back to the labelled heuristic that exists now. This keeps the game running while countries are filled in one at a time.

Food and housing costs likewise come from the country's own price solve (`foreign_economies.py` already prices a partner's goods from its civilisation file); the `price_index` ratio is replaced by the country's own subsistence basket cost. `housing_cost` forwards to the country's land and building prices, which exist once land is a market (`sim/economy/land_market.py`).

### 3.4 CountryWorld after the change

`CountryWorld` stops rescaling. For these four questions it forwards to the country's economy through the world's economy object (a `country_economy(country_id)` member on the shared world, `sim/actors/world_people.py`, because `sim/agents/` may not import `sim/economy/`), and what it answers for a country with no economy yet is the old heuristic, still labelled. The fallback and its helpers are gone: a country with no part of the economy raises `NoCountryEconomy` (`sim/agents/no_country_economy.py`).

### 3.5 Players from other countries

A seat whose `country` is not the home one needs the engine's own country-dependent figures (price level, wage level, geography home, civilisation values, the state it pays tax to) to come from that country. Those are `Sim` fields today (`price_index`, `wage_index`, `civ`, `_home_centroid`, `state_capacity`). The route is: `act_as` also binds a **country view** for the seat (the economy's answers for its country), and the few engine reads of `sim.price_index` and friends go through it. This is the riskiest stage and comes last (stage I). Until then a second seat is a second player of the same country, which is enough to test every other part.

---

## 4. Stages

Stages A to I are built, but not all as the sections above describe them; each line below says what exists. Each line says where the result lives; re-find any name with `grep -rn <name> sim`. The
whole-game runs (`python3 -m sim.tests --slow` and the fingerprint) are the orchestrator's to run before a merge.

- **A, a seat record and the alias.** `SeatState` (`sim/engine/state_seat.py`), `act_as` and `add_seat`
  (`sim/engine/seat_registry.py`). There are no root `household`, `projects` or `founder` fields: they are build-only arguments of `SimulationState`
  (`sim/engine/state.py`) that make the first seat, and the acting seat's record is `state.acting_record`. A save
  holds `seats` and `acting_seat`. There is no `ProjectsState`.
- **B, world and seat holdings.** `HoldingsState` and `SeatProgressState` (`sim/engine/state_holdings.py`) are seat
  parts; there is no `GovernanceState`. `EconomyState` keeps only world fields and `ScenarioState` only the
  calendar, weather salt and society-wide notes.
- **C, one party identity.** The asking party is `state.acting_seat`; `HouseholdParty` (`sim/agents/household_party.py`; there is no `SeatParty` or `FounderParty`) runs every act as its seat, the posted
  price leaves out only the asking seat's flows, and lenders and borrowers are per seat.
- **D, a second seat and the year steps every seat.** `sim/engine/year_run.py` orders the year: world phases once under
  the first seat still in play, seat phases for each seat in join order inside `act_as`; `sim/seats/run.py` ends a seat's
  run alone. A seat is built from data (`seat_from_template` in `sim/engine/state_seat.py`, `join_seat` in `sim/seats/run.py`, the civilisation's `cast.seats`). Known
  limits: the society's farm workforce is sized under the first seat in play; interest groups' blame and the state's
  petitions land on the seat acting when they fire; seats share one random stream, so an idle second seat changes later
  dice for the first.
- **E, commands address a seat.** `"as"` on any command (`sim/ui/proto/seat_address.py`), `--seat` on `agent` and
  `play`, `seats` and `join` commands, the state screen names the seat; `sim/PROTOCOL.md` has the section.
- **F, fog, knowledge, disclosure between seats.** Fog and `revealed` are each seat's own. A seat hears of another's work
  only when enough of it shows at its distance (`sim/seats/sight.py`, `sim/seats/sight_rules.py`; a secret never shows
  enough). The society's diffusion counts every seat's work. Licences go to firms, the state and other seats.
- **G, partner countries enter the agent economy.** Behind the `enabled` flag of each economy in
  `data/world/foreign_economies.json`; tiles carry a country and each country's producers are placed by the economy's own
  opening.
- **H, a labour quote per area.** `LabourMarket.quote_annual_in`; `CountryWorld` answers pay, output and cost of living
  from the country's own part of the economy (`sim/economy/country_figures.py`) and raises `NoCountryEconomy` for a country not in the
  economy; there is no scaling fallback.
- **I, a seat from another country.** The acting seat's country sets the wage, the prices and the state it deals with
  (`acting_country` in `sim/seats/run.py`, `state_treasury` in `sim/actors/cast.py`). The engine's own price level, state capacity and geographic home still read
  the game's country, so a partner seat's costs that come from them are the home's.
- **Seat dealings (Complaint 103).** A seat holds patents, shares held and its own issued equity in `HoldingsState`;
  `seat_party(seat_id)` (`sim/actors/seat_parties.py`) is the actor an exchange deals with. The commands `patent`, `offer`, `offers`, `accept`,
  `decline` and `shares` address the acting seat through `sim/seats/dealings.py` and
  `sim/ui/proto/dispatch_dealings.py`.

## 5. Where `Player` and the cast fit


`Player` records stay: AI rivals, scripted opponents and strata-like actors in a scenario need a cheap actor. A seat is the full model for a person who plays. A seat is not an `ActorRecord`, but it presents the surface an exchange needs through `HouseholdParty` (`sim/agents/household_party.py`), which already does this for the founder; stage C generalises its `actor_id`. So firms and the state deal with a seat as they deal with any actor, and `ActorsState.cast` may list a seat's template under a `"seats"` entry so a Rome start and a Han start differ in data, not in code.

---

## 6. Risks

- **Alias drift.** A cached reference to a seat's object across `act_as`. Mitigation: only the year loop and dispatcher enter `act_as`; a test with two seats that mutates through a captured reference and checks the right seat changed; pylint-level review of `act_as` call sites.
- **Hidden single-seat reads.** Engine code that reads `sim.household` in a world phase (for instance the market closing reading the founder's draws). The year loop runs the world phases outside any seat, with the root aliases pointing at the first seat; a world phase that reads them is silently first-seat-only. Mitigation: bind the aliases to a sentinel in the world phases under a debug flag (`Sim.debug`, which already runs invariants) so any such read raises, then fix each.
- **Fingerprint blindness.** `fingerprint` checks one-seat behaviour only and does not cover the protocol layer (CLAUDE.md section 6). Two-seat behaviour needs the new tests.
- **Rebase cost.** Stages A and B edit a few hot files (`core.py`, `state.py`). Keep each PR small and merge quickly; do not hold stage A open across the 382 step 1 merge.
- **Order dependence in the year.** Fixed seat order and one market close is a design, not a proof; a two-order test for non-trading seats catches regressions only for that case.
- **A partner economy filled in unevenly.** Countries with some data and not other data produce `None` answers. The heuristic fallback must stay labelled (CLAUDE.md 4.4) and its use must be counted (`python3 sim/constants.py --burndown`).
- **Player death and the run.** The run today ends with the founder's death or bankruptcy. Several seats need an end rule or the first death ends everyone's game.
- **Save size and speed.** Each seat adds a household's worth of state to every save and every `--session` command. Measure the save file and command time for two seats before adding more.

## 7. Open questions

1. Is the second player a full seat (this plan) or should `Player` grow staff, projects and fog until it is the same thing? The plan chooses the seat; confirm.
2. What ends the game with several seats: every seat done or dead, the first goal reached, a fixed horizon? It decides `dead_reason`, `goal_year` and the run's report.
3. Real concurrency: several processes, one save? This needs a lock and a ready set per year, or a small server. Not in scope; hot seat first. Who owns that decision?
4. Do seats of one country share a labour pool and a market fully (they will, in this plan), and do they see each other's wage offers under fog? The labour core has no fog.
5. A seat of one country in a different country's economy (a foreign merchant house in Rome): the seat's `country` is its origin, its holdings are in some area. Is that area's country the economy it hires in? The plan says yes; confirm with the owner decisions on foreign actors.
6. Naming: the seat's `Household` facade and `FounderState` are named for one family and one mortal person, while `sim/economy/households*` are cohorts of the same word. Rename the facade to the seat and `FounderState` to something owner-neutral now (a mechanical rename, cheaper before more seats exist), or later? The field-level mortal-person flags in `SIM_STATE_INVENTORY.md` section 6 apply (`life_left`, `director_hours_spent_founder`, `policy.auto_court_heir`, `living_cost_paid`).
7. Seat creation at game start versus a `join` command mid-game (Complaint 401). A mid-game join needs a starting purse and techs rule that does not hardcode an outcome (CLAUDE.md 4.1); starting capital might be a share of the seat's country's `society_output()` once that is real.
8. Should a seat's `granted` be a copy or a read of its country's `starting_techs`? The plan copies for read speed; if the copy must be kept in step with a mod patch, make it a read.
9. Exchange rates: stage H keeps one scalar conversion at the route. When does Complaint 392's several-moneys design replace it, and does that precede stage I?
10. Does stage G need 382 step 2 first (partner cohorts), or can partner areas start with the current household model? The plan assumes step 2 is merged; if not, G waits.

## 8. How to re-measure

Re-run every command in the table in section 1 and update its count and the date. The per-class field counts come from the `python3 -c` line after the table. After stage A a root alias must not be serialized, and after stage B a holder-owned field must not be read through `state.economy`; neither is checked by a test, so re-run the greps.
