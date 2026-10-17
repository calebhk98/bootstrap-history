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
