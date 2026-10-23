# Firms own plants: one business object for every owner

**Status:** plan, nothing built (2026-10-14). Answers `Complaints/510-most-tree-nodes-charge-upkeep-and-make-nothing.md`
and `Complaints/514-the-founders-ventures-and-firms-concerns-are-two-implementations.md`. Sequel to
`ONE_PRICE_OWNER_PLAN.md` (507), whose stage order this plan depends on (section 5).

Owner direction (2026-10-14), kept word for word in meaning:

- A **tech node is knowledge only**. Holding it costs nothing and it earns nothing. It unlocks recipes and plants and
  has a research cost.
- A **business is a firm**, owned by an actor (the founder, a firm, a state, another player), that runs one or more
  **plants**. A plant is one production entry's physical unit, with its own crew and upkeep.
- "Opening lead" means founding or buying a firm that runs lead-smelting plants. How many plants it runs, so its size,
  follows what it can sell.
- One implementation runs every owner's businesses (514).

Rules this plan keeps (CLAUDE.md section 4): no hardcoded outcomes, no content ids in the engine, every transitional
shortcut labelled, no save migration. Every list below was measured on this branch; the command that produced it is
under it. Lists lag the code, so re-run before acting. No numbers are stated; the commands print them.

## 1. Where a node carries upkeep, staff, revenue or a plant

A node is a dict loaded by `sim/engine/data.py` (`python3 -c "from sim.engine import data; print(sorted({k for n in data.load()[0]['nodes'] for k in n}))"`
prints every field). The money fields are **derived**, not authored, for almost every node: `node_revenue.apply_revenue`
fills them from the production entries that name the node (`requires_node` or `operated_by`, found by
`node_output.entries_gated_by`) or, for a node with no output, from a programme figure, a science's staff, or a labelled
share of the build bill (`node_upkeep.unstated_upkeep_hours`, a heuristic).

**There is no `plant` field on a node.** A node's plant is the `capital` list (with `annual_output_at_basis`) of the
entries it gates or operates (`data/production/_SCHEMA.md`), reached through `node_output.output_baskets`. The only
node-level plant fields are `plant_crew_people` (read only by `plant_crew.py`), `annual_output_t`, `annual_labour_hours`,
`annual_consumables`, `garrison`, `electricity_generation`, and `mechanics` (`institution_places`, `staff_capacity`,
`supervision_room`, `state_levy`, ...).

| Field | Meaning today | Writers | Readers |
|---|---|---|---|
| `up_hours`, `up` (money) | yearly upkeep of the node's concern | `node_revenue` (`_apply_output`, `_apply_unlisted_upkeep`), `node_upkeep`, mods via `_up_hours_authored` | see 1.1 |
| `rev_hours`, `rev` | yearly takings at long-run prices | `node_revenue._apply_output`; `validate_node_money` forbids stating it | see 1.2 |
| `cap_hours`, `cap` | plant build cost plus tooling | `node_capital.resolve` | `node_revenue`, `node_capital`, `node_defaults`, `money_units`, `civ_start_check` (measure: `grep -rnw cap_hours sim --include=*.py`) |
| `art`, `sch` | people the node's project needs while researching, and also its operating staff | tree data | see 1.3 |
| `lab`, `mat`, `yrs`, `build_yrs` | research and build cost | tree data | project cost code; stays (research) |

### 1.1 Readers of `up`

Measure: `grep -rnE '\["up"\]|get\("up"[,)]|"up":|\bup_hours\b' sim --include=*.py | grep -v tests`.

