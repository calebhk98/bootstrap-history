# The compiled year: shared tables instead of per-item objects

**Status:** under way (Complaint 968 is the problem this answers). The book, the year ledger, the goods orders and their clearing, the
labour core with its bids, offers and settlement, the close, the loans, the plans and the merchants' expectations are on tables. What
is left is one list, "What is left" at the end; per-section descriptions say what each owner has today.

## Why

Most of a warm year is spent in the Python around the kernels rather than inside them: building and reading per-item
objects (`Bid`, `Offer`, `Fill`, `Settlement`, `Transfer`, `GoodsMove`, `LabourOffer`, ...), and reading the book, the
market memory and the ledger one value at a time by string key. No committed command splits kernel time from Python time; the
measuring commands below show where a year goes.

A prototype that moved goods orders into numpy columns while the rules around them stayed in Python made no gain: every reader and
writer not yet converted paid to rebuild or number objects, and numpy calls on a market's handful of rows cost more than a plain
loop. So the rule of this plan:

**A table pays only when both its writers and its readers are compiled code working over a whole good, market set or year.**
A half-converted edge is allowed as a step, but it is not measured as a result; the gate is at the end of a stage.

## How to measure

| Question | Command |
|---|---|
| How long does the whole year take, and how many instructions? | `python3 sim/simulator.py year-time --session SAVE --years 2 --count-instructions` |
| How long does a named function take in a warm year (plain timers, no profiler inflation)? | `python3 tools/measure/function_times.py SAVE module:function ...` |
| Who calls what, how often (cProfile; inflates Python-heavy code, so read call counts, not seconds)? | `python3 tools/measure/warm_year_profile.py SAVE OUT.prof`, then `pstats` sorted by `tottime` |
| Did a change move the game? | `tools/measure/save_compare.py` on two-year saves (float dust only); `year-time --reload-check` for the save round trip; `python3 -m sim.tests.fingerprint` where behaviour must not change |
| Does a fresh spin-up depend on the hash seed? | `python3 -m sim.tests --slow --only hash_seed_order` |
| Do a topic's tests pass? | `python3 -m sim.tests --slow --only TOPIC` |
| Do the table types keep their cache names? | `python3 tools/check_table_names.py` |

**The bar.** A conversion is worth making when the function it replaces is at least about one percent of a step, measured with
`function_times.py` against the whole step from `year-time`. A function below the bar stays Python, and its section says so. Every
conversion keeps the game's rules: a jump in a discrete value is traced before merging, and float sums keep the order of the Python
they replace so the year-time digest moves only by float dust.

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
  debugging), never inside the year loop;
- the plain Python of a rule that moved into a kernel is kept in `sim/tests/*_plain.py`, and a test runs both on random inputs.

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
A number is the order of admission, so a numbering fed one name at a time follows whoever wrote first, and a set of strings
makes that the hash seed. Every goods market an area map defines is therefore admitted as one sorted batch when the areas are drawn
(`market_memory_areas.number_area_markets`: the opening, a load, a redraw); the single-name fallback (`goods_row_for_write`) is for
keys outside the map. The hash-seed command in "How to measure" checks the result across hash seeds.

## The tables and their owners

| Table | Owner module | Replaces |
|---|---|---|
| balances (agent x currency), stocks (slot) | `sim/book.py` | the book's dicts and per-key reads |
| transfer postings, goods-move postings (append-only per year, applied by a kernel, all-or-none per batch) | `sim/book*.py` | `Transfer`, `GoodsMove`, `move_many`, `transfer_many`, `post_settled` |
| market memory, market-indexed (price, usual price, cleared price, trade age, quote kind, volume, years without bids/offers; wages by labour market) | `sim/economy/market_memory*.py` | the `good|area` string-keyed stores and `area_of` reads |
| year ledger: agent vectors (money out, sales in, wages in, plant spend), (agent, good) rows (received, sold, output), market vectors (delivered, unmet) | `sim/economy/year_ledger*.py` | `YearLedger`'s dicts |
| goods bids, goods offers, goods market results, pairs | goods side | `Bid`, `Offer`, `ClearingResult`, `ArrayClearing`, `Pairing`, `Settlement`, `LeftMarket` |
| labour bids (tranches cut in the kernel), labour offers, labour market results, hired hours (market x employer) | labour | `LabourBid`, `EmployerHoursBid`, `LabourOffer`, `LabourClearing`, `LabourResult`, labour `Fill` |
| plans | `sim/economy/plan_table.py` | `Plan` per producer |
| loans | `sim/loans/` | `Contract` objects in a list |
| producers, cohorts (updated in place) | close, entry | `replaced(producer)` and `put_producer` per change |

Each table's owner is the only module that writes it outside a kernel the owner provides (CLAUDE.md: one owner per fact);
other modules read through the owner's view or call the owner's kernel.

## The book

`sim/book_tables.py` declares every column with its meaning and unit; `sim/book_store.py` holds the ids and tables;
`sim/book_apply.py` and `sim/book_plan.py` are the posting kernels. Agents, goods, tiles, currencies, agent kinds and
purpose templates are `IdTable`s saved with the book (the record's `numbering`). Balances are one row per (agent, currency) at
`agent * stride + currency`; stock slots are rows found through a hash index on the packed (agent, good, tile), chained per agent
in the order they were made (`tools/measure/book_index.py` shows why slots are found through a hash). A purpose is a template id
plus a reference id (`sim/book_purposes.py`); the year's goods moved per (good, purpose) are rows of a flows table.

**How a converter posts.** It holds ids (`book.agent_number(name)` and the like admit a name), appends rows to a
`TransferPostings` and a `GoodsMovePostings` table (rows grouped by batch, batches rising; a batch is all-or-none, money checked
before goods), and calls `book.apply_postings(transfers, moves, batch_count)`. It gets one `BatchOutcomes` row per batch (a
cause code from `BOOK_CAUSES` and the offending cell) and turns a refused batch into a refusal with `book.refusal_of`.
`economy/posting_sequence.post_in_order` does this for a list of steps: it turns them into rows in step order (so the book numbers
its names as posting them one by one would), applies them in one call, one batch per step, and replays a refused step through the
object path to raise the book's own error. `book_settled.post_settled_by_numbers` posts settled totals.

**How it reads.** The kernels in `sim/book_read_kernels.py` (`read_balances`, `find_slots`, `read_stocks_at`, `holder_columns`,
`counted_stocks`, `currency_values`) take the book's tables from `book.tables()`, `book.balance_table`, `book.stock_rows`; an id
below zero reads as nothing held. `economy/stock_block.stock_block(book, agent_numbers, good_numbers, tile_numbers)` reads any
number of stock cells in one call. Re-fetch tables after any call that may admit a name or reserve room (a grown table is a new
object). The methods callers use (`balance`, `stock`, `post`, `post_settled`, ...) are wrappers over the same kernels.

## The year ledger

`sim/economy/year_ledger_tables.py` declares every column; the ledger owns no numbering. Rows are keyed by the book's agent, good and
purpose numbers and the market memory's goods-market, labour-market and trade numbers (`YearLedger(book=..., markets=...)`; a ledger made
bare, as a test does, gets a book store and market tables of its own).

- **Agent figures** (row = agent number): `money_out`, `wages_in`, `sales_in`, `plant_spend`, `plant_worn`, `hours_sold`, `spare_hours`,
  each with an `order_*` column (place in entry order, 0 = not a member); and for the nested figures (`received`, `grown`,
  `hours_hired`) the agent's presence, entry place and first and last row.
- **Pair rows** (hash index `KeyedRows` on the packed agent, subkey, extra): `received`, `grown`, `sold`, `output`, `hours_hired`,
  `hours_hired_by_market` (hours and money), `imports_paid`, `exports_received`. The subkey is a good, a trade, a labour market, or a
  purpose template with its reference in `extra` (the foreign-money figures keep the purpose the book numbered).
