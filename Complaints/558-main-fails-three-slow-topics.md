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

- Branch `507-stage-7-price-search-within-year`: `economy_innovator_pricing` "the price path falls steadily without a
  swing between years" fails in year 6 (a rise of 1.253 against the 1.2 limit; earlier variants of the branch failed
  the same check in year 16 or 20 by a hair). Cause: the in-year search plus the queued holding-value floor lets a
  year's price fall fast while the entrant's capacity is still small, and the next year's price recovers by more than
  the limit; it comes from the floor commit, not the exit valuation. Complaint 553 notes this check sits at its
  threshold in every variant of the yearly step, so it is read as a cycle property, not a defect of one rule. The test
  is not loosened and stays failing (`python3 -m sim.tests --slow --only economy_innovator_pricing --jobs 1`).

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

## Slow topics that pass on origin/main and fail on pm-settling-speed-and-walls (integration bisect)

Bisected on the first-parent merges, one topic list per commit (`python3 -m sim.tests --slow --only <topics> --jobs 1`).

- Fixed, engine: the 589 merge (7d98a10a) gave `Household` a `record` property (its `HouseholdState`) that shadowed the
  `ActorRecord` convention; `charge_coin_carriage` read `record.country` on the founder paying a concern levy, so
  every step with a levy failed (`complaint_584_forecast_takings_cash_book`, `actor_treasury`). The shared borrowing rule now reads
  `arrears_book`. Regression check in complaint_584.
- Fixed, tests: `complaint_181_save_cost` and `step_interrupts_and_alerts` called `_play_run_one_command` without the
  `SavePolicy` 497 added. `complaint_181_save_cost` counts every `os.replace`, so a cache write inside a shared
  process can make its "a step rewrites the save" read 3; it passes alone.
