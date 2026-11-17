# The agent economy's spin-up never settles, so the opening is a point on a cycle

**Status:** partly - settled stays a fixed point and the economy must not be chaotic (the owner). Poaching, household time, servant hiring, durable demand and the lenders' expected inflation no longer amplify or cycle (Updates 30 and 31); an ore with no deposit is dug nowhere and the opening's recipe choice settles (Update 32, the owner's answers to questions 8 and 9). `spin_up_settled` still fails for every civilisation measured: producers' inventory value and some watched prices move by many times the tolerance, hired hours and output by one to three times it. Update 32 lists what stands in the way: output falls by a fifth in the first two years after the opening, households cannot buy what they plan to and the unspent coin piles up with them out of the producers' working coin; a co-product nobody buys piles up; and inventory value is measured against itself although it sits near nothing (owner questions 10 to 12)

Research on reference models for making the opening a steady state (issue #61): `Complaints/reports/research-reference-economy-models.md`.

Found while tracing why the opening money wage moved several-fold between builds of the same branch (the
fix for that is in `Complaints/closed/470`). The price level in the hidden spin-up cycles with a period of
about twenty-five years (one Rome trace: about 0.94 at the start, 2.7 a dozen years on with the interest rate
over twenty per cent, back near 1 by year twenty-four), the first stage does not meet its convergence tolerance
within its years, and the game opens wherever the cycle stands. Unrelated changes (a producer's expansion rule,
the smoothing bound) moved the opening price level and the money wage by a large factor through that alone.

The cause is not households' opening money: they open at their cash-balance target, the producers' working
capital passes to them in the first year whatever the opening cash was, and scaling households' opening cash
or income up or down on the small fixture (`sim/tests/economy_fixture.py`, which cycles the same way) changes
nothing. The mismatch is between the opening income, which assumes every worker is employed all year at the
opening wage, and producers sized to a much smaller final demand: realised income is a fraction of the opening
figure, and producers' expansion and hiring against idle labour drive the cycle.

Why it matters: every price, wage and purse a player sees at the opening depends on where the cycle stops,
so a small change to any mechanism can move the whole opening economy, and a measurement taken at the opening
says little about the mechanism measured (CLAUDE.md 4.2: the baseline should be a plausible draw, not an
accident of when the warm-up stopped).

Evidence: build a game with `sim.tests.harness.sim(capital=400000.0)` and print `game.capital` (the founder's
purse is repriced by the opening money wage, `sim/engine/opening_money.py`) on two builds that differ only in
an unrelated rule; print the spin-up's price level, households' cash over the wealth they keep, and spending
over income by spin-up year (no committed command prints these).

A longer trace (Rome, the first stage run for a couple of hundred years with no tolerance met) shows the
cycle sits on a drift that does not end. At the opening most of the hours households offer go unhired;
producers borrow and expand for decades and the hired share climbs, and the unskilled wage falls the whole
time. Capacity and the hired share level off after several decades, but the economy does not: the money
supply shrinks every year by about the coin wear (`metal_stock.COIN_WEAR_PER_YEAR`), the mint strikes almost
nothing to replace it (its edge nets to about nothing, and some years it melts), the wage keeps falling, and
after the better part of a century households start going short of food and the price level climbs by
multiples. The money audit (`money_audit.year_report`, `YearOutcome.money_audit`) shows the wear edge as
the only steady sink. So a longer spin-up cannot settle it, and the shipped openings (`openings/`, written by
`simulator.py openings`) are the declared-length spin-up, not a resting point. No committed command prints
the trace; it is each year's `YearOutcome` from `Economy.step` during the spin-up.

What it would take: an opening whose producers' capacity, workforce and households' income agree (sized from
the same final demand), and a model of how fast producers expand and hire against idle labour that damps rather
than overshoots; coin lost to wear replaced (new metal reaching the mint when coin is scarce) so the money
supply does not drain; then a spin-up that runs until its tolerance is met, or records plainly when it is not.

Related: 470 (closed), 472 (closed), 464.

## Playtest evidence (Rome, `play --civ rome_100ad --kit merchant --seed real25`)

The cycle reaches the player. Over the first two decades the `money` screen's market rate moved from single
digits to the ceiling `bounded_rate` sets (four times the civilisation's `starting_interest_rate`,
`sim/world/capital_market.py`), and stayed there for several years. Over the same years "funds lenders hold"
fell to about a quarter of its year-104 figure. Funds lenders hold is built mostly from `household_saving()`
(`sim/finance/capital_market.py`, `sim/actors/world_credit.py`; that function no longer exists: `grep -rn household_saving sim` finds nothing), so household saving collapsed. The founder's borrowing is far too
small to move it. A founder who had borrowed at a normal rate to hire staff paid well over half the debt in
interest each year and went insolvent. Wages (and with them the workshop's revenue, which is a markup on
wages) fell through the same years. Reproduce by stepping a year at a time and reading `money`.

## Current state (Update 4, stage 2 of 507)

Built on `507-stage-2-opening-from-costs`: household income settled with the demand it pays for, plant sized to the share that
works, workforce placed for the runs producers expect to sell, producers opening with their inputs, recipes ranked with
deposit ceilings and demand-limited co-products, the metal the money loses a year as the mint's final demand, and the coin
priced at the marginal cost of its metal.

Fixed: the money stock follows from the transactions and the metal's cost, the chain behind the coin metal exists at the
opening, and the wear test passed at the time (`test_the_money_stock_keeps_up_with_wear`, since removed; the mint tests are `sim/tests/test_mint_settles_by_regime.py` and `test_economy_mint.py`) (the mint's strikes are about wear over the last decades;
`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`).

Not fixed (so this complaint stays open): the spin-up still reports not settled for every civilisation. The price level no
longer cycles but falls for decades with the wage, while employment grows into the gap; realised income in the first year is a
small share of the opening figure. The cause is the wage: the labour market clears at the households' outside option from
the first year, and prices follow it down slowly. Seeding the wage at that level does not help because prices and the outside
option scale together. What it needs is a settled model of how a labour glut passes into prices (the economy's rent and price
search, stages 5 and 7 of 507), then a spin-up that runs until its tolerance is met. Do not weaken the settling tests.
Regenerate `openings/` (`python3 sim/simulator.py openings`) when this lands; the shipped entries are keyed on the source and
every source change leaves them unread. The owner's decision on 507 (one price owner, 2026-10-14) is made, so this does not wait on it.

## Measured sections and what each found (full text in `Complaints/reports/473-history.md`)

- Coin wear and the spin-up report: `spin-up-trace` exists; the money stock sinks by coin wear and the mint struck nearly nothing to replace it.
- Update 2, material orientation: answers three questions on why the chain cannot feed the mint; the haul term is restricted to fixed-site inputs.
- Update 3, joint recipes gated on value: `producers.runs_for_stock` judges a joint run on the outputs' prices; the mint's strikes over wear rose, the test still failed then.
- Note 2026-10-15: England's `MONEY_LAG_YEARS` check was loosened while the price level climbs; restore it when the price level stops climbing.
- Settling statistic, main against the in-year price search (507 Stage 7): the within-year price search (branch deleted unmerged) shrank rate and level swings and settled the money stock; the level and wage still fell (608).
- What made the integration branch's spin-up swing (probe table by change; the 467 check now excludes the plot trade and trades under one worker-year of jobs).
- Which merge tips the spin-up into cycling (table by commit): the price-level index is part of the loop, not all of it; planning to the area's demand in single-area thin markets was not tried.
- The opening basket held to supply (merge 66da3cd3): the household basket was never held to what producers could leave; fixing it took the 20-year probe from cycling to calm; the labour glut remains.
- Where the unhired hours are: the sizing fix needs the price index and joint by-products (bran) handled first; not a labour mechanism.
- Expansion that replaces wear before it grows (branch deleted unmerged): calm at 20 years, an earlier and higher surge at 60; not merged.
- Why makers with plant sit idle while their price climbs: not `producers.py`; the fix lies in entry of an input maker where buyers exist, merchants carrying bloom and bar, and price memory under scarce supply.
- Entry does fire for a bloom market with no maker, but builds where the ore is; the fix lies with merchants and the makers' input chain.
- The late brick and cart surge is not a wear wave (stocks are steady-state with no ages); carts lack iron bar; why bricks stop was not traced.
- How the yearly rate is set: no defect proven, no code changed; candidates are an inert credit market, the one-way step limit and unbounded `maximum_rate`.
- Where the households' cash goes in the year of the rate spike: lent out by `lending.lend_working_capital` to merchants whose wage loans were over-asked; the wage-loan sizing fix cut the loans sharply (later years unmeasured).
- Is the steady deflation the mint failing to replace worn coin: no, the stock shrinks far less than the price level; the real economy contracts; no code changed.
- Why output falls tenfold after the opening: producers follow sales; the stock gate (`producers.runs_for_stock`) binds from year 1 and supply moves only a quarter of capacity a year.
- Opening sized net of the own-plot cut (branch deleted unmerged): lowers traded value further; the root is the year's own-plot rule, and land-limited plots (551) are needed first.

## Design comparison (2026-10-20)

`Complaints/reports/research-agent-based-economy-design.md` compares this economy with published agent-based models
(Lengnick 2013, Caiani et al. 2016, Wiese et al. 2024, Peters et al. 2022). Two departures bear on settling: those
models start from a solved stationary state spread over the agents (Caiani) or a long burn-in (Lengnick), rather than a
spin-up hoped to settle; and labour demand there comes from vacancies, with hires bounded by the smaller of the jobless
and the vacancies. The share of offered hours unhired here may count own-plot hours as idle; report them apart before
reading it as unemployment. Pricing departures are 642 and 643, the rate 641.

## Update 5: the replacement figure goes negative because the mint melts coin once the price level runs away

money_replacement (sim/economy/baseline_checks.py) is struck net of melted, over wear; its sign is right (in the cached 40-year Rome traces the stock change equals struck less wear each year). The mint rule is intended: it sells the metal it holds at parity (mint.mint_orders), so when other buyers pay more than the mint pays for bullion it melts coin, and the measure counts that on purpose. Early years strike a large share of wear; as the price level climbs the run (the food shortage owned by other work) metal becomes dearer than coin, the mint stops buying and sells, and the last decade nets to melting. So silver not reaching the mint is no longer the binding cause late in the run; the price level is. Rows: python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 40.

## Finding: the Norse baseline price level falls without any intervention

Measured earlier with a seven-year Norse play (no mined metal), the basket price level
by year is 1.07, 1.41, 0.96, 1.07, 0.96, 0.55, 0.46. Millet, about a third of the basket's weight, falls to about 0.4 of
its base price by year five, and wheat is already about 0.37 of base in year 0. With 10% extra mined metal each year the
level follows the same food collapse a year earlier (the money stock does double). So the slow validation "more metal
raises the price level" (`check_more_metal_raises_price_level`) is drowned by the unsettled economy for Norse; the
transmission rules are held by `test_money_reaches_prices`.

## Update 6: a one-year closure test on the small fixture, and the movers it finds (branch opening-stationary-state)

What is built: `sim/economy/opening_stationary.py` (a plain function: the runs that meet a final demand by the
input-output solve in `opening_runs`, the hours they hire, and the incomes they pay, so wages plus profit equal the
value of final demand), `stationary_setup` (now `sim/economy/fixture_setups.py`; the fixture with each worker offering the hours its runs
hire plus a stated slack), and `sim/tests/test_opening_stationary_rules.py` (a stepped year against the settling
bounds in `sim/economy/settling.py`). The opening does not yet seed its producers from the solver. Run:
`python3 -m unittest sim.tests.test_opening_stationary_rules sim.tests.test_opening_input_stocks`; the red parts are
marked `expectedFailure`, so an unexpected success shows when one of them is fixed. The figures below came from throwaway
probes (no committed command prints the year-by-year table).

Movers, in the order they bite:

1. **Hours offered against hours hired; the wage is a unit root.** The stated fixture offers many times the hours its
   runs hire, so year 1 clears the wage at the workers' survival wage (`labour_ask_floor`), an order of magnitude below
   the stated wage, and grain follows it down because sellers price at cost. The stated wage is not a clearing wage
   (608). Scaling every price and wage down does not help: the survival wage is the floors' cost over the hours, so it
   scales with the prices. The nominal level has no restoring force: with hours short of demand wage and price jump
   once and stay; with hours in excess they drift down a few per cent a year; only the knife edge where hours offered
   equal hours demanded rests. The stationary opening therefore has to fix the hours offered or the wage jointly with
   the runs (`opening_stationary.hours_offered_over_demanded`), not take the cost table's wage.
2. **Seeded inputs the same year's market also supplies** (`opening._stock_producers_with_inputs`). Producers produce
   and clear in input-depth order, so a user buys its input from an earlier maker in year 0 and works it the same year; the
   seed makes year 0 buy none, the maker's year piles up unsold, its sales estimate halves and the stock gate
   (`producers.runs_for_stock`) plans it down the next year. Built and measured (year 0 then trades the input), then not
   landed: the dug input's cobweb moves a year earlier and two fixed-bound tests fail (`economy_vessel_price_fixture`
   year-to-year swing, `economy_no_offer_memory` price floor). Bounds were not widened. The rule's test is kept as an
   expected failure (`test_opening_input_stocks`).
3. **Input bids reach the buyer's whole run margin** (`producers._input_bids`: price plus margin per run over the input
   per run). With the coin metal's price pinned by the mint, the smelters' margin grows as wages fall and the ore price
   climbs to the cap; the sellers' own ask is bounded at a multiple of unit cost (`ask_raise.ASK_BAND_CEILING`, retire
   643), so a buyer-side cap at the input's cost would only restate that band. Not changed.
4. **The mint strikes less than the coin wears** (14 per cent short in year 1 on the stationary fixture): the metal
   demand the opening sizes (`opening_metal.yearly_replacement`) is met by capacity the chain places with the opening's
   spare share, then the smelters' expansion swings it. Owned by mint/entry work.
5. **The rate moves by several points in year 3** on the stationary fixture (credit clearing; owned by the credit work).
6. **Expected inflation read the basket index.** Fixed: `currency.price_inflation` (weighted median of the goods' price
   changes) feeds the households' expectation (`households_close.close_year`) and the memory's
   (`MarketMemory.note_basket_price_level`); rule tests in `test_economy_price_inflation`. On the fixture the heavy good
   moves, so the median follows it and the fixture's figures do not change; it matters where thin goods run away.

Not reproducible on the fixture: 545 (the fixture has no land per run, so households grow nothing for themselves);
the stock gate is not the first mover once the seed is gone (the gate binds in year 1 only on the seeded run).

Orchestrator commands (minutes each, shared cores; not run here): `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`
and the settling statistic over its rows (`sim.economy.settling.settling_report`, as `port_trace.spin_up_trace` feeds it).

## Update 7: hours offered are a choice against the plot; the stationary fixture rests (branch opening-labour-supply-and-seed)

