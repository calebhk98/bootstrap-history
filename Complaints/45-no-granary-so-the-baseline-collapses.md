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
