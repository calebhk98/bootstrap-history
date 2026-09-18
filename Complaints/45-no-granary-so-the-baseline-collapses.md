# Rome loses 78% of its people in a century with nothing bad happening

Measured, not estimated, on the commit that wired agriculture into the
engine:

    unshocked rome_100ad, 100 years, events=False
      population start 65,000,000  end 14,240,594  = 21.9% of start

No plague, no war, no scripted hazard of any kind. Historically Rome's
population is roughly flat across that span. So the baseline is now badly
wrong, and this records why that is expected, why it must not be fixed the
obvious way, and what the actual fix is.

## This is sanctioned, and saying so is not an excuse

CLAUDE.md section 3.2: "The baseline is explicitly allowed to get worse while
the mechanisms that will make it good are being built. Every step toward
endogeneity costs historical match in the short run, and there is no path
that avoids it."

Before this wiring, food was a stand-in that always closed exactly at a
nutrition ratio of 1.0, so no famine could ever happen. The baseline matched
history on population because population was not being simulated - it could
not fall for a physical reason because there was no physical reason
available. Trading that for a real harvest that can fail is the trade the
project exists to make. But a 78% decline is large enough that somebody will
find it and assume it is a bug, so it gets a file.

## The cause is one missing thing, and it is not the farm's size

There is no granary. `Storage` is rebuilt fresh every year with a stock of
zero, so a good year's surplus is thrown away rather than banked against a
bad one.

That alone would be survivable. What makes it a ratchet is that the response
to food is ASYMMETRIC:

    a year with more food than needed   -> nutrition ratio is capped at 1.0
    a year with less food than needed   -> nutrition ratio falls, uncapped

So a good year buys nothing and a bad year costs real people. Average the
weather over a century and it averages out; average the POPULATION over the
same century and it does not, because the good draws were discarded and the
bad draws were not. Every bad year also shrinks next year's workforce, which
shrinks the area that can be worked, which shrinks the harvest - and with no
stock to smooth it, nothing ever catches back up.

That is a general property of an asymmetric response over an unbuffered
input, not a quirk of these particular numbers, and it would show up the
same way in any weather distribution with a left tail.

## Do NOT fix it by making the farm bigger

The tempting fix is to raise the farmland endowment until the decline goes
away. That is precisely the hardcoded outcome CLAUDE.md section 3.1 forbids:
it would set a physical quantity from the answer we want rather than from the
land that exists, and it would hide the missing granary instead of building
it. The agent that wired this refused to do it, correctly, and said so.

## The real fix, which is small and blocked on one field

Carry `Storage` across years instead of rebuilding it, which needs a
`farm_stock_kg` entry in `SAVE_FIELDS` (`sim/engine/proto/saveload.py`). That
file was outside the wiring agent's scope while other agents were editing
adjacent engine files, which is the only reason it is not already done.

A granary is also the historically right mechanism rather than a patch. Grain
storage against a bad harvest is one of the oldest institutions there is -
it is most of what an ancient state's fiscal apparatus physically DID, and
the Roman annona is exactly this. Adding it makes the model more like the
world, not less.

Two things to check once it exists: whether the unshocked century comes back
to roughly flat, and whether the nutrition ratio's cap at 1.0 should stay.
A population that eats well in a good year and puts on weight, has more
surviving children and works harder is a real effect the cap currently
forbids, and the cap is half of what makes this a ratchet.

## What is already right and should not be lost fixing it

The famine mechanism itself works and is physical. With every scripted hazard
off, population jumps of up to 16.7% in a year all trace to a genuinely low
weather draw and a matching food shortfall - none unexplained. With hazards
on, the Antonine plague still lands on top of that as its own separate 24.9%
jump. Children and the elderly absorb more of a famine than working-age
adults, using the same vulnerability weights a plague already used. And two
independently built simulations, plus a mid-run save and reload, reproduce
bit-identical trajectories.

