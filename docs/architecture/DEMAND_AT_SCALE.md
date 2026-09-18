# Does household demand work away from Roman Egypt?

**Reviewing:** `sim/world/demand.py` at commit `ee0b8bb`, against the
stakeholder's own critique (quoted in full below) and the three questions he
ranked. **Status:** analysis and a concrete recommendation, not a plan
anyone has approved.

**Every number in this document was produced by running something against
that commit**, and each section names the exact command. Nothing here was
reasoned about in the abstract; the task this document answers explicitly
required running the module rather than reading its algebra and guessing
what it does.

`sim/world/demand.py` is being renamed and re-worded by another agent while
this document is being written, and `sim/world/deposits.py` by a third. This
document does not edit either file. Two of its module-level constant names
(`BETA_FOOD_SURPLUS_SHARE`, `BETA_MANUFACTURES_SURPLUS_SHARE`,
`BETA_SILVER_SURPLUS_SHARE`) changed mid-session to
`FOOD_SURPLUS_BUDGET_SHARE` / `MANUFACTURES_SURPLUS_BUDGET_SHARE` /
`SILVER_SURPLUS_BUDGET_SHARE` between this document's first and second draft.
Every command below was re-run after that rename and gives the same figures;
where this document needs to point at one of those constants it does so
through the stable public objects (`demand.FOOD.marginal_budget_share`, not
the private name), for the same reason `sim/tests/test_demand_at_scale.py`
does.

---

## 0. The stakeholder's critique, in his own words

> Does the demand work when you raise the economy, like in an industrial
> revolution Britain, or modern day USA, or whatever? What about a
> fictional Atlantis whose coinage is shells? ... yes, a computer when no
> one can afford breakfast won't sell. BUT, computers sell today even when
> they don't make you richer, so that is clearly not the full story right?
> And even people in poor 3rd world countries that walk for miles for
> water, can still buy phones today, so it's not like just because you are
> in subsistence farming, you can't afford a phone right? But IDK how to
> model that.

Three questions follow from this, in the order he ranked them. This document
answers them in that order: the subsistence floor first (the sharp one),
then whether the demand system scales to industrial and modern income
levels, then Atlantis and the shells.

---

## 1. The subsistence floor is not a floor

### 1.1 What the module actually predicts, run rather than reasoned about

`household_quantity_demanded_per_capita` solves the textbook Stone-Geary /
linear expenditure system: a household pays every good's subsistence
quantity first, then splits whatever income is left across every good in a
fixed marginal budget share. Below subsistence - income too small to cover
even the committed subsistence bundle - the function switches to a second
formula: it scales every good's subsistence quantity down by the same
factor, `income_per_capita / committed_per_capita`.

That second formula is the sharp point. A good with a subsistence quantity
of zero - `demand.py`'s own `SILVER` and `MANUFACTURES`, and anything else
without a biological floor - has its scaled-down quantity computed as `0.0
scaled by any factor`, which is `0.0` regardless of the factor. **A
household below its own food floor demands exactly zero of every other
good, at any price, however cheap.** Not "less than it would demand with
more income" - exactly, identically zero, the same zero whether the price
is a denarius or a thousandth of one.

Constructing the stakeholder's own example - a household with a real food
subsistence floor and a cheap phone available - and asking the module for
both goods' demand at several below-subsistence income levels:

```
python3 - <<'PY'
from sim.world import demand
food = demand.Good("wheat_kg", demand.FOOD.subsistence_quantity_per_capita_per_year, 0.95)
phone = demand.Good("phone", 0.0, 0.05)
basket = (food, phone)
demand.validate_basket(basket)
wheat_price = demand._illustrative_recursive_labour_content_price_per_kg("wheat_kg")
prices = {"wheat_kg": wheat_price, "phone": 0.01}
committed_food_cost = wheat_price * food.subsistence_quantity_per_capita_per_year
for fraction in (0.30, 0.50, 0.80, 0.95, 0.99, 1.00, 1.01, 1.50, 2.00):
    income = fraction * committed_food_cost
    phone_qty = demand.household_quantity_demanded_per_capita(phone, prices, income, basket)
    print("income = %.2fx committed food cost -> phone demand = %.6f" % (fraction, phone_qty))
PY
```

