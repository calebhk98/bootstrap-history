# Turning on solved prices today would make land free

Found by measuring the new `sim/engine/prices.py` wiring rather than by
reading it. The wiring itself is right and is correctly defaulted OFF; this
records what the measurement says about when it may be turned ON, so that
nobody flips the switch on the strength of the coverage number alone.

## The coverage number, which looks encouraging

    PRICES.JSON BURNDOWN, rome_100ad
       solved     95   52.8%
       book       85   47.2%
       total     180

Over half of `data/prices.json` can already be replaced by a computed
number. That is the burndown the stakeholder asked for - "prices.json slowly
deleted" - and it is real.

## The number that says not yet

    materials the solver prices at exactly ZERO: 1 that matters
       iugerum_land             book = 250.0 denarii

Land is free. In a simulation whose central question is how fast an agrarian
economy can be pushed to an industrial frontier, land costing nothing is not
a rounding error - it is the single input whose scarcity drives Malthusian
pressure, rent, urbanisation and the whole shape of a pre-industrial economy.

It is not alone, and the company it keeps identifies the cause exactly:

    material                    book       solved       ratio
    cinnabar_kg             54.00000      0.00263    20,571x
    agate_kg                30.00000      0.00450     6,667x
    graphite_kg              8.00000      0.00144     5,556x
    calcite_kg               8.00000      0.00180     4,444x
    asbestos_kg              6.00000      0.00285     2,105x
    oil_mineral_kg           1.20000      0.00075     1,600x
    kieselguhr_kg            0.60000      0.00038     1,600x
    lodestone_kg             5.00000      0.00360     1,389x

Every one of those is EXTRACTED - dug, quarried or gathered rather than
made. The solver prices a material as what it costs to produce, and for
something nature supplies there is no production cost, only rent. Rent is
currently fixed at 0.0, which the solver announces on every single run:

    Rent on extracted materials is fixed at 0.0 this round (RENT_IS_ZERO)

So these are not eight separate mispricings. They are one missing mechanism,
seen eight times, and `Complaints/32` predicted exactly this before the
engine could see it.

## What follows

**The switch stays off until rent lands.** Not because the wiring is
unfinished - it is finished, it is cached correctly, it is measurable, and
the engine's behaviour is byte-identical with it off. Because the thing it
would switch to is wrong in a specific, known and already-being-fixed way.

**And coverage is the wrong readiness test.** 52.8% solved sounds like
"halfway to deleting prices.json", but the half that is solved includes the
extracted materials that are nearly free, and swapping those in would do
more damage than leaving the whole book in place. A material should only
graduate out of `prices.json` when its computed price is defensible, not
merely when one exists. Whoever builds the deletion queue should sort by
DEFENSIBILITY, not by availability - and the honest first cut of that is:
nothing `extracted_from` anything graduates until rent is real.

**This is the wiring earning its keep on day one.** `Complaints/32` measured
rent's absence in the solver a while ago and it stayed an abstract number.
Land coming out free in the engine's own goods table is the same fact, and
it is much harder to leave alone.

## Update: rent landed for ore, and land is still free

`sim/world/deposits.py` is now wired into the solver, and the line this
complaint quoted is gone. The solver's own replacement for it is honest
about its scope, which is the point of this update:

> Rent on the ore of iron, copper, tin, lead, silver and mercury is now
> priced from `sim/world/deposits.py`'s Ricardian marginal-deposit supply
> curve; **every other extracted material (forest, quarry, salt pan, gold's
> placer-and-amalgamation step) still prices at zero rent.**

So six ores gained a rent term and moved a long way toward their book
prices - cassiterite 24.6x, silver ore 8.75x, galena 7.58x, tin 6.74x - and
mercury's rent computed as exactly 0.0, which independently reproduces
`Complaints/32`'s reading through the full solver rather than a standalone
run: Almaden's grade covers the demanded output without ever pushing the
margin, so mercury's remaining gap is institutional rather than a missing
mechanism.

And:

    iugerum_land   0.00000

Land is still free. It was never going to be fixed by this work - land is
not an ore, and `deposits.py` models mineral deposits. The eight materials
this complaint listed have split into two groups: the ore ones are handled,
and the ones that come from a forest, a quarry, a salt pan or a field are
not, because nothing yet models the rent on those.

