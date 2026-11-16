# Passnote: Complaint 473, the agent economy's spin-up never settles

For whoever picks this up next. It says what the goal is, where the work stands, how to measure, what was learned,
what was tried, and what to do first. The detail behind every claim is in
`Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md` (Updates 24-29) and the
owner's open questions in `Complaints/reports/473-owner-questions.md`. Figures are not repeated here: each claim names
the command that measures it.

## 1. The goal

Before a game, a hidden spin-up (`sim/markets/spin_up_run.py`: a first stage, a workforce trim, a trimmed stage) runs
the agent economy until it is stationary, and `spin_up_settled` must pass: every watched quantity
(`sim/economy/spin_up_state.py`: price level, rate, real output, hired hours, producers' inventory value, unmet food
need, and the prices of the goods the opening basket spends most on) moves less than `SPIN_UP_TOLERANCE` a year over the
last `SPIN_UP_MEASURED_YEARS` (`sim/markets/spin_up_gap.py`). 473 closes when that holds for every shipped civilisation
(`england_1300`, `han_china_100ad`, `mexica_1500`, `norse_900ad`, `rome_100ad`). Complaints 970, 511, 519, 526, 607,
545, 608, 554, 557 and the Rome group 960-963 wait on it.

The owner's further requirements, which any change must keep:
- **Not chaotic.** A small nudge must move the economy a small step. Doubling iron's price should move each good's price
  by about its iron cost share, and leave the rest close to where it was. A rounding-sized perturbation must not grow
  into a different economy.
- **Do not weaken the settling tests** (the check stays as it is unless the owner answers question 1).
- The project rules in `CLAUDE.md` (no hardcoded outcomes, no content ids in the engine, every heuristic declared with
  a `retire`, TDD, a test calls one function, no figures in markdown or comments).

## 2. Where it stands

Branch `spin-up-settles` (the PR this note ships with). What it merged, each with a rule test (Complaint 473 Updates
24-27 give the mechanism and evidence for each):
- Household money leak: the floors grown on the own plot are met before the budget is sized
  (`households_orders_kernel.py`, `household_grown_floors.py`).
- Unmet need measured against the economy's food need.
- Mint: bids where its metal trades, pays weighed metal at parity, melts only backing above holders' cash targets
  (`mint.py`, `mint_price.py`, `mint_bid_split.py`).
- Residue: stock decayed to `STOCK_RESIDUE_UNITS` is removed and is no offer (`stock_residue.py`).
- Unpriced tools costed by their fallback chain in placement, entry, planning and the close.
- Chaos amplifiers made continuous: labour clearing demand, entry from residue demand, trade switching (one logit with
  staying), residue bids (`flexible_budget_left`, `store_pot`), and allocation of unserved demand in proportion.
- Measurement: `spin-up-trace --stages` and `--ensemble N` (below); the test runner reports unexpected successes and
  skips; seven vacuous tests and the opening checks' vacuous passes fixed.
- Reverted: a continuous market-memory blend (Updates 26-27). The memory is the trade-weighted rule again.

Not settled. Measured on eight-member ensembles (section 3):
- England and Han: hired hours, real output and the price level move by a little more than the tolerance; producers'
  inventory value and the rate move by many times it, and England's inventory value also trends down.
- Rome (four members only): like England, with larger moves of output and hours.
- Norse: every quantity moves by many times the tolerance (question 7).
- Mexica: not re-measured since the chaos work; its tool makers are caught in a learning trap (question 6).

## 3. How to measure (read this before changing anything)

**The economy is chaotic enough that one run judges nothing.** Two spin-ups whose households' cash differs at the
rounding level end in different places. Compare rules only on ensembles, and with eight members: four members once
showed an output collapse that eight did not (Update 26).

```bash
python3 sim/simulator.py spin-up-trace --civ england_1300 --stages --ensemble 8 --jobs 2
```

Member k starts with every cohort's cash multiplied by `1 + k * 1e-12` (a measurement perturbation only). Per quantity
it prints each member's **end gap** (the largest year-to-year change over the last measured years: what
`spin_up_settled` tests) and **trend** (first half against second half of the trimmed stage), then the median and
spread. Read the median end gap against `SPIN_UP_TOLERANCE`, and the median trend for drift. One ensemble takes a few
minutes per civilisation with numba (Rome much longer). For one run year by year: `spin-up-trace --civ <civ> --stages`.

Run long measurements on a detached worktree pinned to the commit, never the checkout you are merging into:

```bash
git worktree add --detach ../pin_<commit> <commit>
```

To compare two rules, build each in its own pinned worktree and run the same ensemble on both, one after the other.

**Machine limits.** Each replay holds several GB (Rome more). On a 16 GB, 4-core container, `--jobs 2` for one ensemble
at a time; four replays at once were killed for memory. A killed worker aborts the whole ensemble with
`BrokenProcessPool` and empty output: check the `.err` file, not only the exit code.

**Environment.** `pip install -r requirements.txt` (numba: without it every game is many times slower) and
`pip install shapely` (the geography tests need it and `requirements.txt` does not list it). A container restart
drops both, and kills background runs silently: an empty output file means relaunch. Use
`ROME_KERNEL_CACHE_KEY=kernels` for edit-test loops (compiled kernels survive edits to non-kernel files).

**Probes.** `probes/` beside this note holds the scratch scripts that found each mechanism below. They replay a
spin-up year by year and write JSON lines; each is written against the commit it was used on, so a field it reads may
have moved. Run them from a checkout with `PYTHONPATH` set to it:

