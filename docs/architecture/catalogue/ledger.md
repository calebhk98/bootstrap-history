# Module `ledger`

Money and goods balances: the one writer of what an actor holds.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## The seat's purse: who owns what (Phase 6b; done, with what stays)

The seat's money is an account in the actors' `Purses` book, named by the seat's id. The migration removed the bridge views
`legacy_acting_household`, `legacy_household_actor`, `seat_party` and `seat_party_with_margins`, which handed modules the household's state, its
facade and the seat as an exchange party. Decided per fact, from the code:

| Fact | Owner | Reached through |
|---|---|---|
| The book (accounts, debts, the pool, every actor's purse) | actors (`sim/agents/purses.py`, world slot `ActorsState`) | `cast_state` view, for the ledger's postings and the seat's borrower |
| A seat's account in the book (its balance, its postings) | ledger | views `acting_balance`, `seat_balance[seat]`; commands `PayEdge`, `ReceiveFromEdge`, `PayWages`, `PayActor`, `PayActorFromHousehold`, `TakeFromHouseholdPurse`, `SettleWithEdge`, `RestorePurse` (a seat named or the acting one), `RescaleHouseholdMoney`, `WithdrawHouseholdMoney`, `OpenPurse`, `CreditSeat`, `DebitSeat` |
| A seat's cash book (cash by cause, its mark, the closed years) and the year's spending | ledger (`LedgerSeat`) | views `cash_book`, `cash_causes_since`, `cash_unaccounted`; commands `NoteSeatCash`, `OpenCashBook`, `CloseCashPeriod`, `NoteSpend` |
| The founder's interest on its debt, its arrears and its default | finance (`FinanceSeat`, `Arrears.settle_interest`) | `SeatBorrower` (sim/agents) over the ledger's balance and `NoteSeatCash`; the rule is the one every borrower follows |
| The seat's business reviewed (which plants close, why) | ventures | `FounderReview` (sim/agents), asking the actors' world |
| The seat as a party to an exchange (patents, shares, offers, licences, a concern sold) | actors | `HouseholdParty` over `SeatPorts` (`sim/actors/seat_parties.py`), built for one dealing and handed to no other module; the seats, diffusion and ventures modules send `ApplyForPatent`, `MakeOffer`, `AnswerOffer`, `GrantLicence`, `SellSeatConcern` and read `concern_sale_terms` |
| The acting seat's visible scale to the state | actors (`BudgetView.acting_seat_visible_scale`) | the views `staff`, `standing`, `acting_balance`, `visible_scale` |

How a posting is made: the ledger builds, for the length of one command, a `SeatAccount` (the seat's purse and its cash book, as a party in
the book), so `ledger.transfer` makes one posting between two accounts whichever command moves the money, and the seat stands at the home
country's centre when coin is carried. Nothing outside the ledger holds it. A party that moves a seat's money does it with
`CreditSeat`, `DebitSeat`, `NoteSeatCash` and `RestorePurse`, naming the seat, so it needs no seat switch.

What stays, and why:

- `HouseholdState` holds the cause book rows (`cause_rows`, `cause_mark`) and the saving target; they are not money.
- The party holds no record of the seat's dealings or plants. It reads a copy of the seats' stored dealings (view `seat_dealings`) and the
  ventures' plants (views `operating`, `venture_opened_year`, `venture_size`), the exchange (sim/agents) changes the copy in place as it does an
  actor's record (`sim/agents/tracked.py`), and each change is sent to the owner: `SetDealing` (the whole stored field the deal left) to the
  seats, `ReleasePlant` and `AdoptPlant` to the ventures. What stays (Complaint 931): the seats' command replaces a field and does not know
  the rule that made the change, because the exchange's rules run on the party's copy.
- A party reads another seat's staff and know-how by running as that seat (`acting_as`), because `staff` and `techniques_held` answer for the acting seat.
- The ledger's views `acting_balance` and `seat_balance` read the book directly and are uncached: the actors' own code moves the book too.
- The save listing reads a save's purse from the book the save carries (`settings.purse_in_save`); the household section no longer has a `capital`.
- The equivalence tool derives the base's `/seats/<id>/household/capital` leaf from the book and relocates the cash book to the ledger's slot (sim/tests/equiv_run.py, equiv_fields.py).

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 5 / 10 |
| Old methods and properties owned (after regrouping) | 10 |
| Of those, referenced from another module's mixin code | 9 (2 classed read-only or pure by Appendix B, 7 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 11 (9 from mixins, 0 only from outside) |
| Views per used name | 0.45 |
| Views that replace exactly one referenced method and no field (one-to-one) | 0 of 5 |
| Views of other modules it reads | 1, from 1 modules |
| Commands of other modules it sends | 1 |

**Existing surface and files.** Existing: `sim/book.py` (the shared `Book`), `sim/agents/purses.py` (`Purses`, `adopt_book`), `sim/agents/edges.py`, `sim/agents/ledger.py`, `sim/economy/settlement.py` (`post`), `sim/economy/api.py` (`move_goods`, `post_transfers`, `account_balance`, `account_holdings`). The engine side is `ActorsMixin.pay_edge/receive_from_edge/pay_wages/edge` (`sim/engine/society_actors.py:54-67`) and the founder's tonnes ledger in `MaterialSupplyMixin` (`sim/engine/economy_materials.py:735-791`).

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `MaterialSupplyMixin` | `sim/engine/economy_materials.py` | 4 | 4 |
| `ActorsMixin` | `sim/engine/society_actors.py` | 4 | 4 |
| `ForwardingPropertiesMixin` | `sim/engine/core_properties.py` | 4 | 2 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `spend_last_year`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state and a per-seat dataclass `LedgerSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.holdings._material_stock_ledger` | seat | - | - |
| `state.holdings._material_stock_opening` | seat | - | - |
| `state.household.capital` | seat | <ui> 72, finance 29, <engine-functions> 21, projects 18, workforce 9, hazards 9, +10 more | <engine-functions> 4, <agents> 1 |
| `state.household.cash_flow` | seat | <engine-functions> 4 | <engine-functions> 1 |
| `state.household.cash_mark` | seat | <engine-functions> 2, core 1 | <engine-functions> 2, core 1 |
| `state.household.cash_periods` | seat | <engine-functions> 4 | <engine-functions> 1 |
| `state.household.cause_mark` | seat | <engine-functions> 1 | <engine-functions> 1 |
| `state.household.cause_rows` | seat | <engine-functions> 7 | <engine-functions> 1 |
| `state.household.spend_last_year` | seat | - | polity 1 |
| `state.household.total_spend` | seat | - | projects 3 |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `balance` | keyed | no | Net money of one actor or purse (positive is cash, negative is debt carried in the purse), in the actors' currency. `Purses.net`; read by finance for credit and by agents for their own books. | `actors.purses`, `actors.purse_lenders` | - | - | `money` | 5 |
| `acting_balance` | table | yes | The acting seat's household money; the figure every screen calls `capital`. | `capital` | `household.capital` | `balance` | `money` | 18 |
| `cash_book` | table | yes | The seat's cash flow rows, periods, mark and the cause rows of the year. | - | `household.cash_flow`, `household.cash_periods`, `household.cash_mark`, `household.cause_rows`, `household.cause_mark` | `balance` | `money` | 2 |
| `goods_stock` | keyed | yes | Tonnes the acting seat holds, per commodity key (`emp_key`). | `_commodity_ledger`, `_material_stock`, `material_stock_t` | `holdings._material_stock_ledger` | - | `stock` | 10 |
| `goods_stock_opening` | table | yes | The stock as it stood when this year's accounting began, plus the year it was struck. | `_material_opening_stock` | `holdings._material_stock_opening` | `goods_stock` | `stock` | 3 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `cash_book`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 9 methods are referenced from other modules' mixin code: 5 are replaced by a view here, 4 by a command. 0 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 11 used names, 9 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 2 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `_material_opening_stock`, `_material_stock`, `material_stock_t`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `PayEdge` | payer (default the acting seat), edge, amount, purpose | `ActorsMixin.pay_edge` and `edge`: a named counterparty that is not an actor the simulation models. It never refuses for lack of cash; a household may go negative and finance enforces the limit later. Methods: `pay_edge`, `edge` | `sim/engine/projects_starting.py:167,244`, `sim/engine/projects_ventures.py:252,323`, `sim/engine/economy_mining.py:721,944`, `sim/engine/economy_goods.py:562,579`, `sim/engine/economy_freight.py:559`, `sim/engine/step_phase_money.py:52,54,55`, `sim/engine/step_phase_projects.py:366`, `sim/engine/projects_cost_tail.py:28`, `sim/engine/ways.py:95`, `sim/engine/works.py:55`, `sim/engine/colonies.py:72`, `sim/engine/mine_deposits.py:176`, `sim/engine/core_step_phases.py:460`, `sim/engine/society_hazards.py:752`, `sim/engine/projects_completion.py:338`, `sim/engine/projects_staffing.py:751`, `sim/engine/state_demand.py:26,78`, `sim/engine/goods_market_api.py:41`, `sim/engine/labour_port.py:51`, `sim/engine/step_phase_staff.py:199`, `sim/engine/step_phase_project_start.py:300`, `sim/labour/labour_training.py:299,486,657`, `sim/labour/labour_population.py:95`, `sim/labour/labour_bondage.py:275`, `sim/labour/labour_settlement.py:193` | `unknown_edge` | - |
| `ReceiveFromEdge` | payee (default the acting seat), edge, amount, purpose | `ActorsMixin.receive_from_edge`. Methods: `receive_from_edge` | `sim/engine/step_phase_money.py:51`, `sim/engine/economy_mining.py:808`, `sim/engine/founder_sales.py:66`, `sim/engine/projects_review.py:68`, `sim/engine/economy_port_seats.py:45`, `sim/engine/goods_market_api.py:45`, `sim/engine/labour_port.py:55`, `sim/labour/labour_wages.py:118` | `unknown_edge` | - |
| `PayWages` | payer, amount, purpose | `ActorsMixin.pay_wages` and `payroll.pay_wages`: the payer's money reaches the home country's people. Methods: `pay_wages` | `sim/engine/step_phase_money.py:53`, `sim/engine/agents_port.py:67`, `sim/agents/arrears.py:37`, `sim/agents/government.py:153`, `sim/agents/business_books.py:36,55` | `unknown_payer` | - |
| `Transfer` | payer, payee, currency, amount, purpose | Direct postings in the shared book: `Purses.transfer`, `Actor.earn/spend` and the economy's clearing postings. | `sim/agents/purses.py:111,139,155,163,202,205,216,221,228,237,258`, `sim/agents/base.py:339,343`, `sim/agents/edges.py:65,69`, `sim/economy/insurance.py:81,123`, `sim/economy/funds.py:87,103`, `sim/economy/entry_year.py:77,123,136`, `sim/economy/banks.py:95`, `sim/economy/bank_founding.py:12`, `sim/economy/mint.py:157`, `sim/economy/tax_farming.py:69`, `sim/economy/mint_labour.py:68,86`, `sim/economy/api.py:478` | `unknown_account`, `unknown_currency`, `non_positive_amount` | - |
| `PostBatch` | transfers, moves | A year's clearing posted whole: `settlement.post`, `year_close` (`book.post`). | `sim/economy/year_close.py:85`, `sim/economy/settlement.py:53,95`, `sim/economy/year_goods.py:180` | `unbalanced_batch` | - |
| `MoveGoods` | moves (good, tile, units, from, to) | `economy_api.move_goods`: goods between holders in the economy's book. | `sim/engine/economy_port_cargo.py:73`, `sim/engine/economy_port_actors.py:197`, `sim/engine/economy_port_year.py:227,312,376`, `sim/engine/mod_effects.py:71,77` | `insufficient_goods`, `unknown_holder` | - |
| `ChangeStock` | seat, commodity, tonnes (signed), purpose | Direct edits of the founder's tonnes ledger. | `sim/engine/goods_market_api.py:61`, `sim/engine/living_stock_yearly.py:73`, `sim/engine/economy_electricity.py:431-433,531-532`, `sim/engine/economy_materials.py:760-781` | `insufficient_stock` | `holdings._material_stock_ledger`, `holdings._material_stock_opening` |
| `NoteSpend` | seat, amount | The year's spend counter (`HouseholdState.record spend`, `state.py:188`): accounting only, no balance change. | `sim/engine/projects_starting.py:245`, `sim/engine/step_phase_projects.py:367`, `sim/engine/projects_cost_tail.py:29`, `sim/labour/labour_settlement.py:194` | none: always applies | `household.total_spend`, `household.spend_last_year` |
| `MarkCash` | seat | `cash_mark` reset on a seat switch and at opening; the cash and cause books. | `sim/engine/core_seats.py`, `sim/engine/cash_book.py:44-48`, `sim/engine/cause_book.py:89-90`, `sim/engine/opening_money.py:24` | none: always applies | `household.cash_flow`, `household.cash_periods`, `household.cash_mark`, `household.cause_rows`, `household.cause_mark` |
| `ResetBalance` | account, amount, purpose | Opening setup and rescaling: `reset_cash`, direct `capital =`. | `sim/engine/opening_money.py:16,22`, `sim/engine/state.py:159`, `sim/agents/household.py:221,337` | none: always applies | `household.capital` |

**Direct write sites of owned fields outside this module's mixin files** (AST scan; includes the module's own function modules, and writes made through a forwarding property are marked `alias`). Each becomes a command above.

