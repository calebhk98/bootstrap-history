# Module `reporting`

Indicators, the event log and warn-once notes; everything computed to be read, not to act on.

**Status:** moved (branch `mr/reporting`). The package is `sim/reporting/`; this file describes what shipped, not the draft proposal. The draft's tables below the "Draft proposal" line are kept for the record, measured at `e8b004c`; re-measure before acting on one. Counts of what shipped come from the module spec (`python3 -c "import sys; sys.path.insert(0,'.'); from sim.reporting.module_spec import MODULE_SPECS as s; print(len(s[0].publishes), len(s[0].applies), len(s[0].reads))"`).

## What changed from the draft

- **Warn-once notes are not reporting's.** The draft's `NoteOnce` over the `_said_*` flags is dropped. Of the five fields it named, `_last_buy_refusal`, `_said_stack_caution`, `_said_command_index`, `_said_parallelism` and `_dashboard_history` are the screens' own memory (written only by `sim/ui` through `ui_port.py`, read by no rule); they belong in `state.interface`, "the UI's own memory; the engine never reads it", not in a module. `_said_scandal` is a warning band for the scandal rule (`core_step_phases.py`) and goes with `polity`. Nothing about them moved here (`grep -rnE "_said_scandal|_said_parallelism|_dashboard_history" sim --include=*.py | grep -v /tests/` lists them).
- **World events are not here.** `state.economy.world_events` is the hazards module's (`hazards.md`).
- **Views:** 8 instead of 3. A caller asks one question (the per-head figure is read in the cache keys of five hot paths, the hours twice a year), so each is its own view: `event_log`, `automation_rows`, `real_output_per_head`, `real_output_hours`, `money_real`, `real_price_ratio`, `last_market_price_ratio`, `coin_value_ratio`. `price_ratios` (the draft's view under the three-caller floor) is not a view: its callers are `coin_value_ratio` (the coin module), `last_market_price_ratio` (the labour package's wage rule) and the module's own phase.
- **Commands:** 6. `RecordEvent`, `RecordAutomation`, `RecordAutomationSkip` (they existed, applied by the engine bridge), `DiscardEventsAfter`, `CloseRealOutput`, `ErodeMoney`. The draft's `RecordIndicator` is two commands because its two writers carry different facts: the market's close sends nothing but "the year has closed", a debasement carries its share. `RecordEvent` gained `facts`, `seat` (the hazards write to every playing seat's log, acting or not) and `year` (the year a recovery or a closure reports is not always the current one).
- **`DiscardEventsAfter` is a debt, not a design.** `work_for_wages_dry_run` (labour) logs as it runs, restores every book and then truncates the log. The right fix is a pure quote of the sale; until then the command takes the lines back.
- **Phases:** `trim_audit` (the audit trail drops rows older than the years kept) is split out of `begin_seat_year`, with `hear_of_other_seats` named as its own phase after it, so the three steps keep their order. `wage_market_ratios` is the module's phase. The close of real output stays at the end of `_step_market` as the command `CloseRealOutput` (a mod running `after: market` must see the closed figure).
- **A read that writes, kept.** `agent_basket` fixes the baseline prices at the first read that finds prices, in the module's own state, inside views that are not cached (they read the agent economy's prices, which legacy code writes). Making the baseline an explicit command would change which year fixes it if the first reader changed.
- **State** (relocated in `sim/tests/equiv_fields.py`): per seat `ReportingSeat` (`log`, `automation_audit`); per game `ReportingWorld` (`output_per_head`, `introduction_prices`, `money_real`, `wage_market_ratios`, `agent_baseline_prices`). `_base_basket_cache` is a never-saved cache on the module, keyed to the world slot it was read for, so a load drops it.
- **A framework gap met:** a command can name a seat that is not the acting one, but a module only saw the acting seat's slot. `Module.seat_of(seat_id)` (set by `game_assembly.attach`) answers another seat's state, and `game_assembly.give_seat_slots` builds the slots of a seat added after the game began.

## As shipped

| Measure | Value |
|---|---|
| Views / commands | 8 / 6 (+ the phases `trim_audit`, `wage_market_ratios`) |
| Views of other modules it reads | 13: `year`, `acting_balance`, `money_per_labour_hour`, `opening_population`, `home_coin_metal` (published), and `agent_prices`, `agent_opening_basket`, `agent_volume_baseline`, `agent_traded_volumes`, `new_goods_units`, `household_prices`, `population_total`, `wage_materials` (bridged in `sim/engine/bridge_reporting.py`; they go when `markets`, `demography` and `workforce` publish theirs) |
| `legacy_*` reads (debts) | none |
| Log writes converted | 100 `.log.append` sites in the engine, labour and the UI became `RecordEvent` sends; 14 audit calls became `RecordAutomation` / `RecordAutomationSkip` sends. No household-log append remains: `grep -rn "\.log\.append" sim mods --include=*.py \| grep -v /tests/` finds the module's own append and the armies' `army.log`, which is not the seat's log |
| Forwarders left (`sim/engine/forward_reporting.py`) | `Sim.log`, `Sim.money_real`, `Sim.real_output_per_head`, `Sim.real_output_hours`, `Sim.last_market_price_ratio` |
| Files absorbed | `real_output.py`, `real_price_ratios.py`, `automation_audit.py` deleted; `real_output_measure.py` became `sim/reporting/output_rules.py` |