- Real dynamic, 612-614 (075f790b): the generic `artisan` trade is now a remnant. Its national pool fell
  (`people_who_exist("artisan")` on rome_100ad: about 40158 before, about 181 after; measure with
  `labour.people_who_exist`) because the economy's artisan hours moved to the new trades. `complaint_585_staff_pay_retention`
  and `actor_firms_compete` staffed the generic trade: fixtures moved to `labourer` (their subject is not the artisan pool).
  Still red for the same cause: `firm_borrows_to_enter`, `firm_expansion`, `firm_costs_scale`: `concern_staff`
  (sim/engine/agents_port.py) always asks for `artisan` craftsmen, so a firm of about 32 artisans against a pool of
  about 181 pays a scarcity wage (wages roughly triple after year one in `firm_borrows_to_enter`'s setup) and the
  opening firms close. `firm_entry_default_game`: the iron bar's year price at the opening fell (0.31 against 2.26 per kg),
  so `finery_puddling` has zero market factor (pig iron bought costs more than bars sold) and no entrant sees a margin;
  it fails from 609-611 (1c0e7ea2). The fix is a design call: firm craftsmen drawn from the trades the concern's recipes name.
- Real dynamic, 589 (7d98a10a): `failure_and_bounty_money` "a year's late spending cannot leave capital past the credit
  limit". `enforce_credit_limit` no longer clamps or settles on the spot; spending past the ceiling becomes arrears and
  defaults after `ARREARS_YEARS_BEFORE_DEFAULT` years. The 438 invariant is superseded; left failing for the owner of 589
  to restate (what bounds a year's late spending now).
- Open engine defect, 609-611: `soldiers_leave_production`. The registry flags `labourer` as the fallback, but
  `labour_allocation._non_farm_shares` excludes the fallback's own people and `society_hours` gives it no hours, so
  its tightness factor saturates (1.148) with or without an army. The test now reads the world's flagged fallback
  (`trade_data.fallback_trade_of`) and fails on the real cause: the hours left after farm and specialists should go to
  the fallback trade in `sim/labour/labour_allocation.py` (`society_hours`).

## Fixes on `fix-firms-hire-recipe-trades`

- Fixed: a business's crew is the trades its recipe names. `Sim.venture_crew_by_trade` (`plant_figures.crew_by_trade`)
  is the one function the founder's path (`venture_hands`) and the agents path (`concern_staff`) read; a plant whose data
  states no hours takes the flagged unskilled trade, not a named generic one. Regression: `crew_is_the_recipes_trades`.
  `firm_borrows_to_enter`, `firm_expansion`, `firm_costs_scale` pass. `founder_and_firm_agree` and `firm_count_whole_game`
  now read the crew as the sum over its trades (their subject is the founder and firm agreeing, not the artisan pool).
- Fixed: `soldiers_leave_production`. The specialists work their people's hours and `society_hours` gives the flagged
  fallback trade the hours left after farm and specialists (`labour_allocation._non_farm_shares(rest_hours)`).
- Fixed: `auto_hire_buys_room`. The founder's auto_hire still hires the generic craft trade, whose estimate of people had
  fallen to the no-demand floor ("nobody left to hire"); the generic craftsman is any craftsman, so its share of town
  work is that of the craft family together (`labour_population._share_of_town_work`).
- Fixed, test: `failure_and_bounty_money` restated for 589: late spending past the credit limit is carried as arrears no
  larger than the spending, counts a year each year, and is defaulted in year `ARREARS_YEARS_BEFORE_DEFAULT`.
- Still failing, not the trades: `firm_entry_default_game`. At HEAD the opening agent economy's wages are several times
  the earlier ones (furnaceman and engraver most; measure with `economy.agent_wage_per_hour(trade)` on a default game),
  which lifts the iron bar's long-run price and so cuts its market factor, and the entrant's value test
  (`entry_round.NicheEntry.found`) fails on the copy cost. The jump is not in 609-614: wages are normal at 549
  (84858956) and at 5e744142, and high at 44cd2125 (Merge 605-607, saving finds a use: households count what they own of
  the firms and the opening estimates it from the runs). Owner of 605-607 to look at the opening wage level.
- `foreign_actor_trade` passes on `origin/main` (19 checks, 0 failures) and fails on `pm-settling-speed-and-walls` at
  "...and no longer swings from year to year" (partner price moves by more than 1 percent between years). Bisected
  (first-parent merges, `python3 -m sim.tests --slow --only foreign_actor_trade --jobs 1 --topic-seconds 400`): passes
  through `5e744142` (513) and `84858956` (549); first fails at `44cd2125` (merge of 605-607-saving-finds-a-use).
  Cause confirmed by switch: with `owned = 0.0 * equity_of(view, cohort.agent_id)` in
  `sim/economy/households_orders.py` the check passes again. The households' equity term (605) changes the Rome
  opening's prices a little; the test's cargo (`cargo_for`, millet, about 1.98 million units a year, no return cargo)
  is sized to what still pays against the partner's price, so it is about the same every year, and the partner's
  stock-and-capacity book (`close_partner_books`, `market.adjusted_capacity`, `market.stock_after_year`) answers it
  with a limit cycle: in the failing run the partner price is 130.28 in most years and falls to 64.7 in year 4 and 78.3
  in year 7 (at the 44cd2125 merge: 72.1 every other year, 68.5, 69.4, 70.1 between), snapping back the next year as
  the glut clears. The home side is not stepped in this fixture, so the swing is the partner book's own dynamic at a
  cargo near its threshold, not a home-economy defect. Not fixed; the bound is not loosened. Open (a partner book
  whose capacity answers a steady cargo without a two-year cycle is the fix to find).
- Fixed, 607 (branch `fix-opening-wages-after-equity`): the opening counted the households' equity in its income fixed
  point (`opening_equity.py`). A household may spend wealth above what it wants to keep at up to a year's income a
  year (`WEALTH_DRAWDOWN_LIMIT`), so equity added a lasting demand the opening settled on: Rome's opening income was
  76 percent higher and the thin trades' (furnaceman, engraver) wages at one labour area (`work@france_05`) ran to
  20 times the others after year one. Removed from the opening; the in-run equity read stays. Regression:
  `opening_income_equity`. After it, `agent_wage_per_hour` on a default game is back to the 549 levels
  (labourer 0.043, furnaceman 0.061, engraver 0.080) and `foreign_actor_trade` passes (19 checks, 0 failures).
  `firm_entry_default_game` still fails and also fails at 84858956, before 605-607: its cause is the 609-611 one above
  (the iron bar's price), not the opening wage. `saving_finds_a_use` "households spend most of their income" read the
  opening's state (0.92 came from the opening equity; the run's own effect is 0.878 against 0.875 without it), so it
  now compares runs with and without the equity read.

## Integration branch regressions (fix-integration-regressions-2)

Measured on the integration branch with `python3 -m sim.tests --slow --only <topic> --jobs 1`; each passes on `origin/main`.

- `cli_one_process_session`: one process playing four commands leaves a different save from one process per command
  (`python3 -m sim.tests --slow --only cli_one_process_session`). Bisected over the first-parent merges: equal through
  996ce535 (598), different from 4e521c8f (627-628); inside it, commit 3b7a5900 (627). Setting `wage_scale` in
  `sim/economy/carriage_hours.py` to 1.0 makes the two saves equal again at that commit, so the cause is the
  carriage wage scale, whose effect a reload does not reproduce: the year-2 differences start at about one part in
  1e15 on a merchant's hours wanted and grow through the price search. The reloaded table, the persisted `carried`
  flows and `memory.wages` were checked and match; which unpersisted input of `wage_scale` differs is not yet
  found. Open: the check stays failing.
- `economy_carriage_hours`: `test_hours_given_to_carriage_are_taken_from_what_other_employers_hire` fails from 598
  or earlier on float noise (others hired equal to one ulp: carriers hired almost nothing), and stopped failing
  after the opening-income fix, when carriers are hired but only 8 of 43 planned hours. That makes
  `test_a_plan_the_market_can_fill_is_hired_in_full` fail: the bid's maximum wage (1.2) is far above the town wage
  (0.04), yet the town's labourer hours are all taken (others plus carriers is constant), so the labour market
  rations. Not a fixture mistake; the check stays failing until the market's rationing of a late bidder is decided.
- `firm_entry_default_game`: since 1c0e7ea2 (609-611) no entrant copies `finery_puddling`. Measured on the
  branch: the market factor is no longer zero, expected takings are 12k a year (25k before), but the copy plan
  costs 200k (72k before), because the opening market price of coal rose (the case for `blast_furnace`'s coal
  in `project_material_bill`: 58k before, 220k at 1c0e7ea2, 185k now) while the price solver's coal price barely
  moved. The trade split left the unskilled `labourer` pool as the poor and the bonded and put the farm stratum on
  `farmer` (whose quoted wage is four times the labourer's), and coal's hewing and haulage hours are labourer and
  miner hours. Open: why the economy's coal price at the opening is two to three times its solved price.
