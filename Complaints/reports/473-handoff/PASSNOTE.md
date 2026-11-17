# Passnote: Complaint 473, the agent economy's spin-up never settles

For whoever picks this up next. It says what the goal is, where the work stands, how to measure, what was learned,
what was tried, and what to do first. The detail behind every claim is in
`Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md` (Updates 24-30) and the
owner's answers in `Complaints/reports/473-owner-questions.md`. Figures are not repeated here: each claim names
the command that measures it.

## 1. The goal

Before a game, a hidden spin-up (`sim/markets/spin_up_run.py`: a first stage, a workforce trim, a trimmed stage) runs
the agent economy until it is stationary, and `spin_up_settled` must pass: every watched quantity
(`sim/economy/spin_up_state.py`: price level, rate, real output, hired hours, producers' inventory value, unmet food
need, and the prices of the goods the opening basket spends most on) moves less than `SPIN_UP_TOLERANCE` a year over the
last `SPIN_UP_MEASURED_YEARS` (`sim/markets/spin_up_gap.py`). 473 closes when that holds for every shipped civilisation
(`england_1300`, `han_china_100ad`, `mexica_1500`, `norse_900ad`, `rome_100ad`). Complaints 970, 511, 519, 526, 607,
545, 608, 554, 557 and the Rome group 960-963 wait on it.