## Draft proposal (task 1.5, measured at `e8b004c`)

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 3 / 3 |
| Old methods and properties owned (after regrouping) | 21 |
| Of those, referenced from another module's mixin code | 6 (3 classed read-only or pure by Appendix B, 3 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 13 (6 from mixins, 7 only from outside) |
| Views per used name | 0.23 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 3 |
| Views of other modules it reads | 10, from 5 modules |
| Commands of other modules it sends | 0 |

**Existing surface and files.** Engine: `RealOutputMixin`, `RealPriceRatiosMixin`, `ViewShareMixin` (a caching mechanism, dissolved), `invariants.py`. Complaint 554 would be this module.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `RealPriceRatiosMixin` | `sim/engine/real_price_ratios.py` | 5 | 2 |
| `RealOutputMixin` | `sim/engine/real_output.py` | 7 | 2 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 16 | 4 |
| `StepPhasesMixin` | `sim/engine/core_step_phases.py` | 1 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_agent_basket`, `_said_scandal`, `base_basket`, `last_market_price_ratio`, `opening_output_hours`, `real_output_lines`, `real_price_ratio`, `traded_measure`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `ReportingWorld` and a per-seat dataclass `ReportingSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.agent_baseline_prices` | world | - | - |
| `state.economy.introduction_prices` | world | - | - |
| `state.economy.money_real` | world | <ui> 1 | core 1 |
| `state.economy.output_per_head` | world | markets 3, core 2, production 1 | - |
| `state.economy.wage_market_ratios` | world | - | - |
| `state.holdings._dashboard_history` | seat | - | <engine-functions> 1 |
| `state.household._last_buy_refusal` | seat | <agents> 1 | <engine-functions> 1 |
| `state.household._said_command_index` | seat | - | <engine-functions> 1 |
| `state.household._said_stack_caution` | seat | <agents> 1 | <engine-functions> 1 |
| `state.household.automation_audit` | seat | <engine-functions> 3 | <engine-functions> 2 |
| `state.household.log` | seat | polity 18, projects 17, <ui> 14, finance 12, hazards 11, workforce 6, +8 more | polity 18, projects 17, finance 12, hazards 9, <ui> 9, workforce 6, +8 more |
| `state.seat_progress._said_parallelism` | seat | <engine-functions> 1 | <engine-functions> 1 |
| `state.seat_progress._said_scandal` | seat | polity 1 | polity 2 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `real_output` | table | no | Real output per head and per hour, output lines, the basket and introduction prices. | `real_output_per_head`, `real_output_lines`, `real_output_hours`, `opening_output_hours`, `traded_measure`, `base_basket` | `economy.output_per_head`, `economy.introduction_prices`, `economy.money_real` | `prices.material_prices`, `demography.population`, `markets.household_demand` | `indicators` | 6 |
| `price_ratios` | table | no | Real price ratio, coin value ratio, last market ratio, wage and baseline ratios. | `real_price_ratio`, `coin_value_ratio`, `last_market_price_ratio`, `_agent_basket` | `economy.wage_market_ratios`, `economy.agent_baseline_prices` | `markets.agent_economy`, `workforce.wage` | `indicators` | 1 |
| `event_log` | table | yes | The seat's log of events and the dashboard history. | `log` | `household.log`, `holdings._dashboard_history`, `household.automation_audit`, `household._said_command_index`, `household._said_stack_caution`, `household._last_buy_refusal`, `seat_progress._said_scandal`, `seat_progress._said_parallelism` | - | `log` | 16 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `price_ratios`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 6 methods are referenced from other modules' mixin code: 3 are replaced by a view here, 2 by a command. 7 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 13 used names, 6 are covered by a view or command through the method itself, 6 through a field alias, 1 are year-phase hooks and 0 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_agent_basket`, `coin_value_ratio`, `real_price_ratio`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `RecordEvent` | seat, kind, facts, text | `household.log.append(...)` with a `LogLine` (`sim/refusal.py`): every module reports through it. | `sim/engine/society_state_pressure.py`, `sim/engine/projects_starting.py`, `sim/engine/economy_credit.py`, `sim/engine/society_hazards.py`, `sim/engine/step_phase_money.py`, `sim/engine/projects_staffing.py`, `(104 `.log.append` sites in total: `grep -rnE '\.log\.append\(' sim mods --include=*.py / grep -v /tests/ / wc -l`; 12 in core_step_phases.py, 11 in society_state_pressure.py, 9 in society_hazards.py, 8 each in projects_completion.py and economy_credit.py, 6 in ui/proto/dispatch_ventures.py)` | none: always applies | `household.log` |
| `NoteOnce` | seat, key | The `_said_*` warn-once flags on household, scenario and seat progress. | `sim/engine/state.py:112-119,391-395` | none: always applies | `household._said_command_index`, `household._said_stack_caution`, `household._last_buy_refusal`, `seat_progress._said_scandal`, `seat_progress._said_parallelism` |
| `RecordIndicator` | name, value | `_close_real_output`, `record_wage_market_ratios`, `_dashboard_history`. Methods: `_close_real_output`, `record_wage_market_ratios` | `sim/engine/real_output.py`, `sim/engine/real_price_ratios.py` | none: always applies | `economy.output_per_head`, `economy.introduction_prices`, `economy.money_real`, `economy.wage_market_ratios`, `economy.agent_baseline_prices`, `holdings._dashboard_history` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `economy.money_real`: 2 sites: `sim/engine/shock_year.py:160`, `sim/engine/core.py:506` (assign (alias))
- `holdings._dashboard_history`: 1 site: `sim/engine/ui_port.py:149` (assign (alias))
- `household._last_buy_refusal`: 4 sites: `sim/labour/labour_bondage.py:266`, `sim/labour/labour_bondage.py:273`, `sim/agents/household.py:264` (assign (alias)), `sim/engine/ui_port.py:205` (assign (alias))
- `household._said_command_index`: 1 site: `sim/engine/ui_port.py:213` (assign (alias))
- `household._said_stack_caution`: 2 sites: `sim/agents/household.py:265` (assign (alias)), `sim/engine/ui_port.py:221` (assign (alias))
- `household.automation_audit`: 2 sites: `sim/engine/automation_audit.py:16`, `sim/engine/automation_audit.py:25` (.append())
- `household.log`: 101 sites: `sim/labour/labour_staff_controls.py:99` (.append()), `sim/labour/labour_wage_ledger.py:34` (.append()), `sim/labour/labour_wage_ledger.py:52` (delete), `sim/labour/labour_staff_ledger.py:32` (.append()), `sim/labour/labour_staff_ledger.py:119` (.append()), `sim/ui/proto/dispatch_labour.py:422` (.append() (alias)), `sim/ui/proto/dispatch_labour.py:445` (.append() (alias)), `sim/ui/proto/dispatch_ventures.py:305` (.append() (alias)), `sim/ui/proto/dispatch_ventures.py:538` (.append() (alias)), `sim/ui/proto/dispatch_ventures.py:567` (.append() (alias)) and 91 more
- `seat_progress._said_parallelism`: 2 sites: `sim/engine/core_properties.py:741`, `sim/engine/ui_port.py:229` (assign (alias))
- `seat_progress._said_scandal`: 3 sites: `sim/engine/core_properties.py:749`, `sim/engine/core_step_phases.py:475`, `sim/engine/core_step_phases.py:485`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `coin`: `coin.coin_metal` (home_coin_metal)
- `demography`: `demography.population` (input of reporting.real_output)
- `markets`: `markets.agent_economy` (economy, economy.agent_opening_basket, economy.agent_prices, economy.agent_traded_volumes ...); `markets.household_demand` (_opening_population, household_new_goods_units, input of reporting.real_output); `markets.household_prices` (goods_market.household_prices); `markets.trade_quote` (goods_market)
- `prices`: `prices.material_prices` (input of reporting.real_output)
- `workforce`: `workforce.labour_market` (labour.money_per_labour_hour); `workforce.staff` (labour); `workforce.wage` (input of reporting.price_ratios)

