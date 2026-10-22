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
`python3 -m sim.tests --slow --only purchase_limited_by_offered_volume_scenario --jobs 1`.

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

Traced with the spin-up uncached (probe not committed: `economy_port_year.SPIN_UP_CACHE_DIRECTORY` set to a temporary directory, wrapping `producers.plan`
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
none it plans from its expectation as before. Tests: `sim/tests/test_economy_first_year_plans_from_stationary.py` (a stationary quantity below capacity is
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
  1.0, 11.4, 20.1, 50.2, 4.0, 2.4, 1.05 after. Slow topics (`--slow --only economy_bronze_market_price,price_over_making_cost_band_validation,baseline_fixture,purchase_limited_by_offered_volume_scenario --jobs 1`):
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

Tests: `sim/tests/test_economy_opening_household_plans.py` (a solved opening's grain demand is what its households buy at its prices, flour price high and
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