- **Market figures** (row = goods-market number): `delivered`, `unmet`; **clearing rounds** (market, quantity, price), whose totals
  (`round_totals`) are summed exactly as `math.fsum` does, so the figures match the dict ledger bit for bit.

**Entry points for converters** (`year_ledger_arrays.py`, reached through `YearLedger.add_money_out`, `add_income`, `add_pair_amounts`,
`note_settlement_rows`, `note_hours_rows`, `note_round_rows`) take numbers and arrays, one row per agent in a settlement, per fill, or per
round, and may hold many settlements in one call. `YearLedger.note_settlement`, `note_hours`, `note_clearing` and `note_output` keep the
object signatures: they append to plain lists (`year_ledger_batch.py`) and a read of a table first adds the rows of the kind it waits on
in one kernel call. The attribute API (`ledger.money_out["farm"]`, `ledger.hours_hired.setdefault(...)`) is unchanged:
`year_ledger_views.py` and `year_ledger_pair_views.py` show the tables as dict-likes in entry order. Reading one cell through a view costs
more than a dict get does, so a reader that loops over agents uses `get_many` or the tables. `NestedView.as_plain()` reads every agent's
rows in one pass (`year_accounts._cohorts`, `_goods`).

Not on tables: the goods side's `ClearingResult`s as `note_clearing` takes them, `ledger.mint_takes`, `crew_hours_bought`,
`own_plot_hours`, `grown_units` and `carried_in`.

## Goods orders and clearing

`sim/economy/goods_order_tables.py` declares the tables, every column with a meaning and a unit: `GoodsBids` and `GoodsOffers`
(one row per order in the order it arrived, with the result columns the clearing writes in place), `GoodsMarketResults` (one row
per market cleared by the batch), `GoodsPairs` (one row per bid-and-offer pair that traded) and `BidOrder`/`OfferOrder` (the rows of
each cleared market in clearing order). Ids are the book's (`agent_number`, `good_number`, `tile_number`) and the market memory's
(a goods market is the row of `good|area` in `MarketTables.goods_markets`). Ids are numbered by arrival, the rules sort by name, so
the clearing ranks names once (`goods_table_group.name_ranks`) and sorts rows by those ranks.

`goods_order_book.GoodsOrderBook` is what `year_goods.clear_goods` clears. Kernels append whole arrays of rows (`append_bids`,
`append_offers`: the households' bids by `households_bid_rows.cohort_bid_rows`, the producers' offers by
`year_goods_offer_rows.OfferRows`). Everything else hands over `Bid` and `Offer` objects, through `add_orders` or the dict door
(`book.setdefault((good, area), ([], []))[0].append(bid)` that the mint, the state, lending and the engine use); an object waits and
becomes a row in arrival order the next time the tables are read. Objects are made from rows only at an edge (`bids_of`, `offers_of`,
lazily: `goods_table_views.LazyObjects`).

**One door for the rare sources.** `order_rows.OrderRows(order_book, source)` collects a source's bids and offers by name (`bid`,
`offer`, or `bids_from`/`offers_from` for a rule that still makes objects) and `write()` hands them to the book. The mint, the state
(`state_budget.goods_bids`, `state_store` through `year_order_sources.state_orders`), the households' tool bids and plain-path bids,
merchants and their carriers (`year_order_sources.merchant_orders`), the engine's seat orders, firm land bids, plant bids and
`lending.bid_household_loans` write through it. `GoodsOrderBook` (items in `goods_order_items.py`) keeps these rows and the plan table's
in its own arrival list and numbers the names of everything waiting as one batch at the flush, so agents, goods, tiles and goods
markets are numbered exactly as when each order waited as an object (the market numbering is saved, so a digest sees it). A plain
`GoodsOrderBook` or a `{(good, area): (bids, offers)}` dict still works as the target (tests).

**Clearing.** `goods_good_clear.clear_good` clears one good's markets in area order. A market takes one of three ways: traded in the
batch (`goods_table_pack` packs columns for `goods_year_kernel.decide_markets`, `goods_table_clear` writes the answer back,
`TableClearing` is the `ArrayClearing` that reads the tables), did not trade (`goods_table_quotes`: the quote and the wanted quantity
from columns), or the rules still written over objects (a book edge selling, a good outside the year arrays). A market on the tables
carries its rows (`goods_market_rows.MarketRows`), and the respend pack, the memory's notes and `_remember_markets` read them as lists of
columns. `TableClearing.batch` offers the allocation arrays (`pair_ptr`, `pair_bid`, `pair_offer`, `pair_quantity`, `ask`) and
`(agent, tile)` views of the rows; the same figures are in the `GoodsPairs` and `GoodsMarketResults` tables.

**The root search over columns.** `goods_market.crossing`'s search (`solve_price`, `at_a_ceiling`, the schedule's `total_at` and
`uncapped_at`) is kernels over `crossing_columns.DemandColumns`: the funded bids grouped by schedule in clearing order (the order matters
because the plain total adds each group with `sum`; the groups are in first-appearance order over all bids), the groups' exact totals
and the ceilings. Files: `crossing_columns.py` (prepare, every column documented), `crossing_demand.py` (the quantities wanted, with
`python_sum` and `exact_sum` where the Python uses `sum` and `math.fsum`), `crossing_solve.py` (the search; `math.exp`/`math.log` so the
plain run equals the Python), `crossing_price.py` (the entry kernels and `ColumnDemand`). A figure the kernels do not reproduce (NaN, an
infinite floor or quantity, a power or exponential the Python raises on) sets a flag and the Python runs on objects, raising or answering
as before. Two callers: `expansion_price.PreparedMarket` (the close's `share_of_row`) reads `MarketBids.columns` and
`MarketBids.clearing_order` (`bid_order.clearing_order`: the order tables' rows and the added bids ranked by name with `numpy.lexsort`,
no `Bid` made); `goods_market.crossing` (reached by `clear_at_one_price`, the price-response path) calls `price_at_levels` on the sorted
bids' columns. Test: `test_crossing_kernels.py`.

## Goods settlement, the ledger's notes and the memory's notes

`year_goods.clear_goods` settles, notes and remembers a good's markets from the order tables in blocks. Per good:

| Step | Module | Does |
|---|---|---|
| settlement | `settlement_ids.py` | `settle_by_ids` reads the pairs of the good's traded markets (the batch's pair arrays, which are the `GoodsPairs` rows) as agent and tile numbers from the bid and offer tables, numbers the (agent, tile) keys and the agents in the order `settlement_batch.KeyTable` did (`settlement_numbering.local_numbering` cuts them by market), runs `settlement_batch_kernel.settle_markets` (purses and stocks carried market to market in area order) and applies the sums with `book_apply.apply_settled`; no `KeyTable`, no names, no `Settlement` |
| ledger | `goods_settle.py` | one `YearLedger.note_settlement_rows` call per good (the plant purchases, the foreign-money figures and the mint's takes from columns) and one `note_round_rows` call for the good's clearings; the respend rounds are noted the same way (`goods_respend_unpack.note_rounds`) |
| memory | `goods_idle_years.py`, `goods_memory_kernels.py`, `goods_memory_notes.py` | the years without bids or offers of a good's markets are one kernel call; `_remember_markets` reads last year's quote flags and usual volumes as columns, works out every signal, then one kernel writes quote kinds, prices, usual prices and cleared prices in sorted (good, area) order, and the usual volumes are written the same way; the trade ages are `note_year_traded` over the markets that delivered |
| production | `goods_production.py`, `producers.production_lines` | the turn's input stocks, output stocks, purses and running costs are read as arrays; the production moves of all the turn's producers are one `GoodsMovePostings` batch and the output is added to the ledger by `add_pair_amounts`; a name the book has not numbered takes the `Book.move_many` path |

A good takes the object path (`settlement.settle_goods_many`, `YearLedger.note_settlement`) when one of its traded markets is not a
`TableClearing` of the good's batch (a mod replaced the rules). Tests: `test_goods_settle_ids.py` (the id path against `settle_results`
on random batches), `test_goods_memory_notes.py`, `test_goods_idle_years.py`, `test_goods_production.py` (each kernel against the
wrapper calls it replaces).

