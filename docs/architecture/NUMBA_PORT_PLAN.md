# Numba port of the economy's year

**Status:** in progress on branch `speed-year-step-and-openings`. One PR when every item below is ticked.

**Measured** (`year-time --session SAVE --years 2 --reload-check` on the shared Rome save; seconds of the two years):
- before the port: about 23 and 20
- items 1, 2 and 5 in part: about 17 and 13.5, reproducible after a reload
- with labour's heads and switching, entry's practice and the national prices: about 15 and 11 (machine loaded)
- with settlement, the ledger and the producers' read caches: about 13 and 9
- with the labour tail, the urban ceilings and the partner countries' kept figures: about 12 and 8
- with the respend rounds in one kernel: about 11 and 7.5

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
  goes unseen in a compiled run); `year-time --reload-check` on the shared Rome save is
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
- [ ] `sim/economy/year_arrays.py`: producers (recipe, tile, runs, capacity, crew, expectations by recipe good), cohorts
      (tile, people, cash, basket), market memory (prices, wages, quotes by good or trade and area), the recipes' input and
      output matrices
- [ ] built in `Economy._run_year`, refreshed by entry and exit, checked against the records in a test
- [ ] the first phase moved onto it: the year's close (`producers_close.close_year`, `firm_year.settle_year`, `households_close`)
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
    - [ ] what is left of the clearing is the write-back of one `LabourClearing` and its state entries per market (the saved
          record format) and `import_cost.reach`, one route search per area
- [ ] Trade switching (`switching.switch_trades`, `_odds`, `_planned_moves`)
    - [x] the per-band logit (`switching_kernel.band_shares`; `test_year_speed_labour_switching`)
    - [x] targets, gains, costs, plan reuse and moves for every source of an area (`switching_kernel.plan_area`,
          `take_moves`; `test_year_speed_labour_plans`)
    - [x] the carry-out and the refusal path (`switching_kernel.enrol_groups`)
    - [x] the round's moves collected in one kernel (`switching_kernel.collect_moves`) instead of numpy glue in `_planned_moves`
          (`test_year_speed_labour_plans`)
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
- [ ] What is left: the cost itself over arrays (`unit_cost.full_cost_per_unit` per seller, dictionary prices in and out);
      the markets of one good's areas cleared by one kernel call (a `ClearingResult` with its fills and pairing is still
      built per market, because the ledger, the settlement and the markets' memory read them). Measured in the second
      year (cProfile seconds, `year_goods.clear_goods` 3.5 in all): `unsold_search.clear_with_search` 0.9 over 4054
      markets (floors, held values, salvage floors, the raise: Python per offer), `_produce_and_offer` 0.7,
      `settlement.settle_goods` 0.5 (packs the pairing's tuples per market), `seller_offers.strategic_offers` 0.4
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
- [ ] dispatch and close
- [ ] the carriers' wage scale (`carriage_hours.wage_scale`: mostly route searches cached after the first year)
- [ ] Checks: reproducible, compared, share measured

### 6. Entry and closing (`entry*.py`, `location.py`, `practice.py`, `producers_close.py`, `firm_year.py`, `households_close.py`)
- [ ] entry plans and siting
    - [x] practice means over packed crews (`practice.py` kernels; `test_year_speed_practice_kernel`); each recipe's
          entrant crew read once per entry year (`entry_practice.entrant_crew`)
    - [x] reads kept per view and per siting call (the memory's wage, price on offer and price kind by tile, the input haul and
          hands of a recipe and tile, one planned recipe per hours; `test_year_speed_producer_reads`); the game unchanged by them
    - [ ] siting (`location.siting`), `entry_trial.recipes_by_cost`, `entry_backed.unfilled` over packed wage, price and rent tables
          (what is left is per-request Python: `planned_recipe`, `input_haul_cost`, `full_cost_per_unit`; a kernel needs the
          year's price and wage tables packed per (good or trade, tile) once and the requests as index arrays)
- [ ] producers' and firms' close of the year
    - [x] pooled practice, input prices and wages read once per recipe and tile and handed to each producer's close
    - [ ] `producers_close.close_year`, `next_expectations`, `_pledgeable`, `firm_year.settle_year` over packed arrays
- [ ] households' close (the offered prices read once per good and tile, `households_close._priced_needs`; the rest is Python)
- [ ] Checks: reproducible, compared, share measured

### 7. The rest of the economy's year
- [x] `live_wages_at` and `present_prices_at` read once per trade and tile until the memory is written to (`YearView.wages_at`),
      land sellers indexed once a year (`land_bid.owners_of_sellers`): `firm_land_bids` from about 0.3 s to 0.02 s of a year
- [ ] producers' plans (`producers.plan`), cohorts' orders (`year_goods.cohort_orders`), produce and offer
- [ ] hour supply, outside option, labour context, land bids and leases, wear and spoilage, the outcome
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
      the Rome record before the port is still to be compared (an old-code Rome opening takes about twenty minutes)
- [ ] the rest of Rome's opening is outside this item's files: `household_plans`/`work_terms`, `_place_producers`/`location`,
      `labour_state.producers_hours_needed`

### 10. Finish
- [ ] A Rome year under one second, and every civilisation's year measured (`year-time` on a save of each)
- [ ] `openings --prune` rebuilt and committed; the full build timed
- [ ] the slow suite green, or each red topic explained with the complaint that owns it
- [ ] Complaint 497 updated with the measured year; PR opened