| Probe | What it logs |
|---|---|
| `probe_spin_years.py` | every spin-up state quantity, the rate, the price level and the watched prices, by year |
| `probe_output_decomposition.py`, `analyse_decomposition.py` | output by good, hired hours by trade, producer figures; shares of the swing |
| `probe_cohort_hours.py` | per cohort: household-work, plan, plot, whole and sold hours, hour value, ground share (written on `grinding-share-continuous`) |
| `probe_inventory.py`, `probe_rate.py` | producers' held stock by good and producer; the loan clearing's target, lowest ask and expected inflation |
| `probe_producer_flow.py` | one producer's stock, output, offered lots, buyers' bids, sales and price (written on `stock-offered-in-tranches`) |

## 4. What was learned

Each is in Complaint 473 with its evidence; the file is named so you can start there.

- **Norse: household work leaves a small remainder of sellable hours** (Update 27, owner question 7). In Norse's
  swinging Swedish area household work (`data/world/household_work.json`, `sim/economy/households_work.py`
  `hours_per_person_per_year`) takes most of the cohorts' year, and the hours sold are what is left
  (`sim/economy/labour_supply.hours_kept_at_home`). A small change in either term takes the remainder to zero; the
  fishers' and farmers' output falls with it. Halving household work in a scratch copy roughly halved Norse's swing.
- **The rate is the cheapest lender's ask every year** (Update 28): `sim/loans/clearing_kernel.settled_rate` snaps
  to `lender_ask.lowest_ask` (time preference plus expected inflation), so the rate follows the year's observed
  inflation (`currency.price_inflation`), which follows the middle goods' price noise.
- **Inventory value lumps come from buyers** (Update 29). Producers' output and asks are smooth; households bid for
  draught animals in some years and not at all in others, so stock piles up and clears in one sale.
- **Removing one traced lump moved the noise elsewhere** (Update 29). Four rules were made continuous and none calmed
  the quantity it fed (section 5). This is the main evidence for owner question 1.
- **A memory rule that pulled thin markets toward making cost** deflated the economy, and the continuous memory blend
  as a whole made Han and England swing more (Updates 26-27). The trade-weighted rule measures better; a sliver of
  trade still moves it a discrete step.
- **The opening solver is not proportional** (Update 25): a change to one recipe re-solves the opening and moves most
  producers' capacity. The agent economy's first years after the opening do respond in proportion.

## 5. Tried and not merged

Each is a patch in `unmerged/` beside this note, against the `spin-up-settles` commit it was made on (apply with
`git apply` on a branch from that commit, or rebase). Each has its rule tests and passed the quick tier on its own.

| Patch | Rule | Why not merged |
|---|---|---|
| `grinding-share-continuous.patch` | grind-or-buy-milled a logit share per grain; the basket caps the grain continuously | Norse's hours and output swung more: a smooth move of a large term still wipes out the small remainder (question 7); slower year |
| `inflation-trimmed-mean.patch` | observed inflation a weighted trimmed mean of price ratios | the rate moved as much or more on England and Han |
| `stock-offered-in-tranches.patch` | held stock offered as up to four lots of a year's sales | inventory value moved as much: the lumps are on the buyers' side |
| `durable-demand-continuous.patch` | durable bids replace wear plus a share of the gap; affordability falls smoothly, a durable against its service life's budget | inventory value moved as much; Han's hours and rate moved far more |
| `opening-grown-floor-budget.patch` | the opening meets own-plot floors before sizing the budget, like the yearly rule | the households' opening savings shrink and Norse's ore and silver markets stop trading at the opening (question 3) |

Each of these rules is still a discrete or lumpy rule on the branch. If the owner answers question 1 with a
stationarity test, they may matter less; if the fixed point stays, they are where to look again, together.

## 6. Owner questions (all in `Complaints/reports/473-owner-questions.md`)

Each has a default the branch follows until it is answered.
1. **What "settled" means**: a fixed point of every quantity, or stationarity over an ensemble. **Blocks 473.**
2. People on fertility-0 tiles (Norse): intended, or a data question.
3. The opening's cash and savings once own-plot floors are met first.
4. Silver at parity far above its making cost: what `price_over_cost_coin_metal` should test.
5. The cloud environment's setup script should install `requirements.txt` (and shapely).
6. How an unpractised crew decides to work (Mexica's tool makers never start).
7. **Where household work's hours come from. Blocks Norse.**

## 7. What to do first

1. Read the owner's answers to questions 1 and 7, if there are any. If not, ask; nothing below closes 473 without them.
2. Reproduce the state: set up the environment (section 3), then run the eight-member ensemble on England, Han and
   Norse at the head, so your numbers are your own.
3. If question 1 says stationarity: build the test on the ensemble in `sim/markets/spin_up_gap.py` /
   `spin_up_run.py` (the proposal is in question 1: no trend between halves of a longer window, the year-to-year
   spread under a bound, over members that differ at the rounding level), with the fixed-point gap kept as a reported
   figure.
4. Change household work's time budget as question 7 says; re-measure Norse.
5. Re-measure all five civilisations, Mexica included (`python3 sim/simulator.py opening-checks --civs <civ>` as well).
6. Then questions 6, 3 and 4, and the remaining movers `spin-up-trace --stages` names.

Before any PR: `python3 -m sim.tests --slow`, then rebuild openings as the last commit
(`python3 sim/simulator.py openings --prune`) and check `python3 tools/check_openings_current.py` lists none stale.