- **Charged as a running cost:** `economy_production.upkeep`, `upkeep_by_concern`, `institution_upkeep`
  (the founder's ledger); `economy_port.concern_upkeep` (what a firm or player pays, via `agents_port.upkeep`);
  `economy_credit.py` (seizure price). `economy_electricity.py`, `economy_materials.py` and `commodities.py` read it only as
  "this concern is running and uses materials".
- **Used to decide to close or shed:** `step_phase_money.py` (loss shedding), `economy_credit.py` (seizure and the
  "ways out" advice), `projects_staffing.py` (staffing closure order, auto-open order, mothball), `projects_staffing_shortfall.py`.
- **Used to price opening or restoring:** `projects_ventures.venture_capex`, `projects_venture_quotes.reopen_fee`,
  `projects_ventures._expand_institution`.
- **Used as the test "is this a concern":** `projects_capability.is_concern_node` (so `is_venture`), `ui/proto/techtree.py`,
  `ui/proto/why_material.py`, `step_phase_project_start.py`, `planner.py`, `node_payback_diagnostic.py`, `cause_book.py`.
- **Display:** `ui/proto/state_shut_staffing.py`, `techtree.py`.

### 1.2 Readers of `rev`

Measure: `grep -rnE '\["rev"\]|get\("rev"[,)]|"rev":|\brev_hours\b' sim --include=*.py | grep -v tests`.

- **Credited as takings:** `economy_production.concern_revenue`, `concern_takings`, `ledger_concern_rows`,
  `revenue_sources`; `agents_port.concern_takings` and `entry_gross` (a firm's takings, through `sim.concern_takings`);
  `concern_levy.py`; `projects_venture_quotes.venture_real_earnings`.
- **Used for size and supervision:** `projects_ventures.venture_hands_founder_staffed` (crew floor from revenue),
  `venture_foreman`, `plant_crew.py` (fallback only).
- **Used to decide:** the closing and opening readers of 1.1, plus `projects_completion.py` (reputation bonus),
  `society_diffusion.py` (weights spread by revenue), `projects_capability.py`.
- **Display:** `ui/cli.py`, `ui/proto/techtree.py`, `state_shut_staffing.py`.

### 1.3 Readers of `art` and `sch`

Measure: `grep -rnE '\["(art|sch)"\]|get\("(art|sch)"[,)]' sim --include=*.py | grep -v tests`.

- **Research staffing (stays knowledge):** `projects_starting.py`, `sim/labour/labour_capacity.py`, `labour_training.py`,
  `labour_population.py`, `planner.py`, `fuzzy_estimates.py`, `ui/proto/techtree.py`, `ui/cli_analysis.py`.
- **Operating staff (moves to plants):** `node_output.py` (staff hours that bound a line), `node_upkeep.py`
  (staff places cost), `node_capital.py` (tooling), `node_revenue.py` (cache key), `projects_ventures.py` (supervision crew),
  `economy_production.py` (practice trade), `defence_stores.py` (garrison crew).
- **Validation:** `validate_running_gates.py`, `validate_unlinked_producers.py`.

### 1.4 Nodes that charge upkeep and run no entry

Measure: `python3 -m sim.engine.validate_unlinked_producers` (prints the count, the staffed share, the kinds and the
categories; most are staffed engineering nodes). Reader of that module: `sim/ui/cli.py` (`validate`), `sim/tests/test_twin_nodes_earn.py`.
The target (section 3.4) splits that list into knowledge nodes (upkeep deleted) and product-making nodes (each gets a
production entry).

## 2. Every rule a business follows, and each implementation of it

There are **three** runners, not two. The founder and every other human seat run Sim mixin code (a seat is bound by
`act_as`, `core_seats.py`, so seats use the founder path). `Firm` and `Player` actors run `agents/concern_ops.py`.
A business here is just a node id in a set (`record.concerns`, or `projects.operating`); the size is `record.capacity`
or `governance.inst_units`. Measure the entry points: `grep -rn "def open_venture\|def operate_concern\|def operate\b" sim --include=*.py`.

"Shared" means one function computes the figure for both runners today. "Differs" is what 514 warns about.

| Rule | Founder or seat path (Sim mixin) | Agents path (`Firm`, `Player`) | State |
|---|---|---|---|
| **Crew** (how many, of which trade) | `venture_hands` (supervision share of `art`/`sch`, or the plant's derived hours via `plant_crew`, scholars drop out once `concern_runs_without_founder`), `venture_foreman`, `venture_garrison` | `agents_port.concern_staff` calls the same three, times capacity | Shared number, different meaning: the founder's are people of the household tied up supervising (no wage per concern); a firm hires them and pays wages |
| **Staffing: household versus hiring** | `venture_staff_free` against `household.artisans`/scholars; refusal text `staffing_open_refusal` | `concern_ops.staff_concern` takes from the shared pool (`free_fte`), pays market wage via `concern_wage_bill` | Differs |
| **Supervision** | founder's own hours (`VENTURE_SUPERVISION`, `VENTURE_FOREMAN_SHARE`, both labelled heuristics) | a manager's hours over a span of control (`firm_entry.management_cost`, `carry_concern`) | Differs |
| **Upkeep** | `institution_upkeep`: node `up` times units times price level, occupancy scaling for capability institutions (`INSTITUTION_FLOOR`) | `economy_port.concern_upkeep`: node `up` times cost scale times capacity, plus wages, plus site rent and management | Differs. Suspect: node `up` already contains the crew's pay (`_upkeep_hours_parts` staff), so a firm may pay the crew twice. Measure before stage 3 |
| **Takings** | `concern_revenue` / `venture_real_earnings`: `rev` x units x ramp x price level x market factor x value ratio x learning ratio | `agents_port.concern_takings`: the same `sim.concern_takings` x capacity x market factor x category share (or divided among rivals); skipped where the good sells in the economy's book (`sells_on_book`) | Differs in the market share and in book-versus-estimate; the learning ratio reads the founder's tenure stock for every operator |
| **Ramp** | `venture_ramp`, from `projects.opened_year` | `agents_port.ramp`, from `record.opened_year` | Same formula copied twice |
| **Opening cost and gates** | `venture_capex` (share of project cost, floor of years of upkeep), `running_gate_refusal`, `staffing_open_refusal`, `spending_power("open")` | firm: `imitation.copy_plan` stake plus ramp losses; player: `begin_concern`, no fee and no gate | Differs three ways |
| **Size** | `units`, only for `SCALABLE_INSTITUTIONS`; `_expand_institution`; `auto_expand` | `record.capacity` for every concern; `firm_expansion` grows while return beats cost of capital; ceiling `industry_scale_ceiling` | Differs; the founder's list is a content-id set (also 4.7) |
| **Closure and exit** | manual `close_venture`; `close_unstaffed_ventures`; loss shedding in `step_phase_money` (`auto_shed`); creditor seizure in `economy_credit`; `CLOSED_*` reasons in `projects.closures` | firm: `loss_years`, `weak_years`, `insolvent_years` close the whole firm (`firm_exit.close_firm`); AI player: closes on a negative margin; human player: `close` order | Differs |
| **Mothballing and restore** | `mothball_work`, `restore_work`, `reopen_fee` with `STAFF_CLOSURE_GRACE` discount | none: closing discards size and staffing | Differs |
| **Sale** | `founder_sales.sell_concern` -> `agents/exchange_sale.sell_concern` | same function | Shared (the model for the rest) |
| **Levy, royalty, tax** | `concern_levy_due` (`state_levy` mechanic), patent royalty by disclosure | `government.collect`, `collect_royalty` in `operate_concern` | Differs |
| **Auto opening** | `auto_open_ventures` (policy) | `entry_round`, `firm_entry`, `Player.decide` | Differs, by design (different deciders); the opening itself must be one verb |
| **Credit and seizure** | `economy_credit` (halt, freeze, seizure of concerns) | `borrowing`, `Firm.pay_interest`, `firm_exit` (debt written off) | Differs |
| **Imitation exposure** | `agents_port._proven_concerns_of_acting_seat` (opened long enough and a positive `concern_margin`), node `copy_visibility`, `society_diffusion` weight by `rev` | `Player.proven_concerns` (margin, `is_public`, `exposure`), `Firm` through the registry's totals (`concern_totals`) | Differs |
| **Spin-off** | seat staff leave via `release_seat_staff` | `spinoff.release_leaver` | Same module, a branch for the household |

Files by owner today. Founder: `sim/engine/projects_ventures.py`, `projects_venture_quotes.py`, `projects_open_gate.py`,
`projects_staffing.py` (+ `_report`, `_shortfall`), `projects_completion.py`, `projects_capability.py`, `projects_running_gates.py`,
`industry_concern.py`, `industry_depth.py`, `industry_learning.py`, `concern_levy.py`, `concern_volume.py`, `plant_crew.py`,
`defence_stores.py`, `economy_production.py`, `economy_credit.py`, `step_phase_money.py`, `founder_sales.py`. Agents:
`sim/agents/concern_ops.py`, `concern_totals.py`, `firm.py`, `firm_entry.py`, `firm_exit.py`, `firm_expansion.py`, `entry_round.py`,
`entry_ramp.py`, `spinoff.py`, `exchange_sale.py`, `player.py`, `player_commands.py`, `supply.py`. The bridge between them is
`sim/engine/agents_port.py` and `agents_port_capacity.py`, which already call the founder's functions, so the two share
inputs and diverge on how they are used.

## 3. The target model

### 3.1 The business object

`Business` is a saved dataclass in `sim/agents/` (files `business.py`, `business_plant.py`, `business_crew.py`,
`business_books.py`, `business_closing.py`, each short), published through `sim/agents/api.py`. It holds:

- `business_id`, `owner_id` (any actor id: seat, firm, government, player), `name`, `founded_year`, `tile`;
- `plants`: a list of `Plant`;
- `books`: income and outlays by purpose, per business (so a sale prices its record and a seizure sees its debts).

`Plant` holds `entry_key` (the production entry it runs), `size` (count of the entry's plant, a float so a half-built one
exists), `opened_year`, `state` (`operating`, `mothballed`, `closed`) with `since_year` and `reason`, `crew_found`
(share of the crew staffed), and `margin_history`. Everything else is **derived** from the entry, not stored.

The business owns the rules of section 2 as one set of functions over `(business, owner, world)`: `crew_needed`,
`staff`, `upkeep`, `takings`, `ramp`, `close`, `mothball`, `restore`, `sell_price`, `exposure`. The owner is reached through
the existing `Actor` surface (`money`, `workforce`, `credit`, `debit`); a seat's household is already an `Actor` subclass,
so the founder is an owner like any other. What differs between owners is the **decider** (a command, a policy, an AI),
never the arithmetic.

Where it lives: `ActorRecord.businesses` for firms, players and states; `SeatState.businesses` for seats. Same
dataclass, saved by the automatic mechanism. `projects.operating`, `mothballed`, `closures`, `opened_year`,
`governance.inst_units`, and `record.concerns`, `capacity`, `opened_year`, `staffing`, `margins` are deleted; readers get
views (`owner.businesses`, `plant.state`). The registry's `ConcernTotals` sums plant size by entry across owners.

The plant's physical figures come from one **kernel** in `sim/world/` (`plant_figures.py`, pure functions of an entry,
prices and wages, no engine, no agents): crew by trade from the entry's labour hours (what `plant_crew.derived_hours` and
`node_output.output_baskets` do now), output a year (the smaller of plant capacity and what the crew can work), upkeep (crew
pay is **not** upkeep; upkeep is capital wear and consumables, `node_upkeep.plant_wear_hours`), takings (outputs and energy
sold at the prices the caller passes, less inputs). It takes `input_price_of` and `wage_of` as arguments, so it is the same
cost calculator 507 stage 5 wants, with no solver call inside. The engine adapter passes the economy's prices.

Business size follows sales: the owner adds a plant while the added plant's margin at the economy's price, after the
price falls with its output, beats the cost of capital (`firm_expansion` already states this rule; it becomes the one
growth rule), and closes or mothballs a plant when its margin stays below running cost. No number of plants is stated.

### 3.2 The founder's commands act on the object

| Command (`sim/ui/proto/`) | Acts on |
|---|---|
| `open <product>` (`dispatch_ventures.py`) | founds the founder's business for that product if none, else adds a plant; pays for the plant (the entry's `capital`) and **hires its crew** through the labour market; refuses with the labour market's reason (nobody to hire, no money), not with supervision-hand arithmetic |
| `close <id>`, `mothball`, `restore` | close or mothball a plant or a whole business; release its crew; restore at the entry's reopening cost |
| `sell business <id>` (was `sell concern`) | `exchange_sale` on the business: crew, plants and debts go with it |
| `quote` | the same functions, dry run: plant cost, crew wage, expected takings and the ramp |
| `ventures`, `portfolio`, `stuck`, `available`, `why`, `techtree` | read `owner.businesses`; `available` lists products an owner may open, not nodes |

