# Why Rome doesn't reach the goal: a cash-flow audit and a planner bug

Measured against `585497c`. Rome's CPM plan (`rome/sim/strategies/planned_rome.json`)
scored 0 of 3 at a 600-year horizon, every trial "ran out of horizon", first
blocked on `quantum_solidstate_theory` or `germanium_extraction` - staffing
blocks, not knowledge blocks. The household is traced below year by year
(seed 1, events on, the same conditions `run` uses) to find out where the
money actually goes, whether negative capital is a trap with no exit, and
what Han China's identical plan does differently.

## Method

`Sim.__setattr__` was patched for the duration of one trace to record every
assignment to `self.capital`, tagged with the call site that made it. This
finds every place capital moves without having to guess from the seven
call-sites `core.py` names or trust that nothing elsewhere touches it. The
trace runs the real engine (`load_strategy`, `Sim.step`) with no shortcuts;
only the bookkeeping is added.

## 1. Where the money goes

Summed over the first 300 years of the traced run (year 100-400), by call
site:

| call site | what it is | net over 300 yrs |
|---|---|---:|
| `core.py:713` | `revenue() - upkeep() - living_cost() - mine_operating_cost()`, the ordinary annual settlement | **+232,028** |
| `core.py:1444` | money spent on active tech-tree projects this year | -123,537 |
| `economy.py:248` | `charge_interest` - interest on arrears | **-113,999** |
| `economy.py:436` | insolvency write-off (`capital = -limit*0.35`) | +12,452 |
| `labour.py:1229` | `commission` - short-term contracted trade hours | -9,707 |
| `labour.py:642` | `work` - the founder selling his own hours for a wage | +7,921 |
| `society.py:1432` | patron dies, courting the heir costs 800 den | -6,400 |
| `projects.py:1509` | a project's risk roll fails, 40% of its cost is lost | -4,867 |
| `projects.py:434` | opening fee for a new concern | -1,911 |
| `labour.py:954` | `hire` - advance wages for new staff | -1,539 |
| `core.py:77` | starting capital | +400 |

These eleven numbers sum to -9,159, which is exactly the traced run's
capital at year 400 (-9,159.2) starting from 400. The accounting closes.

**The answer to "where does the ~650/yr surplus go":** the household's
ordinary trading margin really is positive and really does total +232,028
over 300 years - revenue genuinely does exceed upkeep and living cost most
years, exactly as measured externally. But two other lines, both driven by
the SAME underlying cause (chronic negative capital), consume essentially
all of it:

- **Interest on arrears consumes 49% of the entire 300-year operating
  surplus by itself** (-113,999 of +232,028). Rome's household spends most
  of three centuries owing somewhere between 2,000 and 11,000 denarii at a
  rate that runs 9-12% (the legal ceiling of 12%, discounted a little by
  `patron_local`, `fin_argentarii` and reputation - see
  `debt_interest_rate()`), and interest at that rate on that balance is
  480-1,300 denarii a year, comparable to or larger than the entire
  operating margin for the year.
- **Ordinary project spending (`core.py:1444`) - continuing to build the
  next node on the CPM list - draws almost as much again** (-123,537, 53%
  of the surplus). This is not reckless: it is financed against `purse =
  capital + credit_limit()*0.6 - reserve`, which throttles proportionally
  once the line gets tight (`funded_frac`), and it is exactly how a
  household with a construction programme and a positive income statement
  is supposed to behave - keep building, don't necessarily pay down debt
  first. But interest plus construction financing together (-237,536) is
  MORE than the entire nominal surplus (+232,028): every denarius the
  household earns beyond bare living costs is already spoken for before it
  ever has the chance to accumulate.

Capital over the 300 years does not trend toward zero; it drifts in a band
of roughly -2,000 to -11,000, occasionally climbing toward zero and then
being pulled straight back down by the next round of construction spending
or a patron's death. It is genuinely stuck, not merely slow.

