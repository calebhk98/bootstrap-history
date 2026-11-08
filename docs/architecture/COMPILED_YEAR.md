# The compiled year: shared tables instead of per-item objects

**Status:** stage 1 under way (Complaint 968 is the problem this answers). The book, the year ledger, the labour core and the close are on tables (below); the market memory and the goods side are with other owners.

**Status:** stage 1 under way (Complaint 968 is the problem this answers). The book is on tables (below); the market memory and the year ledger are with other owners. Stage 2: the goods orders and their clearing are on tables (below); settlement, the ledger and entry read them through wrappers.

## Why

Most of a warm year is spent in the Python around the kernels rather than inside them: building and reading per-item
objects (`Bid`, `Offer`, `Fill`, `Settlement`, `Transfer`, `GoodsMove`, `LabourOffer`, ...), and reading the book, the
market memory and the ledger one value at a time by string key (a warm-year profile: `python3
tools/measure/warm_year_profile.py SAVE OUT.prof`; no committed command yet splits kernel time from Python time). Measure a
whole year with `python3 sim/simulator.py year-time --session SAVE --years 2 --count-instructions` (load-independent
instruction counts).

A prototype that moved goods orders into numpy columns while the rules around them stayed in Python made no gain: every
reader and writer not yet converted paid to rebuild or number objects, and numpy calls on a market's handful of rows cost
more than a plain loop. So the rule of this plan:

**A table pays only when both its writers and its readers are compiled code working over a whole good, market set or year.**
A half-converted edge is allowed as a step, but it is not measured as a result; the gate is at the end of a stage.

## Conventions

`docs/architecture/COMPILED_TABLES.md` and `sim/compiled_tables/` fix how a table looks (a `TableSpec` of documented
`Column`s, a namedtuple of numpy columns, `row_count`/`capacity`), how ids work (`IdTable`), how rows grow (`reserve_rows`
then `claim_row`), how groups are read (`group_starts` + `stable_order`), how sums are taken (`ordered_total`, never numpy
`.sum()` for a figure that must match), and how a kernel reports a problem (a `Causes` code, a `Refusal` at the boundary).
Every converter follows it, and these readability rules:

- every column has a one-line meaning and a unit; every kernel has a docstring saying what it does;
- names are spelled out (CLAUDE.md naming); no function longer than a screen; a rule is a chain of small `njit` helpers,
  which cost nothing once compiled;
- per-item Python objects exist only at the edges (save and load, the UI and protocol, mods, tests, `describe_row` for
  debugging), never inside the year loop.

## Ids (one numbering per kind, carried across years, saved)

| Kind | Admitted by | Notes |
|---|---|---|
| agent | the book, when an agent first holds or owes anything | one numbering for producers, cohorts, merchants, the state, edges; per-row flags (`is_edge`, `is_mint`, `is_external`, kind) replace string-prefix tests |
| good, trade, currency, tile, recipe | the setup | admitted mid-game when a mod or a discovery adds one |
| goods market (good, area) | the area map | redrawn areas remap through `IdTable.compacted` |
| labour market (trade, labour area) | the setup | |
| loan | the credit record | never reused |
| book slot (agent, good, tile) | the book | the stock of one holding |

Each numbering is an `IdTable` saved as its ordered name list, so a loaded game numbers exactly as the live one did
(CLAUDE.md: order must not depend on history). A leaver keeps a dead row until a year boundary compacts it.

## The tables and their owners

| Table | Owner module | Replaces |
|---|---|---|
| balances (agent x currency), stocks (slot) | `sim/book.py` | the book's dicts and per-key reads |
| transfer postings, goods-move postings (append-only per year, applied by a kernel, all-or-none per batch) | `sim/book*.py` | `Transfer`, `GoodsMove`, `move_many`, `transfer_many`, `post_settled` |
| market memory, market-indexed (price, usual price, cleared price, trade age, quote kind, volume, years without bids/offers; wages by labour market) | `sim/economy/market_memory*.py` | the `good|area` string-keyed stores and `area_of` reads |
| year ledger: agent vectors (money out, sales in, wages in, plant spend), (agent, good) rows (received, sold, output), market vectors (delivered, unmet) | `sim/economy/year_ledger*.py` | `YearLedger`'s dicts |
| goods bids, goods offers, goods market results, pairs | goods side | `Bid`, `Offer`, `ClearingResult`, `ArrayClearing`, `Pairing`, `Settlement`, `LeftMarket` |
| labour bids (tranches expanded in the kernel), labour offers, labour market results, hired hours (market x employer) | labour | `LabourBid`, `EmployerHoursBid`, `LabourOffer`, `LabourClearing`, `LabourResult`, labour `Fill` |
| producers, cohorts (updated in place) | close, entry | `replaced(producer)` and `put_producer` per change |

Each table's owner is the only module that writes it outside a kernel the owner provides (CLAUDE.md: one owner per fact);
other modules read through the owner's view or call the owner's kernel.

