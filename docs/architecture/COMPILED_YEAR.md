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

**No cutoff.** Everything that runs in the year loop is converted however small: Python orchestrates a handful of whole-table kernel
calls per phase (one per good where goods must run in sequence) and otherwise serves the UI, the protocol, saves, mods and tests. A
section that says a function is "below the bar" records an earlier rule and is on the list below. `function_times.py` against the whole
step from `year-time` is how a conversion is measured. Every
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
| producers (a row per producer, every `Producer` field a column; the names are the store's own `IdTable`s) | `sim/economy/producer_store.py` (`producer_rows.py`: the spec) | the dict of frozen `Producer` records, `replaced(producer)` and `put_producer` per change |
| cohorts (a row per cohort, every `Cohort` field a column; the names are the store's own `IdTable`s) | `sim/economy/cohort_store.py` (`cohort_rows.py`: the spec); writers `households_cohort.py`, `cohort_close_write.py`, `cohort_people.py` | the dict of `Cohort` records, `replaced(cohort)`, `put_cohorts` and `change_cohort` per change |

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

**One posting, and the cost of a call.** `Book.transfer`, `Book.move` and a one-posting `Book.post` write their row into one-row tables the
book keeps (`sim/book_single.py`, `SinglePostings`), numbering names in the order the table path would, and call the money or goods
kernel directly. `apply_batches` runs only the half a batch has (a money-only batch does not plan, commit or record the goods half,
and the reverse): dispatching a kernel costs for every array it is given, and a nested bundle of tables costs more than the same arrays
passed flat do (`tools/measure/function_times.py` on `sim.book_post:apply_batches`, `apply_money`, `apply_goods` shows it). A converter that
holds names and not ids numbers them with `IdTable.numbers_of` (one call for a list; -1 for a name the table lacks) or
`Book.agent_numbers_in_order` (admits the new ones one at a time, as `agent_number` does, which a batch admit would number differently).

**How it reads.** The kernels in `sim/book_read_kernels.py` (`read_balances`, `find_slots`, `read_stocks_at`, `holder_columns`,
`counted_stocks`, `currency_values`) take the book's tables from `book.tables()`, `book.balance_table`, `book.stock_rows`; an id
below zero reads as nothing held. `economy/stock_block.stock_block(book, agent_numbers, good_numbers, tile_numbers)` reads any
number of stock cells in one call. Re-fetch tables after any call that may admit a name or reserve room (a grown table is a new
object). The methods callers use (`balance`, `stock`, `post`, `post_settled`, ...) are wrappers over the same kernels. Whole-table
reads that save a loop of scalar ones: `balances_by_currency` (each row in its own currency), `balances_of` / `rows_of` / `slots_of`
(a list of names), `balance_by_agent` (`balances_of` as a dict by name, for a caller that looks figures up afterwards), `goods_held_many`
(`goods_held` for a list of agents: one kernel gathers every agent's slots, one sort puts them in name order, one pass writes the dictionaries;
`sim/book_holdings.py`), `goods_flows` and `edge_goods_net_by_good` (the year's flows and an edge's nets for every good), and
`flow_by_purpose` / `flow_by_prefix` (the year's flow of one purpose, or of a purpose prefix summed exactly, for a list of goods:
`sim/book_flow_columns.py`). `goods_held` and `goods_of` are the one-agent forms of the same read; a caller that wants only the goods uses
`goods_held`, not `holdings(agent)["goods"]`.

**Names to numbers in one pass.** `IdTable.numbers_if_known(names)` numbers a whole list in one C-level pass (`map` over the dictionary) or
answers None when a name is new; `_agent_numbers`, `_admit_goods`, `_admit_tiles`, `_admit_currencies` and `posting_sequence` use it, so a
sequence of posting steps whose names the book knows is turned into rows with one pass per column over all the steps, not one per step
(a sequence with a new name is numbered step by step, as the book numbered it before). `IdTable.name_order()` and `name_rank()` give the
numbers in the order of their names and each number's place in it, kept until a name is admitted.

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
rows in one pass (`year_accounts._cohorts`, `_goods`): `year_ledger_plain.plain_by_agent` sorts the live rows by agent once (stable), makes
all the sub names with the sub's `names` block call, and builds each member's dict from its slice. The year's goods accounts
(`year_accounts._goods`) are columns, one list per figure with one entry per good (`year_accounts_columns.py`: `column`, `summed_by_key`
adds in the order the rows came, as the running dictionary sum did, `sum_across` for the exact sums).

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
| production and offers | `goods_turn.py`, `goods_turn_kernel.py`, `goods_turn_offers_kernel.py`, `goods_turn_spec.py` | `TurnWorld` (built once a year from the year arrays) takes each good's turn as positions in the producer columns (`has_output` of the recipe rows); `produce_turn` is `producers.production_lines` for every planned producer at once (stocks from the book's stock rows, hours from the ledger's `hours_hired` pair rows, the tool fallbacks in recipe-row arrays, the crew's multipliers from `ProducerColumns.hours_scale`) and its moves are one `GoodsMovePostings` batch, the output added to the ledger by `add_pair_amounts`; `offer_pairs` gives each producer's held outputs and expected prices, `year_goods_offers.offer_reservations` the reservations, and the rows go to the order tables with the markets read from `markets_by_good_tile`. A producer with an output held and no expected price (`slow`), or a name the book has not numbered, takes the `producers.offers` / `Book.move_many` path at its place in the order. `goods_production.py` and `year_goods._produce_and_offer` remain for a year with no arrays (a test's) and a storage cost |

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

**The goods record's stores and the year's market table.** `record.goods.volumes`, `unsold`, `unmet` and `margin_years` are
`goods_market_column.MarketColumn`s (`MarketFigures` keyed by `good|area`, indexed by the memory's goods-market numbering, `bind_markets`
on the record): `_record_year_markets` writes each with one `replace_rows`, and `entry_plan_pack.traded_grid`,
`entry_margin_tables._streaks_in`, `goods_table_pack.market_figures` and `entry_unmet.markets_of` read them with `take` or the ledger's
`member_columns`. Iteration lists the markets in (good, area) order, as the dictionaries written in sorted order did.

