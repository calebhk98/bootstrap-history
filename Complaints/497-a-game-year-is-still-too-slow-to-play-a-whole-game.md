# A game year is still too slow to play a whole game

**Status:** partly - opening and per-year cost cut; a year is still several times the target, and has not been re-profiled since the goods market and seller pricing were replaced by the Eurace rules (logit clearing in `goods_market_logit.py`, vectorised with numpy; `price_setting.best_price`)

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
What is left in `clear_goods` is the sellers' price choice (`seller_offers.strategic_offers` calling `price_setting.best_price`; the
earlier book search is gone) and the price root-finds under it, then book postings and settlement.

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

Left, measured by `cProfile` of a warm year (before the Eurace seller pricing, whose search `best_reservation` is deleted): `strategic_offers` was that search (about 0.5 s of a profiled 15 s
year) and unit costs; `clear` is mostly `solve_price` and per-market setup, over half of its calls trade nothing;
`close_agents` is `producers_close.close_year` per producer (expectations and expected run), flat; settlement posting
and `producers.plan`/`offers` are outside the files this round owned.

## Round 7: country figures reused while their inputs are unchanged; producers share reads

Branch `year-speed-country-figures-and-producer-reads`. All exact: the sorted-key dump of the save after a warm-up
and three warm stepped Rome years (`harness.sim()`) is identical before and after (cmp of the two dumps, twice).

- `country_figures.prices` (24 calls a year, 19 of them the same country asked by `material_cost`) and
  `traded_volumes` keep their answer with copies of the prices, weights and volumes they read, and reuse it only
  while the live dicts compare equal (a C-speed dict comparison, so any change between calls, in place or not,
  rescans). Measured with `time.process_time` around the function over three warm years: `prices` 0.525 s a year
  before, 0.050 after; `traded_volumes` 0.028 before, 0.008 after. Test: `test_country_prices_memo` (random markets,
  random changes between calls, against the unmemoised `scan_prices` / `scan_volumes`).
- `producers.next_expectations` reads the input prices from the `live_inputs` its caller passes instead of reading
  them again; `producers.offers` hands its expected output prices to `shortfall_at_working_scale` and
  `share_that_pays`; `producers_close._expected_run` reads a market price only for an output with no expectation;
  `YearView.present_prices_at` builds the market keys of a recipe's goods and trades once per tile
  (`live_input_prices_at`, `live_wages_at`). Test: `test_producers_shared_reads` (random recipes, producers and
  markets, against the calls that read for themselves). These four are inside the noise of a whole year: `plan`
  0.143 to 0.161, `offers` 0.078 to 0.079, `close_year` 0.265 to 0.244 s a year.

CPU per warm year (`time.process_time` around `Sim.step()` after one warm-up, the machine shared with other
sessions, load average 4 on 4 cores, so only differences above half a second mean anything): old 5.78, 7.18, 7.57 and
6.39, 6.45, 5.72; new 5.55, 6.09, 5.98 and 6.10, 6.48, 5.87. By the component timers the change is about 0.5 s a year.

Profile of a warm year after this round (cProfile, inflated about 2.3 times): `clear_goods` 3.4 of 17.3 s, of
which merchants 2.3; `clear_labour` 3.1; `close_agents` 2.0; `open_entrants` 1.9; `_lend` 1.1, nearly all
`merchants_credit.credit_request` running a second full route search for the two merchants that borrow (the
second search sees post-clearing prices and so misses the memo of the first); `wear_and_spoilage` 0.5. In the
files this round owned nothing above about 0.3 s of real time is left: `settlement._settle` with `Book.post`
(about 0.27 s; already tight, per-call overhead), the book-search function `best_reservation` since deleted (about 0.33 s; the book clearing and the
pruned search), `producers.plan` (0.15 s), `close_year` (0.25 s). Not taken: lazy unit costs for crowds in
`strategic_offers` (the unsold search needs a crowd's cost for its floor in every market that reaches it, and a
market with nothing unsold is a third of the cost at most, under 0.05 s).

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

## Round 8: the labour year's reads (after the fetch-cost search, bonded room and per-use rent merged)

Branch `year-speed-after-merges`. All exact: `python3 -m sim.tests.fingerprint`'s `state_of` / `digest` of a `harness.sim()`
game after 4 and after 12 stepped years is the same hash before and after (the full `--quick` fingerprint is four
hundred game years, far over twenty minutes at this speed, so it was not run; the quick tier and the topics named below
were).

Profile (cProfile, three Rome years after one warm-up on `harness.sim()`; cProfile inflates about 2.5 times). Of the
agent economy's year: labour clearing 47 s of 93 (the market core 43: `clear_all` 30, `form_trades` 7, `switch_trades` 3.5),
goods clearing 11, closing 6.6, entry 4.7, credit 4.3, producers' planning about 2 (inside close/offers). Own time, top of
the list: `dict.get` 9, `labour_supply.sold` 5.5 (3.3 million calls), `bonded_room.buyers_in` 3.1 (every call scanned all
bids), `merchants._good_routes` 2.8, `import_cost._fills` and `hours_at` 4, `cheapest_carriage` 1.8, `share_at` 1.8 (every
market scanned all offers), `plot_hours_kept` chain 3.6. A late year (eleven warm-ups) has the same shape with labour
clearing a quarter, merchants' route search (orders and credit requests, 79 percent memo misses because each merchant's
expectations differ) a quarter, `_lend` 8 of 75.

