# Numba port of the economy's year

**Status:** stopped at about 3.5 to 3.7 s a warm Rome year (see Measured); the branch `speed-year-step-and-openings` goes
to a PR at that point by the owner's decision. What is left, and the redesign the one-second goal needs, is carried by
Complaint 968; the unticked items below are its starting list.

**Measured** (`year-time --session SAVE --years 2 --reload-check` on the shared Rome save; seconds of the two years):
- before the port: about 23 and 20
- items 1, 2 and 5 in part: about 17 and 13.5, reproducible after a reload
- with labour's heads and switching, entry's practice and the national prices: about 15 and 11 (machine loaded)
- with settlement, the ledger and the producers' read caches: about 13 and 9
- with the labour tail, the urban ceilings and the partner countries' kept figures: about 12 and 8
- with the respend rounds in one kernel: about 11 and 7.5
- after items 1 to 9 (opening, year arrays, close, entry, merchants, labour, goods): warm years about 3.5 to 4.5, typically 3.7

**Goal.** A Rome year under one second (three at most; a game is five hundred years), with the game unchanged in its
rules and reproducible: the same save stepped on the same machine gives the same game, straight or saved and loaded in
between. Matching the old Python bit for bit is not required; a ported phase may differ from it in the last digits
of its floats.

**Why numba.** A kernel pilot (Complaint 497, round 11 and after) ported the hiring rounds to JAX, numba, Rust and
Cython. Every compiled one was tens of times faster than CPython and exact; JAX was a few times faster; a GPU does not
pay at this size (a few thousand producers, a long chain of small dependent steps). numba was chosen because agents on
any platform can edit and run a kernel with nothing but `pip install numba`: it carries its own compiler, so there is no
binary to build, ship or merge.

## How a phase is ported

- **Kernels go through `sim/jit.py`** (`from sim.jit import njit`): nopython, no fastmath, no parallel loops, cached.
  `ROME_NO_JIT=1` runs the same code as plain Python.
- **Pack, run, unpack.** A phase packs the records it reads into numpy arrays when it starts (string ids become integer
  positions in sorted id order), runs one or a few kernels over every market or agent at once, and writes the answer
  back into the records. The saved record format does not change, so saves made before the port still load.
- **Batch across markets.** A kernel takes all the year's markets (or agents) of a phase, not one, and loops inside.
- **Order.** Every loop runs in a fixed order (sorted ids); no set iteration and no dict order decides a sum. Python's
  `sum()` of floats is compensated summation on 3.12 and later; a kernel uses a plain left-to-right sum, so a phase's
  figures move in the last digits once, deliberately.
- **Tests.** Each ported rule keeps a copy of its old Python path in its test, run beside the kernel on random built
  inputs, agreeing within a stated relative tolerance (a kernel sums in a different order). Rule tests that called the
  old functions still call the phase's public functions.
- **Checks before a phase is ticked.** The quick tier is green, also with `ROME_NO_JIT=1` (the plain-Python path) and with
  `NUMBA_BOUNDSCHECK=1` and a fresh `NUMBA_CACHE_DIR` (numba does not check array bounds, so a write past an array's end
  goes unseen in a compiled run); a new game opens and steps on an empty cache (`ROME_CACHE_DIR` on an empty
  directory, `agent --civ england_1300` with `state` and one `step`: the checks above all load a save, and a new game's
  spin-up runs code no save reaches); `year-time --reload-check` on the shared Rome save is
  reproducible; the game after two years is compared with the one before the port (`--keep` and a field-by-field
  compare: which modules moved and by how much, explained in the item); the phase's measured share of the year is
  written in its item with the command.

Measure: `python3 sim/simulator.py year-time --session SAVE --years 2 --reload-check` (a saved Rome game; the save is
copied, never written). A phase's share: `cProfile` of `agent --session COPY` with one `step`, the callees of
`Economy._run_year`.

## Items