**The respend rounds** are rows: a later round's clearing is a tuple of `LeftMarket.later` and a row of the ledger's rounds (no
`ClearingResult`), and the bids it adds are `goods_added_bids.AddedBids` columns (objects only through `bids()`). The respend pack reads
columns: `goods_respend_rows.py` turns the first-round bids and the offers left into columns for every market (a market on the order
tables from the table's rows, `MarketRows.bid_array` and `left_array`; a market on the objects from its `Bid` and `Offer` objects),
interns the agent and tile names (`Interner`: ids by first sight, `ranks()` for the sort by text) and sorts the offers with
`numpy.lexsort` by market, reservation, seller name, tile name. The units a first-round bid bought come from one search over the
settlement's columns (`BoughtColumns.columns`, keyed by market and book agent number); a market whose `bought` is a mapping is read by
name. The packed arrays equal the object pack's byte for byte (`test_goods_respend_rows.py` checks the column functions against the
sorted-object rules on random inputs). `year_goods._received_price` reads the tuple and the rows. `standing_demand.with_standing_bids`
hands the year's `MarketBids` on when no standing bid joins a market.

A producer's turn reads its runs from the plan table's column and its hired hours from the ledger's pair table in one kernel call
(`goods_production_reads.py`).

## Entry's bids as one table

`year_goods.clear_goods` builds the year's bids once, after the respend rounds, as `year_bids.YearBids` (`ledger.year_bids`): every
market's bids in one set of columns (`bid_columns.BidColumns`), markets in sorted (good, area) order, `start` giving each market's rows,
a market's first-round bids (read from the order table's columns in one gather, or from the `Bid` objects of a market on the objects)
followed by the bids later respend rounds added (the `AddedBids` lists, written in one scatter). `ledger.bids_by_market` is
`year_bids_by_market.BidsByMarket`, which makes a market's `MarketBids` when first read, its columns views of the block (no gather per
market; objects only when a rule asks). `standing_demand.standing_block` joins a project's standing bids (`YearBids.with_standing`; the
block itself when there are none). `demand_at` and the unfilled sum are the kernels `bid_columns.demand_at_columns` and
`sum_taken_at_columns`, bit for bit the Python (`test_bid_columns.py`).

What reads it: `entry_bid_markets.weigh` walks the block's markets once for the margin and the trial rule (area, reachable capacity,
price; `EntryTables.capacity_in` makes its grid once); `entry_margin` and `entry_trial` first work out their streaks, rankings and every
price they will ask a market about, then take all the demands in one call (`year_bids_kernels.demand_at_many`, which runs
`bid_columns.demand_at_columns` on each market's rows, so each answer equals the single call) and only then take the plans market by
market in the greedy order, siting each. The demands do not depend on the plans already made, so asking them first changes nothing; the
capacity, room and `built` totals that do depend on earlier plans stay in the loops. `entry_backed.unfilled_at_cost` reads the block's
rows. Tests: `test_year_bids.py` (the block against the per-market columns, `with_standing`, `demand_at_many` against
`bid_columns.demand_at`, `BidsByMarket`).

## Labour

### Offers as a table

`sim/economy/labour_offers_table.py` holds the year's offers, one row per cohort x trade, with the supply parameters as columns and
`sold_hours`, `kept_hours` as outputs; `labour_offers_kernels.py` builds the matrix the labour clearing kernels read (`offer_matrix`) and
settles the offers at the cleared wages (`settle_offers`). `HourSupply` is the thin wrapper for callers not yet on the table. Where a
plot rule is a bare function, or a caller replaces a market's schedule in the `hours_sold_at` mapping (`MarketHours`), the plain path
takes it. The cohort offers are written as rows by the code that makes them (see "Bids and offers as rows" below); the shared agent
numbering replaces the per-year cohort numbering through the seam `LabourIds`; the cleared wages arrive in `HourSupply.settle` as a
dict read of the market memory, not yet as a market-indexed array.

### The core as tables

`MarketState` (`sim/labour/market/market_state.py`) holds what the labour core carries between years in the tables of
`state_tables.py`: workers (a row per area x trade pair, people per ability band), markets (wage, ask, and where the pair's hired hours
and cohorts sit), hired hours (a row per market x employer), and trainees (a row per cohort, grouped by market). Areas and trades are
numbered in sorted name order (`state_ids.SortedIds`), so a grid row is `area * trade_count + trade` and a kernel visits areas and
trades in the order the Python did by counting up. Employers are numbered once, in arrival order, through an `IdTable`, and
`EmployerIds.rank` gives the place of a name among all names for the sorts that go by name. The seam for the economy's shared agent
numbering is `LabourIds(employers=...)`: handing the book's `IdTable` in is not done, because the core admits into the table it is
given and the book must also give an admitted agent a row in its own tables, so the core would have to admit through the book.

The dict API is `state.workers`, `.trainees`, `.wages`, `.asks`, `.hired_hours`: live views (`state_fields.py`, `state_views.py`) over the
tables that list areas and trades in the order they were given their entries, and `to_plain` and `from_plain` round-trip nested dicts,
so the save, the economy's readers and the tests do not change. A view names its pair, so it stays right when a new area or trade
renumbers the grid. A reader that loops over the views pays for them: code inside the year reads the tables.

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
`exact_sums.py` holds `sum`, `math.fsum` and `math.sumprod` as kernels, so a rule moved into a kernel adds the numbers the way the Python
did. The plain Python of the rules is kept in `sim/tests/labour_*_plain.py`, and each rule has a test that runs both on random inputs
(`sim/tests/test_labour_*_tables.py`). A mod that replaces `fetch_wage`, or a schedule that is not packed, takes the plain path through
`clearing._prepare` and `_finish`.

### Bids and offers as rows

**Bids.** `sim/labour/market/bid_table.py` holds `LabourBidTable`, the year's one table of labour bids (columns `employer`, `trade`,
`area`, `hours`, `maximum_wage`, each documented in `LABOUR_BIDS`). Rows stay in the order the writers appended them, and that order is
a bid's sequence: it breaks ties in the core. The numbers in the columns are the table's own, given in the order a name first arrives
(`RowNames`), not the book's agent numbers: admitting every bidder to the book early would change the saved agent numbering. The core
numbers employers again in name order, so the arrival order changes nothing downstream. Writers: `PlanTable.write_labour_bids`,
`carriage_hours.write_bids`, `state_budget.plan_year`, `mint_labour.staff`, through `labour_bid_sink.put_bids` (a table takes the figures
as rows, a plain list of records, as a test passes, gets `LabourBid`s). `TrancheBids(table, ...)` cuts tranches from the kernel's
columns and `bid_book.numbered` turns the table's numbers into the state's with one array per column (only the distinct names are
looked up). `year_labour.clear_labour` takes the table (a list of records is put into rows first).