- `holdings._material_stock_ledger`: 2 sites: `sim/engine/economy_materials.py:760`, `sim/engine/economy_materials.py:768`
- `holdings._material_stock_opening`: 2 sites: `sim/engine/economy_electricity.py:540`, `sim/engine/economy_materials.py:781`
- `household.capital`: 8 sites: `sim/labour/labour_wage_ledger.py:49`, `sim/agents/household.py:275` (assign (alias)), `sim/agents/household.py:337`, `sim/agents/household.py:221`, `sim/engine/state.py:148` (assign (alias)), `sim/engine/state.py:153` (assign (alias)), `sim/engine/state.py:159` (assign (alias)), `sim/engine/opening_money.py:22`
- `household.cash_flow`: 2 sites: `sim/engine/cash_book.py:47`, `sim/engine/cash_book.py:25`
- `household.cash_mark`: 3 sites: `sim/agents/household.py:225`, `sim/engine/cash_book.py:48`, `sim/engine/opening_money.py:24`
- `household.cash_periods`: 2 sites: `sim/engine/cash_book.py:46` (delete), `sim/engine/cash_book.py:44` (.append())
- `household.cause_mark`: 1 site: `sim/engine/cause_book.py:90`
- `household.cause_rows`: 1 site: `sim/engine/cause_book.py:89`
- `household.spend_last_year`: 1 site: `sim/engine/core_step_phases.py:416`
- `household.total_spend`: 4 sites: `sim/labour/labour_settlement.py:194`, `sim/engine/projects_starting.py:245`, `sim/engine/step_phase_projects.py:367`, `sim/engine/projects_cost_tail.py:29`