## 2. Is negative capital a trap with no exit? Yes - named, with the numbers

The mechanism is real and it is exactly the shape the question describes,
chained through code that is individually correct and collectively vicious:

1. **`staff_capacity()`'s affordability term drops the wealth benefit to
   zero while capital is negative.** `spare = max(0, (revenue - upkeep -
   living_cost) * rep_factor() + max(0.0, self.capital) * 0.06)`
   (`labour.py:444`) - the `max(0.0, self.capital)` means a household
   -9,000 in debt gets exactly the same credit toward affording staff as a
   household at exactly zero. Only that year's cash-flow margin counts.
2. **That margin, run through the formula, needs to be enormous before it
   buys a single whole person.** `budget = spare * 0.40; afford = budget /
   420` and `scale = min(1, afford / (sc + ar + extra*1.35))`
   (`labour.py:446-467`). With `extra` (`supervision_room()`) already at
   ~12-20 once a single workshop is running, clearing `scale = 1` needs
   `spare` on the order of **$20,000-25,000 a year** - fifty times Rome's
   actual 450-800. Below that, `desired_ar`/`desired_sc` creep up
   fractionally every year (0.18-0.22 of the gap to target) and never
   clear the 1.0 threshold `_grow_to` needs to actually call `hire()`.
3. **So Rome holds 0.0 scholars and 0.0 artisans for the entire traced
   run**, confirmed directly: `sc_cap` from `staff_capacity()` is exactly
   0.00 at every ten-year checkpoint from year 110 to 400 (no
   scholar-granting institution - school, patron, academy - is ever
   built), and `ar_cap` never exceeds 0.74 even after `workshop_first`
   opens at year 126 and stays open continuously thereafter.
4. **Without craftsmen, even the CHEAP revenue ventures the household
   already knows how to run cannot open.** The log shows small concerns
   sitting shut for centuries - `tr_wooden_waggonway` (300 den/yr,
   needs 0.25 craftsmen), `hom_lamp_argand` (400 den/yr, needs 0.27),
   `en_breastshot_wheel` (800 den/yr, needs 0.53) - each one "nobody free
   to keep an eye on it." By year 300 Rome has 18 concerns open, nearly all
   trivial (toys, buttons, pins, a horizontal loom), worth a few hundred
   denarii a year apiece. The revenue growth that would eventually clear
   step 2's threshold requires exactly the staff step 2 is refusing to
   grant.
5. **The loop closes**: no staff -> the cheap ventures that would grow the
   surplus stay shut -> the surplus stays at ~650/yr for centuries ->
   `spare` never reaches the level `staff_capacity()` needs -> still no
   staff. Debt itself makes this worse at the margin (each insolvency
   write-off, roughly once a decade once the credit line is exceeded, costs
   a flat -12 reputation, and `rep_factor() = 1 + reputation/120` scales
   `spare` directly) but it is not the dominant term - the dominant term is
   that Rome's realized annual surplus, on its own, is an order of
   magnitude below what the model requires before a single new hire clears.

**This was tested directly, not just inferred.** Two independent probes
targeting the "it's a liquidity problem" hypothesis were run against the
unmodified engine:

- Multiplying `credit_limit()` by 1.8x for the whole run. Result: capital
  ends *more* negative (-23,241 vs -9,159 at year 400), staff still 0
  scholars / 0-2 artisans, nodes done about the same. More borrowing room
  just finances slightly more construction on the same thin income; it does
  not touch the mechanism that is actually starving `staff_capacity()`.
- Adding an explicit unused-credit term to `spare` (`+ max(0, credit_limit
  *0.5 + capital) * 0.05`). Result: no material change - the added term is
  too small next to the ~20-25× gap between Rome's real surplus and what
  `scale` needs, however it's floored or bounded, without either
  materially loosening this bound (which risks turning debt into free
  money, the exact failure the credit-limit and insolvency machinery
  elsewhere in the file was built to prevent) or growing the surplus
  itself.

