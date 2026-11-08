# The compiled year: shared tables instead of per-item objects

**Status:** stage 1 under way (Complaint 968 is the problem this answers). The book, the year ledger, the labour core and the close are on tables (below); the market memory and the goods side are with other owners.

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

