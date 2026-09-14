# Solving the dice-free problem first, then seeing what survives the dice

Goal node, read from the tree at measurement time (`tree["meta"]["goal_node"]`,
the same line `planner.py` and `path_search.py` both read it from, never
hand-typed): **`junction_transistor`**. Its prerequisite closure, also read
from the tree (`engine/data.py:closure()`, which follows `pre` and every
single-option `req_any` group): **168 nodes** (`simulator.py validate`
confirms this independently: "required for goal: 168" - measured twice,
before and after the merge below, both times 168, not 158 or 185, both of
which were briefly written down elsewhere today and are wrong).

Measured against `f764e5e`. Partway through this work the shared branch
picked up a large, unrelated performance pass (a 300-year single-seed run
went from 12.8s to 7.8s; a 700-year single seed that previously would not
finish inside a ten-minute timeout now takes about three and a half
minutes) plus real balance changes to `core.py`/`economy.py`/`society.py`/
`protocol.py` from four other agents. Merged cleanly (no conflicts outside
`cli.py`, which `git` resolved on its own). Determinism through the merge
was checked directly, not assumed: the dice-free Rome trial's state at
year 1000 - capital `29,520,851.012074385`, `employees` down to the
fraction (`chemist: 10.45, engineer: 10.45, machinist: 2.0, optician: 2.0,
electrician: 4.0`) - is byte-for-byte identical before and after the merge.
The speed is not, and it is the reason section 1's answer below is
**correct** rather than merely faster: every horizon this report quotes
past year 1000 was too expensive to reach before the merge, and the
pre-merge version of this same investigation (reaching only as far as year
1000, because that was already tens of minutes of compute) concluded "no"
to the question section 1 actually answers "yes" to. That draft conclusion
never left this file's own working history - it is recorded here, once,
as the clearest illustration this report has of why "solve the
deterministic problem first" has to mean "run it to an horizon long enough
to find out," not "run it as long as seemed affordable an hour ago."

## Method

"Solve the deterministic problem first," per the brief: turn off events
(`--no-events` already exists) AND turn off the one other source of
randomness that is not gated by `events` - a project's own risk of failing
outright, which is a bare `self.rng.random() < n["risk"]` in
`projects.py:_complete` that fires whether or not `events=True`. A seeded
rng whose `random()` always returns 1.0 is never below any probability
threshold anywhere in the engine - not that roll, not the 3.5% yearly
attrition check, not the 25% manumission check, not the fractional-headcount
stochastic rounding - so it reproduces a single trial with money, staff,
calendar and the tree's own dependency structure as the only constraints.
This lives in the new module `rome/sim/path_search.py` as `DetRNG`, built
and run with an `immortal=True` founder and `events=False`, never by
editing `core.py`/`projects.py`/`labour.py`/`society.py`/`economy.py`.

A footnote worth recording rather than burying: CPython hashes strings
differently by default in every process (`hash("machinist")` differs run to
run), and a few places in this engine walk a bare, unsorted `set` of node or
trade ids - `core.py`'s own comment on `rng.sample(losable, ...)` names this
exact risk for one such set and sorts it there specifically because an
earlier version did not. Every repeated trial here (same order, same
`DetRNG`, separate `python3` processes, before AND after the performance
merge) came back bit-identical regardless - so nothing here was silently
corrupted by it - but `path_search.py` pins `PYTHONHASHSEED` before any
`Sim` runs anyway (`ensure_fixed_hash_seed`, a one-time self-re-exec),
because removing the question costs nothing and is cheaper than
re-auditing every set-iteration site in files that are not this module's to
edit and that keep changing under other agents' hands.

## 1. The deterministic answer

**Yes.** With the dice removed entirely, the current critical-path plan -
`backward_plan()`'s own output, byte-identical to what `simulator.py plan`
produces with no flags, which is in turn byte-identical to the committed
`strategies/planned_rome.json` and `planned_han.json` - reaches
`junction_transistor` on BOTH civilisations, given a long enough horizon.
Money and the generic scholar/artisan pools are never the reason it takes
as long as it does (both end up far beyond abundant on every trial below);
a slow-to-resolve cash-flow/named-trade bottleneck is, and it resolves on
its own, eventually, without any help from ordering.

**Han China** (`han_china_100ad`): reaches the goal at **year 555 AD - 455
years after arrival**, against a 142.2-year critical-path floor.