### 0. Groundwork
- [x] `sim/jit.py`: the one `njit`, with the plain-Python fallback (`test_jit`).
- [x] numba in `requirements.txt`.
- [x] `simulator.py year-time`: years' seconds, a digest of the game after them, `--reload-check`, `--keep`.
- [x] The game reproducible across a save and load before any port (`year-time --reload-check` found two causes).
    - [x] Han's rich stratum differed in its last digits after a load: `country_figures.output_value_and_unpriced`
          summed over the producers in their live order; now `math.fsum` (`test_country_output_value_order`)
    - [x] `industry_opening_rate` wrote an int on one path and a float on the other; now always a float
          (`test_industry_experience_rules`)
    - [x] `year-time --reload-check` passes on the shared Rome save

### 0b. Year arrays shared by every phase
Packing a phase's records on entry costs about as much as the phase's own work once the arithmetic is compiled: a
phase reads the fields of every producer and cohort through Python objects. The year arrays are built once a year: the
producers', cohorts' and market memory's numeric fields as columns indexed by row, with the id-to-row maps. They are
kept in step when producers enter or exit, read by every kernel, and written back to the records only where a phase
changes a field. The saved record format does not change.
- [x] `sim/economy/year_arrays.py`: producers (recipe, tile, runs, capacity, crew, expectations by recipe good), cohorts
      (tile, people, cash, basket), market memory (prices, wages, quotes by good or trade and area), the recipes' input and
      output matrices
- [x] built in `Economy._run_year`, refreshed by `sync` (replaced rows re-read; a rebuild when producers enter or leave),
      checked against the records in `test_year_arrays`
- [ ] the first phase moved onto it: the year's close
    - [x] the producers' close as one kernel (`close_kernel.py`, `close_pack.py`, `close_run.py`, `year_close_producers.py`;
          `test_year_speed_close` beside the old close on random economies, and on every producer of a real Rome close)
    - [ ] the households' close and the equity built for it (`households_close`, `equity.producer_worths`, `credit_view.equity`):
          the households' own part is small (312 cohorts); the cost is the producers' net worths (`equity._built_worths`, one
          `plant_value_per_run` per recipe and tile and one `inventory_value` per producer), built once per view
    - [x] the close hands its producer columns to entry (`year_arrays_closed.columns_after_close`, from the kernel's answer;
          `test_year_speed_close_arrays`): the `sync` in `open_entrants` finds no row to read again (about 0.09 cProfile s of a warm year)
    - [x] the close's pack reads rows as lists and one currency per area (`close_pack.pack`)
    - [ ] the per-producer tail: dividends (`spread`, `transfer_many`), `write_off`, loan asks
- [ ] every other ported phase reads from it instead of packing its own

### 1. Labour clearing (`sim/labour/market/`)
- [ ] Market clearing (`clearing.clear_all`, `clear_one`, `hire_through_rounds`, `import_cost`)
    - [x] every market prepared, then all their hiring rounds in one kernel (`hiring_kernel.py`, `applications.hire_markets`),
          then finished (`test_year_speed_labour_hiring`, the old rounds in `labour_hiring_reference.py`)
    - [x] the hours-sold schedule over a matrix of wages (`sim/economy/labour_supply_kernel.py`; `test_year_speed_labour_sold_hours`)
    - [x] the fetched-hands search and the wage searches for every market at once (`clearing_kernel.market_heads`,
          `clearing_arrays.py`; `test_year_speed_labour_heads` against `clearing._plain_head`; the plain path kept for a
          mod's fetch search or an unpacked schedule)
    - [x] the per-market tail (`clearing_tail_kernel.py`, `clearing_tail.py`: employers left by the wage, retention,
          ceilings, hiring arrays, the wage paid, poaching and the asks; `test_year_speed_labour_tail`)
    - [x] `pack_heads`' bid sums over arrays (`np.add.at`, `np.maximum.at` in bid order); the employer columns by `attrgetter`;
          `clearing._kernel_head` and `_prepare`'s unused `head` argument removed (the heads test converts the kernel's row itself)
    - [x] the carriage search of every origin in one pass over a cost matrix (`carriage.carriage_table`, used by
          `YearInputs.carriage_from`; `test_year_speed_labour_carriage`): about 0.015 s to 0.004 s of a year
    - [ ] what is left of the clearing is the write-back of one `LabourClearing` and its state entries per market (the saved
          record format) and `import_cost.reach`, one route search per area
