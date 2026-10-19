# A game year is still too slow to play a whole game

**Status:** partly - opening and per-year cost cut; a year is still several times the target

A playtester found a new Rome game took a quarter of an hour of hidden spin-up before the first prompt and
the better part of a minute per in-game year, so a whole game would take hours of stepping. The target is a
year in under two seconds.

## Where it stands

- **Opening.** A new game reads the shipped openings (`openings/`, `sim/engine/shipped_openings.py`): the
  spin-up record and the opening price solves of every civilisation, under the same cache keys the game
  computes. When they match, a new game opens in seconds. Any change to the economy or engine source makes
  them stale and the game silently computes its own opening again, so `python3 sim/simulator.py openings
  --prune` must be run before a build goes to players. It is also the only check that runs a full-length
  spin-up: the test suite shortens it (`ROME_SPIN_UP_YEARS`), and a crash in the full spin-up was found only
  by regenerating the openings.
- **A year.** Measure with a saved full-length game: `echo "step 5" | python3 sim/simulator.py play
  --session FILE` prints the time it took. A year costs about twice as much the first time the engine meets
  a new interest-rate band (a cold price solve) as on a warm disk cache (`.cache/price_solves`).
- **Per command.** Each CLI command loads the save, rebuilds the economy and saves again, a fixed cost paid
  once per typed command (`echo state | python3 sim/simulator.py play --session FILE`).

What was done, in order of size: the opening ships; the engine's in-game price solve starts from the same
solve at the starting rate and stops at a looser tolerance (`prices.ENGINE_SOLVE_TOLERANCE`); the seller's
reservation search prunes candidates and prices a sole offer without a full clear; the labour year reuses
odds across rounds and folds negligible choices (`entrants.NEGLIGIBLE_CHOICE_SHARE`,
`switching.NEGLIGIBLE_MOVE_SHARE`, `switching.PLAN_REUSE_TOLERANCE`); the carriage table is cached on disk
(`sim/economy/carriage_cache.py`); the saved economy record is exported only when the game is saved; a
multi-year step saves between years at most every `step_progress.SAVE_INTERVAL_SECONDS`; and many exact
memos and hoisted loops. The labelled approximations are each a `temporary_heuristic`
(`python3 sim/constants.py --burndown`).

Also done: the cyclic collector stays off while `play` builds and loads the game and runs its first command
(`cli_interactive.cmd_play`); a saved merchant's price and volume keys are split without a method lookup per
key (`record._split_keys`); and the market-area partition reads each tile's cost table once instead of
asking per pair (`market_areas.partition`). All three are exact: stepping one saved game before and after
gives a save whose parsed content is identical (compare with a sorted-key dump; the raw bytes differ only in
the order a set is written, which varies from process to process). Measure the fixed per-command cost as CPU
time of `echo state | python3 sim/simulator.py play --session COPY`, several runs, since wall time on a
shared machine swings by more than these changes save.

A profile of the load-and-save alone (`echo state | python3 -m cProfile ... play --session FILE`) shows the
cost spread over five things of similar size: importing the engine (module bodies and the data files read at
import), parsing the save (the C decoder, near its floor), rebuilding the economy from its record, loading
the tree and the opening price table (`engine/data.py` `load`), and encoding the save again (the C
encoder). None has a cheap exact cut left; the way under is one `play` process for many commands (below).

The idle-ask check in `seller_offers.strategic_offers` reads what a seller sells off the market's book
(`goods_market.price_and_sold`) instead of clearing the whole market with fills; a view caches each market area
by name and tile; merchants group their expectations with fewer lookups. All exact (same stepped save).
What is left in `clear_goods` is the sellers' reservation search (`seller_book`) and the price root-finds under
it, then book postings and settlement.

## Why the rest is hard

A warm profile of `step 3` from a saved game (`python3 -m cProfile ... play --session FILE`) is now flat:
the agent economy's year is interpreter overhead spread over thousands of producers, the sellers' price
searches, the labour market, closing and merchants, with no single function worth a large share. PyPy was
tried and was no faster (it also reads different cache keys).

## What it would take

- Ship the price tables of the starting techniques for every interest-rate band, so the cold years of the
  early game become warm (exact).
- Play in one `play` session rather than one process per command, which removes the load and save per
  command (exact).
- Fewer agents: one producer per recipe and market area where several now stand side by side (a model
  change).
- The market-clearing core in compiled code or arrays (adds a build step for players).

Related: 473 (the spin-up does not settle, so a longer spin-up cannot replace shipping it), 464.

## Partner civilisation records read once per game

A profile of one stepped year of a game with a partner outside the agent economy (the setup of the
`home_cargo_price` topic) found `load_civ` called thousands of times a year, nearly all to read one field of a
partner (`coin_standard`, `state_capacity`, `opening_stock`, `population`, tiles held, the route). The `Sim` now
keeps each loaded partner for the game (`Sim.partner_civ`, `sim/engine/partner_civs.py`) and the per-year
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