## The book on tables (stage 1, done)

`sim/book_tables.py` declares every column with its meaning and unit; `sim/book_store.py` holds the ids and tables;
`sim/book_apply.py` and `sim/book_plan.py` are the posting kernels. Ids: agents, goods, tiles, currencies, agent kinds and
purpose templates are `IdTable`s saved with the book (the record's `numbering`), so a loaded book numbers as the live one did.
Agent flags (`is_edge`, `is_mint`, `is_external`, `kind`) are set once at admission and replace string-prefix tests. Balances
are one row per (agent, currency) at `agent * stride + currency`; stock slots are rows found through a hash index on the packed
(agent, good, tile), chained per agent in the order they were made. A purpose is a template id plus a reference id
(`sim/book_purposes.py`); the year's goods moved per (good, purpose) are rows of a flows table.

**How a converter posts.** It holds ids (`book.agent_number(name)` and the like admit a name), appends rows to a
`TransferPostings` and a `GoodsMovePostings` table (rows grouped by batch, batches rising; a batch is all-or-none, money checked
before goods), and calls `book.apply_postings(transfers, moves, batch_count)`. It gets one `BatchOutcomes` row per batch (a
cause code from `BOOK_CAUSES` and the offending cell) and turns a refused batch into a refusal with `book.refusal_of`. **How it
reads:** the kernels in `sim/book_read_kernels.py` (`read_balances`, `find_slots`, `read_stocks_at`, `holder_columns`,
`counted_stocks`, `currency_values`) take the book's tables from `book.tables()`, `book.balance_table`, `book.stock_rows`; an id
below zero reads as nothing held. Re-fetch tables after any call that may admit a name or reserve room (a grown table is a new
object). The methods callers use today (`balance`, `stock`, `post`, `post_settled`, ...) are wrappers over the same kernels.
`tools/measure/book_index.py` shows why slots are found through a hash.

## The year ledger on tables (stage 1, done)

`sim/economy/year_ledger_tables.py` declares every column; the ledger owns no numbering. Rows are keyed by the book's agent, good and
purpose numbers and the market memory's goods-market, labour-market and trade numbers (`YearLedger(book=..., markets=...)`; a ledger made
bare, as a test does, gets a book store and market tables of its own).

- **Agent figures** (row = agent number): `money_out`, `wages_in`, `sales_in`, `plant_spend`, `plant_worn`, `hours_sold`, `spare_hours`,
  each with an `order_*` column (place in entry order, 0 = not a member); and for the three nested figures (`received`, `grown`,
  `hours_hired`) the agent's presence, entry place and first and last row.
- **Pair rows** (hash index `KeyedRows` on the packed agent, subkey, extra): `received`, `grown`, `sold`, `output`, `hours_hired`,
  `hours_hired_by_market` (hours and money), `imports_paid`, `exports_received`. The subkey is a good, a trade, a labour market, or a
  purpose template with its reference in `extra` (the foreign-money figures keep the purpose the book numbered).
- **Market figures** (row = goods-market number): `delivered`, `unmet`; **clearing rounds** (market, quantity, price), whose totals
  (`round_totals`) are summed exactly as `math.fsum` does, so the figures match the dict ledger bit for bit.

**Entry points for converters** (`year_ledger_arrays.py`, reached through `YearLedger.add_money_out`, `add_income`, `add_pair_amounts`,
`note_settlement_rows`, `note_hours_rows`, `note_round_rows`): they take numbers and arrays, one row per agent in a settlement, per fill,
or per round, and may hold many settlements in one call. `YearLedger.note_settlement`, `note_hours`, `note_clearing` and `note_output`
keep the object signatures: they append to plain lists (`year_ledger_batch.py`) and a read of a table first adds the rows of the kind
it waits on in one kernel call, so a year's thousands of settlements cost a few calls. The attribute API (`ledger.money_out["farm"]`,
`ledger.hours_hired.setdefault(...)`) is unchanged: `year_ledger_views.py` and `year_ledger_pair_views.py` show the tables as
dict-likes in entry order. Reading one cell through a view costs more than a dict get did, so a reader that loops over agents should
use `get_many` or, once it is converted, the tables. Not on tables yet: the clearings, fills and bids (objects the goods side owns),
labour results, mint takes, `crew_hours_bought`, `own_plot_hours`, `grown_units` and `carried_in`.

## Goods orders and clearing on tables (stage 2, first part)

`sim/economy/goods_order_tables.py` declares six tables, every column with a meaning and a unit: `GoodsBids` and `GoodsOffers`
(one row per order in the order it arrived, with the result columns the clearing writes in place), `GoodsMarketResults` (one row
per market cleared by the batch), `GoodsPairs` (one row per bid-and-offer pair that traded) and `BidOrder`/`OfferOrder` (the rows of
each cleared market in clearing order). Ids are the book's (`agent_number`, `good_number`, `tile_number`) and the market memory's
(a goods market is the row of `good|area` in `MarketTables.goods_markets`). Ids are numbered by arrival, the rules sort by name, so
the clearing ranks names once (`goods_table_group.name_ranks`) and sorts rows by those ranks.