`projects_ventures.py` keeps only the founder's choices: what to open, how big, whom to put in charge. Automatic opening
and shedding (`auto_open_ventures`, `auto_shed`) stay as the founder's **policy**, a decider calling the same verbs a
firm's decider calls.

### 3.3 Firms, states and seats use the same object

`Firm.operate`, `Player.operate` and the seat's yearly step all call `business.operate(owner, world)`; a state runs
`state_works` businesses the same way. `concern_ops.py` is deleted. `Firm` entry (`entry_round`, `firm_entry`) founds a
`Business` with its first plant. A spin-off founds a business with a copy of the plant. A sale moves the `Business`
between owners.

### 3.4 What the node keeps

Knowledge: prerequisites, research cost (`lab`, `mat`, `yrs`, risk), research staffing (`art`, `sch` read only by project
code), `kb`, traits, `mechanics` that are capabilities of knowing. It **unlocks** entries (`requires_node`) and plants
(an entry's `capital`), and improves yields on entries others run.

Deleted from the node: `up`, `up_hours`, `rev`, `rev_hours`, `cap_hours`, `cap`, `plant_crew_people`, `annual_*`, and the
operating use of `art`/`sch`. `operated_by` on an entry goes: an entry is run by whoever holds the node its
`requires_node` names; "operated by" was the node standing for a plant.

The list from section 1.4 splits:
- **Knowledge nodes** (a method, a standard, a measurement): their upkeep is deleted, nothing replaces it.
- **Product-making nodes** (brushes, lenses, sintered ore, and the twins 504 linked): need a production entry with a
  demand side; `validate` reports a product-making node without one as an error.
- **Institutions** (schools, laws, benefactions): not goods. Proposed as `service` entries whose output is a capability
  (places, schooling flow) with their own crew and upkeep, so they are plants too. Open question 1.

`validate_unlinked_producers` is retired and replaced by a `validate` rule: no node carries a running-cost field; every
node whose `kind` makes a good is named by at least one entry.

## 4. Stages

Each stage merges alone and leaves the suite green. A stage that must not change behaviour is proved by
`python3 -m sim.tests.fingerprint` (record before, check after); a stage that changes behaviour on purpose is proved by
relationship tests (CLAUDE.md 4.2). Every stage also runs `python3 sim/simulator.py validate`, `python3 -m sim.tests`
and, before its pull request, `--slow`. Each stage lists the files it owns; two stages that list the same file run in
sequence.

**Stage 0: the ratchet wall test.** `sim/tests/test_business_wall.py` scans `sim/` with `ast` and fails when a module
outside `sim/agents/business*.py` and `sim/world/plant_figures.py` (a) defines or calls a crew, upkeep or takings
function (a name list in the test: `venture_hands`, `venture_foreman`, `institution_upkeep`, `venture_real_upkeep`,
`venture_real_earnings`, `concern_takings`, `concern_wage_bill`, `plant_crew`, `venture_ramp`, `concern_upkeep`), or (b)
subscripts a node with a money field (`"up"`, `"rev"`, `"up_hours"`, `"rev_hours"`). It starts with an allowlist of
today's offenders, and also fails when an allowlisted file no longer offends, so every stage shrinks the list; stage 5
empties it. Owns: that test only. Proof: it passes now and fails on a deliberate new offender.

**Stage 1: the object and the agents path (fingerprint-proof).** Build `Business` and `Plant` and the rules of
section 2 for firms and players, reading the node figures exactly as `concern_ops` does. `Firm`, `Player`, spin-off,
entry and exchange sale move to it; `concern_ops.py` goes. No behaviour change. Owns: `sim/agents/business*.py`,
`concern_ops.py`, `concern_totals.py`, `firm*.py`, `player*.py`, `entry_round.py`, `entry_ramp.py`, `spinoff.py`,
`exchange_sale.py`, `exchange_commands.py`, `records.py`, `supply.py`, `api.py`, `sim/engine/agents_port*.py` (names only).
Proof: fingerprint unchanged; `test_firm_*`, `test_actor_*`, `test_complaint_462_concern_totals.py` green; new
`test_business_owner_kinds.py`: one business, same capacity and year, run by a firm, a player and a state, gives equal crew,
upkeep, takings and ledger identity (purse = opening + income - outlays, per business and per owner).

**Stage 1 done** (branch `514-stage-1-business-object`). `Business` (`sim/agents/business.py`) holds a list of `Plant`
(`business_plant.py`: entry key, size, opened year, crew found, last margin) and is the `ActorRecord.business` field of
every record, so a firm, a player and a state keep their plants the same way; `concerns`, `capacity`, `opened_year`,
`staffing` and `margins` on the record are gone, and `owner.concerns` is a set view that opens and closes plants. The
agents-path rules are `business_crew.staff`, `business_books.operate`/`carry`/`ramp`/`yearly_costs` and
`business_closing.release_plant`; `concern_ops.py` is deleted; spin-off, entry, firm exit, expansion and exchange sale go
through them. Not yet on the object: `state`/`since_year`/`reason` and `margin_history` on the plant (the founder's path,
stage 3, brings mothballing), the `books` of a business, the kernel (stage 2), and the seat's own plants (a seat is only
a party to an exchange, through `HouseholdParty.release_plant`/`receive_plant`). Allowlist: the four agents entries that
moved behind the object are pruned (`python3 -m sim.tests --only business_wall`); `protocols.py` and `engine/agents_port*`
still name the world-view methods, which stage 3c replaces. Proof: `test_business_owner_kinds.py`, fingerprint unchanged.