```
income = 0.30x committed food cost -> phone demand = 0.000000
income = 0.50x committed food cost -> phone demand = 0.000000
income = 0.80x committed food cost -> phone demand = 0.000000
income = 0.95x committed food cost -> phone demand = 0.000000
income = 0.99x committed food cost -> phone demand = 0.000000
income = 1.00x committed food cost -> phone demand = 0.000000
income = 1.01x committed food cost -> phone demand = 3.069328
income = 1.50x committed food cost -> phone demand = 153.466387
income = 2.00x committed food cost -> phone demand = 306.932773
```

This is not a smooth ramp that happens to pass through a low value near the
floor. It is an exact zero for every income below the floor, followed by an
immediate jump to a specific positive quantity the instant income crosses
it by even one percent - a household earning 99% of its committed food cost
buys no phones at all; the same household earning 101% buys three a year.
Real households do not have a step discontinuity in their spending at any
single income level, and this one is a direct artefact of the algebra, not
a description of anything in the world. `sim/tests/test_demand_at_scale.py`'s
`HardSubsistenceFloorZerosOutEveryOtherGoodTests` pins both the exact zero
and the exact jump size (`3.069328`) so this cannot silently change without
the pinned test failing first.

### 1.2 What the evidence says, and what it rests on

The stakeholder is right that this is empirically false, and the citations
he is gesturing at are specific enough to name:

- Banerjee and Duflo, "The Economic Lives of the Poor" (*Journal of Economic
  Perspectives*, 2007), surveys household expenditure data for people living
  under $1-2/day across thirteen countries and finds that a meaningful share
  of spending goes to festivals, alcohol, tobacco and (in the more recent
  editions of this literature) mobile phones and phone credit, among
  households whose measured caloric intake sits below any commonly used
  subsistence threshold. This is the single clearest empirical rebuttal to
  the module's below-subsistence branch: real households facing a
  below-floor income do not spend everything they have on the floor good,
  they keep spending on other things too.
- Jack and Suri, "Risk Sharing and Transactions Costs: Evidence from Kenya's
  Mobile Money Revolution" (*American Economic Review*, 2014), documents
  M-Pesa's adoption reaching a majority of Kenyan households, a population
  whose median income sits well under any reasonable subsistence line for
  the basket this module would build for it.
- Jensen, "The Digital Provide: Information (Technology), Market Performance,
  and Welfare in the South Indian Fisheries Sector" (*Quarterly Journal of
  Economics*, 2007) is the sharpest single case for treating a phone as
  something other than ordinary consumption - Kerala fishermen's mobile
  phone adoption reduced price dispersion and waste by letting them call
  ahead to markets, raising their income rather than only spending it. This
  is evidence for interpretation (b) below specifically, not for the
  subsistence-floor question in general.

These are stated as facts this document rests its argument on, not
re-derived from this project's own data - there is no equivalent household
survey in this repository to run a number from, and CLAUDE.md 3.4's own
instruction is to say so plainly rather than invent one.

### 1.3 Four ways to fix it, and which one to build first

The task named four candidate mechanisms. Evaluated against what each would
actually take to build in this codebase, and against how much of the
evidence above each one explains:

**(a) The floor is social and tradeable, not biological.** Loosen the
Stone-Geary formula's below-subsistence branch so a household short of its
subsistence bundle does not spend literally everything on it - some fixed
or income-scaling share of spending happens on non-subsistence goods even
while calorie-short. This explains the Banerjee-and-Duflo evidence most
directly, because festivals, tobacco and alcohol are not investments by any
reasonable reading - real households really do trade some biological margin
for a status or social good. The cost is that it touches the functional
form itself: the "pay every floor first, in full, before anything else"
structure is Stone-Geary's own definition, so this is not a parameter change
but a different utility specification (something closer to a household that
trades off calorie shortfall against other goods at a finite, not infinite,
marginal rate of substitution near the floor).