`clear_good` returns a `goods_good_clear.GoodClearing`: per market of the good, in clearing order, the first round's quantity, price, demand,
offered, quote (`quote_price`, `quote_kind`), what buyers wanted, the memory's flags, `way` (traded in the batch, did not trade and quoted from
the columns, or on objects), and the pointers cutting the bid rows and the offers left out of the order tables. `goods_settle.settle_good` takes
it and returns a `GoodSettlement` (delivered as an array; `bought` and the mint's `takes` when asked), and `note_clearings`, `idle_years` and
`last_prices` read the columns. Each good's rows are then added to the year's table `goods_year_markets.GoodsYearMarkets` (`YearMarkets`: the
figures per market, the bid rows and the offers left with their units as flat columns, the first round's settlement per buyer, later rounds and
the bids later rounds added) and `goods_left_markets.LeftMarkets` remembers where each market's row is.
  Readers of the table: the respend pack (`goods_respend_rows.table_columns` and the column branches of `bid_rows`, `offer_rows`, `bought_columns`),
the respend's unpack (`_add_rounds` as `YearMarkets.add_rounds`, `_leave_offer_units`, the added bids and later rounds as columns), `year_bids.build`
(`_build_from_table`) and `year_remember.remember_markets`: the price sellers got from the ledger's rounds (`received_prices`), what a market's
buyers would take at the old price (`wanted_at_markets`: `math.fsum` as `exact_sum`, the power as the Python raises or not, a figure the kernel does
not reproduce flags the Python rules), the bids-only quote (`bid_figures`) and the signals (`signals`), then one `goods_memory_notes.write_markets`.
Tests: `test_goods_market_column.py`, `test_goods_year_markets.py`, `test_goods_remember_kernel.py` (each kernel against the Python on random inputs).
Ground goods (not portable) are cleared in the batch like any good: the held value of an offer that is ground is its capitalised rent
(`goods_table_clear._ground_values`, the `held_value` column of `goods_year_kernel.decide_markets`).

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
| which markets a country's national price and wage count (`country_figures._prices`, `wages_per_hour`) | the area map's sorted tile table (`AreaMap.tile_table`) against the layout's place arrays; the labour areas by one `isin` | `price_index_masks` (numpy over whole arrays) |
| each good's national price (`national_prices.national_prices`) | one exact-sum pass over the layout's runs | `market_column_kernels.traded_price_by_group` |
| making costs and the estimates of untraded and thin goods (`notional.making_costs`, `_estimated_prices`) | the setup's recipes as runs in dictionary order, every good in input-depth order in one call, sums as the Python adds them | `notional_kernel.costed_goods` |
| what each cohort owns of the producers (`equity.holdings` over the year arrays) | the worths split by ownership share and the outside share holders, in the producers' order | `year_arrays_holdings.share_out_kernel` |
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
| producers' new figures (written into the store's columns) and the plant worn | `producer_close_write.py`, `year_close_ledger.py` | `set_in_order` over the ledger's `set_figure` |
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

**Producers are columns.** `record.producers` is a `ProducerStore`: the close's answer is written into its columns in place
(`producer_close_write.write_close`: block writes for the figures, a slot-by-slot pass for the expected prices, and the crews'
practice for the producers that have one), and no `Producer` is made. The year arrays' producer columns (`ProducerColumns.of`) are
block reads of the store in sorted id order, read again when the store's `version` rose. A `Producer` is built only when something
asks for one through the mapping (`store[id]`, `.values()`, `.items()`, `.get`): the screens, the protocol, mods, the tests, and the
readers still on records (`grep -n "record.producers" sim` lists them; the commands in "What is left" count the builds a year).
The save is written from the columns in the old format (`ProducerStore.to_plain`). Rows are in entry order, an exit leaves a dead row
that `compact` removes (`order`, `rows_of` and the saves compact), `seat_sorted` puts them in id order at the year boundary. Exits
(`producer_exit.ExitBatch`), loan write-offs and loan requests stay Python, in producer order.

