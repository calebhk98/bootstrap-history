# The compiled year: shared tables instead of per-item objects

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
   and writing tables, no per-item objects from plans to the ledger. **Gate:** after this stage the warm-year instruction
   count must be clearly below the stage's start; if it is not, stop and re-plan.
3. **Close, then entry and credit** (variable-length searches and greedy queues; the smallest share of the year).

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
