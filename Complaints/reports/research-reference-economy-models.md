# Reference economy models: Capitalism Lab, Eurace@Unibi, Econ-ARK HARK, Caiani et al. 2016

Research report for issue #61 (make the opening a steady state), Complaint 473 and its relatives
(606, 607, 641, 642, 643, 655, 497). It adds to, and does not replace,
`Complaints/reports/research-agent-based-economy-design.md` (Lengnick, Caiani, Wiese, Peters) and
`docs/architecture/ECONOMY_MODEL_SURVEY.md`.

## Sourcing key

- OPENED: I read the text in this session. Local copies were kept in the session scratchpad
  (`refs/`): the Eurace@Unibi clone, the HARK clone, and the Caiani PDF converted to text.
- SNIPPET ONLY: seen only in a search result summary.
- NO SOURCE FOUND: I looked and found nothing I could open.
- "Reading" marks my own inference from what I opened. It is not a claim by the source.
- No figure below is recalled from memory. Numbers quoted from a source are that source's, not this
  project's, and per CLAUDE.md 4.1 and 4.5 none should be copied into the simulator as a value. Only structure.

Repo state read: branch `test-audit-and-market-corrections` merged into
`research-reference-economy-models`; HARK clone head commit dated 2026-10-07; Eurace clone is the default branch
(depth 1).

---

## 1. Capitalism Lab (Enlight Software), game design only

**What it is.** A commercial business simulation game. This is game design, not evidence about how an economy works.

**Sources opened.** The publisher's marketing and guide pages only:
- https://www.capitalismlab.com/beginners-guide-gameplay-basics/ (OPENED, via a page fetch that summarises the page)
- https://www.capitalismlab.com/?p=5718 (OPENED, same method)
- https://www.capitalismlab.com/?p=7614 (the "Learning Microeconomics Through Simulation" page): fetch returned HTTP 404. Not read.
- Search snippets for the older original game's manual: SNIPPET ONLY.
- No official manual, formula page or wiki page that gives equations: NO SOURCE FOUND.

**What the pages say** (closely paraphrased):
- Prices and demand: a product has an overall rating built from price, quality and branding, with weights that differ by
  product (the guide gives cigarettes as mostly branding, with price a smaller share). Competitors and consumers buy from
  whoever's rating is high enough. When a rating is too low the guide advises cutting price first, because brand
  and quality take longer. Demand for an old product drops when a replacement is invented and on sale.
- Supply chain: industrial seaports sell raw and semi-finished goods, competitor firms can undercut them, freight cost
  rises with distance, factories and purchasing units keep buying inputs while there is inventory space and stop when
  it fills.
- Banks: loans up to the firm's current assets, interest only (principal need not be repaid), and inflation erodes the
  principal. Interest rate guidance is rules of thumb with no formula.
- Stocks: issue proceeds depend on the share price; a holder of half the shares takes over a firm, which ends the game.
- Not covered by the pages: any elasticity, rating formula, how AI firms set prices, how the interest rate moves,
  how share prices move, bonds, credit ratings.

**On our five problems.** (a) settling, (b) thin markets, (c) interest rate, (d) labour, (e) speed: NO SOURCE FOUND for any.
The pages describe player-facing behaviour only. A game that hands the player a seaport selling every raw material at
an exogenous price sidesteps exactly the problem this project has (prices that must come out of production), so
it would violate CLAUDE.md 4.1 and 4.5 if copied.

**Borrow.** Nothing concrete. One design echo that is already in the project: a buyer choosing among sellers on
a combined price and quality rating is the logit idea in Eurace and the switching rule in Caiani, which are documented.

**Licence.** Commercial closed-source game; no code. Ideas only, and there are no documented ideas to take.

---

## 2. Eurace@Unibi (Dawid, Gemkow, Harting, van der Hoog, Neugart)

