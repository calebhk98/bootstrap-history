# The agent economy's spin-up never settles, so the opening is a point on a cycle

**Status:** partly - a one-year closure test and the stationary quantities now exist (Update 6); the money stock is sustained (Update 4, `spin_up_money_supply` passes); the spin-up still does not settle: the price level and wage drift for decades because the labour market clears far below the cost table's wage (Update 4)

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
(`sim/engine/economy_capital_market.py`), so household saving collapsed. The founder's borrowing is far too
small to move it. A founder who had borrowed at a normal rate to hire staff paid well over half the debt in
interest each year and went insolvent. Wages (and with them the workshop's revenue, which is a markup on
wages) fell through the same years. Reproduce by stepping a year at a time and reading `money`.

## Current state (Update 4, stage 2 of 507)

Built on `507-stage-2-opening-from-costs`: household income settled with the demand it pays for, plant sized to the share that
works, workforce placed for the runs producers expect to sell, producers opening with their inputs, recipes ranked with
deposit ceilings and demand-limited co-products, the metal the money loses a year as the mint's final demand, and the coin
priced at the marginal cost of its metal.

Fixed: the money stock follows from the transactions and the metal's cost, the chain behind the coin metal exists at the
opening, and `test_the_money_stock_keeps_up_with_wear` passes (the mint's strikes are about wear over the last decades;
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

Measured with `play("norse_900ad", 7)` from `sim/tests/money_regimes_play.py` (no mined metal), the basket price level
by year is 1.07, 1.41, 0.96, 1.07, 0.96, 0.55, 0.46. Millet, about a third of the basket's weight, falls to about 0.4 of
its base price by year five, and wheat is already about 0.37 of base in year 0. With 10% extra mined metal each year the
level follows the same food collapse a year earlier (the money stock does double). So the slow validation "more metal
raises the price level" (`check_more_metal_raises_price_level`) is drowned by the unsettled economy for Norse; the
transmission rules are held by `test_money_reaches_prices`.

## Update 6: a one-year closure test on the small fixture, and the movers it finds (branch opening-stationary-state)

What is built: `sim/economy/opening_stationary.py` (a plain function: the runs that meet a final demand by the
input-output solve in `opening_runs`, the hours they hire, and the incomes they pay, so wages plus profit equal the
value of final demand), `economy_fixture.stationary_setup` (the fixture with each worker offering the hours its runs
hire plus a stated slack), and `sim/tests/test_opening_stationary_scenario.py` (a stepped year against the settling
bounds in `sim/economy/settling.py`). The opening does not yet seed its producers from the solver. Run:
`python3 -m unittest sim.tests.test_opening_stationary_scenario sim.tests.test_opening_input_stocks`; the red parts are
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
and the settling statistic over its rows (`sim.economy.settling.settling_report`, as `economy_port_trace.spin_up_trace` feeds it).

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
  `test_opening_stationary_scenario` (OpeningHoursTests, KnifeEdgeTests).

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
rome_100ad --years 60`; `python3 -m sim.tests --slow --only baseline_fixture,baseline_rome_full_length,real_output_baseline,spin_up_money_supply_full_length --jobs 1`;
`python3 sim/simulator.py opening-checks`.

Leisure is limited to hours the plot could not still use (`HourSupply.parts`): without that limit Rome's one-year hunger share rose to
0.49 (`labour_margins_baseline_validation`), since hours that used to grow food became leisure. Now, Rome one year: hired share 0.33
(was 0.04), wage over floor 4.8 (was 3.4), hunger share 0.17 (was 0.15). `baseline_fixture` passes whole.

## Measured (2026-10-21, 60-year Rome trace at 9eb35921: hour supply schedule plus supply fixes)

Output: `Complaints/reports/473-trace-9eb35921.txt`. The first four decades are calmer than at 72e81e68 (the price level near
a hundred at year forty instead of nearer two hundred, hired hours steady), then the economy explodes after year forty: the
price level, the wage and the rate run away together within a few years (the rate far above one, the wage thousands of
times its opening). A per-good decomposition of years 35 to 52 is running (`decomp.py` probe, the same as for 72e81e68).

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
