# Model run: Mark-0 (Gualdi, Tarzia, Zamponi, Bouchaud), labour market read from the code that runs

**Status:** report. Code built and run here; rules below are read from `mark0_covid.cpp`, not from the paper.

## Code, licence, build

- Repository: https://github.com/KarlNaumann/Mark0 (cloned to
  `/tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/models/mark0/code`).
  The model is one C++ file, `mark0_covid/mark0_covid.cpp` (725 lines), with a thin Python wrapper
  (`mark0_covid.py`, only builds the command line) and `default_parameters.yaml` / `default_hyper_parameters.yaml`.
  It is the Naumann-Woleske / Sharma "COVID" extension of the original Gualdi code: the same firm and household
  rules, plus a bank, a central bank and a shock switch (`doshock false`, off).
- Licence: MIT (`LICENSE`, Copyright 2022 Karl Naumann-Woleske). Running is fine; copying code into our repository is
  also allowed by MIT with the notice kept, but we take ideas only, as instructed.
- Build: the file includes `gsl/gsl_rng.h` and `gsl/gsl_sf.h`; libgsl-dev is not installed and apt cannot find it. The
  file uses only `gsl_rng_alloc`, `gsl_rng_set`, `gsl_rng_uniform` (Mersenne twister) and `gsl_sf_exp`. I wrote a
  four-line shim header directory (`scratchpad/mark0_scripts/shim/gsl/`, `std::mt19937_64` and `std::exp`) and built
  with `g++ -O2 -I shim`. Consequence: the random stream differs from the authors', so a given seed gives a
  different path than theirs; statistics are what to compare. A run of 5000 firms for 5000 periods takes about 2 s.
- Output: one line per period, `t u bust Pavg Wavg S Atot ...` (header in `mark0_covid.py` lines 79-100 comment names).

## The model in one paragraph

N firms, each a producer-employer; households are not agents: the household sector is one aggregate (`S`, savings;
`budget`) and the labour force is exactly N units (one unit of labour produces one unit of goods; firm i employs
`Y[i]` of the N workers; `e = sum(Y)/N`, `u = 1 - e`). So unemployment is not a matched stock of persons: it is the
share of the fixed labour supply not in anyone's `Y`. Time unit is one period (a month in the papers).

## Labour supply

- Every household supplies one unit, always (`e = Ytot / N`, line 426; `u = 1 - e`, line 427). There is no reservation
  wage, no participation choice, no household-level search. Supply is perfectly inelastic and equal to N.
- Households choose which firm to buy from by price (logit with intensity `beta`, lines 507-523) and spend a share
  `propensity` of (wage income + savings) (line 505, `G0 = c_0 = 0.5` default, plus a real-rate term when
  `alpha_c != 0`). The wage bill `Wtot = sum(W*Y)` is the household income.

## Labour demand: how a firm changes its workforce (lines 337-380)

Each firm remembers last period's demand `D[i]` (set at lines 519-523 as its share of the household budget divided by
its price) and its production `Y[i]` (= its employment). Once per period, in the update loop:

- `dY = D[i] - Y[i]` (line 323). The firm's only signal is the gap between last period's demand it faced and what it
  produced. There is no forecast, no inventory, no planned run; goods are not storable (sold `min(Y,D)`, the rest is
  lost: line 525, 527).
- Excess demand (`dY > 0`, lines 337-357): hiring `Y += min(eta * dY, u_share)` with `eta = eta0p * (1 + ren)` clipped to
  [0, 1], `eta0p = R * eta0m` (line 129, 340-344). `u_share` is the firm's slice of the unemployed:
  `u * N * (1 - bust) * exp(beta*(W_i - Wmax)/Wavg) / wage_norm` (line 329). So a firm can hire at most its
  wage-weighted share of the currently unemployed; the unemployed are rationed across firms by logit on wage
  (higher-wage firms attract more).
- Excess production (`dY <= 0`, lines 359-380): firing `Y += eta * dY` with `eta = eta0m * (1 - ren)` clipped to
  [0, 1] (lines 363-366). No cap beyond eta <= 1.
