# Module `finance`

Debt: credit limits, interest, arrears, insolvency, bondage and the capital market.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

**Moved.** `sim/finance/` is the module: `Finance` (capital market, credit line, arrears, insolvency, debt service, purchases, bank) with `FinanceSeat` as its seat state, the views and commands named in its `module_spec.py`, the rules in `rules.py`, `affordability.py`, `credit_freeze.py`, `purchase_rules.py` and `bank_rules.py`, and its declared numbers in `constants.py`. The old mixins are gone from `Sim`; the names callers still use are one-line forwarders in `sim/engine/forward_finance.py`. Bridge reads it still needs are in `sim/engine/bridge_finance.py`. Left where they are: the credit, bank, fund and insurance files of `sim/economy/` (the agent economy's own credit market, reached through `sim.economy.api` and imported across that package), `living_cost`'s workforce share (the module publishes `living_cost` and `dependants_cost` until workforce takes the people-cost facts), and `economy_housing.py` (the housing and trade-school prices are workforce's). The sections below are the draft of the move and stay as written.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 7 / 7 |
| Old methods and properties owned (after regrouping) | 50 |
| Of those, referenced from another module's mixin code | 8 (1 classed read-only or pure by Appendix B, 7 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 34 (8 from mixins, 22 only from outside) |
| Views per used name | 0.21 |
| Views that replace exactly one referenced method and no field (one-to-one) | 2 of 7 |
| Views of other modules it reads | 29, from 13 modules (over the 15-read limit of task 2.4) |
| Commands of other modules it sends | 18 |

**Existing surface and files.** Existing: `sim/contracts.py` (`Contracts` registry), `sim/agents/borrowing.py`, `sim/economy/credit.py`, `sim/economy/credit_lines.py`, `sim/world/capital_market.py`. Engine: `CreditMixin` (21 methods), `DebtServiceMixin`, `CapitalMarketMixin`, `InterestMixin`, `SeatBankMixin`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `CreditMixin` | `sim/engine/economy_credit.py` | 17 | 4 |
| `DebtServiceMixin` | `sim/engine/economy_debt_service.py` | 7 | 0 |
| `CapitalMarketMixin` | `sim/engine/economy_capital_market.py` | 9 | 3 |
| `InterestMixin` | `sim/engine/economy_interest.py` | 4 | 1 |
| `SeatBankMixin` | `sim/engine/seat_bank.py` | 1 | 0 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 12 | 0 |
| `StepPhasesMixin` | `sim/engine/core_step_phases.py` | 3 | 0 |
| `MoneyPhaseMixin` | `sim/engine/step_phase_money.py` | 3 | 0 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_deputy_consequence`, `_deputy_hours_sentence`, `_lender_party`, `_step_bondage`, `_step_money`, `answer_exhausted_credit`, `charge_interest`, `dependants_beyond_means`, `enter_debt_bondage`, `interest_paid`, `last_settlement`, `lender_offers`, `market_credit_room`, `market_funds`, `recurring_net_before_interest`, `settle_insolvency`, `settle_lender_interest`, `shed_loss_makers`, `state_owes`, `warn_near_the_limit`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `FinanceSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.household.arrears_years` | seat | - | - |
| `state.household.bondage_debt` | seat | <ui> 1 | - |
| `state.household.bondage_years_left` | seat | <ui> 2, production 1 | - |
| `state.household.credit_frozen_until` | seat | <ui> 4, projects 2 | - |
| `state.household.insolvent_years` | seat | <ui> 2, projects 1 | - |
| `state.household.interest_arrears` | seat | - | - |
| `state.household.interest_paid` | seat | - | - |
| `state.household.last_settlement` | seat | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `spending_power` | table | yes | What the acting seat can commit this year: balance plus remaining credit minus what active work already owes. | `spending_power`, `funding_capacity`, `funding_breakdown` | - | `ledger.acting_balance`, `credit_limit`, `projects.committed_cost` | `debt`, `money` | 4 |
| `credit_limit` | table | yes | The most the seat may owe, and the part of it a creditor will bear. | `credit_limit`, `bearable_part_of`, `credit_line_sought` | - | `production.revenue_estimate`, `workforce.living_cost`, `ledger.acting_balance`, `mechanics.effect` | `debt`, `income` | 8 |
| `debt_status` | table | yes | Frozen-until year, insolvent years, arrears, bondage term and debt, last settlement. | `interest_on_arrears`, `debt_bondage_term_years`, `stall_diagnosis` | `household.credit_frozen_until`, `household.insolvent_years`, `household.bondage_years_left`, `household.bondage_debt`, `household.interest_arrears`, `household.arrears_years`, `household.last_settlement` | - | `debt` | 4 |
| `debt_interest_rate` | table | yes | The rate the acting seat pays this year. | `debt_interest_rate` | - | `market_rate` | `debt` | 2 |
| `market_rate` | table | no | The market rate of interest of the home economy. Read 15 times by `sim/agents`. | `market_rate`, `economy.base_rate`, `economy.agent_rate`, `economy.credit`, `economy.agent_credit_room` | - | - | `capital_market` | 9 |
| `debt_service_forecast` | quote | yes | Recurring net income, living cost, sustainable debt and the service a given debt would need. | `recurring_net`, `recurring_living_cost`, `debt_service_forecast`, `sustainable_debt`, `dependants_beyond_means`, `recurring_net_before_interest` | - | `production.revenue_estimate`, `production.upkeep`, `workforce.living_cost` | - | 1 |
| `capital_market` | table | no | Lender offers, lenders' share, the state's lending and what it is owed. | `lender_offers`, `lent_share`, `market_funds`, `market_credit_room`, `state_lending`, `state_owes`, `capital_market_report` | - | - | `capital_market` | 3 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `debt_interest_rate`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 8 methods are referenced from other modules' mixin code: 6 are replaced by a view here, 2 by a command. 22 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 34 used names, 24 are covered by a view or command through the method itself, 4 through a field alias, 2 are year-phase hooks and 4 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `bearable_part_of`, `credit_limit`, `credit_line_sought`, `debt_interest_rate`, `debt_service_forecast`, `dependants_beyond_means`, `funding_breakdown`, `funding_capacity`, `interest_on_arrears`, `recurring_living_cost`, `recurring_net`, `recurring_net_before_interest`, `spending_power`, `stall_diagnosis`, `sustainable_debt`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `PayInterest` | payer, lender, owed | `CreditMixin.charge_interest`, `InterestMixin.pay_interest`, `settle_lender_interest`. Methods: `pay_interest`, `note_lender_posting` | `sim/agents/borrowing.py:133,140`, `sim/engine/economy_interest.py:15`, `sim/engine/economy_credit.py:305` | `no_such_debt` | `household.interest_paid` |
| `EnterBondage` | seat, term_years, debt | `enter_debt_bondage`: the household is bound to labour. | `sim/engine/economy_credit.py:506-507`, `sim/engine/core_step_phases.py:534` | none: always applies | `household.bondage_debt`, `household.bondage_years_left` |
| `SettleInsolvency` | seat, kind | `default_on_debt`, `settle_insolvency`, `answer_exhausted_credit`: freeze credit, write off, record the settlement. Methods: `default_on_debt` | `sim/engine/economy_credit.py:436,520,539`, `sim/agents/borrowing.py:140` | `not_insolvent` | `household.credit_frozen_until`, `household.last_settlement` |
| `NoteInsolvency` | seat, years | The per-year insolvency counter inside the money phase. | `sim/engine/step_phase_money.py:121,123,141` | none: always applies | `household.insolvent_years` |
| `FoundBank` | seat, capital | `seat_found_bank`: a seat founds a bank (sends Transfer). Methods: `seat_found_bank` | `sim/engine/seat_bank.py`, `sim/economy/bank_founding.py:12` | `cannot_afford` | - |
| `EnforceCreditLimit` | seat, year | `enforce_credit_limit`: the year phase `credit_limit`; sheds loss makers, warns, defaults. Methods: `enforce_credit_limit` | `sim/engine/year_phases.py (credit_limit)` | none: always applies | - |
| `RefreshLenderOffers` | tick | `refresh_lender_offers`: part of the actors phase. Methods: `refresh_lender_offers` | `sim/engine/society_actors.py (advance_actors)` | none: always applies | - |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `household.bondage_debt`: 1 site: `sim/engine/core_step_phases.py:534`
- `household.bondage_years_left`: 1 site: `sim/engine/core_step_phases.py:534`
- `household.insolvent_years`: 1 site: `sim/engine/core_properties.py:97`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `actors`: `actors.cast` (actors, actors.active_firms, actors.actors, actors.state)
- `hazards`: `hazards.output_factor` (economy.output_factor)
- `ledger`: `ledger.acting_balance` (household.capital, input of finance.credit_limit, input of finance.spending_power); `ledger.balance` (actors.purse_lenders)
- `markets`: `markets.agent_economy` (economy, economy.agent)
- `mechanics`: `mechanics.effect` (effect_sum, effect_values, input of finance.credit_limit); `mechanics.mechanic` (nodes_with_mechanic); `mechanics.patronage` (deputies_carry_the_work, deputy_hours)
- `polity`: `polity.standing` (household.reputation); `polity.state_treasury` (military_leverage, state_treasury)
- `production`: `production.revenue_estimate` (estimated_revenue, held_trade, input of finance.credit_limit, input of finance.debt_service_forecast ...); `production.running` (projects.operating, running_with_mechanic); `production.upkeep` (input of finance.debt_service_forecast, upkeep)
- `projects`: `projects.active_projects` (projects.active); `projects.committed_cost` (input of finance.spending_power)
- `reporting`: `reporting.event_log` (household.log)
- `resources`: `resources.forest_and_nitre` (holdings.forest_ha); `resources.mine_cost` (mine_operating_cost); `resources.mine_output` (mine_capacity)
- `seats`: `seats.founder` (founder.policy); `seats.seat_party` (dealing_party, seat_party)
- `ventures`: `ventures.closures` (note_venture_year, review_ventures)
- `workforce`: `workforce.hours_available` (labour.hours_for_sale); `workforce.labour_market` (labour.market); `workforce.living_cost` (dependants_cost, input of finance.credit_limit, input of finance.debt_service_forecast, living_cost); `workforce.staff` (household.artisans, household.directors_extra, household.freedmen, household.scholars ...); `workforce.staffing_quote` (labour.SLAVE_BASE_PRICE, labour.work_for_wages_dry_run); `workforce.wage` (labour.best_wage_trade, labour.standing_job_pay); `workforce.wage_bill` (household.wages_prepaid, labour.wage_bill)

Sends (commands of other modules):

- `actors`: `AdvanceActors`
- `coin`: `ChargeKeeping`, `ChargeTheft`
- `demography`: `StepPopulation`
- `diffusion`: `AdvanceSociety`
- `hazards`: `SetOutputFactor`
- `ledger`: `PayEdge`, `PayWages`, `ReceiveFromEdge`
- `polity`: `ChangeStanding`
- `projects`: `CloseLapsedDependents`
- `reporting`: `RecordEvent`
- `resources`: `OpenMine`
- `ventures`: `CloseWork`, `OpenVenture`
- `workforce`: `Fire`, `Hire`, `NotePay`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `money_seat`: `charge_interest`, `shed_loss_makers`, `warn_near_the_limit`, `enforce_credit_limit`, the insolvency step (`step_phase_money.py:93-141`)
- `credit_limit` (the same `enforce_credit_limit` again as its own phase)
- `seat_work`: `_step_bondage` (`core_step_phases.py:138`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 57 | `spending_power`, `credit_limit`, `debt_interest_rate`, `recurring_net`, `credit_frozen_until`, `recurring_living_cost`, `debt_service_forecast`, `interest_on_arrears` |
| agents | 16 | `market_rate`, `pay_interest` |
| engine/(function modules) | 8 | `market_rate`, `credit_limit`, `_step_money_seat`, `_step_money_world`, `enforce_credit_limit` |
| engine/agents_port* | 5 | `state_lending`, `pay_interest`, `credit_limit`, `debt_interest_rate`, `default_on_debt` |
| engine/economy_port* | 3 | `debt_bondage_term_years`, `market_rate`, `credit_line_sought` |
| mods | 1 | `market_rate` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui: `spending_power` 12, `credit_limit` 8, `debt_interest_rate` 7, `recurring_net` 5, `credit_frozen_until` 4, `recurring_living_cost` 3. sim/agents: `market_rate` 15, `pay_interest`. `agents_port` calls `state_lending`, `credit_limit`, `debt_interest_rate`, `default_on_debt`. mods: `market_rate`.

## (h) Hard spots and caches

- `_step_money_seat` is one sequence of postings in a fixed order that touches production (revenue), workforce (wages), resources (mine cost), coin (keeping), finance (interest, insolvency) and seats (win check). Splitting it into per-module phases must keep the order; model it as an ordered list of money sub-steps the ledger runs, each a command from its owner.
- `credit_limit` reads revenue, which reads prices, which read wages (and `spending_power` is read by project starting inside the same year): a derived view with several inputs of other modules; its freshness is the join of the inputs' channels. It is also a quote when asked with a hypothetical.
- `living_cost` / `dependants_cost` live in `CreditMixin` today but are workforce facts (cost of people); they move to workforce and finance reads them.
- Debt contracts are in `Contracts` (shared with the economy record). The household keeps its own debt fields as well (`bondage_debt`, `credit_frozen_until`, `insolvent_years`, `interest_arrears`): a second debt story the module must reconcile or fold into `Contracts`.

Caches and version counters held today (feed for task 1.2):

- None of its own beyond version counters; `credit_limit` is recomputed on demand today.