**The switch therefore stays off, for the same reason and a smaller one.**
The readiness test in this complaint is unchanged and now has a sharper
edge: a material graduates out of `prices.json` when its computed price is
defensible. For the six ores that is now arguably true. For anything whose
`extracted_from` names a forest, a quarry, a salt pan or arable land it is
still false, and agricultural land is the one that matters most, because it
is the input whose scarcity drives the entire pre-industrial economy this
project is trying to simulate.

The next piece of work this points at is not more solver wiring. It is a
rent model for land, which is a different mechanism from a mineral deposit:
a mine depletes and a field does not, so land rent comes from location and
fertility against a margin of cultivation rather than from a grade that
falls as you dig.

## Update: land rent landed, and Han China's land is still free

`sim/world/land.py` now prices `iugerum_land` as Ricardian rent at the margin
of cultivation - a civilisation's held regions sorted best-first and filled
until its population is fed, with everything better than the marginal region
earning the difference. `data/world/geography.json` gained an arable area and
a fertility multiplier for all 21 real regions, anchored so Italia is exactly
1.0 because `wheat_kg`'s own yield figure IS Roman-Italian dry-farmed wheat.

    rome_100ad        9.141 hours per iugerum   (was 0.0)
    han_china_100ad   0.0
    england_1300      0.0
    norse_900ad       0.0
    mexica_1500       0.0

Rome's margin sits at hispania; north_africa, levant_mesopotamia and italia
all earn rent above it. The mechanism works and it is genuinely
per-civilisation, which ore rent still is not.

### But only half of Ricardo is built

Rent has two sources and this has one.

The EXTENSIVE margin is better land against worse land, and that is what
landed. The INTENSIVE margin is diminishing returns to more labour on the
SAME land - the second and third ploughing of one field yielding less than
the first - and it is missing. With only the extensive margin, a
civilisation holding a single uniform region has free land no matter how
many people are on it.

That is why Han China comes out at zero while feeding 58 million people. It
is not that Chinese land was abundant; it is that the model has no way to
express a field being worked harder. A fertile island with ten million
people on it has expensive land, and this model would say it is free.

The project already knows this distinction: `sim/world/deposits.py` has both
margins, and its intensive one is the declining ore grade as a deposit is
worked out. Land has the extensive half and is missing the half deposits
already has.

So the honest reading of the table above is not "Rome has scarce land and
China does not". It is "Rome holds regions of differing quality and the
others do not", which is a statement about the model's resolution rather
than about the world. The `_doc` note and the solver's own printed message
both say this, which is the right handling - the number is wrong and the
tool says why.

### And it is a flow priced against a stock

`--compare` puts computed 9.141 hours against a book price of 3,333 hours,
which reads as a 365x disagreement and is not one. The computed figure is
one year's RENT. The book figure is a PURCHASE PRICE. Land sold for
something like twenty to twenty-five years' rent historically, so the
comparable annual figure is nearer 130-165 hours, and the computed rent is
then roughly fifteen times too low rather than 365 times.

Capitalising a flow into a stock needs a discount rate, and this project has
none anywhere - the existing capital mechanism spreads a build cost over a
service life with no interest at all. So this is not a land problem, it is a
missing mechanism that land is the first thing to need. Recorded rather than
invented.

### The switch still stays off

For a smaller reason than before. Land is no longer free for Rome, ore rent
landed last round, and the extracted materials that started this complaint
have real numbers now. What remains is that four of five civilisations still
price their land at zero for a structural reason, and that no rent anywhere
is capitalised. That is much closer than "land is free", and it is not there
yet.

## Update: the intensive margin landed, and nobody's land is free

    rome_100ad        55.779 hours per iugerum   (was 9.141)
    han_china_100ad   47.242                     (was 0.0)
    mexica_1500       18.415                     (was 0.0)
    england_1300      17.156                     (was 0.0)
    norse_900ad       13.581                     (was 0.0)

The extensive margin - better land against worse - is untouched. The
intensive margin is added beside it: output on a fixed area grows more slowly
than the labour applied to it, so by Euler's theorem on the constant-returns
production function `agriculture.py` already uses, paying labour its own
marginal product leaves land the remaining share. That residual is rent, and
it needs no worse region to compare against, which is exactly why a single
uniform region can now earn it.

### The ordering, and why it is not tuned