- [ ] Trade switching (`switching.switch_trades`, `_odds`, `_planned_moves`)
    - [x] the per-band logit (`switching_kernel.band_shares`; `test_year_speed_labour_switching`)
    - [x] targets, gains, costs, plan reuse and moves for every source of an area (`switching_kernel.plan_area`,
          `take_moves`; `test_year_speed_labour_plans`)
    - [x] the carry-out and the refusal path (`switching_kernel.enrol_groups`)
    - [x] the round's moves collected in one kernel (`switching_kernel.collect_moves`) instead of numpy glue in `_planned_moves`
          (`test_year_speed_labour_plans`)
    - [x] the carry-out's grouping of moves in one kernel (`switching_kernel.group_moves`; `test_year_speed_labour_groups`)
    - [ ] expected incomes at graduation (`expected_income`, `income_at_graduation`): still one Python call per destination and
          round; `graduates_coming` is one `math.sumprod` per cohort. A kernel needs the area's clearings and trainees packed once
    - [x] migration: `migration.move_shares` without dictionaries (`test_year_speed_labour_finish`); `migrate` itself is still
          Python per origin, trade and route
- [x] Trade formation (`formation.form_trades`): early return where no origin sells, origin asks kept for the year; the
      carriage search is made once per origin for the year and shared with the import cap (`YearInputs.carriage_from`), the
      routes' destinations are indexed once; the per-market purchase is Python
- [x] Labour path reads: the priced basket of a cohort kept per (tile, hearth, hired work, milled grains) until the market memory is
      next written to (`household_work_year.priced_basket`, `priced_reads.kept_reads`); a trade's wage on a tile kept the same
      way (`kept_wages`, `api.trade_wage_at`, which `labour_wages.wage_signature` reads 28 times a year)
- [x] Checks: reproducible, compared, share measured. `year-time --years 2 --reload-check` on the shared Rome save: digest the
      same after a reload; the game after two years against the base's moves in the last digits only (`save_compare.py`).
      Share: `clear_labour` is about 1.8 of 22 cProfile seconds of the second year (`prof_second.py`, callees of
      `Economy._run_year`), 1.9 before this step; the labour year is about a twelfth of a Rome year, so the rest of the
      time is in the other items

### 2. Goods clearing (`sim/economy/goods_market*.py`, `unsold_search.py`, `seller_offers.py`, `price_setting.py`, `demand_search.py`, `market_quote.py`)
- [x] The market clear: the logit allocation, rationing and redirect rounds, buyers' requests and trades
      (`goods_market_kernels.py`; `test_goods_clearing_kernels`)
- [x] The unsold-stock search and the sold-out raise, each bisection in one kernel
- [x] Sellers' pricing: every searching seller of a market priced in one call (`price_setting_kernel.py`)
- [x] A market's bids packed into the kernels' arrays by one kernel (`goods_market_kernels.pack_demand`,
      `goods_market_demand.DemandArrays`), not through the per-bid groups of `DemandSchedule`, which only the crossing and
      the flood price still build (`test_year_speed_demand_arrays`)
- [x] A seller's unit cost and input share read once per market (`seller_offers.cost_figures`, `UnitCosts`); the pairing's
      tuples built with `attrgetter`; fills built without a list per bid
- [x] A good's markets cleared, then settled together: `settlement.settle_goods_many` (`settlement_batch.py`, kernel
      `settlement_batch_kernel.settle_markets`: purses and stocks carried from market to market, the book posted once per good;
      `test_year_speed_settlement_batch`). Second-year wall time of the settlement stage about 0.27 s to 0.14 s
      (a `perf_counter` wrapper around `settle_goods_many` in `year_goods.clear_goods`)
- [x] The costs of every producer's outputs over the year arrays, once a year (`year_arrays_costs.OfferCosts`: cost,
      input share, expected price, share of the plant a run pays; `test_year_speed_goods_markets`)
- [x] A good's markets with offers re-priced, searched and cleared in one kernel call (`goods_year_kernel.decide_markets`,
      packed by `goods_year_batch.clear_markets`; called from `year_goods.clear_goods` when it is given the year arrays):
      the sellers' re-pricing, the floors, the salvage floors, the search down and the sold-out raise, each rule as in
      `seller_offers.strategic_offers` and `unsold_search.clear_with_search`; the market is then cleared once with the answer.
      On the Rome save every batched market of a year ends with the old path's reservations
      (`python3 sim/simulator.py year-time` digest differs only in float noise). Markets with a book edge selling in them
      or a good that is not portable (ground) still go through the old path