**Stage 2: the plant kernel in `sim/world/`.** Move `node_output` baskets, `node_upkeep` plant wear, `plant_crew` and the
capital arithmetic into `sim/world/plant_figures.py`, taking prices and wages as arguments. `node_revenue` becomes a caller,
so node figures are unchanged. Owns: `sim/world/plant_figures.py`, `sim/engine/node_output.py`, `node_upkeep.py`,
`node_capital.py`, `plant_crew.py`, `energy_prices.py` (move only). Parallel with stage 1 (different directories). Proof:
fingerprint unchanged; new `test_plant_figures.py` (relationships: crew hours scale with output; output is the smaller of
plant capacity and crew hours; upkeep rises with plant capital and falls to consumables alone with none; takings are linear
in output prices; no node dict is read), plus `test_concern_supply_derived.py`, `test_concern_volume.py`,
`test_twin_nodes_earn.py`.

*Stage 2 done (branch `514-stage-2-plant-kernel`).* The kernel is `sim/world/plant_figures.py` (crew, takings, upkeep, ramp,
non-crew share) over `sim/world/plant_baskets.py` (entry baskets and line capacities); `node_output.output_baskets`,
`node_upkeep.maintenance_hours`/`non_labour_share` and `node_revenue._apply_output` are adapters over it; `plant_crew.py` is
deleted; `venture_ramp` and `agents_port.ramp` call the one `plant_figures.ramp`. Fingerprint unchanged. Left for later
stages: the adapter names `venture_ramp` and `venture_hands` (still on the wall's name list), the node money-field writers in
`node_revenue`/`node_capital`, `energy_prices.py` (still in the engine; the kernel takes any object with `can_run`, `bought`
and `sold`, so it needs no move yet). Test: `sim/tests/test_plant_figures.py`.

**Stage 3a: the founder's businesses move onto the object (state and verbs).** Seats hold `businesses`; `open_venture`,
`close_venture`, `mothball_work`, `restore_work`, `reopen_fee`, `_expand_institution` call the business; `operating`,
`mothballed`, `closures`, `opened_year`, `inst_units` are deleted. Behaviour changes where paths differed; the winner for
each rule is the agents path unless open question 3 says otherwise. Needs 1 and 2. Owns: `projects_ventures.py`,
`projects_open_gate.py`, `projects_capability.py`, `projects_running_gates.py`, `state.py` (`ProjectsState`, `GovernanceState`),
`state_seat.py`, `seat_*.py`, `core_properties.py`, `founder_sales.py`, `saveload.py` (round trip only), `sim/ui/proto/dispatch_ventures.py`,
`dispatch_money.py` (`close`, `sell`), `ventures.py`, `state_projects.py`. Proof: `test_ventures_lifecycle.py`,
`test_ventures_saves_and_dice.py`, `test_seat_as_actor.py`, `test_saveload*` ported; new `test_founder_and_firm_agree.py`
(the same business owned by a seat and by a firm for one year produces the same crew, upkeep, takings and closing decision
inputs); closing frees its crew and stops its outlays; mothball then restore returns the same plants.

*Stage 3a partly done (branch `514-stage-3a-founder-businesses-on-the-object`).* Moved: the seat's plants live in
`ProjectsState.businesses` (one `Business` per seat so far, reached as `projects.business`); `Plant` gained `state`
(operating or mothballed), `since_year` and `reason`; `Business` gained `mothball`, `restore` and `forget_reason`, and
set-like views (`business_views.py`: `operating()`, `mothballed()`, `closures()`) so readers keep their `in` and iteration.
`ProjectsState.operating`, `mothballed` and `closures` are now properties over the business; `opened_year` and
`GovernanceState.inst_units` are deleted (a plant's `opened_year` and `size`). `open_venture`, `close_work`
(`close_venture`, `mothball_work`), `restore_work`, `_expand_institution`, `institution_units`, `reopen_units` and the
seat's side of an exchange (`HouseholdParty.capacity_of`, `release_plant`, `receive_plant`) act on the business; a seat
selling a plant now hands over its size and age, as a firm does. Saves check saved plants against the tree. Tests:
`test_founder_and_firm_agree.py`, mothball and restore in `test_business_owner_kinds.py`, the fingerprint reads
`businesses`. Not moved, still to do: the opening fee is still `venture_capex` (a share of the project cost), not the
entry's `capital` (needs the entry capital wired for every node; changes openings); the crew rule (`venture_hands`,
`venture_foreman`, supervision) and the yearly takings and upkeep are still the founder's own code (stages 4 and 3c), so
the wall allowlist did not shrink; manual `close` still mothballs (so `restore` works after it) where the agents path
discards the plant; the world-view methods on `HouseholdParty` and `agents_port` still exist (stage 3c); `playtest/` and
`sim/PROTOCOL.md` need no change yet (the command shapes are unchanged).

**Stage 3b: the yearly rules.** Staffing closure and reopening, loss shedding, creditor seizure and the capability
institutions' occupancy scaling become the business's `close` reasons, driven by one `Business.review(owner, world)`. Owns:
`projects_staffing.py` (+ `_report`, `_shortfall`), `economy_credit.py` (seizure and advice), `step_phase_money.py`,
`step_phase_project_start.py`, `cause_book.py`, `sim/ui/proto/dispatch_inspection_stuck.py`, `state_shut_staffing.py`.
After 3a. Proof: `stuck` and `open` give the same refusal for the same reason (one function, as `staffing_open_refusal` is
today); a business that loses money for consecutive years closes under the same rule for a seat and a firm (when the seat's
`auto_shed` is on); seizure takes the business, not the owner's knowledge (extend `test_firm_exit_debt.py`).

*Stage 3b partly done (branch `514-stage-3b-business-review`).* Moved: `Business.review(owner, world, rules)`
(`sim/agents/business_review.py`) decides which plants close and for which reason (`STAFF_SHORT`, `LOSS_MAKING`,
`CREDITOR_SEIZURE`; the `CLOSED_*` names on `Sim` alias them), and `Business.review_reopening` brings staff closures
back. The owner answers through `Reviewable` hooks (defaults on `Actor`; the founder's household answers through
`business_founder_review.py` and `sim/engine/projects_review.py`, reached as `SimWorld.founder_review()`). A `Plant`
counts `loss_years` (`Business.note_year`); one rule closes a plant after `EXIT_LOSS_YEARS` loss years for a firm
and for a seat whose `auto_shed` is on (capability institutions, granted works and `never_abandon` works are
spared); `Firm.act` exits when the review leaves it no plant. `close_unstaffed_ventures`, `reopen_restaffed_ventures`,
`shed_loss_makers` and the seizure in `answer_exhausted_credit` call the review; the inline abandonment in
`step_phase_money` is gone (the same pressure rule, `cuts_losses_now`, runs in `shed_loss_makers`). A firm's default
(`firm_exit.close_firm`) seizes every plant through `Business.seize_all`, leaving what it learned. `open` and `stuck` call
`open_refusal` (running gate, then people); the running gate is a coded refusal, and `stuck` reports `blocked_by`.
Differences resolved: the loss streak is per plant, not the last plant's margin overwriting the firm's count; a seat's
streak is its fully-ramped margin (`concern_margin`), a firm's is its realised margin (ramp years included) until 3c
puts both on the kernel; `stuck` charges `opening_fee` (grace discount included) and compares to `spending_power("open")`,
as `open` does; pressure shedding and seizure rank by `concern_margin`, institutions last. Not moved: the occupancy
scaling of capability institutions (`INSTITUTION_FLOOR` in `economy_production.institution_upkeep`) stays an upkeep
figure, for 3c; a firm has no staffing closure (it finds a share of its crew and makes that share), pending stage 4;
the seat's staffing closure still ranks by node figures inside `concerns_to_close_for_staffing`. Tests:
`test_business_review.py`, `test_firm_exit_debt.py`. Allowlist: four entries pruned.

*Stage 5 groundwork done (branch `one-business-object`).* A node with upkeep and no entry is a `validate` error unless listed in
`data/unlinked_upkeep_nodes.txt`, a list that only shrinks (`validate_unlinked_producers.check_unlinked_upkeep`,
`test_unlinked_upkeep_ratchet.py`); the opening concern scan reads `Business` objects (`concern_scan.py`, `concern_scan_run.py`). The
remainder of 3c, 4, 5a and 5b, and why the founder is not yet paid from its sale account, are written in Complaints 510 and 514.

**Stage 3c: takings and upkeep through the kernel.** `economy_production.revenue`, `upkeep`, `concern_revenue`,
`ledger_concern_rows`, `revenue_sources`, `venture_real_earnings`, `venture_upkeep_quote`, `concern_levy` and
`agents_port.concern_takings`/`entry_gross` read `business.takings` and `business.upkeep` from the kernel at the economy's
prices. **After 507 stage 5** (section 5). Owns: `economy_production.py`, `projects_venture_quotes.py`, `concern_levy.py`,
`concern_volume.py`, `industry_*.py`, `agents_port.py` (takings lines), `economy_port.py` (`concern_*`), `node_revenue_market.py`.
Proof: a plant's takings equal its outputs at the economy's tile prices less its inputs (new
`test_plant_takings_at_economy_prices.py`); a firm and a seat on the same plant take the same (no learning-ratio leak);
upkeep does not include crew pay, so total outlay per plant equals wages plus wear plus consumables, once (settles the
suspected double count); `test_firm_costs_scale.py`, `test_firm_count_from_costs.py`.

**Stage 4: the founder hires.** A founder's business hires its crew through `sim.labour.market` like a firm; the
household's supervision hands (`venture_staff_free`, `venture_staff_used`, `venture_foreman_free`,
`venture_staff_who_is_watching_what`) are deleted. The founder keeps a manager role open for a business that needs one
(open question 4). Owns: `sim/labour/labour_staff_ledger.py`, `labour_capacity.py`, `labour_port.py`, `projects_staffing.py`
(refusal text), `sim/ui/proto/dispatch_inspection_stuck.py`, `techtree.py` (staff lines). After 3b. Proof: opening a business
with no hireable crew is refused with the labour market's reason; the founder's wage bill rises by the crew's wages and by
nothing else; hands freed by closing return to the pool the market quotes from (`test_complaint_371_actor_staff_between_years.py`).

