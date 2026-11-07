# Numba port of the economy's year

**Status:** in progress on branch `speed-year-step-and-openings`. One PR when every item below is ticked.

**Measured** (`year-time --session SAVE --years 2 --reload-check` on the shared Rome save; seconds of the two years):
- before the port: about 23 and 20
- items 1, 2 and 5 in part: about 17 and 13.5, reproducible after a reload
- with labour's heads and switching, entry's practice and the national prices: about 15 and 11 (machine loaded)

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
- **Checks before a phase is ticked.** The quick tier is green; `year-time --reload-check` on the shared Rome save is
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

### 1. Labour clearing (`sim/labour/market/`)
- [ ] Market clearing (`clearing.clear_all`, `clear_one`, `hire_through_rounds`, `import_cost`)
    - [x] every market prepared, then all their hiring rounds in one kernel (`hiring_kernel.py`, `applications.hire_markets`),
          then finished (`test_year_speed_labour_hiring`, the old rounds in `labour_hiring_reference.py`)
    - [x] the hours-sold schedule over a matrix of wages (`sim/economy/labour_supply_kernel.py`; `test_year_speed_labour_sold_hours`)
    - [x] the fetched-hands search and the wage searches for every market at once (`clearing_kernel.market_heads`,
          `clearing_arrays.py`; `test_year_speed_labour_heads` against `clearing._plain_head`; the plain path kept for a
          mod's fetch search or an unpacked schedule)
    - [ ] the per-market tail in Python: `eligible_bids`, `retain`, `offer_ceilings`, the hiring jobs, `poach`, `asks.record`
- [ ] Trade switching (`switching.switch_trades`, `_odds`, `_planned_moves`)
    - [x] the per-band logit (`switching_kernel.band_shares`; `test_year_speed_labour_switching`)
    - [x] targets, gains, costs, plan reuse and moves for every source of an area (`switching_kernel.plan_area`,
          `take_moves`; `test_year_speed_labour_plans`)
    - [ ] expected incomes at graduation and the refusal path
- [ ] Trade formation (`formation.form_trades`): early return where no origin sells, origin asks kept for the year; the
      per-market purchase and carriage searches are Python
- [ ] Checks: reproducible, compared, share measured

### 2. Goods clearing (`sim/economy/goods_market*.py`, `unsold_search.py`, `seller_offers.py`, `price_setting.py`, `demand_search.py`, `market_quote.py`)
- [x] The market clear: the logit allocation, rationing and redirect rounds, buyers' requests and trades
      (`goods_market_kernels.py`; `test_goods_clearing_kernels`)
- [x] The unsold-stock search and the sold-out raise, each bisection in one kernel
- [x] Sellers' pricing: every searching seller of a market priced in one call (`price_setting_kernel.py`)
- [ ] What is left: the pairing's tuples, the demand schedule's build, sellers' unit costs and ask limits; markets of
      one good's areas batched together (needs `year_goods.clear_goods`)
- [ ] Checks: reproducible, compared, share measured (reproducible after a reload on the merged branch)

### 3. Households' respend (`goods_respend.py`, `goods_respend_year.py`)
- [ ] rounds over every rationed cohort and market in one kernel (uses the goods clear of item 2)
- [ ] Checks: reproducible, compared, share measured

### 4. Settlement and the year's ledger (`settlement.py`, `year_ledger.py`, `sim/book.py`)
- [ ] goods and labour settlement postings in arrays
- [ ] the ledger's notes of postings and plant purchases
- [ ] Checks: reproducible, compared, share measured

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
    - [ ] siting (`location.siting`), `entry_trial.recipes_by_cost`, `entry_backed.unfilled` over packed wage, price and rent tables
- [ ] producers' and firms' close of the year
    - [x] pooled practice, input prices and wages read once per recipe and tile and handed to each producer's close
    - [ ] `producers_close.close_year`, `next_expectations`, `_pledgeable`, `firm_year.settle_year` over packed arrays
- [ ] households' close (the offered prices read once per good and tile, `households_close._priced_needs`; the rest is Python)
- [ ] Checks: reproducible, compared, share measured

### 7. The rest of the economy's year
- [ ] producers' plans (`producers.plan`), cohorts' orders (`year_goods.cohort_orders`), produce and offer
- [ ] hour supply, outside option, labour context, land bids and leases, wear and spoilage, the outcome
- [ ] Checks: reproducible, compared, share measured

### 8. The year outside the economy (`sim/agents/registry.advance`, the engine's other phases)
- [ ] profile and port or cut what is left: actors and strata, the state, events
    - [x] national prices and wages read through a market layout built once per set of keys (`price_index.py`;
          `test_year_speed_national_prices`, equal to the old scan); the game unchanged by it
    - [ ] the price solver's re-solves within a year, the urban ceilings, the trade-wage lookups, the groups' and
          strata's repeated country figures, the state budget's standing lines
- [ ] Checks: reproducible, compared, share measured

### 9. The opening solve (`opening*.py`, `households_orders.goods_orders`)
- [ ] the households' orders and the income root find over arrays (most of a cold game build and of `openings`)
- [ ] Checks: a cold Rome opening timed, its opening compared with the one before the port

### 10. Finish
- [ ] A Rome year under one second, and every civilisation's year measured (`year-time` on a save of each)
- [ ] `openings --prune` rebuilt and committed; the full build timed
- [ ] the slow suite green, or each red topic explained with the complaint that owns it
- [ ] Complaint 497 updated with the measured year; PR opened