The owner's requirements, which any change must keep:
- **Settled is a fixed point, and the economy must not be chaotic** (the owner's answer to question 1). The check is not
  to be weakened or redefined. A small nudge must move the economy a small step: doubling iron's price should move
  each good's price by about its iron cost share and leave the rest close to where it was.
- The project rules in `CLAUDE.md` (no hardcoded outcomes, no content ids in the engine, every heuristic declared with
  a `retire`, TDD, a test calls one function, no figures in markdown or comments).

## 2. Where it stands

Branch `economy-settles-not-chaotic` (on top of the merged `spin-up-settles`). Merged, each with a rule test (Update
30 gives the mechanism and evidence):
- Labour poaching is continuous in the employers' standing (`sim/labour/market/clearing.py`, `clearing_tail_kernel.py`).
- Household work is counted over the labour year's working days (owner question 7), and hiring servants is continuous
  in the budget and gradual (`households_work.py`, `household_servants.py`, `household_work_year.py`).
- The coin-metal opening check asks a metal-paid money that the mint's price covers the making cost (owner question 4).
- Households' durable purchases replace wear and close a share of the gap to the stock wanted; affordability falls
  smoothly (the former unmerged `durable-demand-continuous` patch).
- `requirements.txt` lists shapely (owner question 5).

Not settled. What moves, by civilisation (section 3 says how to measure):
- Norse: far calmer than before (household work was most of its swing); hired hours and output still move by one to
  two times the tolerance, inventory value and the rate by many times it.
- England: hired hours, output and the price level move by a little under the tolerance on average, with end gaps
  about at it; inventory value and the rate by several times it. Its money stock falls by the coin wear every year
  (section 4).
- Han: hired hours, output and the price level move by two to three times the tolerance and the rate by many times;
  its hours are calmer than before and its price level, watched prices and rate are not.
- Mexica: its output shrinks through the whole spin-up; not traced.
- Rome: not re-measured on this branch (its replay is slow and holds much memory).

## 3. How to measure (read this before changing anything)

**One run judges nothing, and eight end gaps judge little.** Two spin-ups whose households' cash differs at the
rounding level end in different places, and the end gap's spread across eight members is as large as its median. Use:

```bash
# every year of every member (members run one after another in one process), then each quantity's mean yearly move
# over the trimmed stage beside the end gap the check uses
PYTHONPATH=. python3 Complaints/reports/473-handoff/probes/ensemble_years.py england_1300 8 /tmp/years_england.jsonl
python3 Complaints/reports/473-handoff/probes/ensemble_moves.py head=/tmp/years_england.jsonl
# the committed command (end gaps and trends per member; members in parallel)
python3 sim/simulator.py spin-up-trace --civ england_1300 --stages --ensemble 8 --jobs 2
```

Compare two rules on the mean yearly move, on at least England, Norse and Han: a rule that calms one has more than once
made another swing.

**To find where a difference grows: twin runs** (`probes/twin_probe.py`, read with `show_twin.py`, `show_states.py`,
`show_detail.py`). Two economies from one opening, the second with households' cash scaled by a rounding-sized factor,
are stepped side by side and their whole records compared leaf by leaf after every year. `late_twin_probe.py` forks
the twins from one saved economy late in the trimmed stage; `phase_probe.py` compares what goes into and comes out of
the lending, planning and labour phases of one year; `hire_probe.py` looks inside the labour clearing. A difference
that jumps by many orders of magnitude in one year and one section is a discontinuity; follow it to the rule.

**To find what cycles: one run year by year.** `series_probe.py` (output by good, each labour market, each producer and
cohort, holdings by good) with `analyse_series.py`; `wage_probe.py` (one labour market's wage rule: last wage, goal,
reservation, hours offered, wanted and hired); `labour_totals_probe.py` (hours offered, wanted and hired over all
markets). The older probes of Updates 24-29 are beside them. All are scratch scripts written against the commit they
were used on: run them from a checkout with `PYTHONPATH` set to it.

**Pinned trees.** Run long measurements on a detached worktree pinned to the commit, never the checkout you are
merging into (`git worktree add --detach ../pin_<name> <commit>`).

**Machine limits.** A year of England or Norse takes about a second per economy with numba, Han a few times that, Rome
far more. Compiling the kernels for a tree takes several minutes and several GB in each process that does it, and a
new tree path or an edited kernel file compiles again; a replay holds one to a few GB. On a 16 GB, 4-core container
two compiles, or one compile and a Han ensemble, are the most that fit: more were killed for memory. A killed worker
aborts an ensemble with `BrokenProcessPool` and an empty output: check the `.err` file, not only the exit code. Setting
`NUMBA_CACHE_DIR` to one directory per pinned tree keeps its compiled kernels between runs; after editing a kernel
file that other kernels call, use a fresh directory (numba does not recompile the callers).

**Environment.** `pip install -r requirements.txt` (numba, shapely). A container restart drops installed packages and
kills background runs silently. `ROME_KERNEL_CACHE_KEY=kernels` for edit-test loops.

## 4. What was learned

Each is in Complaint 473 with its evidence.

- **The first amplifier was poaching** (Update 30): hours moved between employers on which stood a hair higher.
  Fixed. Twins forked late in England's trimmed stage now stay together for years, so what is left there is mostly
  deterministic movement (cycles and drifts), not rounding noise. The first years of the first stage still amplify.
- **England's and Norse's swing in hours was the households' own time** (Updates 27 and 30): household work counted
  over the civil year against a labour year of working days, and a yearly all-or-little choice to hire servants on last
  year's wage. Fixed.
- **A durable's purchase was the whole gap to the stock wanted** (Updates 29 and 30), an accelerator on a good whose
  making is most of England's measured output. Fixed by the stock-adjustment rule, which calmed England and Norse once
  the two causes above were gone (it had not, measured before them).
- **The money stock wears away** (Update 30). England's opening places its silver smelters on a route whose ore
  nothing in England mines, the mint strikes a small share of the coin wear, and the price level, the wage and the
  workers' reservation fall together at the wear rate with real balances level. Norse's and Han's money stocks also
  fall by their whole yearly loss on this branch. A fixed point of the price level needs a coin-metal chain the
  civilisation's tiles can supply at the opening, sized to the loss.
- **A quarter of England's offered hours go unsold in every year** and the wage stays a steady multiple of the
  reservation (Update 30; Complaints 608, 963).
- **The rate is the cheapest lender's ask every year** (Update 28) and follows the year's inflation; it settles last.
- **Inventory value lumps come from buyers** (Update 29) and from single goods whose price creeps up and falls back.
- **The opening solver is not proportional** (Update 25).
- **Mexica's tool makers** (owner question 6): judging a learning crew on the cost of the crew it will become makes it
  run, but only a fraction of a run: entry sizes it to nothing (Update 30).

## 5. Tried and not merged

Patches are in `unmerged/` (against the `spin-up-settles` commit they were made on); branches are pushed.

| Patch or branch | Rule | Why not merged |
|---|---|---|
| branch `opening-cash-at-the-yearly-steady-state` (the `opening-grown-floor-budget` patch re-applied) | the opening meets own-plot floors before sizing the budget, as the yearly rule does (owner question 3, option a) | alone it calms England and Norse; on top of the durable rule England's hours move more and Han's hours and wage swing far more. The cause in Han is not traced |
| branch `learning-path-plan` | a crew still learning judges whether to run on the discounted cost of its learning path; entry takes the same path (owner question 6) | Mexica's wooden-tool crews go from no runs to a fraction of one: entry sizing still holds them to nothing, so it does not yet do what it is for |
| `grinding-share-continuous.patch` | grind-or-buy-milled a logit share per grain | measured before household work was fixed; not re-measured |
| `inflation-trimmed-mean.patch` | observed inflation a weighted trimmed mean | the rate moved as much or more |
| `stock-offered-in-tranches.patch` | held stock offered as up to four lots of a year's sales | inventory value moved as much |
| (not kept) | producers plan no stock cover and the ask only falls with unsold stock | prices fell every year: the step that raises an ask when stock is under its cover is what raises asks between years |

## 6. Owner questions

All seven are answered (`Complaints/reports/473-owner-questions.md`, top). Done: 4, 5, 7. Question 1 is the standing
requirement of section 1. Question 2 needs nothing. Questions 3 and 6 are built on branches and not merged (section 5).

## 7. What to do first

1. Set up the environment and reproduce: `ensemble_years.py` on England, Norse and Han at the head, so your numbers
   are your own.
2. Han: find why its hours and wage swing with the opening branch on top (`series_probe.py` and `analyse_series.py` on
   Han for the trade and area, then `wage_probe.py` on that market, as Update 30 did for England). Then question 3
   can be merged.
3. The coin metal: make the opening place the coin-metal chain on recipes whose ores the civilisation's tiles can
   supply and size it to the money's yearly loss, so `money_against_wear` passes and the price level can rest
   (Complaints 961, 970). England is the traced case; Norse and Han lose their whole yearly loss too.
4. Mexica: trace why output shrinks through the spin-up; then entry sizing for a trade nobody practises, so question 6
   can be merged.
5. The single goods that saw and the first years' amplifiers named in Update 30, with the twin probe.
6. Rome, once the others are close: one member takes long, so measure it last.

Before any PR: `python3 -m sim.tests --slow`, then rebuild openings as the last commit
(`python3 sim/simulator.py openings --prune`) and check `python3 tools/check_openings_current.py` lists none stale.