| year | closure nodes done | capital (den) | named-trade employees |
|---|---:|---:|---|
| 250 | 43/168 | -2,388 | (none taught yet) |
| 300 | 82/168 | +640,039 | all five at 4.0 |
| 350-400 | 85/168 | +3.5m to +5.1m | all five still at 4.0 (plateaued) |
| 450 | 109/168 | +3,867,285 | all five at ~4.29 |
| 500 | 145/168 | +225,269,370 | all five at 10.45 |
| **555** | **168/168 - GOAL REACHED** | **+1,210,824,657** | all five at 10.45 |

**Rome** (`rome_100ad`): reaches the goal at **year 1121 AD - 1,021 years
after arrival**, nearly twice Han's span.

| year | closure nodes done | capital (den) | named-trade employees |
|---|---:|---:|---|
| 250-700 | 30/168 | -4,100 to -5,839 | (none taught yet) |
| 750-950 | 36-41/168 | -6,583 to -17,198 | 0 to 2 each, as they get taught and occasionally lost |
| 1000 | 109/168 | +29,520,851 | chemist/engineer 10.45, machinist/optician 2.0, electrician 4.0 |
| 1050 | 140/168 | +753,790,341 | all five at 10.45 |
| 1100 | 162/168 | +1,516,565,621 | all five at 10.45 |
| **1121** | **168/168 - GOAL REACHED** | **+1,818,924,430** | all five at 10.45 |

Both tables show the same shape, at different scales: a long plateau (Han
~250 years, Rome ~950 years) in which capital sits flat or mildly negative
and none of the five `TRADES_ABSENT` trades (chemist, electrician,
engineer, machinist, optician) have any headcount at all, followed by a
single expensive cascade year in which staffing, revenue and the closure
count all jump together (Han: 85→109→145 in 100 years; Rome: 41→109→140 in
150 years), after which every trade converges to the same 10.45 headcount
and the rest of the closure clears in well under a century.

**What the plateau actually is.** `data/review/ROME_SOLVENCY.md` traced
this independently, under real seeded trials, to `staff_capacity()`'s
affordability term: it needs an annual operating surplus on the order of
$20,000-25,000 before it grants a single whole hire, and neither
civilisation's own trading margin clears that on its own for a long time -
Han because it takes roughly 150-200 years to compound its technological
head start into that much surplus, Rome because it starts with none of
that head start and needs closer to 900. Nothing about strategy ORDER
shortens this: it is a property of household income relative to a fixed
affordability formula, exactly the kind of live money/staff modelling
`planner.py`'s own docstring declines to duplicate and leaves to the
engine. Once the surplus clears the threshold, the five named trades -
which grow ONLY through `step()`'s once-a-year, two-people-at-a-time
auto-teach, normally frozen almost the instant any of them gets nonzero
headcount (the sole re-trigger is `market_supply(t) <= 0.0`, never true
again short of a trade dying out completely) - get pushed through several
cycles of being staffed, lost (to unpaid wages in a tight year, not to
attrition, which `DetRNG` disables), and re-taught in quick succession
once the household can actually afford to keep rehiring them, which is
what the post-cascade convergence to 10.45 each actually is. None of this
needed search to find - it is what simply running the unmodified plan out
far enough shows.

## 2. The search

`rome/sim/path_search.py` automates "repeatedly relax the binding
constraint" - one of the two methods the brief names - rather than a blind
metaheuristic over the space of 168! orderings, because at any one moment
the constraint here is not diffuse: it is measurably one or a few named
trades, read directly off a live `Sim`'s own `active`/`employees`/
`hours_you_can_call_on` state, not modelled a second time. Each round:

1. Runs a dice-free trial of the current order.
2. `diagnose_scarce_trades`: flags a `TRADES_ABSENT` trade as the binding
   constraint if two or more still-outstanding nodes want it AND their
   combined outstanding hours are worth more than `--backlog-ratio` (6, by
   default) years of what the household can draw on in a single year.
3. Two moves, applied only to nodes that touch a flagged trade:
   - **Pull every side branch that draws on it out of the interleaved
     order, to the very end** - a side branch exists only to fund the
     spine, so one competing with the spine for the one thing actually
     blocking the spine is a net cost. (Measured aside: 7 of Rome's 12
     CPM-picked side branches - locomotives, TNT, dynamite, a double-acting
     engine - draw on these exact five trades, spread through the order
     specifically so they compete with the spine for them the whole run.)
   - **Within a tied CPM slack band, move nodes that draw on it to the
     front, smallest total hours of it first** - shortest-processing-time-
     first, the standard remedy for many jobs queued on one non-shareable
     resource, applied only where `planner.py` already treats the graph as
     unable to tell two nodes apart.
