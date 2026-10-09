# Plan: per-actor state, then partner countries as economies

**Status:** design, written 2026-10-06 against branch `structural-dedupe-and-owner-decisions`. Nothing here is built.
**Covers:** Complaint 382 step 3 (per-actor household, project and knowledge state, so a second player can exist), Complaint 382 step 4 and Complaint 407 (partner countries as economies with their own labour market and output).
**Comes after:** 382 step 1 (every money posting names a counterparty), 382 step 2 (households as cohort actors) and 428 (the labour core sets the agent economy's wages). Those are in flight; this plan says where it must wait for each.

Every count below was produced by the command beside it, on the date in the table heading. Re-run before acting; counts drift.

---

## 1. Where the single founder is wired in today

The household is already a facade. `sim/agents/household.py` (`Household`) holds no persistent state: it reads and writes the live `SimulationState` through a field map. The saved state is one dataclass per subsystem, and `SimulationState` holds exactly one of each. So "one founder" is not a class problem, it is that the root holds one `household`, one `projects`, one `founder`, and the engine reads them through the root.

Four facts decide the design:

1. **The root fields are read directly almost everywhere.** `self.state.household.x`, `self.state.projects.x` and `self.state.founder.x` are called from the engine, the packages and the UI. Rewriting those to take a seat argument is the largest possible diff and the one `HOUSEHOLD_EXTRACTION.md` already measured as costly (an indirection per access on the hot path, and every call site touched).
2. **`EconomyState` mixes two things.** Market books, foreign ledgers and the agent economy's record are world state. Mines, forest, nitre beds, farm hectares, the material stock ledger, `throttle`, `binding` and `shortages` are what one holder owns. Today the holder is the founder.
3. **A second kind of player already exists, but a thin one.** `Player` (`sim/agents/player.py`, `ActorRecord`) has a purse, knowledge, concerns and works, and queues orders. It has no staff hours, no project engine, no fog, no standing, no log. It is a copy-research actor, not a founder. Giving a human a thin record would make the second seat a different game from the first.
4. **The party id is a string constant in several places** (`FOUNDER` in `goods_market_api.py`, `FOUNDER_AGENT` in `economy_port_year.py`, `FOUNDER_ACTOR_ID` in `household_party.py`, `FOUNDER_LOAN` in the capital market). They are the same idea spelled four times.

`SIM_STATE_INVENTORY.md` was measured before the typed state existed. Its field names are right and its category column (HOUSEHOLD, WORLD, SCENARIO, INTERNAL) is still the classification used here, but its "first set" and "file count" columns describe `Sim` attributes that are now state fields. The fields to move are listed from the dataclasses below, not from that table.

### Measurements (2026-10-06, branch `structural-dedupe-and-owner-decisions`, test files excluded unless stated)

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

Fields per state class: `python3 -c "import dataclasses; from sim.engine import state as s; [print(c.__name__, len(dataclasses.fields(c))) for c in s.ALL_STATE_CLASSES]"` (household 69, projects 21, economy 38, governance 2, founder 9, scenario 15, population 5, actors 5 on the date above).

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
- **Generation is by data.** Seat creation is a function from a seat template (`starting_capital`, `country`, `location`, `starting_techs`, `goal`) to a `SeatState`, the same way `CastEntry` seeds actors from data (`sim/agents/agents_port_cast.py`). No seat id is named in engine code (CLAUDE.md 4.7).

Rejected alternatives:

- *Rewrite call sites to `state.seat(seat_id).household`.* Every site the table counts, plus most of the test lines that name the household, for no behaviour. It also makes every mixin method take a seat argument, which is the decomposition `sim/ARCHITECTURE.md` rejected.
- *One `Sim` per player.* Players would not share a market, a rng, a population or a year. The point is one world.
- *Make every second player a `Player` record.* Cheapest to start, but it leaves two player models (founder with projects and staff hours, others without) and every future mechanism would need both. Section 5 keeps `Player` for lightweight NPC-like actors and AI rivals, and this plan makes seats the human and LLM path. Whether to retire `Player` later is an open question.

### 2.2 Which fields move

The authoritative lists are the dataclasses in `sim/engine/state.py` and the field map in `sim/agents/household.py` (`_SUBSYSTEM_MAP`). The rule, from `SIM_STATE_INVENTORY.md`: HOUSEHOLD moves, WORLD, SCENARIO stay.

| State class | Goes onto the seat | Stays world or scenario |
|---|---|---|
| `HouseholdState` | all of it: purse, cash book, cause book, staff pools, `employees`, trades taught, contract hours, standing (`reputation`, `scandal`, `eminence`, `familiarity`, `protection`), slaves and freedmen, bondage, credit freeze, saving target, log, `base_tile`, hour allocations, training queue, `labour_pressure_records`, and the `_said_*` markers | nothing, with one exception below |
| `ProjectsState` | all of it: `active`, `done`, `done_year`, `operating`, `failed_attempts`, `mothballed`, `bountied`, `granted` (a copy made at seat creation from the seat's country), `revealed`, `disclosures`, `keep_staffed`, `excluded`, `closures`, staffing tallies | nothing |
| `FounderState` | all of it: `founder_alive`, `life_left`, `dead_reason`, `policy`, living cost, director hours | nothing |
| `EconomyState` | the owner-held part: `mines`, `mine_pending`, `mine_ready`, `mine_cost_paid`, `mine_tranches`, `shortages`, `throttle`, `binding`, `shortage_condition`, `forest_ha`, `nitre_bed_m2`, `market_pressure`, `_material_stock_ledger`, `_material_stock_opening`, the `farm_*` fields, `material_demand_at_last_throttle`, `_dashboard_history` | `agent_economy`, `output_factor`, `output_per_head`, `introduction_prices`, `money_real`, `market_book`, `market_flows`, `foreign_market_book`, `foreign_actor_trade`, `home_actor_trade`, `foreign_ledger`, `foreign_trade_by_year`, `capacity_pool`, `society_labour_hours`, `wage_tightness_factors` |
| `GovernanceState` | `inst_units`, `gov` | none |
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

What needs real work, in `sim/engine/fog.py`, `society_diffusion.py`, `society_adoption.py`, `society_disclosure.py`, `agents_port_disclosure.py`, `knowledge_warning.py`:

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

Money: the core says "Money is whatever unit the caller's wages and subsistence costs are given in". Each area's subsistence is stated in the area's own coin, and the choice of a worker to migrate compares log of expected wage over subsistence, which is unit-free. The moving cost is the only place a conversion appears, converted once at the route. This matches `sim/economy/currency.py` (`CurrencySpec` per money) and `Complaints/reports/agent-economy-several-moneys.md`, which this plan does not re-decide. The scalar conversion in `sim/engine/foreign_payments.py` stays until a currency per country exists.

### 3.3 Output measure per country

`society_output()` for a country becomes the sum of what its own producers and households make at its own prices, from its own record in the agent economy, using the same real-output measure the home economy uses (`sim/engine/real_output.py`, `EconomyState.output_per_head`). It is not home output times a ratio. The partner's producers are the economy's `Producer` records for the country's tiles; the data for that is what Complaints 324 and 350 already ask for (sourced output per region). Until a country has them, `society_output()` for that country answers `None` and its callers (revenue of the foreign government, strata incomes) fall back to the labelled heuristic that exists now. This keeps the game running while countries are filled in one at a time.

Food and housing costs likewise come from the country's own price solve (`foreign_economies.py` already prices a partner's goods from its civilisation file); the `price_index` ratio is replaced by the country's own subsistence basket cost. `housing_cost` forwards to the country's land and building prices, which exist once land is a market (`sim/economy/land_market.py`).

### 3.4 CountryWorld after the change

`CountryWorld` stops rescaling. For these four questions it forwards to the country's economy through the world's economy object (a `country_economy(country_id)` member on the engine adapter `SimWorld`, because `sim/agents/` may not import `sim/economy/`), and what it answers for a country with no economy yet is the old heuristic, still labelled. When no country needs the heuristic, `_relative`, `_home_profile` and the `TEMPORARY HEURISTIC` docstring are deleted, and `sim/tests/test_one_labour_market.py`'s check is extended to catch the helper form (any call to `pay_per_person_year` whose result is multiplied by a profile figure, or any use of `profile.wage_index` outside the opening), since today it only sees a direct `.wage_index` product.

### 3.5 Players from other countries

A seat whose `country` is not the home one needs the engine's own country-dependent figures (price level, wage level, geography home, civilisation values, the state it pays tax to) to come from that country. Those are `Sim` fields today (`price_index`, `wage_index`, `civ`, `_home_centroid`, `state_capacity`). The route is: `act_as` also binds a **country view** for the seat (the economy's answers for its country), and the few engine reads of `sim.price_index` and friends go through it. This is the riskiest stage and comes last (stage I). Until then a second seat is a second player of the same country, which is enough to test every other part.