Built: `households_hours_offered.py` (a household keeps hours for its plot down to where the next hour adds no more
than the wage it faces; no land or nothing the land grows serving a need means all hours offered; hours nobody hired go
back to own production, `own_production`), `household_hours_year.py` (the rule per cohort, wired into
`Economy._shortfall_hours` beside the own-plot plan and household work, so the kept hours leave the offer and the
clearing's workforce), tests in `test_economy_households_hours_offered`. The hours kept at a wage do not depend on the
hours a worker has (the marginal hour is in absolute hours on the plot), so the fixture's hours are the hours its runs
hire plus the hours kept at the stated wage (`economy_fixture.stationary_setup`, now with a plot: `land_per_run` on the
farm recipe, and no slack by default).

Measured (python3, seconds, throwaway probe): stated fixture, hours offered over hired 11.6, wage 1.0 to 0.075 in year 1,
grain 0.3 to 0.045. Stationary fixture before (no plot, 10 per cent slack): wage 0.795 in year 1, grain 0.294 then 0.249.
Stationary fixture now (plot, no slack): log changes in year 1 wage +0.03, grain -0.05; year 2 wage -0.02, grain -0.08;
year 3 wage -0.03, grain +0.02; with 10 per cent slack the wage still drops by a third in year 1 (the knife edge:
only offered equal to hired rests). Closure checks now plain: wage, grain, metal price and money within the bound each
year; the rate within its bound. Still expectedFailure with causes named: the stated fixture's one-year check (it has no
plot, so 2000 hours a worker cannot be used at home; leisure and household work do not exist in it), the ore price (year 3,
log +0.5, the smelters' bids against the ask band, mover 3) and the mint (strikes about 30 per cent less than wears, mover 4).
Hired hours still fall in later years (0.68 to 0.53 million over 3 years, demand side). Not done: seeding the engine's
opening wage and `opening_income_per_head` from `opening_stationary` (Rome offers 2000 hours a worker against what its
recipes hire; the household-work hours (645) are what should take the difference, unmeasured).

## Measured (2026-10-21, 60-year Rome trace at 3d05ffbe)

`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60` in a checkout pinned to the merge of the robust inflation
index and the real-rate credit bound (before the households' plot-hours choice). Output: `Complaints/reports/473-trace-3d05ffbe.txt`.
The price level still runs away after the first decade and hired hours fall many-fold; the wage rises with prices. Expected
inflation no longer follows one thin good, so the run-up is real: it is the supply collapse traced on #61 (year-0 overproduction,
the stock gate planning zero runs, idle capacity decaying, food running out) and the input-bid ratchet (a buyer's cap is the
input's price plus its whole run margin, so a scarce input is bid up without bound). Next: the stock gate eases instead of
zeroing plans when stock will clear; capacity is not shed while expected sales cover cost; an input bid is bounded by what the
input is worth in use against its substitutes, with rationing by bid only when supply is short. Re-run the same command after.

## Update 8: the supply collapse and the input-bid ratchet, each link as a rule (branch supply-collapse-and-bid-ratchet)

Rules (each with a rule test that builds producers and views, not a game):

1. Planning (`producers.runs_for_stock`, `STOCK_CLEARING_YEARS`, test_economy_stock_drawdown): excess stock over the target
   is worked off over several years (runs are expected sales less excess over those years), so a producer with a positive
   margin whose stock clears in them keeps working; it plans none only for stock that cannot clear.
2. Capacity (`producers_close.close_year`, `idle_capacity.py`, test_economy_idle_capacity_life): idle plantless capacity
   wears at the one over its tools' service life (`IDLE_CAPACITY_DECAY_SHARE` retired); a producer sheds workplaces
   in the first year its expected sales do not cover running cost, not after three loss years, and not so many that the
   workplaces that pay would make less than it expects to sell (short supply lifts the price). `LOSS_YEARS_BEFORE_EXIT`
   stays only as entry's wait (`entry_margin`). The bare removal of the count was measured to be worse on the fixture
   (the model re-draws the workplaces' cost spread each year, so shedding to the paying share repeats), hence the
   expected-sales floor.
3. Input bids (`producers.input_ceiling`, `tool_fallback.value_in_use`, test_economy_input_ceiling_share): a ceiling is the
   price plus the run's margin shared by the input's cost share (not the whole run margin), and for a tool never more than
   it saves against the cheapest substitute in the basket (wooden tools, then by hand). The old wide-margin test that
   pinned a ceiling of ten times the price now pins the margin share.
4. Ask band (`ask_raise.band_edge`, `seller_offers.input_share_of_cost`, test_economy_ask_band_chain): the band multiple
   applies to what a seller adds; inputs it buys pass through. On a three-stage chain the old ceilings were 3, 12, 39
   times a stage's value added, now 3, 6, 9. `ASK_BAND_CEILING` (retire 643) is unchanged; the Caiani check (markup on
   unit cost, moved with inventory) holds, with the markup bounded per stage.

Fixture (stationary_setup, 8 years, throwaway probe, same seed): grain price year 5 0.224 (was 0.230), wage 0.916 (was
0.886); year 7 grain runs summed over the three producers 857 (was 510), real wage (wage over grain price) 5.1 (was 3.9);
staple runs after five years 72 per cent of the first year's (66 before; `test_economy_supply_collapse_scenario`). The
price still falls in later years: the wage unit root (mover 1) and the demand side are not touched here.

Not done: a Rome trace (orchestrator: `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`, then the
settling statistic). Left: the cost spread is re-drawn each year; the ore price and mint movers (3, 4 above).

## Measured (2026-10-21, 60-year Rome trace at 72e81e68, after Update 8)

Same command, checkout pinned to the merge of the supply-collapse fixes (stock drawn down over a horizon, idle capacity worn by
tool life, plant shed by margin, input bids bounded, ask band on value added). Output: `Complaints/reports/473-trace-72e81e68.txt`.
Against the 3d05ffbe trace: hired hours no longer collapse (they hold within a few-fold of the opening instead of falling
twenty-fold), and the price level's peak is an order of magnitude lower. It still rises by about two orders of magnitude between
the first and third decades and then wanders; not settled. Next: decompose the run-up by good (probe in the session's notes,
per-good contributions to `basket_price_level`) and fix the rule that moves the leading goods.

## Update 8: hours sold are a schedule against the wage; the opening splits time so offered equals hired (branch opening-elastic-hours-and-seed)

Cause of the knife edge found: the labour core cleared a market with all offered hours at the ask floor (`clearing_target`:
bids taken highest first, and when the bids' hours fall short of the offered hours the target is the ask itself), so a sliver
of excess hours took the wage to the floor. Built:

- `households_hours_offered.leisure_share / leisure_hours_kept / leisure_anchor_wage`: of the hours the plot and household
  work leave, a share falls to leisure, one half at an anchor wage, falling smoothly as the wage rises. The elasticity is a
  labelled heuristic (`LEISURE_ELASTICITY`, retire 675).
- `labour_supply.HourSupply`: a cohort's hours sold as a function of the wage (own-plot plan and household work fixed, plot by
  `plot_hours_kept`, leisure by the above). `Clearing` in the labour core takes it (`YearInputs.hours_share_at`) and finds the
  wage where hours sold meet the hours wanted (`clearing.supply_target`); hours kept, sold and at leisure are then read at the
  wage the market cleared at, and `_grow_own` no longer counts leisure as spare hours.
- `opening_leisure.seed`: at the opening, each trade's anchor wage is solved so the hours sold at the opening wage equal the hours
  the opening's producers hire (Eurace initialises so labour demand equals supply; Caiani et al. 2016). Stored in
  `EconomyRecord.leisure_anchor_wage` (real, at the opening's price level). Where the free hours do not exceed the hours hired
  there is no leisure.
- Tests: rules in `test_economy_households_hours_offered` (LeisureTests) and `test_labour_core_supply_schedule`; the fixture in
  `test_opening_stationary_rules` (OpeningHoursTests, KnifeEdgeTests).

Measured (throwaway probes over `economy_fixture.stationary_setup`, year 1 to 6): hours the households have beyond the opening's
split (given after the opening, `KnifeEdgeTests`): first-year log wage change -0.07 for three per cent more hours and -0.22 for ten
per cent, where before it was -0.35 and -0.41 (the wage fell to the ask floor for any excess); with the excess fitted into the
fixture's hours the opening's leisure absorbs it, and year-by-year wage over six years is 1.00 0.99 0.97 0.95 0.93 0.90 (three per
cent) against 0.70 0.70 0.67 0.64 0.53 0.46 before. The stated fixture (2000 hours a worker, plot) opens with offered over hired 1.01
and the wage 1.0 in year one, where the earlier fixture's wage fell to 0.075 and offered over hired was 11.6. The wage moves about
twice the excess: the plot alone makes hours sold rise by half a per cent for each per cent of wage; leisure adds to that only where
the opening found hours to spare.

The decline of hired hours is not gone (stationary fixture, slack none: 0.68 0.59 0.56 0.55 0.50 0.43 million hours, was 0.68 0.57
0.53 0.50 0.44 0.36). Traced: the grain farms' planned runs are the cash they hold over the cost of a run (`producers.plan`,
`affordable`), and their cash falls every year by what the households add to their own cash (about 41 thousand in year one, 76
thousand in year two, on a wage bill of 680 thousand): spending is below income and no lender takes the difference (607, 606). Year
one's revenue is also below its wage bill because the price falls to clear (the opening prices leave no margin). Not a defect of
the hours rules, so not changed here.

Rome is not measured here. Commands to run: `python3 sim/simulator.py spin-up-trace --civ
rome_100ad --years 60`; (the test was removed from the suite);
`python3 sim/simulator.py opening-checks`.

Leisure is limited to hours the plot could not still use (`HourSupply.parts`): without that limit Rome's one-year hunger share rose to
0.49 (`labour_margins_baseline_validation`), since hours that used to grow food became leisure. Now, Rome one year: hired share 0.33
(was 0.04), wage over floor 4.8 (was 3.4), hunger share 0.17 (was 0.15). `baseline_fixture` passes whole.

## Measured (2026-10-21, 60-year Rome trace at 9eb35921: hour supply schedule plus supply fixes)

Output: `Complaints/reports/473-trace-9eb35921.txt`. The first four decades are calmer than at 72e81e68 (the price level near
a hundred at year forty instead of nearer two hundred, hired hours steady), then the economy explodes after year forty: the
price level, the wage and the rate run away together within a few years (the rate far above one, the wage thousands of
times its opening). A per-good decomposition of years 35 to 52 is running (a `decomp.py` probe, not committed; the committed copy of the same kind is `Complaints/reports/473-decomposition-probe.py.txt`).

Decomposition of the late runaway (years 35 to 51 at 9eb35921, `Complaints/reports/473-decomposition-9eb35921.txt`; the probe
is `Complaints/reports/473-decomposition-probe.py.txt`, run from a checkout root with `FROM_YEAR=35 python3 <probe> 52`): wheat,
starch, leather and iron tools carry the index at hundreds to thousands of times base through year 43; thin goods spike in
year 44 (felt, milk, bricks); from year 45 nearly every good jumps at once while the wage rises many-fold, which points at the
unit of account (a real figure turned nominal with an index that thin goods spike) rather than one good's market. Being
traced as an indexation spiral (the leisure anchor and other real figures converted with `basket_price_level`).

## Update 9: real figures were turned nominal with the fixed-basket index (branch late-indexation-spiral)

Hypothesis from the year-44 to 50 trace: an indexation spiral. Conversion sites that used `basket_price_level` (the fixed basket over
recently traded goods at their remembered prices): `Economy._hour_supply` (the leisure anchor wage, economy.py), `state_budget.py`
(the real spending target and the state's wage fallback, and its inflation expectation), `mint_labour.py` (the wage fallback),
`opening_leisure.seed` (equal to one at the opening). A thin good's remembered ask spiking moves that index, so the nominal anchor
wage moved with it: built input in `sim/tests/test_price_level_indexation.py` (stationary fixture, anchor of one in real terms, the
thin `metal_kg` price multiplied by a million): the anchor wage was the basket level, about ten thousand; it is now 0.94.

Fix: `MarketMemory.price_levels` chains the opening's one by each year's observed inflation (the weighted median `price_inflation`),
read through `MarketView.chained_price_level`; the four sites use it, and `rebase_basket_price_level` resets it. `basket_price_level`
stays a reported statistic (outcome, trace, cohorts' cash target comparison). Not changed: weights in `price_inflation` use each
good's full opening quantity, so a sliver-trade good still weighs fully in the median; the cohorts' reservation wages and survival
wage were not found to use the index. Whether the late explosion goes away needs the 60-year Rome trace
(`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`), not run here.

## Measured (2026-10-21, 60-year Rome trace at 5306f780: after the chained price level, Update 9)

Output: `Complaints/reports/473-trace-5306f780.txt`. The late runaway is gone: the wage stays within a narrow band from the
fourth decade on (it had run to thousands of times its opening), hired hours hold steady for the whole run, and the rate stays
below its old ceiling. The fixed-basket price level (now a reported statistic only, read by nothing that sets a wage or a
target) still wanders over an order of magnitude and more, carried by thin goods' remembered asks (decomposition at 9eb35921).
Left for the settling check: the fixed-basket level's wander (drop thin goods' asks from it, or weight by what traded), the
rate's year-to-year steps against `settling_report`'s bound, and the slow baseline validations (`baseline_rome_full_length`,
`spin_up_money_supply_full_length`, `baseline_fixture`, `real_output_baseline`) re-run on this head.

## Update 9: the wheat run-up decomposed by year; it follows the iron chain starved of furnaceman hours (branch wheat-price-runaway)

Throwaway probes (per-good price multiple, `market_record`, producers' capacity, runs and expected sales; a wrapper on `producers.produce`
printing planned runs against the input and hour limits), 18 to 22 years after the cached spin-up, at 72e81e68 and again at 221bb02e.
No committed command prints the tables. No wheat rule was landed (last paragraphs).

Before the merge (72e81e68), wheat price multiple of base, years 0 to 17: 1.0, 0.72, 0.76, 0.74, 0.72, 0.73, 0.77, 0.79, 0.85, 0.92, 0.92,
1.0, 2.5, 3.5, 7.8, 14, 13.5, 13.5. Wheat producers' capacity falls from 3.06 million runs to 17 thousand; runs worked 2.5 million
(year 0), 0.3 million (1), 4 thousand (2), then hundreds, while unmet demand stays at 1 to 25 million kg. After the merge the path
changed: wheat sits low first (0.22, 0.19, 0.17, 0.15, 0.14, 0.11, 0.11, 0.10, 0.09, 0.09, 0.10, 0.12 in year 12) with runs zero or
hundreds in years 5 to 12 under a stock overhang of 1.5e8 kg; capacity falls to 3.6e4 runs by year 13; then wheat rises 0.42, 0.70,
1.0, 1.5, 3.5, 8.4 (years 14 to 19), 20 in year 20.

Which side moved first: supply, upstream of wheat. Leaders after the merge: bread (240 times base in year 5), thermal energy, mortar
and flint (170 times in year 9), then iron bar (3 in year 5, 10 in 11, 25 in 13, 47 in 14), iron tools (0.8 in year 10, 3 in 12, 19 in
14, 62 in 15, 210 in 16, 1000 in 20), and wheat follows iron tools. Wheat's recipe takes `iron_tools_kg` as a tool; by year 20 a
run's tool bill is 745 against a run revenue of 7900, so it is the shortage of hours that holds wheat output down: farmer hours hired
fall from 3.0e9 (year 0) to 4e7 (year 10) with 3e9 idle in other areas, and wheat producers in several areas get zero farmer hours in
years 17 to 19 (china_32, spain_03: planned 856 and 758 runs, hour limit 0.0).

The tool chain, from the produce wrapper: iron tools need iron bar (hard input), iron bar needs iron bloom and charcoal, and bloom is
made in four areas only. In year 12 the bloom makers plan 498, 4090, 1340 and 2150 runs and achieve 2.3, 1130, 10.6 and 35.7: the
limit is furnaceman hours (italy_02 hired 2.9e4 hours against 3.6e5 a year earlier), not ore or charcoal (held at three to ten times
the run's need), not cash and not the plan. Furnaceman hours are fully taken (idle 0) at a wage of 0.05 to 0.09 while the employers'
bids carry a worth of 3.6 to 8.6 an hour. The wage is held down by `sim/labour/market/clearing.py` `ceiling` (the trained
substitute wage, the unskilled wage times a training premium, then the import cost), and the trade's people shrink while the
vacancy stands (furnaceman hours in italy_02 for years 10 to 13: 6.8e5, 3.6e5, 2.9e4, 3.5e4). Owner: the labour work.

Tried and not landed: a producer's expected sales are what it sold (`year_close._with_sales`), so a seller that sells out in a market
with unmet demand expects only its own shrunken sales and its exit and shedding (`producers_close.close_year`) read that. A rule
adding a sold-out seller's share of the unmet demand (pure function, tested on built numbers) kept ten times the wheat capacity in
year 12 (3.8e5 against 4.6e4 runs) but wheat still falls to 3.6e4 runs in year 13 and reaches 8.4 times base in year 19, and it
failed `economy_service_lives` (a cash shortage sells more of the stock than the fixed bound allows). Not committed, bound not widened.

The slow baseline failure "stocks are not eaten through" on grain is not this runaway: on the fixture grain price drifts 0.36 to 0.40
over 60 years with the wage (1.0 to 1.29), and the grain stock is float dust (1e-10 kg) against sales of 1.8e6 kg a year. The check
`baseline_checks.stock_depletion` counted a start-of-window dust stock as a stock and its disappearance as a draw-down of 1.0. It now
skips a stock under `FEASIBILITY_TOLERANCE` of the good's largest flow (test_baseline_stock_depletion). The fixture's own drift (price
level up 0.4 per cent a year with the wage) remains, and is the settling failure above, not a runaway.

## Update 10: the scarce skilled trade's wage clears against bids (branch scarcity-wage, Complaint 678)

`clear_one` no longer caps this year's wage at the training cost; the cap stays on what entrants expect. Probe (`probe10.py` with the
shortened hidden spin-up, 5 years; a full spin-up exceeds five minutes): wheat price multiple years 0 to 4 was 1, 0.21, 0.19, 0.17, 0.16 and
is 1, 0.75, 0.73, 0.74, 0.72; iron bar year 4 was 3.2 and is 1.4; furnaceman hours hired hold at 2.5e8 to 2.7e8 (were 1.7e8 to 2.4e8). The
run-up after year 12 is not yet re-measured; command: `ROME_SPIN_UP_YEARS` unset, `python3 probe10.py 20` from the worktree root.

## Update 11: the below-cost reading after the sourced household day is a phase of the cycle, not a rule (branch opening-below-making-cost)

`price_over_making_cost_band_validation` (558) went red at e72b36c0, which changed only `data/world/household_work.json` and
`data/world/needs.json`. Putting those two files back to their 1cd50f79 content on the e72b36c0 tree restores the earlier numbers
digit for digit, so the data is the whole cause. The two sides of the check read the same wages: `economy_cost_book` takes
`agent_wage_per_hour` (the economy's hours-weighted wage by trade), and the price is the goods market's. No rule reads the wage
before household work on one side and after on the other.

Probe (not committed; `sim(civ="rome_100ad", capital=1e9)`, then `_step_market()` a year at a time, the check's own median of
price over `CostBook.cheapest_cost` for goods the economy traded), median ratio by year, years 0 to 8:

- 1cd50f79: 1.13, 1.12, 1.02, 1.06, 1.12, 1.08, 1.15, 1.52, 1.41.
- e72b36c0: 1.12, 1.11, 1.02, 1.02, 0.90, 1.00, 1.00, 1.01, 1.24.

The opening itself (year 0) is the same at both. The household day does enter the hour supply: hours offered for sale at year 0 are
about a tenth fewer and a third fewer at year 1 (`labour_supply.HourSupply` keeps the household's own work out of the offer), while
hours hired differ little. What differs is where the unsettled cycle (this complaint) carries the price level afterwards: it stays
low through year 2 at e72b36c0 and rises a year later, and at year 4 the farmer and vine-and-olive wages the cost side reads are
spikes from markets that hired few hours (farmer 1.2 coin an hour at e72b36c0 against 0.14, unskilled 0.09), which the price
follows only the next year. So the median at year 4 sits in a dip of a series that otherwise hovers about one. The check reads
one year of a cycle that does not settle, which is this complaint, not a mispriced opening; the check and its bounds are left
as they are, and it should go green when the cycle settles. Open question for whoever settles it: an hours-weighted wage over
markets that hired few hours (`wages_by_trade_weighted`) lets a thin market set a trade's cost; not changed here.

## Update 12 (PM): runs whose surplus is worth thousands of coin an hour

After the joint labour bids (678), the highest maximum wage any run bids for plumbers, masons and furnacemen in a Rome game is
still in the thousands of coin an hour in years 0 to 5, against an unskilled wage under one: the run's output is priced far
above what its inputs and hours cost. Which recipes set those maxima is not yet isolated; it is the price side of this
complaint (an output whose price is many times its making cost). Probe: wrap `sim/labour/market/clearing.clear_one` and
record the highest `maximum_wage` per trade and the recipe behind it.

### Update 12 result: the outsized surpluses are mostly planning on quotes from markets that did not trade (branch outsized-run-surplus)

Probe (not committed; `sim(civ="rome_100ad", capital=1e9)`, `ROME_SPIN_UP_YEARS=3,2`, wrapping `producers._labour_bids`, years 0 to 5, every country's
producers since the game runs the partners too; 25 thousand plans). Highest surplus an hour (`revenue / working_cost_ratio - inputs`), one row per output, years 0 to 5:

- cooked meal, china_29, year 4: 9.2e3 an hour; expected price 367 a kg against a making cost of 0.93; 4 hours-trade (domestic servant); 59 makers; sold 1.5e8 kg of 1.1e8 more wanted, stock 6e9; the price was a `best_unfilled_bid` quote.
- salted meat, china_02 and twenty more china tiles, year 3: 8.4e3; expected 448 against 2.2; 98 makers; sold 2.5e4 kg, 1.1e9 wanted, stock 7.5e3; `best_unfilled_bid`.
- water, china_40, year 0: 6.6e3 for half an hour a run; expected 3.3 against 0.0002; 104 makers; sold 2e11, stock 1.5e11; `best_unfilled_bid`.
- bread, china_54, year 5: 4.3e3; expected 262 against 5.8; 88 makers; `traded` (the year after a quote).
- gold, spain_03, year 4: 3.3e3 an hour; expected 5.8e3 against 2.5e3 (2.3 times; two makers; sold 4e3 kg, stock 1.1e5): a genuine ratio, the hours are a thousandth of the run's cost, so the whole surplus per hour is large; `traded`.
- piped water, turkey_05, year 5: 2.3e3; plumber maximum 7.9e3, last wage 13; expected 0.016 a kg against 2.6e-5 (the run's labour is its only cost); 70 makers; sold 1.3e10, wanted 9.5e10 more, stock 3.2e10; `traded`.
- timber, china_55, year 5: 2.0e3; 5.8 times its cost; 102 makers; `traded`.
- cattle, china_43, year 2: 1.9e3; 65 times; 19 makers; `traded`.
- glass, france_01, years 0 to 3: 1.4e3; 105 times; 6 makers; `lowest_unfilled_ask`.
- timber frame, china_55, year 4: 1.4e3 though price is 0.4 of cost (the working-cost ratio multiplies the revenue of a run that barely pays).

Cause. `producers.next_expectations` moves a maker's expected price toward `view.price`, which for a market that did not trade is a quote:
the best unfilled bid (the largest maximum any one buyer would pay, not a price anyone paid) or the lowest unfilled ask (a seller's own ask coming
back). In the first rows above the market had sold nothing; the quote (a household's ceiling of hundreds a kg for a floor good) moved the expectation
from 1.5 to 206 to 448 in two years, the maker's ask and its labour ceiling followed, and the next year a thin sale at that ask became a traded
price. Of the 200 plans with the highest surplus a hour, 80 read a `best_unfilled_bid`, 7 a `lowest_unfilled_ask`, 95 a traded price (mostly the next year's echo), 16 the opening estimate.
Not the cause: the ask band (643) bounds a seller's ask from the break-even price, but the break-even was the expected price's own scale; the founder and
the state buy none of these goods.

Fix (`sim/economy/planning_price.py`, called from `producers.next_expectations`): an output whose latest price is a bare quote lifts the expectation
no further than `ask_raise.band_edge` around the unit's cost-covering price (and never cuts an existing expectation). Gating the quote out
altogether was tried and broke `economy_vessel_price_fixture`: a market with buyers and no seller shows only that quote, and a maker needs it to start. Tests:
`sim/tests/test_economy_planning_price.py` (pure `held_to_band`, and `next_expectations` on a built view).

Measured, same probe, plans with positive runs: top five surplus an hour in year 3 were 8.4e3 x5, now 1.6e3 to 1.5e3; year 4 9.2e3, 7.9e3 now 2.6e3, 2.2e3;
year 5 7.7e3 now 2.7e3; plans more than 100 times their making cost, years 3 to 5: 39, 57, 110 before and 14, 30, 48 after. Highest furnaceman maximum 2.6e3, 3.3e3, 2.4e3 before and
1.5e3, 2.1e3, 1.9e3 after. Not closed: the plumber's maximum (thin piped water; a traded price, 8e3 before and 1.1e4 after in year 5, the market sells 1.3e10 of 1.1e11 wanted,
and the trade needs years of training: a real scarcity rent with entry blocked by training, whose rule is 678's short-run wage and the training lag), and thin sellers
asking far above cost in a traded market (salted meat sells 2.5e3 kg of 9e8 wanted at 55 times cost; the ask band is about the seller's ask from the expectation, which has no quote now; the remaining chain is the ask side, 643).

Slow topics (`--jobs 1`): `opening_floor_and_thin_trades` green before and after. `staff_closure_reopening_scenario` red before (1 closed concern left shut) and after (6),
a cycle phase more than a rule. `price_over_making_cost_band_validation` green before and RED after (median 0.9905, the check's lower bound is one): the unsettled
cycle (Update 11) lands a year lower. Not loosened; not resolved.

## Update 13 (PM): the staple's producers cobweb with period two

`sim/tests/test_complaint_651_wage_step_gain.py` `test_labourer_wage_does_not_sawtooth` is an expected failure naming this
complaint: in that fixture the staple's output and price alternate year to year (producers' adaptive expectations,
`producers.next_expectations` with `EXPECTATION_ADJUSTMENT_SHARE` and `OUTPUT_CHANGE_SHARE_PER_YEAR`), the leisure anchor and so
the hours offered follow, and the labourer wage follows them. Trace in 641. It turns into an unexpected success when the
producers' expectations stop alternating.

## Update 14: the staple's period-two cycle is the hours households sell, not the producers' expectations (branch producer-expectations-stable)

Measured on the 651 fixture (`economy_fixture.small_setup()`, one `Economy.step` a year; probes not committed): the staple
producers' plans do not alternate. Planned runs and expected prices move monotonically (`producers.plan` and the expectation
after `next_expectations`, years 0 to 70), while the runs achieved alternate, because the hours hired alternate: hours wanted
exceed hours offered every year, so output is the hours offered over the hours a run takes. The hours offered alternate with
the leisure anchor, `record.leisure_anchor_wage` times the chained price level (`Economy._hour_supply`). That level is last
year's reading, and the staple's price follows the hours worked the same year (income, then demand), so: a high level, fewer
hours offered, less income, a low price and a low level, more hours, and so on. Holding the level at one removed the wage
sawtooth (4 flips in 46 years). Producers on the fixture: price elasticity of supply (plan against a one per cent move of the
expected price, year 20) was 1.7 for the hills farm and 0 for the other two, which plan at what their cash affords; the market
curve (`api.price_response`) gave a price elasticity of demand near 1.8 at a one per cent change in units landed. A plan from
price alone is stable here by Nerlove's condition (the share of last year's surprise folded in is 0.5, and the regressive weight
adds damping); unsold stock and unmet demand enter only through `runs_for_stock` (excess stock) and `ask_raise` (sold out).

Fix: households scale the leisure anchor by a perceived level, the chained level moved part of the way each year
(`market_memory.PERCEIVED_PRICE_LEVEL_SHARE`, a labelled heuristic that retires here; its value equals the producers' share and was
not tuned). Tests: `sim/tests/test_complaint_473_expectation_damping.py` (producer rule on built inputs: an alternating price and a
step; the perceived level on alternating inflation; the anchor reads it). `test_labourer_wage_does_not_sawtooth` is now a plain
test. Before: 10 sign flips of the wage change in the town's labourer market (limit 8.55); after: passes (4 of 56 flips from
year 12; staple price still changes sign most years but the swing is about a third of what it was). Not closed: the ore cycle of
`baseline_fixture` (period near seven years) is not re-measured; `baseline_fixture` `test stocks are not eaten through` fails before
(metal_kg) and after (ore_kg), unrelated to this change.

## Update 15 (PM): no one grows wheat at Rome's opening

`purchase_limited_by_offered_volume_scenario` "the economy offers the staple on the founder's tile" is red: at france_05 no
wheat is offered for five years while its price climbs. The wheat producer stays idle because a run's planned labour and rent
cost more than its revenue, while most farmer hours sit idle and millet and flour supply the grain. Before the held rate (641)
the check passed only on leftover stock. A staple whose producers cannot cover labour and rent at the opening, with farm
hours idle, is the opening's prices and wages failing to meet (this complaint); the check stays red. Command:
(the test was removed from the suite).

## Update 16: the idle wheat producer was charged the rent a mine bids the tile up to (branch wheat-at-the-opening)

Probe (not committed; `sim(civ="rome_100ad", capital=1e12)`, `_step_market()` a year at a time, wrapping `producers.plan`, the wheat producer at
france_05, years 0 to 5; a second wrap of `land_market.clear_land` printed the tile's demands). Before the fix, plan margin per run was
negative every year because of rent, not wages or price:

- Expected wheat price 1.17 rising to 1.50, traded 0.71 to 1.18 (a traded price, not a quote; the expectation sits above it, so no cap holds it down).
- Farmer wage the plan reads, 0.91 falling to 0.61 (the labourer's 0.47 to 0.57): the wage side does move with the idle hours. Labour a run 431 falling to 292
  against revenue 557 rising to 711, so a run pays its labour at every year; with no rent the margin is positive from year 0.
- Rent a run 247 rising to 595; margin -122, -159, -207, -201, -196, -180. Millet, hemp and vegetables were idle for the same reason; opium (a dearer crop a hectare) ran.
- Cause: `land_market.clear_land` charges every use on a tile the tile's differential rent at the hectare-weighted mean value a hectare gives its uses. At
  france_05 year 0 the demands were 229 thousand hectares at a mean value of 3.6 thousand a hectare, of which coal (2.7 thousand hectares at 221 thousand a
  hectare) alone carried the mean: the rent clears at 507 a hectare, and about 140 without coal. Wheat earns about 450 a hectare. A use that earns little a
  hectare was charged what the use that earns most bids the tile up to, and an idle producer asks for no land, so it reads that tile figure.

Fix (`sim/economy/land_market.py`, `land_rents.py`): a use pays the tile's rent in proportion to its own value a hectare over the tile's mean
(`use_rent_per_hectare`); the tile's total, `record.land_rent` and the tenancy and title readers are unchanged. Producers that ask no land this year are
priced at the value their runs would fetch at the prices they expect. `rent_paid_by_tile` now sums each producer's rent a run times its runs. Tests:
`sim/tests/test_economy_land_rent_by_use.py` (the pure rule on built demands: proportion, the mean-valued use pays the tile rent, totals conserved, nothing
asked; `settle_year` on a built record with an idle grain producer next to a mine); `test_state_land_revenue.py` fixtures carry each producer's rent a run.

After (same probe): the wheat producer plans 22 thousand runs in year 0 (rent a run 183), the economy offers 94 thousand tonnes of wheat on the tile and
`purchase_limited_by_offered_volume_scenario` is green. Not settled: the opening now holds 76 million kg of wheat stock at the producer, which
`runs_for_stock` works off (no runs in years 1 to 5 although the margin is positive), and the price of wheat there is 92 falling 30 per cent a year to 17
while millet is 0.3 and bread 0.12; a price that high for a good whose labour cost is about a coin a kg is the sold-out ask raise and the spin-up cycle (this
complaint), not a price the rent produces. Entrants (`entry_trial`, `location`) still read the tile rent, not a use's share.

Slow topics (`--jobs 2`): `farm_land_quality_scenario`, `opening_floor_and_thin_trades`, `opening_consistency`, `opening_basket_agrees_scenario`,
`price_over_making_cost_band_validation` (red after Update 12, now green) and `land_tile_partition_invariance` green. `baseline_fixture` "stocks are not eaten
through" (ore_kg) fails before and after, as noted in Update 14.

### Update 16 (later): the 92 a kg was a remembered bid ceiling blended with a sliver of trade

Traced with the spin-up uncached (probe not committed: `port_year.SPIN_UP_CACHE_DIRECTORY` set to a temporary directory, wrapping `producers.plan`
and `unsold_search.clear_with_search` for wheat at france_05). The parent's 0.71 was a `cost_covering` quote on a market where nothing traded and the
producer held no stock, not a price. With wheat running, the spin-up cobwebs: year 1 plans the plant's whole capacity at the opening estimate (238 million kg
held after it), the price falls to 0.1, no one plans in year 4 (stock gone), a buyer's ceiling of 130 is remembered as a `best_unfilled_bid`, year 5 plans
231 thousand runs. The opening year then cleared 1.5 thousand kg of 94 million at 13 a kg, and the remembered price moved from the ceiling toward 13 by the
share of a usual volume that sliver was (`year_goods.remembered_price`): 92, then 65 and 48 in the next years, while the market itself cleared at 13, 8.7 and 3.3.
The ask path is not a raise: the producer holds stock, `ask_raise.sold_out_outputs` is empty for it, its reservation is the holding reservation and the unsold
search brings it to its queue-held floor.

Fix: a trade replaces a remembered quote whole (`year_goods.price_after_trade`; `record.memory.quote_kinds` says which), since no one paid a quote and the volume
weight is for blending traded prices. Tests: `test_economy_year_goods.py` `PriceAfterTradeTests`. Wheat at france_05 after, price at the year's plan, years 0 to 5:
2.28, 2.17, 0.75, 0.46, 0.84 and 0.84 after; stock at the producer 76, 75, 48, 25, 0 million kg. `purchase_limited_by_offered_volume_scenario`,
`price_over_making_cost_band_validation` green, quick tier green. The spin-up's own cobweb (a plant planned at capacity on the opening estimate) is this complaint.

### Update 16 (entrants): a newcomer prices a site at its own use's rent (branch entrant-use-rent)

Entrants (`entry_trial.recipes_by_cost`, `location._tile_part`, `entry.entry_plans` through `entry_year`) read the tile's mean rent; they now read
`entrant_rent.site_rent_per_run`, which applies `land_market.use_rent_per_hectare` to the newcomer's expected value a hectare (its outputs at the prices
the market shows it, times the site's yield, over the land a run takes). `settle_year` keeps the tile's mean value on `record.land_mean_value` for it.
Tests: `sim/tests/test_economy_entrant_rent.py` (a grain entrant beside a mine pays its own rent; a use at the tile mean pays the tile rent; siting picks
the tile where its own use's rent is lowest, and the mean-rent reading would pick another). Quick tier green; `firm_count_whole_game_scenario`,
`firm_borrows_to_enter_scenario`, `purchase_limited_by_offered_volume_scenario` green with `--slow --jobs 1`.

## Update 17: the first year's plan starts from the stationary runs, not the plant (branch spin-up-plans-from-demand)

Where capacity was read: `producers.plan` bounds a producer's runs by `capacity_runs * share_working` and `within_a_years_change`, which for a producer
with `last_runs < 0` (its first year) returned the runs unchanged, so only the plant, cash and `runs_for_stock` bound them. The opening sizes the plant at
the stationary runs times the spare share over the share that works (`opening._add_producers`) and keeps the stationary runs in `expected_sales`, but
nothing in the first plan read them.

Fix (`producers.within_a_years_change`): a producer in its first year plans at most its `expected_sales` (the stationary runs) when it has one; with
none it plans from its expectation as before. Tests (the file `test_economy_first_year_plans_from_stationary.py` is no longer in `sim/tests/`; `ls sim/tests | grep stationary` lists what is; it covered: a stationary quantity below capacity is
planned; none plans from expectation; one above capacity does not lift the plant; after the first year the cap is gone).

Measured with the spin-up uncached (`ROME_CACHE_DIR` empty; probe not committed, `economy_api.blank_economy` + `begin_spin_up` + `step`, Rome, years 1 to 6),
national figures, runs last year / price:
- wheat: the first plan was already under the stationary runs (1.98 million of 3.0 million; the 1.26 million of Update 16 was before the rent fix), so the
  cap does not bind and wheat is unchanged: stock after year 1 is 694 million kg before and 698 million after, price 2.15 and 2.49, then 0.25 and 0.23 in year 2.
  The stock is not planned capacity: year 1 sells nothing (goods made in a year are offered in the next) and years 2 and 3 sell 172 and 42 million kg
  against an opening demand of 660 million, so the transient is the households' settling spend, not the plan.
- bronze: year 1 runs 13.5 thousand before, 12.3 thousand after (the stationary runs; capacity 24 thousand); stock 13.5 and 12.3 million kg; shown over cost
  1.00, 6.38, 12.37, 30.6, 8.6, 7.6 before and 1.00, 8.12, 14.77, 33.4, 8.85, 8.28 after. The opening's first-year price over making cost is 1.00 both ways.
- iron bar: year 1 runs 27.1 thousand both ways (stationary 44 thousand); price 5.44 and 5.90.

So the premise that the first year plans capacity does not hold at this commit for these goods; the cap is correct and tested but moves bronze by a tenth.
The cobweb comes from the demand side of the spin-up. Slow topics: `economy_bronze_market_price`, `price_over_making_cost_band_validation`,
`staff_closure_reopening_scenario`, `purchase_limited_by_offered_volume_scenario` green; `baseline_fixture` "stocks are not eaten through" red before (ore_kg)
and after (metal_kg). Quick tier: `economy_service_lives` "a year of cash shortage sells at most a third of the stock" goes red; it is phase-sensitive
(spin-up lengths 56, 58, 60, 62, 64 and 70 years: base fails at 56 and 62, with the change at 56, 58, 60, 62 and 70) because the fixture swings for decades (398).

PM note on Update 17: the first-year cap on stationary quantities (branch `spin-up-plans-from-demand`, commit 7175c621) was
not merged. It barely binds at this commit, so it does not move the transient, and it shifts the phase of a fixture that
swings for decades. The lead to follow is the demand side named above: nothing sells in the first year because goods made in
a year are offered the next, and the households' settling spend is what the cobweb starts from.

## Update 18: the first year's demand side, measured; two opening rules disagree with year one and no fix lands yet (branch spin-up-demand-side)

Measured with the spin-up uncached (`ROME_CACHE_DIR` an empty directory; scratch probe, not committed: `economy_api.blank_economy` + `begin_spin_up` + `step`
for seven years, wrapping `households_orders.goods_orders`, `producers.plan` and the ledger's clearings), Rome, national figures, millions of kg
unless stated. Each year, wheat: made, sold, stock at the year's end, price.

| year | made | sold | stock | price |
|---|---|---|---|---|
| 1 | 787 | 0 | 694 | 2.15 |
| 2 | 1 | 250 | 411 | 0.23 |
| 3 | 3 | 131 | 262 | 0.38 |
| 4 | 3 | 2.5 | 242 | 0.41 |
| 5 | 92 | 4.9 | 296 | 1.83 |
| 6 | 9 | 176 | 118 | 0.78 |
| 7 | 0 | 23 | 88 | 1.25 |

**The households' spend is not what is short.** Household income swings by half and back (year 1 about 2.7e10 coin, year 2 1.4e10, year 3 3.5e10, year 4
1.3e10) because wages follow the producers' plans, which follow last year's prices; but households hold cash of the order of a year's income and their
bids sum to all of that cash, while wheat is a few percent of what they would spend. The spending band does not bind (`expected_spending` is zero in year
1, and `smooth_rise` is off in the spin-up), no food is met from own plots (`grown_own` is zero), and the bids are not under the asks (the one buyer's
ceiling is above the reservation). The wheat buyers are not households at all.

**Who buys wheat.** Households bid for no wheat in years 1 and 2: every cohort's `milled_grains` holds wheat and millet, so its food bids go to flour and
bread. The only user of wheat that works is the starch maker, and in year 1 it opens holding a year of wheat (`opening._stock_producers_with_inputs`),
so it bids for none: the farmers' whole year piles up unsold (694 of 787). In year 2 the starch maker plans from a lagging expectation (runs fall to about
half its first year's) and buys 250 million kg.

**Timing rule (item 2).** A good made in a year is offered the same year (`year_goods._produce_and_offer` produces, then offers the stock), and goods clear in
input-depth order, so an input is bought and used in the year it is made. "Made in a year, offered the next" is true only of an input the user already
holds at the opening, which is the seed above: the opening carries a year of inputs *and* the makers make a year, a year of the intermediate goods more
than the stationary solve has (that solve has each year's output meet the year's use, nothing in store at the start). Households eat in year 1 from what is
made in year 1 (flour and bread sold, from the seeded stock of inputs), so the first year's food is not the problem.

**Opening against year one, found by reading the opening.** The opening's final demand is solved with every cohort's `milled_grains` empty and no household
work hired (`opening._opening_bids` takes `cohort_basket` before `opening_leisure.seed`, via `household_work_year.decide`, sets them). Opening demand for
wheat is 660 million kg and for millet 1.2e10 kg (households grinding by hand), with no hired domestic service; one economy-step later every cohort buys
both grains milled and hires 468 hours a person. So the wheat farmers are sized for 660 million kg that no household bids for, and the whole of the
household-work hiring (over half of year 1's household budget) is demand the opening never sized labour for.

Tried and not landed (patches kept in the scratchpad, not committed):
- Dropping the input seed for an input whose maker is opened and clears before the user works (a plain function over recipes and the clearing order; its
  rule test passes, the existing expected-failure test `test_a_smelter_does_not_open_holding_ore_the_miners_sell_it_in_year_zero` turns green). Rome year 1:
  wheat made falls to 319 million and the wheat market leaves 113 million kg unmet (the chain's later stages are not ready), then wheat sold is 303, 32, 10; the
  quick tier fails four checks of the small fixture (`economy_vessel_price_fixture` twice, `complaint_651_wage_step_gain`, `economy_tax_farming`): the
  fixture's dug input cobwebs once it is bought in year 0 (the vessel price reaches more than two orders of magnitude above its opening price in year 23).
- Solving the opening's second pass with the cohorts' year-one plans (`household_work_year.plans` read from the first pass, put on the cohorts before the
  income and demand solve). With both the milled grains and the hired work: the hired work asks for more hours than there are, the opening's labour fit
  drops the bakers (bread demand 9 billion kg, no bread producer opened), year 1 bread is not sold. With the milled grains alone (quick tier green, rule
  tests pass): wheat demand at the opening is zero, bread is sold in year 1, wheat price stays between 0.84 and 2.15 instead of 0.23 and 2.15, but wheat
  sold is 0, 402, 37, 39, 2.6, 7.9, 10.8 with stock 462, 102, 174, 200, 182, 165, 142. Bronze over cost: 1.0, 7.8, 13.7, 31.0, 9.3, 7.6, 4.0 before and
  1.0, 11.4, 20.1, 50.2, 4.0, 2.4, 1.05 after. Slow topics (the test was removed from the suite):
  at the parent `baseline_fixture` (stocks are not eaten through, ore), the bronze band (`price_over_making_cost_band_validation`, shown over cost worst 11.1)
  and "the typical traded good sells at no less than its cost of making" (0.9987) are red; with the grain plan the same band check is red at worst 32.7, the
  typical-good check is green, baseline_fixture stays red. The band is worse, not better, so it was not committed.

What this leaves: the cobweb's starting point is not the households' settling spend but two opening rules that disagree with the first year (the intermediate
input seed, and the final demand solved before the households' grinding and hiring choices). Both need the opening solved together with them: sizing labour
for the household work the households hire (Complaint 645's decision postdates the opening solve), then carrying the intermediate stock only for what a
cycle cannot buy in time. The input-seed removal wants a fix for the small fixture's dug-input cobweb first (the input's price swings once it is traded in
year 0), which is the open item in `test_opening_input_stocks`.

## Update 19: the opening solved with its households' first-year choices (branch opening-with-household-choices)

The two disagreements Update 18 named between the opening and year one were the households' choices: which grains they buy milled and which hours of
household work they hire. The opening (`opening.open_economy`) now solves to a fixed point with them (`opening_plans.py`): a solve is read by its own
households (`household_work_year.plans`, at the solve's prices, wages and workforce), the plans are put on the cohorts (`hired_work_per_person`,
`milled_grains`) and the opening is solved again, until the cohorts hold what they then plan (`opening_plans.settle`; bounded, a choice that cycles stops
at the bound). The money-replacement solve is kept: the first solve gives the replacement, later solves reuse it.

- Grain: a cohort that buys a grain milled no longer bids for it in the opening's final demand, so the wheat farmers are sized for the millers' wheat and the
  starch maker, not for demand nobody bids.
- Hired work: with the cohorts' hired hours as the floor of the household-work need, the final demand holds domestic service, which the input-output solve
  covers like any good made from hours (a recipe of servants' hours), and the workforce is sized to it.
- The hands: the earlier attempt dropped the bakers. The cause was placement, not the hours in total: the servants were placed first (a final good is placed
  before the recipes that feed it), took their share of every tile's hands, and `location_inputs.place_oriented` then found no hands left for a processor
  tied to its input's site (brick for the bakers' oven, then everything that cascades from it in `opening_runs.fit_to_supply`), so those producers were
  dropped. Now a service made from hours alone is placed last (`opening._only_hands`), and the hours a market area's households would hire are held to the hands
  its tiles have left after the other producers' expected hours (`opening_plans.hands_left_by_tile`). Where they would take more, the area's price of an hour
  hired rises until hiring falls (`households_work.service_price_that_fits`: the household whose hour is worth least stops hiring first); the opening posts
  that price in the service's market (`opening_plans.post_service_prices`), so year one's choice (`household_work_year.decide`) is the opening's. No producer
  is dropped to fit. The area, not the tile, is the market (the service's market areas span several tiles).

Tests (the file `test_economy_opening_household_plans.py` is no longer in `sim/tests/`; it covered: a solved opening's grain demand is what its households buy at its prices, flour price high and
low; its cohorts hold what its households choose; the hired hours are service demand, servant hours in the producers and servants in the workforce; where
hands are short the posted price rises, hiring falls and no other producer is dropped; the rationing rule; the placement order; the fixed point on built
callables, including a cycle). The four checks on a built economy fail with the opening solved once as before.

Measured with the spin-up uncached (`ROME_CACHE_DIR` an empty directory; scratch probe, not committed, as in Update 18, `economy_api.blank_economy` +
`begin_spin_up` + `step`, Rome, years 1 to 7), national figures, millions of kg:

| year | wheat made before/after | sold | stock | price |
|---|---|---|---|---|
| 1 | 787 / 598 | 0 / 0 | 694 / 524 | 2.15 / 2.15 |
| 2 | 1.1 / 15 | 250 / 522 | 411 / 34 | 0.25 / 1.63 |
| 3 | 3.5 / 1.4 | 148 / 12 | 246 / 28 | 0.54 / 1.87 |
| 4 | 3.4 / 0.05 | 0.8 / 0.02 | 229 / 26 | 0.92 / 2.60 |
| 5 | 92 / 6.9 | 20 / 0.0005 | 270 / 30 | 1.81 / 2.34 |
| 6 | 9.3 / 0.9 | 36 / 0.07 | 223 / 28 | 1.56 / 2.18 |
| 7 | 0.01 / 0.002 | 52 / 4.0 | 158 / 23 | 0.90 / 2.13 |

- The opening's household-work hours: before, none hired in the solve and up to 7.8e10 hours done by hand (all grain ground by hand); one step later every
  cohort hires all 5.7e10 hours. After, the solve holds 5.6e10 hours hired and 1.5e9 done by the households themselves; the step's choice is the same.
- Bread: the opening's demand (`record.opening_demand`) is 4.5e9 kg before and 9.3e9 after; bread sells in year 1 both ways (601 and 2100 million kg) and
  after it the unmet floor stays of the same order, 2 to 3 thousand million kg a year, so the bakers are placed and still short in the later years.
- Bronze shown over making cost, years 1 to 7: before 1.00, 6.34, 12.18, 30.08, 10.04, 7.91, 3.78; after 1.00, 4.28, 13.92, 0.42, 5.71, 7.80, 6.18. The 0.42 is
  year 4's cost, not its price: the live copper price in the cost reads 208 that year (shown 87); the peak over the seven years is 13.9 against 30.1.

Wheat no longer piles a year's surplus into a stock that then drains over decades (stock after year 2 is 34 million kg, not 411) and its price stays between
1.6 and 2.6 instead of 0.25 and 2.15. Wheat sold is almost nothing from year 3 on (its only user in the opening is the starch maker, since the households'
flour is milled from millet by the recipe the opening chose); the cause is not traced here, and the wheat made after year 2 is correspondingly small. The
intermediate-input seed (`opening._stock_producers_with_inputs`) is left alone, as Update 18 asks, and the chains' cobweb after year one is still open.

Topics: quick tier green; `economy_bronze_market_price`, `price_over_making_cost_band_validation`, `purchase_limited_by_offered_volume_scenario`,
`opening_consistency`, `opening_basket_agrees_scenario`, `economy_vessel_price_fixture` green with `--slow --jobs 1 --topic-seconds 290`.

## Update 20 (PM): after the opening solved with household choices, markets thin out

Two fix groups after 31b70bc5 found the same pattern: coal sells almost nothing in nearly every market area after the opening
(producers fell by about a fifth while coal demand rose about fourfold), wheat sells almost nothing from year three (Update 19's
table), and skilled pay rose several times (the mint's furnacemen and engravers). Several founder scenarios now pick a good
or project the opening still trades so their own subject stays testable. The leading suspect is the household-service hiring
(645, last section): domestic service near half the opening basket draws hands and income away from goods. Re-measure coal and
wheat volumes after 645's hiring fix before tracing further.

## Update 21: the opening's income is where households stop saving, not where a pass bound stops (branch opening-income-fixed-point)

The income the opening pays was whatever 60 passes of income-into-demand reached (about 0.99 to the 60th of the ceiling).
Measured on Rome: demand over income is one below a kink at about 0.48 of the ceiling (first solve, no replacement) and
falls above it, because households' saving has no user in the final demand (607). The income is now the largest at which
households save nothing net (`opening_income.settled_income_per_head`, a root find; 497 Round 10). First solve: 443 a head
(0.477 of the ceiling) against 467 (about 0.50) from the pass bound; the final solve, which carries the coin metal's
replacement as demand that is not from households' income, 748 against 752 (0.806 against 0.810 of the ceiling).

Spin-up years 1 to 7 (scratch probe, not committed; unskilled wage, wheat, coal, bronze price), before then after:
wage 0.726, 0.668, 0.635, 0.553, 0.422, 0.386, 0.380 then 0.719, 0.659, 0.630, 0.511, 0.414, 0.379, 0.374; wheat 2.139, 1.511,
1.685, 1.433, 1.404, 1.321, 1.280 then 2.152, 1.424, 1.683, 1.421, 1.383, 1.292, 1.314; coal 0.0146, 0.0323, 0.0652, 0.1230,
0.1528, 0.1592, 0.1731 then 0.0146, 0.0319, 0.0632, 0.1161, 0.1427, 0.1787, 0.1984; bronze 4.79, 43.8, 121.3, 96.3, 113.0,
135.4, 132.6 then 4.79, 29.0, 35.3, 44.5, 77.7, 137.6, 140.9. The drift is unchanged in kind (wage falls by half over the years,
bronze is thin and jumps): the income was never what set it. Still open: counting the demand that matches households'
saving (607) would raise the income at which they stop saving.

Measure the settling and the feasibility of the books with `python3 sim/simulator.py spin-up-trace` (Rome, whole length) and `python3 sim/simulator.py economy-check`; the slow tests that asserted them (baseline_fixture, baseline_rome, baseline_rome_full_length) were removed in Complaint 640's pass because a failure named a series, not a function. The rules they used are tested in test_baseline_checks_rules and test_series_settling_rule.

Two whole-game validations were deleted in the rule-test pass (they read the unsettled opening and could not name a rule): `real_output_baseline` (output per head stays within a factor of two of the baseline year, and goods far from baseline carry at most a tenth of the basket) and `real_output_validation` (a 40 percent mortality shock leaves output per head within a quarter of an undisturbed run). The arithmetic and wiring they stood for are in `test_real_output_measure` and `test_real_output_wiring`. No simulator command measures either relationship yet; `python3 sim/simulator.py baseline-ensemble rome_100ad` stores the population and wage distributions only, so output per head belongs in it when 473 closes.

## Test migration (slow-test overhaul)

`test_opening_floor_and_thin_trades` is deleted: it read one year of an unsettled economy and could not name the function that broke.
The relationships it read are measured by `python3 sim/simulator.py opening-checks` (wage over the household floor, prices over
making cost), `python3 sim/simulator.py economy-check --civs rome_100ad --years 1` (staple price over labour cost, hunger) and
`python3 sim/simulator.py spin-up-trace`: household floors over the food floor, a trade's heading wage over its trained substitute, a
good's price drift against wheat, and the mason share of the opening workforce (the opening-stock rules are in
`test_economy_service_lives` and `test_durable_stationary_state`). The ceiling rule is in `test_labour_core_skilled_ceiling`.

The one-year Rome baseline of idle labour, wage over the unskilled floor and hunger share (`test_labour_margins_baseline_validation`) read an
unsettled opening economy and is deleted; `python3 sim/simulator.py economy-check --civs rome_100ad --years 1` prints the same figures.

Test migration (rule-tests-05): `firm_count_whole_game_scenario` is deleted (the count settling and not overshooting over 30 years read an unsettled economy; the rules are test_firm_count_from_costs and test_entry_gross_rule). No simulator command prints firm counts by market size; `python3 sim/simulator.py economy-check --years 30` is the nearest measure of the agent economy.

Test migration (rule-tests-07): `home_cargo_price_scenario` is deleted (after one year of the Rome agent economy the zero-cargo quote disagrees with the market price for one good, which reads the unsettled opening and cannot name a function; the quote arithmetic is in `test_home_cargo_price`, the ship booking in `test_trader_cargo_settlement`). `python3 sim/simulator.py economy-check --civs rome_100ad --years 1` prints the home prices to compare against.

Test migration (rule-tests-07): `granary_persistence_validation` is deleted (an unshocked Rome century ending above half its start population, and a mean nutrition ratio between 0.9 and 1.1, read one seed of the unsettled opening and could not name a rule; the granary rules are in `test_granary_persistence`). `python3 sim/simulator.py baseline-ensemble rome_100ad` stores the population distribution for the same century; it does not yet store the mean nutrition ratio.

Test migration (rule-tests-02): `complaint_467_trades_open_to_the_jobs` is deleted (the opening workforce of each skilled trade against the first year's producer, mint and state wage bids, with an unsourced three-times limit, read one year of an unsettled opening and could not name a function). No simulator command prints workforce hours against bid hours by trade yet; `python3 sim/simulator.py economy-check --civs rome_100ad --years 1` prints idle labour and the wage over the floor, the nearest measure.

Test migration (rule-tests-16): `spin_up_money_supply_full_length` (the money stock keeping up with wear over forty spun-up years)
is deleted: it read an unsettled economy, was red on main by design and could not name the function that broke. `python3
sim/simulator.py opening-checks` (money against coin wear) and `python3 sim/simulator.py spin-up-trace` print the same relationship.
The short part, `spin_up_money_supply`, is replaced by `test_money_year_figures_rule` (the money columns are read from the audit's
edges, the saved spin-up result is read back); that a few spun-up years' stock changes by struck less worn is the money audit's
identity over a whole economy step and is measured by `spin-up-trace`'s `change`, `struck` and `wear` columns. The staffing
scenarios `staff_closure_reopening_scenario` (twelve years of twenty-five concerns, auto-hire reopening every closure free staff could
run; red on main) and `sited_ore_price_over_cost_validation` (519) are deleted for the same reason: no command prints the
reopening count over years; `python3 sim/simulator.py economy-check --civs norse_900ad --years 12` is the nearest measure.

- Whole-economy claims no longer unit tests (one function per test): more money against the same goods raises the price level, a state that prints raises prices, money is conserved year after year, and a lean-seam mine leaves. Measure them with `python3 sim/simulator.py economy-check` and `python3 sim/simulator.py spin-up-trace`.

Test migration (rule-tests-04): `economy_money_regimes` and `economy_money_regimes_norse` are deleted. The price-level-rises-with-metal
checks read this unsettled economy; `python3 sim/simulator.py spin-up-trace --civ norse_900ad --years 7` prints the basket price level
by year. The money-stock and mint rules are `test_mint_settles_by_regime` and `test_economy_mint`; the transmission to prices is
`test_money_reaches_prices`.

Test migration (rule-tests-04): `economy_innovator_pricing` (a near-zero-cost entrant: price starts near the incumbents', falls as the entrant grows, the
entrant's takings within the demand ceiling; two further bounds were expected failures) and `economy_supply_collapse_scenario` (a stationary fixture's
staple runs not falling by more than a bound over five years) are deleted: each read a year loop of the whole fixture economy and could not name the function
that moved. No simulator command prints either; `python3 sim/simulator.py economy-check --civs rome_100ad --years 6` prints the staple and metal price
volatility from the opening. The rules the supply-collapse test joined are `test_economy_stock_drawdown`, `test_economy_idle_capacity_life`,
`test_economy_input_ceiling_share` and `test_economy_ask_band_chain`.

Whole-game relationship checks deleted (Complaint 640): the five `full_length_opening_checks_<civilisation>` topics (red on main) asserted price over making cost, wage over floor, money against wear and spin-up settled on each full-length opening, which cannot name a function. `python3 sim/simulator.py opening-checks` prints the same relationships for every civilisation; the known failures stay tabled in `sim/tests/full_length_opening_support.py` (`EXPECTED_FAILURES`).

The whole-economy stepped-year checks of the stationary fixture (every year within the settling bounds, hours hired holding, ore price, the mint against wear, the first-year wage move against excess hours, households' cash against producers') left the unit tests with `test_opening_stationary_rules`, which now holds only the rules (`opening_stationary.solve`, `opening_leisure.anchors`). Measure the settling claims with `python3 sim/simulator.py spin-up-trace`.

## Update 8: the mint was last in the queue, so cheap bullion never reached it (branch mint-replaces-wear)

Cause of the draining money stock: the mint's bid was served after every other buyer of the metal (`MINT_PRIORITY`), and a
seller sells at its own ask, so when asks fell with the price level the other buyers of the metal (cheap metal draws more
demand) took all of it and the mint, which would pay far more than the ask, was rationed to nothing. The profit test was
sound (`maximum_price` is the mint price; the ask fell well below it). Now the mint is served first among buyers at or below
its price, and its yearly capacity counts the wear of the coin it strikes (`yearly_monetisation`). Measure:
`python3 sim/simulator.py spin-up-trace --fixture small --years 40` (and `--fixture stationary`), columns `money_supply`.
Still short on the small fixture in the middle years: the metal's makers supply less than the mint bids for (producers' side).

## Update 22: producers, rent, credit, goods and labour rules of branch labor-market-economy-stability

What the code does now, each rule with its owner:
- Producers pay out cash above next year's needs (`firm_finance.cash_to_keep`, `excess_cash`, `payout`, called from `firm_year.py`).
- Land rent counts in producers' running costs (rent is posted by `sim/economy/year_ledger_postings.py`), and a producer whose remembered earnings are negative closes
  that share of its capacity, at most a year's change in output (`producer_losses.shed_share`, used by `producers_close.close_year`).
- Sellers turned away from by buyers raise their asks within the year to where requests meet the stock (`demand_search.raise_asks`,
  `unsold_search.raise_sold_out`); a sold-out seller's expectation is not pulled to cost (`ask_adjust.regressive_weight`) and a crowd
  asks its expected price for stock it expects to sell (`seller_offers.expected_ask`).
- The logit allocation redirects rationed buyers round after round until no stock is reachable (`goods_market_logit.allocate`).
- Households' expected spending counts what they planned (`durable_stock.update_expected_spending`), and they read share wealth as
  recorded at the last close (`households_buffer_stock.share_wealth_carried`).
- The mint is served first among the metal's buyers (`mint.MINT_PRIORITY`; see Update 8 above).
- The opening sets land rent by the year's own rule and covers it in prices and property income (`opening_rent.py`).
- Credit rations by quantity at the lenders' ask and cuts a priced-out request to what its pledge bears (641).
- Labour: offers rise each search round while vacancies stay open, a searcher asks no more than the best posted offer, the import-wage bound
  weighs the hours that can be fetched, graduation income counts the chance of finding work (`sim/labour/market/DESIGN.md`).

The households' spending-cap merge was titled as ending the stationary fixture's late crash; it did not. The labour-core, rent, shedding
and switching merges after it did.

Measured on the fixtures with `python3 sim/simulator.py spin-up-trace --fixture stationary --years 50`: hunger is zero and idle hours
are small after the first years, but the spin-up does not settle: the basket price level, the unskilled wage and the money supply
still drift downward over the fifty years. `--fixture small --years 50`: the price level and wage keep falling to the end and the idle
hours shrink as the wage falls, so it is not settled either. Not re-measured on a civilisation
(`spin-up-trace --civ rome_100ad --years 60` is the remaining gate). The status stays `partly`.

## Update 23: the mint buys at the mint price and holds its coin metal unless bullion fetches parity (branch mint-pays-mint-price)

Chain, stationary fixture (`sim/economy/fixture_setups.py`: parity 100, mint price 95): the market settles every sale at its mean price, so the mint
paid the metal's sellers the market price (about 60 to 88) and the issuer kept the whole gap to parity as seigniorage; the makers' expected price
followed the market, so smelting shrank as ore cost rose. The mint also offered its whole coin metal at parity into the same market; the logit
choice gave that offer a share of the ornament buyers, and the mint's sales washed against its purchases (net intake negative in some years, about 270 kg sold in year 54).
Now `mint_price.pay_top_ups` adds, after the markets, the gap between the mint price and the settled price on what the mint bought, shared among the
metal's sellers by what they sold (seigniorage is then the mint's charge only), and the mint offers its metal only while bullion's remembered price is at least parity
(`mint_price.melting_pays`). Measure: `simulator.py spin-up-trace --fixture stationary --years 60` with the money columns `wear`, `struck`.

## Update 24: the money flow, not the money stock, contracts; the own-plot leak and the mint (branch spin-up-settles)

Measured with a scratch probe that replays `spin_up_run.spin_up` without its early stop and writes each year's settle
quantities, money by holder and watched prices (no committed command prints them by spin-up year; the shipped
`openings/opening_traces/` hold the first stage's money by holder for each civilisation).

What drove the drift, in every base civilisation: the money stock stays roughly constant while coin moves from producers to
households year after year; producers plan runs from their cash, so they shrink, hire less and price lower, and households'
spending follows their falling income. Two ablations on Norse changed nothing: households spending far more of their cash
(`CARROL_CONSUMPTION_PARAMETER`), and producers keeping their excess cash (`firm_finance.payout`). The budget was not what
bound: money reached households and did not come back as bids.

Fixed here:
- **Floors the own plot grew are met before the budget is sized** (`households_orders_kernel._met`, `households_orders.goods_orders(grown_units=)`,
  `household_grown_floors.met_shares`; test `test_household_grown_floor_budget`). The budget was sized as if the household bought its whole
  food floor, and only afterwards were the floors its plot grew cut from its bids; the money that cut freed was neither bid nor offered to
  lenders. On Norse this took the run from collapsing output to output that holds.
- **A change in unmet need is read against the economy's food need** (`spin_up_state.food_floor_units`, `spin_up_gap.state_gaps`;
  `SPIN_UP_UNMET_FLOOR` retired). A shortfall appearing on one tile read as a swing of many thousand times against a floor of one food unit.
- **The mint bids where its metal trades, and weighed metal is paid at parity** (`mint_bid_split.split_bid`, `mint_price.paid_in_metal`,
  `paid_price`; test `test_mint_bid_split`). The bid was split by tile count, so part of it sat in an area with no metal; and a weighed-metal
  economy paid sellers their ask while its own design (`currency.has_mint`, `mint.py` docstrings) says the metal is exchanged at parity. Norse
  now strikes about what wears away (`opening-checks --civs norse_900ad`: `money_against_wear` passes).
- **A holding decayed to residue is removed, and a residue is not an offer** (`stock_residue.STOCK_RESIDUE_UNITS`, `wear_kernels.loss_moves`,
  `inventory._moves`, the on-offer tests in `goods_table_quotes` and `goods_clearing_kernel`). A share-based loss never reaches zero, and a market
  whose only offer was that residue quoted a phantom low ask; households bid on it, the unfilled bid hid the quote, and the next year it
  returned: a period-2 cycle through the food floor cost and the wage floor (`labour_ask_floor.ask_floor_by_tile`). Without it households see
  the real food prices, so measured hunger is higher and honest.
- **The mint sells only the backing above the cash holders want** (`mint.cash_wanted`, `mint.meltable_metal`): striking was already
  limited to what holders want to add; selling (melting) offered the whole stock at parity, so in Mexica, whose money is cacao,
  households ate the money's backing.
- **Producers plan, close and price an unpriced tool at its fallback cost** (`plan_wear.covered_input_bill`, `close_kernel`,
  `grid_wear`, `entry_kernels.pays_after_recovery`): placement and entry alone were not enough, since placed producers then
  planned zero runs and the close counted them at an infinite cost.
- **An unpriced tool is costed by its fallback chain in placement and entry** (`tool_fallback.wear_cost_per_run`, `unit_cost.input_cost_per_run`,
  `entry_wear_kernel`; test `test_tool_wear_cost`). A tool with no price made every cost rule infinite, so a recipe was never placed or entered,
  though producers' own planning already covers a missing tool by the next tool or by hand (`tool_fallback.draws`). In Mexica, with no iron,
  that kept cacao (the money's backing good) and the other recipes using iron tools from ever being made. One Norse run after it showed a steady price level and smaller gaps; the ensemble below shows that was one calm draw.

Tried and not merged (branches pushed for reference):
- `smooth-base-rate`: the rate's declared partial adjustment (`RATE_ADJUSTMENT_SHARE_PER_YEAR`) is overridden in nearly every year by three
  snaps in `clearing_kernel.settled_rate`, and the target is one marginal lender's ask (`MATERIAL_LENDER_SHARE`). Removing the snaps and
  taking the supply and demand crossing smooths the rate but, in a deflating economy, walks it toward a near-zero lowest ask and lends
  nothing while it sits below every ask. Re-try once the economy no longer deflates.
- `opening-grown-floor-budget`: the same own-plot rule in the opening. The opening's silver and ore demand rested on a purse equal to the
  money the old late cut freed; without it households' store-of-value bids collapse and the ore and silver markets stop trading at the
  opening. Needs a derived opening cash and saving (Complaints 545, 607); see `Complaints/reports/473-owner-questions.md`.
- `no-dust-offers` (first version, before the mint fix): measured worse on one Norse run; re-measured on the head with the mint fix it
  removed the alternation in every good and tile checked, and it is merged above.
- `fleet-wanted-follows-routes`: merchants' wanted carrier fleet followed last year's route wear whole; smoothed over a service
  life. Not the mover: the buyers of mules and oxen are households, and one England run moved the worst gap to the rate.
- `durable-replacement-steady`: mules and oxen are bought for households' stores of wealth (`households_store.store_bids`, and its
  copies in `households_orders_kernel` and `opening_demand_kernel`), an (S,s) rule that buys nothing while the store holds most of
  its target and the whole gap once it falls below, so the stock drifts for years and one catch-up purchase lands on the producers.
  Buying back each year's wear and closing a shortfall over years settled England's inventories but made one Norse run hungrier;
  not judged on single runs (see the chaos note below).

**Correction on the measurements above.** The before-and-after figures in this update are single trajectories. A four-member
ensemble of the head on Norse (`spin-up-trace --civ norse_900ad --stages --ensemble 4`; members differ only in households' cash at
the rounding level) shows the end gaps spread over large factors between members, the unperturbed member among the calmest, and the
price level still falling over the trimmed stage in every member. So the fixes above stand on their mechanisms and rule tests; what
each did to settling is not established by one run, and the spin-up does not settle on the head.

What still fails, and the evidence:
- The run is chaotic, not only path-sensitive: changing the summation order of the close's input bill (last-digit
  differences in about one in seventy bills, every other bill identical; merge d77138668) moved Norse's inventory and price
  gaps by factors of about three. A single trajectory's last-years gap is therefore mostly noise at this tolerance; see
  `Complaints/reports/473-owner-questions.md` question 1 for a stationarity test over perturbed runs.
- The run is path-sensitive: a small rule change moves the whole trajectory (the dust branch's trimmed-stage wage starts at about twice the
  base's). One run per change is weak evidence; compare several civilisations before merging a rule.
- The remaining movers on Norse are watched goods' prices and inventories with a period-2 or a four-year cycle (fish and steel follow the
  wage floor's swing; mules and oxen follow lumpy merchant fleet buying, `carriage_fleet_book.to_buy`), and a slow fall of the wage while
  idle hours stay above hired hours where the floor binds (`sim/labour/market/asks.py`, `clearing_kernel.py` reservation at the floor).
- **Mexica is worse on this branch than on main**, through the own-plot fix: once households can afford their flexible food,
  part of it goes to cacao (a food and the money's backing good); cacao's price rises above the mint's parity, the mint sells its
  cacao at parity whenever the remembered price is at least parity (`mint_price.melting_pays`, `mint.mint_orders`), households eat
  the money's backing and the money stock falls by most of itself within a decade (`opening-checks --civs mexica_1500` fails the
  staple, sited ores, money against wear and wage over floor checks, which main passed in its last rebuild, Complaint 970). On main
  the leak suppressed that demand. Nothing grows cacao in any spin-up year although the recipe exists, Mexica knows its node and
  about half its tiles have the climate: being traced (placement or entry).
- Mexica after the tool and melt fixes: money against wear passes, but its crops run by hand because a new wooden-tool crew
  never covers its unpractised hours (`practice.recipe_for`), so it never runs and never learns; entry counts nominal idle capacity
  (`entry.gap_beyond_spare`, `entry_margin.gap_at_entry_price`). On main the same crops had no producers at all, so main's Mexica
  checks read cost estimates of goods nobody made. Owner question 6.
- Silver now trades at parity far above its making cost (`price_over_cost_coin_metal`), Complaint 519's question in another form.
- Hunger sits on fertility-0 tiles whose people have no plot and whose markets sell out (`household_hours_year.usable_plot_hours`).

Measure: `python3 sim/simulator.py spin-up-trace --civ <civ> --stages` prints both stages year by year (settle quantities, money by
holder, watched prices) and the gap by quantity over the measured years, with the watched good that moves most;
`python3 sim/simulator.py opening-checks --civs <civ>` reads the opening's own saved `spin_up_result`.

## Update 25: the economy amplified rounding noise; the amplifiers found and made continuous (branch spin-up-settles)

The owner's requirement: a small nudge (iron made dearer) should move each price by its cost share and leave the rest
of the economy close to where it was. Measured with scratch probes (no committed command prints a phase-by-phase
comparison of two economies):
- **The cost calculator meets it.** Halving the bloom recipe's output moves every good's making cost by its iron share
  and nothing else (`notional_kernel.cost_estimates`).
- **The opening solver does not.** The same change applied before the opening re-solves the opening and moves most
  recipes' capacity; the bloom producers' capacity changes many-fold (not traced; `opening.open_economy`).
- **Applied after the opening, the agent economy's first years respond in proportion** (goods with no iron share stay
  within a fraction of a per cent for several years), but two spin-ups whose households' cash differs at the rounding
  level drift apart within a few years: the economy is chaotic.

Amplifiers found by stepping two such spin-ups phase by phase, each replaced by a rule continuous in its inputs:
- **Wage clearing on a step demand** (`sim/labour/market/clearing.py`, `clearing_kernel._supply_target`): each bid's
  tranches wanted all their hours up to their cap, so with supply nearly fixed a sliver of excess demand lifted the
  wage from the reservation to the lowest cap. Each tranche's hours now spread between the caps (the continuous limit
  of `BID_TRANCHES`); the core's wage memory is seeded from the opening wages (`labour_state.seed_opening_wages`), so
  the first year takes the damped move.
- **Entry from residue demand** (`entry.py`, `entry_unmet.py`, the entry kernels): a rounding-sized bid opened a
  producer of rounding-sized capacity that never closed. Entry now needs demand above `STOCK_RESIDUE_UNITS`, and a
  producer below it closes.
- **Trade switching on a threshold** (`sim/labour/market/switching_kernel.band_shares`, `plan_area`): an established
  worker weighed only trades scoring above staying. Every destination now enters one logit with staying; the
  negligible-share redirect is a continuous trim; `PLAN_REUSE_TOLERANCE` is gone. One assertion was loosened:
  `test_labour_core_year`'s steadiness bound on a trade's workforce went from 60 to 80, because under the continuous
  rule the count holds flat near 70 against a target of 30 (steady, but over its target: not traced).
- **Residue bids and a binary "traded" memory** (`opening_demand_kernel.flexible_budget_left`, `year_goods.price_after_trade`,
  `goods_remember_kernel`): a household whose floors took all its cash posted rounding-noise bids, and any trade at
  all replaced a market's remembered quote with the dearest seller's ask. The leftover is now exactly zero, and a
  trade moves the remembered quote by its weight against the market's usual volume.

Measure: `python3 sim/simulator.py spin-up-trace --civ <civ> --stages --ensemble N` (the spread of each end gap across
members that differ at the rounding level). An ensemble with only the first two fixes still spread widely.

## Update 26: one market memory rule pulled every thin market toward its making cost (branch spin-up-settles)

An eight-member Norse ensemble (`python3 sim/simulator.py spin-up-trace --civ norse_900ad --stages --ensemble 8 --jobs 2`)
on each merge since the residue-bid fix showed the price level and the watched prices trending down over the trimmed
stage from the memory-blend merge on; the allocation merge after it changed the trends little. A four-member ensemble
had suggested an output collapse at the head: two of its members collapsed, the eight-member medians do not, so four
members are too few to judge a rule. Memory per replay limits the machine to two replays at a time.

The cause: `market_memory_blend.blended_price` drifted every market toward its target in proportion to the untraded
share of the whole reference volume. A market that traded has no quote, so its target is its making cost, and almost
every market that traded was pulled toward its making cost each year besides the thin-trade rule; costs are read from
the remembered prices of the inputs, so the pull fed on itself. Ensembles on scratch copies of the head: with the drift
off for markets that traded, most of the trend went; without the per-good scale in the reference volume, little of it
went; with the allocation merge reverted, none of it went. The drift now fades as the trade nears
`REPRESENTATIVE_TRADE_SHARE` of the reference volume, as the thin-trade rule does, and stays continuous in the quantity
traded (`test_market_memory_blend`); the ensemble on that rule matched the drift-off one.

Still open: late in the trimmed stage real output and hired hours move by large shares a year in every member, before
and after this fix; that swing, not the trend, is now what keeps `spin_up_settled` failing on Norse.

## Update 27: the continuous memory blend is reverted; Norse's swing is household work (branch spin-up-settles)

**Correction to Update 26.** Its fix (the cost drift fading with the trade) helped Norse but not Han: Han's late-stage
year-to-year moves of hired hours, real output and the price level stayed far above those before the blend. Eight-member
ensembles (`python3 sim/simulator.py spin-up-trace --civ <civ> --stages --ensemble 8 --jobs 2`) on scratch copies of
the head, each with one part changed: reverting the allocation merge, dropping the per-good scale, measuring the
thin-trade rule against the usual volume, a full drift for untraded markets, reverting the store pot, or treating traded
markets as the old rule did each left Han well above the old rule; only the memory files put back whole brought Han
and England near or under the tolerance for those three quantities. The memory is back to the trade-weighted rule (its
remaining step at a sliver of trade stands); the store pot of the blend's merge is kept.

**Norse's swing.** Probes of one spin-up logging every cohort's year (scratch scripts; no committed command splits a
cohort's year into household work, plot, plan and sold hours) show that in Norse's swinging Swedish area household work
takes most of the cohorts' year, and the hours they sell are the small remainder, which reaches zero in several late
years; the fishers' and farmers' output there falls with it. Making the grind-or-buy-milled choice continuous (branch
`grinding-share-continuous`, not merged) did not remove the swing: a smooth move of a large term still wipes out a small
remainder. Halving household work in a scratch copy roughly halved Norse's swing in hired hours and real output, on
either memory rule. Where household work's hours should come from is owner question 7
(`Complaints/reports/473-owner-questions.md`); Norse will not settle without it.

Still open after this: inventory value and the rate move by more than the tolerance in every civilisation measured, and
unmet need in Han.

## Update 28: the rate follows the year's price noise; a continuous inflation reading does not calm it (branch spin-up-settles)

A probe of one England spin-up (scratch scripts) shows the rate is the cheapest lender's ask in every year
(`sim/loans/clearing_kernel.settled_rate` returns `lowest_ask` whenever the sticky move would fall below it, and with
funds far above requests it always does), and that ask is time preference plus the cohorts' expected inflation
(`lender_ask.lowest_ask`), which adapts toward the year's observed inflation (`currency.price_inflation`, a weighted
median of the goods' price ratios). The rate zigzags with observed inflation while the price level falls steadily.
Replacing the median with a weighted trimmed mean, continuous in every ratio and weight (branch `inflation-trimmed-mean`,
not merged), left the rate's late-stage moves as large on England and larger on Han in eight-member ensembles
(`python3 sim/simulator.py spin-up-trace --civ <civ> --stages --ensemble 8 --jobs 2`): the noise is in the middle goods'
prices themselves, so the rate should settle when they do. A four-member Rome ensemble on the head shows the same
pattern as England (inventory value and the rate move most) with larger moves of hired hours and real output.

## Update 29: three traced lumps made continuous; none calmed the quantity it fed (branch spin-up-settles)

Each traced on England with a scratch probe of one spin-up, each made continuous on its own branch (not merged), each
judged on eight-member ensembles of England and Han (`python3 sim/simulator.py spin-up-trace --civ <civ> --stages
--ensemble 8 --jobs 2`) against the head:
- `inflation-trimmed-mean`: observed inflation a weighted trimmed mean, not a weighted median (Update 28). The rate moved
  as much or more.
- `stock-offered-in-tranches`: held stock offered as a staircase of lots of a year's sales, not one lot at one
  reservation. Producers' inventory value moved as much. A probe of the lumpiest producer (a mule maker) showed why:
  its output and asks were smooth, and in many years no household bid at all.
- `durable-demand-continuous`: households' durable bids replace wear and close a declared share of the gap to the
  stock wanted, and a good's affordability falls smoothly with its price (a durable against its service life's budget),
  instead of the whole gap at once and a yes/no gate on one year's budget. Inventory value moved as much on both, and
  Han's hired hours and rate moved far more.

So removing one traced lump moves the year-to-year noise elsewhere rather than removing it; on England, hired hours,
real output and the price level already move by little more than the tolerance while inventory value and the rate move
by many times it. This is evidence for owner question 1 (a stationarity test over an ensemble, rather than a fixed
point of every quantity), not a reason to change the check without the owner.

## Update 30: the owner's answers; twin runs find where differences grow; poaching, household time and servants (branch economy-settles-not-chaotic)

**The owner's answers** (`Complaints/reports/473-owner-questions.md`, top): settled stays a fixed point and the economy
must not be chaotic; fertility 0 is intended; households open at the yearly rule's steady state; questions 4 and 6
follow the real world; shapely goes into `requirements.txt` and there is no setup script; a person's time has one
source of truth.

**How it was measured: twin runs.** Two economies are opened from one setup, the second with households' cash scaled
by a rounding-sized factor, and stepped side by side; after every year the two exported records are compared leaf by
leaf, by record section (`Complaints/reports/473-handoff/probes/twin_probe.py`, read with `show_twin.py`,
`show_states.py` and `show_detail.py`). `late_twin_probe.py` forks the twins from one saved economy late in the
trimmed stage; `phase_probe.py` compares what goes into and comes out of the lending, planning and labour phases of
one year; `hire_probe.py` does the same inside the labour clearing. This names the year, the phase and then the rule in
which a difference first grows, which an ensemble's end gaps cannot. `series_probe.py`, `wage_probe.py` and
`labour_totals_probe.py` log one run year by year (output by good, each labour market's wage rule, the cohorts' hours,
holdings by good, the labour totals). The probes are scratch scripts: run them from a checkout with `PYTHONPATH` set
to it; no committed command prints these figures.

**What the twins showed first.** On England the twins agreed to rounding through the first year and differed by whole
per cents in single outputs in the second. Everything that went into the second year's labour clearing agreed to
rounding; the hours each employer came out with did not, while each market's total was the same.

**Fixed, each with a rule test:**
- **Poaching was a jump at equal standing** (`sim/labour/market/clearing.py` `on_the_job_loss_share`, `poach`; kernel
  `clearing_tail_kernel._poach`; `test_labour_poach_continuous`). A higher employer drew a share of every lower one's
  hours at any gap in standing (its highest bid cap) and none at none, and employers took turns by rank. Employers of
  one trade often stand level, their caps being one figure, so the last digit decided who lost hours. The share now
  rises from nothing with the recruiting premium, and all short employers draw at once from the hours held before any
  moved. Twins forked late in England's trimmed stage (`late_twin_probe.py`) show what it bought: at the head before,
  the difference between them grew several hundredfold a year after its second year; with this fix it grows about
  fourfold a year. That is far slower and still growth: the economy is still chaotic, and a rounding-sized difference
  still becomes a visible one within the length of a spin-up.
- **Household work was counted over two year lengths** (owner question 7; `households_work.hours_per_person_per_year`,
  `EconomySetup.working_days_per_year`; `test_household_time_budget`). The tasks' hours a day were multiplied by the
  civil year and taken out of a labour year that holds working days only. They are now counted over the labour year's
  working days: housework on the other days is done on those days and takes nothing from the hours a household can
  sell or hire out. The household-work need's satiation in `data/world/needs.json` follows.
- **Hiring servants flipped every year** (`household_servants.hired_hours_whole`, `households_work.adjusted_hired_hours`,
  `SERVANT_HIRING_ADJUSTMENT_SHARE_PER_YEAR`). Each cohort chose, on last year's wage and by a steep rule with a cliff
  at its budget, how much household work to hire; a cohort's own work alternated between a large and a small share of
  its year, the hours it sold alternated with it, and so did the wage: the period-two swing of England's hired hours
  and output (traced with `wage_probe.py` and `series_probe.py`: the employers' hours wanted were steady, the hours
  offered were not). The share able to pay now falls smoothly with the budget, and the hours hired move a declared
  share of the way from last year's to the choice each year (the opening takes the choice whole).
- **A durable's purchase was the whole gap to the stock wanted** (`durable_stock.purchase_toward_stock`,
  `households_ability.affordability`; `test_durable_demand_continuous`; the former unmerged `durable-demand-continuous`
  patch). A small change in the flow a household plans moved a year's purchase by about the good's service life times
  as much. England's households hold noric steel worth years of the economy's output, and making it, with its charcoal
  and wood, is most of real output at opening prices; producers' steel piled up and cleared in lumps. Purchases now
  replace wear and close a declared share of the gap, and affordability falls smoothly. Update 29 measured this patch
  as no help; measured again after the two fixes above, it is one (below).
- **The coin-metal check** (owner question 4; `opening_checks.mint_price_over_cost`, `coin_metal_check`;
  `test_opening_check_mint_cover`): for a money paid in metal at a stated price the check asks that the price the mint
  pays covers the metal's making cost, with no ceiling; commodity money keeps the band. Research and sources:
  `Complaints/reports/research-coin-metal-check.md`.

**Measured.** The end gap of eight members is a noisy figure: its spread across members is as large as its median, and
the same code gave different medians in two sessions. So rules were compared on each quantity's mean yearly move over
the whole trimmed stage, across every member (`Complaints/reports/473-handoff/probes/ensemble_years.py` keeps every
year of every member as `spin-up-trace --stages --ensemble` replays them; `ensemble_moves.py` prints the mean and
median yearly move beside the median end gap). Eight members for England and Norse, four for Han, each configuration on
its own pinned worktree:
- **Against the head before this branch**, the branch head moves hired hours a third as much and real output about
  half as much on England, both about a fifth as much on Norse, and on Han hours about half as much and output about
  three quarters as much. Unmet need falls to almost nothing on England and to a small share on Norse. The rate moves
  a third as much on England and Norse. Not everything is better: Norse's inventory value moves about three times as
  much, and Han's price level, watched prices and rate move two to three times as much.
- **Still over the tolerance.** England's hired hours and output move by a little under the tolerance on average with
  end gaps about at it, and its inventory value and rate by several times it. Norse's hours and output move by one to
  two times the tolerance and its inventory value more than before. Han's hours, output and price level move by two to
  three times it and its rate by many times. `spin_up_settled` fails for all three. Mexica's output shrinks through the
  whole spin-up (`series_probe.py`); Rome was not measured.
- **Each change, in the order merged.** Poaching and household time took most of Norse's swing and about half of
  England's and Han's in hours, and left England's inventory value moving more; the durable rule then about halved
  England's and Norse's moves in hours, output and the rate and was about level on Han (its price level and wage
  moved more, on four members).

**Built and not merged** (branches pushed; the passnote's table has the reasons):
- `opening-cash-at-the-yearly-steady-state` (owner question 3, option a: the `opening-grown-floor-budget` patch
  re-applied, so the opening meets own-plot floors before sizing the budget as the yearly rule does). Alone it calmed
  England and Norse. On top of the durable rule England's hours moved more and Han's hours and wage swung far more
  than without it; the cause in Han is not traced, so it waits.
- `learning-path-plan` (owner question 6): a crew still learning judges whether to run on the discounted cost of its
  learning path over the years it expects to keep the trade, and entry takes the same path
  (`Complaints/reports/research-how-an-unpractised-crew-starts.md`). On Mexica the wooden-tool crews go from no runs to
  a fraction of a run: the plan no longer refuses, but entry sizes the crew to almost nothing, so tools are still not
  made.
- `sold-out-ramp-and-margin`: two amplifiers the late twin probe found at the branch head, each made continuous with
  rule tests. A producer added its share of its market's unmet demand to its sales only when its stock left was under
  a rounding share of them (`expected_sales.demand_seen`); the branch makes that a narrow ramp. A market's count of
  years with its price over the entry price went back to nothing when the price touched the entry price, and margin
  entry was all or nothing (`entry_margin.margin_streak`); the branch makes it a standing that moves by how far the
  price stands from the entry price, with entry in proportion. They do what they are for: twins forked late in
  England's trimmed stage (`late_twin_probe.py`, one fork) stay within rounding of each other for three years and
  differ by several orders of magnitude less after five than at the branch head. But measured together on the yearly
  moves, England is level and Norse's hours and output move nearly twice as much, so neither is merged; they were not
  measured apart.

**Found and not fixed** (each seen in a probe; none has a fix on the branch):
- **England's money stock wears away, so England's settled state is a deflation at the wear rate.** The coin-metal
  chain is nearly absent at England's opening. The opening places silver smelters on the jarosite route in most tiles
  although nothing in England mines jarosite ore: they smelt the stock they open with, then hire hands every year and
  make nothing until their cash is gone. The one silver-ore mine cannot sell its ore and closes. Silver made is a small
  share of the year's coin wear from the first year, the mint strikes a small share of the wear in every year, and the
  money stock falls by the wear rate each year; the price level, the wage and the workers' reservation follow it down
  together while real balances stay level (`python3 sim/simulator.py spin-up-trace --civ england_1300 --stages` prints
  `struck` and `wear`; `series_probe.py` logs the producers). `money_against_wear` fails for England. A fixed point of
  the price level needs an opening whose coin-metal chain its own tiles can supply (Complaints 961, 970), or a money
  whose loss is replaced some other way. This was so before this branch (the money stock of the head before it falls
  at the same rate). It is not England alone: on this branch Norse's and Han's money stocks also fall by their whole
  yearly loss (the `money_supply` of `ensemble_years.py`'s rows); Han's mint replaced part of its wear before, and
  its opening money is now several times larger (households sell more hours and hold more) while its strikes are not.
- **About a quarter of England's offered hours go unsold in every year**, and the wage stays a steady multiple of the
  workers' reservation while both fall with prices (`labour_totals_probe.py`). The labour market does not close the
  gap; Complaints 608 and 963 are the same finding at the opening.
- **Single goods still saw.** A medicine good's price creeps up for two years and falls in the third with its output
  swinging by a third; the crops' outputs fall together in some years. Not traced to one rule. A trial that dropped the
  producers' stock cover from the plan and let the ask only fall with unsold stock made prices fall every year and was
  dropped: the step that raises an ask when stock is under its cover is the only thing that raises asks between years.
- **The rate follows the year's inflation** (Update 28). Its relative move stays under the tolerance only when the
  yearly inflation is steady to a small fraction of a per cent, so it settles last.
- **Differences still grow.** Twins part within the first years of the first stage, and late in the trimmed stage
  their difference still grows about fourfold a year. Seen in the differences: a producer's expected sales adding the
  market's unmet demand when its stock is a rounding share of its sales and not otherwise (`expected_sales.demand_seen`),
  a market's margin-entry streak resetting when its price touches the entry price (`entry_margin.margin_streak`; one
  twin kept a streak of decades, the other lost it), a market's memory moving by a different rule when it traded and
  when it did not, and capacity shed or grown on the sign of the margin (`close_kernel`). The first two are made
  continuous on branch `sold-out-ramp-and-margin` (above).

## Update 31: the rate, the two amplifier fixes measured apart, and why the price level cannot rest (branch economy-settles-not-chaotic)

**Merged: expected inflation takes up a surveyed share of a year's surprise** (`currency.EXPECTATION_ADJUSTMENT_SPEED`).
The lowest rate a lender asks is its time preference plus the inflation it expects (Update 28), and the expectation
took up half of each year's surprise, so the rate followed each year's price noise. The share is now four quarters of
the weight on a new quarterly observation that surveyed inflation expectations imply (the source is in the
declaration; what was opened is in `Complaints/reports/research-inflation-expectation-weight.md`). It stays a
temporary heuristic and names what retires it: a weight that follows how lasting the surprises have been, small where
price changes are noise and large where they last. Under commodity money a year's inflation told little about the
next year's, so a lender who took up much of each surprise repriced on noise. On the yearly moves (`ensemble_years.py`
then `ensemble_moves.py`; England and Norse eight members, Han four) the rate's mean yearly move falls from several
times the tolerance to about the tolerance in England and Norse and from many times it to under twice it in Han,
whose hired hours, output, price level and wage move less too. Nothing measured moves more by more than the spread
between runs.

**The two amplifier fixes of branch `sold-out-ramp-and-margin`, measured apart** (branches `ramp-only` and
`margin-only`):
- Neither alone cuts the growth of a late twin difference on England (`late_twin_probe.py`); only both together do.
  Each of the two rules is enough on its own to carry a rounding difference up to whole per cents.
- The ramp alone makes Norse's hired hours and output move about twice as much as the head and does not calm Han;
  margin entry alone moves Norse's somewhat more in the mean and about as much in the median. Most of the swing seen
  with both is the ramp's: a producer that counts its
  market's unmet demand in proportion to how nearly it sold out chases that demand in more years than the threshold
  let it. The rule being smoothed, a producer adding its market's unmet demand to its own expected sales, is the
  suspect; the earlier form of the fix showed the same.
- With both, the first leaves to part in the late fork are one building trade's wage and the output of a plant good,
  in one year (`show_twin.py` on the probe's output). Not traced.
Not merged: the ramp because of Norse, margin entry because alone it cuts nothing and calms nothing.

**England, one run, year by year** (`series_probe.py`, read with `analyse_inventory.py` and `money_ratios.py`):
- Through the trimmed stage the price level and the unskilled wage fall, in nearly every year and faster than the
  money stock does. The producers' cash drains; the households' stays level.
- The households hold about two years of their income in cash and the producers about a year of their sales.
- Producers' inventory value is a small share of a year's output, so its relative move is the goods markets' yearly
  residual magnified many times. The goods that carry it (the fuels, a medicine, a grain) end a year with nothing left
  or with a large share of a year's output left, and in the same years as one another, which points at what the
  households spend as a whole in those years and not at one market. Not traced further.

**Why the price level cannot rest: the coin metal** (Complaints 981 and 982, with the probes that measure each).
- The money stock falls by about its whole yearly loss in every metal-money civilisation measured, because the mint
  strikes next to nothing. England's opening returns one phase of a cycle for its silver recipes
  (`coin_passes_probe.py`): smelters on the jarosite route, no mine for their ore, the lead route sized for lead's
  other buyers, galena and silver ore dug with no smelter to use them. The jarosite ore recipe is tied to no
  deposit in any civilisation and is treated as unlimited. Norse opens with no maker of silver at all, Han with next to no maker of its coin
  bronze (`unsited_probe.py`).
- A consistent chain does most of it: on a scratch copy without the jarosite recipe England's silver comes from its
  own galena and silver ore, the mint strikes most of the coin's loss, and the money stock falls about a quarter as
  fast and the price level about a third as fast (Complaint 981 says how it was run, and what it shows next: the lead
  that comes with the silver piles up unsold).
- Even so the stock still falls: the loss of a stock this large is more silver than the ceilings of England's own
  ores give once households take their share. The stock is that large because households rest at years of income in
  coin (Complaint 982).
- So a fixed point of the price level, and of the wage, the reservation and cash with it, needs the money's loss
  replaced. That is a decision about what households hold their wealth in and about which ores a civilisation has
  (`Complaints/reports/473-owner-questions.md`, questions 8 and 9), before it is an engine change.

## Update 32: the owner's answers to questions 8 and 9; what was built, what the research found, what the hoard is (branch economy-settles-not-chaotic)

**The owner's answers** (`Complaints/reports/473-owner-questions.md`): households keep most of their wealth in things
other than coin and the loss rates are to be sourced (question 8); a civilisation cannot dig an ore it has no deposit
of, and where its coin was a metal the mines it dug that metal from are to be researched and added (question 9).

**A correction to Update 31 and Complaint 982.** They said the price level cannot settle while the money stock falls.
The settle test compares consecutive years (`spin_up_gap.state_gaps`), so a price level that falls steadily by less
than the tolerance a year passes it. What fails is the size of the yearly moves. The coin chain decides
`money_against_wear` and how fast prices drift; it is not by itself what keeps `spin_up_settled` from passing.

**Built and merged, each with a rule test:**
- **An ore with no deposit on the economy's tiles is dug nowhere** (`port_sites.site_limits`,
  `test_economy_port_sites_rules`): such an ore keeps a limit of nothing on every tile where it used to have no limit
  and run anywhere. **A deposit type can name its own ore good** (`resource_links.ore_goods_by_deposit_type`, the
  resource catalogue's `ore_goods` on a deposit type; worked-deposit rows carry their type): the jarosite ore is dug
  from gossan deposits alone and silver ore from silver's other deposits. Before, the jarosite ore recipe was tied to
  no deposit in any civilisation.
- **The opening's recipe choice settles** (`opening_runs.required_runs` and its kernel twin,
  `test_required_runs_settles`): where whole steps circle the passes go on from where they stand with the step
  halved, block by block, until the runs stop moving (Complaint 981's first half).
- **Deposits from the research**: the Crown's silver-lead mines at Bere Ferrers (England) and the Yandao copper mine
  (Han), each with the source opened (`Complaints/reports/research-coin-metal-mines.md`).

**What the research found** (three reports under `Complaints/reports/`, each citation opened in its session and one
of each opened again here):
- `research-coin-metal-mines.md`: England's coin silver was mostly brought in by trade and the Norse mined none; the
  one home source for England about the start date is Bere Ferrers. Rome's silver and Han's copper were mined at home;
  the Mexica's money is cacao. So for England and the Norse there are no missing home mines to add: their money was
  kept up from abroad, and the hidden spin-up is a closed economy with no foreign orders. Rome's Spanish silver
  deposits are in the catalogue with no working date, so the engine sizes none of them: Rome's silver on its tiles
  comes from one district. Not changed here.
- `research-coin-loss-and-money-held.md`: estimates of a coin stock's whole yearly loss start at the declared rate and
  run upward; wear alone is a fraction of it; no source was found for the loss of plate. England's coin about the
  start date was about a fifth of a year's income; Petty's account of England's wealth puts coin at a small part of it
  and wares, plate and furnishings at several times the coin.
- `research-inflation-expectation-weight.md` (Update 31).

**Measured with the ore rule** (`ensemble_years.py`, `ensemble_moves.py`; England and Norse eight members, Han four):
England's money stock falls about three fifths as fast and its yearly moves are level with before (its watched
prices move less). Norse's output, rate, wage and watched prices move less and its inventory value more. Han's hired
hours, output and wage move more in a sample of four, which is within the spread between earlier samples of four for
hours and output and above it for the wage; not settled which, and Han needs more members to judge. In one England
run the opening now places the lead-silver route and the silver-ore route at their ceilings and silver is made every
year (`coin_passes_probe.py`, `coin_opening_probe.py`, `series_probe.py`).

**The hoard is made by the yearly rules, and the opening's purse only starts it there** (England, one run each;
`series_probe.py` read with `money_ratios.py`):
- The opening gives a household the coin at which a yearly share of its account covers the floors its own plot grows
  (`opening_resting.resting_household_purse`, `extra_spending`): years of income for a household that grows its
  food. Branch `money-at-the-yearly-steady-state` (the earlier `opening-cash-at-the-yearly-steady-state` merged on the
  ore rule) opens without it: households open with well under a year's income in coin and the money stock is a little
  over half as large.
- Within twenty years every class of household again holds about two years of its income in coin. It comes out of the
  producers, whose coin falls by more than half; hours sold a head fall by a quarter in the first five years, the
  wage ends at a fraction of its opening and output ends lower than with the opening hoard. Not merged.
- Raising the share of savings a household keeps as store goods (`households_store.STORE_SAVINGS_SHARE`,
  `STORE_SHARE_LIMIT`, to the share Petty's figures give) does not send the coin back to the makers. With the opening
  hoard the opening sized a rush into store goods and output opened a third lower; without it households bought next
  to no store goods (what they hold wears away), and the rate and the price level jumped late in the run. Not merged.
  The store rule buys the whole gap once past a dead band and nothing below it, which is one more jump.
- The households' accounts say what the hoard is (`household_accounts_probe.py`): in every year households plan to
  spend about a third more than they do. Their bids are not filled, because the goods are not made, while a quarter
  of the hours offered find no employer; output falls by a fifth in the first two years after the opening and takes
  decades to come back. The hoard is the spending that found nothing to buy, and the coin it holds is the coin the
  producers would pay wages with.
- So the change question 8 asks for is larger than the opening, and the first thing in its way is that the first
  years do not reproduce the opening (Complaints 608 and 960 to 963, found on Rome; England falls the same way).
  Owner question 12.

**Found and not fixed:**
- **A co-product nobody buys piles up.** With England's silver on the lead route, the lead has few buyers: its price
  goes to nothing, it piles up in the smelters' stock (so producers' inventory value grows every year), and the
  lead-silver smelter's runs fade through the trimmed stage although a run pays at the year's prices. The plan rule
  already leaves a minor output's pile out of the runs (`producers.runs_for_stock`); what does hold the runs back is
  not traced (`agent_flow_probe.py` shows its coin, capacity and runs falling together).
- **The watched prices**: the cart is the watched good whose price moves most in most years; draught animals, which
  are not watched, swing by tens of per cent a year; shoes are watched and never made (one maker, no runs), so their
  price is a remembered one. Read from the `prices` of `ensemble_years.py` rows.
- **Inventory value is the residual of markets that clear inside the year** (`unsold_search.py`, `demand_search.py`):
  most goods end most years with nothing left and a floor that binds leaves a lump. It is measured against itself with
  no floor, although the settle test gives a floor to the two other quantities that can sit near nothing (the rate and
  unmet need). Owner question 11.

## Update 33: the first years do not reproduce the opening, and what holds England's first year back (branches economy-settles-not-chaotic, opening-staffs-every-trade)

**How it was measured** (scratch probes in `Complaints/reports/473-handoff/probes/`, run from a checkout with
`PYTHONPATH` set to it): `first_year_probe.py` (for each recipe the runs the opening sized, the capacity it placed and
the runs staffed and worked in each of the first years, valued at the opening's prices), `first_year_labour_probe.py`
(the first year's labour markets by work area and by trade), `producer_inputs_probe.py` (one producer's coin and what
it holds of its inputs, plant and outputs before and after each year) and `household_accounts_probe.py`.

**What England shows.** The first year works about three quarters of the output the opening sized and the second
about three fifths. Employers want fewer hours in total than households offer, and still about a tenth of what they
want is not hired: the shortfall is by place and by trade.

**Fixed and merged, with a rule test** (`sim/labour/market/opening.py` `staffed_share`,
`test_labour_core_opening`): an area short of people gives every trade the same share of its need. The opening
placed an area's people trade by trade, hardest first, and the fallback trade took who was left. On England's busiest
tile the producers need more hours than its people sell, so labourers and spinners opened with next to nobody and
peat, coal and thread could not run. With the fix England's first year rises from about three quarters to more than
four fifths of the sized output.

**Found and not fixed** (each seen in a probe):
- **Wool is one producer, sized at about twice the runs its pasture allows** (`land_run_cap` against the expected
  sales the opening gives it), so its first year is half its sized runs from the start.
- **In its second year that producer hires its herders, gets no salt, makes next to nothing and loses most of its
  coin.** Salt is a small input of a run and its price rises by a third that year. Thread, cloth, felt, shoes and
  leather stop with the wool. This is the pattern of the silver smelters of Update 30: hands are hired and paid before
  the year's inputs are bought, so an input that does not arrive costs the whole wage bill. The project rule that a
  shortage of one input must not silently stop everything that uses it is not met here.
- **Labourers are offered exactly the hours wanted in every area and about seven eighths of those are hired**, where
  the skilled trades are offered a tenth more than wanted and are hired almost in full.
- **About a billion hours offered by farmers find no employer**, in tiles where labourers are short: a household with
  spare time on its plot does not take labouring work within the year.
- **The busiest tile's producers still want about a quarter more hours than its people offer** after the fix: the
  opening sizes a tile's producers without regard to its hands (Complaints 961 and 963 on Rome).

**The staffing fix measured, and Norse's zigzag traced** (`ensemble_years.py`, `ensemble_moves.py`). With the staffing
fix England's hired hours, price level, rate and wage move less (hours, the price level and the rate are under the
tolerance on average) and Han's price level, rate and output move less. Norse moved about twice as much: of 24
members a quarter sat in a low-employment zigzag, against one in 24 before. Traced on the unperturbed member
(`series_probe.py` with `analyse_series.py`, then `grinding_probe.py`):
- the hours labourers are hired for on Norse's main tile alternate by a third and their wage alternates against them;
- the households' own housework hours alternate, because the share of their food they count as ground by hand flips
  between about a half and nothing;
- that share follows their food mix, and the mix jumps: in alternate years a by-product food (cheese one year, lard
  another) holds a price of next to nothing for a year, and the mix, which is set by price alone
  (`priced_need_kernel.mix_shares`), gives it most of the food they plan to buy. The market cannot supply it, the
  bids are re-spent inside the year, and the next year the food has no price and the mix is back.

**Merged with it: grinding by hand is a smooth share and moves gradually** (branch `grinding-share-continuous`: the
parked `grinding-share-continuous` patch re-made on the current tree, with a gradual step added;
`household_grinding.bought_shares`, `ground_by_hand`, `stepped_ground`, `stepped_overall_share`,
`household_work_year.counted_share`, `Cohort.food_ground_share`, `GRINDING_ADJUSTMENT_SHARE_PER_YEAR`;
`test_economy_household_grinding`). A cohort buys a share of each grain milled that is a smooth function of the two
costs, and the share of its food it counts as ground by hand, which sets its housework hours, moves a declared share
of the way from last year's to this year's each year (the opening takes it whole). With both merged Norse's zigzag
is back to one member in 24 and its yearly moves are a little under what they were before either.

**Not fixed: a thin, cheap good takes most of a need's planned spending.** The damping above cuts what the jump does
to hours; the jump in the planned diet is still there, and so are the bids that find nothing. A good's share of a
need should be held to what its market usually trades and a year's growth on it (`limit_shares` already takes a
limit for each row, and the market memory keeps each market's usual volume).

**Han's first year falls much further short than the others'** (`first_year_probe.py han_china_100ad`): it works well
under half of the output its opening sized, with several times as many hours idle as hired; firewood and wood are
staffed at about a third of their sized runs, the one wool producer is sized for more hours than any tile could give
and is not staffed at all, and draught animals, oil and flour run at a fraction. England's and Norse's first years
work about four fifths of theirs after the staffing fix. Han's yearly moves in the trimmed stage sit on top of that
gap, and its samples of four members differ by nearly as much between like configurations as between unlike ones. A
larger sample (twelve members on the merged state against seven at the start of this round, the rest of that run
having been killed for memory) says Han's hired hours and wage now move about twice as much, and its output, price
level and rate about as much as before. The samples of four put the step at the ore rule (Han's silver can no longer
come from jarosite ore dug anywhere), not at the staffing or grinding changes. Not traced further.


## Update 34: a long run never rests; the opening put whole trades on one tile, ignored land it had already cleared, and the hiring rounds starved large employers (branch economy-settles-not-chaotic)

**How it was measured** (probes in `Complaints/reports/473-handoff/probes/`, run from a checkout with `PYTHONPATH` set
to it): `probe_spin_years.py <civ> <first years> <trimmed years> <out>` for one long run, read with `windows.py`
(mean yearly move and net drift of every watched quantity by window of years) and `table.py`; `price_kinds.py` on an
`ensemble_years.py` file (for each watched quantity the mean move, the drift a year and the lag-one correlation of
the moves: negative is a zigzag, a drift with none is a slide); `series_probe.py` read with `drift_goods.py` (which
goods carry a change in real output); `first_year_probe.py`, `first_year_labour_probe.py`, `labourer_probe.py` (one
labour market: every employer's posts against the hours it was given), `placement_probe.py`, `placement_trace.py`,
`unsited_list.py`, `fit_probe.py`, `oriented_probe.py`, `opening_sizes.py` and `hunger_probe.py` for the opening and
the first year. `ablations.py` holds two switches for `probe_spin_years.py` (`ABLATE=nowear`, `ABLATE=floor`).

**A long run of England never comes to rest.** Run for two centuries, no window of twenty years has every watched
quantity under the tolerance, and the moves do not shrink with time. What the forty-five years of the spin-up show is
mostly a one-way slide, not a zigzag: the wage falls for a generation, bread and flour fall by about the tolerance
every year, linen and coal rise by more than it every year. Three things lie under it:
- **The money stock falls every year, in every civilisation measured** (`money_supply` in any `ensemble_years.py`
  file). Wear takes its declared share and the mint strikes about half of it in England and the Norse lands and
  none in Han. Over the long run England's stock falls to about a third; the wage and the price level follow and
  late in the run households go hungry. With wear switched off (`ABLATE=nowear`) the totals move about half as much
  for several decades, the calmest stretch of any run, and then swing widely: the stock is one cause, not the only
  one. Complaint 982 holds the cause; owner questions 10 and 13 are the decision. Holding the stock for the length
  of the spin-up (`ABLATE=held`: coin wears only as far as the mint struck) leaves England's yearly moves about as
  they are and makes the Norse lands' a little larger, so the fall is a long-run matter, not what fails the check.
- **The wage ask cannot be held by a floor at the subsistence wage** (`ABLATE=floor`): the wage still falls, because
  the subsistence wage is the cost of the food basket and the food's price is mostly the wage. The two follow each
  other down against the goods whose price is held (silver at the mint price, goods at the top of their band).
- **The first year does not reproduce the opening**, so capacity is shed in the first years and comes back in rare
  steps (`series_probe.py`: a producer's capacity stands still for decades and then rises by half in one year). The
  rest of this update is what was found and fixed there.

**Fixed, each with a rule test.**
- **A site-bound recipe with no declared site was placed whole on its market's anchor tile** (`location.opening_split`;
  `test_economy_sites`). A good that trades over the whole economy has one market area, so flax, poppy, wool, wax and
  draught animals all opened on one tile, which wanted far more hours than its people sell while a third of all hours
  offered elsewhere found no employer. They are now shared over the area's tiles by their people, like an unbound
  recipe. This is the busiest tile of Update 33 and most of its idle farmers.
- **A processor tied to its input's site got no tile when the tile's hands were spoken for** (`location_inputs.place_oriented`;
  `test_location_inputs`, `test_opening_smelters_beside_ore`). Its placement was capped at the hands left after
  every producer placed before it, counted at their full capacity; with none left it was not placed, and the supply
  fit then held every user of its output to nothing. With the first fix England's only iron-ore tile was in that
  state and the whole iron chain opened at nothing. It is now capped at what all the tile's hands could work and
  shares them with the others through the labour market.
- **A processor tied to a sited input served every market from one tile** (`location_inputs.place_oriented`;
  `test_location_inputs`). Its runs for all markets went to the tile cheapest on average, as far as the supply and
  hands there allowed, so Han's wooden tools and pottery opened whole on one tile each. Each market's runs now go to
  the tiles cheapest for that market.
- **The hiring rounds starved an employer with most of a market's posts** (`hiring_kernel._shares_of_prefix`,
  `labour_hiring_reference._taken_by`; `test_labour_eurace_applications`, `test_year_speed_labour_hiring`). A
  searching household applied to a few posters picked evenly. A producer here stands for every workplace of its
  recipe on a tile, so one posting half a market's hours drew as many applications as one posting a hundredth, could
  not take back what each round's dismissals cost it, and ended every year about a quarter short while the small
  employers were full: the labourers of Update 33 who were offered exactly the hours wanted and seven eighths hired.
  An application now goes to a poster with the chance of its share of the hours posted.
- **The opening ignored the land it had already cleared** (`opening_land_fit.held_to_land`, `fit_to_land`,
  `opening_runs.limited_goods` with the land a run takes; `test_opening_fit_to_land`). The opening's land market
  states the runs each producer's grant allows and the first year's plan works no more, but sales, plant, coin and
  the users of the output stayed sized for the runs asked. Han's wood, firewood and draught animals opened at many
  times what their ground allows. Each producer is now cut to its grant and the users of what only land makes to
  that supply. This closes the users of a land-bound good that no opening producer makes: in all three
  civilisations the wheat farms (their plough teams are plant no placed herd breeds, so the plant wore out a tenth
  a year and bread lost its price late in the spin-up) and the cheese makers (no milk is made; they ran one year on
  an opening stock and then hired hands for nothing). Leaving those users as they were sized was tried
  (`ensemble_years.py` on England): the totals moved nearly twice as much. They come back when a herd that makes
  draught animals and milk is part of the opening (owner question 15).
- **An input's price limit counts the wages already committed** (`producers.input_ceiling`, `plan_bids.place_bids`;
  `test_economy_input_ceiling_share` and the three beside it). The limit was the price plus a percentage margin, so
  a small input a little dearer than the margin was not bought and the run's wages were lost (the salt of Update
  33). It is now what the run can pay for its inputs once its hands are hired.
- **The settle test reads a change in producers' inventory value against the year's real output** (owner question
  11; `spin_up_gap.state_gaps`, `test_spin_up_measure`).

**What the first year works of the output the opening sized** (`first_year_probe.py <civ>`): England about nine
tenths (about three quarters at the start of Update 33), Norse more than four fifths, Han about two thirds (under two
fifths before). Hours staffed are within a few per cent of hours sized in all three; what is left is hours hired
and not worked, for want of an input or a tool. Han's farms work about two fifths of the runs they hire hands for:
the opening has next to no iron tools there (its iron chain is sized at next to nothing while its ores are dug) and
the wooden tools the opening sizes in their place do not reach the farms, so the work is done by hand.

**Han and the Norse lands are hungry from the first year** (`hunger_probe.py <civ>`). About two fifths of Han's
food need and a sixth of Norse's is unmet in year one, before any yearly dynamics. In Han the hungry are on fertile,
populous tiles whose households work no plot at all (the land went to producers that outbid the plots) and hold
several years of income in coin; the farms that took the land hire nearly all the hours they are sized for and work
about two fifths of the runs. In the Norse lands they are the tiles with no farmland, with coin in hand and no food
reaching them. Neither can settle while this holds, and the yearly moves measured on them sit on top of it.

**Tried and not merged.**
- **Households' mix within a need anchored on what the market usually spends on each good** (branch
  `households-mix-follows-the-market`): England moved more on every watched quantity.
- **Producers hire within what their inputs' markets can supply** (branch `plans-within-reach`): hiding the shortage
  from the plan hid it from prices and entry as well; bidding for the whole plan while hiring within reach stirred
  late prices and inventories.

**Found and not fixed.**
- **A good whose buyers want more than there is stays rationed for years, because its price cannot leave the band
  above its cost** (`ask_adjust.band_edge`, `unsold_search.ask_limits`), **and the rationing is pro rata among
  households' bids and producers' input bids alike** (`goods_market_ration.ration`, `goods_market_kernels.serve`:
  one tier for both). England's households take the leather the shoemakers were sized to use (leather meets
  clothing cheaply), the shoemakers work a quarter of their runs, and shoes then have no price in most years, which
  the check counts as a full move. Han's wooden-tool makers work and sell all they are sized for
  (`producer_inputs_probe.py`), yet its farms get next to none of the tools and work by hand: the households'
  spending on implements takes them. A price that could rise would hand the good to whoever it is worth most to; a
  maker's bid for an input states that worth (`producers.input_ceiling`) and is not used to rank it. Linen and coal
  climb a few per cent every year for the band's reason.
- **Inputs carried from the one tile that makes them do not arrive in the first year**: England's bloomeries work
  about a third of their runs, and the crops that wear iron tools about three quarters.
- **Capacity grows only when buyers are turned away at the price**, and the search inside the year raises the price
  until none are, so a sold-out maker with a wide margin has no signal to grow.
- Still open from earlier updates: the unsold co-product, the cart and draught-animal price swings, Rome and Mexica
  unmeasured on this tree.