It falls out of population density on held territory, which is measured from
figures already in the repository rather than chosen:

    rome_100ad       0.136 person per iugerum
    han_china_100ad  0.117
    the other three  0.03 to 0.04

Rome and Han China are both dense, so their intensive rents come out close.
Rome then adds extensive rent on top, because it holds seven regions of
differing quality and China holds one. That Rome finishes highest with China
a close second, both far clear of the land-abundant three, is the "both
margins, not either alone" result this complaint asked for.

Norse, England and Mexica stay cheap because they have three to four times
more land per head, which is the correct reason for cheap land.

### It also closes most of the flow-versus-stock gap

This complaint recorded that the computed figure is a yearly rent and the
book price a purchase price, so the comparable annual figure is about 130 to
165 hours at a historical twenty to twenty-five years' purchase. Rome was
roughly fifteen times low. At 55.8 it is now about two and a half to three
times low. Still a gap, and no longer the kind that suggests a missing
mechanism.

### Two things deliberately left

The extensive fill still uses the flat reference yield rather than the
intensity-adjusted one, so a crowded civilisation's higher yield per iugerum
does not yet reduce how much land it needs in the first place. Labelled a
temporary simplification in the module rather than hidden.

And capitalising the flow into a stock still needs a discount rate, which
this project has nowhere - the capital mechanism spreads a build cost over a
service life with no interest at all. Land remains the first thing to need
one.

### A cost worth naming

`land.py` is standalone by design and may not import `agriculture.py`, so the
production elasticity and the reference labour intensity are now DUPLICATED
between the two modules rather than shared. They can drift apart silently.
That is the same class of problem as the two import roots that let one file
become two module objects, and it wants the same kind of fix: one home for a
physical constant, imported from wherever it is needed.

## Update: can the switch turn on now? Measured, and the answer is still no

Both blockers this file named - land free, and only one civilisation of five
having a rent at all - are gone. This round asked the question this file has
deferred twice already: can `use_solved_prices` be turned on. It cannot yet,
and the reason is sharper than either previous update, because measuring the
question surfaced a bug the wiring itself had, on top of the two modelling
gaps already on record.

### Bug found first: the switch would have made land free anyway

`sim/engine/prices.py`'s `solved_prices()` - the function `use_solved_prices`
actually calls - was calling `solve_prices.compute_resolvable_materials` and
`solve_prices.solve` WITHOUT the `rent_hours_per_kg_by_material` argument
that `sim/solve_prices.py`'s own `main()` builds and passes on every run.
Both default that argument to `None`, which is the old RENT_IS_ZERO answer
this whole complaint is about. So every number this file has quoted from
`python3 sim/solve_prices.py --civ ...` - land at 55.779 hours for Rome, ore
rent on cassiterite and galena, all of it - was real in the STANDALONE tool
and would still have been silently discarded the moment the engine's own
switch was flipped, because the engine-facing wrapper had never been updated
to call the same two rent functions the CLI does. A second, independent copy
of exactly the bug this complaint's first update fixed, sitting one file
away from the fix and never updated to match it.

Fixed this round, in `sim/engine/prices.py` only: `solved_prices` now calls
`solve_prices.rent_hours_per_kg_by_ore_material` and `solve_prices.
land_rent_hours_per_iugerum` itself, the same way `main()` does, before
calling `compute_resolvable_materials`/`solve`. Reproduced through the
engine's own code path, not the CLI, for all five civilisations:

    rome_100ad        55.779 hours/iugerum   (4.183 denarii)
    han_china_100ad   47.242                 (3.543 denarii)
    mexica_1500       18.415                 (1.381 denarii)
    england_1300      17.156                 (1.287 denarii)
    norse_900ad       13.581                 (1.019 denarii)

Identical to the CLI's own figures to five significant figures - the fix
reproduces the same mechanism, not a second one.