- `ren = Gamma * A_i / payroll_i` (line 313) is the firm's balance sheet (cash/debt `A` over its wage bill) times
  `Gamma = max(Gamma0 * (rm_avg - pi_used), Gammas)` (line 299). When the loan rate `rm_avg` exceeds expected inflation,
  indebted firms (A < 0) hire less (eta0p*(1+ren) shrinks) and fire more (eta0m*(1-ren) grows). With the
  default yaml `alpha_gamma = 50` (that is `Gamma0`) this couples credit to employment; at `alpha_gamma = 0` the
  rule reduces to the pure rates `eta0p`, `eta0m`.
- Hiring/firing asymmetry: `R = eta0p / eta0m` (default 2.0, yaml), the ratio of speeds. It is a relative speed, not a
  cap per period. A firm closes a fraction `eta0p` (0.2 at defaults) of its demand shortfall per period when hiring
  and a fraction `eta0m` (0.1) when firing.
- A firm with no workers: `Y[i] = 0` is not dead; hiring is `eta*dY` from `dY = D - 0`, so it restarts from demand as
  long as it is ALIVE and `u_share > 0`. A firm is dead only on bankruptcy: `A[i] <= -theta * payroll` (line 309),
  then `Y = 0`, `ALIVE = 0` (lines 408-415). Dead firms revive with probability `phi` (0.1) per period (lines 553-567)
  with `Y = max(u, 0) * rand` (a random share of the current unemployment), price and wage set to the market averages,
  and cash `W*Y`.

## Matching

There is none beyond the `u_share` rationing: no applications, visits, queues or hire order. A hiring firm takes up to
its logit-weighted share of the unemployed; the unemployed are interchangeable and never idle in a particular place.
All firms update in index order in one sweep (line 300), but `u_share` uses the `u` of last period's close, not a live
count, so ordering inside the sweep does not matter for hiring (total hired can slightly exceed the pool in a period;
`e` is clamped to 1 afterwards, line 618, and `e - 1 > ZERO` flags `collapse=2` and ends the run, line 612).

## Wage setting (lines 350-355, 372-378, 385)

- Excess-demand firm, only if its last profit was positive: `W *= 1 + (1 + ren) * rw * e`, `rw = U(0, gammaw)`,
  `gammaw = r * gammap` (defaults 0.1 * 1.0). The raise is scaled by the employment rate `e`, so wage growth is fast in tight
  labour markets. It is capped so the wage bill does not exceed revenue plus interest (line 353).
- Excess-production firm, only if its last profit was negative: `W *= 1 - (1 - ren) * rw * u`. The cut is scaled by
  the unemployment rate, so wages fall little when unemployment is low and faster when it is high.
- A profitable firm with excess production, or a loss-making firm with excess demand, leaves its wage unchanged. Wages
  are therefore sticky in a particular sense: cut only by loss-making firms facing slack.
- With `DOANTICIPATE` true (line 16, 382-386) every firm also multiplies price by `1 + pi_used` and wage by
  `1 + wage_factor * pi_used`, where `pi_used = tau_tar*pi_target + tau_meas*pi_avg` (line 297).
- Prices are renormalised each period by the average price (`RENORM`, lines 253-269), so the numeraire is the price
  level.

## Initial conditions

Not sized to full employment. `Y[i] = y0 + noise` with `y0 = 0.5` (line 178): half the workforce is unemployed at
t=0 (u = 0.50). Price 1, wage 1 (lines 177, 180). Firm cash `A[i] = 2*Y*W*rand`, normalised so that total money (household savings + firm
balances) = N (lines 183-211). Demand `D[i] = y0`. So the model starts at 50% unemployment and the dynamics move
it to its attractor.

## Measured runs (my runs, scratchpad scripts `run.py`, `scan*.py`)

All: N = 5000 firms unless stated, defaults from `default_parameters.yaml` (R = 2, alpha_gamma = 50, eta0m = 0.1,
gammap = 0.1, r = 1). My GSL shim changes the random stream.