**Cohorts are columns.** `record.cohorts` is a `CohortStore` (`cohort_store.py`; `cohort_rows.py` declares the columns). Each float field
has a bit in `numpy_typed` saying it was written as a numpy float (the unmet and own-plan mappings keep a flag per figure), because
CPython's `sum()` compensates only over exact Python floats; a block write says whether its values are numpy floats (`set_rows(..., typed=)`).
A `Cohort` is built only when something asks through the mapping (`store[id]`, `.values()`, `.items()`, `.get`) and is a snapshot kept until its
row is written. The writers: `households_cohort.put_cohort`, `change_cohort`, `set_people`, `set_column`, `set_work_plans` and
`rebase_price_level` (a plain mapping, a test's, still works through them); the close writes every figure in one block
(`cohort_close_write.write_close`); `cohort_people.follow_population` rescales every tile's cohorts to demography's people in one block and
`apply_work_plans` stores the household-work plans that differ. Block reads: `store.column(name)`, `floats` (typed as written), `order`,
`rows_on_tile`, `tiles_present`, `ids_on_tiles`, `exact_total`, `unmet_of(need)`, `milled_of`, `pairs_of`, and `figures(rows)`, the
`CohortFigures` (id, tile, people, working people, last year's income, hired work, grains milled, optionally the own plan) that rules written over
a cohort read without a `Cohort` being built. Totals by tile in table order (`cohort_people.total_by_tile`) use `sum_in_order_by_group`,
which adds left to right from zero as the loops did. Converted to columns: the year's close (`year_close_households`: only the market-view
questions of `households_close.closed_figures` stay per cohort), `_follow_population` and the hunger by tile, `CohortColumns.build`, the labour
offers (`labour_offers_write`), `subsistence_cost_by_tile`, `outside_option_by_tile`, `ask_floor_by_tile`, `hectares_held`,
`ownership.owner_cohort`/`spread`, `year_close_owners.owner_table`, `titles.settle_tenancies`' steward, `titles_inheritance.divide_estates`,
`home_scope` (the home ids and working people), the state's wage bids, the mint's cash wanted, `debt_relief`, `lending`
(`expected_inflation_of`, the spare cash, `household_requests`), `year_accounts`, `flight_year.tenants_flee`, the plot parameters, the
own-plan hours and `_grow_own`, and `goods_respend_pack.pack`; and, through `cohort_reads.py` (the same answers from the columns or from a plain mapping of cohort-like objects), the land
margins and leases (`land_bid_year.best_margin` takes a tile id; `land_lease_year` reads `CohortFigures`), `capital_year.note_exposure`, the carriage
hours' populated tiles, `merchants_dispatch`'s poorest cohort of each tile, `take_up_own`'s owner, `country_figures` (`money_held` and the floor costs),
`api._ranked_cohorts` and `year_arrays_holdings.share_out`. The save is written from the columns in the old format
(`CohortStore.to_plain`). Tests: `test_cohort_store.py`, `test_cohort_people.py`, `test_cohort_reads.py`.

A warm year builds no `Cohort` (measured by counting `CohortStore._build` around one warm `game.step()`: a throwaway wrapper that records the first
non-store caller; `tools/measure/warm_year_profile.py` loads and warms the game). The first object reader after each block write rebuilds every
stale snapshot, so the count stays at zero only while every reader between two writes reads columns; a new reader that asks the mapping for a
`Cohort` brings the rebuilds back, and the wrapper finds it. The last three were `year_order_sources.cohort_orders`, `household_offers_year.plans`
and `lending.bid_household_loans`. `cohort_orders` reads `cohort_order_figures.order_figures` (the fields the orders kernel, the store offers, the land
and tool bids and the basket key read, a cohort-like tuple with the scalar types a `Cohort` hands back) and orders every cohort through
`households_orders_pack.kernel_orders` (the per-cohort `households.goods_orders` branch for a basket the kernel does not cover was never reached
and is gone); `plans` and `bid_household_loans` pass `CohortFigures` to the rules written over a cohort (`work_terms_at`, `grinding_plan`,
`households_credit.floor_bids`, which only read id, tile and people). `CohortStore.milled_of` keeps the tuple of each row until the row's grains
are written. The basket keys of all cohorts come from one pass (`household_work_year.signatures_of_figures`, `signatures_of`), whose hearths come from
`titles_worked.worked_shares`: the tenancies of a tile are read once for all its holders instead of once for each.

Tests: `sim/tests/test_close_pack_kernels.py`, `test_year_close_dividends.py`, `test_producer_close_write.py`, `test_producer_store.py`, `test_wear_kernels.py`,
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

The entry plans are a table, `EntryPlans` (`entry_plan_table.py`: recipe row, tile row, good column, runs, yearly return, in the order the plans
are applied), written by three compiled greedy loops that run the Python loops' steps in the same order, so the capacity, hands, room and
`built` each plan changes are what the next one reads. `entry_unmet.py` packs the markets with unmet demand (the gap beyond the spare output, the
recipes of each ranked by one sort over the returns kernel) and `entry_unmet_kernel.unmet_plans` takes the loop: unfilled demand at the recipe's
full cost, the size held to the trade the markets carried (`entry_plan_steps.sized_runs_at`, over `entry_plan_pack.traded_grid`) and the siting
(`entry_plan_steps.site_newcomer`, the same `site_choice` as before, the runs-anywhere branch and the unsited candidates now inside the kernel).
`entry_margin_tables.py` does the same for the margin and the trial (`entry_margin_kernel.py`): `Weighed` is `entry_bid_markets.weigh` as
columns, `ranked_by_cost` is `recipes_by_cost_many` as columns, and only the saved `margin_years` dictionary is read and written through the
markets' keys (`entry_margin.keep_streaks`). The three loops share the siting arrays of `EntryTables`, whose `_ready_siting` now runs once.
What each recipe's siting reads (`entry_plan_steps.SiteTables`) is worked out in Python once per recipe asked for, the first time it is
asked (`entry_plan_pack.site_tables`). The plain Python of the three rules (`entry.entry_plans`, `entry_margin.margin_entry_plans`,
`entry_trial.trial_entry_plans`) stays for a year with no arrays, and `test_year_speed_entry_arrays` compares the year's plans with and without them.
`open_entrants` reads the plan columns and applies them to the producer store: an existing producer's capacity and workshops are column writes, a
newcomer is a row appended by `ProducerStore.enter`, and the recipe's peers' crews come from `crews_by_recipe` (table order, as the mapping
iterated); the stakes and loan requests per plan are still made one plan at a time.

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
| priced needs as tables | `priced_need_tables.NeedBatch` (any number of (tile, basket) requests as need rows and good rows, spec rows kept per spec and per basket) and `priced_need_kernel.price_needs` (every need priced from a tile-by-good price matrix, exact sums and the share-limit search, ceilings). `priced_needs.PricedBatch` keeps the answer as columns over the priced goods (`names`, `price`, `effect`, `share`, `ceiling`, with `start`/`stop` per need row, and the same as numpy arrays in `arrays`); a basket's `priced_need_list.PricedNeeds` is the list of its need rows, read by `blocks()` (spec, price index, first row, end row). A `PricedNeed` object is made only when something indexes or iterates the list (screens, mods, tests, the reference rules). Tests: `test_priced_need_kernel.py` (the Python against the kernel bit for bit on written-out and random needs, with limits that bind and quality re-mixes, and batches of many tiles and baskets), `test_priced_need_list.py` (the columns, floor cost and column readers against the objects; no object made while columns are read) |
| orders template rows (`households_orders_pack.add_template`) | `households_template.template_rows` gathers a basket's row floats, pass-local good numbers, first unit, priority and name order from the answer's arrays in numpy (`selected_rows`, `LocalGoods`, `first_unit_of_goods`); what does not move with prices (areas, the book's good and market numbers of a tile's goods) is kept by tile and goods (`static_rows`). Test: `test_households_template.py` (against the per-row object loop) |
| close pack (`households_close_pack.PackedBaskets.add`) | a basket's goods, effects, lives and durable places from `basket_rows` and one book-number column by good number, no loop over goods. Test: `test_households_template.py` (against the loop) |

**Priced needs go through the kernel in batches, and are read as columns.** `priced_need_prime.price_asked` prices any list of
(tile, key, basket) asks together: one request per ask (a basket's whole `needs` tuple, no per-need dedupe or key) in a `NeedBatch`, the tiles'
offered prices as one matrix (`PriceGrid.matrix`, through `YearView.offered_price_matrix`), one `price_needs` call, and for each ask the
`PricedNeeds` of its priced need rows (`PricedBatch.positions_by_request`, two numpy passes over the batch). `priced_reads.kept_need_prices` uses it
for every miss: the tiles' own baskets (`TILE_BASKET_KEY`) all at the first miss after a write (`asked_by`), and any other ask by itself. The passes that
loop over cohorts ask for all their baskets first: `cohort_prime.prime_cohort_baskets` (the orders through `BidMemory.priced`, `lending.household_requests`,
`year_labour.subsistence_cost_by_tile`, `labour_ask_floor.ask_floor_by_tile`, `year_close_households.close_households`) and
`cohort_prime.prime_food_baskets` (`household_offers_year.plans`, for `grinding_plan`), once per write to the memory; a cohort whose basket changed
after that has another key and is priced when asked. `kept_need_prices_many` and `households_basket.tiles_need_prices` take a pass's asks up front
(`country_figures`). A view that cannot answer from its grid prices the basket from the offered prices through the same tables
(`priced_needs.priced_needs_at`). The readers take columns: `households_orders_pack.add_template`, `households_store.staple_price_per_kg`,
`store_return.service_values_per_year`, `household_work_year.grinding_plan` (the food rows are kept per tile and hearth, `_food_rows`),
`labour_ask_floor`, `state_budget.goods_bids`, `households_credit.floor_bids` and `floor_cost_unmet`, `country_figures` floor costs,
`year_labour` and `year_close_households` (`PricedNeeds.subsistence_cost_per_person`, the same `fsum` of the same products). A reader given a list of
`PricedNeed` objects (a test, a mod) is wrapped by `priced_need_list.priced_needs_of`. Tests: `test_priced_need_kernel.py`, `test_priced_need_prime.py`,
`test_priced_need_list.py`, `test_households_template.py` (`cohort_prime`).

**Cohort orders are below the bar.** `function_times.py SAVE` with no names times the cohort orders and what they call. No part that
`year_order_sources`, `households_orders_pack`, `tool_wear`, `households_cohort` or `opening_bid_memory` owns reaches the bar, so nothing
there is converted:

| Part | Owner | Why it stays |
|---|---|---|
| first touch of `CreditView.equity` (every producer's worth) | credit and equity | the next reader of `view.equity` pays it instead, so moving it saves nothing |
| `kept_need_prices` first touches in `BidMemory.priced` | `priced_reads`; shared with the close and the labour readers | the first asker prices every cohort basket in one batch (`cohort_prime`); the rest read kept lists |
| `add_template` (one per basket key per year) | the households' pack | prices change every year, so a template cannot outlive the year; its rows are numpy gathers (`households_template`); what stays per template is `_store_weights` (a basket key is a tile here, so no two templates share a tile's weights) and the `weights` dict loops |
| `land_bids` | land-bid owner | not in the households package |
| per-cohort reads (`ledger` wages and plot hours, balances, claims, loss rate, `tool_bids`), `change_cohort` of `planned_spending`, `_orders_of` | dict lookups and a record copy per cohort | vectorising them costs a column copy of every cohort field for a saving far below the bar |
| `year_orders` (the compiled kernel) and `cohort_bid_rows` | already compiled | |

Revisit after the cohort records become columns, when the cohort figures can be handed to the kernel as slices of those columns.

**Who needs `Cohort` and `PricedNeed` objects.** `Cohort`: every module that reads `record.cohorts`. `PricedNeed`: nothing in the year loop (a warm Rome
year makes none, count them with the profile); the reference rules (`households_orders.goods_orders`, `need_basket.need_prices` in `actors/world_people`,
`households_close._priced_needs`, `goods_respend.priced_needs` which prices at the cheapest asks), the screens and the mods.

**Measured on a warm Rome year** (`python3 tools/measure/warm_year_profile.py .scratch/rome_start.json OUT.prof`, then `pstats` `print_stats` and `print_callers`; the objects counted by wrapping `PricedNeed.__init__` around the profiled `game.step()`; cProfile inflates times about three-fold, calls are exact). `PricedNeed` objects built: 6097 before, 0 after.

| Function | Calls before | Calls after |
|---|---|---|
| `PricedBatch.need` | 1665 | 0 |
| `priced_need_prime.need_key` | 13440 | removed |
| `need_basket.priced_need` | 5248 | 0 (the kernel prices every ask; the function is the reference) |
| `need_basket.price_ceilings` | 4432 | 0 (a ceiling is a column of the answer) |
| `priced_need_tables.NeedBatch.add` | 1944 | 530 (one per ask, not per need) |
| `priced_need_prime.price_asked` | 3 | 9 |
| `households_orders_pack.add_template` own time (106 calls) | 19 ms | 8 ms; rows are numpy gathers |
| `households_store.store_candidates` calls of `dict.get` | 28250 | not among the fourteen most-called callers (the last of them has 16468); it loops the storable goods that have a price |
| `households_close_pack.PackedBaskets.add` own time (312 calls) | 14 ms | 2 ms |
| `households_own.own_production` own time (538 calls) | 9 ms, every need of the basket | 7 ms, the needs that have an option (`growing_needs`) |
| `household_work_year.basket_signature` | 5122 | 3344 |

Still per item in the households' part, and why: `static_rows` asks `view.area_of(good, tile)` once per good of a tile (the area map is a
dictionary of dictionaries, no array form); `_store_weights` runs `store_candidates` once per tile (`math.log` and `math.exp` in `carrying_return` and
`split_by_return` and `math.fsum`, whose last digit a numpy or numba port would have to reproduce, and its result is a dict of weights that `store_offers`
reads) and `store_holding` reads the book's stock of each store good; `own_production` runs per cohort over the needs it can grow (hours, hectares and
the next need depend on the one before; it makes a `GoodsMove` per grown good that `post_in_order` takes); `grinding_plan`, `priced_basket`,
`basket_signature` and `has_hearth` run per cohort: the signatures come from the cohort columns (`signatures_of`) but the hearth asks the land titles per
cohort (`titles_worked.worked_share`); `household_offers_year.plans` and `BidMemory` still take `Cohort` snapshots (the orders pack reads their fields).
A warm Rome year builds 1131 `Cohort` snapshots (counted by wrapping `CohortStore._build`), none of them from the priced needs' readers: the sites are
`land_lease_year._margins`, `capital_year.note_exposure`, `carriage_hours.bid_figures`, `year_order_sources.cohort_orders` and `lending.bid_household_loans`.

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

