# Model run: Caiani, Godin et al. 2016 benchmark (JMAB, Java)

> **Checked against the code (2026-11):** the labour core now pays one market wage per (trade, area); every hour hired is paid it and no employer holds a contract wage of its own (`sim/labour/market/DESIGN.md`, "Clearing"; `contracted_wage` and `contract_wages` no longer exist). Where this report describes per-employer contract wages it describes an earlier build.


Paper: "Agent Based-Stock Flow Consistent Macroeconomics: Towards a Benchmark Model" (Caiani, Godin, Caverzasi, Gallegati, Kinsella, Stiglitz; JEDC 2016; SSRN 2664125; the working paper is `benchmark/paper/BenchmarkModel.pdf` in the model repository).

## What was run

- Code: `github.com/S120/jmab` (the framework, 307 Java files with the model) and `github.com/S120/benchmark` (the benchmark model: agents, strategies, init, Spring XML). Cloned to `/tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/models/jmab/{jmab,benchmark}`. File:line citations below are in those clones (`jmab/src/jmab/...`, `benchmark/benchmark/src/benchmark/...`, config `benchmark/benchmark/Model/modelBenchmark_light.xml`).
- Licence: both READMEs carry the MIT text ("Copyright (c) 2016 Alessandro Caiani and Antoine Godin"); the Java file headers say GPL v3 or later; the JABM jar it needs is GPL. Running locally is fine. We copy no code into our repository (ideas only).
- Build: OpenJDK 21 here. The repository ships no build file and no JABM jar (its `lib/` has only colt, log4j, spring). JABM 0.9.9 is on Maven Central; I resolved it and its plain dependencies with a pom of my own (kept outside the clone, GUI-only transitive dependencies excluded) and ran `javac` over the 307 sources. It compiled unchanged.
- Run: `benchmark.Main` with `-Djabm.config=.../mainBenchmark_light.xml`, the shipped benchmark configuration (400 periods, seed 1, 8000 households, 20 capital firms, 100 consumption firms, 10 banks, 1 government, 1 central bank). The "light" configuration only drops some report series; the model beans match the full file. About 40 minutes for 400 periods on one core (a period costs several seconds: the dividend step values every household's wealth for every firm, and the labour market reshuffles all sellers for every hire).
- Period = a quarter (the paper says "over the year (i.e., four periods)").
- Series written to `.../scratchpad/work/run2/data/*.csv`; two variants (150 periods each) in `.../scratchpad/work/run_mt12` and `run_to15`.

## Result: unemployment rate from the calibrated start

Series = `1 - employed/8000` (`jmab/report/UnemploymentRateComputer.java:55-63`); the 1360 public servants count as employed.

| periods | mean | min | max |
|---|---|---|---|
| 1 (the start) | 0.080 | | |
| 1-20 | 0.092 | 0.072 | 0.098 |
| 21-50 | 0.057 | 0.042 | 0.083 |
| 51-100 | 0.061 | 0.048 | 0.075 |
| 101-150 | 0.083 | 0.051 | 0.110 |
| 151-250 | 0.074 | 0.053 | 0.096 |
| 251-400 | 0.075 | 0.054 | 0.093 |
| all 400 | 0.073 | 0.042 | 0.110 |

First 12 periods: 0.080 0.073 0.072 0.083 0.089 0.095 0.096 0.096 0.097 0.098 0.097 0.098. It never runs away: after the early swing (a dip to about 4-5% around periods 30-60, a peak of 11% around period 140) it stays in 5.4-9.3% with sd 0.0067 in periods 251-400. The paper's published quasi-steady-state table for the same baseline (`paper/Benchmark Model - Similation Results/Summary Tables Quasi-SS.xlsx`, sheet "Summary Baseline", average over runs) gives mean unemployment 0.0784, sd of the trend 0.0027, cyclical sd 0.0908; my single run (mean 0.0749 over periods 251-400) sits in that. The paper's text: "unemployment fluctuating just below 8%", with a "great recession" with unemployment peaks between periods 45 and 130 in its figure (not reproduced as a deep peak in my seed: one run, one seed).

Nominal series in the same run: average wage 5.0 at period 1, 6.3 at 50, 9.0 at 100, 10.5 at 150, 13.3 at 200 (steady nominal growth, `gss`); consumption firms' bankruptcies 793 in total over 400 periods across 100 firms (about two per period).

### Parameters
The authors' stated sensitivity set (`Model/experiment.properties`, and the paper's sensitivity section) is about banks' risk aversion, firms' precautionary deposits, and the weights of cash flow and capacity in investment. None is a labour parameter, and the paper reports unemployment moving little across them (the Quasi-SS sensitivity sheets: mean unemployment between 0.062 and 0.077 across all values of those four parameters). The labour-side lines in `experiment.properties` are `householdsWageStrategy.macroThreshold=0.06:0.01:0.12`, `governmentPrototype.unemploymentBenefit=0.2:0.1:0.6` and the turnover `turnoverVal.value=0:0.05:0.3`. I changed two, same seed, 150 periods:

| change | periods 1-20 | 21-50 | 51-100 | 101-150 | 150-period mean |
|---|---|---|---|---|---|
| baseline (macroThreshold 0.08, turnover 0.05) | 0.092 | 0.057 | 0.061 | 0.083 | 0.0714 |
| macroThreshold 0.12 | 0.093 | 0.064 | 0.066 | 0.093 | 0.0781 |
| turnover 0.15 | 0.097 | 0.056 | 0.065 | 0.087 | 0.0746 |

(Baseline 150-period mean is the first 150 periods of the full run.) Tripling the share of workers separated each period or raising the wage-raising threshold by half changes the long-run unemployment by a fraction of a percentage point. Unemployment is set by the demand side, not by the wage rules (below).

## Labour supply

- Every household (8000, `modelBenchmark_light.xml:2602`) offers one job's worth of labour: employed or not, no hours. A household is `LaborSupplier` with one `wage` field, which is both its ask and the wage it is paid (`AbstractHousehold.java:31`; wages are paid at `wage` in `ConsumptionFirmWagesEnd.java:165`). No separate reservation wage, no search effort, no participation choice.
- It is in the labour market while it has no employer (`Households.java:204-209`: each period at `TIC_LABORSUPPLY` it recomputes its wage and, if `employer==null`, activates itself on `MKT_LABOR`). Fired workers are reactivated at once (`AbstractFirm.java:130-134`).
- The ask moves by `AdaptiveWageStrategy.computeWage` (`jmab/strategies/AdaptiveWageStrategy.java:42-54`):
  - if `microReferenceVariable > 0.49`: `wage -= wage * |N(0, 0.0094)|` (a cut of 0.7% on average);
  - else if `macroReferenceVariable <= 0.08`: `wage += wage * |N(0, 0.0094)|`; otherwise unchanged;
  - floor `getWageLowerBound()`, which returns 0 (`Households.java:379-382`).
  - `macroAdaptiveParameter = microAdaptiveParameter = 1`, `foldedNormal1` has mean 0 and stdev 0.0094 (`modelBenchmark_light.xml:2770-2777, 2952-2956`).
- Micro reference (`Households.java:397-407`): for an unemployed household, `(1 + sum of LAG_EMPLOYED over lags 1..3) / 4` where `LAG_EMPLOYED` is 1 if employed that period and 0 if not (`Households.java:233-238`); for an employed one, 0. Macro reference (`Households.java:427-432`): 0 for an unemployed household; for an employed one, the economy-wide unemployment rate of the previous period (`LAG_AGGUNEMPLOYMENT`, set by the government each period, `Government.java:155`).
- Consequences read from the code, not the paper:
  - Employed workers never cut (micro = 0) and raise their wage by a draw whenever last period's unemployment was at most 8%. Wages are down-rigid for the employed.
  - An unemployed worker who was employed in at least one of the last three periods (`(1+k)/4 > 0.49` for `k >= 1`) cuts. One who has been unemployed for three periods (`k = 0`, value 0.25) falls into the else branch where his macro variable is 0, which is `<= 0.08`: he RAISES his ask each period. The long-term unemployed ask more, not less.
  - The rule is the opposite of the paper's (see Differences).
- Benefit: the government pays each unemployed household `0.4 * average wage of the employed` each period (`GovernmentAntiCyclical.java:101-125`, `unemploymentBenefit = 0.4`, `modelBenchmark_light.xml:2842`), from its reserve account. It enters the household's income (`Households.java:349-372`), not its ask.

## Labour demand