Default parameters, seed 0, first periods: u = 0.500, 0.496, 0.491, 0.484, 0.477, 0.471, 0.464, 0.458, 0.451, 0.445
(about 1% of the workforce hired per period at first, then it accelerates). Unemployment falls to about 0.4% by about
period 150-250 and then stays at 0.33-0.45% (mean 0.0036, range 0.0032-0.0045 over t = 200-2000). The full-employment
residual of 0.4% is the floor set by firms that are bankrupt or have not yet revived (the paper's frictional
unemployment).

### The phase transition in R (alpha_gamma = 0, seed 0, T = 5000)

`alpha_gamma = 0` removes the credit effect on hiring and isolates the labour rule. Late-time unemployment (t >= 2500):

| R = eta0p / eta0m | behaviour |
|---|---|
| 0.5 | u rises from 0.50 to 0.99 and stays (late mean 0.984) |
| 0.8 | u hovers 0.43-0.58 (late mean 0.52), a high-unemployment equilibrium |
| 0.9 | falls to 0.004 by t~500, then drops to 0.83 at about t=1750 and recovers late (mean 0.69) |
| 1.0, 1.1, 1.2, 1.5 | u ~0.4% for the whole 5000 periods (seed 0) |
| 2.0 | u ~0.4% until about t~3900, then crashes to 0.8 and stays |
| 3.0 | full employment, crash at ~t=2250 to 0.79, recovers by t~4000 |

So the transition: R well under 1 (firing faster than hiring) gives a stable high-unemployment phase, R of about 1 and above gives full employment. Near
R = 0.8-0.9 both phases coexist in time. The pure-labour transition is near R about 0.9-1.0. In the paper's phase diagram this is the
boundary between the "full employment" and the "high unemployment" phase.

### A second, credit-driven route into high unemployment (not a labour effect)

Large R does not buy stability. With R at or above 1.5 the full-employment state is metastable: a bankruptcy cascade
tips it into u of about 0.8-0.98 with no change in parameters. Anatomy of one crash (R=2, alpha_gamma=0, seed 0, from my run `anat`): bust
(share of dead firms) 0.08 at t=3900, then 0.09, 0.10, 0.11, 0.14, 0.17, 0.23, 0.35, 0.49; u goes 0.045, 0.051, 0.061, 0.077, 0.10,
0.14, 0.22, 0.38, 0.58 in nine periods. Firms' debt equals household savings (S = -Atot), falling wages/prices
follow; unemployment settles near 0.8. Over 30000 periods and four seeds each (T = 30000, N = 5000, seeds 1-4):

| setting | share of periods with u > 0.5 per seed | note |
|---|---|---|
| alpha_gamma 0, R = 1.0 | 0.07, 0, 0, 0 | first crash at t=27905 in one seed |
| alpha_gamma 0, R = 2.0 | 0.46, 0.44, 0.46, 0.45 | first crash t = 2369-16379 |
| alpha_gamma 50 (default), R = 1.0 | 0, 0.36, 0, 0 | seed 2 crashed at t=10602 and the run stopped early (exit(1)) |
| alpha_gamma 50 (default), R = 2.0 | 0.80, 0.84, 0.33, 0.83 | first crash t = 5121-13727; seed 3 stopped at row 20196 |

The yaml's "full employment phase" default (R = 2, alpha_gamma = 50) is therefore the least stable setting measured:
roughly four fifths of a long run is spent in the crisis state. At R = 5, seed 0, the economy crashes at about t~2200 and stays.
The unemployment rate in the "high" state is 0.8-0.98, in the "low" state 0.3-1.0%, and the intermediate region is
traversed only during a crash or a recovery.

### The other parameters the authors name (seed 0 unless stated)

- `eta0m` (firing speed, with `eta0p = R * eta0m`), alpha_gamma 0, R = 2: 0.01 gives u of about 0.37 for hundreds of periods then a crash (75% of periods u > 0.5);
  0.03 recovers to 0.3% by t=400 then crashes (66% high); 0.1 gives 0.4% steady; 0.3 gives 1.1% steady. A faster
  adjustment lowers the crisis exposure but raises the residual (more churn and firm death). Start-up time scales as
  1/eta: u(t=100) = 0.46 at 0.01, 0.36 at 0.03, 0.003 at 0.1.
