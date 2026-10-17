# Main fails three slow topics

**Status:** open

Measured on `origin/main` at f0ff751d with `python3 -m sim.tests --slow --only market_records_ownership,economy_tin_dearer_than_copper,insolvency_whole_game`:

- ~~`market_records_ownership`: "no module outside the market writes a market record" names
  `sim/engine/economy_electricity.py` writing `market_flows`.~~ Fixed: the throttle peek saves and
  restores the flows through `goods_market.snapshot_flows` / `restore_flows`.
- `economy_tin_dearer_than_copper`: tin shows far cheaper against copper than the labour its recipe embodies
  (511). Measured again on the 511 branch: tin is above its cost (about four to seven hours of wage a kilogram
  against about one hour of embodied labour); copper shows six to nine times its smelting cost, so the ratio fails
  on copper's scarcity price, not on unsold tin or gravel asks. Cash, loans, ore and plant do not bind year zero
  (the test's only year): the opening's workforce by trade and seeded `last_runs` do (smith hours in Spain are all
  hired), so a fix belongs with the opening. Later years: starved flux makers never grow (511's third update).
  Open.
- `insolvency_whole_game`: fixed (see 524): a household in arrears now lives within its income, so its debt no
  longer climbs past the credit limit and its cash rises.

A red slow suite on the default branch means every branch's slow run starts red and its own regressions are
read against noise. Each failure needs a fix or, where the subject is an open design issue, a pinned status
with the test kept honest.
- `affordability_and_credit`: fixed (test, not engine). The last section stepped twice and then read a project whose
  calendar floor is two years; on this branch the project (the dearest the founder can start on 30% of its bill) now
  finishes in the second step, on origin/main it was still active (late with arrears). Both are legitimate. The test
  now steps once, so a two-year floor leaves it active, and checks it is part-paid with cost still left.
- `economy_bronze_market_price`: the 502 check on bronze's shown price over its cost fails (worst about 2.4).
  Measured (stepping `rome_100ad` 18 years as the test does; shown bronze over `notional.cheapest_cost` at the shown
  input prices): it PASSES on `origin/main` (worst 1.81 in year 12, `python3 -m sim.tests --slow --only
  economy_bronze_market_price`, 133 s) and fails on this branch (the test's own 18-year run shows the worst
  years 15 to 17 at 4.1, 4.5, 5.6). It is not copper alone: bronze's cost is 90 percent copper at the shown price,
  but on the branch copper falls to 5.4 to 7.5 in years 15 to 17 while bronze stays 22 to 31, so the ask lags a
  falling input (a markdown share a year) and a thin market holds it. With the 550 change (`seller_offers.stands_for_many`,
  aggregate producers keep the price-taking reservation) disabled the late spike goes (years 15 to 17 about 0.96)
  but year 5 still shows 3.07 against the 3.0 bound, from copper halving over years 1 to 4 (12.8 to 6.8) faster than
  bronze's ask follows. So two things: the 550 aggregate pricing makes the late bronze price ratchet (not yet
  explained: why a price-taking reservation reaches 4 to 5 times cost), and any fast fall of copper shows as a
  ratio above 1 because the cost is read at the same year's inputs. Not fixed; the diagnosis is a lead for 550 and 511.
- `economy_bronze_market_price`, bisected on `economy-accounting-and-speed` (helper `bronze_multiples(6)` in the
  test file, one game per commit): years 1 to 6 are inside the bound through the 546 and 558 merges; entry sized
  to unfilled bids (559) briefly pushes year 4 over; food intake above need (513) pushes year 2 over (traded about
  3.1 times cost) through households' demand and labour, not through any bronze rule; the aggregate ask markdown
  (550) adds a lag behind falling copper in years 2 to 6. The late-year spike from 550 is fixed. What is left
  moves with every change elsewhere, as `economy_innovator_pricing` does (553): the early price over cost is a
  scarcity price while supply catches up, and it depends on when entry and expansion arrive. The test topic
  also runs over the time limit. Open; not loosened.
- `real_output` passes on `origin/main` and fails on `economy-accounting-and-speed`: the checks that a new
  entry's producer lowers the posted price, the founder's bill and raises cleared quantity and real output.
  Bisected (first-parent merges, `python3 -m sim.tests --slow --only real_output --topic-seconds 290`, one at a
  time): it first fails at the merge of `fix-550-aggregate-ask-2` (the aggregate producer marks its ask down by
  the share left unsold); `4379d546` and earlier pass. The engine is not wrong; the fixture was. (1) The cleared
  volume of a good is measured against the first year a late entry clears it, and the twin (no entry admitted)
  was pinned to its reference, so the check compared the game's year-0-to-year-5 drift of the whole world
  against 1.05; the 550 change moved the opening and the drift, so the game's ratio fell below the pinned twin
  though it still cleared more than a twin measured the same way. (2) With the herd joint products (532) `fat_kg`
  is a by-product of flock and herd entries, so halving the first entry that outputs it was not the incumbents'
  entry and its cost ratio was far above the bound, and a staple or by-product answers a price fall by less than
  the drift. Fix in `sim/tests/test_real_output.py`: the twin is baselined on its own first year, the source
  entry is the incumbents' (`_reference_entry`), and the good is `copper_ore_kg`, whose cleared volume answers a
  cheaper entry by far more than the drift. Every assertion and bound is unchanged. Closed.
- `purchase_reads_economy_price` passes on `origin/main` and fails on `economy-accounting-and-speed` at "a larger
  order costs more a tonne" (every mean equal). Bisected (first-parent merges, `python3 -m sim.tests --slow --only
  purchase_reads_economy_price`): first fails at the merge of `data-532-herd-joint-products`. The engine is not
  wrong; the fixture was. The staple's supply schedule is flat (sellers price at cost) until the order nears what
  they hold, then climbs; the fixture's biggest order was a 0.9 share, and the order is priced at slice midpoints,
  so it reached the climb on `origin/main` but stopped short of it on the branch, where the opening's sellers hold
  a little more. Fix in `sim/tests/test_purchase_reads_economy_price.py`: the largest order is 0.99 of the book,
  which walks up the schedule. The assertion is unchanged (means sorted and the last above the first). Closed.
- `arrears_hours` (and the three below) crashed with `KeyError: ('fulminate_kg', 'sweden_01@b4')` in
  `year_close.close_agents`: the merchants' price news is keyed by the area a clearing used, but the area map had
  been rebuilt at the year's prices and the good now sat in another value bucket, so the area (and its anchor)
  was gone. Fix: `merchants.close_year`'s `lag_years` may return None for a market whose area is no longer in the
  map and that news is skipped (nothing reads an expected price of a vanished area); `year_close` returns None
  when the anchor is missing. Regression: `test_merchant_travel_time.py`. `arrears_hours` still has its auto_hire
  check failing (not this item).
- `port_unskilled_trade`: its opening fixture lacked `carriage_wage`, which `in_units` now counts; fixture gains
  it and asserts it is counted in the trade's hour. No engine change.
- `whole_game_gold_silver_ratio`: the test read `area_of` for silver, which has no market (no price, no area).
  The test's reader now treats a good outside `area_map.goods()` as unpriced. Assertions unchanged.
- `complaint_173_credit_forecast_once`: the fixture's cash left after the first start now covers the third
  start's materials, so it never borrowed. Cash is set to nothing after the first start so later starts must
  borrow; assertions unchanged.
- `economy_imports`: `sim/engine/living_stock_opening.py` imported `sim.economy`; it now asks
  `EconomyPort.producer_capacities()` (new, via `AgentEconomy.producer_capacities` in `economy_port_year.py`).
- `state_budget` ("the same shortfall spread over a second equally visible taxpayer asks half as much of each")
  passes on `origin/main` and fails on `economy-accounting-and-speed`. Bisected (first-parent merges, `python3 -m
  sim.tests --slow --only state_budget`, one checkout at a time): passes through `40877b9a`, first fails at the merge
  `80065efd` (data-532-herd-joint-products). The engine is not wrong; the fixture was. The test adds a firm with a 60M
  purse and a staff, then steps a year; the year spends part of that purse (herd entries, 532), so the firm's visible
  scale (staff, wealth, prominence) fell below the household's (about 0.52 against 0.57) and it was no longer
  "equally visible". Fix in `sim/tests/test_state_budget.py`: after the year, the firm's purse is set (bisection on
  `visible_scale_of`) to the household's visible scale. The assertion and bound are unchanged. Closed.
- `economy_money_regimes_norse` ("and the price level") passes on `origin/main` and fails on the branch. Bisected
  the same way (`--only economy_money_regimes_norse`): passes through `40877b9a`, first fails at `80065efd` (532). The
  engine is not wrong; the window was. On the short spin-up the Norse basket level drifts up several-fold over fourteen
  years in the twin and the mined run alike, and the mined run's ratio to its twin swings from 0.65 to 1.17 year to
  year (`play("norse_900ad", 14, ...)` with and without `mined_share`), so the mean over years 4 to 7 sat in a
  trough. Moving the window until it passes (a later, longer window passes with a thin margin) would fit the test to
  the drift, so the window is unchanged and the topic stays failing until the opening settles (Complaint 526). Open.
- `economy_state_budget` ("printing to cover a deficit ... can run away"): passes on `origin/main` and through
  `4379d546`; first fails at the merge `38113d14` (fix-550-aggregate-ask-2: a crowd's ask closes the gap to cost by the
  share left unsold). NOT fixed, test unchanged. Measured (`resumed(fiat=True)` control against `StatePolicy(real_spending_target=4*supply,
  financing_order=("issue",))`, eight years): on the suite's short spin-up the no-printing control itself inflates (price
  level 12 times in eight years with the money supply constant, expected inflation to 0.55; 6.7 times at `4379d546`),
  and the printing run rises 16.6 times (36 times at `4379d546`), so "3 times the control" fails; printing
  harder (1 to 12 times the supply) leaves the level at 16 to 27 times, i.e. not driven by the money printed. On the
  declared-length opening the control is settled (price falls), printing raises the level about 8 times the control,
  expectations and supply checks pass, but the level saturates near 3 to 5 times even at 100 times the supply, at
  `4379d546` and on the branch alike. So the old pass came from the short opening's drift (Complaint 526), and the
  engine shows no runaway on a settled opening: money printed is not reaching prices proportionally (suspect the
  546 cash-limited producers or the per-year ask adjustment). The assertions need that mechanism, not a looser
  bound. Open.