**Stage 5a: authored data (parallel with anything).** Give every product-making node from section 1.4 a production entry
with a demand side; one worker per `data/branches/<domain>` and the matching `data/production/` file, so domains do not
overlap. Owns: `data/production/**`, `data/branches/**` per domain, `sim/engine/validate_production.py`. Proof:
`python3 sim/simulator.py validate` after every edit; the product-making share of the 1.4 list reaches none.

**Stage 5b: the node loses its money fields.** Delete the fields of 3.4, `node_revenue.py`, `node_rederive.py`'s money half,
`validate_unlinked_producers.py`, `validate_node_money.py`; `is_concern_node` asks "does an entry name this node"; `society_diffusion`
weights by the business's takings instead of `rev`; mods lose `rev_hours`/`up_hours` (`mods/README.md`). After 3c, 4 and 5a, and
after 507 stage 2 (it owns `node_rederive.py`, `data.py`). Owns: `node_revenue*.py`, `node_defaults.py`, `node_rederive.py`,
`data.py`, `tree_source.py`, `tree_merge.py`, `money_units.py`, `civ_start_check.py`, `validate_*`, `society_diffusion.py`,
`sim/ui/cli.py`, `cli_analysis.py`, `techtree.py` (display), the stage 0 allowlist (emptied). Proof: stage 0 test passes with an
empty list; a game that learns many nodes and opens none pays no outlay (new `test_knowledge_costs_nothing.py`: money flow
of a run with extra nodes learned equals one without, apart from research); regenerate openings
(`python3 sim/simulator.py openings --prune`) and `--slow`.