**(b) The good is not consumption, it is investment, and belongs on the
income side.** A phone that finds work, checks crop prices or moves money
(Jensen's fishermen, M-Pesa) raises the household's own income rather than
spending down a fixed one, so it should be modelled as a purchase that pays
for itself out of the extra income it generates - closer to how this module's
own `derived_intermediate_demand` treats a firm's capital purchase (a
`build_materials` line amortised because it enables future output) than to
a household's Stone-Geary basket. The cost here is smaller in one specific
sense: it requires no change to `household_quantity_demanded_per_capita`'s
already-validated algebra at all. It requires a new mechanism entirely - a
household treated as a small enterprise that can buy a capital good if its
expected return exceeds its price - which does not exist in this module or
adjacent to it (this module's own docstring says it "does not model saving,
credit ... or a household's labour-supply decision"). It also only explains
the subset of below-subsistence purchases that genuinely raise income; it
has no answer for tobacco, alcohol or a festival.

**(c) Lumpy durables plus saving.** Nobody buys one thirty-sixth of a phone
a month; they save and buy one, which a per-period flow demand system
cannot express by construction - this module's own docstring names "saving,
credit, storage of wealth across years" as exactly what it does not model.
Building this means adding a wealth stock, a saving rule, and a discrete
purchase-timing decision - a genuinely new state variable that a per-period
demand function cannot represent no matter how its formula is adjusted, and
one that (per CLAUDE.md 3.5) would need to round-trip through
`SAVE_FIELDS` correctly from day one.

**(d) Network and status goods.** A good's value to one buyer rising with
how many others already own it needs an aggregate adoption state fed back
into every household's demand for it - a genuine feedback loop between the
market-clearing calculation and household preferences that does not exist
in this module (or, so far as this document found, anywhere else in
`sim/world/`). It is the most explanatory of the four for phones and
M-Pesa specifically (a phone is worth more precisely because other people
already have one to call), but it is also architecturally the most
different from anything this module currently does.

**Recommendation: build (a) first.** Three reasons, in order of weight:

1. It is the only one of the four whose evidence base covers the FULL
   range of what Banerjee and Duflo actually document - festivals, tobacco
   and alcohol are not investments and do not need network effects or
   durability to explain; they need the floor to stop being absolute.
   Building only (b) would leave the sharpest defect - the hard zero at
   1.4 in this document - fully in place for every non-investment good, and
   this module's basket has at most one plausible investment good in it
   (nothing at all in `DEFAULT_BASKET` today; a phone is the stakeholder's
   own hypothetical, not something this basket currently represents).
2. It needs no new state. (c) needs a wealth stock and a saving rule; (d)
   needs an adoption-share state and a feedback loop into the price
   solver. (a) only needs the below-subsistence branch of an existing,
   already-tested function to trade off differently - a change to one
   function's algebra, not a new mechanism, a new persisted field, or a new
   cross-module wire.
3. It is the cheapest to get honestly wrong and cheaply corrected. A
   softened floor is one number (how much of spending stays protected even
   below the floor) with an honest `temporary_heuristic` declaration next
   to it, in the same spirit as `FOOD_SURPLUS_BUDGET_SHARE`'s own
   provenance note - exactly the kind of number CLAUDE.md 3.4 asks to be
   tagged rather than invented silently. (b), (c) and (d) each need a
   mechanism built from scratch before there is anywhere to put a number at
   all.

(b) is not wrong and should not be shelved - it is the right model
specifically for a phone used to find work or check prices, and it reuses
`derived_intermediate_demand`'s existing shape almost exactly (a household's
capital purchase, amortised against the income it enables, is the same
arithmetic as a firm's). It is the natural SECOND piece: once (a) stops the
floor from being an absolute wall, (b) is what explains why a **productive**
purchase in particular clears that softened floor more easily than an
unproductive one, because it pays part of its own way. (d) is worth
returning to only once a basket actually contains a good whose adoption
externality matters for this project's own scenario (a telegraph network,
a rail gauge standard); nothing in the current three-good `DEFAULT_BASKET`
needs it yet.

---

## 2. Does it scale? Testing at industrial and modern income levels

### 2.1 The closed form, run at six orders of magnitude of income

