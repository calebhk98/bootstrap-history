# Complaint 497 history: rounds of speed work

Each section is verbatim from the complaint as of the move, in its original order. Timings were taken on a shared machine on the commits of the day; re-measure before relying on a figure. `Complaints/497-*.md` carries the current state.

## Partner civilisation records read once per game

A profile of one stepped year of a game with a partner outside the agent economy (the setup of the
`home_cargo_price` topic) found `load_civ` called thousands of times a year, nearly all to read one field of a
partner (`coin_standard`, `state_capacity`, `opening_stock`, `population`, tiles held, the route). The `Sim` now
keeps each loaded partner for the game (`Sim.partner_civ`, `sim/engine/foreign_economies.py`) and the per-year
readers go through it: partner coin metal, the foreign-economy facts, foreign supply and mineral share, coin
carriage, partner spending and coin settlement, the living-stock trade, smuggling and routes, and the goods
market's route lookup. The shared record is read-only; nothing that reads it writes to it (checked: after
three stepped years the kept records equal a fresh `load_civ`). Same stepped save before and after (sorted-key
dump of `save_state` after three years, identical). Measure with `cProfile` over `Sim.step()` and
`pstats.print_callers("load_civ")`; any `load_civ` caller still showing counts per year should read through
`partner_civ`.

## Route graph compiled once per set of modes and improvements; defender search remembered

A profile of one stepped year sorted by self time (`cProfile` over `Sim.step()`, `pstats` sorted by
`tottime`) put `routes_compile.compile_graph` first among the project's own functions: the route search
compiles a graph for every distinct set of freight prices (one per good priced, so many per year), and each
compile re-derived every edge's modes, grades, rates and physical costs, which do not depend on prices. The
price-independent links are now built once per (modes, improvements) and kept on the map
(`routes_compile._skeleton`); a compile for a set of prices only scales them, in the same order and with the
same expressions. `sea_freight.defenders_to_hire` is a pure search over constants, called for the same few
arguments thousands of times a year by `_sea_crew`; it is now memoised. Same stepped save before and after
(sorted-key dump of `save_state` after three years, identical). Measure with the compile time inside one
step (wrap `compile_graph` with `time.process_time`) and CPU of `Sim.step()` over several runs. The profile
after these is again flat: the next items are the many small readers of fixed data (`parameters.parameter`
and `RateTable.rate` lookups, `_price_tables` per call) and the goods clearing's own arithmetic.

## Carrier models kept between price changes

`_carrier_models` (`engine/foreign_routes.py`) was rebuilt on every call, over a thousand times a year, though
it depends only on the price table, the sea crew's wage, the map and the team size. It is now kept while those
are the same objects or values (the rest of the build is `_build_carrier_models`, unchanged). Same stepped
save before and after (sorted-key dump of `save_state` after three years, identical). Measure with `cProfile`
over `Sim.step()`: builds fall from the thousand to a handful, and the profile loses a few percent of its
function calls. Step CPU on the shared machine varies more than the saving, so count the calls.

Checked and left alone: `parameters.parameter` and `RateTable.rate` no longer show any measurable self time in
the profile. `_price_tables` already returns its kept tables; what remains in it per call is computing the keys
(the banded market rate and the techniques in use), which is the check itself, so memoising on its inputs
would save nothing.

## Merchant route search: trip years kept per pair, tighter destination loop