- `merchants_batch.prepare` (called by `merchants_plan.prepare_rows` from `lending.merchant_requests` and `year_order_sources.merchant_orders`)
  searches the candidate rows of every merchant of a pass in two kernel calls (`merchants_batch_kernel.search_blocks`, which searches
  once for the merchants that count the same prices in a good and redoes only the (merchant, good) cells that needed unknown holding
  years, then `sorted_rows`, the two stable sorts of `numpy.lexsort`); `merchants_plan` takes a merchant's rows from the pass when its rate,
  home tile and expected prices are the ones searched. `RouteBook.nearest_flat` keeps each area's cheapest haul out.
- `merchants_book.route_pass` reads the memory's price column by slot (`FloatStore.values_in_slots`, `YearView.prices_by_slot`); a view
  without that method is read good by good as before.

The merchants' per-merchant state is a table (`merchant_table.MerchantTable`, one per record, found by `MerchantTable.of(record.memory.tables)`):
capital base, the expected price and volume matrices (merchant row by goods-market row; `RowFigures` is a merchant's dict-like row), the hauls
on the road (ragged rows with interned goods and tiles) and the price histories (ragged, sorted by packed key). A `Merchant` is a handle on its
row; the save still writes each merchant as before. On the table, `merchant_year.learn_year` (one `hear_all` kernel for the news and
histories, one array step for the figures) and `merchant_year.close_all` (`settle_profits`, exact sums) replace the per-merchant learning and
close; `merchants_credit_batch.credit_requests` sizes every merchant's loan in one kernel (`commit_credit_all`) from rows searched together
(`merchants_batch.search_arrays`) and stock by slot (`held_by_slot`); `carriage_wear_batch.settle_all` keeps and wears every merchant's carriers
in two passes over the book. `merchants_dispatch.dispatch_merchants` dispatches every merchant of the year in one kernel call (`merchants_dispatch_settle_kernel.dispatch_all`) over
four tables (`merchants_dispatch_tables`): pairs (a haul's fee, crew hours, carrier wear, dues and carrier money, once for each distinct source and
destination), routes (what a merchant holds at a good and source tile), legs (a route's destinations) and merchants (purse, crew hired by key, fleet by
carrier good). The kernel shares each route's stock over its legs, sizes the shipments, cuts them to the crew hired, the fleet's wear and the purse,
pays the dues and the fee, wears the carriers and pays the rent of hired fleets, moving the purses in merchant order (a merchant paid rent by an
earlier one dispatches with it). `merchants_dispatch_pack` is the edge that builds the tables once a year (and `wear_needed`, the same tables read by
`merchants_dispatch_kernel.wear_needed_all` for `share_idle`); `merchants_dispatch_answer.Dispatched` reads the answer back as the `merchants.Dispatch`
each merchant had, and the moves and transfers are posted to the book once. `merchants.dispatch` stays as the per-merchant reference the tests compare to.
Still per merchant, with their inputs as Python objects: the reads that fill the tables (`inventory.held_stock`, `carriage_fleet_book.own_capacity`,
`carriage_hours.engaged`, `merchants_transit.advance`), the writing back of the answer and the per-move ledger notes (`carried_book`, `flow_ledger`), then
`merchants_plan.orders` (stock arrays, `routes` legs, `Bid` and `Offer` objects handed to `OrderRows`), `carriage_fleet_book.bids`. `python3 tools/measure/function_times.py SAVE sim.economy.merchants:learn_year sim.economy.merchants:close_year sim.economy.merchants_batch:prepare`.

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

**Cached on the memory channel, and kernels in the phases.** `agent_rate`, `agent_people_by_tile_and_trade`, `agent_need_floor_costs` and
the keyed `agent_hours_offered_cell` (the workforce's read of the hours a trade offered at a tile; `agent_hours_offered_at` stays the
uncached quote) are cached on the markets module's `memory` channel (`sim/markets/module_spec.py`, `_WATCHED`; test
`sim/tests/test_agent_views_cached.py`; a game stepped with
`game_assembly.SHADOW_CHECK_EVERY = 1` re-checks every cached read, no `StaleView` over three Rome years). `ActorWorld` builds a part the first time it is asked for (`sim/actors/world.py`), so a world made for one
answer builds one part and each world keeps its own turn's memo. The stability phase reads a state's tiles as columns and runs
`stability_kernels.read_tiles` once per pass (a rising ends a pass; `sim/campaigns/stability_tiles.py`, tests `test_stability_kernels.py`,
`test_stability_tile_passes.py`, the plain chain in `sim/tests/stability_tiles_plain.py`). Still per actor in Python: the government's and
the strata's year (`agents/government*.py`, `budget*.py`, `stratum_year.py`), the household theft exposure, `material_prices`
(`sim/prices/module_spec.py` says why it cannot be cached), `urban_fraction`, `reachable_trade_population` and the quotes (see the table below).