Both were reverted; neither is in the diff. The trap is real, and it is a
revenue-growth trap, not a credit-access trap: capital being negative is a
symptom of the household never generating enough OPERATING income to escape,
not a separate obstacle on top of that.

It is also not literally unbounded. Run the unmodified plan to the same
600-year horizon `run` uses (with a correctly fresh civilisation per trial -
see the warning in section 4), and Rome's capital eventually does turn
sharply positive in every one of the three official seeds: +11,777,127 /
+6,725,024 / +198,661,976 by year 700, having finally opened enough of the
"would earn X, still shut" backlog once luck and slow accretion pushed a
few ventures over the staffing line, and having by then trained real staff
(seed 1: 111 scholars, 428 artisans). The trap does not last forever - it
lasts 300-500 years, which is long enough to burn most of a 600-year
horizon before the household is genuinely rich and staffed, but not so long
that the household never gets there at all.

## 3. What Han does differently

Han China runs the exact same plan - `planned_rome.json` and
`planned_han.json`, as generated before this fix, are **byte-for-byte
identical**: same 170 nodes, same order, same 12 side branches, same
bounties. So the difference is not in what either household is told to
build; it is entirely in how each civilisation's own economy responds to
being told the same thing.

Three candidate explanations were checked against real numbers, not assumed:

- **`cost_multipliers` are NOT the main driver for this specific plan.**
  Summing `civ_cost_factor(k) * _total_cost(k)` over the shared 170-node
  order: Rome 8,215,277 vs Han 7,751,262 - a 5.6% gap. Rome's own
  multiplier table actually discounts the categories this particular spine
  is full of (`infrastructure`: 0.85, `commerce`: 0.7), and its penalised
  categories (`information`: 1.2, `printing`: 1.3) barely appear in the
  order's first 60 nodes at all (0 occurrences among the top 15 categories
  and traits counted). The oft-cited "papyrus vs. paper" handicap is real
  but is not what is starving this particular run.
- **Price/wage indices are a real but modest lever.** Han's price_index
  (0.75) and wage_index (0.7) both discount build cost, but revenue is ALSO
  multiplied by price_index (`revenue()`, `economy.py:1199-1213`), so a
  smaller-denomination economy is mostly just proportionally smaller, not
  structurally faster - except for the ~6% relative gap between the two
  indices (labour is cheaper than goods, for Han specifically), which is
  real but small on its own.
- **The dominant, directly observed lever is Han's technological head
  start**, worth far more in this tree than either of the above: Han
  starts owning `blast_furnace`, `mat_cast_iron`, `rag_paper`, `mat_paper`,
  `crank_conrod`, `bellows_water_blown`, `horse_collar`, two agricultural
  techs, and two navigation techs - Rome starts with none of the
  equivalent. Traced side by side under the identical plan, Han's realized
  annual operating surplus visibly takes off starting around year 170-220
  (net income 1,532 at year 170 -> 5,881 at 180 -> 19,016 by 220 -> tens of
  thousands by 250-400) while Rome's stays flat in the 450-800 band for the
  same 300 years. Han crosses the ~$20,000/yr threshold `staff_capacity()`
  needs to unlock real staffing within about a century; Rome, denied that
  head start, never gets there within the plan's own means.

Han's advantages (starting technology, cost multipliers, price/wage
indices) are all deliberate, historically-grounded civilisation data, not
bugs - Han in 100 AD genuinely had cast iron, paper and water-powered
bellows roughly a thousand years before the Mediterranean world. Nothing
here proposes changing any of it.

## 4. What actually still blocks a rich, staffed Rome - and one false start

