# Module `resources`

Extractive resources: the seat's mines and the deposits they name, prospecting, coppice woodland, nitre beds, and the standing timber firms fell.

**Status:** moved (branch `mr/resources`). The package is `sim/resources/`; this file now describes what shipped, not the draft
proposal. Counts come from the module spec
(`python3 -c "import sys; sys.path.insert(0,'.'); from sim.resources.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads))"`).

## What changed from the draft

- **Views:** 27 instead of 5. The draft's five were each a bundle of old methods; the readers ask separate questions (a cheap
  `mine_capacity` inside the throttle's hot loop, a `mine_quote` for the player, the deposit rows for the agent economy's firms), so
  the views are the questions. Seven are cached on the module's own channels (`mines`, `forest`, `nitre`, `timber`), because
  every write to what they read is a command or the phase of this module: `mine_workings`, `mine_capacity`,
  `mines_being_sunk`, `mine_depletion`, `forest_hectares`, `nitre_beds`, `timber_felled`. The rest read prices, wages, the
  state's reach or the map and stay uncached.
- **Commands:** 10 instead of 4. `OpenMine`, `CloseMine`, `MothballMines`, `DrawDeposit`, `Prospect`, `BuyForest` and
  `LayNitreBeds` (the draft folded the nitre bed into `BuyForest`: it is another good with another price, and a refusal
  names its own cause), plus three the draft missed because its scan counted only fields written inside mixins:
  `NoteMineCostPaid` (the money phase added the year's running cost into `mine_cost_paid`), and `FellTimber` and
  `RegrowTimber` (the agent economy's port wrote `economy.forest_felled`). `commission_mines` is not a command: it is the first step of the
  module's `materials` phase.
- **`forest_holding` and `mine_operating_cost` were already views** (coin and projects had bridged them under those names);
  they are now this module's, with the shapes their readers already had.
- **`material_shortfall_t` is not resources'.** The draft listed it with the forest and nitre view. It is the materials
  accounting (need, own supply, market) and stays in `FreightMixin` until materials moves; resources reads it as the view
  `material_shortfall`. The remedy text (`shortage_remedy_plan`) is resources', as drafted.
- **The `materials` phase was split.** The old `_step_materials` commissioned mines, bought woodland, sank mines and laid beds,
  then told the player what a shortage cost. The first three are this module's phase `materials` (it keeps the old name: a
  mod's `after: materials` most likely meant "after the supply is bought"); the telling is the engine's new phase
  `material_shortage_notes`, which reads the throttle the first part left in `holdings.throttle` (no step between them
  recomputes it; the micro equivalence check holds). It goes with materials.
- **`mineral_scale`, `inspection_reach`, `forest_reach` and the text views** are read from the bridge under the names their owners
  will publish (`land`, `polity`, `reporting`).
- **Moved with it:** `mine_ceiling.py` and `forest_ceiling.py` into `sim/resources/ceilings.py`, `mine_labour_profile.py` into
  `labour_profile.py`, `deposit_history.py`, `shortage_sizing.py` into `sizing.py`; the constants (`MINE_*`, `DEPLETION_*`,
  `FOREST_*`, `NITRE_*`, `PROSPECT_*`, `AUTO_*`, `REVENUE_SCALE_*`) into `constants.py`. Dropped as dead code: `MINE_OPEX_PER_T`.

## At a glance

| Measure | Value |
|---|---|
| Views / commands | 27 / 10 |
| Views of other modules it reads | 40, none of them `legacy_*` except `legacy_world_map` (the map handle the geography package's searches take) |
| Commands of other modules it sends | the ledger's `PayEdge` and `ReceiveFromEdge`; reporting's `RecordEvent`, `RecordAutomation`, `RecordAutomationSkip` |
| State | seat: `mines`, `mine_pending`, `mine_ready`, `mine_cost_paid`, `mine_tranches`, `deposits_found`, `deposit_drawn`, `prospected_person_days`, `forest_ha`, `nitre_bed_m2`; world: `forest_felled` |
| Phases | `materials` (seat) |
| Log lines written | `workings_exhausted`, `workings_closed`, `mines_mothballed`, `coppice_limit`, `nitre_bed_laid` |

## Mixin classes absorbed

| Class | File | Where it went |
|---|---|---|
| `MiningMixin` | `economy_mining.py` (deleted) | `sim/resources/workings.py` (what stands, depletion, commissioning), `costs.py` (capex, opex, ceiling, quote), `sinking.py` (open, close, mothball), `woodland.py` (coppice and nitre), `rules.py` |
| `MineDepositsMixin` | `mine_deposits.py` (deleted) | `sim/resources/deposits.py` (rows, drawing, prospecting) |
| `FreightMixin` (4 methods) | `economy_freight.py` | `build_nitre` -> `woodland.py`; `shortage_remedy`, `shortage_remedy_plan` -> `remedies.py`; `material_shortfall_t` stays (materials) |
| `MaterialsPhaseMixin` | `step_phase_materials.py` | `materials_phase.py`; the shortage notes stay as `_step_material_shortage_notes` |
| `ForwardingPropertiesMixin` | `core_properties.py` | `forest_ha`, `nitre_bed_m2`, `mines`, `mine_tranches` aliases deleted |

## State owned

Relocations are in `sim/tests/equiv_fields.py`.

| Today's path | Was |
|---|---|
| seat `modules/resources/{mines, mine_pending, mine_ready, mine_cost_paid, mine_tranches, deposits_found, deposit_drawn, prospected_person_days, forest_ha, nitre_bed_m2}` | `holdings/<same>` |
| world `modules/resources/forest_felled` | `economy/forest_felled` |

A seat handover carries the seat's `resources` slot (`MOVED_MODULE_STATE` in `sim/engine/seat_handover.py`) and refuses a replacement that holds one.

## Views

Kind T is table, K keyed, Q quote. Cached views name their channel.

| View | Kind | Answers | Callers |
|---|---|---|---|
| `mine_workings` (mines) | T | the standing workings, in commission order | ui, view stamps |
| `mine_capacity` (mines) | T | rated capacity by material | materials, electricity, cash remedies, hazards, ui |
| `mines_being_sunk` (mines) | T | `{tranches, pending}` | ui, remedies |
| `mine_depletion` (mines) | K | a material's capacity-weighted share of day-one yield | materials |
| `forest_hectares` (forest) | T | hectares of coppice | materials, electricity, credit, ui |
| `nitre_beds` (nitre) | T | `{square_metres, tonnes_per_square_metre}` | materials, ui |
| `timber_felled` (timber) | T | the felled ledger | the agent economy's port |
| `mine_operating_cost` | T | the workings' running cost together | finance, projects, money phase, ui |
| `mine_working_cost`, `mine_working_report` | Q | one working's cost; its depletion, yield, cost and note | cash remedies, ui |
| `mine_quote`, `mine_land_ceiling`, `mineable`, `mine_catalog_hint`, `mine_works_materials`, `mine_demand_goods` | Q/K/T | what a mine would cost, how large one can stand, which names are minable, the catalogue's hints | ui, materials |
| `mine_yield`, `mine_depletion_note` | K | a material's output, and why it is below the tonnage sunk | ui |
| `found_deposits`, `partner_deposits`, `deposit_remaining`, `mine_room_in_deposits` | K/Q | the deposits a seat names, those of the partners' tiles, what is left, the room | agent economy, materials, ui |
| `forest_holding`, `forest_price`, `forest_ceiling`, `nitre_price` | T | the forest held and what a hectare or a square metre costs | coin, ui |
| `shortage_remedy_plan` | Q | what would end a shortage, as text and commands | ui, the shortage notes |

## Commands

| Command | Refusal causes |
|---|---|
| `OpenMine(material, tonnes_per_year, partial, order, deposit)` | `nothing_asked`, `not_minable`, `no_room`, `no_deposit_found`, `cannot_afford` |
| `CloseMine(material)` | `no_workings` |
| `MothballMines()` | none |
| `DrawDeposit(deposit, tonnes)` | none |
| `Prospect(tile, material, person_days)` | `no_deposit_data`, `not_held`, `no_effort`, `cannot_afford` |
| `BuyForest(hectares)` | `no_room`, `cannot_afford` |
| `LayNitreBeds(square_metres)` | `nothing_asked`, `cannot_afford` |
| `NoteMineCostPaid(amount)`, `FellTimber(cuts)`, `RegrowTimber()` | none |

## Hard spots, and how they were handled

- **Reads that write.** `mine_operating_cost` reads prices and wages; the prices read `mine_capacity` through the throttle's
  demand; the engine breaks the loop with a re-entry flag in `_banded_market_rate` (`incumbent_prices.py`), set while it
  reads the market rate. The module neither sets nor depends on the flag: `mine_cost` is a quote that reads the views
  `material_price`, `wage` and `price_index` (the bridge asks the engine exactly as the old code did) in the old order, so
  the flag still guards the same chain. `resource_throttle` also writes (it banks the year's unused own output into the
  stock): it is the bridge quote `resource_throttle`, called once per phase as before, and splitting it into a reading and a
  command is the materials owner's.
- **Caches.** The three the draft found: `_running_kept_tables` (an engine helper materials still uses, now in
  `forward_resources.py`; the module keeps its own memo of the works' effects keyed on the bridge view `running_stamp`),
  `_deposit_base_cache` and `_modelled_sizes_cache` (now module fields set up in `setup()`, never saved), plus the
  labour-hours profile cache, a module-level table shared by all games as the class attribute it was (Complaint 730).
- **Float order.** Every product keeps the order of the old expression (`tonnes * capex * price_index * scale`; `capacity *
  opex * price_index * scale`); the forest price is `(hours * money_per_labour_hour) * price_index`.

## Debts

`legacy_world_map` (read in place by the geography searches). Forwarders left on `Sim` (`sim/engine/forward_resources.py`):
`mine_capacity`, `MINE_OPEX_MATERIALS`, `base_mine_catalog_hint`, `mine_operating_cost`, `mine_operating_cost_for`,
`_workings_of`, `mothball_mines`, `found_deposits`, `partner_deposits`, `draw_deposit`, `mine_depletion_factor`,
`shortage_remedy`, `shortage_remedy_plan`, `_running_kept`, `_running_kept_stamp`.
