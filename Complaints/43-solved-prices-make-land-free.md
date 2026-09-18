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
EOF
