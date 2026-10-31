# Model run: BAM (Delli Gatti et al. 2011), via the `bamengine` Python package

## Source and licence

- Implementation: BAM Engine, `https://github.com/kganitis/bam-engine` (PyPI `bamengine`), commit
  `50e14d175d98ff6f4cc89338d0bff2c05fffb70e`, cloned to
  `/tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/models/bam/src`.
- Licence: MIT. Running locally is fine; redistribution is allowed with the notice, but we take ideas only.
- Dependencies are only numpy and PyYAML (both present); Numba is optional.
- Other implementation: NetLogo, `github.com/alexplatasl/BAMmodel` (not read; the package's own paper says it deviates
  on several metrics).

## Run status: NOT RUN

The measured unemployment series the brief asks for does not exist. The one attempt to run the package (`python3 -I`
on a runner script that put the package's `src/` on `sys.path` and stepped 1000 periods) was refused by the session's
permission classifier ("Code from External"). I did not retry or route around it. Everything below is from reading
the code, with file and line; none of it is observed behaviour. To run it, approve:

    python3 -I /tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/scripts/run_bam.py \
      /tmp/claude-0/-home-user-bootstrap-history/3fd926e9-2dd6-5683-a341-1f67fe54596b/scratchpad/models/bam/src/src base '{"n_periods":1000}'

(The script prints the first 12 periods and mean/min/max by window; I wrote it but it was never executed. It lives in
the scratchpad, not the repository.)

Numbers the package reports about itself, which I did not reproduce: its docs example prints "Final unemployment
rate: 4.20%"; its validation target is mean unemployment 0.065 +/- 0.025 (book Figure 3.2b mean 0.0646), with a hard
gate that fails the run if the maximum exceeds 20% (`src/validation/scenarios/baseline/targets.yaml` lines 113-120).

Parameters the config suggests matter for unemployment (I did not vary them, nothing ran): `theta` (contract length,
8 quarters), `max_M` (applications per worker per quarter, 4), `h_xi` (wage-offer shock cap, 0.05), `h_rho`
(production shock cap, 0.10), `labor_productivity` (0.5).

Paths below are under `src/bamengine/` in the clone.

## Labour rules in the code

Time step is one quarter. Default 100 firms, 500 households, 1000 periods (`config/defaults.yml`).

**Labour supply.** Every household is a worker with one indivisible unit of labour (one `employer` id, one `wage`).
There is no reservation wage: an unemployed worker applies to any firm and takes whatever is offered. Nobody leaves
the labour force. The only worker-side state beyond employment is `employer_prev`, `contract_expired`, `fired`
(used by the loyalty rule).

**Labour demand** (`events/_internal/planning.py`):
- `firms_decide_desired_production` (l.24): expected demand = last period's production, times (1 + shock) if
  inventory is zero and price >= average, times (1 - shock) if inventory is positive and price < average, otherwise
  unchanged; shock uniform in [0, `h_rho`]. So production moves at most 10% a quarter.
- `firms_decide_desired_labor` (l.323): `ceil(desired_production / labor_productivity)`. One worker yields a fixed
  0.5 goods; no wage enters the hiring decision.
- `firms_decide_vacancies` (l.365): vacancies = max(desired - current, 0).
- `firms_fire_excess_workers` (l.396): if current exceeds desired, fire the whole excess at once, victims chosen at
  random. Hiring is limited by who applies; firing is immediate and complete (asymmetric).
- Credit-driven firing, `events/_internal/credit_market.py` `firms_fire_workers` (l.466): a firm whose wage bill
  exceeds its funds after the credit rounds fires random workers until the gap is covered.
- A firm with no workers: `firms_run_production` (`production.py` l.140) gives production = productivity x labour
  = 0 and copies it to `production_prev`. `mark_bankrupt_firms` (`bankruptcy.py` l.64) treats `production_prev <= 0`
  or net worth < 0 as bankrupt (the "ghost firm" rule), fires all its workers, and `spawn_replacement_firms`
  (l.192) replaces it with a firm at half the survivors' trimmed-mean net worth and production, and a wage offer of
  half the mean wage (floored at the minimum wage).

**Matching** (`events/_internal/labor_market.py`):
- `workers_decide_firms_to_apply` (l.206): each unemployed worker draws up to `max_M` firms at random and sorts them
  by posted wage, highest first. The shipped config default `job_search_method: all_firms` samples all firms,
  including ones with no vacancy (wasted applications); the function's own default is `vacancies_only` (l.211).
- Loyalty (l.286): a worker whose contract just expired (not fired) and whose previous employer still has vacancies
  puts that employer first.
- `labor_market_round` (l.406), run `max_M` times per quarter: every active worker sends the next application; one
  to a firm with no vacancy is consumed and lost (l.461-472); `resolve_conflicts` (`utils.py`) accepts at random up
  to the firm's vacancies; the hire takes the firm's current offer as wage and a `theta`-quarter contract (l.501-505).

**Wage setting.**
- `firms_decide_wage_offer` (l.130): offer = max(offer x (1 + U[0, `h_xi`]) if the firm has vacancies, else offer x 1,
  minimum wage). Offers rise only; a firm without vacancies never cuts. There is no response to the unemployment
  rate, only to the firm's own open vacancies. An offer falls only when a new firm replaces a bankrupt one.
- A hired worker's wage is fixed for the contract. At expiry (`workers_update_contracts`, `production.py` l.186)
  the worker is released and must reapply, so contract expiry is the main churn besides firing: every worker faces
  the market every 8 quarters unless the firm hires them back.
- Minimum wage (`adjust_minimum_wage`, l.77): every `min_wage_rev_period` (4) quarters times (1 + last annual
  inflation); employed workers below it are lifted. Initial value is 0.5 x the initial offer. It indexes to
  inflation only; it does not respond to unemployment.

**Initial conditions** (`simulation.py` l.793-825, 870). `production_init = n_households x productivity / n_firms`,
the output of full employment; `current_labor` starts at zero and `wage_offer = price_init / 3`. So the start is
sized so that desired labour equals the number of households, but period 0 begins with everyone unemployed and the
market fills through the first quarters (4 rounds of up to 4 applications each).

## Code versus documentation

- `defaults.yml` ships `job_search_method: all_firms` (wasted applications) while the function default is
  `vacancies_only`. Which one the book intends is not settled by the code.
- `default_pipeline.yml` says the order "has been validated against the reference implementation"; not verified here.
- `mark_bankrupt_firms` clears `employer_prev` for workers of bankrupt firms, so the loyalty rule cannot apply
  to them.
- I could not test whether the docs' 4.20% and the 6.5% target are reproduced by the code as shipped.

## Comparison with our labour core

Our files: `sim/labour/market/` (`clearing.py`, `applications.py`, `asks.py`, `layoffs.py`, `DESIGN.md`) and
`sim/economy/producers.py` `plan` (l.282) and `_labour_bids` (l.455), `sim/economy/labour_bids.py`.

Alike in kind:
- Bounded applications, highest offer taken, an offer that only rises while vacancies stay open, no repricing of
  hired workers (DESIGN.md says this follows Eurace; BAM does the same in `firms_decide_wage_offer` and
  `labor_market_round`).
- Immediate dismissal of workers a firm no longer needs (`layoffs.py`; `firms_fire_excess_workers`).

BAM rules with no counterpart in ours:
1. Fixed-length contracts (`theta`): every BAM worker is released after 8 quarters. Ours dismisses a random share of
   each employer's workers per search round and keeps `contracted_wage` per employer for the year; there is no
   contract length or tenure counter.
2. Loyalty to the previous employer (l.286): nothing like it in `applications.py`.
3. Wasted applications: BAM's default sends some applications to firms without vacancies. Ours applies only to
   employers whose offer is at or above the searcher's ask.
4. Wage-blind head count: a BAM firm's labour is `ceil(desired output / fixed productivity)` with no wage term.

Where ours differs:
- No reservation wage in BAM; ours has `reservation_wage` from subsistence per hour (`clearing.py`) and asks that
  fall when a search fails (`asks.py`). For our 52-90% unhired this is the largest structural difference: a BAM
  worker cannot refuse work, so BAM unemployment is only a lack of vacancies or luck in a four-draw search.
- Sizing: BAM sizes labour from last period's production moved at most 10% a quarter on an inventory-and-price
  signal. Ours sizes labour bids from `plan`: runs chosen by expected margin at live wages, limited by
  `OUTPUT_CHANGE_SHARE_PER_YEAR` (`producers.py` l.54), then `_labour_bids` offers hours = runs x `labour_hours` at a
  ceiling from `joint_labour_ceilings`, split by `sloped_bids` into tranches whose ceiling falls with the tranche. A
  producer whose margin is negative returns `Plan(0.0)` and bids for nothing at once, which is closer to BAM's
  ghost-firm exit than to BAM's gradual change.
- Wage response: BAM's offers respond only to a firm's own open vacancies and never to unemployment; ours has a
  market wage that falls to the clearing point at once, with hired workers kept at their contract wage.

## Caveat

Nothing here is measured. The reading suggests BAM's low unemployment (by its own docs) comes from every worker
accepting any offer, firms sized to full-employment output at the start, and 0-10% quarterly output moves, none of
which our core has; but that is an inference from code, not a result. Running the command above would test it.

## Measured run (orchestrator, after the owner allowed running the package)

BAM Engine at commit 50e14d1, baseline defaults, 1000 periods, three seeds, run with `python3 -I`
(runner scripts `scratchpad/scripts/run_bam.py` and `run_bam_validation.py`, not committed).

| Seed | Unemployed at production, after 500-period burn-in: mean (std, min-max) | First 50 periods | Unemployed at period end, after contract expiry |
|---|---|---|---|
| 0 | 0.053 (0.026, 0.004-0.134) | 0.001 | 0.188 |
| 1 | 0.056 (0.025, 0.000-0.134) | 0.002 | 0.150 |
| 2 | 0.059 (0.030, 0.002-0.156) | 0.002 | 0.150 |

The package's validation target (mean 0.065, tolerance 0.025, from the book's Figure 3.2b) is met when employment is
read where the validation reads it: at `firms_run_production`, after the period's hiring
(`validation/scenarios/baseline/__init__.py`, `COLLECT_CONFIG`). Read at the end of a period, after fixed-length
contracts expire and before the next hiring round, the unemployed share is about three times larger. So BAM's
single-digit unemployment depends on when it is counted: a large share of workers turns over every period and is rehired
within it. The run starts at full employment (the first periods show near zero) and unemployment emerges over the
burn-in.