Sends: none.

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `begin_seat_year`: the automation audit
- `market`: `_close_real_output`, `record_wage_market_ratios` (`market_clearing.py:200,202`)
- `seat_work`: the year's `hours_this_year` and `spend_last_year` captures, if they stay here (see workforce)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 15 | `log`, `_said_stack_caution`, `money_real` |
| engine/ui* | 6 | `_said_parallelism`, `_dashboard_history`, `_last_buy_refusal`, `_said_command_index`, `_said_stack_caution` |
| engine/(function modules) | 2 | `real_output_hours`, `verify_step_invariants` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

ui: `log` 13 reads, `money_real`, `_said_*` (underscore fields read by the protocol); agents_port: `open_view_scope`, `close_view_scope`.

## (h) Hard spots and caches

- `household.log` is appended to from 104 sites in about twelve modules; a `RecordEvent` command is the single largest mechanical change in the migration, and the cheapest to do first because it changes no value.
- `ViewShareMixin` was a hand-made version-stamp cache (`view_share.py`); it is now the `sharing` module (`sim/sharing/`).
- `_said_*` and `_dashboard_history` are underscore fields read by `ui_port`.

Caches and version counters held today (feed for task 1.2):

- `_base_basket_cache` (`real_output.py:43`)
- `_view_scope`, `_standalone_scope` (`view_share.py:19,58`)

Detected by the cache scan in this module's mixin files: `engine/real_output.py:43 _base_basket_cache`.