- A consumption firm sets planned output from expected real sales: `max(0, expSales + (0.1 * expSales - inventories))` (`TargetExpectedInventoriesOutputStrategy.java:46-52`, `inventoryShare = 0.1`, `modelBenchmark_light.xml:2092-2097`; the capital firm uses the same strategy, `:1799-1804`). Expected sales is an adaptive expectation of past real sales.
- Workers wanted = what the planned output needs on its capital. `getRequiredWorkers` (`ConsumptionFirm.java:267-299`) fills the planned output starting with the most productive capital vintage; each capital good needs `quantity / capitalLaborRatio` workers (ratio 6.4 for the capital good, `modelBenchmark_light.xml:1547`; capital productivity 1). Fixed coefficients; the wage plays no part in the head count. Output is capped by capacity (the loop just stops filling when the capital runs out).
- Hiring and firing (`ConsumptionFirmWagesEnd.computeLaborDemand`, `:183-214`; same in `ConsumptionFirm.java:306-356` and the government's `GovernmentAntiCyclical.java:144-180`):
  1. Every firm first dismisses `turnoverLabor * employees` at random (`for (i < 0.05 * currentWorkers) fireAgent(shuffled.get(i))`; `turnoverVal = 0.05`, `modelBenchmark_light.xml:2018-2020`). The loop runs to `i < 0.05 * n` so it dismisses `ceil(0.05 n)`: at least one worker from any non-empty firm.
  2. Then `nbWorkers = getRequiredWorkers()`. If more than held, `laborDemand = nbWorkers - held`, active on the labour market. If not more, it posts no vacancy and dismisses the excess at random (`:200-209`).
  - So: hiring and firing are symmetric and immediate and uncapped: the head count follows planned output within the period. No hiring or firing cost, no notice, no hysteresis. The only friction is the 5% random turnover, which sends workers back to the pool to be rehired in the same period's market.
- A firm with no workers: it still asks for what its output needs (required workers is computed from capital); it simply has `laborDemand` equal to the full need. A firm that cannot pay the wage bill defaults (`minWageDiscount = 1`, `ConsumptionFirmWagesEnd.java:136-155`: any shortfall of the deposit against the wage bill sends it to `bankruptcy()`), and restarts through the bankruptcy strategy.
- Government: `fixedLaborDemand = 1360` (`modelBenchmark_light.xml:2841`), the same turnover; the class is called "AntiCyclical" but its labour demand is a constant (17% of households), not a function of unemployment.
- Wages are paid at the end of the period (`TIC_WAGEPAYMENT`, after sales: the `WagesEnd` classes), which is why credit is sized to cover `nbWorkers * expectedWage` (`ConsumptionFirm.java:411-418`).

## Matching

- One labour market (`SimpleMarketSimulation`, `laborMarket`, `modelBenchmark_light.xml:345-365`), `nbRuns = 8000` passes, closed when no buyer or no seller is active (`AbstractMarketMixer.java:48-62`).
- Each pass (`SelectionRandomRobinBuyerMixer.invokeInteractions`, `jmab/mixing/SelectionRandomRobinBuyerMixer.java:99-125`): buyers (the 120 firms plus the government) are shuffled; each active buyer sees up to `nbSellers = 10` randomly chosen unemployed households and hires ONE, the one with the lowest ask (`SelectCheapestWorkerStrategy.selectWorker`, `:37-48`, used by both firm types, `modelBenchmark_light.xml:1816, 2109`; the government picks at random, `:2876`). The hire is unconditional: no comparison with any wage limit of the firm (`UnconstrainedLaborMechanism.java:30-37`, `worker.setEmployer(employer); employer.addEmployee(worker)`), and the wage paid is that worker's ask.
- Repeats until every firm's `laborDemand` is zero or no unemployed is left. So the market always clears on quantity: employed = min(total wanted, 8000). Unemployment is the residual `8000 - jobs wanted`. There is no vacancy that stays open beside an unemployed worker (the process continues until one side is empty); no matching function; no queue.

## Wage setting (the firm side)

There is none: the firm takes the ask of the cheapest of ten random unemployed. The only wage dynamics are the households' ask rule above (step about 0.7% a quarter, up only when unemployment is at most 8%, cuts only after an employed-recently spell). The wage a firm "offers" does not respond to its vacancies, and a firm cannot refuse to hire because it finds the ask too high. Prices follow as a markup on expected unit labour cost (`ConsumptionFirm.java:846-850`, paper eq 3.6), so wages feed prices, prices feed real consumption demand, and demand feeds sales, planned output and head count: that loop is the only path from wages to employment.

## Initial conditions (is the start sized to full employment?)

No: sized to the target unemployment rate, 8%. The paper (section on the stationary-state calibration, steps 1-3) solves the aggregate model in a real stationary state with exogenous values for "parameters for which some empirical information is available (e.g. unemployment rate, mark-ups, ...)". In the code the result is the initialiser's numbers (`modelBenchmark_light.xml:1385-1419`, read by `SFCSSMacroAgentInitialiser.java`): `ksEmpl = 1000` (50 per capital firm), `csEmpl = 5000` (50 per consumption firm), government `1360` of 8000: 7360 employed at period 1 and 640 unemployed, exactly 8%. Employed households are placed in order into firms (`SFCSSMacroAgentInitialiser.java:194-217, 337-344, 493-500`), the rest left with `employer = null`; the initial aggregate unemployment lag is set to `0.08 * (1 + draw)` (`:517`, flagged TODO). All other opening values (deposits 80704 for households, loans, capital stock 40000, prices 2.6875 and 1.03, wage 5, sales 5375 and 32971) are the solved stationary state, so firm head count, capacity, household income and propensities to consume (`0.385808` out of income, `0.25` out of wealth, `:2751-2757`) are mutually consistent: the demand that the 7360 jobs' wages create is the sales that need those 7360 jobs. The unemployed 8% is a calibration input, held in place by the demand system, not an outcome of the labour rules.

## Differences between the code and the paper

1. Reservation wage cut. Paper (eq 3.15): cut if unemployed for more than two of the last four periods; raise if unemployed for at most two and the aggregate rate is at most `upsilon`. Code (`Households.java:397-407`, `AdaptiveWageStrategy.java:46-52`): the "unemployment average" is built from employed flags (`LAG_EMPLOYED` = 1 if employed), starts with 1 for "now" and uses three lags, and the threshold is 0.49 on the share: so an unemployed worker cuts if he had a job in at least one of the last three periods, and the long-term unemployed raise (macro variable returns 0 for the unemployed, so the raise condition always holds for them). The sign of the spell test is inverted and the thresholds differ (>2 of 4 versus >=1 employed of 3). The employed also raise when unemployment is low, which matches the paper's intent.
2. Fixed number of workers from planned output; the paper (3.1.1, eq 3.5) says the same, but adds that excess workers are "randomly sampled from the pool of firm employees and fired" and a positive turnover share: the code also fires `ceil(0.05 n)` before any head-count decision, always at least one worker per firm, even when the firm is hiring. The paper does not say the dismissed are re-pooled and can be rehired in the same period by the same firm.
3. Government: the class `GovernmentAntiCyclical` has a constant labour demand and the dole is `0.4 * average wage`, a rule of the benefit, not anti-cyclical spending.
4. The paper says the model is solved for a stationary state with growth `gss`; the 8% input is hard-wired as head counts, not a parameter named in the config, and the aggregate lag `0.08 * (1+draw)` is a TODO in the initialiser.
5. Paper text: hiring and firing are "immediately able to adapt the number of employees" (validation section), which the code confirms; it says the high relative volatility of unemployment (13.25 versus 8.22 observed) comes from this.

## Comparison with our labour core

Our files: `sim/labour/market/DESIGN.md` (core), `sim/labour/market/{clearing,applications,asks,layoffs}.py`, `sim/economy/producers.py` `plan` and `_labour_bids`, `sim/economy/labour_bids.py`, `sim/economy/opening*.py`, `sim/labour/market/opening.py`.

- Unemployment is an input there, an outcome here. Caiani sizes the start so that 640 of 8000 are unemployed and sizes every firm so that its jobs produce the sales those wages create: employment, capacity and demand are one solved stationary state. Ours opens with producers sized by input-output from final demand (`opening_runs.py`: "Final demand plus what the producers of it consume fixes the quantity of every good"; `opening.py` `_open`), and the people left over are not employed by anyone: `sim/labour/market/opening.py` puts the working people nobody needs in the idle trade (own plots), `opening_own.py` `hired_share` counts the share of hours producers hire and gives the rest to plots. So we also size from demand, but the labour supply is not matched to it: our opening hands the producers' need to the people and leaves the remainder as unhired hours (the 52% in the brief), where Caiani chooses the head counts of the firms and the government so that the remainder is the target rate, and then solves demand to be consistent with that remainder. The relevant missing piece in ours is a labour-market-side solve: the stationary state with a target unemployment (or equivalently a target employment/participation) so household income, which depends on wages earned, is consistent with who is employed. (Caiani's own input is an empirical rate, 8%; our equivalent target would come from the participation and plot-labour rules, not a number.)
- Planned head count. Theirs: planned output (expected sales plus the inventory gap) divided by the labour a capital vintage needs, one unit of capital needs `1/6.4` worker, fixed coefficients, wage not in it. Ours: `producers.plan` chooses runs as `min(capacity_runs * share_working(revenue, variable), runs_for_stock, affordable)`, where `share_working` is a normal probability that a run's revenue covers variable cost (`producers.py:373-405`) and `affordable` is cash over cost per run (`:316-320`); hours follow as `runs * recipe.labour_hours[trade]` (`_labour_bids`, `:455-461`) with a ceiling per hour from `joint_labour_ceilings`, then `labour_bids.sloped_bids` splits each bid into four tranches whose ceilings average the bid's (`BID_TRANCHES = 4`, `BID_VALUE_SPREAD = 0.5`, temporary heuristics). In ours the wage enters the head count (through margin, ceiling and affordability); in theirs it does not, except through the end-of-period default rule and credit. Ours also has no expected-sales-plus-inventory target in `plan` (the expectation is of price, and `expected_sales.py` exists separately); Caiani's output target is exactly that, and it is what makes their unemployment follow demand.
- Firing. Theirs: every firm dismisses a random 5% every period, then fires any excess at random, immediate, symmetric. Ours (`applications.py`): `SEPARATION_SHARE_PER_ROUND = 0.05` of a firm's hours per search round, several rounds a year (Eurace's protocol), plus `layoffs.hours_to_lay_off` for excess. Same idea, different clock: ours takes 5% per round and runs many rounds per year, Caiani 5% per quarter. Hours replace workers; no per-worker identity, so a dismissed worker's ask cannot depend on the spell.
- Ask (reservation wage). Theirs: one number per household, steps of about 0.7% a quarter, up when unemployment is below 8% for employed workers (and always for the long-unemployed, by the sign slip), cut after a recent job; floor 0; no link to subsistence or the dole. Ours: `reservation_wage = subsistence_per_worker_year / hours * (1 + fatality risk * value of life years)` as a floor (`DESIGN.md`, "Clearing") with `asks.py` cutting the ask of searchers who found nothing (`RESERVATION_CUT_PER_ROUND`). Their floor is zero, ours a physical subsistence floor; their cuts are not driven by unemployment spells in the executed code, ours are driven by failing to find a vacancy.
- Matching. Theirs: no friction beyond ten random sellers per visit and the cheapest of them; every firm repeats until its demand is met or the pool is empty, so no vacancy and unemployed coexist. Unemployment is demand shortfall alone. Ours: bounded applications (`APPLICATIONS_PER_ROUND = 3`) to posters whose offer is at or above the ask, so a vacancy and an idle searcher can coexist when asks exceed offers. Caiani has no such wedge: the firm hires at the worker's ask without any limit. That means that in their model an ask above the firm's value of an hour cannot stop a hire; in ours it can (`maximum_wage`, `capped_asks`). A candidate cause of our persistent unhired mass is that wedge; theirs removes it by construction.
- Down-rigidity. Theirs: an employed worker's wage never falls, a firm cannot cut a wage (the ask moves only for the unemployed and employed raises). Ours (one market wage per trade and area, paid to retained hours and new hires alike; it falls to the clearing point at once): no per-employer contract wage, so a hired worker's wage is not rigid downward, unlike theirs.
- Government demand. They have a fixed public payroll of 17% of the households, in the unemployment base as employed; ours: no state employer in the labour core's opening (state demand arrives through recipes and bids); nothing like a fixed public workforce propping up the floor of employment.