**Offers.** `labour_offer_rows.LabourOfferRows` is the year's offers as columns (`worker`, `trade`, `area`, `hours`,
`reservation_wage`), sharing the bid table's trade and area numbers. `labour_offers_write.write_cohort_offers` makes every cohort's
offers at once (cohorts by id, trades by name; a cohort x trade is a row of an expansion over its labour area's trades).
`labour_offers_table.build_labour_offers`, `HourSupply`, bondage placement and the settlement read the columns: `HourSupply.settle`
returns `labour_sold_offers.SoldOffers` (the `LabourOffers` table with the hours sold), and `labour_fills.sell_rows` reads its columns
(market of each offer, hours sold, distinct workers).

**Bondage.** `bondage_hours.place_held`, `place` and `payable_keep` work on the rows; the rules are kernels in `bondage_kernels.py`
(`place_held_kernel`, `place_bonds_kernel`, `payable_keep_kernel`). The Python only prepares indexes (`bondage_rows.ranges_of`: the rows
of one market or one holder in row order), so a holder reads the bids of its own (employer, trade, area) and an offer the bids of its own
market, not every row. Sums are `python_sum` (the order and brackets of the Python they replace, kept in `sim/tests/bondage_plain.py`).
The keep is `KeepRows` and is posted by `bondage_keep.post_keep` as one batch of transfer postings (one `apply_postings` call; a refused
batch is posted again as records to raise the book's error) and one block into the ledger's money out.

**Who still builds the objects.** `LabourBid`: `producers.plan` (the producers the plan kernel leaves out, read into rows by
`plan_table_rows.object_rows`), a seat's staff bids (`markets/port_staff.employer_bids`, handed over as `AgentOrders.labour_bids` and put
into rows by `add_objects`), and the workforce's views (`workforce_settle`, which read `carriage_hours.bids` and
`state_budget.wage_labour_bids`). `LabourOffer`: a seat's own offers. The household decisions (`household_offers_year.decide` and `plot_parameters_by_cohort`)
read the rows through `household_offer_reads.OfferReads` (hours, worth of an hour and hours offered by market are the kernels of
`household_offer_kernels.py`, equal to the record loops last digit included; a set holding a NaN or infinite figure takes the record
version). Count the record constructions in a warm year by wrapping `LabourBid.__new__` and `LabourOffer.__new__` around
`Economy._run_year` (no committed command). Tests: `sim/tests/test_year_speed_labour_rows.py`, `test_year_speed_bondage.py`.

### Settlement on tables

`clear_labour` (`sim/economy/year_labour.py`) settles every labour market of the year from the core's result tables in a few calls; no
`LabourResult`, `Fill`, `Pairing` or `Settlement` is made per market in the year.

| Step | Module | Does |
|---|---|---|
| columns | `labour_fills.py` | `rows_from_clearings` reads the core's `Clearings` (market rows, the hired table); `rows_from_objects` takes a plain list of `LabourClearing`s. `fills_of` adds the sells (hours hired shared over a market's offers by hours offered, the sum taken in the offers' order) and sorts each side by name. An agent is a `ref`, its place in the sorted names of the year |
| pairs | `labour_walk_kernel.py` | `walk_pairs` is `settlement_limits.pair_fills` over all markets; `market_agents` lists each settlement's agents (buyers used, then new sellers); `fill_slots` gives the ledger's slot per distinct agent of a market |
| book | `labour_wage_kernel.py` | `settle_wage_markets` runs `settle_pairs` and `book_apply.apply_settled` market by market on the balances the earlier ones left, and grows the currency's gross total by the exact sum paid: what `Book.post_settled` does, market after market, in one kernel call. A market the book refuses is replayed through `post_settled` so the error is the plain path's |
| ledger | `labour_settle_year.py` | `settle_year` calls the above and feeds `YearLedger.note_settlement_rows` and `note_hours_rows` once each |
| results | `labour_results_table.py` | `LabourResults` stands where the ledger's list of results stands; its items are `LabourResult`s built from the columns on demand, `fills` on first use. `hours_totals`, `bought_value` and `hours_by_market` read the columns |

The core's employer ids are not the book's. They are mapped to the book's agent numbers once a year with one array (`numbers_of_refs`),
admitting a name the book has not met in the order the per-market path would.

Who still builds the objects: `year_labour._result` (one `LabourResult` of a clearing and its offers; the reference the tests compare
with), `settlement.settle_labour` and `YearLedger.note_labour`/`note_hours` (tests and the reference ledger), `LabourResults` items
(`economy._outcome` reads totals from the columns; `year_close.close_agents` iterates the items, without their fills, only when carriage
hours hire), and the offers (`LabourOffer`, built upstream and by `HourSupply.settle`). Tests: `sim/tests/test_year_speed_labour_settle.py`.

### Readers in the economy

The economy's readers of the labour core read its tables in blocks (`sim/labour/market/state_reads.py`, kernels in
`state_read_kernels.py`, both behind `sim/labour/api.py`) instead of iterating the dict views one value per call. A figure that is a
`math.fsum` or a `sum` of a list is the same kernel (`exact_sum`, `python_sum`).

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
`test_economy_labour_readers.py`). Calls into `state_views.py`, `state_fields.py` and `state_ids.py` in a warm-year profile are the
readers still on the views.

## Price and wage reads through the year view

The year view's readers take a block of the market memory's tables where they once asked `area_of` and `offered_price` or `wage` per item.

| Read | Block | Kernel |
|---|---|---|
| offered price of every good on a tile (`YearView.offered_prices_on`, `offered_prices_for`) | `price_grid.PriceGrid`: goods by tiles, through `year_arrays_memory.markets_by_good_tile`; NaN in the grid is "no price", the tile's block holds only goods that have one | `price_grid_kernels.offered_by_good_tile` |
| remembered price of every good on a tile (`remembered_prices_on`, `present_prices_at`) | the same grid's second layer; the usual price (`YearView.usual_prices_on`) is a third | the same kernel |
| the one wage rule for trades by labour areas (`YearView.wage_rule_block`, `wage_rule_at`; `trade_wages.wage_in_view`, `year_arrays.wage_grid`) | `wage_block.wage_rule_block`; `WageRuleTable` keeps every trade of the setup in every tile's labour area | `wage_block_kernels.wage_rule_grid` over `labour_market_matrix` and `market_rows_of` |
| national prices and wages, the notional volumes (`national_prices.remembered_columns`, `notional._traded_volumes`) | the goods and labour tables' columns in the stores' entry order (`MarketStore.rows`) | `market_column_kernels.add_in_order_by_group` |
| kinds of price per good (`MarketMemory.price_kinds_by_good`, from `quiet_year.kept`) | the goods market table's `held`, `trade_age`, `quote_kind`, `price` and `area` columns in one pass: traded wins, else the kind of the good's first priced market in name order by the rank of the area names; `price_kinds_of_goods` names the codes | `price_kind_kernels.kinds_by_good` (registered in `ui/kernel_signatures.py`; no fixture year reaches it) |

**When a grid is filled again.** A grid or table is refilled by the first read after the memory is written to: `price_grid.memory_stamp`
combines the write count of the memory (`written_stamp`), the count of writes through a store (`MarketTables.writes`, which every
`prices[...] = ...`, `pop` and `clear` bumps, so a price written without `note_written` is still seen) and the numbering's generation. A
new writer of a column that goes round the stores and the memory's methods must bump one of these. `PriceGrid.refreshes` and
`WageRuleTable.refreshes` count the refills.

**What a block read does not cover.** A good the area map holds no market for is answered "no price" only while the memory numbers no
market for any such good (`EVERY_GOOD`); otherwise it is read by itself, as is a tile the area map does not hold (which refuses). The
scalar getters (`price`, `offered_price`, `wage`, ...) stay for the screens, the protocol and callers that read one cell.

