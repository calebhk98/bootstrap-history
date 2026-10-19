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
- `economy_state_budget` ("printing to cover a deficit ... can run away"): FIXED on `fix-printed-money-prices`, test
  unchanged. Cause: the state's goods bids carried its programme as a flexible quantity at the elasticity of
  substitution (Complaint 502), so in a market where the state's own demand pushed the price up the bid shrank with
  the price (firewood in the capital's market cleared near 6 times its reference price on a budget that would have
  paid 30 times; steel and wine the same) and most of what was printed stayed in the treasury: of 2.8e9 issued the
  first year the state spent about 3.5e8, and it still held 40 percent of the coin after eight years. Not the
  cause (measured by lifting each on the settled opening, `resumed(fiat=True, full_length=True)`): households'
  `WEALTH_DRAWDOWN_LIMIT` and `SPENDING_CUT_LIMIT` (printing run 3.67 with both lifted against 3.57), the sold-out
  ask raise, the hour cap on the state's hiring (lifting it lowers the level, more labour hired). A helicopter drop
  (every agent's cash doubled or multiplied by ten, no state spending) does pass to prices: about 9 times the
  control after eight years for ten times the cash. Fix: a stated real spending target (`StatePolicy.real_spending_target`)
  sets `StateBudget.real_programme`, and its goods bids are floors (bought whatever the price, up to the budget);
  a budget-led state keeps the substituting bids. Tests: `test_economy_state_need_bids_substitute` (programme
  bids), `test_economy_state_budget` (a bigger programme raises the level more). Remaining: the state buys in the
  capital's market only and spends on goods with no sellers (flour), so sub-proportional pass-through to the national index.
- `auto_hire_buys_room`, `auto_hire_rich_founder`, `round8g_display` (its train/why checks), `arrears_hours` ("no closed
  concern stays shut") pass on `origin/main` and failed on `economy-accounting-and-speed`; one cause. Bisected
  (first-parent merges, the topics together with `--only`): first fails at the merge of `data-532-herd-joint-products`
  (`40877b9a` passes). The opening herds (532) are credited to the held-stock ledger, which has one holder (the
  founder), and each year's growth of that ledger is billed to the founder as "stock raised" labour: about 11 million
  cash on a first step, so the founder went to -20973, could not pay staff and bonded. Fix: the herd the society's
  producers keep is recorded (`society_herds`, set at the grant) and moves with the herd's own growth and loss; only
  growth of head beyond it is billed (`living_stock_yearly.py`). Regression: `opening_herd_growth_unbilled`.
- `foreign_actor_trade`: "no longer swings from year to year" passes on `origin/main` and fails from the same 532
  merge. The widest-paying cargo is now millet, a glut of which the partner holds as stock for about five years
  and then gives way in price once before the cycle repeats. Choosing a cargo that happens not to swing would fit the
  test to the case, so the fixture is unchanged and the topic stays failing: the held-then-released glut is a
  real stock cycle in the partner's market (553). Open.
- `economy_money_regimes` (england_1300, struck coin: "and the price level") failed after the 550 workplace-size
  data (since reverted on this branch; it passes again) and passed just before it. The data moves the opening and with it the phase of the price cycle (473): over
  years 4 to 7 the mined run dips once below its twin, while over fourteen years extra metal raises the price
  level well above the twin. The window is unchanged and the check stays failing until the spin-up settles. Open.
- `affordability_and_credit`, `arrears_hours`, `arrears_visibility`, `failure_and_bounty_money` failed from the 550
  workplace-size merge (since reverted) and passed just before it (bisected over the first-parent merges; `arrears_hours` per merge).
  The data moves the opening so the founder's market rate starts several times dearer (read it with
  `sim(capital=1000.0).market_rate()`). Two causes. (1) Engine: the credit line's serviceable bound let the running
  tab's own interest, at a dear rate, take the line's interest above income; now only the earning left after the
  tab's interest backs new advances (`credit_limit`, regression: the dear-rate check in `affordability_and_credit`;
  `credit_line_effect` states the new bound). (2) Fixture: "in arrears" was set far deeper than the subject needs
  (purse negative), so one year's interest at the dear rate crossed the limit and wiped the project; the arrears
  are now the smallest that make the purse negative, every assertion unchanged.