## 5. Interaction with 507, saves, screens and gameplay

### 5.1 Order against 507 (`ONE_PRICE_OWNER_PLAN.md`)

| 510/514 stage | Needs from 507 | Can interleave with |
|---|---|---|
| 0, 1, 2 | nothing | any 507 stage (different directories; stage 2 takes prices as arguments, so it does not care who owns them) |
| 3a, 3b | nothing | 507 stages 1 to 4, 7, 8 |
| 3c | **507 stage 5 first** | both rewrite `node_output_market_factor`, `producer_costs`, `projects_venture_quotes.py`, `economy_production.py` (factor) and the takings lines of `agents_port.py`. Doing 3c first means rewriting the market factor twice |
| 4 | nothing | 507 stages 6 to 8 |
| 5a | nothing | everything |
| 5b | 507 stage 2 (owns `node_rederive.py`, `data.py`) | after 3c |

Change 507 stage 5 in one respect: it says the long-run table stays "the reference for node `rev`". Here node `rev` is
deleted. Have 507 stage 5 build the market factor as a function of (entry, prices) and not of a node, so 3c lifts it into
the kernel without rework. `ONE_PRICE_OWNER_PLAN.md` section 4 should list `sim/world/plant_figures.py` as shared.

### 5.2 Save and load

No migration (CLAUDE.md 4.6). The deleted fields are removed from `SimulationState` and `ActorRecord`; `Business` is a
dataclass the automatic mechanism saves. Round trip must still hold within a build: add `Business` round trip to
`test_saveload*` and `--session` (every command saves and loads). Shipped openings carry the founder's starting state, so
every behaviour stage regenerates them before its pull request.