Callers still reading one value at a time through the view: `producers.py` (`expected_price`, `paid_input_prices`,
`live_input_prices_at`, `live_wages_at`), `year_goods.py`, `plan_year.py`, `year_goods_offer_rows.py`, `households_orders_pack.py`,
`goods_respend_pack.py`, `entry_year.traded`, `land_bid_year.py`, `state_budget.py` (`wage_in_view` callers there and in `location.py`,
`mint_labour.py`, `year_close.py` already read the rule's table). Each can read a tile's block with `view.offered_prices_for(tile, goods)`,
`view.remembered_prices_on(tile)` or `view.wage_rule_block(trades, labour_areas)`. Tests: `sim/tests/test_price_grid.py`,
`test_wage_block.py`, `test_market_columns.py`, `test_price_kind_kernels.py`. Calls to `area_of`, `offered_price` and `price_of` in a
warm-year profile are the readers still on single values.

## The close

The close reads the book and the ledger with kernels, posts its dividends, wear, spoilage and consumption as posting tables, and makes
the producers' new records once from the close kernel's answer. A kernel replaces the Python only where it adds, orders and numbers
exactly as the Python did.

| Step | Python entry | Kernels / tables |
|---|---|---|
| the pack: stocks, held goods, the ledger's sales, costs, sold, made, hours hired | `close_pack.py` | `close_pack_kernels.py`: `slot_stocks`, `held_goods` (exact sum of the tiles, as `math.fsum`), `pair_values_by_slot` |
| producers' dividends: `shares.split_dividend` and `ownership.spread` | `year_close_dividends.py`, `year_close_owners.py` | `year_close_dividend_kernels.py`: `dividend_rows` (rows in the order of the payments), `add_in_order` (the property income) |
| producers' new records and the plant worn | `year_close_records.py`, `year_close_ledger.py` | `set_in_order` over the ledger's `set_figure` |
| the rows that need the credit record: exits, write-offs, loan requests, rebuild plans | `year_close_producers.py` (`_effects_by_row`) | Python, in producer order |
| wear and spoilage, coin wear | `wear_year.py` | `wear_kernels.py`: `loss_moves` |
| households: receipts (received and grown), wages, spending, consumption | `year_close_households.py` | `year_close_household_kernels.py`: `receipts_with_grown`, `consumption_postings` |

**Order the tables keep.** Posting rows come out in the order the objects were made, and a batch is all-or-none: all the non-exit
dividends are one batch, applied after the exits (which post as they happen); wear and spoilage are one batch each, both worked out
from the stocks before either is booked; consumption is one batch per cohort, in one `apply_postings` call. The book numbers the names
a batch meets *together, in name order* (`IdTable.admit`), so the close numbers an unseen name through
`year_close_dividends._numbers` and `year_close_households._number_unseen`, not one at a time; purposes are encoded in the order they
first appear. The property income dictionary gets each payee's payments added in the order of the producer rows, exits included
(`add_property_income`), so each sum and the order of new keys are the loop's. A cohort's consumption changes only its own stock, so
reading the stocks once for all cohorts gives what reading them after the earlier cohorts' moves would.

**Producer and Cohort objects.** The close's answer is columns; `closed_records` makes one new `Producer` per producer from them (a copy
of the old record's fields with the changed ones replaced) and `producer_table.put_producers` puts them back at once. The records are
read by entry (`entry_year`, `opening`), the next year's plans (`plan_year`, `year_goods`, `seller_offers`, `land_bid_year`), the labour
state, equity and tax-farming code, the save and the screens (`grep -rl "record.producers" sim` lists them). Retiring the record needs
those readers on the columns first. Cohorts are put back together once by `close_households` through `put_cohorts`; `closed_cohort`
replaces each cohort record one at a time (`renewed`), and keeping cohorts as columns waits for the modules that read `record.cohorts`
(entry, labour offers, demography, the screens, the save). Exits (`producer_exit.ExitBatch`), loan write-offs and loan requests stay
Python, in producer order.

Tests: `sim/tests/test_close_pack_kernels.py`, `test_year_close_dividends.py`, `test_year_close_records.py`, `test_wear_kernels.py`,
`test_year_close_households.py` (each kernel against the Python it replaces on written-out inputs).

## Entry, exit, credit and worths

The worths read the book's stocks in blocks (`year_arrays_worths.packed_stock` calls `close_pack_kernels.held_goods` once for every
producer; a good the matrices have no column for gets a column past them and is priced as before); the producers' cash comes from
`book.balances_at`. Entry's stakes, the owners' restakes and the exits post through `economy/posting_sequence.post_in_order`.
`open_entrants` keeps the owner's cash as the earlier stakes leave it and posts the stakes after the plans are applied; `ExitBatch`
collects the postings of each exit (repayments, dividend, goods) and posts them at `finish()`, which is safe because an exit reads only
its own cash and goods.

Siting's reads (`entry_siting_tables.py`, called by `EntryTables._ready_siting` and `_site_of`): the carriage matrix is read once per
carriage table and set of tiles from its searched costs and scaled on the way out; the hours a run takes for every producer, the
land-short tiles, the tile commitments and the recipe capacities are whole-column reads, summed in producer order by
`year_close_dividend_kernels.add_in_order`; a recipe's yield and limit rows are one list read each.

The entry plans (`entry_plans`, `margin_entry_plans`, `trial_entry_plans`, with their sitings) stay Python: they are thin glue spread
over many small calls (the plans' loops, `unfilled`, `gap_at_entry_price`, the per-call glue of `EntryTables.siting`), and `closed_records`
is below the bar. See "What is left" for what each needs.

## Loans

`sim/loans/` holds the term loans as one column table, `Loans` (`columns.py`: every column has a meaning and a unit), and nothing else
holds a copy. `LoanStore` (`store.py`) owns the table and the numbering of its names: lenders and borrowers, currencies, collateral
tiles and kinds are `IdTable`s of the store's own (kernels never iterate agent numbers; every sort by name goes through a rank array, so
the numbering can differ between a live game and a loaded one without changing a sum), and each loan has a number that is never reused,
with its id text in `texts`. Rows stay in the order the loans were struck, which is the order the credit market's sums follow. The save is
the list of records (`records()`, `load()`).

| Part | How it works |
|---|---|
| the credit record's loans | `LoanList` (`view.py`): rows read and written through `LoanRow`; a write bumps `store.version` |
| whole-list replacement (service, write-offs, exits, bank code, debt relief) | `store.retain(mask)` (drop rows), `store.gather(order)` (drop and reorder), `store.replace_all` (a test's or a rare caller's list) |
| transferring, shrinking and renaming | `store.split_off`, `store.shrink_collateral`, `store.rename` |
| service | `credit_service.serve` over the due rows, sorted by id text: kernel `service_loans`; the answer is arrays (a row per loan served, a slot per lender for the `Receipt`) and the table is changed after the losses it causes are booked (`apply_served`) |
| payments and disbursements | rows posted by `transfer_rows.post_payments`; names are numbered as `transfer_many` numbers them |
| clearing | `economy/credit_clearing.clear_with_cause`: requests and offers are packed into the `Requests` and `Offers` tables (`loans/clearing_tables.py`), kernel `clear_loans` fills the new-loans table, the requests' output columns and the base rate |
| claims, debts, principal and arrears history by borrower | `reads.py` over the columns (`credit_claims` sends a `LoanList` there and any other sequence of loans through its Python) |
| the close's loan loop, write-offs | `close_kernel.producer_loans`, `write_down_kernel.write_down` |