- `stock_growth_and_smuggling` crashed at import: its stand-in `Game` lacked `society_herds`, which the yearly
  living-stock step now reads (the 532 fix). The stand-in now carries the mixin property and an economy field.
  `interface_honesty` ran over six minutes: the near-the-limit check started at 75% of the limit, but a year's
  deficit now carries the household past 100%, so it settled its debt and stepped all fifty years at several
  seconds each. It starts at 60% (a year's drift lands it past 70%, short of 100%) and the topic takes about
  half a minute (`python3 -m sim.tests --slow --only interface_honesty --jobs 1`). The assertions are unchanged.
- `spin_up_money_supply` fails on `origin/main` (measured at `678e74da`): the money stock falls below one decade of
  unreplaced wear (`python3 -m sim.tests --slow --only spin_up_money_supply`). Complaint 473's status line, which
  says this topic passes, is stale. Limiting opening prices to goods a start can make (566) moves it closer to the
  bound without passing.

- Complaint 570 closed: the opening now sizes the fuel its smelters burn (`fit_to_supply` holds the chain, not only the timber's direct users). `economy_tin_dearer_than_copper` still fails with a narrower gap (`python3 -m sim.tests --slow --only economy_tin_dearer_than_copper --jobs 1`); `opening_floor_and_thin_trades` (building boom) fails marginally on the branch base as well.

- Complaint 511 traced again on `tin-against-copper` (see its Update 5): `economy_tin_dearer_than_copper` still fails on
  copper's year-zero scarcity, which comes from the suite's unsettled short opening (smelters idle in the last hidden
  year, stock gone, yearly pace limit) and from smith hours capped by the trained-substitute wage ceiling. No engine
  defect found; the check is not weakened and stays failing until the opening settles or the labour ceiling is
  revisited.
- Branch `pm-complaints-burndown`: `sited_ore_price_over_cost`'s common-ores check (green on main) is red. Forest
  timber as a stock (539) makes iron ore open far above its cost while the opening stocks a year of inputs; the fix
  (open with a working stock, 519's last section) turns four other cycle-dependent checks red until the spin-up
  settles (473), so it is held back. Two more checks green on main are red here for the same reason (both pass
  with the working-stock change in): `full_length_opening_checks_han` wage over floor and
  `full_length_opening_checks_norse` sited ores. Three known regressions, all waiting on 473; none is marked as an
  expected failure, so they stay visible.

## Stage 4 of 507: checks that fail on the economy's real dynamics (2026-10-19)

Left failing on purpose, with causes (`python3 -m sim.tests --slow --only real_output,real_output_cheaper_entry,real_output_baseline --jobs 1`):

- `real_output_cheaper_entry`, "clears a larger quantity of it than the same society without it" (factor kept): with
  `GOOD` a final good (stone blocks) the game clears only about three tenths of a percent more than its twin. Cause:
  households' demand for a building stone is nearly inelastic, so a cheaper entry moves real output through value
  weights, not volume. Real output and output per head still rise.
- `real_output`, "...but not output per head, which stays near where it was": after a 40% fall in people, output per
  head reads 1.26 to 1.58 over the following years. Food volumes rise (survivors eat more of the same land's food)
  while construction falls. This may be the right economics (more land and capital per head after a population fall, as
  after historical plagues), so the owner decides what the proof should be; the expected direction is not changed here.
- `real_output_baseline`, goods far from their baseline: the unsettled spin-up (473) moves goods beyond the bound
  stated in the test; measure with the topic's MEASURE line.