- [x] The turn's producers' offers (`year_goods_offers.offer_reservations`): holding reservation and the distress by the cash
      still to raise, one kernel call per good; a producer with an output that has no expected price goes through `producers.offers`
- [ ] What is left: the second allocation inside the final `goods_market.clear` and the fills and pairing it builds per market
      (the kernel could return its last allocation); `_produce_and_offer`'s `producers.produce` and `book.move_many`
      (sim/book.py), `_remember_markets` and the per-market notes after the clear (`note_bids`, `note_offers`,
      `offers_left`, `note_clearing`); the memory arrays are read again before the clear (`year_arrays_costs.refreshed`: the
      wages move after the year start)
- [ ] Checks: reproducible, compared, share measured (see item 4)

### 3. Households' respend (`goods_respend.py`, `goods_respend_year.py`)
- [x] shared across households: the need of each good, the area each good is bought in, the cheapest asks, the priced
      needs of one basket at one set of asks (`goods_respend.priced_needs`)
- [x] rounds over every rationed cohort and market in one kernel (`goods_respend_kernel.respend_rounds`; the baskets
      flattened and the records packed by `goods_respend_pack.py`, the answer written back by `goods_respend_unpack.py`):
      the money each buyer was rationed of, the bids' pricing (`goods_respend_basket_kernel`: `need_basket.priced_need`,
      `price_ceilings`, `respend_bids`), each round's clears of the touched markets and their settlement against the
      purses and stocks as they stand, and the round stop rule. A round's result carries no fills and no pairing (only
      households bid in these rounds); the book is posted once per good and the ledger noted once per respend
      (`YearLedger.note_summed_sales`). `test_year_speed_respend` runs the old rounds (`sim/tests/respend_reference.py`)
      beside it
- [x] Checks: reproducible after a reload; compared with the old rounds on the same base (last digits, then a diverging
      game: the kernel sums left to right, a purse or stock is start less out plus in per round as the book makes it, and
      a buyer left a quantity at rounding noise goes on to bid or not); share measured: respend 2.4 of 19.8 cProfile seconds
      of the second year before, 0.5 of 17.9 after (`python3 <scratchpad>/prof_second.py SAVE OUT.prof`, callees of
      `year_goods.clear_goods`; pack 0.27, kernel 0.06, write back 0.16)

### 4. Settlement and the year's ledger (`settlement.py`, `year_ledger.py`, `sim/book.py`)
- [x] goods and labour settlement of a market in one kernel over its pairs (`settlement_kernel.settle_pairs`): stock and
      purse limits, the walk, every per-agent sum the ledger and the buyers' maps need; posted summed per agent
      (`Book.post_settled`, the same entries, totals and edge records as posting every pair); the Transfers and GoodsMoves
      are rebuilt only for a caller that asks (`Settlement.postings`) (`test_year_speed_settlement`, the old per-pair
      settlement kept in `sim/tests/settlement_reference.py`)
- [x] the ledger's notes of a settlement from its per-agent sums (`YearLedger.note_settlement`, `note_labour_settled`),
      plant purchases included
- [x] producers of one good book their output and the state's tax in kind together (`year_goods._produce_and_offer`)
- [ ] the pair arrays still come from the clearing's `Pairing` tuples; packing a settlement's agents and keys is Python
      per bid and offer used
- [ ] Checks: reproducible, compared, share measured

**Measured (items 2 to 4, the Rome save, second year, cProfile seconds, which inflate real time about two and a half
times; `python3 <scratchpad>/prof_second.py SAVE OUT.prof`, callees of `Economy._run_year`):** `year_goods.clear_goods`
10.7 of a year of 34.8 before, 5.5 of 25.7 after (the merged branch also moved other phases). Inside it: respend 3.8 to
2.6, settlement 3.4 to 0.9, the ledger's notes 1.3 to 0.1, `clear_with_search` 1.3 to 0.8, `strategic_offers` 0.56 to
0.38, producing and offering 1.2 to 0.6. `year-time --years 2` on the same base with and without these changes: seconds of
the two years 15.96 and 12.34 before, 15.43 and 11.11 after (a shared four-core machine, so a second or so of noise).
The game moves in the last digits only (the kernel sums left to right, the book is posted summed), and then diverges as
any rounding change does; the digest is the same on two runs and after a reload.