`goods_order_book.GoodsOrderBook` is what `year_goods.clear_goods` clears. Kernels append whole arrays of rows (`append_bids`,
`append_offers`: the households' bids by `households_bid_rows.cohort_bid_rows`, the producers' offers by `_OfferRows`). Everything else
still hands over `Bid` and `Offer` objects, through `add_orders` or the dict door (`book.setdefault((good, area), ([], []))[0].append(bid)`
that the mint, the state, lending and the engine use); an object waits and becomes a row in arrival order the next time the tables are
read. Objects are made from rows only at an edge (`bids_of`, `offers_of`, lazily: `goods_table_views.LazyObjects`).

`goods_good_clear.clear_good` clears one good's markets in area order. A market takes one of three ways: traded in the batch
(`goods_table_pack` packs columns for `goods_year_kernel.decide_markets`, `goods_table_clear` writes the answer back, `TableClearing`
is the `ArrayClearing` that reads the tables), did not trade (`goods_table_quotes`: the quote and the wanted quantity from columns), or
the rules still written over objects (a book edge selling, a good outside the year arrays). A market on the tables carries its rows
(`goods_market_rows.MarketRows`), and the respend pack, the memory's notes and `_remember_markets` read them as lists of columns.

**What a converter of the next phase finds.** Settlement still takes `ArrayClearing`s: `TableClearing.batch` offers the allocation
arrays (`pair_ptr`, `pair_bid`, `pair_offer`, `pair_quantity`, `ask`) and `(agent, tile)` views of the rows, so
`settlement_arrays` works unchanged; the same figures are in the `GoodsPairs` and `GoodsMarketResults` tables. The year ledger is still
handed `ClearingResult`s (`note_clearing`). `ledger.bids_by_market` holds a lazy list per market that the entry rules read as `Bid`
objects (`entry_trial.demand_at`, `entry_margin`); they are what builds objects at the end of the year until entry reads columns.

**Where the gain waits.** A measured year with this stage shows no clear gain in the goods phase: the objects are gone from the writers
and the batched clearing, but settlement, the ledger, the entry rules and the many sources that still hand over objects rebuild or
read them, which is the prototype's lesson again. `python3 sim/simulator.py year-time --session SAVE --years 2 --count-instructions`
(and `tools/measure/warm_year_profile.py`) measure it.

## Stages

1. **Foundations, in parallel:** the book as tables with the two posting tables; the market memory as market-indexed
   arrays; the year ledger as tables. Each keeps its present Python methods as thin wrappers so callers not yet converted
   still work, and adds whole-table kernels for converted callers.
2. **Goods and labour on the tables:** orders written by the kernels that compute them, clearing and settlement reading
   and writing tables, no per-item objects from plans to the ledger.