### What made their unemployment stay at a plausible rate

From the code, in order of weight:
1. The start is the solved stationary state at that rate (calibration, not a labour rule).
2. Head count is a fixed-coefficient function of expected sales, adjusted every quarter with no friction, so employment tracks demand and unemployment is the demand gap, and demand is itself tied to wages paid (propensity 0.386 out of income and 0.25 out of wealth, household income and dole fed from firms' wage bills and the government).
3. The labour market closes completely each period (one hire per visit until all vacancies or all searchers are gone), so no unfilled vacancy and no wage-versus-ask wedge can strand workers.
4. Wage moves are small (0.7% a quarter) and the raise condition `u <= 8%` makes wages rise only when the economy is tight: a weak negative feedback on the rate around 8%.
Changing the labour parameters barely moved the series (table above); the stable rate is the calibration plus demand-determined head counts, not wage adjustment.

### Ideas, not code, for our side

- Test whether the unhired share is a vacancy/ask wedge or a demand gap by running our market with Caiani's rule (every posted hour is filled from the pool at the searcher's ask, no acceptance test) and see how much of the 52% remains.
- A producer's labour bid sized from expected sales plus an inventory gap on fixed labour coefficients (their `getRequiredWorkers`), compared with the share-working formula in `producers.plan`.
- A start where households' income comes from the jobs the opening actually offers (their solved stationary state), instead of an income ceiling with unhired hours put to plots.