In a Rome agent economy stepped on its own (the setup of `economy_bronze_market_price`), `merchants._candidate_routes`
is about a third to two fifths of a year's CPU, nearly all of it `_good_routes`. Its inputs differ for almost every
merchant and pass (each merchant's expectations, and the credit and ordering passes see different interest rates), so
the route memo seldom hits and a larger memo does not help; the cost is the inner loop over destinations. Three
changes, each exact: the years a haul between two tiles is held (`merchants_transit.years_between`) are kept per
carriage table instead of recomputed from `days_between` for every destination and every area's news lag; a merchant
works out once per call which areas' news has reached it; and the destination loop drops the checks that cannot
fire (the source's own area nets a loss, an unreachable tile nets minus infinity) and tests one threshold instead
of two. Same stepped saves before and after (sorted-key dump of `save_state` after three stepped years, and the
shown and traded prices after three `economy.step` years, identical). Measure by wrapping `_candidate_routes` with
`time.process_time` over several `economy.step` years: its share falls by about a fifth, and a whole year by
under a tenth. Shared-machine variation in a whole step is larger than that, so compare a replay of recorded
`_good_routes` arguments, interleaving the old and new function. What remains is the loop itself (one carriage
lookup per destination examined, per source, per good, per merchant); cutting it further needs fewer distinct
questions, not a faster answer.

## Merchants with no cash search only for the stock they hold; book totals read without per-agent sorting

In a saved Rome game (`python3 sim/simulator.py play --civ rome_100ad --session FILE`, then `step 1`), nearly all
merchants hold stock but no cash and no capital. `merchants.orders` built the whole candidate-route list for each
of them (every good, every source area) although a merchant that cannot buy uses the list only to send stock it
already holds along the route out of its area, and `credit_request` returns before searching for a merchant with no
equity. `orders` now asks `_candidate_routes` for the held goods only, and `_good_routes` for the source areas
holding that stock only (`only_held`, `source_ids`); each row is the row the full search gives, the partial result
stays out of the memo the full searches share, and the held-tile list is sorted once per good instead of once per
row. A merchant with cash searches as before. Also: `merchants.close_year` learns prices and volumes inline (same
arithmetic as `_expect`) and `year_close` works the news lag out once per anchor tile per merchant; the year's
stock totals (`year_accounts.stocks`) come from `Book.goods_totals` instead of `holdings` for every agent
(`math.fsum` is order independent, emptied stock is skipped as before).

Same stepped save before and after (sorted-key dump of the save after three warm years, byte-identical); the
totals were also compared with the old computation at each call over two years. Measure CPU per warm year as the
CPU between the second and third `play` prompts of a saved game stepped one year first (in-process, patching
`input`): about a fifth lower (roughly 5.6 s to 4.6 s on a shared machine, including one save per command), with
`merchant_orders` falling from about a quarter of the economy's year to a twentieth. Left alone, measured as
flat: the clearing core (`clear_goods`), producers' planning and closing (about 5000 producers a year, each
costing the same unit costs several times), the labour year, and `MarketView.area_of` (half a million calls over
two years, spread over households, producers and entry).

## Round 2: route search skips what cannot pay; the year is flat, merchants are its largest part

Measured on a fresh `rome_100ad` save, a year (warm, `step 2` after `step 1`, CPU) is about seven seconds on the
shared machine, nowhere near the target. Wrapping the economy's phases in `time.process_time` (not under
`cProfile`, which inflates call-heavy code) gives, as shares of a stepped year: merchants' orders and credit
requests together about three tenths, `clear_goods` about a fifth, `close_agents` a tenth, the labour clearing
under a tenth, entry and households' orders a few percent each. Producers' planning is about two percent and
their closing about five, so the "five thousand producers a year" lead from round 1 is not where the time is.

What was cut, each exact (same stepped save: the sorted-key dump of the save after three warm years is
byte-identical before and after): `merchants._good_routes` returns at once when the dearest destination, kept
after spoilage, cannot cover the cheapest source's floor cost, skips a source whose floor cost the dearest
destination cannot cover before reading its carriage row, sorts the destinations as plain tuples instead of by a
key function, and reads the years a haul is held from the table's own memo (`merchants_transit.years_kept_for`);
`shared_room` no longer builds an empty sum for a good the merchant does not hold. Replaying the captured
`_good_routes` calls of one year against a copy of the old function (interleaved, `time.process_time`) gives
about a fifth less CPU in that function and no differing row (`sim/tests/test_merchant_good_routes_exact.py` keeps
the equivalence against a search that tries every destination). Whole-year function calls under `cProfile` fall
by about a tenth; whole-year CPU moved by less than the machine's run-to-run variation (a few percent either way
at a load average of six), so no per-year saving is claimed beyond that.

Checked and left alone, with what was found:

- **Sharing the search between merchants.** Across the merchants of one year nearly nine in ten full searches
  differ in some area's price (a median of about a seventh of the areas, by a median of about an eighth of the
  price): the merchants' own expectations are genuinely different, so a bigger memo or a shared base search
  cannot be exact. The credit pass and the ordering pass also see different interest rates (the credit clearing
  moves the rate between them), so they cannot share either.
- **A nearest-first walk of destinations.** Replaced the walk over dearer destinations by a walk outward by
  carriage cost with an early stop. Exact, but about twice as slow: a source examines only a handful of dearer
  destinations (a few per source), while the nearest-first order has to step over every nearby tile.
- **Producers' repeated unit costs.** Memory prices change as each good clears, so a cost computed at planning
  is not the one the seller's search sees later; caching across those calls is not exact. Within one call the
  repeats are a few dict reads each.
- **`MarketView.area_of`** is already a per-view dict lookup (`YearView._area_by_tile`); the call count is the
  cost, spread over households, producers and entry.
- **`clear_goods`**: a market has on average between one and two sellers, so the book's sorting and the
  reservation search are not repeated over long lists; what is left is the per-market fixed work.
- **Collection.** `Economy.step` shows a few percent of its own time after the year: the cyclic collector, kept
  off during the year, walks the whole young generation when it is switched back on. Freezing the heap instead
  would keep the year's cyclic garbage for good, so it was not done.

What would still move a year by a quarter is structural, as listed above: one `play` process for many commands,
shipped price tables for every rate band, fewer merchants' distinct searches (a model change), or compiled
clearing.

## One process for many commands

`agent` and `play` already read commands from stdin in one process; what an agent driving the game one tool call
at a time paid was a process (build or load, rebuild the economy) per command, plus a full save after each. Both
now take `--save-interval SECONDS` (`sim/ui/save_policy.py`): the default 0 saves after every command as before; a
positive figure writes when that long has passed, on `save`, `load` and `quit`, when the game ends, and on
leaving. `sim/PROTOCOL.md` and `playtest/BRIEF.md` say how to keep one process alive (a named pipe).

Exact: `sim/tests/test_cli_one_process_session.py` compares the sorted-key dump of the save after the same commands
(including two `step 1`) run one process per command, one process, and one process with held-back writes, and the
same for typed `play`. It found one difference: a whole number in a civilisation's church data stayed an int in a
fresh game and became a float after a reload; `sim/agents/cast.py` now makes it a float when the record is made.

Measured, CPU user plus system, three runs at a load average of 6 to 7: eight `agent` commands (norse_900ad, seed 3,
two `step 1`) as eight processes took 15.5 to 15.6 s; as one process 4.2 to 4.3 s (about 3.7 times less); as one
process with `--save-interval 3600` 3.9 to 4.3 s. Held-back writes save little over so few commands: the saving is
the process start, not the write. Command: `time python3 sim/simulator.py agent --civ norse_900ad --seed 3
--no-events --session F < commands.txt`, against the same lines fed one per process to the same command.

## Price solves shipped for the other interest-rate bands

`python3 sim/simulator.py openings` now also ships the opening's price solves at the other bands the market
rate is likely to meet (`sim/engine/shipped_rate_bands.py`). The build records the solves the opening makes
at the starting rate (`SolveRecorder`), replays each at every band from nil to twice the starting rate,
nearest the start first, never past `capital_market.RATE_CEILING_SHARE` times the start, capped at
`MAX_BANDS`. The range comes from a stepped game: its banded rate swung from near nil to above the start within
five years, and `bounded_rate` only caps the rate (there is no floor at `RATE_FLOOR_SHARE` in `market_rate`).
Each replay goes through `solved_prices_at_wages` itself with `band_interest_rate` values, so the keys are
exactly those a game computes; the reader (`solve_cache.cached_json`) is unchanged. A test
(`shipped_rate_bands`) ships a band, clears every cache and checks the table equals the cold solve and that
nothing was solved.

