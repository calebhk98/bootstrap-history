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
