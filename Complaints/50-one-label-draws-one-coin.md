# Han China farms an empire and flips one coin for all of it

Complaints/47 fixed the wrong half of a two-part bug and the fix made the
remaining half measurable. Weather is now drawn per home region and pooled
by each region's share of the cultivable land, which took an unshocked
rome_100ad century from 85.5% of its starting population to 107.6%.

Then the same measurement across all five civilisations:

    civilisation       home regions   unshocked century
    rome_100ad                    7              107.6%
    england_1300                  2              105.3%
    han_china_100ad               1               83.8%
    mexica_1500                   1               77.9%
    norse_900ad                   1               71.8%

Region count predicts the outcome exactly. Nothing else does, and the
obvious alternative explanation is ruled out by the data file itself:

    civilisation       total land km2   arable km2   regions
    rome_100ad              9,517,500    1,205,170         7
    han_china_100ad         9,597,000    1,247,610         1

Han China is the same size as the Roman Empire to within 1%, holds MORE
cultivable land than all seven Roman regions combined, and its harvest
carries a standard deviation sqrt(7) = 2.65 times larger - because
`data/world/geography.json` files China under one name and Gaul, Britannia,
Hispania, North Africa, Greece and the Levant under six.

This is `Complaints/46` - a region is not a unit of area - appearing for the
third time. It was found in land rent, then in `forest_land_ceiling` (where
the same two territories differed sevenfold on the same ground), and this is
the weather channel. The lesson has now cost three separate fixes: any
quantity that scales with how big a territory IS must read an area, and
`len(home_regions)` is never that.

## What is actually wrong

`Sim._pooled_farm_weather_multiplier` (`sim/engine/core.py`) draws one
independent weather sample per region record. Two assumptions are buried in
that, and both are wrong in the same direction for different reasons:

1. **A region record is one weather system.** It is not. Nothing about a
   harvest cares how a data file chunks a continent. North Africa at
   5,750,000 km2 is not one growing season, and neither is China.
2. **Two region records are independent draws.** They are not. Gaul and
   Hispania share weather systems; Britannia and Mesopotamia do not. The
   existing code labels this approximation honestly in its own docstring
   (CLAUDE.md SS3.4) and states the direction of the error - optimistic for a
   compact empire - which is why this complaint can be written from the
   code's own admission rather than from a re-derivation.

The two errors partly cancel for Rome, which is why Rome looks right. They
do not cancel for anyone else, and a mechanism that is only correct for the
civilisation it was calibrated against is the thing CLAUDE.md SS3.1 exists to
forbid.

## The shape of the fix

One mechanism should replace both assumptions, because both are the same
physical question: over what distance does growing-season weather stop
agreeing with itself?

Territory is divided into cells of a stated area, independent of how many
labels the data file uses, and cells draw from a field whose correlation
decays with the distance between them. `geography.json` already carries the
lat/lon centroids this needs, and `land_tiles` already carries 1,139
equal-area cells of 150,000 km2 built for exactly this class of problem.
Rome's effective number of independent draws should then fall out of its
geography - large, and spread from Britain to Mesopotamia - rather than out
of its row count, and China's should fall out of being an empire rather than
out of being one word.

The decorrelation length is a physical constant and therefore an allowed
input (CLAUDE.md SS3.1). It is also the one number this fix turns on, so it
gets a sourced value, a confidence marker, and a sensitivity run across its
plausible range rather than a single figure presented as settled.

## It is variance, and only variance - measured, not argued

This section originally warned that Norse Scandinavia might be failing for
reasons variance has nothing to do with, and said to measure it rather than
assume. Measured, the warning was wrong, and the real answer is much
stronger than the complaint above claims.

First, the three failing civilisations are not underfed. Mean nutrition
ratio over the unshocked century, against the population that ends it:

    civilisation       mean nutrition   worst year   pstdev   century
    rome_100ad                 1.0042       0.8909   0.0310    107.6%
    england_1300               1.0241       0.6236   0.0911    105.3%
    han_china_100ad            1.0222       0.3511   0.1537     83.8%
    mexica_1500                1.0139       0.5314   0.1357     77.9%
    norse_900ad                0.9908       0.4603   0.0947     71.8%

Han China eats BETTER than Rome on average - 1.0222 against 1.0042 - and
loses a quarter of its population anyway. What separates them is the third
and fourth columns: Rome's worst year in a century is 0.8909 of subsistence
and Han China's is 0.3511.

Second, and decisively: with weather variance removed entirely (
`draw_weather_multiplier` patched to return 1.0, in BOTH module objects -
`world.agriculture` and `sim.world.agriculture` are the same file loaded
under two roots, which is a trap CLAUDE.md SS6 records someone already
falling into), ALL FIVE CIVILISATIONS LAND AT 109.0%:

    civilisation       no variance   actual   lost to variance
    rome_100ad              109.0%   107.6%                1.4
    england_1300            109.0%   105.3%                3.7
    han_china_100ad         109.0%    83.8%               25.2
    mexica_1500             109.0%    77.9%               31.1
    norse_900ad             109.0%    71.8%               37.2

Identical, to the precision printed. That is the expected result rather than
a suspicious one: with steady weather every civilisation's nutrition ratio
sits at or above subsistence, the mortality and fertility responses saturate
at their well-fed values, and what is left is the demographic model's own
unconstrained rate under an ancient disease burden - the same for everyone,
because nothing civilisation-specific is left to differ.

So every one of these societies has the food to grow. The entire gap between
109.0% and where each actually lands is harvest variance, and the variance
each one suffers is set by how many rows its territory occupies in a JSON
file.

This is Jensen's inequality on a one-sided response curve, the same
mechanism `Complaints/45` and the demography work already record: a convex
mortality response against symmetric weather means eating 18% extra in a
good year saves far fewer lives than eating 65% less in a bad year costs.
Averaging N independent draws divides the spread by about sqrt(N), which is
why the fix is worth 25 to 37 points to the three civilisations that
currently get N = 1, and only 1.4 to Rome, which already has seven.