### 5. Merchants (`merchants*.py`, `lending.merchant_requests`, `carriage_hours.py`)
- [x] route search for orders and credit requests over a carriage-cost matrix per good (`merchants_kernel.py`,
      `merchants_search.py`; `test_merchant_good_routes_exact`); the game unchanged by it
- [x] orders and credit requests: one search kernel over every good and the commitment loops in kernels
      (`merchants_book.py`, `merchants_book_kernel.py`, `merchants_plan.py`; `test_year_speed_merchants`); the game unchanged
      (same digest as the base); `merchant_orders` 0.72 to 0.13 and `merchant_requests` 0.38 to 0.09 of a warm year's profile
- [x] close: expectations updated over arrays (`merchants_news.py`): 0.19 to 0.04
- [ ] dispatch: callbacks answered once a pair (0.32 to 0.22); the per-haul loop is still Python (crew, dues, fleet, purse)
- [x] the carriers' wage scale (`carriage_hours.wage_scale`) is 0.01 of a warm year; the cost was the first year's searches
- [ ] Checks: reproducible, compared, share measured

### 6. Entry and closing (`entry*.py`, `location.py`, `practice.py`, `producers_close.py`, `firm_year.py`, `households_close.py`)
- [ ] entry plans and siting
    - [x] practice means over packed crews (`practice.py` kernels; `test_year_speed_practice_kernel`); each recipe's
          entrant crew read once per entry year (`entry_practice.entrant_crew`)
    - [x] reads kept per view and per siting call (the memory's wage, price on offer and price kind by tile, the input haul and
          hands of a recipe and tile, one planned recipe per hours; `test_year_speed_producer_reads`); the game unchanged by them
    - [x] costing and siting over the year arrays (`entry_tables.py`, `entry_kernels.py`; `test_year_speed_entry_arrays`): the
          cost of a recipe on a tile (`recipes_by_cost`, the unfilled demand at that cost), the returns of every unmet market's
          recipes, the output makers could reach and the idle output, and the tile a newcomer is sited on, read the year's
          prices, wages, recipe matrices and carriage as arrays; the plans on the shared Rome save are the old plans (every
          plan, runs equal to 1e-6). The rules stay in `entry.py`, `entry_margin.py`, `entry_trial.py`, `location.py`
          with the costing behind a `costs` argument (the old Python path stays as the reference when it is None)
    - [x] the apply loop reads each recipe's crews once (`open_entrants`), `restake_owners` reads the live prices and wages once per
          recipe and tile, and the exits of a close end their term loans in one pass over the contracts (`producer_exit.ExitBatch`,
          `Contracts.default_many`; `close_idle_producers` from about 0.13 to a few hundredths of a cProfile second)
    - [ ] what is left of entry is Python per request: the greedy loops of `entry_plans`, `margin_entry_plans` and
          `trial_entry_plans` (a kernel call per unfilled-demand costing and per siting, the sized runs, the bids' schedules),
          the apply loop in `open_entrants` (a producer, a stake and a loan each; about 0.06 cProfile s)
- [ ] producers' and firms' close of the year
    - [x] pooled practice, input prices and wages read once per recipe and tile and handed to each producer's close
    - [x] `producers_close.close_year`, `next_expectations`, `_pledgeable`, `firm_year.settle_year` in one kernel (item 0b)
- [ ] households' close (the offered prices read once per good and tile, `households_close._priced_needs`; the rest is Python)
- [ ] Checks: reproducible, compared, share measured

### 7. The rest of the economy's year
- [x] `live_wages_at` and `present_prices_at` read once per trade and tile until the memory is written to (`YearView.wages_at`),
      land sellers indexed once a year (`land_bid.owners_of_sellers`): `firm_land_bids` from about 0.3 s to 0.02 s of a year
- [ ] producers' plans (`producers.plan`), cohorts' orders (`year_goods.cohort_orders`), produce and offer
    - [x] every producer's plan in one kernel over the year arrays (`plan_kernel.plan_rows`, packed and unpacked by
          `plan_year.plans_of`; `test_year_speed_plans` against `producers.plan` on random economies). A recipe with tool
          fallbacks or wear, or a crew whose practice stretches the recipe, still goes through `producers.plan`
    - [ ] cohorts' orders, produce and offer