- `r = gamma_w / gamma_p` (wage vs. price flexibility), R = 2, alpha_gamma 0: r = 0 (frozen wages): u = 15% on average
  in t >= 500; r = 0.5: 0.5%; r = 1: 0.39%; r = 3: 0.28%. Wage flexibility matters through the `e` and `u` scalings
  above, and the labour market clears fast only if wages can move.
- N (1000, 5000, 20000) at R = 2, alpha_gamma 0, seeds 1-3, T = 5000: no crash in 5000 periods in any of the nine, low-state u 0.36-0.39%.
  No sign in these short runs that N matters for u; crashes are rare events on a 5000-period timescale and show up in the T = 30000 table.

## Code versus paper / documentation

- yaml default comments in `default_parameters.yaml` ("Default parameters ... full employment phase", `eta0m 0.1`,
  `gammap 0.1`) differ from the comments in `mark0_covid.cpp` lines 85-107 ("default: 0.2", "0.01", "default 0.04", "default 0.5"
  for alpha_c, G0 etc.). The cpp comments describe the older stand-alone program. The wrapper's yaml is what runs.
- The yaml names the credit-effect parameter `alpha_gamma` (2017-13); in the cpp it is `Gamma0`, and yaml `gamma_0` maps to `Gammas`
  (floor of Gamma). Both are positional on the command line (`argc == 31`), so a reordered yaml silently feeds the wrong
  parameter. The wrapper's order comes from `parameter_names` dict order in `mark0_covid.py`.
- The CB term for employment (`alpha_e * log(...)`, line 634) is commented out: `phi_e` (yaml) does nothing.
- `FACPI = 0` and `RENORM = 1`; `tau_tar` is forced to 0 when `alpha_pi < ZERO` (line 234). `phi_pi = 0` in the yaml means no
  Taylor rule; the central bank rate is the constant `rho_star`.
- `seed` -1 maps to 0 and the comment says there is no `seed_init`, but `seed_init` is used (line 161) for the initial
  draws.
- Accounting check (lines 432-453) calls `exit(1)` without a message when the identity (savings + firm cash - debt = M0)
  drifts by more than 1e-9. Several of my runs ended this way (rows stop early; seen 2 of 16 long runs, and at
  `eta0m = 0.03`, `R = 2`, `alpha_gamma = 50`: first `scan.py` run), so floating-point drift in the crisis state can kill the program
  and leave a truncated output file with exit status 1.
- The paper describes the phase transition in R; the code reproduces it (R below 1 stays high), but the "full-employment
  phase" is metastable in the code at the authors' default R = 2 over long horizons.

## Comparison with our labour core

Our setting: a producer plans yearly runs from expected sales (`sim/economy/producers.py` `plan`, lines 282-324,
via `expected_sales.py`, `OUTPUT_CHANGE_SHARE_PER_YEAR = 0.25` of capacity per year in `within_a_years_change`, line 327),
turns them into tranche bids for hours (`_labour_bids`, `sim/economy/labour_bids.py` `sloped_bids`), and the clearing
is in `sim/labour/market/` (`year.py`, `clearing.py`, `layoffs.py`, `asks.py`).

1. **Hiring/firing speed asymmetry.** In Mark-0
   `Y_i` (employment) moves by `eta * (D_i - Y_i)` every period, from last period's realised demand, a first-order lag
   with separate hiring and firing speeds (R). Ours has one symmetric lag (`within_a_years_change`: the same 25% of capacity up or down)
   and plans from expected sales and margin; there is no hiring/firing asymmetry parameter. Mark-0's phase transition
   lives in that asymmetry (R < 1 gives a stable high-unemployment state); our core has no equivalent knob to test.