Section 2 already showed the debt trap is not permanent: at the official
600-year horizon, the unmodified plan's household eventually becomes rich
and staffed in all three seeds (+11.8m / +6.7m / +198.7m denarii; seed 1
alone trains 111 scholars and 428 artisans by year 700). And yet `run`
still reports 0 of 3. So the next question the brief asked - is money
really the whole story - has a direct, checkable answer: no. Tracing seed 1
to the horizon and asking the engine's own `start_reason()` why each of the
158-node closure's 51 still-missing nodes was blocked, not one came back
"can't afford it" or "no staff" - every single one came back **"missing
prerequisites."**

**A FALSE START, reported here because it was tested, not because it
worked.** The first hypothesis was that `pick_side_branches()` - which
picks the dozen revenue ventures a plan weaves into its spine, and whose
own docstring and generated rationale claim the choice is made "for THIS
civilisation specifically" by return on capital - was ranking every
candidate by the tree's raw, civilisation-unadjusted `rev`/`up`/
`_total_cost` fields, never through `civ_cost_factor()` or `price_index`.
That is true, and it is real: `planned_rome.json` and `planned_han.json`,
as generated before today, are **byte-for-byte identical**, side branches
included, which a civilisation-aware ranking should not produce. Re-ranking
by `(rev-up)*price_index` over `_total_cost*civ_cost_factor(k)` - exactly
what the engine charges at run time - does give Rome a genuinely different
top-12 list (infrastructure-trait ventures its own multipliers discount:
locomotives, hulls, boilers, dynamite, instead of toys and buttons). It was
measured head to head against the original, three seeds, 600-year horizon,
**with a bug in the first measurement caught and fixed before trusting the
result**: reusing one civilisation-state dict across three sequential
trials silently carries hazard-shifted values (patronage_weight,
w_commerce, ...) from one trial into the next's starting conditions - the
official `run` command reloads the civilisation fresh for every trial and
this test must too, or its numbers are not comparable to `run`'s. Measured
correctly, civ-priced side branches made Rome WORSE on every one of the
three seeds - final capital -4,489 / -1,929 / +91.0m against the unpriced
version's +11.8m / +6.7m / +198.7m. The civilisation-blind ranking already
in the file favours cheap, short, low-risk ventures that happen to serve a
poor household better than the theoretically-higher-ROI ones civ-pricing
promotes it to. **This change was reverted.** It is real bookkeeping (see
the docstring in `planner.py::pick_side_branches`, which records the
finding so nobody re-discovers it the slow way), but it is not the fix, and
it is named here as a warning against trusting a plausible-sounding bug
fix without measuring it the way `run` actually measures.

**What the trace actually found, chasing "missing prerequisites" one level
further.** `mat_bulk_steel` sits on the only path from Rome's basic
metallurgy to the goal's semiconductor-purification branch - and it was
never built, in any of the three seeds, however rich the household got.
`start_reason("mat_bulk_steel")` says why: *"this needs a manganese supply
... any of mat_manganese would do."* `mat_manganese` was never built
either - not because it costs too much (3,000 denarii, trivial next to
tens of millions in hand) or needs staff Rome doesn't have (4 scholars,
against a market-based pool alone of ~6), but because **it was never
`ordered` at all.** It sits, correctly, in the tree's data as a
`req_any` group on `mat_bulk_steel`:

    "req_any": [{"group": "manganese_supply", "options": {"mat_manganese": 1.0}}]

