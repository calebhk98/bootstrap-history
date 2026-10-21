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

## Rounds done (full text and measurements in `Complaints/reports/497-history.md`)

- Partner civilisation records read once per game (`partner_civ`; `load_civ` was called thousands of times a year).
- Route graph compiled once per set of modes and improvements; defender search remembered.
- Carrier models (`engine/foreign_routes.py`) kept between price changes.
- Merchant route search: trip years kept per pair, tighter destination loop.
- Merchants with no cash search only for the stock they hold; book totals read without per-agent sorting.
- Round 2: route search skips what cannot pay; the year became flat, merchants its largest part.
- One process for many commands (`agent` and `play` read commands from stdin; a save after each is skipped).
- Price solves shipped for the other interest-rate bands (`sim/engine/shipped_rate_bands.py`, written by `openings`).
- Round 3: entry siting priced each tile once per demand; entry fell from a fifth of the year to under a tenth.
- Round 4: the unsold-stock search clears without building fills; the year is flat again.
- Round 5: a warm-year profile; the allowed small readers were cut; merchants are a fifth to a quarter of the year.

## Round 6: the unsold search ends at a shared floor without its trials; buyers prepared on demand

Branch `year-speed-clearing`. All exact: the sorted-key dump of the save after a warm-up and three or four warm
stepped Rome years (`harness.sim()`) is byte-identical before and after.

- `unsold_search.search_asks`: when every searched ask has one floor and the buyers want, at that floor's effective
  price, less than the searched offers hold (each of a distinct seller and tile), every higher level leaves one of
  them unsold, so the bisection ends at the floor and its trials are skipped
  (`unsold_search.unsold_above_the_floor`). Measured: in a warm year about 1300 markets search, the condition holds in
  all but a few dozen, and it removes about 16000 of 16700 trials. Test: `test_unsold_search_floor_shortcut` (random
  books, against a copy of the bisection without the shortcut).
- `seller_offers.strategic_offers` merges the bids and prepares the buyers when a seller first searches, not before
  (about two thirds of markets have no searching seller); `Buyers.schedule` is built when a market with offers reads it;
  a market with no searchable floors skips the unsold check. Tests: `test_strategic_offers_lazy_buyers`,
  `test_buyers_schedule_lazy`.

Measured (CPU per warm year, years after one warm-up, alternating an exported copy of the old tree and this one, same
machine): old 6.57, 6.46, 6.37; new 6.25, 6.01, 5.99, about 0.4 s or six percent. Command: `time.process_time` around
`Sim.step()` of `harness.sim()`.

Left, measured by `cProfile` of a warm year: `strategic_offers` is `best_reservation` (about 0.5 s of a profiled 15 s
year) and unit costs; `clear` is mostly `solve_price` and per-market setup, over half of its calls trade nothing;
`close_agents` is `producers_close.close_year` per producer (expectations and expected run), flat; settlement posting
and `producers.plan`/`offers` are outside the files this round owned.

## numpy tried, not adopted (owner asked for a measurement, 2026-10-21)

Branch `numpy-speed-probe` (kept, not merged) vectorises the merchants' route search, the largest single phase of a
warm Rome year, over a cached carriage-cost matrix per good; `sim/tests/test_merchant_routes_array.py` holds it equal
to the scalar search exactly. The phase got only about a tenth faster: the scalar search is already pruned and
memoised, and what is left is building output rows and numpy's per-call cost on small arrays. Whole warm years on the
old and new trees, alternated, are inside each other's noise with identical price digests. Measure: step
`harness.sim()` once, then `time.process_time` around each further `step()`, on a worktree of each branch.

What would let arrays pay: batching across goods and distinct price vectors in one call a year, which means
reworking the merchants' sequential route commitment (each merchant's commits change what the next sees), and
array-shaped data for `clear_goods`, `clear_labour`, `close_agents` and `open_entrants`. That is the model change of
option 1 or 3 above, not a translation. A mod-swappable kernel for such a change is Complaint 661.