Measured: in a stepped Rome game most solve keys a year asks for (every one after the first year) are among
the replayed keys. A cold band costs about a fifth of a CPU second per band for the opening state (three
solves), against milliseconds shipped, which is a few percent of a year, not the doubling seen above: the rest
of a year that meets a new band is not these solves and is still open. Measure with the in-game solve keys
and a cold `ROME_CACHE_DIR` (`solve_cache.recording()` around `Sim.step()`, and `time.process_time()` around
`shipped_rate_bands.solve_other_bands`).

## Round 3: entry siting priced each tile once per demand; entry falls from a fifth of the year to under a tenth

Profile of the second warm stepped Rome year (`harness.sim()`, `step()`, then `cProfile` over the second `step()`,
sorted by `tottime` and `cumtime`; and the economy's phases wrapped in `time.process_time`). The profile put
`open_entrants` at under a third of the profiled year and, inside it, `location.entry_siting`'s `siting` at
about a quarter of the whole: it prices a recipe on every candidate tile for every unmet demand (about 1800
calls, about 28000 candidate tiles a year), and each candidate re-read wages, live input prices, the land rent,
the input haul (`location_inputs.input_haul_cost`, a weighted carriage sum per input), the tile's spare hours
(`people_by_trade`) and the headroom, none of which depends on the demand being sited. Phase shares of the
timed year, before: `clear_goods` about a fifth, `open_entrants` about a fifth, merchants' orders about a
sixth, labour clearing about a tenth, `close_agents` a tenth, `_lend` (merchants' credit requests) under a tenth.

Cut (both exact): one `entry_siting` call now reads each (recipe, tile) once (`location._tile_part`: variable
cost, yield, input haul, staffable runs, headroom) and only the output's carriage to the demand's anchor is
priced per demand (`location.assembled_cost`, the same arithmetic `cost_per_run` now calls). Nothing the
parts read changes while the plans are made (producers are added after all plans), and the supplies were
already kept per call. Proof: the sorted-key dump of `save_state` after three stepped Rome years is identical
before and after (md5 equal over three runs); `sim/tests/test_location_assembled_cost.py` keeps the parts
equal to `cost_per_run`; quick tier green.

Measured (CPU, shared machine at load 4 to 6, so the spread is real): `open_entrants` 1.47 s before, 0.79 s
after the first memo, 0.46 s after the second (one phase run each); a warm year (years 2 and 3 of three) 6.1 to
6.5 s before, 5.3 to 5.9 s after. Command: step three years of `harness.sim()` with `time.process_time` around
each `step()`; phases by wrapping the names `economy.py` imports.

Left: `clear_goods` and merchants (`_good_routes` is about three quarters of merchants' orders: its inner loop
over destinations is about 3.6 million iterations a year, each a lookup and a few additions; the break bound
already stops it at the profitable destinations, and a carriage-sorted walk changes tie order), then labour
switching (`_odds`, `_carry_out`), `close_agents` and credit requests, each flat. The year is still about
twice the target.

## Round 4: the unsold-stock search clears without building fills; the year is flat again

Phases of the second and third warm stepped Rome year (`harness.sim()`, `step()` three times, `time.process_time`
around the names `economy.py` imports and around `unsold_search.clear_with_search`; not under `cProfile`), as
shares of the year, now against round 3: `clear_goods` about 28 to 33 percent (round 3: about a fifth; it now holds
the in-year unsold-stock search, about a tenth of the year on its own, 0.73 to 0.83 s), merchants' orders about 16
percent (round 3: about a fifth; `_good_routes` is all of it, 2600 full searches a year, none with `source_ids`),
labour clearing about 12 percent (round 3: about a tenth, not edited here), `close_agents` about 9 to 10 percent,
`open_entrants` about 6 percent (down from a fifth, round 3's cut), `_lend` 3 to 4 percent, households' orders 3
percent. The year itself is 6.2 to 6.9 s CPU on this machine, so the unsold search (new since round 3) cancelled
most of what round 3 saved. Inside `clear_goods` the largest parts are `strategic_offers` (0.75 s, of which
`best_reservation` 0.57 s), the unsold search (0.52 s after the cuts below), `_produce_and_offer` (0.23 s) and
settlement (0.18 s).

Cuts, both exact:

- The search built `goods_market.Buyers` and the full clearing (buyer fills, seller fills, self-trade washing,
  unmet quantity) for each of its trials (about 15000 a year). It now builds one `Buyers` per market
  (`goods_market.clear(..., buyers)`), reads each trial's sold quantities with `goods_market.sold_by_seller` (the
  same crossing, rationing and seller filling, no fills) and builds the full clearing once, for the level it
  keeps. `_with_level` calls `Offer(...)` instead of `dataclasses.replace`. The sequence of trial levels is
  unchanged, so the kept level is the same.
- `strategic_offers` hands the sellers' unit costs to `clear_with_search`, which read them again to find the
  floors (about 5800 duplicate `unit_cost` calls a year; nothing changes the prices between the two).

Proof: the sorted-key dump of `save_state` (`saveload.state_text`, parsed and dumped with sorted keys) after three
stepped Rome years has the same md5 before and after each cut (c56b1eb987691b7218c2cf6dc131c8b8);
`sim/tests/test_sold_by_seller_exact.py` keeps `sold_by_seller` equal to the sell fills of `clear`, and `clear` with
a shared `Buyers` equal to `clear` alone; quick tier green. Saving: the search phase 0.73 to 0.83 s before,
0.52 to 0.53 s after (same wrapping, years 2 and 3), about 0.25 s a year, four percent of the year; whole-year CPU,
alternating a copy of the old tree (`git archive`) and the new one, three pairs, years 2 and 3 of each run: old
mean 6.61 s (6.10 to 7.11), new mean 6.20 s (5.83 to 6.74), about six percent, with a spread of the same order as
the saving, so read it as about 0.4 s plus or minus 0.3. Command: `time.process_time` around `unsold_search.clear_with_search`
over `Sim.step()` of `harness.sim()`.

Left, measured: merchants' route search (0.9 s a year, about 1400 destination iterations per call; sharing one
merchant's per-source result with another needs every changed area to sort after the break point, which a seventh of
areas changed per merchant makes rare, so it was not built); the bisection could start from last year's level but
the kept level would differ by up to the search precision, which is not exact; labour switching and `close_agents`
are flat (no function above a few percent). The bisection's cost is now the price solve of each trial; fewer trials
need a model change (a looser `SEARCH_PRECISION` or a bracket from last year's level).

## Round 5: a profile of a warm year; the allowed small readers cut, merchants are a fifth to a quarter of it

Profile of warm stepped Rome years (`harness.sim()`, `step()`, then `cProfile` over the next `step()`, sorted by
`tottime` and by `cumtime`). Flat again: by self time the dict `get` inside `merchants._good_routes` (about three
million calls a year) is first, then `_good_routes` itself; the first thing outside merchants is `fsum`/`sorted`
spread over many callers. Merchants' route search and credit requests together are about a fifth to a quarter of a
year (`_candidate_routes` alone about one second of CPU, `time.process_time` around it, not under `cProfile`); that
work was not touched here.

Cut, all exact: `country_figures.people_by_trade` adds each trade's bands tile by tile without building and sorting
a dict per tile (the labour package asks it about 160 times a year through `national_trade_population`);
`trade_data.fallback_trade_of` reads the fallback trade off the registry's flags without building every
`TradeSpec` (`trades.fallback_trade_of_registry`; it was called for every trade priced); `switching._carry_out`
takes and removes switchers with `map(min, ...)` and `map(sub, ...)`. Proof: the sorted-key dump of `state_text`
after three stepped Rome years has the same md5 before and after; `sim/tests/test_year_hot_path_shortcuts_exact.py`
keeps the first two equal to the plain computations.

Measured (CPU, mean of years 2 to 4 after the first, alternating a copy of the unchanged tree and the changed one,
two pairs): about 6.09 s before, about 5.92 s after, a little under three percent. Command: step four years of
`harness.sim()` with `time.process_time` around each `step()`.

Left, measured: `AgentEconomy.people_by_trade` is still summed about 160 times a year for the same workforce; a
cache needs every writer of the economy's workforce (the labour year, population scaling, `trim_to_expected_hours`)
to drop it, which was not built. `strata_observed.rank_key` and the labour `_odds` (a column-wise rewrite measured
no faster) are each about one percent.