- [ ] hour supply, outside option, labour context, land bids and leases, wear and spoilage, the outcome
    - [x] `bondage_hours.place_held` indexes bids and offers once (`test_year_speed_bondage`)
    - [x] `wear_and_spoilage` reads only the goods that spoil or wear (`test_year_speed_wear`)
    - [x] the memory arrays are kept until the memory is next written to (`MemoryArrays.is_current`; `market_memory.written_stamp`)
          instead of read again by each `sync` and `refreshed`
    - [x] land leases read the loans' pledges once (`titles.pledges_by_title`; `test_year_speed_titles`)
    - [x] `_hour_supply`: priced needs and the prices on a tile kept per read (`priced_reads.kept_need_prices`, shared by
          `household_work_year` and `plot_schedules`), the cheapest service price kept per tile; `HourSupply.settle` without
          `dataclasses.replace`. Wall time of `_hour_supply` in the second year about 0.057 s to 0.035 s (a `perf_counter` wrapper)
    - [ ] left: `household_work_year.plans` (one `cohort_plan` per cohort, about 0.02 s),
          `year_accounts.build`, `land_market.settle_year`, `outside_option_by_tile`, `_grow_own`
- [ ] Checks: reproducible, compared, share measured

### 8. The year outside the economy (`sim/agents/registry.advance`, the engine's other phases)
- [x] profile: of a warm Rome year, every phase except the market's is small; the economy's step is the rest
      (wrap each `year_phases.SHIPPED` handler and `Economy.step` with a timer: the outside is about a tenth)
- [x] the town ceilings' route searches kept across years while the techniques held and the ways built are unchanged
      (`urban.kept_carriage_costs`; `test_year_speed_urban_carriage`)
- [x] a partner country's economy answers (pay, floors, output, idle hours, people) kept until the economy next steps
      (`country_part.KeptAnswers`, `Economy.years_stepped`; `test_year_speed_kept_country_answers`)
- [x] the price solver re-solves only when its wage ratios change (banded in its key; cached in memory and on disk): a
      warm year makes no new solve, so nothing to cut there
- [ ] what is left is spread thin (invariants' per-trade view reads, `port_year_inputs.build`, `port_sites.deplete`,
      stratum advance, the home world's repeated floor and pay reads): each a few hundredths of a second
    - [x] national prices and wages read through a market layout built once per set of keys (`price_index.py`;
          `test_year_speed_national_prices`, equal to the old scan); the game unchanged by it
    - [ ] the price solver's re-solves within a year, the urban ceilings, the trade-wage lookups, the groups' and
          strata's repeated country figures, the state budget's standing lines
- [ ] Checks: reproducible, compared, share measured

### 9. The opening solve (`opening*.py`, `households_orders.goods_orders`)
- [x] the households' orders and the income root find over arrays: `opening_demand.OpeningDemand` packs the cohorts, needs,
      goods and store goods once per solve; `opening_demand_kernel.demand` runs the orders, the purse search, the plot cut and
      the quantities of every cohort at once (`test_opening_demand_kernel`: equal to `goods_orders` through
      `resting_orders` and `quantity_at`, on random cohorts)
- [x] `opening_runs` over recipe matrices: `opening_runs_pack.RunSolver` and `opening_runs_kernel.required_runs` (the input-output
      fixed point, tool fallbacks, by-product ceilings); `fit_to_supply` sweeps on arrays (`test_opening_runs_kernel`)
- [x] `_seed_durable_stocks` and the demand after the settle ask the packed cohorts too (`durable_bids`, `final_demand`)
- [x] Checks: England cold opening (`open_economy`, empty `ROME_CACHE_DIR`, `open_dump.py` in the port scratch folder) about
      44 s before and 5 s after; its record agrees with the one before in every producer, cohort income, cash and price
      (the sums the old code made with `math.fsum` are exact in the kernel, which matters: a bid at the edge of what a
      cohort can afford exists or not by the last bit). Rome cold opening about 120 s after; Rome's household plans
      are discrete and its opening moves with last-digit changes (producer counts differ between kernel variants), so
      the Rome record before the port is compared below
- [x] Rome's opening changed by the port (8170 producers against 8189, households' hired work about 15 against 0.3):
      the packed settle reused the households' stock from before the durable stock was seeded, so durables that serve a
      need and are also stores of wealth were counted as wealth; the old path's memo of orders (`own.uncut`) was stale the
      same way when it was reused. After seeding, the orders are made again and the cohorts packed again from the stock
      held (`OwnPlots.forget_orders`, `OpeningDemand.repacked`; `test_opening_seed_repack`). Rome's opening agrees with the
      old code's (8189 producers, worst relative difference about 1e-14); England's is unchanged