Tests: `sim/tests/test_response_memo.py`, `test_year_accounts.py` (`PlainLedgerReadTests`), `test_year_ledger_views.py` (`as_plain`).

**The first work of figures after the economy stepped.** Measure with `python3 tools/measure/warm_year_profile.py SAVE OUT.prof` (kernels
compiled first, `compile-kernels`, or the profile times the compiler) and read the calls and own time of each function with `pstats`.

| Figure | Before | Now |
|---|---|---|
| price response of a book (`market_curves.price_response`) | a clearing through `goods_market.clear_at_one_price` per book (`Bid` and `Offer` objects, fills, a `DemandSchedule`) | `curve_clearing`: the summarised book is columns kept against the book object (`PreparedCurve`), the crossing is one kernel (`clear_summary`, over `crossing_price.price_at_levels`), and the book alone is cleared once per last price; no `clear_at_one_price` call, no object. Test: `test_curve_clearing.py` (columns against `price_response_objects`, bit for bit, on written and random books); a figure the kernels do not take (`NeedsObjects`) is answered by the objects |
| floor costs of the tiles (`_worked_need_floor_costs`) | one `price_asked` batch call over every tile of the country; a `PricedNeed` per priced need | the same one batch call; the floor costs read `PricedNeeds.blocks()`, no object and no per-need key |
| `country_figures._prices`, `price_index.kept` | already columns: `MarketLayout.masked` builds the country's mask from the tile table (`price_index_masks.country_price_mask`), `national_prices` reads the goods table's columns; `MarketLayout.kept` (the per-market Python rule) runs only for an area map without a tile table (a test's stand-in) or for no rule | unchanged |

Still per item, and why:

- **`material_prices`** (read from many views a year, `prices/tables.py` `Tables.price_tables` lines 43-69): the cost is the validity check of the table (the
  techniques granted and in use, the banded farmed hectares, the market rate, the home tiles), not a loop over goods; `rules.money_prices` runs only when the table or the hour's money moves. It stays uncached for the reason `sim/prices/module_spec.py` gives (its inputs are written outside the owners' commands); the check
  can be cached once `techniques_in_use` and `market_rate` bump a channel.
