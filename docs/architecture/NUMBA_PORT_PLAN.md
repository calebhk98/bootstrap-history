# Numba port of the economy's year

**Status:** in progress on branch `speed-year-step-and-openings`. One PR when every item below is ticked.

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
- [ ] The game reproducible across a save and load before any port: Han's rich stratum (welfare, migration outlay and
      the falling-incomes group's claim, grievance and strength) differs in its last digits after a load, and
      `industry_opening_rate` of a seat writes `0` before a load and `0.0` after. Found by `year-time --reload-check`.
    - [ ] find the order-dependent sum behind the stratum figures and fix it (regression test)
    - [ ] the opening-rate field keeps one type (regression test)
    - [ ] `year-time --reload-check` passes on the shared Rome save

### 1. Labour clearing (`sim/labour/market/`)
- [ ] Market clearing (`clearing.clear_all`, `clear_one`, `hire_through_rounds`, `import_cost`)
    - [ ] pack the year's labour markets, bids and offers into arrays
    - [ ] kernel over every market: reservation, ceiling, wage, eligible bids, retention, hiring rounds, poaching
    - [ ] unpack wages, hired hours, asks; rule tests beside the old path
- [ ] Trade switching (`switching.switch_trades`, `_odds`, `_planned_moves`)
- [ ] Trade formation (`formation.form_trades`)
- [ ] Checks: reproducible, compared, share measured

### 2. Goods clearing (`sim/economy/goods_market*.py`, `unsold_search.py`, `seller_offers.py`, `price_setting.py`, `demand_search.py`, `market_quote.py`)
- [ ] The market clear (`goods_market.clear`, the logit allocation, the demand schedule)
- [ ] The unsold-stock search (`unsold_search.clear_with_search`, `raise_sold_out`, `demand_search.raise_asks`)
- [ ] Sellers' pricing (`seller_offers.strategic_offers`, `price_setting.best_price`)
- [ ] Checks: reproducible, compared, share measured

### 3. Households' respend (`goods_respend.py`, `goods_respend_year.py`)
- [ ] rounds over every rationed cohort and market in one kernel (uses the goods clear of item 2)
- [ ] Checks: reproducible, compared, share measured

### 4. Settlement and the year's ledger (`settlement.py`, `year_ledger.py`, `sim/book.py`)
- [ ] goods and labour settlement postings in arrays
- [ ] the ledger's notes of postings and plant purchases
- [ ] Checks: reproducible, compared, share measured

### 5. Merchants (`merchants*.py`, `lending.merchant_requests`, `carriage_hours.py`)
- [ ] route search for orders and credit requests over arrays of goods, areas and carriage costs
- [ ] dispatch and close
- [ ] the carriers' wage scale (`carriage_hours.wage_scale`)
- [ ] Checks: reproducible, compared, share measured

### 6. Entry and closing (`entry*.py`, `location.py`, `practice.py`, `producers_close.py`, `firm_year.py`, `households_close.py`)
- [ ] entry plans and siting
- [ ] producers' and firms' close of the year
- [ ] households' close
- [ ] Checks: reproducible, compared, share measured

### 7. The rest of the economy's year
- [ ] producers' plans (`producers.plan`), cohorts' orders (`year_goods.cohort_orders`), produce and offer
- [ ] hour supply, outside option, labour context, land bids and leases, wear and spoilage, the outcome
- [ ] Checks: reproducible, compared, share measured

### 8. The year outside the economy (`sim/agents/registry.advance`, the engine's other phases)
- [ ] profile and port or cut what is left: actors and strata, the state, events
- [ ] Checks: reproducible, compared, share measured

### 9. The opening solve (`opening*.py`, `households_orders.goods_orders`)
- [ ] the households' orders and the income root find over arrays (most of a cold game build and of `openings`)
- [ ] Checks: a cold Rome opening timed, its opening compared with the one before the port

### 10. Finish
- [ ] A Rome year under one second, and every civilisation's year measured (`year-time` on a save of each)
- [ ] `openings --prune` rebuilt and committed; the full build timed
- [ ] the slow suite green, or each red topic explained with the complaint that owns it
- [ ] Complaint 497 updated with the measured year; PR opened