3. **Close, then entry and credit** (variable-length searches and greedy queues; the smallest share of the year).
4. **Every remaining reader in the year loop** reads the tables in blocks, and the per-item wrappers leave the year loop
   (they stay only for the UI, the protocol, saves, mods and tests). The packages, each with its own files:
   - labour readers in the economy (hours cleared, national wages, people by trade, flight, scaling);
   - the goods unit's far end (goods settlement, the ledger's clearing notes, the memory's notes after clearing, the
     respend pack, production moves);
   - plans and the rare order sources (plan bids as rows, outlay room, land, mint, state, lending, merchants, carriers);
   - entry, exit and credit (entry plans and siting, exits, loans as a table, the close's loan loop, worths);
   - price and wage reads through the year view (priced needs, live input prices and wages, wage grids, kept figures);
   - the phases outside the economy step (actors, government, theft, revolts, the year's accounts).

The year is judged when the conversion is complete: a partial conversion is expected to cost more than it saves, since
every unconverted reader pays the wrapper. Instruction counts after each merge are kept as progress, not as a gate.

Every step keeps the game's rules: the year-time digest may move only by float order (`tools/measure/save_compare.py` on
two-year saves shows dust only); a jump in a discrete value is traced before merging. Save and load round-trip
(`year-time --reload-check`).

## Labour offers as a table (stage 2 groundwork)

`sim/economy/labour_offers_table.py` holds the year's offers, one row per cohort x trade, with the supply parameters as
columns and `sold_hours`, `kept_hours` as outputs; `labour_offers_kernels.py` builds the matrix the labour clearing kernels
read (`offer_matrix`) and settles the offers at the cleared wages (`settle_offers`). `HourSupply` is the thin wrapper for
callers not yet on the table. Where a plot rule is a bare function, or a caller replaces a market's schedule in the
`hours_sold_at` mapping (`MarketHours`), the plain path takes it. Stage 2 plugs in at three named seams: the shared agent
numbering replaces the per-year cohort numbering (`LabourIds`), the cohort offers are written as rows by the code that makes
them (today `labour_offers_table.build_labour_offers` reads `LabourOffer` objects), and the cleared wages arrive as a
market-indexed array from the market memory (today a dict read in `HourSupply.settle`).

## The labour core as tables (stage 2)

`MarketState` (`sim/labour/market/market_state.py`) holds what the labour core carries between years in the tables of
`state_tables.py`: workers (a row per area x trade pair, people per ability band), markets (wage, ask, and where the pair's hired
hours and cohorts sit), hired hours (a row per market x employer), and trainees (a row per cohort, grouped by market). Areas and
trades are numbered in sorted name order (`state_ids.SortedIds`), so a grid row is `area * trade_count + trade` and a kernel visits
areas and trades in the order the Python did by counting up. Employers are numbered once, in arrival order, through an `IdTable`,
and `EmployerIds.rank` gives the place of a name among all names for the sorts that go by name. The seam for the economy's shared
agent numbering is `LabourIds(employers=...)`: hand the shared `IdTable` in and the core numbers its employers with it.

The old dict API is `state.workers`, `.trainees`, `.wages`, `.asks`, `.hired_hours`: live views (`state_fields.py`, `state_views.py`)
over the tables that list areas and trades in the order they were given their entries, and `to_plain` and `from_plain` round-trip
nested dicts, so the save, the economy's readers and the tests do not change. A view names its pair, so it stays right when a new
area or trade renumbers the grid. A reader that loops over the views pays for them: code inside the year reads the tables.

The year's rules, each a chain of small `njit` helpers over the tables:

| Rule | Python entry | Kernels |
|---|---|---|
| bids as columns; tranches cut in a kernel | `bid_book.py` | `cut_into_tranches` |
| clearing: heads, employers, hiring rounds, finish, state written | `clearing_arrays.py`, `clearing_tail.py`, `clearing_write.py` | `clearing_kernel`, `clearing_tail_kernel`, `hiring_kernel`, `clearing_write`, `clearing_pack` |
| training | `training.py` | `training_kernel.py` |
| switching, with the incomes it weighs | `switching.py` | `switch_year.py`, `switch_kernel.py`, `income_kernel.py`, `cohort_book.py`, `switching_kernel.py` |
| migration | `migration.py` | `migration_kernel.py` |
| formation of empty trades, bonded purchase | `formation.py` | `formation_year.py`, `formation_kernel.py`, `formation_buy.py` |

The clearing's results are `Clearings` (`clearing_results.py`): columns, with `LabourClearing` objects built from them on demand for a
reader outside (`report.clearings` iterates as objects). The later phases read the same results on the grid (`results_grid.py`).
`exact_sums.py` holds `sum`, `math.fsum` and `math.sumprod` as kernels, so a rule moved into a kernel adds the numbers the way the
Python did and the year-time digest stays the same. The plain Python of the rules moved here is kept in `sim/tests/labour_*_plain.py`,
and each rule has a test that runs both on random inputs (`sim/tests/test_labour_*_tables.py`).

Measure the labour year alone with `python3 tools/measure/warm_year_profile.py SAVE OUT.prof` (call counts, `run_year` in the
profile) and the whole year with `year-time --count-instructions`. A mod that replaces `fetch_wage`, or a schedule that is not packed,
still takes the plain path through `clearing._prepare` and `_finish`.

## Labour settlement on tables (stage 2)

`clear_labour` (`sim/economy/year_labour.py`) settles every labour market of the year from the core's result tables in a few calls;
no `LabourResult`, `Fill`, `Pairing` or `Settlement` is made per market in the year.

| Step | Module | Does |
|---|---|---|
| columns | `labour_fills.py` | `rows_from_clearings` reads the core's `Clearings` (market rows, the hired table); `rows_from_objects` takes a plain list of `LabourClearing`s. `fills_of` adds the sells (hours hired shared over a market's offers by hours offered, the sum taken in the offers' order) and sorts each side by name. An agent is a `ref`, its place in the sorted names of the year |
| pairs | `labour_walk_kernel.py` | `walk_pairs` is `settlement_limits.pair_fills` over all markets; `market_agents` lists each settlement's agents (buyers used, then new sellers); `fill_slots` gives the ledger's slot per distinct agent of a market |
| book | `labour_wage_kernel.py` | `settle_wage_markets` runs `settle_pairs` and `book_apply.apply_settled` market by market on the balances the earlier ones left, and grows the currency's gross total by the exact sum paid: what `Book.post_settled` did, market after market, in one kernel call. A market the book refuses is replayed through `post_settled` so the error is the old one |
| ledger | `labour_settle_year.py` | `settle_year` calls the above and feeds `YearLedger.note_settlement_rows` and `note_hours_rows` once each |
| results | `labour_results_table.py` | `LabourResults` stands where the ledger's list of results stood; its items are `LabourResult`s built from the columns on demand, `fills` on first use. `hours_totals`, `bought_value` and `hours_by_market` read the columns |

Ids: the core's employer ids are not the book's. They are mapped to the book's agent numbers once a year with one array
(`numbers_of_refs`), admitting a name the book has not met in the order the old per-market path did. Handing the book's `IdTable` to
`LabourIds(employers=...)` was not done: the core admits into the table it is given, and the book must also give an admitted agent
a row in its own tables, so the core would have to admit through the book.

Who still builds the objects: `year_labour._result` (one `LabourResult` of a clearing and its offers; the reference the tests compare
with), `settlement.settle_labour` and `YearLedger.note_labour`/`note_hours` (tests and the reference ledger), `LabourResults` items
(`economy._outcome` reads totals from the columns; `year_close.close_agents` iterates the items, without their fills, only when
carriage hours hire), and the offers (`LabourOffer`, built upstream and by `HourSupply.settle`). Measure with
`python3 tools/measure/warm_year_profile.py SAVE OUT.prof` (the calls of `settle_labour`, `settle_many`, `post_settled`, `_result` are gone) and
`year-time --count-instructions`. The tests are `sim/tests/test_year_speed_labour_settle.py`.

## Labour readers in the economy (stage 4, first package)

The economy's readers of the labour core read its tables in blocks (`sim/labour/market/state_reads.py`, kernels in
`state_read_kernels.py`, both behind `sim/labour/api.py`), where they iterated the dict views one value per call. A figure that
was a `math.fsum` or a `sum` of a list is the same kernel (`exact_sum`, `python_sum`), so digests do not move.