Cuts, each beside a copy of the old path on random built inputs (`sim/tests/test_year_speed_labour_reads.py`):
- `ImportCosts`: the spare hours of a source and the sum over a list of sources are kept for the year (the bisection asked
  the same list every step); `hours_at`, `everyone` read the memo once.
- `HourSupply.sold_hours_schedule` does the leisure test once per offer and inlines `leisure_share`; `shares()` groups the
  offers by market once instead of scanning all of them per market; `household_hours_year.plot_schedule` replaces a
  `functools.partial` over `plot_hours_kept` with a closure whose wage-free part is done once.
- Bonded purchase: `bonded_room.hours_by_market` groups the bids once per year (`buyers_in` scanned every bid per call);
  `bonded_worth.carriage_from` is one search per origin instead of one per (origin, destination); both live in the memo
  `form_trades` hands to `formation_bonded.buy`.

Measured (CPU seconds of `Sim.step()` on `harness.sim()`, two processes at once on four cores, old tree and new side by
side, `python3 /tmp/.../yspeed_prof.py ROOT time 12`): second to fourth year 13.7, 10.9, 11.2 before and 9.9, 8.8, 9.8 after;
tenth to twelfth year 10.2, 9.7, 10.0 before and 9.3, 9.5, 9.4 after. About fifteen percent early, about five late.

Left: the fetch-cost search itself (`ImportCosts.wage`: each candidate source list is evaluated at its own wage, so the
share schedules are computed afresh, about 1.1 million `hours_at` misses in three years; a binary search over the
sorted sources would cut it but relies on the schedule being exactly monotone, which rounding does not promise); merchants'
route searches for orders and credit requests (per-merchant expectations make the shared route memo miss); `switching`
(`_carry_out`, `_odds`); `land_bid.owners_of_sellers` scans every producer per (good, tile).

## Round 9: the opening solved with households' plans (branch `opening-plans-speed`)

An uncached Rome opening had gone from tens of seconds to several minutes when `open_economy` began solving to a fixed
point with the households' first-year choices (`opening_plans.settle`, `_by_margin`). Measured with a script that wraps
`opening._open` and `open_economy` around `harness.sim(civ="rome_100ad")` with `ROME_CACHE_DIR` on an empty directory:

- Solves: the replacement-free first solve, the metal-replacement solve, the settle passes and the bisection on the
  households ranked by what an hour hired gains them make 16 full solves of the opening in all (the same 16 after the
  change; none repeats a plan, so remembering solves by plan was tried and dropped). Each took about 16 s (a few 4 to 7 s
  where a price solve was cached).
- Where one solve spends it (cProfile of one solve): about nine tenths is `_settle_income`, the income fixed point
  (`opening_income.settled_income_per_head`), which asks `_final_demand` (every cohort's bids) once per pass. It runs its
  whole pass bound every time: income falls by about one percent a pass and never reaches the tolerance, so the result
  is the income after that many passes (a separate issue: the bound, not a fixed point, sets the opening's income).
  Because the answer is where the iteration stops, starting a solve from the last one's income would change the result,
  so it was not done.
- The cut: the basket, the priced needs and the store weights of a cohort do not depend on its income, so
  `opening_bid_memory.BidMemory` holds them for the passes of one `_settle_income` (exact: the same calls, made once).
  Uncached Rome opening 231 s before, 108 s after (two runs, one machine, `prof.py`-style wrapper); a solve about 7 s.
- Exactness: the cohorts' plans, `opening_demand`, `opening_basket` and every price in the opening memory are equal
  (`==`, not within tolerance) before and after on the Rome opening. Test: `test_opening_plans_speed` (the same bids at
  several incomes with and without the memory; a small economy whose choice settles, and one whose choice is made to
  cycle so the bisection runs, give equal plans, quantities, prices and producers with and without it).
- Not done: bisecting on the ranking with the solve's prices held (it re-solves less, but the producers' sizing and
  prices move with hiring, so the result would differ from the fixed point); the per-pass work left is `goods_orders`
  itself, flat in the profile.

## Round 10: the opening's income is a root find, not a pass-bound iteration (branch `opening-income-fixed-point`)

`opening_income.settled_income_per_head` iterated income into demand from the full-employment ceiling and ran its whole
pass bound every time (Round 9). Measured with a scratch wrapper around it on the Rome opening: households spend all of a
low income (demand over income is one less the margin their bids leave unspent), and above a kink they save a surplus
(a savings target on income above their floors) that nothing in `_final_demand` spends, so demand over income falls
from there up. Demand is therefore income below the kink (every income there is a fixed point) and below income above
it: the map slid down the saved share a pass and stopped where the bound did.

The solve is now a root find on the income left unspent (the largest income at which households save nothing net;
docstring of `opening_income.py`), by a line through the lowest incomes that still save, bisection where the line leaves
the bracket. No positive root, or no close, is a `Refusal` (`no_positive_income_fixed_point`, `income_root_not_found`),
raised by the opening as `OpeningIncomeRefused`. Rule tests in `test_opening_consistency`.

Measured, uncached Rome opening (`ROME_CACHE_DIR` on an empty directory, one machine, two runs of a wrapper, 32 and 31 income
solves): income passes 1649 before, 466 after; opening 269 s before, 171 s after. Passes per solve were 60 before, 11 to 23 after.