A second bug rode in with the first fix and had to be closed at the same
time: land rent is genuinely PER CIVILISATION (`sim/world/land.py` prices a
civilisation's own held regions), but the cache this module keeps was keyed
on the held GATE-NODE set alone. Two civilisations can hold an identical
gate-node set while holding entirely different territory - nothing about
`requires_node` says anything about geography - so the old cache key could
have handed a second civilisation the first one's land price the moment
both asked in the same process. `civilization_id` is now a first-class
parameter of `solved_prices` and `priced_goods_table`, folded into the
cache key alongside the gate-node set, defaulting to `solve_prices.
DEFAULT_LAND_CIVILIZATION` (Rome) so every existing call site - which knows
nothing of the new parameter - behaves exactly as before. Pinned in
`sim/tests/test_engine_prices_civilization_rent.py` (module name for
registration in `sim/tests/__main__.py`: `engine_prices_civilization_rent`),
including the fabricated case (same held-technology set, different
`civilization_id`) that a real pair of civilisations might never happen to
exercise on their own.

### 1. The three-state split, per civilisation, through the now-fixed wiring

Measured with `sim.engine.data.goods_provenance(starting_techs,
civilization_id=civ)` for each civilisation's own `starting_techs`:

    civilisation        solved       gated    no_recipe   total
    rome_100ad         103 57.2%    68 37.8%    9  5.0%     180
    england_1300       103 57.2%    68 37.8%    9  5.0%     180
    norse_900ad        101 56.1%    70 38.9%    9  5.0%     180
    han_china_100ad    100 55.6%    71 39.4%    9  5.0%     180
    mexica_1500         83 46.1%   88 48.9%    9  5.0%     180

`no_recipe` is flat at nine across every civilisation, which is right - it
is nothing making a material ANYWHERE, an authoring gap independent of who
is asking. `gated` moves with how much of the tree an era has actually
reached (Mexica's 88 is the largest, matching it holding the fewest
technologies of the five). Coverage still says nothing about defensibility,
which is the whole reason this complaint exists - see next.

### 2. The indefensible ones: this is bigger than the original eight

The original measurement named eight extracted materials priced near zero
because rent was fixed at 0.0 everywhere. Splitting Rome's 103 "solved"
materials by WHY each one resolved, using the same rent dict the solve
itself used, finds the eight were a sample, not the whole population:

    category                                    count   median   mean     worst
    manufactured (real recipe, no rent question)  40      3.9x    85x*   1210x*
    extracted, ore rent actually attached          2     37.5x    37.5x    60x
    extracted, rent still fixed at zero           60     39.8x   873x   20571x

    * dominated by mercury_kg and gold_kg, both "manufactured" by this
      classification (their own recipes have no extracted_from) but poisoned
      by an extracted, zero-rent INPUT - see below.

Sixty of 103 Rome materials the solver marks "solved" are extracted goods
still priced at exactly the labour cost of digging or gathering them, with
no rent term at all - not the eight named in 2024, all of them: agate,
calcite, graphite, asbestos, oil_mineral, kieselguhr, lodestone,
mineral_pigment, natron, boric_acid, bitumen, fluorspar, emery, cork,
horsehair, salt, wood/timber/firewood, ox and mule (pasture, an unmodelled
land use), and - this round's own addition to the list - four of the six
ore materials the mechanism was built for: `iron_ore_kg`, `copper_ore_kg`,
`silver_ore_kg` and `cinnabar_kg` land at exactly zero rent for ROME
specifically (only `cassiterite_kg` and `galena_kg` come out positive this
era), because the Ricardian margin for those four metals' fixed demand
figure does not bind against Rome's own gated recipe set. `mercury_kg`'s
gap (1210x) and `gold_kg`'s (990x) are both this same zero-rent cinnabar
propagating one and two steps downstream through completely ordinary
smelting recipes that have nothing wrong with them.

Reading each disagreement rather than trusting the ratio, as this complaint
has said from the start to do:

  - **cinnabar_kg, mercury_kg (1,209-20,571x, book higher).** The computed
    number is an honest floor (extraction plus smelting labour, nothing
    hidden) and the earlier update already found mercury's OWN margin does
    not bind at Almaden's grade - an institutional finding, not a missing
    mechanism, for mercury. Cinnabar's 20,571x is that same finding one
    step upstream. Neither number is fully defensible: the book's 720
    hours is probably closer to the truth (cinnabar/mercury was a Roman
    STATE MONOPOLY worked by convict labour under armed guard, which is a
    real cost this model has no way to represent - not a competitive
    Ricardian rent at all, but an institutional friction), and the computed
    number is a genuine physical lower bound. Recorded as neither side
    winning, not a solver bug.
  - **gold_kg (990x, book higher).** Deliberately left at zero rent by
    `sim/solve_prices.py`'s own design (folded placer-and-amalgamation, no
    separate ore stage - see RENT_BEARING_ORE_MATERIALS's own comment).
    The book price is more defensible here: gold's ancient scarcity premium
    (monetary demand, not industrial use) is exactly the kind of thing a
    production-cost model cannot see by construction, independent of rent.
  - **agate_kg, calcite_kg, graphite_kg, asbestos_kg, and the rest of the
    sixty (labour-only, book higher by 2-3 orders of magnitude in the
    worst cases).** The computed number is NOT defensible - it is the same
    finding as the original eight, generalised: nature does not hand out
    a quarry, a salt pan or a placer deposit for free just because
    `sim/world/deposits.py` has not been extended to model it yet. The
    book number is not obviously right either (it is 91.8% one author's
    estimate), but "not obviously right" beats "structurally cannot be
    right", which is what a hand-computed zero rent is here.
  - **wood_ash_kg (13.75x), linen_rag_kg (4.87x), manure_kg (3.75x)
    (computed HIGHER than book).** Read individually rather than as a
    pattern: wood_ash and manure are trivial in absolute size (both under
    1.1 hours) and the book figure for both looks like a rounding
    afterthought rather than a considered estimate - the computed number is
    the more defensible one for both. linen_rag_kg's gap is a hint the BOOK
    is internally inconsistent (its own rag price does not track its own
    linen price by the ratio the recipe implies), which is a finding about
    `prices.json`, not about the solver.
  - **platinum_g (2.40x, computed higher).** More likely a mislabelling
    than a price dispute: `platinum_ore_kg` resolves as available to every
    era (`requires_node: null`), and platinum was not smelted before the
    18th century. This is an authoring question for whoever owns
    `data/production/` - flagging it rather than fixing it, since `data/`
    is out of this round's scope - not a solver defect.

### 3. Flow-versus-stock: still real, still not the reason to hold the switch

Rome's land rent (55.779 h) against the book's purchase-price figure
(3,333 h) is a 59.8x disagreement on `--compare`'s own arithmetic, and this
complaint has already shown that reading it as a straight ratio is wrong -
the book is a STOCK (a purchase price) and the computed figure a FLOW (one
year's rent). At a historical 20-25 years' purchase the comparable stock
figure is roughly 1,115-1,395 hours, so the real disagreement is about
20-25x, not 60x, and entirely explained by there being no discount rate
anywhere in this project to do the capitalising with - not a defect in the
rent calculation itself. This blocks `iugerum_land` ITSELF from graduating
cleanly (a caller that wants a purchase price would get a rent, correctly
computed but the wrong quantity), but it does not block anything else: no
other material in this table is priced as a stock, so this is a land-only
gap, exactly as the previous update concluded, now confirmed to still be
land-only.

### 3b. The gap this file had not yet named: land's rent does not reach a single crop

`sim/world/land.py`'s own module docstring already recorded this precisely
(see its OTHER SIMPLIFICATIONS section) but this complaint had not yet drawn
the line to the switch decision, so it is drawn here. `recipe_cost_and_
allocation` attaches a material's rent only to a recipe whose OWN output key
is a key of `rent_hours_per_kg_by_material` - which today holds exactly six
ore materials plus `iugerum_land`. Checked directly against every
production entry: not one recipe anywhere in `data/production/` lists
`iugerum_land` as an `inputs` entry.

So `wheat_kg`, `linen_kg`, `wool_kg`, `olive_oil_kg`, `cork_kg`,
`oak_bark_kg`, `rose_petals_kg` and `timber_m3` - every material
`data/production/40_organics.json`'s own `_note` names as GROWN and
land-limited - price at exactly their labour cost, with a rent term that is
mathematically guaranteed to be zero regardless of what `iugerum_land`
itself is worth, because nothing routes it to them. Verified by
construction, not by inspection: `wheat_kg`'s computed price (0.25974
hours) is 150 labourer-hours divided by 577.5 kg of output and NOTHING
else, matching its `inputs: {}` exactly.

This is the finding that most changes this file's own headline claim.
"Nobody's land is free" is true of the ABSTRACT GOOD `iugerum_land` and
false of the thing this project actually cares about: a civilisation with
scarce land does not (yet) pay more for its bread, its wool, its cloth or
its fuel than one with abundant land, in this model, at all. Malthusian
pressure - the reason this complaint opened by calling land "the input
whose scarcity drives the entire pre-industrial economy" - still does not
reach a single price a household actually pays. `iugerum_land`'s own price
is real and matters for the three tech-tree nodes that consume it directly
(verified: three nodes name it in their own `mat`), but it is a dead end for
everything grown ON that land.

This is NOT something this round fixes. A correct fix needs to know how
much land a batch of wheat (or wool, or linen) actually represents, and
that number does not exist as a structured field anywhere today - the
`basis` string ("per hectare of flax per year") is prose for a person, not
data for `solve_prices.py` to read, and inventing a structured
`iugerum_per_batch` field is a `data/production/_SCHEMA.md` change, which
is `data/`, out of this round's ownership and someone else's call to make
alongside whoever is already live on that schema. Recorded here as the
single most consequential open item, not implemented.

### 4. What a gated material should cost: recommended, not implemented

`priced_goods_table`'s own docstring already names the real question: a
material this era's recipes cannot reach falls back to the book price
today, and the honest alternative is probably "cannot be had at any price"
or "arrives at an import price," not "costs what a modern author guessed."
Not implemented this round, for the same reason as 3b: either answer needs
a mechanism this project does not have yet - unavailability needs
`sim/engine/economy.py` to handle a material a household cannot buy at any
price without crashing every place it currently assumes a float, and an
import price needs a trade/reach model this file's own tool (`sim/
solve_prices.py`) has no view of at all - and both belong to files this
round does not own (`economy.py` is explicitly another agent's this round;
trade and reach live in `sim/world/`). Recommended for whoever picks this
up next: unavailability is the more defensible default for a "gated"
material whose gate is a HARD technological wall (aluminium, for instance -
no amount of Roman effort produces it), and an import price is more
defensible for one gated only by REACH (something Han China already knows
that has not yet diffused to Rome) - which argues for splitting "gated"
itself into those two reasons before picking a single answer, rather than
picking one answer for both.

### 5. Yes or no

**No, not for the table as a whole.** But this is not a flat no, and the
measurement above is precise enough to say exactly where the line sits.

**Yes, right now, for:** the 40 Rome materials (and their equivalents in
the other four civilisations - the exact list moves with which techniques
an era has reached) that resolve through a REAL manufacturing recipe with
priced material and labour inputs and no extracted, zero-rent good
anywhere upstream of them - things like brick, ceramic, cloth, ink,
parchment, glue, thread, stone blocks. Their disagreement with the book is
modest (median 3.9x for Rome) and reads as "the book was a rough guess,"
not "the computed number is structurally wrong." `cassiterite_kg` and
`galena_kg` join this list - their rent mechanism is real and their
disagreement with the book has already closed by an order of magnitude.

**No, not yet, for:** every extracted material with no rent attached - the
sixty-plus per civilisation this update measured, `iron_ore_kg`,
`copper_ore_kg`, `silver_ore_kg` and `cinnabar_kg` among them this era, and
everything downstream of any of them (`mercury_kg`, `gold_kg`, and by
extension anything that consumes those). They graduate only once
`sim/world/deposits.py`'s Ricardian mechanism (or something like it) covers
their own deposit category, or someone judges a specific one's zero rent
already correct for a specific era (mercury's Almaden case is the one
example on record).

**No, and structurally so, for:** every GROWN, land-limited material -
wheat, linen, wool, olive oil, cork, oak bark, rose petals, timber - until
land rent has a physical channel into their price, which is a
`data/production/` schema question, not a solver one. This is the single
biggest reason the switch should stay off: it is not a small remaining
gap, it is the mechanism this whole complaint was chasing (Malthusian
pressure reaching a real price) not yet reaching ANY price a player
actually pays.

**Conditions for turning the switch on**, named rather than left implicit:
graduate materials INDIVIDUALLY (a per-material list, not a global
boolean), starting with the manufactured set above; hold every extracted
material back until its own deposit/rent mechanism exists or its zero rent
is a judged, documented finding rather than a default; and do not graduate
`iugerum_land` into anything that reads as a purchase price until this
project has a discount rate, or land into anything that reads as feeding
Malthusian pressure until a crop recipe actually consumes it.
EOF