| Reader | Block read |
|---|---|
| `LabourRecord.hours_cleared_in`/`hours_cleared_by`/`hours_cleared_in_markets`, `people_in_markets` | `hours_cleared_at`, `people_at` over grid rows from `grid_rows_of` (a name the state does not number is row -1, read as nothing) |
| `national_prices.national_wages` | one `wage_means_by_group` call over every remembered wage, hours and people read as arrays |
| `country_figures.people_by_trade`, `labour_state.people_by_trade` | `people_by_trade_over` (areas added in the order given) |
| `labour_state.PeopleByTile.working_people` (the levy) | `working_people_in_areas` |
| `labour_state.scale_people` | `scale_people_in_area` |
| `labour_state.mirror_wages` | `wages_in_view_order` (areas in the order named, trades in the order they got a wage) |
| `flight_step.mean_year_income`, `people_before`; `records.people_in`, `MarketState.area_people` | `people_weighted_wage_by_area`, `people_in_areas` (trades in the workers view's order, then cohorts) |

Each block read has a test against the per-item path on written-out inputs (`sim/tests/test_labour_state_reads.py`,
`test_economy_labour_readers.py`). Measure with `python3 tools/measure/warm_year_profile.py SAVE OUT.prof` and look for calls into
`state_views.py`, `state_fields.py` and `state_ids.py`: those are the readers still on the views.

## The goods unit's far end (stage 4, first package)

`year_goods.clear_goods` settles, notes and remembers a good's markets from the order tables in blocks. Per good:

| Step | Module | Does |
|---|---|---|
| settlement | `settlement_ids.py` | `settle_by_ids` reads the pairs of the good's traded markets (the batch's pair arrays, which are the `GoodsPairs` rows) as agent and tile numbers from the bid and offer tables, numbers the (agent, tile) keys and the agents in the order `settlement_batch.KeyTable` did (`settlement_numbering.local_numbering` cuts them by market), runs `settlement_batch_kernel.settle_markets` (purses and stocks carried market to market in area order) and applies the sums with `book_apply.apply_settled`; no `KeyTable`, no names, no `Settlement` |
| ledger | `goods_settle.py` | one `YearLedger.note_settlement_rows` call per good (the plant purchases, the foreign-money figures and the mint's takes from columns) and one `note_round_rows` call for the good's clearings; the respend rounds are noted the same way (`goods_respend_unpack.note_rounds`) |
| memory | `goods_idle_years.py`, `goods_memory_kernels.py`, `goods_memory_notes.py` | the years without bids or offers of a good's markets are one kernel call; `_remember_markets` reads last year's quote flags and usual volumes as columns, works out every signal, then one kernel writes quote kinds, prices, usual prices and cleared prices in sorted (good, area) order, and the usual volumes are written the same way; the trade ages are `note_year_traded` over the markets that delivered |
| production | `goods_production.py`, `producers.production_lines` | the turn's input stocks, output stocks, purses and running costs are read as arrays; the production moves of all the turn's producers are one `GoodsMovePostings` batch and the output is added to the ledger by `add_pair_amounts`; a name the book has not numbered takes the `Book.move_many` path |

A good takes the object path (`settlement.settle_goods_many`, `YearLedger.note_settlement`) when one of its traded markets is not a `TableClearing`
of the good's batch (a mod replaced the rules). Tests: `test_goods_settle_ids.py` (the id path against `settle_results` on random batches),
`test_goods_memory_notes.py`, `test_goods_idle_years.py`, `test_goods_production.py` (each kernel against the wrapper calls it replaces).

Still reading goods objects: `ledger.clearings` and `ledger.mint_takes` keep the `ClearingResult` of every market (the mint and entry read
them); the watchers' buy fills are `Fill` objects (`bought_by`, only for markets a merchant or the state bought in); `LeftMarket` and its
`bought` mapping (built from columns when the respend pack asks); the respend pack and unpack still mix columns and objects; the markets cleared
on the rules over objects (a book edge selling, a good outside the year arrays); `producers.production_lines` and `producers.offers` are
the rules over one producer; `ledger.hours_hired.get` is a per-producer view read.

## The close on tables (stage 3)

The close reads the book and the ledger with kernels, posts its dividends, wear, spoilage and consumption as posting tables, and
makes the producers' new records once from the close kernel's answer. Decision rule kept from stage 1: a kernel replaces the Python
only where it adds, orders and numbers exactly as the Python did, so the year-time digest is the same.

| Step | Python entry | Kernels / tables |
|---|---|---|
| the pack: stocks, held goods, the ledger's sales, costs, sold, made, hours hired | `close_pack.py` | `close_pack_kernels.py`: `slot_stocks`, `held_goods` (exact sum of the tiles, as `math.fsum`), `pair_values_by_slot` |
| producers' dividends: `shares.split_dividend` and `ownership.spread` | `year_close_dividends.py`, `year_close_owners.py` | `year_close_dividend_kernels.py`: `dividend_rows` (rows in the order of the payments), `add_in_order` (the property income) |
| producers' new records and the plant worn | `year_close_records.py`, `year_close_ledger.py` | `set_in_order` over the ledger's `set_figure` |
| the rows that need the credit record: exits, write-offs, loan requests, rebuild plans | `year_close_producers.py` (`_effects_by_row`) | Python, in producer order, over the few hundred such rows |
| wear and spoilage, coin wear | `wear_year.py` | `wear_kernels.py`: `loss_moves` |
| households: receipts (received and grown), wages, spending, consumption | `year_close_households.py` | `year_close_household_kernels.py`: `receipts_with_grown`, `consumption_postings` |

**Order the tables keep.** Posting rows come out in the order the objects were made, and a batch is all-or-none as before: all the
non-exit dividends are one batch, applied after the exits (which post as they happen); wear and spoilage are one batch each, both
worked out from the stocks before either is booked; consumption is one batch per cohort, in one `apply_postings` call. The book
numbers the names a batch meets *together, in name order* (`IdTable.admit`), so the close numbers an unseen name through
`year_close_dividends._numbers` and `year_close_households._number_unseen`, not one at a time; purposes are encoded in the order
they first appear. The property income dictionary gets each payee's payments added in the order of the producer rows, exits
included (`add_property_income`), so each sum and the order of new keys are the loop's. A cohort's consumption changes only its own
stock, so reading the stocks once for all cohorts gives what reading them after the earlier cohorts' moves gave.

**What still builds Producer and Cohort objects.** The close's answer is columns; `closed_records` makes one new `Producer` per
producer from them (a copy of the old record's fields with the changed ones replaced) and `producer_table.put_producers` puts them
back at once, where `replaced(...)` and `put_producer` ran per producer in a loop with a dictionary of changes. The records are
still read by entry (`entry_year`, `opening`), the next year's plans (`plan_year`, `year_goods`, `seller_offers`, `land_bid_year`),
the labour state, equity and tax-farming code, the save and the screens: about forty modules read `record.producers`. Retiring the
record needs those readers on the columns first. Cohorts are replaced one by one in `close_households` (`closed_cohort` reads the
market view per cohort, which stays Python). Exits (`producer_exit.ExitBatch`, seven stores), loan write-offs and loan requests stay
Python, in producer order.

**Measure.** `python3 sim/simulator.py year-time --session SAVE --years 2 --count-instructions` for the whole year;
`python3 tools/measure/warm_year_profile.py SAVE OUT.prof` for call counts of the close (`close_agents`, `close_producers_of_year`).
Tests: `sim/tests/test_close_pack_kernels.py`, `test_year_close_dividends.py`, `test_year_close_records.py`, `test_wear_kernels.py`,
`test_year_close_households.py` (each kernel against the Python it replaces on written-out inputs).


## Entry, exit, credit and worths (stage 4, first part)

Done: the worths read the book's stocks in blocks (`year_arrays_worths.packed_stock` calls `close_pack_kernels.held_goods` once for
every producer; a good the matrices have no column for gets a column past them and is priced where it was before); the
producers' cash comes from `book.balances_at`. Entry's stakes, the owners' restakes and the exits post through
`economy/posting_sequence.post_in_order`: the steps are turned into rows in step order (so the book numbers its names as it did
posting them one by one), applied in one `apply_postings` call, one batch per step, and a refused step is replayed through the object
path to raise the book's own error. `open_entrants` keeps the owner's cash as the earlier stakes leave it and posts the stakes after
the plans are applied; `ExitBatch` collects the postings of each exit (repayments, dividend, goods) and posts them at `finish()`, which
is safe because an exit reads only its own cash and goods.

Loans are on a table (next section). Not done, and why (measure with `python3 tools/measure/warm_year_profile.py SAVE OUT.prof`):

- **Entry reading columns.** The remaining entry cost is spread over thin Python (the plans' loops, `unfilled`, `gap_at_entry_price`,
  `demand_at` over `Bid` objects, the per-call glue of `EntryTables.siting`). The bids come from `ledger.bids_by_market`, which the
  goods side fills with `LeftMarket.all_bids` (first-round rows plus later rounds' `Bid` objects): entry can read GoodsBids columns
  only when that owner hands over per-market column blocks (floor, flexible, reference price, elasticity, budget, maximum price).

## Loans as a table (stage 4)

`sim/loans/` holds the term loans as one column table, `Loans` (`columns.py`: every column has a meaning and a unit), and nothing else
holds a copy. `LoanStore` (`store.py`) owns the table and the numbering of its names: lenders and borrowers, currencies, collateral
tiles and kinds are `IdTable`s of the store's own (kernels never iterate agent numbers; every sort by name goes through a rank array, so
the numbering can differ between a live game and a loaded one without changing a sum), and each loan has a number that is never
reused, with its id text in `texts`. Rows stay in the order the loans were struck, which is the order the credit market's sums follow.
The save is the same list of records as before (`records()`, `load()`), so a save round-trips and its digest is unchanged.

| Was | Now |
|---|---|
| `record.credit.loans`, a list of mutable `Contract`s changed in place | `LoanList` (`view.py`): rows read and written through `LoanRow`; a write bumps `store.version` |
| whole-list replacement (service, write-offs, exits, bank code, debt relief) | `store.retain(mask)` (drop rows), `store.gather(order)` (drop and reorder), `store.replace_all` (a test's or a rare caller's list) |
| `transfer_loan`, `shrink_collateral`, `Contracts.rename` | `store.split_off`, `store.shrink_collateral`, `store.rename` |
| `credit.service_split` over a sorted list | `credit_service.serve` over the due rows, sorted by id text: kernel `service_loans`; the answer is arrays (a row per loan served, a slot per lender for the `Receipt`) and the table is changed after the losses it causes are booked (`apply_served`) |
| `Transfer` per payment and per disbursement | rows posted by `transfer_rows.post_payments`; names are numbered as `transfer_many` numbers them |
| `credit.clear_with_cause` | `credit_clearing.clear_with_cause`: requests and offers are packed into `ClearingRequests` and `ClearingOffers`, kernel `clear_loans` fills the new-loans table, the requests' output columns and the base rate |
| claims, debts, principal and arrears history by borrower | `reads.py` over the columns (`credit_claims` sends a `LoanList` there and any other sequence of loans through its Python) |
| the close's loan loop, write-offs | `close_kernel.producer_loans`, `write_down_kernel.write_down` |

**Who still holds a `Contract`.** Objects are made from rows only at the edges: `store.snapshot(row)` for the UI, the protocol, mods and
tests; the loans a clearing struck (`LoanClearing.loans`, which `economy._lend`, `credit_lines.split_lines`, `banks.draw_deposits`, `shares`
and `lending.bid_household_loans` still read as a list before `add_loans` packs them); the `Default`s that `titles.foreclose`,
`bondage.enter` and `credit_claims.losses_by_lender` take (made from the kernel's rows, few); a producer's loans at an exit
(`producer_exit`); and the `LoanRow`s that the bank rules (`banks`, `bank_runs`, `bank_service`), `funds.marked_holdings` and
`secondary_trade` hold for the handful of loans they weigh one by one. A `Contract` handed to `add_loan` is copied: change the row it
returns, not the object. The loan requests are still `LoanRequest` objects in `record.credit.loan_requests` (their writers are the
close, entry and the state); they become a table at the clearing.

**Tests.** Each kernel against the Python it replaced, on random inputs, equal to the last bit: `test_loans_service_kernel`,
`test_loans_clearing_kernel` (the Python is `sim/tests/credit_clear_plain.py`), `test_loans_reads`, `test_loans_write_down_and_close`,
`test_loans_store` (`sim/tests/loans_plain.py` is the service, write-off and close Python). Bank paths: `test_bank_runs`,
`test_economy_banks`, `test_secondary_trade`, `test_funds` run on the table; the same bank scenarios were run in the tree before this
change and after it with identical end states.

## Plans and the rare order sources (stage 4, one package)

**Plans.** `plan_year.plans_of` returns a `PlanTable` (`plan_table.py`): producer columns (`runs`, `wanted_runs`, `wage_line`, and the two
sums the readers need, `budget_total` and `outlay_total`, added by `plan_sums` exactly as Python's `sum` of floats adds them) and one
row per input bid and per labour bid, grouped by producer in slot order (`plan_table_rows.py` reads the plan kernel's answer into the
rows with `np.nonzero` over the recipe masks; the few producers `producers.plan` still plans have their `Plan` read into the same
rows). `outlay_room.by_plan_table`, `land_bid_year.write_firm_land_bids`, `land_market` (through `wanted_runs_by_id`) and the goods
clearing (`PlanTable.get(id).runs`) read the columns; `plan_table.write_bids` hands the bid rows to the book of orders. `Plan`, `Bid`
and `LabourBid` are made only at an edge: `plan_of(id)` (tests, screens) and `labour_bid_objects()`, the one call into
`year_labour.clear_labour`, which still takes a list of labour bids.

**Block reads.** `stock_block.stock_block(book, agent_numbers, good_numbers, tile_numbers)` reads any number of stock cells in one kernel
call (`numbers_of` turns names into ids). `plan_year.stocks_by_slot` and `households_orders_pack.kernel_orders` use it.

**One door for the rare sources.** `order_rows.OrderRows(order_book, source)` collects a source's bids and offers by name
(`bid`, `offer`, or `bids_from`/`offers_from` for a rule that still makes objects) and `write()` hands them to the book. The mint, the
state (`state_budget.goods_bids`, `state_store` through `year_order_sources.state_orders`), the households' tool bids and plain-path
bids, merchants and their carriers (`year_order_sources.merchant_orders`), the engine's seat orders, firm land bids and plant bids all
write through it. `order_book_named.NamedOrderBook` (what `economy.py` makes with `new_named_order_book`) keeps these rows and the plan
table's in the book's own arrival list and numbers the names of everything waiting as one batch at the flush, so agents, goods, tiles
and goods markets are numbered exactly as when each order waited as an object (the market numbering is saved, so a digest sees it).
A plain `GoodsOrderBook` or a `{(good, area): (bids, offers)}` dict still works as the target (tests).

**Still objects.** The rules `households.goods_orders` (a basket with share limits), `households_store.store_bids/store_offers`,
`tool_wear.tool_bids`, `merchants.orders`, `carriage_fleet_book.bids`, `land_bid.hectare_bid` and `producers.plan` build `Bid`/`Offer`
objects inside the rule; they are unpacked into rows at the call (`bids_from`), never handed to the book. `lending.bid_household_loans`
still uses the dict door.

Measure: `python3 tools/measure/warm_year_profile.py SAVE OUT.prof` for the call counts of `stock`, `balance`, `make_bid` and
`plans_of`; `year-time --count-instructions` for the whole year. Tests: `sim/tests/test_year_speed_plan_tables.py`,
`test_year_speed_plans.py`, `test_year_speed_cohort_orders.py`.

## The phases outside the economy step (stage 4, last package, first part)

The phases outside `Economy.step` (the money phases, revolts, the market wrapper) are a small share of a warm year. Measured with a
profile of those phases (a handler wrapper over `year_phases.SHIPPED` and `tools/measure/warm_year_profile.py`): most view
computations are cheap lookups; the cost is the first work of a figure after the economy stepped (shown prices, the floor costs of
every tile, a price response), plus the same figure asked again with the same inputs. Only the repeats were removed:

| Figure | Was | Now |
|---|---|---|
| price response of a book (`economy.api.price_response`, `prices_at.price_response_at`) | cleared again for every ask, state costing and the household's holdings asking the same order | `response_memo.price_response`: kept against the book object it was cleared from; a new clearing makes a new book object, so nothing stale is served |
| floor costs of a tile and of a country (`country_figures`) | worked out per ask | `quiet_year.kept`, like the prices: once while the economy stands between steps |
| money value of an unskilled hour (`labour_wage_schedule.money_per_labour_hour`) | built a priced copy of the schedule to read one field | the field itself (`_hour_money`); `trades.field_of` skips the abstract-class check for a plain dict |
| `year_accounts._cohorts`, `_goods` | read the ledger one cohort and one good at a time through the view | `NestedView.as_plain()`: every agent's rows in one pass over the table; the hunger need's goods are worked out once per tile |

Digests are unchanged (Rome two years with reload, England five). What is left outside the step is the first work of those figures
(`country_figures.prices`, `kept_need_prices` per tile, the price solver's tables after a step), which belongs to the price and wage
reads, and the unconverted workforce views declared `cached=False` (`money_per_labour_hour`, `trade_registry`, `wage_signature`,
...), which the assembly cannot cache until their owner bumps its channels on every write. Tests: `sim/tests/test_response_memo.py`,
`test_year_accounts.py` (`PlainLedgerReadTests`), `test_year_ledger_views.py` (`as_plain`).