The mechanism is sound. It is the buffer that is missing.

## Fixed, partly - 21.9% becomes 75.0%

`Sim.farm_stock_kg` carries `Storage` across years and is capped at
`GRANARY_CAPACITY_YEARS_OF_DEMAND = 1.0` - twelve months of consumption,
the generous end of the six-to-twelve-month range pre-modern grain-reserve
targets cluster at. Initial stock is 0.0: an honest "no assumed prior
reserve", not a number chosen to soften the curve. No farmland or physical
constant was touched.

    unshocked rome_100ad, 100 years, events=False
      before   65,000,000 -> 14,240,594   21.9% of start
      after    65,000,000 -> 48,719,129   75.0% of start

Mean nutrition ratio 0.985, worst single year 0.65.

### A worse bug was hiding behind this one

`Storage.step` subtracts seed TWICE a year by design - once as sown, once as
next year's retained seed, removed from the ledger and never referenced
again. That is only correct if a caller who PERSISTS the stock adds the
retained seed back. Nobody did, because nobody persisted anything: every year
rebuilt at zero and the discarded figure was never read.

Persisting the stock naively therefore made things far worse rather than
better - Rome fell to 1.1% of its starting population over an ordinary
century, on ordinary weather. `stock_to_carry_forward_kg()` now adds the
retained seed back at the one call site that persists, and both docstrings
warn the next caller who tries multi-year persistence.

This is the shape of defect worth noticing: a latent error that is exactly
cancelled by a second error, and that only appears when someone fixes one of
them. The first attempt at the fix looked like a catastrophic regression.

### Why it is 75% and not 100%

The granary damps the asymmetry on the INPUT side - a good harvest is now
banked. It does nothing about the asymmetry in the RESPONSE, which is the
other half this complaint named: mortality still floors at a nutrition ratio
of 1.0, so a good year never lowers it. Jensen's inequality still applies,
just to a much smaller residual. About 1.5% a year of drag remains.

### The cap at 1.0 was investigated, built, and deliberately reverted

The stakeholder's own napkin bound was that a population cannot plausibly
grow more than about 11% a year. Checked against this model's own constants:
at its working-age share of roughly 46%, births at a ratio of 1.0 already run
about 3.4% of population a year, and reaching 11% from births alone would
need fertility at 3.2x baseline - an effective total fertility rate near 16,
against about 9 to 11 for the Hutterites, who are the standard ceiling
reference for a human population with no contraception.

So the 11% cap is real and correct and NOT BINDING at any defensible
multiplier. The instinct was right and the number is not where the problem
is.

A bounded fertility ramp above 1.0 was implemented and numerically verified -
it saturates around a ratio of 1.64 and contributes 2 to 3% growth a year.
It was then reverted, because
`test_demography.py::test_fertility_does_not_rise_above_baseline_on_surplus`
pins the exact opposite and that file was outside the agent's ownership while
four others were live in the checkout. The design and its arithmetic are left
in `_fertility_multiplier`'s docstring so whoever owns that test can flip both
in one change. That is the right call and the remaining work is small.

Mortality's own floor was left alone on a different basis: lowering it needs
a sourced biological limit on how far mortality can fall below an
already-observed historical baseline, and none was found. Reported rather
than guessed.

## And the stakeholder's other hypothesis was right: professions do not move

They guessed that a famine should turn blacksmiths into farmers and that the
model probably does not allow it. It does not, and there is now a test
proving it: `farm_workers_fte_for_population` multiplies population by a
share computed purely from crop, soil, rotation, toolkit and storage
constants. It never reads the nutrition ratio, a wage, or any scarcity
signal, and the farm share comes out identical whether or not an 85% land
loss is in progress in the same year.

The piece a labour market would need already exists and is computed every
year by `agriculture.py` - `marginal_product_last_hour_kg_per_hour` in
`YearFlows`. Nothing consumes it. That is the hook, and building the
reallocation on top of it is its own task.