## (e) Reads and sends

Reads (views of other modules), by provider:

- `foreign_trade`: `foreign_trade.lift` (economy.capacity_pool)

Sends (commands of other modules):

- `foreign_trade`: `ChangeCapacityPool`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- none of its own; it applies the postings every phase sends (the money sub-steps of `money_seat` are its commands)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| ui | 73 | `capital`, `material_stock_t` |
| agents | 31 | `edge`, `pay_wages` |
| engine/(function modules) | 15 | `capital`, `pay_edge`, `material_stock_t`, `receive_from_edge`, `_material_opening_stock`, `_material_stock` |
| mods | 4 | `edge` |
| engine/economy_port* | 3 | `receive_from_edge`, `pay_edge`, `edge` |
| engine/ui* | 2 | `_commodity_ledger`, `_material_stock` |
| engine/mod* | 2 | `edge` |
| engine/save* | 1 | `capital` |
| engine/agents_port* | 1 | `edge` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/ui reads `capital` 72 times and the material-trade quote/stock names about 7 times; `sim/agents` calls `edge` 27 times and `pay_wages` 4 times (Actor.earn/spend, government budgets); mods call `edge` 4 times (`mods/*` via `mod_effects`).

## (h) Hard spots and caches

- The founder's tonnes ledger and the economy book's units-by-tile holdings are two ledgers in different units (STATE_OWNERSHIP_MAP.md, Goods balances); nothing reconciles them. Ledger owns both but must keep two keyed views until they are one.
- `_material_stock()` mutates while reading: it creates the ledger on first call, promotes a loaded dict to `_StockLedger`, and sweeps non-physical keys into `economy.capacity_pool` (`economy_materials.py:760-772`). That last line writes a field foreign_trade owns; it needs a `ChangeCapacity` command or the sweep moves out.
- `_peek_throttle` takes a deep copy of the stock, runs the throttle, then restores stock, flows and caches (`economy_electricity.py:523-541`). A view cannot do that; materials must expose the throttle as a pure quote computed from `goods_stock` and the commit as a command (see materials).
- `HouseholdState.capital` is a property over the purse with `_local_capital` as fallback until `attach_purses` has run (`state.py:195-208`, `455`); a load or `add_seat` must call the ledger's rebind before any read.
- `PayEdge` never refuses; negative balances are legal and the credit rule is applied later (finance phase `credit_limit`). A `Pay` that refused on funds would change behaviour; keep refusals to structural causes.
- The economy's own clearing posts into the same `Book` from inside `sim/economy` (about 16 `record.book.transfer`/`post` sites); until markets sends `PostBatch`, the ledger is not the only writer.

Caches and version counters held today (feed for task 1.2):

- `_commod_ledger_cache`, `_material_commod_map_cache` (`economy_materials.py:186,199`): derived from static data, rebuilt on load.
- `HouseholdState._local_capital` and `__dict__['_purses'/'_account']` (`state.py:126,202`): bindings, not derived values.
- `_stock_throttle_sig` (signature of the stock the last throttle saw; `economy_electricity.py:511`, `goods_market_api.py:63`, `living_stock_yearly.py:76`): becomes the goods_stock version.