**What it is.** A large agent-based macroeconomic model in C on the FLAME framework: households, consumption goods
firms, an investment goods firm, banks, central bank, government, a stock market clearing house, malls (retail outlets),
and a statistical office. Repository: https://github.com/ETACE/eurace_unibi (OPENED, cloned).
Version history in the README: 1.0.0 April 2014, 1.0.1 April 2016. Documents in `documents/`:
`EuraceUnibi-UserManual.pdf` (dated February 3, 2011, version 1.0, OPENED via pdftotext), and
`EURACE_Reference_Manual_with_table_list_indexed.pdf` (dated November 30, 2009, a variable and message table; skimmed,
and old: it predates the Unibi version).

**Papers it cites** (from the README and `LICENSE.md`, OPENED):
- Dawid, Harting, van der Hoog, Neugart (2018a), "Macroeconomics with heterogeneous agent models: Fostering
  transparency, reproducibility and replication", Journal of Evolutionary Economics.
- Dawid, Gemkow, Harting, van der Hoog, Neugart (2018b), "Agent-based macroeconomic modeling and policy analysis: The
  Eurace@Unibi Model", Oxford Handbook of Computational Economics and Finance, ch. 17, pp. 490-519.
- I tried to open the Bielefeld repository copy (pub.uni-bielefeld.de); it served a bot-check page. A search
  result indicated a working paper copy exists (https://pub.uni-bielefeld.de/record/2915476, SNIPPET ONLY). I did not read
  either paper. Everything below about Eurace is from the repo code and the 2011 user manual.

### Agents and sequencing

Households (workers/consumers, own an index share, hold a payment account), consumption goods firms (Leontief
production on vintages of capital, user manual section 3.2; the manual introduction says Unibi uses Leontief and vintages
where the original Eurace used Cobb-Douglas), an investment goods firm, banks, the central bank, government, a clearing
house for one stock index, and a statistical office (directory listing; user manual Chapters 2 to 8). Time runs in
days within months (code uses a 240-day year for interest, `Bank_send_account_interest`), with firms acting on activation
days and monthly planning.

### Market protocols

- **Goods.** Firms deliver to malls. A household with a weekly budget sees the prices and quality of what each mall
  offers and picks a firm by a logit on price (equation 3.26 in the user manual, `Household rank and buy goods 1`); if the
  choice is rationed, the leftover budget goes to a second choice by the same logit. So a buyer always meets a
  list of live prices, and rationing is explicit (`Household receive goods read rationing`).
- **Labour.** Firms post vacancies with a wage offer per skill group; unemployed households compare offers net of
  commuting cost with their reservation wage, rank and apply, firms pick (user manual Chapter 4). Firm rule (code
  and manual quote): if vacancies exceed a threshold, `WAGE_OFFER = WAGE_OFFER*(1+WAGE_UPDATE)`. Household rule: an
  unemployed household lowers its reservation wage by a constant fraction, floored at a share of unemployment
  benefit (`Household update wage reservation`).
- **Credit.** The central bank base rate is a constant in the model (user manual 7.1.2: "The ECB base interest rate is a
  constant in the model"). Banks pay deposits at base rate times one minus a markdown, and lend to a firm at the base
  rate plus a firm-specific markup. In `Bank decide credit conditions` the bank computes a bankruptcy probability from
  the firm's debt plus request over equity, `1 - exp(-(debt + request)/equity)`, caps credit by the bank's excess value
  at risk (alpha times equity minus value at risk) and by excess liquidity over a reserve ratio, and charges
  `MIN_INTEREST + BANK_GAMMA * new_value_at_risk * 0.01 * random(0,1)`. A bank already in debt to the central bank
  does not lend. Firms accept loans lowest rate first.

### Price and wage setting

- Firms set price by an annual (price-setting-month) choice from a grid of candidate prices over a bounded range. The code
  (`Market_Research/Firm_market_research_functions.c`, around lines 560 to 600 and 1855 to 1890) sets
  `PRICE = MARKET_RESEARCH_DATA_PRICING.array[i].price` for the best candidate by expected earnings, where expected demand
  at each price comes from a customer survey (questionnaire functions in the same file). The range is a start and
  end price with an increment (fixed 1.0 to 1.4 at a product's release; otherwise `MR_START_PRICE` to `MR_END_PRICE`; I did not trace how those
  two are set). The fallback in `Firm_calc_pay_costs` (`Cons_Goods/Firm_Producer_Functions.c` line 1362) sets
  `PRICE = LABOUR_COSTS_PRODUCTION / PRODUCTION_QUANTITY * (1 + MARK_UP)` when there is no previous price, and every month
  `UNIT_COSTS` includes capital charge and interest, and `ACTUAL_MARK_UP` is computed.
- Production quantity: planned from market-share estimates by linear regression plus a safety buffer from a quantile of the
  demand-estimate variance (`Firm_calc_production_quantity`).
- Wage: see labour above. No market-clearing wage.

### Initialisation (OPENED, user manual Chapter 10, lines around 6485 to 6715 of the text)

- Stated principles: balance sheets must be initialised stock-flow consistently, "If the balance sheets would be
  inconsistent from the start they would remain so throughout the entire simulation", and start from plausible values
  "in order to alleviate the initial transient effects that any initialization invariably has. In our experience large
  path dependencies can be generated by such initial transients".
- Method: constants chosen so that the aggregates agree. Firm output is set so that total labour demand "would
  correspond to full employment" (output per firm proportional to households per firm); capital stock sized so the
  initial output needs no new investment; firm cash set equal to capital value; initial loan fixed by a leverage ratio;
  past investment financing set to exactly offset monthly depreciation so capital stays constant, with the loan repaid over a
  longer period "to stabilize the simulation with regard to bankruptcies at the beginning"; capital good price a fixed
  multiple of the wage; households start unemployed with a reservation wage equal to the firm offer so they are hired in
  month one; household cash and wealth set from multiples of monthly income. Section 10.2 lists the realised values.
- The repo also ships `its/0_after_2k_transient.xml.tar.bz2` and `its/0_default.pop`. By file name this is a saved state
  after a transient of 2000 iterations, but I did not unpack it and the README does not describe it. So I
  cannot say what it contains; treat the purpose as unverified.

### Stock-flow consistency and validation

- User manual Chapter 2 builds balance sheets for every agent type, defines the money invariant (household, firm,
  bank and government deposits plus bank reserves equal fiat money plus credit money) and Chapter 11 lists 33 tested
  rules: balance sheet identities (assets equal liabilities plus equity per agent type), cross-agent identities (bank
  loans equal firm debts; household money equals household deposits; bonds equal holdings), and the monetary
  conservation rule. The manual says these were "successfully tested".
- Household consumption (user manual 3.3.2, OPENED): `CONSUMPTION_BUDGET = MEAN_NET_INCOME + CARROL_CONSUMPTION_PARAMETER *
  PAYMENT_ACCOUNT + TRADING_ACTIVITY * CARROL_CONSUMPTION_PARAMETER * (asset_wealth - WEALTH_INCOME_RATIO_TARGET *
  MEAN_NET_INCOME)`. The manual (10.1.3) names it "the constant from buffer stock saving theory", a target wealth to
  income ratio and a target savings rate. That is a Carroll-type rule: income plus a small fraction of the excess over target
  wealth. The manual says the initial values are a payment account equal to 15 monthly wages and index assets worth 10 monthly
  wages (the numbers are the authors' choices, not sourced from data in that chapter).
- External validation against data for the 2011 manual: NO SOURCE FOUND in what I opened. The papers cited probably
  contain it; I did not read them.

### On our problems

- (a) Settling: it does not settle by waiting. It sets consistent balance sheets from ratios, avoids first-year
  failures by lengthening loan repayment, and (per file names, unverified) ships a post-transient state. The manual
  concedes initial transients exist. No analytic stationary solve.
- (b) Thin markets: prices are chosen from a bounded grid around a cost-plus start and every buyer sees a list of live
  prices, so a price without trade does not persist as a market price in the way described in 642. Rationing is a
  separate explicit step.
- (c) Interest rate: anchored on an exogenous constant base rate, plus a loan markup from a default probability,
  capped by the bank's value-at-risk headroom. It cannot sit at zero or a ceiling by a clearing glut. The cost is
  that the base rate is not endogenous.
- (d) Labour: vacancies and reservation wages with a floor; output sized at full employment at the start.
- (e) Speed: NO SOURCE FOUND in the manuals I opened. It is C code run under FLAME, with a monthly step.

### What this project could borrow

1. **Opening by ratio and identity** (`sim/economy/opening.py`, `opening_income.py`, `opening_basket.py`,
   `opening_stores.py`): size producers' capacity and workforce from one final demand so labour demand equals the labour
   supplied. This is the same fix 473's own text asks for ("producers' capacity, workforce and households' income agree").
2. **Past investment equals depreciation at the start** (capital financing exactly replacing wear): the analogue here is
   the metal and coin wear that drains the money stock (473). Set the opening mint inflow equal to wear.
3. **Explicit credit-rate formula** (`sim/economy/credit.py`, `lending.py`, `banks.py`): rate equals a policy anchor plus
   a markup from the borrower's default probability, with a cap from the lender's capital headroom. Compare Complaint 641.
4. **The Carroll-type consumption rule** for `households_orders.py` (see section 3 below, where the source is clearer).
5. **A rule-list validator** (`sim/economy/money_audit.py` exists) extended to Eurace-style cross-agent identities as a test.

**Licence.** Custom EULA in `LICENSE.md` and `EULA.rtf` (OPENED). Use and modification are allowed without
distribution. Distribution of the package or modified versions needs prior written permission from the owner, modified
versions must be renamed and documented, and publications must carry the stated acknowledgement. So **ideas only**.
Do not copy code into this repository, which is a distributed project.

---

## 3. Econ-ARK / HARK

**What it is.** A Python toolkit for heterogeneous-agent economics. Repository: https://github.com/econ-ark/HARK
(OPENED, cloned; `pyproject.toml` version 0.17.2). Licence: Apache 2.0 (`LICENSE`, OPENED).

### Buffer-stock model

`HARK/ConsumptionSaving/ConsIndShockModel.py` (OPENED) solves a consumer with CRRA utility, geometric discounting, a
survival probability, permanent income growth, and income shocks that are either fully transitory or fully permanent,
including a probability of unemployment-like zero income (`construct_lognormal_income_process_unemployment`). Default
agent parameters at line 1178 onward: relative risk aversion, a risk-free interest factor, a discount factor, a
survival probability and a permanent income growth factor are inputs (values there are the library's illustrative
defaults and I do not endorse them for any era). A borrowing constraint can be set (`BoroCnstArt`).

The module docstring says it solves a perfect-foresight model, the model with income risk, and a version where debt
has a different interest rate from savings. Other models (`ConsMarkovModel`, `ConsAggShockModel` with a Krusell-Smith
case, `ConsPortfolioModel`, `ConsWealthPortfolioModel` and others) are in the same directory.

### How a steady state or ergodic distribution is found

Three mechanisms, all OPENED:
1. **Conditions for existence.** `check_conditions` evaluates named impatience conditions (absolute, return, finite human
   wealth, growth, and a risk-modified growth condition `GICMod`) and returns a message on whether a non-degenerate
   solution exists and whether a target ratio of market resources to permanent income exists (lines ~1648 to 1930
   and ~2614 to 2790).
2. **Target wealth ratio.** `calc_stable_points` (line 1929) finds `mNrmTrg`, "the target values of market resources",
   as the market-resources ratio at which expected change is zero, by a Newton root of
   `Delta_mNrm_ZeroFunc(m) - cFunc(m)`, and `mNrmStE` for balanced growth. It runs only for single-period infinite
   horizon problems after the consumption function is solved.
3. **Stationary distribution.** `HARK/simulator.py` `find_steady_state` (line 1813) builds the transition matrix of a one
   period infinite horizon model and takes the eigenvector for the unit eigenvalue as the steady state distribution
   of arrival states; `get_long_run_dstn` and a population-average method read it off. `SSJutils.py` builds
   sequence-space Jacobians around that steady state. `Market.solve` (`HARK/core.py` line 2720) finds a fixed point
   between the agents' belief about aggregate dynamics and the dynamics their choices generate, looping until a tolerance.

HARK is a partial equilibrium household toolkit with a market fixed point for aggregates. It has no goods market,
firms, banks, labour matching, or money.

### How it could inform a household's savings wish and drawdown (Complaints 606 and 607)

The project's savings wish is `savings_target` in `sim/economy/households_orders.py` (lines ~105 to 114): years of
surplus income times a response to the real rate over `HOUSEHOLD_TIME_PREFERENCE`, floored and capped, all declared
`temporary_heuristic`. Spending is limited by `WEALTH_DRAWDOWN_LIMIT` and `SPENDING_CUT_LIMIT` (lines ~206 to 212).

What HARK offers (reading, from the code above):
- A principled source for the wish: under a given time preference, risk aversion and income risk (a chance of lost
  income, which for a peasant household is a harvest failure), the buffer-stock solution gives a consumption function
  and a target ratio of wealth to income that is the wealth at which the household neither accumulates nor draws down.
  Its inputs are physical or demographic (interest rate, growth of income, survival, income volatility, discount factor),
  so the wish is derived and not a stored multiple. This matches CLAUDE.md 4.1 and 4.4: the figure `SAVINGS_YEARS_OF_SURPLUS_INCOME`
  would retire to a function of income risk and the discount factor, and the drawdown limits would retire to the
  consumption function.
- Existence conditions are checked, so a household with a discount factor too patient for the rate has no stable wealth
  and the code says so. That is a built-in test that a configuration has a resting point. The project could run the
  same inequality check on its own constants as a unit test (the "test of a rule calls the rule" pattern in CLAUDE.md 6).
- The target-ratio logic also says the household's wealth to income ratio at rest depends on the real rate: this is the
  mechanism the project already approximates with `response` in `savings_target`, but derived.
- The Eurace rule (section 2) is a simpler cousin of the same idea: income plus a small fraction of the gap to a target
  wealth to income ratio. It is a one-line rule that can be used without any solver.

Limits. The discount factor, risk aversion and income-risk parameters are inputs HARK does not supply for a pre-modern
household: **no source found** for those here, and 606's own progress notes say the same for years of surplus
income. So HARK moves the unsourced figure from "years of income" to "discount factor and income risk", which are at
least quantities one can estimate from harvest variance in this project's own weather and yield models (a project
measurement, not a published value).

### On our problems

- (a) Settling: the idea that matters is a solved stationary distribution that is checked before use, and an
  existence check. For households alone only.
- (b), (c), (d): NO SOURCE FOUND in HARK: no goods market or labour market. (c) The household side gives lenders a supply of
  saving that depends on the real rate through the Euler equation; that is a savings supply curve, not a rate rule.
- (e) Speed: reading, the eigenvector solve replaces simulating many years to reach a distribution. It could
  replace years of household spin-up. I did not measure anything.

### What this project could borrow

- A function `stationary_wealth_ratio(real_rate, income_growth, income_risk, discount_factor)` replacing the body of
  `savings_target` in `sim/economy/households_orders.py` and the declared constants around it; opening households' cash
  and savings set at that ratio in `sim/economy/opening_stores.py` and `opening_income.py`, so the opening starts at the
  household's own resting point.
- Use of the Euler-equation consumption function as the drawdown rule: wealth above target is drawn down at a rate that
  falls out of the marginal propensity to consume, replacing `WEALTH_DRAWDOWN_LIMIT`.

**Licence.** Apache 2.0, so code can be reused or vendored with notice, but it is a numpy/scipy/numba stack. Whether
the project accepts those as dependencies is a decision for the owner (I did not check `requirements`). A simple closed-form
rule written here, citing Carroll via HARK's docs and the Eurace manual, avoids the dependency.

---

## 4. Caiani, Godin, Caverzasi, Gallegati, Kinsella, Stiglitz (2016)

**What it is.** "Agent Based-Stock Flow Consistent Macroeconomics: Towards a Benchmark Model", Journal of Economic
Dynamics and Control 69, 375-408. A closed economy of households, consumption firms, capital firms, banks, a government
and a central bank, with all stocks and flows in a balance sheet and transaction flow matrix. OPENED in full: the
Columbia copy,
https://business.columbia.edu/sites/default/files-efs/imce-uploads/Joseph_Stiglitz/Agent%20based-stock%20flow.pdf
(34 pages, downloaded and converted). Equation numbers below are the paper's. The earlier report in this directory covers
the same paper; items below are re-read and added to it, with the appendix on the stationary state read in full.

### Stationary state and calibration before running (section 4, Appendix A)

- The paper says initial stocks and flows must respect quadruple entry (Copeland), then six steps (OPENED, lines
  ~985 to 1017 of the text):
  1. Derive an aggregate version of the model.
  2. Constrain it to "a real stationary state associated with a nominal steady growth equal to g_ss": all real
     quantities constant while all prices and wages grow at the same rate.
  3. Solve the constrained system numerically, setting exogenously "reasonable values for the parameters for which some
     empirical information is available (e.g. unemployment rate, mark-ups, interest rates, and income and profit tax
     rates) or that we want to control (e.g. technological coefficients, number of agents in each sector, distribution of
     workers across sectors, loans and capital durations)". The solution gives every initial stock and flow and also
     "the values of some behavioral parameters", for example the propensity to consume out of income.
  4. Distribute each sector's aggregate uniformly over its agents.
  5. For loans and capital with ages, assume each past period's real value was constant and the inflation rate constant, and
     derive the outstanding values from the amortisation schedules, so that they sum exactly to step 4's totals.
  6. Assign matching partners (suppliers, banks) so each supplier or bank has the same number of customers.
- Appendix A.1 to A.3 writes the stationary system in three solved blocks: capital firms (ten equations in ten unknowns,
  with real output equal to replacement investment, price equal to markup times unit labour cost), consumption firms
  (twelve equations, with capital replaced at 1/lifetime of the stock each period and linear amortisation), and households,
  banks, government (consumption `c = alpha1 * net income / price + alpha2 * net wealth / price`, equation A.26, with
  real consumption equal to the output of consumption firms, equation A.27; bank reserves equal to the central bank's bond
  holdings as a residual).
- Table 3 in the appendix labels each parameter as set before the steady state (`pre-SS`), derived from it (`SS-given`),
  or free. The paper says the SS-given parameters are tied to the initial set-up: "Changing their values would then
  impose an exogenous shock on the model".
- Symmetry: all agents in a sector start identical, so heterogeneity is generated by the stochastic adaptive rules and
  not by arbitrary initial differences.
- The paper then states plainly that starting there "does not imply in any way that the model dynamics sticks to the
  steady state employed in the calibration" (section 5.1). The baseline shows an early run of growth, a recession, and
  recovery to a "stochastic steady-state" or "quasi steady-state", and the authors explain why they analyse the
  later part. They add that the initial symmetry itself causes the first rise in unemployment (footnote 21).
  So a stationary state start does not remove a transient; it removes arbitrary inconsistency and makes the transient
  an outcome the model owns.

### Price, wage, interest rules

- Price (3.6, 3.7): `price = (1 + markup) * expected_average_wage * workers / output`, i.e. markup over expected
  unit labour cost; the markup moves by a folded-normal draw, down when last period's inventories were above the desired
  share of sales, up when below. Expectations are adaptive (3.1).
- Reservation wage (section 3.4): if unemployed more than two quarters of the last year, lower the asked wage by a
  stochastic amount; otherwise raise it, provided last period's unemployment is "sufficiently low". Unemployed workers
  receive a dole equal to a share of the average wage.
- Interest: loan rate `i_t = i_{t-1} * (1 + FN)` if the bank's capital ratio is below the sector target, `(1 - FN)`
  otherwise, with `i_{t-1}` the market average (3.12); the sector target is last period's sector average; the deposit
  rate uses the liquidity ratio the same way (3.14). Central bank cash advances carry a constant rate that "represents
  the upper bound" for deposit rates (line ~958 of the text).
- Credit is rationed case by case: a logistic default probability from operating cash flow against debt service (3.13);
  expected return on the loan includes collateral recovery by fire sale (capital firms have none); the bank lends if the
  expected return is not negative, else the largest amount for which it is.

### Bank capital rules

- A mandatory minimum capital ratio (stated as 6 percent in a footnote) and a minimum liquidity ratio (stated as 8
  percent in the text), plus the endogenous target above. A failed bank is recapitalised by cutting deposits "up to
  the point the bank's capital ratio equals the minimum capital adequacy requirement (6%), similar to a bail-in".
  Failed firms are bailed in by households "in order to maintain the number of firms and banks constant". The
  percentages are the authors' parameters; do not copy them (CLAUDE.md 4.1).

### Validation

- Internal: the balance sheet matrix and transaction flow matrix (paper Tables 1 and 2 in the appendix are checks on the
  initial period) and the check that the identities hold over the whole run; the stock-flow checking is stated in
  section 5 (the paper says the model satisfies these conditions "over the complete simulation time-span").
- External: 100 Monte Carlo runs of 400 periods, compared with stylised facts from other agent-based macro papers and
  empirical studies: relative volatilities against US data (as reported there: consumption relative to GDP 0.79 against
  0.80, investment 4.45 against 4.61; unemployment relative volatility 13.25 against 8.22, which the authors attribute to
  ease of hiring and firing), autocorrelations, cross-correlations, firm size and growth distributions, bank credit network
  (the later parts of section 5.2). They also vary parameters (credit-market risk aversion, near the end of section 5) to show
  the convergence to the quasi steady state holds across settings.

### On our problems

- (a) Settling: this is the closest published answer. Solve the aggregate stationary state, derive stocks and
  behavioural parameters from it, distribute. Gives a pass or fail test: do the identities hold at the start?
  But expect the model to leave the state; they treat what follows as a transient to be described, not hidden.
- (b) Thin markets: prices are rebuilt each period from expected unit labour cost times a bounded adaptive markup, so a
  firm with no sales keeps a cost-based price, never a remembered one (reading of eq. 3.6 and 3.7). Buyers sample a subset
  of suppliers and switch with a probability that rises with the price gap.
- (c) Interest rate: anchored to the sector's average rate and moved by the bank's own capital ratio relative to the
  sector target; deposit rate bounded by a central bank advance rate. A rate has no reason to go to zero by lender
  glut.
- (d) Labour: unemployment is an input to the stationary state. Firms plan labour from expected sales and fire
  excess at random; the authors note this makes unemployment too volatile against data, so unlimited ease of
  hiring and firing is itself a validation miss.
- (e) Speed: the paper reports 100 runs of 400 periods; no timing found in the text I read. NO SOURCE FOUND.

### What this project could borrow

1. A module (new, short, e.g. `sim/economy/opening_stationary.py`) that solves the opening's stationary state as a
   fixed point in real terms: producers' output equal to households' purchases plus replacement of worn stock; wage
   bill plus profit plus rent equal to household income; money stock and mint flow such that coin struck equals coin
   worn; saving equal to investment plus lending needs; labour demand equal to hours supplied net of own plots. It would
   replace what `opening.py`, `opening_income.py` and `opening_basket.py` do by fixed income and a hidden spin-up, and
   would give `spin_up_state.py`/`settlement.py` a target.
2. Derive behaviour parameters from that state where possible (Caiani's step 3), for instance the household propensity
   `alpha1` and bank/lender targets, so that constants like `SAVINGS_YEARS_OF_SURPLUS_INCOME` stop being free
   (Complaints 606 and 607; the paper's own "pre-SS / SS-given / free" labelling maps onto this project's
   `temporary_heuristic` and `retire` tags, `python3 sim/constants.py --burndown`).
3. A cost-anchored ask with a bounded adaptive markup in `seller_offers.py` and `seller_pricing.py` for 642 and 643 (as
   the earlier report ranked first), which also fixes "a price where nothing traded".
4. Interest-rate rule from capital-ratio gap against a sector target and a ceiling set by a lender of last resort
   (`credit.py`, `lending.py`, `banks.py`, `bank_spread.py`) for 641 and 655.
5. A yearly stock-flow identity test and an initial-period identity test (the paper's Tables 1 and 2) as the pass or fail
   gate for the opening.

**Licence.** A journal article; the equations are the authors' published work, copyright Elsevier. Code: none in the paper
(NO SOURCE FOUND for an accompanying repository in what I opened). Ideas only, cited.

---

## 5. How the four compare on the five problems

| | Capitalism Lab | Eurace@Unibi | HARK | Caiani et al. 2016 |
|---|---|---|---|---|
| (a) opening that never settles | no source | consistent balance sheets from ratios; shipped post-transient state (unverified); concedes transients | stationary distribution and target ratio for households only | solved real stationary state, parameters derived from it, then a quasi steady state |
| (b) thin-market prices | no source | bounded price grid, logit over live prices, explicit rationing | no goods market | cost-plus with bounded adaptive markup; random supplier sampling |
| (c) interest rate at 0 or ceiling | rules of thumb only | exogenous base rate, default-probability markup, VaR headroom | savings supply from the Euler equation only | rate moves with capital ratio gap; central bank advance rate as ceiling for deposits |
| (d) unhired labour | no source | vacancy and reservation wage rules; output sized to full employment at start | no labour market | unemployment is a calibration input; adaptive reservation wage |
| (e) slow year | no source | no source found | eigenvector replaces long simulation (reading) | no timing found |
| Licence | closed game | custom EULA, no redistribution | Apache 2.0 | Elsevier article |
| Reuse | none | ideas only | code or ideas | ideas only |

---

## 6. Ranked recommendation for issue #61 (make the opening a steady state)

1. **Take Caiani et al.'s approach as the design.** Build a stationary-state solver for the opening in real terms,
   with the identities of this project's own accounts (`sim/economy/accounts.py`, `money_audit.py`) as constraints, derive the
   stocks and the behavioural parameters from it, distribute them over agents, and treat what follows as the model's own
   transient. It is the only source that addresses the whole problem (production, labour, credit, money) and it states
   what it does not promise (the model leaves the state). It also fits CLAUDE.md 4.1 and 4.2: stocks come from
   physical and accounting constraints, and the baseline is allowed to move afterwards.
2. **Use Eurace's initialisation recipe as the worked example inside step 1.** Size output so labour demand equals
   labour supply, set investment history equal to depreciation, and lengthen the first debts to avoid
   an early failure wave. These are specific, documented, and ideas-only under their licence.
3. **Use the buffer-stock idea (HARK, with Eurace's Carroll-type rule as the simple form) for households' wealth.**
   Make household opening wealth and `savings_target` a function of rate, income growth and income risk. This addresses
   606 and 607 directly. It does not remove the need for sources of the discount factor (no source found).
4. **Capitalism Lab: nothing to take.**

**First step.** A one-year-closure test, written before any code (CLAUDE.md 6, TDD): from a small fixture
(`sim/tests/economy_fixture.py`), derive the opening's real stationary quantities by hand-sized equations (household
spending equals producers' sales; wages plus profits equal income; coin struck equals coin worn; hours demanded equal hours
supplied net of own plots), then assert that stepping one year leaves every price, the rate and the money stock within a
stated band of the start. It fails today for the reasons 473 records. Then write the solver as a plain function in a new
small module, called from the opening, and make the test pass. After that, move the savings wish onto the buffer-stock rule
and re-measure with `python3 sim/simulator.py spin-up-trace`. Run the fingerprint only as a record of how much changed
(CLAUDE.md 6: a gameplay change is meant to change the simulation).

## 7. Caveats

- Eurace: I did not read the two Dawid et al. papers (the repository copy served a bot check; the search result is SNIPPET
  ONLY). The user manual is the 2011 version; the code is later (2014 to 2016), and the manual and code can differ. The
  price grid range constants were not traced to their definition.
- Eurace's `its/0_after_2k_transient.xml.tar.bz2` was not opened; any claim about what it holds is a guess from its name.
- HARK: I read the consumption-saving module headers, the stable-point code, the steady-state method and `Market.solve`; I
  did not run any of them, and I did not check which of the project's dependency rules apply.
- Caiani: a PDF to text conversion garbles some equation symbols; the structure of 3.7 (markup up when inventories
  fall short, down when they exceed) is read from the surrounding sentence.
- Capitalism Lab: the page fetches return summaries, not verbatim pages, and none of the pages state formulas.
- Nothing here was run in the simulator. Statements about this repository's modules are from reading the file names and
  the functions named; the earlier report has the line-level departures.