### 5.3 Screens and commands that change

`open` (founds a business or adds a plant; asks for money and a crew), `close` (plant or business), `mothball`, `restore`,
`sell concern` (becomes `sell business`; keep the typed `sell concern <id>` as an alias for the business running that
product), `quote open|sell` (plant cost, wage, takings, buyer), `portfolio` (businesses with plants, crew, margin; knowledge
shows no cost), `stuck` (blockers become money and crew you cannot hire; the supervision-hands lines go), `available`
(products you can run, grouped by the knowledge that unlocks them), `ventures`, `why`, `state`, the `techtree` rows. Update
`sim/PROTOCOL.md` and the playtest setup in `playtest/` with stage 3a; the protocol's `open` keeps its shape (an id) so agent
players keep working, the id is a product.

### 5.4 Gameplay effects to show the owner

- The founder no longer pays upkeep for knowledge. The ledger lists upkeep only for plants.
- Opening a business means hiring: you pay wages and need people the market can supply; you no longer spend your own
  household's hours "watching" it.
- Several businesses can make the same good, and your size follows what you can sell; the price you receive falls as you add
  plants, and a plant that cannot cover its running cost is mothballed or closed.
- A business can be sold with its crew, plants and debts; a creditor takes the business, not your knowledge.
- Firms and states can mothball, restore and sell exactly as you can; other players have the same fees and gates.
- Net effect on the baseline may be worse at first (CLAUDE.md 4.2); judge it on the ensemble.

