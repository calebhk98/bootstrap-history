# Rome's harvest in Britain and Egypt are the same coin flip

The unshocked century ends at 76% of starting population. The stakeholder
said "with 0 large events, you shouldn't have a population decline over a
century - something is wrong there", and they were right, but it is not the
mortality floor, the granary or fertility. It is that a continent-spanning
empire gets ONE weather draw a year.

`Sim._farm_year_weather_seed(year)` is a pure function of (civilisation id,
year). One seed, one multiplier, applied to the whole territory. Rome holds
seven regions from Britannia to Mesopotamia and every one of them has the
same harvest, good or bad, every single year.

## What pooling does, measured

Averaging N independent draws divides the standard deviation by the square
root of N. Applying that and re-running the unshocked century:

    regions pooled    effective stdev     century end
     1 (today)            0.2000             76.0%
     3                    0.1155             98.1%
     7                    0.0756             98.7%
    21                    0.0436             98.5%
    63                    0.0252             98.4%

Three regions is enough. The century goes from a 24% collapse to
essentially flat, which is what the historical record says Rome's population
did.

## Why this is the cause and not a coincidence

The mortality agent decomposed the drag before this was found, and its
numbers predict exactly this result. `_excess_mortality_multiplier` is flat
above a nutrition ratio of 1.0 and rising below it, so it is CONVEX at the
kink. Measured over the real century: the expected multiplier is 1.0788
while the multiplier at the mean ratio is 1.0322. About 60% of the excess
mortality is therefore pure Jensen's inequality - drag produced by variance
around a mean that is itself almost exactly 1.0.

Jensen's term is second order in the standard deviation, so halving the
deviation quarters the drag. That is why three regions already gets most of
the benefit and sixty-three adds almost nothing.

So the chain is: one weather draw for a continent produces variance that a
real empire never faced, and a correctly one-sided mortality response turns
that excess variance into dead people.

## The mechanism this stands in for is real, and Rome is the textbook case

Pooling is not a modelling trick. It is what an empire physically DID. The
annona - the grain fleet from Egypt and North Africa - existed precisely so
that a bad Italian harvest did not become an Italian famine, and it worked
because Egyptian and Italian weather are close to uncorrelated. Egypt's
harvest depends on a Nile flood fed by Ethiopian monsoon rain; Italy's
depends on Mediterranean winter rainfall. The same logic is why Athens
imported from the Black Sea and why medieval cities sat on rivers.

A model that gives one weather draw to a whole empire has removed the single
most important reason large states were worth building.

## What to do, in order

**Per-region weather draws.** The seed becomes a function of (region, year)
rather than (civilisation, year), and a civilisation's harvest is the sum
over the regions it holds. That alone produces the pooling above, with no
new mechanism, because holding more and more varied ground IS the risk
pooling. It also makes conquest matter for a new reason: territory buys
harvest stability, not only acreage.

This lands naturally with the re-tiling work (`Complaints/46`) - once tiles
exist, per-tile weather is the obvious next line, and a tile is small enough
that neighbouring tiles should be correlated rather than independent, which
is a refinement worth having rather than a problem.

**Then correlation, not independence.** Neighbouring regions share weather.
The square-root law above assumes perfect independence and so overstates the
benefit; real pooling across a 2,000-km empire is somewhere between one draw
and seven independent ones. A distance-based correlation would sit naturally
on top of tiles with centroids, which `geography.json` already has.

**And then trade.** Pooling by holding territory is only half of it - Athens
pooled by BUYING, without owning Crimea. That needs the grain to physically
move, which is `sim/engine/economy.py`'s freight work, already wired.

## What was correctly NOT done

The mortality floor stays as it is. Two agents independently searched for a
sourced limit on how far mortality can fall below an already-near-subsistence
baseline and both came back empty: historical class mortality differentials
are smallest exactly where baseline mortality is highest, and the British
peerage shows mortality no better - sometimes worse - than the general
English population before 1800. Inventing an elasticity to flatten the
century would have hidden this finding instead of exposing it.

The double-count hypothesis was also tested and bounded rather than assumed:
Fogel's review of the Wrigley and Schofield series puts all crisis mortality
under 5% of pre-1800 English deaths and famine under 10% of that, so the most
the baseline could double-count ordinary harvest mortality is about 0.5% of
it - over an order of magnitude too small to explain a drag of 0.0788. Real
in direction, negligible in size, and correctly left alone.