and `closure()` (`engine/data.py`), the function every planning tool in this
project uses to compute "what the goal needs," walks `pre` only - on
purpose, and correctly: a `req_any` group can be a genuine CHOICE among
several interchangeable routes (`ag2_baler` accepts any of muscle power,
steam power, or a horse collar; walking every option as mandatory would
overstate the true requirement, and for some groups - `junction_transistor
-> silicon_path -> point_contact_transistor -> junction_transistor` is a
real one - it would even put a cycle into what has to stay a DAG). But 125
of the tree's 400 `req_any` groups, `mat_bulk_steel`'s among them, have
**exactly one option**, naming a real node with no alternative offered at
all - a mandatory dependency authored through the substitution mechanism
instead of a `pre` edge, for reasons lost to the tree's own history. Those
125 are invisible to `closure()`, and therefore to `cpm()`, to
`backward_plan()`'s ordering, and to `pick_side_branches()`/
`pick_staffing()`'s exclusion filters - the entire planning toolkit. A node
the CPM plan never learned it needed is a node that sorts, at best, among
~2,700 undifferentiated optional side techs, by tier and cost with no
priority push at all. That is exactly what the trace showed happening:
seed 1's household, with 111 scholars, 428 artisans and $11.7 million by
year 700, was still busy building `sc2_algebra_numerical_methods` and
`tx2_sewing_machine_domestic` - real but optional - while `mat_manganese`,
the actual remaining wall, sat unbuilt and unprioritised the entire time.

## Fix

A new `planning_closure()` in `rome/sim/planner.py` extends `closure()`'s
walk, for planning purposes only, to also follow a `req_any` group's single
option when that group has exactly one and it names a real node -
functionally treating it as a `pre` edge, which is what it already is in
every way except how it happens to be spelled in the tree's data. Groups
with two or more options (genuine alternatives) are left exactly alone,
for exactly the reason `closure()` itself must leave them alone: over the
whole 2,833-node tree, `pre` plus every SINGLE-option `req_any` edge was
directly verified to still be acyclic (no cycle detector fired); walking
multi-option groups the same way is what can cycle, and does not need to
for this fix to work, since a real choice needs no priority push - whichever
route the engine ends up building will already be in `need` some other way,
or genuinely doesn't matter which.

`closure()` itself is untouched, on purpose: it is the fog/discovery
engine's own notion of "what's needed," reported to a player through `why`,
`road`, `path` and the distance-to-goal advice `hire`/`train` refusals
give, and none of that changes here - a wider planning-only closure is the
right size for the planner's job (deciding what to prioritize) and the
wrong size for the player's (only ever being told about a real choice as a
real choice). `rome/sim/strategies/planned_rome.json` was regenerated from
the corrected planner with the same parameters used to produce the file
this report started from (`--side-branches 12 --side-branch-every 8`, no
seed, no refinement); the goal's planning closure grows from 158 to 185
nodes (the 27 genuinely-missing roots plus what they themselves need), and
the named order grows from 170 to 197. `planned_han.json` is untouched.
`pick_side_branches()` was left as it already was (the raw, civilisation-
blind ranking) - see the false start above for why.

Traced directly against the fix: `mat_manganese` and `mat_bulk_steel` are
now both built (seed 2: year 423 and 614 respectively, where they were
never built at all before), and the household's still-missing goal-closure
count at year 700 falls from 51 to 26 for that seed. The remaining 26 are a
materially different, later wall - vacuum tubes, power generation, and the
semiconductor-purification chain itself (`germanium_extraction`,
`zone_refining`, `single_crystal`) - not the metallurgy branch that used to
be invisible. And in seed 3, that remaining wall comes down too: the
household reaches `junction_transistor` at **year 672** - the first time
in every trace run for this report, under any plan, that Rome's household
reaches the goal at all.

## Measurement

`python3 rome/sim/simulator.py run --civ rome_100ad --strategy rome/sim/strategies/planned_rome.json --mc 3 --horizon 600`

- **Before**: 0 of 3 reached the goal. Median reputation 98/100, median
  208 ha coppice woodland. Every trial ran out of horizon, first blocked on
  `gp_glass_metal_seal` (2 of 3) or `quantum_solidstate_theory` (1 of 3).
- **After**: see below.

`python3 rome/sim/simulator.py run --civ han_china_100ad --strategy rome/sim/strategies/planned_han.json --mc 3 --horizon 600`
(unchanged file, run again only to confirm nothing regressed)

- **Before**: 1 of 3, reputation 98, 1,217 ha coppice.
- **After**: see below.