## 6. Risks

- **Speed (Complaint 497).** The kernel runs per plant per year; measure `echo "step 5" | python3 sim/simulator.py play --session FILE`
  before and after stages 3c and 4.
- **Many nodes become plain knowledge at once (5b).** Revenue weights that used `rev` (spread, reputation, planner ranking)
  lose their input; each must name a replacement or be dropped. Stage 5b lists them in its pull request.
- **Institutions are not goods** (open question 1); if they stay nodes with upkeep, 5b cannot finish.
- **Heuristics.** `VENTURE_SUPERVISION`, `VENTURE_HANDS_PER_REVENUE`, `VENTURE_FOREMAN_SHARE`, `INSTITUTION_FLOOR`,
  `unstated_upkeep_hours` and the capex shares are labelled heuristics that stage 3 to 5 should delete; count what remains
  with `python3 sim/constants.py --burndown`.
- **Content-id sets in the engine** (`CAPABILITY_INSTITUTIONS`, `SCALABLE_INSTITUTIONS`: `grep -rn "CAPABILITY_INSTITUTIONS\|SCALABLE_INSTITUTIONS" sim --include=*.py`)
  become a flag on the entry's plant kind in stage 3a.

## 7. Owner decisions (2026-10-14)

1. Institutions (schools, laws, benefactions) are plants of a `service` kind: a production entry whose output is a
   capability. This may move to a separate kind of owned thing later.
2. The founder's practice is the founder working a normal job: the founder offers hours in the labour market in a
   trade they hold and is paid that trade's wage, like any worker. `practice_income` and the `_your_own_practice`
   revenue line go (done: Complaint 518, closed); supervising hours reduce hours sold through
   `household.supervision_hours_this_year`, which the manager seat fills.
3. Where the paths differ: the firm path wins for hiring and wages, market share and book sales, and exit; mothball and
   restore come from the founder path and become available to every owner; the opening fee comes from the entry's
   `capital`.
4. Each business has a manager seat, filled by the owner's own hours or by hiring.
5. A business gets its own purse and limited liability, after this plan's stages (it depends on Complaint 106's
   capital markets).
6. A firm paying both node upkeep (which includes crew pay) and crew wages is not intended. Fixed on the agents path
   (`test_firm_crew_paid_once.py`: `economy_port.concern_upkeep` excludes the staff part of a derived upkeep,
   `node_upkeep.non_labour_share`). Fixed on the founder's path too (`test_founder_crew_paid_once.py`: `economy_production.institution_upkeep` charges
   the same non-crew share, the payroll in `living_cost` carries the crew). Authored, programme and defaulted upkeep state no staff split and are charged whole.
7. `auto_open_ventures` stays, as a policy any owner can switch on.