- [x] the rest of Rome's opening: the cost was repeated work, not loops. `household_plans` worked the producers' hours demand
      (`expected_shares`) once per cohort; it is worked once per call. `location.opening_split` re-derived the placed tiles of
      a recipe on every call; the placement reads are kept per setup. `crop_sites.sites` works a recipe's paying floor once.
      `_place_producers` asks which tiles hold people and who owns richest by tile from a table made at its start.
      `labour_state.producers_hours_needed` sums over arrays (`opening_hours_needed.hours_by_cell`, test
      `test_opening_hours_needed`: same dicts, same order, same bits). Records agree with the ones before (`open_compare.py`)
      to the last digit in England and to about 1e-14 in Rome. Measure with `open_dump.py` (England and Rome cold openings)
      and `open_prof.py`; not yet ported: `location_inputs.place_oriented`, `opening_demand._buy`, `households_own.own_production`

### 11. The economy's ledger and memory as arrays
After items 1 to 9 a warm Rome year is about 3.7 s (`year-time --years 4` on the shared save, three runs). Its profile is
flat: about 15 million calls a year, a third of them dictionary reads, most of them into the book (balances and stocks
keyed by agent, good and tile) and the market memory (prices, wages and quotes keyed by strings). The kernels are fast;
the cost is reaching the records. Both become arrays indexed by integer ids (agents, goods, tiles, areas, trades
numbered once), with their present methods kept for callers that read one value, and array methods for the phases that
read or post many. The saved format may change (no migration, CLAUDE.md 4.6); save and load must round-trip.
- [x] the book (`sim/book.py`, `book_batch.py`, `book_record.py`, `book_types.py`): balances by (agent, currency), stocks by
      (agent, good, tile) in flat slots, `rows_of` / `balances_of` / `stocks_of`; the game unchanged and no faster yet (the
      packs still read one value at a time); the rest of the line:
      batched posting (`post_settled`, `move_many`, `transfer_many`) straight into them; the phases' packs read them
- [ ] the market memory (`market_memory.py`) - built on branch `port-memory-arrays` and NOT merged: single reads through
      numpy are slower than dict reads and the year was no faster; it pays only once the readers read in blocks (Complaint 968):
      as arrays by (good, area) and (trade, area); `YearView` reads them; the year arrays' memory part becomes a view of them
- [ ] string market keys (`market_key`, `KEY_SEPARATOR` splits) replaced by id pairs on the hot paths
- [ ] Checks: reproducible, compared, the year measured

### 10. Finish
- [x] `python3 sim/simulator.py compile-kernels` compiles every registered kernel (`sim/jit.REGISTRY`) ahead of play, for
      an environment's setup script (with the `NUMBA_CACHE_DIR` the game will use): about two minutes on an empty cache,
      and a Rome year on that cache compiles nothing (`test_compile_kernels_declared`, slow `test_compile_kernels_smoke`)
- [ ] a process's first year on a warm cache is slower than its second: the first year's route searches are a kernel
      (`routes_tree_kernel.least_tree`; `test_kernel_route_tree`), cutting the gap from about 4 s to about 2 s; left: loading
      the cached kernels, building the route graphs, the cost trees. A one-command sitting (`agent --session`, `state`)
      costs about 3.5 s: imports, the save's parse and build, the reply, the save written again
- [ ] A Rome year under one second, and every civilisation's year measured (`year-time` on a save of each)
- [ ] `openings --prune` rebuilt and committed; the full build timed
- [ ] the slow suite green, or each red topic explained with the complaint that owns it
- [ ] Complaint 497 updated with the measured year; PR opened