---

## 4. Staged plan

Each stage ends with the game playable (one seat, as today), the full suite green (`python3 -m sim.tests`, and `--slow` before the pull request), and `python3 -m sim.tests.fingerprint check` identical for the single-seat reference scenarios, unless the stage says what it changes on purpose. Every stage is test-first (CLAUDE.md section 6).

Files named are the ones a stage edits. A new small module is preferred to growing a large one (CLAUDE.md section 5), so new files are named too.

### Order relative to the in-flight branches

| In flight | Branch | Effect on this plan |
|---|---|---|
| 382 step 1 (counterparties) | `every-posting-names-a-counterparty` | Edits about forty founder postings in the same engine files stages A, B and C touch. **Stages A to D wait for it to merge** (rebase conflicts in `economy*.py`, `society*.py`, `core.py` otherwise). Stage F and stage E need not wait. |
| 382 step 2 (households as cohort actors) | not yet a branch name | Independent of seats for stages A to F. Needed before G (partner cohorts reuse the mechanism). Name clash to resolve: the seat's `Household` facade versus `sim/economy/households*` cohorts (open question 6). |
| 428 (labour core sets the agent economy's wages) | `labour-core-sets-economy-wages` | Needed before H (per-area quote). Stage C must use the same employer id 428 uses for the founder; coordinate on `FOUNDER_ACTOR_ID`. Otherwise independent. |

So: A, B, C, D follow 382 step 1; E and F can start as soon as A lands; G can start in `sim/economy/` while A to D proceed (disjoint files), except its engine-side adapter edits, which follow C; H follows 428 and G; I is last.

### Stage A: a seat record and the alias, one seat, no behaviour change

**Status:** built (`sim/engine/state_seat.py`, `sim/engine/core_seats.py`; `sim.act_as(seat)`, `sim.add_seat`). `state.household`, `.projects`, `.founder` alias the acting seat and are not saved; `state._goal` is the acting seat's goal; a save holds `seats` and `acting_seat`. Stage B is built (below).

- New: `sim/engine/state_seat.py` (`SeatState`, `act_as`, alias binding); edits: `sim/engine/state.py` (`seats`, `acting_seat`, alias metadata, `get_save_fields` and `serialize_state` skip aliases), `sim/engine/saveload.py` (bind aliases on load), `sim/engine/core.py` (`__init__` builds the first seat), `sim/engine/core_properties.py`, `sim/agents/household.py` (one facade per seat).
- Tests (new `sim/tests/test_seat_state.py`): the root objects are identical to the first seat's; `act_as` restores on exception; a save round trip keeps one seat and the aliases rebind; a saved file does not contain the aliased fields twice; fingerprint check identical; `test_household_never_happened_fields.py` still passes (absent stays absent).

### Stage B: split `EconomyState`, `GovernanceState` and `ScenarioState` into world and seat holdings

**Status:** built. `HoldingsState` and `SeatProgressState` (`sim/engine/state_holdings.py`) are new seat parts; `GovernanceState` moved whole onto the seat. `SeatState` holds `holdings`, `governance` and `seat_progress`; `state.holdings`, `state.governance` and `state.seat_progress` alias the acting seat and are not saved. `EconomyState` keeps only world fields and `ScenarioState` only the calendar, weather salt and society-wide notes. Readers were rewritten (`state.economy.<held>` to `state.holdings.<held>`, `state.scenario.<seat field>` to `state.seat_progress.<field>`), the household facade map and the `Sim` forwarding properties follow, and a save holds the three parts inside each seat. Walls: `sim/tests/test_seat_holdings_walls.py` fails on any read of a seat field through the world part (direct, through a local, or through `getattr`); the field lists are the dataclasses, so they cannot drift. The root name is `seat_progress` rather than the plan's earlier "scenario markers" wording. The founder as an actor with patents and shares is not in this stage: it belongs to stage C (one party identity, `HouseholdParty` generalised to the seat id) and stage D. Not run: fingerprint, and the whole-game topics that touch the moved fields (CLAUDE.md and the task rules forbid building a game here); run `python3 -m sim.tests --slow` before the pull request.

- Edits: `sim/engine/state.py` and `state_seat.py` (the `holdings` class); read sites for the moved fields (counted in the section 1 table, listed by the grep below), and the test references.
  `grep -rnE "state\.economy\.(mines|mine_pending|mine_ready|mine_cost_paid|mine_tranches|shortages|throttle|binding|shortage_condition|forest_ha|nitre_bed_m2|market_pressure|_material_stock_ledger|_material_stock_opening|farm_[a-z_]+|material_demand_at_last_throttle|_dashboard_history)\b" sim --include=*.py`
- Mechanical: becomes `state.holdings.<field>`; a Haiku-sized task with a stated pattern.
- Tests: a lint test (extending the existing walls tests) that fails when a field listed as holder-owned is read through `state.economy`; the existing test references updated; fingerprint identical.

### Stage C: one party identity for the goods market, the agent economy, credit and the capital market

- Edits: `sim/engine/goods_market_api.py` (`FounderParty` becomes `SeatParty(seat_id)`; `FOUNDER` constant replaced by the party id of the seat acting; the "others only" exclusions at the lines using `party != FOUNDER` become "other than the asking party"), `sim/engine/market_clearing.py`, `sim/engine/agents_port_groups.py`, `sim/engine/economy_port_year.py` (`FOUNDER_AGENT` becomes the seat id; one agent per seat in the agent economy), `sim/engine/economy_capital_market.py`, `sim/engine/economy_credit.py`, `sim/engine/founder_sales.py`, `sim/agents/household_party.py` (`FOUNDER_ACTOR_ID` stays as the first seat's default).
- Tests: two parties with different seat ids buy and sell in one commodity without colliding in the year's flows; the posted price excludes only the asking seat's own orders; credit limit is per seat (two seats borrowing do not share a limit); single seat fingerprint identical.

### Stage D: a second seat exists, and the year steps every seat

- Edits: `sim/engine/state_seat.py` (a `seat_from_template` function), `sim/agents/cast.py` and `sim/engine/agents_port_cast.py` (an optional `"seats"` key beside `"cast"` and the join command that Complaint 401 names), `sim/engine/core.py` (`step()` loops the seat phases), `sim/engine/core_step_phases.py` and `step_phase_money.py`, `step_phase_staff.py`, `step_phase_projects.py`, `step_phase_project_start.py` (no logic change; they run inside `act_as`), `sim/engine/society_hazards.py` and `society_state_pressure.py` (loop seats).
- Phase classification, from `Sim.step`: **per seat** (inside `act_as`, in a fixed seat order): apprenticeships, staff, money, teach trades, standing work, start projects, materials, progress, wage fallback, reputation, bondage, founder mortality, living stock, the credit-limit enforcement. **World, once**: dated shocks (which then apply to each seat's household), the market closing (it must run after every seat's draws and sales, which the party-keyed flows book already supports), random events, the calendar increment.
- Order effect: seats run in a fixed order, and the market is cleared once after all of them, so a seat does not see another's draws within the year. If a mechanism reads another seat's mid-year state, that is a bug to fix by reading last year's, not by ordering.
- Tests: **an idle second seat changes nothing for the first** (same year-end purse, projects, log; market flows differ only by the second seat's own living costs and nothing else); money is conserved across a year for two seats apart from named edges (extends the `ledger.transfer` conservation test described in `sim/agents/MULTIPLAYER.md`); a second seat's research completes in its own `done` and not the first's; seat order does not change the result for seats that do not trade (run both orders).

### Stage E: commands address a seat

- Edits: `sim/ui/proto/dispatch.py` (the single `act_as` wrapper and the `"as"` key), `sim/ui/proto/command_registry.py`, `sim/ui/cli.py` (`--seat`), `sim/engine/ui_port.py` (a member to list seats and set the acting one), `sim/ui/proto/state.py` and `render_screen_state.py` (name the seat, not "the founder"), `sim/PROTOCOL.md`.
- Tests: two seats, the same command with different `"as"` change different households; omitting `"as"` is the first seat; an unknown seat is a refusal; `state` for each seat lists its own concerns; the existing protocol tests pass unmodified.
- Independent of C and D at the file level (UI only); it needs A for `act_as` and D to have a second seat to address, so the first PR can add the wrapper and the refusal tests with one seat, and the two-seat tests land with D.

### Stage F: fog, knowledge, disclosure between seats

- Edits: `sim/engine/fog.py`, `sim/engine/society_diffusion.py`, `society_adoption.py`, `society_disclosure.py`, `sim/engine/agents_port_disclosure.py`, `knowledge_warning.py`, `sim/ui/proto/dispatch_disclosure.py` (licensable ids include seats).
- Tests: seat B's `revealed` is not seat A's; fog hides A's work from B except by `exposure`; A's secret concern cannot be copied by B, a licensed one can for the fee; diffusion counts both seats' built nodes (a node built by B alone diffuses); a seat with the fog off in the scenario sees all.
- Files are disjoint from E and C. It can run in parallel with E once A has landed.

### Stage G: partner countries enter the agent economy as areas, cohorts and producers

- Edits: `sim/economy/setup.py`, `sim/economy/foreign.py`, `sim/economy/opening.py`, `sim/economy/api.py` (a `country_economy` surface), `sim/economy/households*.py` (cohorts per country area, reusing 382 step 2), `sim/engine/economy_port.py`, `economy_port_setup.py`, `foreign_economies.py`, `foreign_payments.py`, `foreign_capacity.py`, `foreign_routes.py`; data: sourced output per region for partner tiles (Complaints 324, 350).
- A country's trade with home becomes goods and money moves between named parties, not `EDGE_EXTERNAL` (which then books only what remains modelled outside).
- Tests: with partner economies on, the home economy's conservation test still holds; a partner cohort's income is its own wage bill (not a scalar of home); a partner's export reduces its own stock; removing a partner (enabled false) restores the current numbers.
- Can start in `sim/economy/` while A to D proceed. The engine-side adapters in this stage (`economy_port*.py`) conflict with C and follow it.

### Stage H: a labour quote per area, `CountryWorld` forwards

- Edits: `sim/labour/labour_market_api.py`, `sim/labour/market/year.py` and `sim/labour/api.py` (a per-area quote member and per-country area registration), `sim/engine/labour_port.py`, `sim/engine/agents_port_budget.py` (`pay_per_person_year` takes the scope's area), `sim/agents/country_view.py`, `sim/agents/protocols.py` (the world protocol's signature), `sim/agents/stratum_year.py`, `government_foreign.py`, `revenue_bases.py`, `budget_lines.py` only if the protocol signature needs it, and `sim/tests/test_one_labour_market.py` (stronger check).
- Tests: a country whose subsistence basket is doubled (by a price shock in its own market, not a profile field) shows a higher wage from its own market and the home wage does not move; the foreign government's revenue follows its country's wage bill; a worker migrates across the border when the real wage gap exceeds the moving cost; the test that no module outside the labour market computes a wage fails on the old `_relative` helper and passes on the new code.
- Needs 428 and G.

### Stage I: a seat from another country

- Edits: `sim/engine/state_seat.py` (country view bound by `act_as`), `sim/engine/core.py` and `core_properties.py` (reads of `price_index`, `wage_index`, `civ` weights and the state's capacity go through the seat's country view), `sim/engine/agents_port.py` (the seat's own `CountryWorld`), `sim/engine/economy_port_year.py` (the seat's agent area).
- Tests: a seat of a partner country pays the partner's wage when it hires, buys at the partner's price, and is taxed by the partner's government actor; the same command from a home seat and a partner seat yields different, correct costs; fingerprint for single-seat unchanged.
- Last: it touches the engine's most shared reads.

### Parallel assignment (disjoint files)

| Agent | Stages | Files it owns |
|---|---|---|
| 1 | A, then B | `sim/engine/state.py`, `state_seat.py`, `saveload.py`, `core.py`, `core_properties.py`, `sim/agents/household.py`, the files listed by the stage B grep |
| 2 | C, then D (after 1) | `goods_market_api.py`, `market_clearing.py`, `economy_port_year.py`, `economy_capital_market.py`, `economy_credit.py`, `founder_sales.py`, `agents_port_groups.py`, `household_party.py`, step phase files, society hazard files, cast files |
| 3 | E | `sim/ui/**`, `ui_port.py`, `PROTOCOL.md` |
| 4 | F | `fog.py`, `society_diffusion.py`, `society_adoption.py`, `society_disclosure.py`, `agents_port_disclosure.py`, `knowledge_warning.py` |
| 5 | G (economy side) | `sim/economy/**` |
| 6 | H | `sim/labour/**`, `labour_port.py`, `sim/agents/country_view.py` and callers |

Agents 1 and 2 are sequential, not parallel (shared state files).

---

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

Re-run every command in the table in section 1 and update its count and the date. The per-class field counts come from the `python3 -c` line after the table. After stage A, add a test that fails when a root alias is serialized, and after stage B, one that fails when a holder-owned field is read through `state.economy`; those make the move self-checking and this document's lists become the tests' lists.