**Who still holds a `Contract`.** Objects are made from rows only at the edges: `store.snapshot(row)` for the UI, the protocol, mods and
tests; the loans a clearing struck (`LoanClearing.loans`, which `economy._lend`, `credit_lines.split_lines`, `banks.draw_deposits`,
`shares` and `lending.bid_household_loans` read as a list before `add_loans` packs them); the `Default`s that `titles.foreclose`,
`bondage.enter` and `credit_claims.losses_by_lender` take (made from the kernel's rows); a producer's loans at an exit
(`producer_exit`); and the `LoanRow`s that the bank rules (`banks`, `bank_runs`, `bank_service`), `funds.marked_holdings` and
`secondary_trade` hold for the loans they weigh one by one. A `Contract` handed to `add_loan` is copied: change the row it returns, not
the object. The loan requests are still `LoanRequest` objects in `record.credit.loan_requests` (their writers are the close, entry and the
state); they become a table at the clearing.

**Tests.** Each kernel against the Python it replaced, on random inputs, equal to the last bit: `test_loans_service_kernel`,
`test_loans_clearing_kernel` (the Python is `sim/tests/credit_clear_plain.py`), `test_loans_reads`, `test_loans_write_down_and_close`,
`test_loans_store` (`sim/tests/loans_plain.py` is the service, write-off and close Python). Bank paths: `test_bank_runs`,
`test_economy_banks`, `test_secondary_trade`, `test_funds` run on the table.

## Plans

`plan_year.plans_of` returns a `PlanTable` (`plan_table.py`): producer columns (`runs`, `wanted_runs`, `wage_line`, and the two sums the
readers need, `budget_total` and `outlay_total`, added by `plan_sums` exactly as Python's `sum` of floats adds them) and one row per
input bid and per labour bid, grouped by producer in slot order (`plan_table_rows.py` reads the plan kernel's answer into the rows with
`np.nonzero` over the recipe masks; the producers `producers.plan` still plans have their `Plan` read into the same rows).
`outlay_room.by_plan_table`, `land_bid_year.write_firm_land_bids`, `land_market` (through `wanted_runs_by_id`) and the goods clearing
(`PlanTable.get(id).runs`) read the columns; `plan_table.write_bids` hands the bid rows to the book of orders. `Plan`, `Bid` and
`LabourBid` are made only at an edge: `plan_of(id)` (tests, screens) and `labour_bid_objects()`; the labour rows go to the year's
`LabourBidTable` through `write_labour_bids`. `plan_year.stocks_by_slot` and `households_orders_pack.kernel_orders` read stocks with
`stock_block`.

**Still objects.** The rules `households.goods_orders` (now only the Python reference: the kernel covers every basket),
`households_store.store_bids`/`store_offers`, `tool_wear.tool_bids`, `merchants.orders`, `carriage_fleet_book.bids`,
`land_bid.hectare_bid` and `producers.plan` build `Bid`/`Offer` objects inside the rule; they are unpacked into rows at the call
(`bids_from`), never handed to the book as objects.

Tests: `sim/tests/test_year_speed_plan_tables.py`, `test_year_speed_plans.py`, `test_year_speed_cohort_orders.py`.

## Households

| Part | How it works |
|---|---|
| share limits in the orders (`households_orders_kernel._remix`) | the quality re-mix searches the limits with `priced_need_kernel.limit_shares` (the exact-sum port of `need_basket.limited_shares`), so `households_orders_pack.covered` is true for every basket. `RF_LIMIT` is a column of the row floats. Test: `test_orders_share_limits.py` (kernel against `households.goods_orders` on random cohorts, with a mutation check that the limits matter) |
| store weights (`households_store._store_weights`) | `priced_reads.offered_prices_for` and `usual_prices_for` read the tile's blocks (the usual price is the third layer of `price_grid.PriceGrid`). Tests: `test_price_grid.py` (`UsualPrices`), `test_store_weights_blocks.py` |
| unmet floors of every cohort (`households_close.unmet_floor_by_need`) | `households_close_kernel.unmet_floors` over `households_close_pack.PackedBaskets` (a basket's needs, goods and service lives, packed once per basket key) and the year's receipts arrays; the durables held are one `stock_block` read. Sums in the Python's order, so the figures are equal bit for bit. Test: `test_households_close_kernel.py` |
| the cohorts written back | `put_cohorts` once |
| priced needs as tables | `priced_need_tables.NeedBatch` (any number of (tile, basket) requests as need rows and good rows, spec rows kept per spec and per basket) and `priced_need_kernel.price_needs` (every need priced from a tile-by-good price matrix, exact sums and the share-limit search, ceilings). `priced_needs.PricedBatch` makes `PricedNeed` objects only on demand. Test: `test_priced_need_kernel.py` (the Python against the kernel bit for bit on written-out and random needs, with limits that bind and quality re-mixes, and batches of many tiles and baskets) |

**`NeedBatch`, `price_needs` and `PricedBatch` have no caller in the year.** `priced_reads.kept_need_prices` takes the object path: the
year asks it often but misses only for a limited set of (tile, basket) pairs per memory epoch (the kept reads are dropped whenever the
memory is written to), so most asks are dictionary hits. A batch that primes every cohort's basket in one call is slower than the
object path, and the kernel is a small part of it: the year would pay for making
`NeedBatch` rows, reading the answer back as lists and making the `PricedNeed` objects (a tile's baskets differ in their climate floors,
so few are shared). The readers of those lists (`labour_ask_floor`, `household_hours_year`, `state_budget`, `lending`, `goods_respend`,
`country_figures`, `year_labour`) all take objects, and converting them cannot add to a saving that is itself below the bar. The batch
waits for a wider change, such as all epochs' requests known up front. Compare `kept_need_prices` against `prime`, `PricedBatch` and
`need` in a warm-year profile.

**Cohort orders are below the bar.** `function_times.py SAVE` with no names times the cohort orders and what they call. No part that
`year_order_sources`, `households_orders_pack`, `tool_wear`, `households_cohort` or `opening_bid_memory` owns reaches the bar, so nothing
there is converted:

| Part | Owner | Why it stays |
|---|---|---|
| first touch of `CreditView.equity` (every producer's worth) | credit and equity | the next reader of `view.equity` pays it instead, so moving it saves nothing |
| `kept_need_prices` first touches in `BidMemory.priced` | `priced_reads`; shared with the close and the labour readers | the first asker pays; the tables wait for readers that take columns |
| `add_template` (one per basket key per year) | the households' pack | prices change every year, so a template cannot outlive the year; sharing the tile-only reads of `_store_weights` between keys of one tile saves part of it |
| `land_bids` | land-bid owner | not in the households package |
| per-cohort reads (`ledger` wages and plot hours, balances, claims, loss rate, `tool_bids`), `change_cohort` of `planned_spending`, `_orders_of` | dict lookups and a record copy per cohort | vectorising them costs a column copy of every cohort field for a saving far below the bar |
| `year_orders` (the compiled kernel) and `cohort_bid_rows` | already compiled | |

Revisit after the cohort records become columns, when the cohort figures can be handed to the kernel as slices of those columns.

**Who needs `Cohort` and `PricedNeed` objects.** `Cohort`: every module that reads `record.cohorts`. `PricedNeed`:
`households_orders_pack` (reads `need.goods`, `ceilings`, `price_index` into its template arrays), `households_store.staple_price_per_kg`,
`store_return.service_values_per_year`, `household_work_year.grinding_plan`, the readers named above, and the screens and mods through
`need_basket.need_prices`.

## Merchants

Each merchant's `expected_prices` and `expected_volumes` are `merchant_figures.MarketFigures`: a float column indexed by the market
memory's goods-market numbering (`MarketTables.goods_markets`, NaN for "none"), with a dict-like view keyed by `(good, area id)` for
readers that ask one market (tests, the UI, mods; `Merchant.__setattr__` copies an assigned dict into the column). A merchant of a record
is bound to the record's numbering (`merchants.put_merchant(..., tables)` at the opening, `EconomyRecord.__post_init__` after a load), so
the columns grow with the numbering; a merchant made alone numbers its own markets.

- `merchants_news.learn_all` moves every merchant's figures for every market of the year in one array step (`move_toward`, bit for bit
  what the dict loop gives, tested against `sim/tests/merchants_news_plain.py`); the price history of a market whose news is late stays a
  Python dict walked only for those markets (`heard_prices`). `merchants.learn_year` is its call from `year_close.close_agents`;
  `merchants.close_year(..., learned=True)` then only settles the profit.
- `merchants_book.merchant_array` gathers a merchant's column into the packed route book's slots by `RouteBook.market_rows` (the memory
  row of each slot), kept while the numbering is.
- `market_memory_follow.follow_goods_markets` returns the renumbering (`GoodsRemap`) and `market_areas_follow` carries each bound
  merchant's columns over it (`MarketFigures.follow`); a merchant bound to another numbering is re-keyed by name. A read of a column
  whose numbering was replaced without `follow` raises.
- The save writes the figures by market name in the order of the `(good, area id)` keys (`sorted_named`), so a save is byte for byte what
  dictionaries give; a load hands them back by name (`hold_named`) and they are indexed once, by the record's numbering.

`merchants.dispatch` is a loop over hauls with the crew and dues arithmetic, and `merchants_book.search` is the route kernel itself; no
per-market column read is left in them to convert. Measure with
`python3 tools/measure/function_times.py SAVE sim.economy.merchants:learn_year sim.economy.merchants:close_year`.

## Cached views

A published view is cached only when everything it reads reports its changes: the owner bumps a channel at every writer, and a source
that cannot be cached (a new object each read, or a quote) still lists the channel so that views over it can be. A debug run with
`SHADOW_CHECK_EVERY` set to 1 in `sim/engine/game_assembly.py` checks every cached read against a fresh computation and raises
`StaleView` on a difference.

**Workforce views.**

| View | Fresh while | Writer and how it bumps |
|---|---|---|
| `trade_registry` | the content's `trade_records` (input) | none: the records are fixed for an assembly; a load moves the era. `TradeReads.trade_registry` builds a new registry object only when the records object changes |
| `unskilled_trade` | `trade_registry` (input) | none besides the registry; labour's own reads (`trade_data.fallback_trade_of`, `trade_of_role(..., "unskilled")`) scan a registry object once (`trade_data.fallback_trade_in`) |
| `is_craft_trade` | content's `trade_family` (input) | none |
| `cleared_wage_change` | the `cleared_wage` channel | `note_cleared_wage`, the one writer of `cleared_wage` and `cleared_wage_before`, bumps it |
| `labour_market`, `labour_state_weights`, `literacy_references` | always (one object or constants; a load moves the era) | none |

**Wage views and the sources under them.**

| Source (owner) | Fresh while | Writers and how each bumps |
|---|---|---|
| `civilisation` (scenario, cached) | the `civilisation` channel | `open_scenario` and `record_opening_literacy` are the only code that changes the record after it is loaded; both bump |
| `home_tiles_held` (land, cached) | the `owners` channel and the `civilisation` input | `Ownership.hand_over` is the one writer of the owner map after it is seeded; it bumps right after the transfer |
| `agent_wage_cell[(trade, tile)]`, `agent_working_hours` (markets, cached) | the `memory` channel | `market_memory.note_written` (every write to the memory's prices, wages and rates, `Economy.change_setup`, the economy being built, `open_agent` finishing, `add_workers`) calls the markets module through a weak listener; `reprice_opening_money` bumps when it sets `money_from_economy` |
| `agent_wage_at` (markets, quote) | never cached | the keyed cell above is the same figure, and what the workforce reads |
| `home_price_level` (coin, cached) | `ratios` channel, input `foreign_coin_home_units` (foreign trade's `books` channel), input `civilisation` | `revalue_coin_metals` bumps `ratios`; `settle_flow` and `record_lift` bump `books`; the opening stock is kept once |
| `farm_land` (agriculture, uncached: a new `Land` each read) | the `farm_land` channel | `set_farm_land` is the one writer of the cleared hectares and quality; it bumps |
| `base_tile` (workforce, cached per seat) | the `base_tile` seat channel and the `home_tiles_held` input | `Relocation.move_base` writes the field and only the `move_base` command calls it; the command bumps when it returns |

Cached on top of them: `money_per_labour_hour`, `wage[trade]` (per seat; inputs `unskilled_trade`, `agent_wage_cell`, `base_tile`,
`opening_money_per_labour_hour`, `home_price_level`), `opening_money_per_labour_hour` (inputs `civilisation`, `trade_records`),
`base_tile`, `farm_land_hectares` (input `farm_land`). A seat handed over or added is a seat put whole under an id, which no channel
sees: `Clock.seat_replaced` (called by `seat_registry.add_seat` and `seat_move.move_seat`) is part of every seat-scoped signature.

**Left uncached, each until its input's owner bumps first:**

- `labour_quote`, `market_annual_wage`, `wage_signature`: before the economy prices the money they read the cost-of-living factors, the
  price index, the town's housing and output per head, none of which report.
- `base_annual_wage`: the hours of a person-year come from `hours_per_person_year` before the economy opens. `hours_per_person_year`
  itself reads the working-day works that run, which production and ventures publish without a channel.
- `standing_job_pay`, `capacity_job_pay`: the seat's hours, written in place.
- `settlement_tiles`, `town_mortality_premium_by_tile`: demography's people by tile and population. The writers (`store_bands`, the
  regions' step) could bump a channel, but each read builds a new object that callers may keep or change, and the workforce reads them
  rarely.
- `seat_base_tile` (keyed by a seat the view is not scoped to), `farming_technique`, `wage_materials`.
- The seat views (`available_trades`, `trade_available`, `taught_trade_people`, `people_who_exist`, `reachable_trade_population`,
  `occupation_*`): labour changes `trades_created`, `trade_schools` and the people in place at several sites.
- The wage and hour views over `agent_wage_at` that lack a channel, and the base-tile, settlement, farm-land, working-day and farming
  views over views that land, demography, agriculture, mechanics and the scenario publish uncached (`home_tiles_held`, `people_by_tile`,
  `farm_land`, `mechanic`, `civilisation`): the module spec's header gives each reason. The unconverted workforce views declared
  `cached=False` (`money_per_labour_hour`, `trade_registry`, `wage_signature`, ...) are what keeps `quiet_year.kept` doing first work after
  each step.

Tests: `sim/tests/test_workforce_cached_views.py` (a real workforce spec over a stand-in provider, `sim/tests/workforce_assembly.py`:
each cached view is read, its writer writes, and the next read is the fresh value; an adjuster of a cached view still applies) and
`sim/tests/test_wage_views_cached.py` (each writer bumps, a mod adjuster still applies, removing any one bump fails a test). To count
`View.fresh` calls by workforce view, wrap `sim.assembly.views.View.fresh` around `year-time`'s `loaded`/`step` (no committed command).

## The phases outside the economy step

The phases outside `Economy.step` (the money phases, revolts, the market wrapper) are a small share of a warm year. Most view
computations there are cheap lookups; the cost is the first work of a figure after the economy stepped (shown prices, the floor costs of
every tile, a price response), plus the same figure asked again with the same inputs. Only the repeats are removed:

| Figure | How it is kept |
|---|---|
| price response of a book (`economy.api.price_response`, `prices_at.price_response_at`) | `response_memo.price_response`: kept against the book object it was cleared from; a new clearing makes a new book object, so nothing stale is served |
| floor costs of a tile and of a country (`country_figures`) | `quiet_year.kept`, like the prices: once while the economy stands between steps |
| money value of an unskilled hour (`labour_wage_schedule.money_per_labour_hour`) | the schedule's field itself (`_hour_money`); `trades.field_of` skips the abstract-class check for a plain dict |
| `year_accounts._cohorts`, `_goods` | `NestedView.as_plain()`: every agent's rows in one pass over the table; the hunger need's goods are worked out once per tile |

Tests: `sim/tests/test_response_memo.py`, `test_year_accounts.py` (`PlainLedgerReadTests`), `test_year_ledger_views.py` (`as_plain`).

**Below the bar, so unchanged.** Time the phase with a handler wrapper over `year_steps.money_world` and `time.process_time`, or
`function_times.py SAVE sim.economy.country_figures:money_held ...`, against the whole step from `year-time`. The government's and
registry's year (`money_world`, nearly all of it the actors' `advance_actors`) is a small share of the step. The cost under
`government.advance` is the first work of economy figures after the economy stepped: `price_response` clearing (nearly all of it
`goods_market.clear_at_one_price`, which the goods package owns, not `response_memo` or `prices_at`), the floor costs of the tiles
(`_worked_need_floor_costs` over `_worked_tile_floor_costs`, almost all of it `kept_need_prices` misses, whose batch form is not wired, see
Households), `country_figures._prices` with the `MarketLayout.kept` mask, `output_value_and_unpriced`, `money_held` and
`price_index.kept`. Each is below the bar, so no block read was added: a floor-cost grid would repeat the `NeedBatch` result, and
`output_value` and `money_held` read the producer and cohort records and one `balance` per holder, which `book.balance` already serves
from its table. The views the actors read are cheap lookups (`tree_nodes`, `civilisation`, `home_tiles_held` are asked most). `ActorWorld`
is built several times per phase; its once-memo keeps a turn's shared answers consistent, so it stays as it is. The largest single
items in the packages the phase owns (`group_jobs.displacing_technique`, `strata_observed.slice_income`, `carriage_surcharge`,
`world_groups.goods_categories`) and `demography.urban_people_by_tile` are each below the bar, and so are the packages' own Python in
all. Re-measure with `warm_year_profile.py` (then `pstats` sorted by `tottime`, summed per directory) and look at `clear_at_one_price`,
`_worked_need_floor_costs`, `MarketLayout.kept`, `output_value_and_unpriced`, `money_held`, `urban_people_by_tile`.

## Other callers of the book and views in the year loop

| Caller | Decision |
|---|---|
| `carriage_wear.settle` | converted: the merchant's and the carrier account's holdings are read once, not once per good (nothing moves between the reads) |
| `Economy._grow_own`, `Economy._build_plant` | converted: each cohort's or producer's moves are a step of `posting_sequence.post_in_order` (one batch each, applied in order in one kernel call), posted once after the loop; neither loop reads the book between steps. What remains is the ledger writes, `hectares_held` and the posting-row build |
| `year_close.tax_facts` | converted: `book.balances_of` once for the taxpayers' list, in the book's name order |
| `producers.live_input_prices_at`, `live_wages_at` | not converted: both already read the tile's block (`present_prices_at`, `wages_at` keep one answer per goods tuple and tile until the memory is written to). A producer stands for one recipe on one tile, so there is little to share between callers, and what is left per call is the dictionary built for the caller. Needs a recipe cost grid (recipes by tiles) before it pays |
| `agents.purses.transfer` -> `book.transfer` | not converted: each transfer first draws on the payer's facility and repays the payee's debt from the purse the earlier transfers left, and the callers are the actors' own advance steps spread over many phases, so a batch would change what each draw sees |
| `YearLedger.running_costs_of` (from `goods_production.turn_figures`) | already a block read; sharing the agent rows between the two figures made no measurable difference (the cost is the pending notes flushed into the table) |
| `country_figures.money_held`, `year_accounts.plain_rows`, `inventory.held_stock` | below the bar |
| `_remember_markets` `wanted_at_rows`; `producers.production_lines` (with `tool_fallback.draws` inside it); the object-rule markets (`unsold_search.clear_with_search`, `seller_offers.strategic_offers`, `goods_market.clear`) | below the bar; a kernel would leave part of each (the packing and the boundary) |

Time any of these with `python3 tools/measure/function_times.py SAVE module:function ...`.

## What is left

One list; each item names what blocks it. The bar for every item is the one in "How to measure": convert when the function reaches
about one percent of a step, and re-measure before acting, since the list lags the code.

- **Entry reading columns, and the greedy loops as kernels.** `entry_plans`, `margin_entry_plans` and `trial_entry_plans` choose each
  candidate's tile with `EntryTables.siting` (Python glue around `entry_kernels.site_choice`, updating the capacity and committed hours
  the next candidate sees) and each plan changes the running `capacity`, `room` and `built`; a kernel for the loop needs the siting's glue
  (the runs-anywhere branch, the unsited candidates' cache) as a kernel first. What a kernel can do before the loop is done (the demands).
  Left per market in Python: the streak (a saved dictionary of `margin_years`, written for every market weighed), the ranking sort and
  the request lists of `EntryTables.recipes_by_cost_many`. `entry_bid_markets.weigh` is a Python loop over the block's markets (a
  dictionary read each for the area, capacity and price); with the goods-market numbers on the block it is a gather over `market_cells`,
  the reach grid and the price grid.
- **`UnmetDemand` and `EntryPlan` as table rows.** The Python loops above and `open_entrants` read them; rows pay only with those kernels.
- **`record.goods.volumes`, `unsold` and `unmet` as columns.** The stores are saved dictionaries keyed by `market_key` that many readers
  and the area-redraw move; a column store needs a dict-like view that saves and loads and a kernel for `sized_runs` to read it, which
  together are worth less than the glue. A derived read is cheap without changing the save:
  `[volumes.get(name, 0.0) for name in memory.tables.goods_markets.name_list]` scattered by `year_arrays_memory.market_cells`.
- **Per-good price readers.** `entry_year._traded_volume`, `producers.paid_input_prices` and `next_expectations` read many keys a year,
  each a dict lookup; the year view has no cleared-price block. `producers.live_input_prices_at` and `live_wages_at` need the recipe
  cost grid.
- **The mint reading the results table; the object-rule markets and `production_lines` as kernels; the watchers' fills from columns.**
  The mint keeps one `ClearingResult` per market of the coin metal in `ledger.mint_takes`; `production_lines` needs the tool fallbacks'
  draws as a kernel; the watchers' buy fills are `Fill` objects (`bought_by`, only for markets a merchant or the state bought in);
  `LeftMarket` and its `bought` mapping are built from columns when a market not on the tables asks.
- **The goods side's `ClearingResult`s.** The year ledger is handed `ClearingResult`s (`note_clearing`) for markets not on the tables, and
  `_produce_and_offer` still loops over producers (`producers.production_lines` and `producers.offers` are the rules over one producer).
- **The record readers.** `record.producers` and `record.cohorts` are read by entry, the plans, the labour state, equity, tax farming,
  the save and the screens; `closed_records` and `closed_cohort` build one record per producer and cohort until those readers are on
  columns.
- **Labour readers that take records.** The cleared wages reach `HourSupply.settle` as a dict read rather than a market-indexed array.
  The household decisions still loop over cohorts in Python (`household_offers_year.plans`: the basket, grinding plan and priced needs
  of each cohort), as do `outside_option_by_tile`, `subsistence_cost_by_tile` and `ask_floor_by_tile`; they wait for the cohorts and
  the priced baskets as columns.
- **Priced needs.** The readers of `PricedNeed` listed under Households take objects, so `NeedBatch` stays unwired.
- **Loan requests** become a table at the clearing; `LoanClearing.loans` and the bank rules still read `Contract`/`LoanRow` objects.
- **Cached views** in the "Left uncached" list wait for their input's owner to bump a channel.

## Stages

1. **Foundations, in parallel:** the book as tables with the two posting tables; the market memory as market-indexed arrays; the year
   ledger as tables. Each keeps its Python methods as thin wrappers so callers not yet converted still work, and adds whole-table
   kernels for converted callers.
2. **Goods and labour on the tables:** orders written by the kernels that compute them, clearing and settlement reading and writing
   tables, no per-item objects from plans to the ledger.
3. **Close, then entry and credit** (variable-length searches and greedy queues; the smallest share of the year).
4. **Every remaining reader in the year loop** reads the tables in blocks, and the per-item wrappers leave the year loop (they stay only
   for the UI, the protocol, saves, mods and tests): labour readers, the goods unit's far end, plans and the rare order sources, entry,
   exit and credit, price and wage reads through the year view, and the phases outside the economy step.

The year is judged when the conversion is complete: a partial conversion is expected to cost more than it saves, since every
unconverted reader pays the wrapper. `year-time --count-instructions` after each merge is kept as progress, not as a gate.