4. Re-simulates, keeps whichever round scored best (see `fitness` - reaching
   the goal beats not reaching it, earlier beats later, more of the closure
   done beats less), and stops itself once a round makes no further change,
   reaches the goal, or flags nothing scarce.

**Honestly measured, across three different diagnosis points, the search
never improves on the plain CPM order - it also never makes it worse, and
for Han it correctly recognises success and stops immediately:**

- Diagnosing at horizon 500 on Rome (cheap, but before the plateau has
  broken): flags four trades as "scarce" (nothing taught yet, so any
  backlog clears the ratio trivially), pulls one side branch
  (`tr_articulated_locomotive`), converges after one round. Final order is
  NOT the plain CPM order (one side branch moved) but scores identically
  at every horizon tested, including the goal itself: **year 1121, both
  ways.**
- Diagnosing at year 1000 on Rome directly, against the real bottleneck
  (`machinist`: 101,559 hours of backlog across 25 still-outstanding
  nodes, against a realised supply of 6,360 hours/year - sixteen years of
  uncontested work just to clear that one year's backlog): correctly and
  precisely identifies the true constraint, pulls the same one side
  branch, and still reaches the goal at **year 1121, both ways** -
  identical capital to the cent (`1,818,924,430`).
- Diagnosing at horizon 900 on Han: the dice-free trial has already
  reached the goal (555 < 900) by the time the first round finishes, so
  the search sees nothing outstanding, flags no scarce trade, and stops
  itself on round 0 rather than hunting for a problem that no longer
  exists. Goal year: **555, both ways.**

**Why the relaxation never matters, even when it correctly identifies the
right trade:** `interchangeable_parts` alone, on its own, already demands
more machinist-hours in a single year than the entire named-trade pool can
supply - so pulling ONE competing side branch off that trade never changes
how fast `interchangeable_parts` itself clears, because it was never
sharing the bottleneck with anything else in the order that mattered within
the years that count. This is not a disappointing footnote to explain away:
**the named-trade freeze, while real and precisely measurable, turns out to
be a multi-century DELAY, not a permanent wall, and the delay's length is
set by the affordability/auto-teach cycle described in section 1, which no
reordering of a strategy file touches.** A search that tries to relax it
anyway, measures three separate times that it cannot, and reports that
honestly is doing its job correctly - the same discipline `planner.py`'s
own comments already apply to the staffing-institution question
("measured, putting them in this order made the run worse, not better"),
extended to a constraint the graph-only CPM pass has no way to see in the
first place. A genuinely different search - one that tries moves this
module does not (loosening `--side-branches` itself, or a different
concurrency cap on how many closure nodes may be simultaneously active) -
might still find something these two moves do not; that is future work, not
a claim made here.

`--search-rounds` is wired into `simulator.py plan` (see `engine/cli.py`
`cmd_plan`) precisely so this is re-runnable rather than a one-off claim:
`plan --search-rounds N --search-horizon H --out FILE` diagnoses and
relaxes for real, on demand, against whatever the tree says today.

## 3. Against real seeds

Since the search never improves on the plain CPM order, "the best
deterministic path" for this measurement IS that order -
`planned_rome.json`/`planned_han.json`, unmodified, exactly as
`simulator.py plan` (no `--search-rounds`) already produces them.
`python3 rome/sim/simulator.py run --civ <civ> --strategy <file> --mc 3 --horizon 700 --seed 1`
(real events on, real project-failure risk, a mortal founder by default -
nothing dice-free about either run; each took a few minutes on this
machine after the performance merge, tens of minutes before it):

**Rome: 0 of 3.**

```
runs                : 3
reached transistor  : 0  (0%)
years spent short of a raw material (median run):
   iron         15 run-years
   coal         11 run-years
   copper       5 run-years
   saltpetre    3 run-years
coppice woodland owned: median 384 hectares
final reputation    : median 99/100
failure modes       :
   ran out of horizon                                           3 (100%)
first blocked node  :
   point_contact_transistor                                     1
   atomic_theory                                                1
   cap_heat_3000                                                1
```

**Han China: 2 of 3 (67%).**

```
runs                : 3
reached transistor  : 2  (67%)
year reached        : best 663 | p25 663 | median 703 | p75 703 | worst 703
elapsed from 100 AD  : median 603 years
years spent short of a raw material (median run):
   saltpetre    217 run-years
   iron         45 run-years
   copper       21 run-years
   coal         18 run-years
   gold         3 run-years
coppice woodland owned: median 1182 hectares
final reputation    : median 100/100
failure modes       :
   ran out of horizon                                           1 (33%)
first blocked node  :
   point_contact_transistor                                     1
```

**How much of the deterministic answer survives the dice, stated plainly:
for Han, most of it; for Rome, none of it - and section 1 already explains
exactly why, with no need to guess.** `--horizon 700` with `start_year 100`
means the test actually cuts off at year 800 AD, not 700. Han's dice-free
trial reaches the goal at year 555, with 245 years of slack against that
800 AD cutoff; two of three real-seeded trials land inside that slack (663
and 703) and the third runs out of the full 800 years without reaching it
at all - real shocks and a mortal founder cost that one trial more than
245 years of margin, which is a real, visible cost of the dice, just not
an unsurvivable one here. Rome's dice-free trial does not reach the goal
until year 1121 - **321 years past the 800 AD cutoff this measurement
actually uses** - so 0 of 3 real-seeded trials reaching it is not evidence
that ordering or luck failed Rome; a perfectly luck-free trial of the
identical order already needed 1,021 years from arrival, and no amount of
good fortune inside an 800-year window was ever going to make up a
321-year gap. The honest conclusion is not "Rome's plan doesn't work" -
section 1 shows that it does - but "Rome's plan needs a longer horizon
than this project has been testing it at," which is a claim about the
TEST, not about the tree, the civilisation, or the planner's ordering.

## A warning, taken seriously: is `planned_rome.json` even current?

The brief's own warning - every saved strategy in this repository was stale
for weeks, targeting a retired goal node, without anyone noticing - has a
concrete, checkable instance in this project's own history. Commit
`758744b` recorded `planned_rome.json` reaching the goal **10 of 10**
trials at a 700-year horizon with events on. That commit predates
`fa31ff1` ("data: both transistors, with the 1951 one as the target"), the
commit that retired the 1947 point-contact device as the goal and made
`junction_transistor` (1951) the target - i.e. that 10/10 almost certainly
measured the OLD goal, not the one this report (and the current tree) is
actually asking about. It is not reused here for that reason, however
tempting a ready-made "10/10" would be. Every number in this report was
measured fresh, this session, against `tree["meta"]["goal_node"]` read
live off the current tree - not against anything remembered from an
earlier session, a stale strategy file, or an old commit's own report. The
nearer-miss version of the same lesson is this report's own section 1: a
number that was true of "as far as this session could afford to compute
an hour ago" stopped being the right answer the moment a performance fix
made computing further affordable, and the fix was to re-run, not to
footnote the old number and move on.

## 4. The 434 AD fixture: a player three times better than this order, and why

A human player reached the point where `junction_transistor` is startable in
Rome at **434 AD - 334 years from the 100 AD start**, with 167 of the goal's
168 closure nodes done, 607,402,406 denarii at roughly +4,045,403/year,
636 employees (451 artisans, 148 scholars, 7.48 each of chemist/electrician/
engineer/machinist/optician), 88% general literacy and 2,132 technologies
done out of 2,836 in the tree. This is preserved as
`rome/playtest/fixtures/rome_434_goal_startable.json`, alongside an earlier
save from the same playthrough, `rome/playtest/fixtures/rome_380_corpus_bug.json`
(year 380, capital 309,213,069, 24 ventures operating). Both are real saves,
not constructed for this report, and both are read directly below, not
summarised from memory.

Section 1's own number for the SAME order, run completely dice-free, was
**1,017 years**; measured fresh against the current tree for this section it
is **1,119 AD - 1,019 years** (the tree has drifted in the time since
section 1 was written - see "A warning" below and the DICE_FREE_FLOOR_YEARS
update at the end of this section). Either way: a strictly luckier
instrument - no sack, no hazard, no project ever fails, an immortal founder -
reaches the goal roughly three times SLOWER than a real, unlucky player who
failed the point-contact transistor six times before succeeding on the
seventh. That gap is not luck. It is policy, and this section measures
exactly what policy, before section 5 tries to fix it.

### 4.1 The same calendar year, two completely different households

Running the planner's own default order (`plan`, no flags - CPM plus 12
return-on-capital side branches, side_branch_every 8) dice-free and reading
its state at year 434 AD, against the fixture's actual state at the same
calendar year:

| | planner's order, dice-free, year 434 | the player, year 434 (fixture) |
|---|---:|---:|
| capital | **-4,789** | **+607,402,406** |
| employees (named trades + artisan + scholar) | **0** (entirely) | **636** |
| scholars | 0.00 | 162 |
| artisans | 0.00 | 491.44 |
| reputation | 33.3 | 92.8 |
| goal's closure done | **30 / 168** | **167 / 168** |
| institutions running (of the 8 `pick_staffing` names) | 1 (workshop_first) | 5 |
| total nodes done (tree has 2,836) | 425 | 2,132 |

Every one of these numbers was read off the same two objects - a live
`Sim` for the planner's order, the fixture's own JSON for the player - at
the identical `year` field. The planner's order is not merely behind; at
the SAME calendar year it has no staff of any kind, negative capital, and
five-sixths of the goal's closure still untouched, while the player has
finished the tree almost end to end and is sitting on over half a billion
denarii. This is not a tech-tree-ordering gap. It is the gap the brief's own
prior names: "the planner has no model of money, staff or calendar... the
player built an ECONOMY and an INSTITUTIONAL BASE first and then bought the
closure outright."

### 4.2 The institutions the player founded in a decade - and when the planner's own order gets to each of them

`planner.pick_staffing` already NAMES the eight institutions that train
scholars and artisans (`collegium_licensed`, `freedman_staff`,
`school_founded`, `corpus_dispersed`, `patron_senatorial`, `patron_imperial`,
`academy_network`, `endowment_land`); its own docstring explains why it
does not schedule them ("measured, putting them in this order made the run
worse"). The player founded every one of them, back to back, in a single
decade. The planner's default order gets to each of them too - eventually:

| institution | player founded it (AD) | planner's order reaches it (AD, dice-free) | gap |
|---|---:|---:|---:|
| workshop_first | 205 | 127 | planner is EARLIER here |
| citizenship (not an institution, but gates collegium_licensed) | 202 | 201 | essentially identical |
| collegium_licensed | 206 | 528 | **+322 years** |
| freedman_staff | 207 | 739 | **+532 years** |
| school_founded | 211 | 788 | **+577 years** |
| patron_senatorial | 226 | 796 | **+570 years** |
| corpus_dispersed | 230 | 1,007 | **+777 years** |
| endowment_land | 216 | 1,000 | **+784 years** |
| patron_imperial | 322 | 1,001 | **+679 years** |
| academy_network | 240 | 1,023 | **+783 years** |

The planner's order is not slow to REACH the point where these become
legal - `workshop_first` and `citizenship` land within a few years of the
player, via the same mandatory, zero-slack chain
(`identity_cover` -> `patron_local` -> `workshop_first`). What diverges
completely is everything downstream of that point: the player turns that
foothold into the entire institutional ladder inside thirty-five years;
the planner's order sits on the SAME foothold for five to eight CENTURIES
before the remaining seven institutions get founded, by which point the
goal itself is only decades away.

### 4.3 The proximate mechanism: a credit-exhaustion cycle the engine's own code already names

Tracing the planner's default order year by year (dice-free) explains why.
Within five years of the 100 AD start, the household has committed to
`identity_cover` (1,580), `patron_local` (1,200) and `workshop_first`
(5,757) - all three genuinely zero-slack prerequisites of the goal - while
the engine's own reactive "earn a living" fallback (`core.py`, "EARN A
LIVING FIRST") simultaneously commits it to `exp_trade_route_extend`
(cost 4,800, net +1,700/year, a 2.8-year payback - the single best-paying
LEGAL venture the moment `patron_local` unlocks it, chosen by the engine
itself from the ENTIRE tree, not from anything this strategy file names).
Capital goes from +232 (year 101) to -4,023 (year 105) in four years,
against a 400-denarii starting kit.

`exp_trade_route_extend` finishes (year 116) but - per `auto_open_ventures`'
own documented guard ("nothing opens while you are deep in arrears... half
the credit line is the line: below it you can still open your way out,
above it you are digging" - `engine/projects.py`) - is never actually
OPENED: the household is already too deep in arrears for an ordinary
venture to clear the gate, so the entire 4,800 denarii is sunk for zero
revenue, ever. Capital sits between roughly -4,000 and -30,000 for the next
~850 years, cycling through the engine's own named insolvency mechanics -
`CREDIT EXHAUSTED: N projects stopped, unfinished` (year 907, 935),
`INSOLVENCY SETTLED: most of the debt is written off... reputation -12.0`
(907, 917, 936, each one pushing the credit freeze out another 12 years),
`creditors took what they could: ... school_founded` / `freedman_staff,
patron_senatorial, corpus_written, collegium_licensed` (935, 936 - two of
the very institutions the previous subsection is about get built, THEN
repossessed) - none of which this module edits or disputes; `engine/
projects.py`'s own comments already call this exact risk out by name.

The escape, when it finally comes (year 973-976), is not a credit event at
all: `"2 machinists finish their training"`, `"you begin teaching the first
opticians this world has ever had"`, `"chemist is no longer only your trade"`
- the SAME once-a-decade-or-never auto-teach cycle section 1 already
diagnosed for the five `TRADES_ABSENT` trades. The moment those trades
exist, projects that had been logging `"cannot go on: no engineer here...
abandoned"` for centuries start finishing, capital crosses from -18,653 to
+433 in one year and to +56,358 the next, and by year 1,000 the household
holds 24.7 million denarii, 214 scholars and 540 artisans. Section 1's
named-trade freeze and this section's credit-exhaustion cycle are not two
separate bottlenecks - they are the SAME bottleneck, observed from two
sides: the household cannot afford to keep the institutions that would
train the trades, because the trades do not yet exist to make the
institutions (or anything else) pay.

### 4.4 Reordering alone cannot touch this - measured, not assumed

Before concluding that, every one of the following was actually tried,
dice-free, against the current tree, not reasoned about in the abstract:

- `--side-branches 0` (no named side branches at all, pure CPM spine plus
  the engine's own "rest" fallback): capital -4,789.4 at year 400,
  identical to the default 12-side-branch order to the nearest tenth of a
  denarius.
- `--side-branches 60`, the candidate pool widened fivefold: capital
  -5,407 at year 600 - no better, and the household's own `freedman_staff`
  never even starts (legal, per `start_reason`, but refused by the
  `start_project` ceiling check every time it is tried).
- All twelve side branches moved to the very front of the order, ahead of
  the entire spine, instead of interleaved one per eight spine nodes:
  goal year 1,119, capital 1,772,085,619 - identical to the baseline to
  the denarius. Reordering WHERE the twelve named side branches sit changed
  nothing, because none of them is legal yet when it would matter (see
  4.5) and the engine's own "earn a living" fallback already searches the
  WHOLE tree for the best currently-legal earner regardless of what this
  strategy file names or where it names it.
- The `identity_cover -> patron_local -> workshop_first` chain deliberately
  delayed by twenty spine positions: capital -4,789.4 at year 400 again,
  identical to the unmodified order. Moving a handful of positions in a
  168-node spine does not delay anything that has no other legal
  competition in its own opening years.
- All eight `pick_staffing` institutions merged into the side-branch list
  and interleaved every four spine nodes instead of reported-only: WORSE,
  not merely unchanged - capital frozen at exactly -5,071.09 for 200
  straight years (300-500 AD), because the added upkeep (900-2,500/year
  each) deepens the arrears the household can never climb back out of
  faster than it already was.

No version of reordering the strategy file - widening, narrowing,
front-loading, interleaving, delaying, or adding institutions as named
priorities rather than scheduled moves - moved Rome's dice-free floor by
more than a rounding error, and one version made it measurably worse. This
is the same honest finding section 2 already reached for the scarce-trade
relaxation, now independently confirmed for a second, larger mechanism: **a
priority list cannot out-argue the automatic optimizer's own reactive
financial behaviour once revenue has gone thin, because that behaviour
scans the whole tree for the best legal move every single year regardless
of what any strategy file prefers, and "legal" here is decided by
prerequisites and credit, neither of which a priority order changes.**

### 4.5 A second, chaotic finding, also worth recording so nobody re-walks into it

The obvious-looking refinement - rank `pick_side_branches`'s candidates by
how soon they can legally start (the same "nearest first" measure
`_room_advice` in `labour.py` already uses), instead of by return on
capital alone, since the unfiltered ranking names side branches such as
`tr_articulated_locomotive` (71 unmet prerequisites), `chm_tnt` (66) and
`chm_dynamite` (67) that cannot fire for decades - was tried, head to head,
and reverted. Ranked by reachability ALONE: Rome ends at 1,121 (no real
change from 1,119) but Han goes from 551 to **675 - 124 years worse**. A
depth-capped hybrid that restores Han to 549 instead leaves Rome **never
reaching the goal inside a 1,200-year horizon** where the unmodified
ranking reaches it at 1,121. Swapping out which five or six cheap,
superficially interchangeable ventures get named measurably shifts WHEN
this tree's own insolvency-recovery and named-trade auto-teach cycles
happen to align - in neither a monotonic nor a predictable direction - so
"more reachable" is not "safer" here. `planner.pick_side_branches` is
therefore UNCHANGED from before this session (return on capital alone);
the attempt and its exact numbers are recorded in its own docstring so the
next agent tempted by the same fix does not have to re-discover this by
hand.

## 5. Growing the supply, honestly tried: path_search.py's third move

The brief's own instruction, read literally: a search that may only permute
the goal's closure cannot find what the 434 AD player did, because what
that player did was not a permutation - it was growth. `path_search.py`
now has a third move alongside the two section 2 already describes:

**`grow_supply`** (and its diagnostic, `diagnose_capital_trap`): whenever a
round's dice-free trial reads as the trap section 4.3 describes (capital
negative, scholars and artisans both still under 1.0, most of the closure
still undone), try founding each of `planner.pick_staffing`'s eight
institutions, ONE AT A TIME, and keep the addition only if a fresh
dice-free trial's `fitness` measures STRICTLY better with it than without -
never "obviously helpful", the same discipline `refine()` already applies
to a captured winner's order. This is the one move of the three that can
ADD something to the order instead of only resequencing what is already
named, and it is tried at most once per `search()` call (the trap, once
present, is measured to persist for centuries - see 4.4 - so re-trying it
every round would only re-spend the same compute to re-discover the same
answer).

**Measured, honestly, against the current tree: it kept none of the
eight.** Every one of `collegium_licensed`, `freedman_staff`,
`school_founded`, `corpus_dispersed`, `patron_senatorial`,
`patron_imperial`, `academy_network` and `endowment_land`, tried
individually at the search horizon, scored no better founded than not -
consistent with 4.3's finding that the blocker is not "this strategy file
never names these institutions" (it does, via `pick_staffing`) but "the
household cannot afford to keep them running once named, because the
credit-exhaustion cycle and the named-trade freeze are the same
bottleneck, and founding an institution earlier does not clear either
one." `grow_supply` reports this plainly (`--search-no-grow-supply` turns
it off and reproduces the search's exact prior behaviour) rather than
silently doing nothing: a round that tries eight candidates and keeps zero
is recorded in the search's own history and in the strategy file's
rationale, not hidden.

## 6. The honest number, before and after, both civilisations

| | Rome (`rome_100ad`) | Han (`han_china_100ad`) |
|---|---:|---:|
| dice-free, plain CPM order (`plan`, no search) | **1,119 AD / 1,019 years** | **551 AD / 451 years** |
| dice-free, CPM + search (moves 1-2, scarce-trade relaxation) | 1,121 AD (one side branch pulled; no real change) | 551 AD (recognises success on round 0, no relaxation needed) |
| dice-free, CPM + search + move 3 (`grow_supply`, this session's addition) | **1,119 AD - unchanged** (8 institutions tried, 0 kept) | **551 AD - unchanged** (no capital trap diagnosed; move 3 never triggers) |
| + descendant-centrality tie-break (section 7) | **1,119 AD - unchanged** | **551 AD - unchanged** |
| goal STARTABLE (167/168, the fixture's own milestone), same order | **1,115 AD / 1,015 years** | reaches full 168/168 at 551, so identical |

**The search is not faster than the plain CPM order on this tree, for
either civilisation, even with a genuine capacity-growing move added to
it, and that is reported plainly rather than tuned until a number looked
better.** Rome's three-times-slower-than-the-player gap (1,019 dice-free
years against the player's 334) is real, precisely diagnosed in section 4,
and NOT closed by anything expressible as a strategy file under the
current automatic optimizer: the mechanism blocking it - the engine's own
reactive "earn a living" fallback combined with its credit-exhaustion
cycle, which between them decide almost the entire opening and middle game
regardless of what any `order` prefers - is not a sequencing problem. This
is not a disappointing footnote to explain away; it is this section doing
its job the same way section 2 already did for the scarce-trade case:
trying a real, different kind of move, measuring it honestly against the
SAME fixture-backed standard the brief set, and reporting that it does not
move the number, rather than reporting a number that looks better than it
measures.

Both prior numbers in this document (1,017/1,121 for Rome, 555 for Han)
have drifted slightly - now 1,119 and 551 - purely from the tree having
moved under other agents' hands since section 1 was written; re-measured
fresh, this session, the same way section 1's own warning insists on. The
`DICE_FREE_FLOOR_YEARS` table in `engine/cli.py` (used only for the New
Game difficulty menu's wording, never for anything this module or
`planner.py` computes) is updated to match: `rome_100ad: 1019`,
`han_china_100ad: 451`.

A loose end, named rather than chased down: `engine/data.py`'s own
`STARTING_KITS` comment claims "the median year the transistor is reached
runs 476 destitute, 489 poor_scholar, 468 rich_merchant, 434 absurd" for
Rome, measured "8 runs a kit, one seed" - numbers wildly different from
everything in this section, and numbers this report does not use anywhere
above for exactly the reason "A warning, taken seriously" already names:
that comment does not say which strategy it measured, and Rome's own
`planned_rome.json` history already has one proven instance (commit
`758744b`, "10 of 10") of a pre-goal-retarget number being quoted as
current. `engine/data.py` is not this module's file to correct; this is
recorded here so whoever owns it next does not take that comment at face
value either.

## 7. A fuller account of the same player, and the sharper benchmark it sets

The 434 AD fixture (section 4) turned out to be a checkpoint, not the end
of that playthrough. The same player finished the run: goal completed **599
AD**, 2,822 of 2,833 technologies (99.6% of the whole tree), 1.1 billion
denarii, 691.7 employees, 89.8% general literacy, 168/168 road nodes -
having deliberately delayed finishing the already-startable goal by 165
years to keep building. Their own account of how they would script it
sharpens the benchmark this report has to answer, and names three ideas
this session tried against the current tree:

- **Descendant centrality** ("a cheap isolated node is less valuable early
  than a 2-year node unlocking fifteen branches"): implemented in
  `planner.backward_plan` as a tie-break within a CPM slack band, using
  `engine/data.py`'s own cached `downstream_count`, which costs nothing
  extra to read. Tested against both civilisations at multiple horizons:
  changes NEITHER Rome's nor Han's dice-free floor by a single year or a
  single denarius. Section 4.4 already explains why - the early game's
  throughput is capped by concurrent-project and credit limits, not by
  which of a small handful of simultaneously-legal nodes gets preferred -
  and this is a second, independent confirmation of that finding, this
  time from a genuinely different and better-motivated ranking principle
  than plain CPM slack. Kept anyway (see its own docstring): it is the
  more honest ranking on its own terms and regresses nothing.

- **Expected attempts** (`1/(1-p)` for a failure-prone node, so a
  95%-failure import averages 20 attempts and should be started early and
  retried opportunistically rather than saved for the end) and **a mop-up
  set working backward from the horizon** are both real, well-reasoned
  ideas about that player's OWN bottleneck - the last 11 of 2,833
  technologies, mostly high-failure late-game imports started too late in
  a run that was otherwise essentially finished. Neither one is reachable
  by this module: both are properties of a run WITH the dice on (`p` is a
  literal, seeded failure probability; a "mop-up" schedule is a plan
  against a specific unlucky sequence of past failures), and `path_search.
  py`'s whole method, by design and by this brief's own instruction, is
  the dice-OFF measurement - `DetRNG.random()` always returns 1.0, so no
  node in a dice-free trial ever fails at all, and there is no `p` for
  `1/(1-p)` to be computed FROM. Applying either idea here would mean
  quietly turning some risk back on inside a module whose entire point is
  measuring the policy with the dice removed - exactly the kind of engine-
  reaching change the brief asked this session to flag rather than make.
  Recorded as future work for whichever module measures Rome WITH events
  on (`compare`/`sweep`/`sensitivity`, none of which are this session's
  files), not silently declined.

### The sharper benchmark, answered plainly

The brief's own correction: the player's goal was startable at 434 AD -
**334 years**, not the 599 it took to actually finish, and the instrument
this session is fixing should be measured against that number, not full
completion. Measured directly (the same "closure minus the goal itself"
reading section 4.1 already uses, on the dice-free trial `backward_plan` +
`grow_supply` + descendant-centrality actually produces): the goal becomes
startable at **year 1,115 - 1,015 years**, when `single_crystal`, the last
of the closure's 167 non-goal nodes, finally completes. **The honest
answer is no: this instrument, even with every move this session added and
tested, does not get Rome to a startable goal within 350 years dice-free -
it takes roughly three times as long as a real player, playing under fog,
with real dice, on their SECOND attempt.** That is not a number this report
tuned toward; it is what `single_crystal`'s own `done_year` says when the
strategy this session actually ships is run out to where it stops
changing. Section 4.3's diagnosis says exactly why a dice-free instrument
measuring a fixed, ordered priority list cannot close a gap whose cause is
the automatic optimizer's own reactive credit and labour behaviour, not
the order of a list - and every move tried in sections 4.4, 4.5, 5 and this
section, honestly measured rather than assumed, is additional evidence for
that diagnosis, not against it.