2. **Rationing of the unemployed by wage.** Their hiring is limited by `u_share`, the firm's logit-weighted slice of the
   unemployed, so unemployment itself is the supply faced by all firms and a high-wage firm gets more of it. Ours matches
   applications to bids by wage and area (`applications.py`, `clearing.py`); no counterpart of "hire at most your share of
   the unemployed" exists as a rule, the quantity comes out of the clearing.
3. **Wage rule is an unemployment- and profit-conditioned multiplicative step.** `W *= 1 + (1+ren)*rw*e` only if profit was
   positive and demand exceeded production; `W *= 1 - (1-ren)*rw*u` only if profit was negative and production exceeded demand.
   Wage motion scales with `e` and `u`, and a firm that is profitable with slack, or loss-making with excess demand, leaves wages
   unchanged. In ours the wage is the clearing price of tranched bids and asks (`asks.py`, `fetch_wage.py`), not a per-firm
   state with a step rule. No counterpart: the cut-only-when-losing condition.
4. **Credit enters hiring in theirs** (`ren = Gamma * A_i/payroll`): an indebted firm hires less and fires more when the loan rate
   exceeds expected inflation. Ours: cash and held inputs cap runs (`affordable` in `plan`) and a firm that cannot pay labour does
   not bid (the cash constraint shows up in the bid size, not as a speed). The debt-deflation crash in Mark-0 (bust 0.08 to 0.49
   in nine periods) has no counterpart we measure; whether our `bank_*`/`credit_*` modules can produce a bankruptcy cascade that
   removes demand is a separate question.
5. **Demand feeds back to jobs through the wage bill.** In Mark-0 the household budget is a fixed share (`c_0 = 0.5` of wage income
   plus savings), so a loss of jobs cuts `Wtot`, demand, and `D_i`, and firing follows: the unemployment trap is the multiplier
   with no price relief fast enough. In ours a similar loop should exist (households spend wages, `expected_sales.py` `demand_seen`; not verified by me), but expected sales lag a year and the step is capped at 25% of capacity, so the multiplier runs year by year.
6. **Supply side.** Their supply is one unit per household, always offered, no reservation wage. Ours offers hours by household
   (`sim/economy/households_hours_offered.py`, `household_hours_year.py`; I did not read these for a reservation wage), so if there is one, part of our 52%/90% "unhired" is
   offered hours the household would give only at a wage the market never pays; Mark-0 cannot show that effect because its
   unemployed accept any job.
7. **Start.** Mark-0 starts at 50% unemployment with `y0 = 0.5` and closes it within about 200 periods at defaults, with no
   sizing to full employment; its dynamics decide where it settles. Ours opens at about 52% unhired and drifts up to 90%, the opposite direction.
   Since Mark-0 started at the same 50% and fell to 0.4%, what differs is the sign of the feedback from a labour surplus to
   hiring: in Mark-0, hiring is driven by `D - Y > 0`; a firm hires whenever its demand exceeds its output, and demand (a share of
   a household budget that is fixed in real terms by renormalising money) keeps rising with wage income. A test for ours: is
   there any state in which a producer's expected sales exceed its current runs and it still does not bid because of
   `share_working` or the cash cap?

## What I did not do

- Did not run the Python wrapper (needs pandas and yaml; not installed); drove the binary directly with the same argument order as
  `_model_call` (`mark0_covid.py` lines 289-308) and checked that order against `argv[1..30]` in the cpp.
- The Mark-0 paper's own phase diagram, and the stable phase at the paper's parameters, were not re-derived; only the
  yaml defaults and a one-dimensional scan of R, eta0m, r were run, with up to four seeds.
- Did not check whether the crash exit(1) is reproducible with the authors' GSL stream.

## Where the numbers are from

Scripts: `/tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/mark0_scripts/` (`run.py`, `series.py`, `scan.py`,
`scan2.py`, `scan3.py`, `scan4.py`); run each with `python3 -I`. Raw output files `out_*.txt` in the same folder (columns: t, u, bust, Pavg, Wavg, S, Atot, firm savings, debt,
inflation, ...).