- **`urban_fraction`** (`demography/urban.py` `urban_people_by_tile`): the ceilings are worked out once a year
  (`_computed_urban_ceilings`, mostly `kept_carriage_costs`, a geography route read); each read then takes `min` over three per-tile dicts
  (`people_for_urban_share`, the ceilings, `world.urban_share_of_people`), which are dicts of the demography world, so an array form would first copy
  them and cost the same.
- **`reachable_trade_population`** (read once per available trade by `engine/invariants.check_labour_market_invariants`: each is
  `LabourSupply.market_supply` (`people_who_exist` through `hands_available`, `labour_supply.py` line 153), the work of that trade, and the two
  literate trades repeat `literate_capacity` (`staff_ceiling`, finance reads). A block form needs the labour core's people by trade as a column.
- **`output_value_and_unpriced`, `money_held`**: the producers' conversion.

## The government's year as tables

| Phase | Table and kernels | What Python still does |
|---|---|---|
| keep of the bonded (`stratum_year.true_up_keep`, `settle_keep`) | `agents/keep_table.py`: one row per bonded stratum, one per keeper; `plan_keeps` draws the keeper's purse down in row order and says which payments it covers | `keep_boundary.py` reads the rows and posts each payment with `ledger.transfer`; a payment the purse does not cover, and every later one of that keeper, goes to `ledger.pay_up_to` (the facility and deposits are contracts the book owns) |
| revenue assessments (`revenue.assess`, `world.revenue.revenue_assessments`) | `agents/assessment_kernels.py`, `assessment_table.py`: one row per form, one per (form, payer); `assess_forms` (reach, rate, tonnes, leakage, payers' seen income and amount owed, Neumaier sums as the built-in `sum`) | the bases are read once per form through the world's views (`revenue_bases.py`); `AssessmentTable` is also a sequence of `Assessment` objects, made from a row when a test, the fiscal menu or a mod asks |
| taking the revenue (`Stores.receive_revenue`) | `plan_collection` (what each payer's first posting pays), `receipts` (coin and labour owed by form), `accumulate_by_group` (goods taken in kind onto the stores, labour owed by destination) | the postings (`ledger.transfer` per payer: each is booked, noted on both parties and seen by the transfer hook); a payer's later rows read its purse again |
| tax collectors (`budget_works.collection_line`) | `collectors_needed` over the forms table | the line itself is still a `Line` |

Not converted, with the measured reason (`warm_year_profile.py`, one warm Rome year: two governments, twelve strata, sixteen actors):
`ActorRegistry.advance` (one pass over sixteen actors, each `actor.advance` a Python method a mod's actor kind overrides; `kinds` in
`ActorExtensions`), `Government.pay_standing_need`, `budget.standing_lines` (about a dozen `Line` objects per government; the profile's
time under it is the world's price and wage views, not the objects), `state_enterprises.run` and `run_enterprises` (a loop over the plants,
each `business_books.operate` posting through the producer records the producers' conversion owns). Re-measure before acting.

## Other callers of the book and views in the year loop

| Caller | Decision |
|---|---|
| `carriage_wear.settle` | converted: the merchant's and the carrier account's holdings are read once, not once per good (nothing moves between the reads) |
| `Economy._grow_own`, `Economy._build_plant` | converted: each cohort's or producer's moves are a step of `posting_sequence.post_in_order` (one batch each, applied in order in one kernel call), posted once after the loop; neither loop reads the book between steps. What remains is the ledger writes, `hectares_held` and the posting-row build |
| `year_close.tax_facts` | converted: `book.balances_of` once for the taxpayers' list, in the book's name order |
| `producers.live_input_prices_at`, `live_wages_at` | not converted: both already read the tile's block (`present_prices_at`, `wages_at` keep one answer per goods tuple and tile until the memory is written to). A producer stands for one recipe on one tile, so there is little to share between callers, and what is left per call is the dictionary built for the caller. Needs a recipe cost grid (recipes by tiles) before it pays |
| `agents.purses.transfer` -> `book.transfer` | not converted: each transfer first draws on the payer's facility and repays the payee's debt from the purse the earlier transfers left, and the callers are the actors' own advance steps spread over many phases, so a batch would change what each draw sees |
| `YearLedger.running_costs_of` (from `goods_production.turn_figures`) | already a block read; sharing the agent rows between the two figures made no measurable difference (the cost is the pending notes flushed into the table) |
| `country_figures.money_held`, `credit_lines.lender_standings`, `land_bid_year.firm_land_bids`, `land_market.settle_year` (the rent cash), `lending.lend_working_capital`, `lending.household_requests`, `capital_year.snapshot` and `_arrange_cover`, `year_order_sources.cohort_orders`, `entry_year.close_idle_producers` and `_restake_over_arrays`, `Economy._rebuild_worn_plant`, `plan_year.plans_of` (the producers the kernel leaves), `payable_keep`'s balances | converted: one `balances_of` or `balance_by_agent` for the list the loop goes over, taken before the loop (none of these loops posts, or its postings are queued to the end, so the balances read together are the ones read one by one) |
| `producer_exit.exit_producer` (through `ExitBatch.hold`), `land_bid_year.take_up_bought`, `state_budget.goods_bids` | converted: the goods the agents hold are one `goods_held_many` (or one `goods_held` before the loop); the exits post at `finish`, a buyer's move leaves the other buyers' stock alone |
| `year_accounts._goods`, `NestedView.as_plain` | converted to columns (see "The year ledger") |
| `EconomySetup.countries`, `tiles_of`, `home_scope.home_cohorts` | converted: `country_by_tile` (one pass over the tiles, `setup_countries.py`) in place of `country_of` once per tile; `home_cohorts` asks about each distinct tile once. `country_of` stays per tile for the callers that ask about one tile at a time (`recipe_allowed`, `carried_book.trade_book`, `route_dues_levied`, `merchants_dispatch`): the owner map (`tile_owners`) is shared with the game and changes during it, so no table of it can be kept between calls |
| `YearView.area_of` / `areas_of` | the area map keeps each tile's table of goods to areas (`AreaMap.areas_on_tile`, made on first ask, since the areas do not change) and the view reads it, so a new view no longer works every pair out again; `areas_of(names, tile)` and `view_areas.areas_in` / `areas_of_pairs` answer a list in one call (`wages_at`, `goods_respend_pack.pack`, the plan table's labour and missing areas). A stand-in view or area map without them is asked one by one |
| `agents.purses.transfer` -> `book.balance` (`purses.purse`) | not converted, same reason as `purses.transfer`: the balance is read after the transfers before it |
| `bonded_purchase.settle` | not converted: each group posts (`book.transfer_many`) before the next group reads its employers' balances, and an employer can pay in several groups |
| `entry_year.open_entrants` (the owner's cash per plan) | not converted: the stakes already decided lower an owner's cash for the next plan (`owner_cash`), a greedy loop over `Producer` records |
| `year_accounts.plain_rows`, `inventory.held_stock` | below the bar |
| `_remember_markets` `wanted_at_rows`; the object-rule markets (`unsold_search.clear_with_search`, `seller_offers.strategic_offers`, `goods_market.clear`) | below the bar; a kernel would leave part of each (the packing and the boundary) |

Time any of these with `python3 tools/measure/function_times.py SAVE module:function ...`.

## What is left

One list; each item names what blocks it. Every item is to be converted, whatever its share of a step; re-measure before acting, since the
list lags the code.

- **Entry: what is left after the plan loops.** The application of the plans in `open_entrants` (a `Producer` per plan, the owner's stake
  taken from the cash the earlier stakes left, the entrant's loan request, `peers_of_recipe` for the crew) is a greedy loop over `Producer`
  objects in `record.producers`, which every phase reads as a dictionary of records; it needs a column store of producers. The per-recipe reads
  of `EntryTables` (`_site_of`, `_ensure_crew`: the people allowed by country, the yield row, the crew's practice) are Python per recipe; they
  need recipe-by-tile and recipe-by-trade tables built once per setup and updated when a country learns a technique. The unmet demand, `margin_years` and `volumes` are columns that
  entry reads whole (see the goods items below).
- **`record.goods.curves`.** `volumes`, `unsold`, `unmet` and `margin_years` are columns of the memory's goods-market numbering
  (`goods_market_column.MarketColumn`, a `MarketFigures` keyed by market name; saved by name, carried over an area redraw by the memory's
  remap, dict-like for the UI and tests). Entry's traded grid, margin streaks, the batch's market sizes and the unmet-demand plans read
  them whole. `curves` holds one book summary per market, not a number, and is still a dictionary; `entry_year._traded_volume`,
  `notional` and `country_figures` still read single keys.
- **Per-good price readers.** `entry_year._traded_volume`, `producers.paid_input_prices` and `next_expectations` read many keys a year,
  each a dict lookup; the year view has no cleared-price block. `producers.live_input_prices_at` and `live_wages_at` need the recipe
  cost grid.
- **The mint reading the results table; the object-rule markets as kernels; the watchers' fills from columns.**
  The mint keeps one `ClearingResult` per market of the coin metal in `ledger.mint_takes`; the watchers' buy fills are `Fill` objects (`bought_by`, only for markets a merchant or the state bought in);
  `LeftMarket` and its `bought` mapping are built from columns when a market not on the tables asks.
- **The goods side's remaining objects.** The year builds no `Cleared`, `MarketRows` or `LeftMarket` for a market on the tables: `clear_good`
  returns a `GoodClearing` (columns), the year's table holds each market's rows, and `goods_left_markets.LeftMarkets` makes a `LeftMarket` only
  when a rule over objects, a test or the UI asks (the entry rules reading `ledger.bids_by_market` per market, and the coin metal's markets,
  still ask). What is left: the coin metal's markets are remembered by the Python rules (`year_remember.remember_one`) because the mint's top-up
  (`mint_price.received_price`, `YearLedger.mint_takes`, `settled_to_mint`) is over (seller, tile) dictionaries and `ClearingResult`s; a market a
  book edge sells in (the mint's wash) is cleared on `Bid` and `Offer` objects (`seller_offers.strategic_offers`, `unsold_search.clear_with_search`,
  `goods_market.clear`, `market_quote`); `_tax_in_kind` builds `YearFacts` dictionaries (the tax rules, `taxes.assess`, take dictionaries); the
  watchers' buy fills are `Fill` objects made only for markets a watcher bought in; `GoodClearing.result` makes a `ClearingResult` for the mint and
  the watchers. `entry_year._traded_volume`, `country_figures` and `api.market_record` still read single keys of the goods record's columns.
- **Tool wear and fallbacks in the plan kernel.** `plan_year` sends a producer whose recipe has tool wear or fallbacks, or a zero entry, to
  `producers.plan`; `plan_kernel.plan_rows` would need the fallbacks' bids and `tool_fallback.value_in_use` ceilings. `_tax_in_kind` builds
  `YearFacts` dictionaries for the producers on home tiles when a tax is paid in kind.
- **The producer record readers.** What still builds a `Producer` in a warm year (count them with `ProducerStore._build` wrapped, as
  `tools/measure/function_times.py` wraps a function): `producers.plan` for the producers the plan kernel leaves (tool wear, fallbacks),
  `land_market.demands_of` and `post_rents` (`expected_output_prices` and the live prices read the record), `year_goods.clear_goods`
  (`plant_makers`, and `_produce_and_offer` when there are no arrays), `seller_offers`, `unsold_search`, `goods_production`,
  `equity`, `labour_state`, `workforce_settle`, `shares`, `funds`, `tax_farming`, `location*`, the entry rules without the year arrays,
  and `api.producers_of` / `all_producers` for the screens and mods. Each reads a handful of fields the columns hold; they move one
  at a time to `store.table` blocks or `ProducerColumns` fields. The crews' practice is still a small dictionary per producer that has a
  crew (`write_close` and `ProducerStore.crew_of` build one), since `practice.crew_runs_after_year` is Python on mappings.
- **The cohort record readers.** What still builds a `Cohort` in a warm year (wrap `CohortStore._build` and count, as the producers' item
  says): the rules written over a `Cohort` object that the opening and the tests share: `land_lease_year._margins` and
  `land_bid_year.best_margin`, `capital_year.note_exposure`, `year_order_sources.cohort_orders` with `households.goods_orders` and
  `households_orders_pack` (the kernel entries hold the cohort), `household_work_year.work_terms_at` / `cohort_plan`
  (`household_offers_year.plans`), `lending.bid_household_loans`, `titles.settle_tenancies`' callers, `opening_*`, `equity`,
  `api._ranked_cohorts`, and, outside this item's owner, `country_figures` and `carriage_hours`, `merchants_dispatch`. Each reads a handful of
  fields; the next step for each is to take a `CohortFigures` (or the fields) as the readers above already do. Builds happen once per row
  per write: a block write drops every kept snapshot it touches, so one reader left on records in each phase between two writes pays the
  whole phase's rebuild. The whole-year writes (`planned_spending` after the orders, the close) are why a single reader per phase matters.
  `closed_figures` still asks the market view per cohort (`view.currency_of`, `basket_price_level`, `observed_inflation`, `equity`, `claims`
  are scalar questions into the markets' views) and `hearth_of` asks the land titles per cohort (`titles_worked.worked_share`).
- **Labour readers that take records.** The cleared wages reach `HourSupply.settle` as a dict read rather than a market-indexed array.
  The household decisions still loop over cohorts in Python (`household_offers_year.plans`: the basket, grinding plan and priced needs
  of each cohort); `outside_option_by_tile`, `subsistence_cost_by_tile` and `ask_floor_by_tile` read the cohort columns and share a priced
  basket per signature (`PricedNeeds`, primed for all signatures at once by `cohort_prime`). `plans` still builds the `Cohort` snapshot of each
  cohort for `work_terms_at`, and `hearth_of` asks the land titles per cohort.
- **Labour readers that take records.** `household_work_year.decide` and `household_hours_year.plot_parameters_by_cohort` read
  `LabourOffer` objects; the cleared wages reach `HourSupply.settle` as a dict read rather than a market-indexed array.
- **Country figures that read per producer or per market record.** `country_figures.output_value_and_unpriced`, `_traded_volumes` and the people counts read producer and cohort records and the saved volumes dictionary one at a time; an array version of `_traded_volumes` was measured slower while the layout of the volumes' keys is rebuilt every year, so it waits for the volumes as a column.
- **Loan requests** become a table at the clearing; `LoanClearing.loans` and the bank rules still read `Contract`/`LoanRow` objects.
- **Cached views** in the "Left uncached" list wait for their input's owner to bump a channel.
- **Area reads in the households' files and the labour offers.** `households_orders_pack`, `households_store` and `labour_offers_write._area_numbers`
  (which takes a callable `area_of(trade, tile)`) still ask `area_of` one pair at a time; they would take `areas_of_pairs`.
- **The settlement of a good** (`settlement_ids.settle_by_ids`, `year_ledger_arrays.note_settlement_rows`) is one call per traded good, each reading the
  purses and stocks the good before it left (`cash_state = book.balances_at(agents, currency)`), so the goods cannot share a call without a kernel
  that settles several goods in order; the noted rows could be queued across goods (`year_ledger_batch.PendingNotes` queues object rows only).
  The per-market `delivered` is a numpy `sum` per market, whose pairwise adding a kernel must reproduce to the last digit.
- **The book's remaining Python-to-kernel calls** are one kernel per scalar read (`Book.stock`, `holdings`) from the loops that
  read one cell or one agent at a time (`producers.runs_for_stock`, `producers._input_bids`, `households_store.store_holding`,
  `economy._build_plant`) and one apply per step of a loop that reads the book between steps
  (`goods_production.post_lines` per turn, `purses.transfer`, `bonded_purchase.settle`). A year-level posting queue does not fit these: each
  reads what the last posting wrote, or needs the refusal at the call. They move when their loops are columns (`stock_block`, `balances_of`).

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