`household_budget_share`'s own value for a good with a positive subsistence
quantity is, algebraically, that good's own marginal budget share plus a
term that shrinks toward zero as income grows - the same `A + B/income`
shape `market_clearing_price`'s own module-docstring derivation gives for a
fixed-supply good's price. That means the food budget share can fall a long
way as income rises (Engel's Law holds in *direction*), but it converges on
the food good's own fixed marginal budget share and can never fall below
it, at any income, however large.

Run directly, holding prices fixed (the demand module takes prices as a
parameter and does not compute how technology would change them as
income rises - see its own "TAKE WHAT YOU NEED AS PARAMETERS" section - so
this isolates the demand-side Engel curve alone, which is what the
stakeholder's question is actually about):

```
python3 - <<'PY'
from sim.world import demand
basket = demand.DEFAULT_BASKET
wheat_price = demand._illustrative_recursive_labour_content_price_per_kg("wheat_kg")
prices = {"wheat_kg": wheat_price, "manufactures": 1.0, "silver_kg": 50.0}
committed = sum(prices[g.name] * g.subsistence_quantity_per_capita_per_year for g in basket)
for multiple in (1.01, 1.1, 1.5, 2, 3, 5, 10, 20, 50, 100, 300, 1000, 3000, 10000, 100000, 1000000):
    income = multiple * committed
    bins = (demand.IncomeBin(population=1.0, income_per_capita_per_year=income,
                              population_percentile_from_top=(0.0, 1.0)),)
    share = demand.household_budget_share(demand.FOOD, prices, bins, basket)
    print("%10.2fx committed subsistence cost -> food budget share = %.4f" % (multiple, share))
PY
```

```
      1.01x committed subsistence cost -> food budget share = 0.9931
      1.10x committed subsistence cost -> food budget share = 0.9364
      1.50x committed subsistence cost -> food budget share = 0.7667
      2.00x committed subsistence cost -> food budget share = 0.6500
      3.00x committed subsistence cost -> food budget share = 0.5333
      5.00x committed subsistence cost -> food budget share = 0.4400
     10.00x committed subsistence cost -> food budget share = 0.3700
     20.00x committed subsistence cost -> food budget share = 0.3350
     50.00x committed subsistence cost -> food budget share = 0.3140
    100.00x committed subsistence cost -> food budget share = 0.3070
    300.00x committed subsistence cost -> food budget share = 0.3023
   1000.00x committed subsistence cost -> food budget share = 0.3007
   3000.00x committed subsistence cost -> food budget share = 0.3002
  10000.00x committed subsistence cost -> food budget share = 0.3001
 100000.00x committed subsistence cost -> food budget share = 0.3000
1000000.00x committed subsistence cost -> food budget share = 0.3000
```

The curve is monotonically decreasing and asymptotes to `0.30` - exactly
`demand.FOOD.marginal_budget_share` - and is already indistinguishable from
it to four decimal places by the hundred-thousand-fold row. It never goes
lower, at any income multiple, because `0.30` is the fixed marginal budget
share coded into `DEFAULT_BASKET`'s `FOOD` good, and the closed form's only
income-dependent term shrinks to nothing rather than crossing zero.

### 2.2 The scale check against real economies

| Economy | Real food budget share | This model's ceiling on how low it can go |
|---|---|---|
| Pre-industrial agrarian (this project's own calibration target, `HOUSEHOLD_FOOD_BUDGET_SHARE_LOW`/`HIGH`) | 60-80% | reachable - the curve above passes through this band between roughly 1.5x and 2.5x the committed subsistence cost |
| Industrial Britain, working-class households, circa 1900 (a commonly cited range from historical household-budget studies of the period, e.g. Feinstein's wage and cost-of-living series) | roughly 40-50% | reachable - between roughly 3x and 5x |
| Modern USA (US Bureau of Labor Statistics Consumer Expenditure Survey, food at home plus food away from home as a share of total expenditure, most recent published years) | roughly 10-13% | **not reachable at any income level** - the model's own asymptote (30%) sits above the top of this range and every value below it is unreachable regardless of income |

This is the concrete form of what the task asked to check: a linear
expenditure system holds marginal budget shares fixed, which is exactly
Engel's Law's mechanism as far as it goes (a good with a positive
subsistence quantity always has a *falling* share as income rises), but the
share it falls to is fixed by that same marginal budget share, not
derived from anything about how food's importance actually changes at
industrial or post-industrial income levels. The direction is right; the
asymptote is a wall the model cannot get past no matter how the population
or its income are scaled up. `sim/tests/test_demand_at_scale.py`'s
`EngelCurveFloorsAtTheMarginalBudgetShareTests` pins both halves of this -
the monotonic fall (correct) and the floor at the marginal budget share
(the defect) - as two separate assertions, so a fix that only changes the
number `0.30` is caught changing the wrong thing while a fix that changes
the *functional form* is recognised as such.

One clarification worth stating plainly, because it could be misread as a
second finding: `demand.py`'s own `CalibrationAgainstHistoricalTargetsTests`
already reports that at this project's own Roman illustrative population
and mean income (`python3 -m sim.world.demand`), the food budget share
comes out at **37.8%**, below even the low end of its own 60-80% calibration
target. That is a real, already-flagged disagreement, but it is a
*calibration* question (is `0.30` and the illustrative income level the
right pair of numbers for Rome specifically), separate from the *scaling*
defect this section is about (no pair of numbers lets the curve fall below
`0.30` at any income, which is the wrong shape regardless of which specific
numbers are chosen for a pre-industrial calibration).

### 2.3 What would fix this, and what it costs

The standard next step in the demand-systems literature is exactly what the
task names: a functional form whose *budget shares themselves* vary with
income, rather than only the term multiplying a fixed share. The Almost
Ideal Demand System (Deaton and Muellbauer, 1980) and its quadratic
extension QUAIDS (Banks, Blundell and Lewbel, 1997) are the standard
references - both let each good's budget share be a function of the
logarithm of income (and, in QUAIDS, its square), rather than a constant
plus a `1/income` term. The cost is real: both need more data than this
module currently uses per good (AIDS needs an income elasticity in
addition to Stone-Geary's subsistence quantity and marginal budget share;
QUAIDS needs a second income-response parameter on top of that), and
neither has the same closed-form single-good market-clearing price that
`market_clearing_price` derives in one line from Stone-Geary's linear
structure - solving for the price that clears a fixed quantity under AIDS
or QUAIDS is a numerical root-find rather than the closed form this module
currently exploits. That is not a reason not to do it eventually, but it is
a real cost this document is naming rather than hiding: adopting either
form gives up the very closed form `market_clearing_price`'s own module
docstring is proud of having found, in exchange for a food-share curve that
can actually reach single digits at high income. Given CLAUDE.md 3.4, this
is exactly the kind of migration worth naming now and doing later rather
than doing quietly inside this task's scope.

---

## 3. Atlantis and the shells

### 3.1 The claim, verified rather than assumed

`sim/solve_prices.py`'s own header states its numeraire is one hour of
unskilled labour (the `labourer` trade), not a coin - confirmed by reading
that file rather than taking it on the task's word:

```
sim/solve_prices.py:26-38 (excerpted):
NUMERAIRE: one hour of UNSKILLED labour, per the design doc's Part 2.1. The
`labourer` trade is the unskilled one ... Every wage is expressed as a
ratio against `labourer`'s rate, so `wage_of("labourer") == 1.0` by
construction and every price this script prints is "how many hours of
unskilled labour", never denarii.
```

`sim/world/demand.py` never reads `data/prices.json` at all -
`NoBookPriceHardcodeTests.test_module_never_opens_the_price_file` enforces
this at the file level (parsing the module's own source and checking every
string literal that ends in `.json`), so nothing in the demand module's
actual computation can be secretly reading a wage table denominated in
denarii. Every reference to `denarii` or `coin` in `demand.py` is prose
inside a `why=` or `source=` provenance string, never inside a function
body - `grep -n "denari\|coin" sim/world/demand.py` returns three matches:
two are on `SILVER_TO_LEAD_PRICE_RATIO_HISTORICAL`'s own declaration,
explaining why its calibration target should not be expected to match
`data/prices.json`'s book figure, and the third is a passing mention of
"hoarded coin" inside `SILVER_SURPLUS_BUDGET_SHARE`'s own `why=` string,
listing coin among the things silver demand represents. None of the three
is reached by any function above `if __name__ == "__main__"`.

### 3.2 Why this is not just an absence of currency code, but a property of the mechanism

The stronger claim - and the one actually worth confirming - is not merely
that the module happens not to read a currency file today, but that its
mechanism has no way to depend on a currency even if someone tried to wire
one in, because every function's return value depends only on *ratios*
between the prices and the income it is handed, never on their absolute
size. This is the standard economic property of "no money illusion" -
demand under Stone-Geary (like almost every neoclassical demand system) is
homogeneous of degree zero in prices and income taken together: multiply
every price and the income figure by the same constant and the quantities
demanded do not change at all. Verified directly, rather than asserted from
the textbook property alone, with a deliberately non-round conversion
factor (a round one like 10 could hide a bug that only shows up away from
the module's own illustrative numbers):

```
python3 - <<'PY'
from sim.world import demand
basket = demand.DEFAULT_BASKET
wheat_price = demand._illustrative_recursive_labour_content_price_per_kg("wheat_kg")
prices_hours = {"wheat_kg": wheat_price, "manufactures": 1.0, "silver_kg": 50.0}
income_hours = 400.0
SHELLS_PER_HOUR = 17.3
prices_shells = {k: v * SHELLS_PER_HOUR for k, v in prices_hours.items()}
income_shells = income_hours * SHELLS_PER_HOUR
for good in basket:
    q_hours = demand.household_quantity_demanded_per_capita(good, prices_hours, income_hours, basket)
    q_shells = demand.household_quantity_demanded_per_capita(good, prices_shells, income_shells, basket)
    print("%-14s hours-priced=%.6f shells-priced=%.6f identical=%s"
          % (good.name, q_hours, q_shells, abs(q_hours - q_shells) < 1e-9))
PY
```

```
wheat_kg       hours-priced=627.436765 shells-priced=627.436765 identical=True
manufactures   hours-priced=220.098739 shells-priced=220.098739 identical=True
silver_kg      hours-priced=0.338613 shells-priced=0.338613 identical=True
```

And `market_clearing_price`'s output rescales exactly with the conversion
factor rather than staying fixed or moving unpredictably, which is what
would have to happen for its *price* output to also be currency-free (a
price is a ratio too - "how many shells per kilogram" - so it should scale
with whatever "one shell" is worth, exactly the way "how many labour-hours
per kilogram" scales with what one hour is worth):

```
price in hours:  33861.34   price in shells:  585801.26   ratio: 17.300000  (conversion factor: 17.3)
```

**Verdict: the stakeholder's suspicion is correct, and it is the easy one.**
A civilisation using cowrie shells, tally sticks, or nothing at all needs no
change to `sim/world/demand.py` whatsoever, because the module's entire
mechanism only ever consumes ratios between prices and income, never an
absolute figure denominated in a particular unit. This holds precisely
because the module never reads `data/prices.json`'s wage or purchase-price
tables and the numeraire question is settled one layer down, in
`sim/solve_prices.py`, which already made the harder decision (a labour-hour
numeraire rather than a metal-weight one) for reasons unrelated to this
task. `sim/tests/test_demand_at_scale.py`'s
`NumeraireInvarianceConfirmsTheAtlantisCaseTests` keeps both checks above as
permanent regression coverage - not a defect pin, since there is nothing
wrong here to invert, but a property worth catching immediately if a future
change ever makes it stop holding (for instance, a term that reads a price
or income value's absolute size rather than a ratio between two of them).

---

## 4. Summary and ranked recommendation

| Question | Verdict |
|---|---|
| Below-subsistence household with a cheap phone available | The model predicts **exactly zero** demand for the phone at any income below the food floor, with a discontinuous jump to a specific positive quantity (3.069328 units at this document's own worked numbers) the instant income crosses the floor by as little as one percent. This is the sharp, real defect the task flagged it as. |
| Does it scale to industrial Britain / modern USA (Engel's Law)? | Direction is right (food's budget share falls monotonically as income rises across six orders of magnitude, `0.99` down to `0.30`); magnitude is structurally wrong (the curve asymptotes at food's own fixed marginal budget share, `0.30`, and cannot fall below it at any income - real modern-US food shares run `0.10`-`0.13`, entirely outside what this functional form can ever reach). |
| Atlantis and the shells | **Confirmed, no change needed.** The module is homogeneous of degree zero in prices and income together (verified directly, not assumed), and never reads a currency file at all. The numeraire question is fully and correctly settled one layer down, in `sim/solve_prices.py`'s own choice of one hour of unskilled labour. |

**Ranked recommendation for what to build first: soften the subsistence
floor (candidate (a) in SS1.3)**, ahead of treating a good as investment,
ahead of adding saving and lumpy durables, and ahead of network effects.
It explains the widest slice of the real evidence (Banerjee and Duflo's
non-investment below-subsistence spending, which an investment-only model
cannot touch at all), it needs no new state (no wealth stock, no adoption
share, no credit mechanism), and it is the cheapest to tag honestly as a
`temporary_heuristic` in the style this module already uses for its beta
shares, rather than requiring a whole new mechanism before there is
anywhere to even put a number. The Engel-curve defect in SS2 is real and
worth fixing (AIDS or QUAIDS, at the cost this document names in SS2.3 of
giving up `market_clearing_price`'s closed form), but it only matters once
this project's scenario actually reaches industrial or modern income
levels; the subsistence-floor defect is live at the income levels the
project is simulating today.

---

## 5. What this document could not do, and what would need to change to let it

**`sim/tests/test_demand_at_scale.py`** (new, in this change) pins both
defects found above (the hard zero and its discontinuity in SS1; the
Engel-curve floor at the marginal budget share in SS2) as passing tests
that assert today's behaviour explicitly, in the style
`sim/tests/test_price_solver_cycles.py` used for Complaints/31 before it was
fixed - each assertion names what a correct fix should change it to, with
instructions to invert rather than delete. A third class confirms the
Atlantis finding (SS3) as ordinary regression coverage, since there is
nothing wrong there to pin.

**This file is not yet registered in `sim/tests/__main__.py`'s `TOPICS`
list**, so `python3 sim/test_regressions.py` does not run it yet. The task
that produced this document explicitly excluded editing that file. The line
that needs adding is one entry, alongside `"demand"` at line 125:

```python
    "demand_at_scale",
```

**`sim/constants.py` needs no change.** This document's tests use plain
numbers for their own scenario construction (income multiples, a
conversion factor, an illustrative phone price), the same way
`sim/tests/test_demand.py` and `sim/tests/test_price_solver_cycles.py`
already do - a test file constructing its own numbers for a scenario is not
the same thing as a `sim/world/` module declaring a number that feeds the
simulation, which is what `declare()`'s provenance registry exists to
police. If SS1.3's recommended fix is built, whatever number it introduces
(how much of spending survives below the subsistence floor) would be
declared inside `sim/world/demand.py` itself with `kind="temporary_heuristic"`,
using the existing `KINDS` vocabulary in `sim/constants.py` - no new kind is
needed for it, so no change to that file is needed for this either.

---

## Follow-up: the income distribution cannot produce a poor household

The subsistence cliff described above is now fixed - the floor is tradeable,
price bites below the line, and a household at 0.99 of its floor buys 1,000
times more of a good made 1,000 times cheaper where before it bought exactly
zero at any price.

The headline figures did not move, and the reason is a second defect.

`income_bins` draws from a **Pareto Type I** distribution, which has a HARD
MINIMUM: no draw can fall below it, by construction. At the illustrative
Roman scenario - 55 million people, mean income 550 labour-hours a year,
Gini 0.40, twenty bins - the poorest bin sits at

    poorest bin   239.17 hours/capita/year   (43.5% of the mean)
    richest bin  3046.55
    cost of all subsistence floors: 61.39

So the poorest fifth of a pre-industrial population is modelled at nearly
four times subsistence, and **the share of the population below the
subsistence line is exactly zero**. Not small - zero, and zero for any
parameters that leave the Pareto minimum above the floor.

That is wrong about the world in a way that matters. A pre-industrial
economy has people at and below subsistence continuously; that is what makes
a bad harvest a famine rather than an inconvenience. It is also why the
cliff fix, though correct and tested, changes nothing in the demo: the
scenario never enters the regime it repairs.

**The cause is a known bad fit rather than a bad parameter.** Pareto Type I
describes the TOP tail of an income distribution well - that is what Pareto
observed and what it is for - and describes the bottom badly, because a hard
lower bound is exactly the wrong shape there. The standard alternative is
lognormal for the body of the distribution, or a lognormal body with a
Pareto tail spliced above some threshold, which is the usual empirical
compromise.

Fixing it would make the cliff repair observable, would let famine
mortality connect to income rather than only to harvest, and is a
prerequisite for asking the stakeholder's own question - whether a
subsistence farmer can buy a phone - of a population that actually contains
subsistence farmers.

Not done here. Recorded with its measurement so the next person does not
have to find it twice.
