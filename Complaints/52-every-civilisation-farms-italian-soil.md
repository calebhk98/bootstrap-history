# Norse Scandinavia grows wheat on Italian loam

Found by asking why five civilisations with wildly different geography gave
the SAME answer. With harvest weather variance removed, the unshocked
century lands on:

    rome_100ad         108.987712673%
    han_china_100ad    108.987712673%
    england_1300       108.987712673%
    mexica_1500        108.987712673%
    norse_900ad        108.987712673%

Identical to nine decimal places. Not close - the same number. Five
territories differing by a factor of ten in land area, a factor of thirteen
in cultivable land and a factor of two in soil fertility produce a
bit-identical demographic trajectory the moment weather stops differing.

That is not a coincidence to be admired. It means nothing about a
civilisation's land reaches the model that decides whether its people eat.

## Where it goes wrong

`Sim.__init__` (`sim/engine/core.py`) builds the farm as

    self.farm_land = agriculture.farmland_for_population(
        self._adult_equivalent_population(self.population))

and `farmland_for_population` (`sim/world/agriculture.py`) returns
`Land(hectares)` - with `quality` left at its default of 1.0. The function's
own docstring is admirably clear that it does this on purpose and that the
caller is expected to do otherwise:

> `land.quality` is left at the default (1.0, decent land) here regardless
> of `soil` ... A caller modelling worse land should build the `Land`
> directly with `quality=soil.quality_multiplier` instead of relying on this
> function to do it implicitly.

No caller does. `data/world/geography.json` carries a
`fertility_quality_multiplier` for every region, each with a sourced note,
and the engine reads none of them for food:

    region              fertility   arable km2
    china                    1.30    1,247,610
    italia                   1.00       69,230
    americas_carib           0.95      378,000
    gaul_germania            0.90      294,300
    britannia                0.85       57,500
    scandinavia              0.65       97,600

Every civilisation is farming Italia.

The same holds for AREA. Region areas and arable fractions do reach
`_compute_farm_region_weights`, but only as weights - proportions that sum
to one - so a civilisation's absolute endowment cancels out. A civilisation
holding thirteen times another's cultivable land is not modelled as holding
any more of it.

## The size of the effect

Rome's own century, varying nothing but `farm_land.quality`:

    quality   real region        century   mean nutrition ratio
       0.65   scandinavia           0.3%                 0.5938
       0.85   britannia            12.5%                 0.8717
       1.00   italia (all five)   107.6%                 1.0042
       1.30   china               147.5%                 1.0830

Soil quality is the most powerful single lever in the demographic model, and
it is currently pinned to one value for everybody. A ±35% change in one
multiplier moves a century between extinction and a 47% expansion.

## The fix is NOT to pass the multiplier through

That is the trap, and the numbers above are exactly why. Setting Norse's
quality to its real 0.65 while leaving everything else alone drives it to
0.3% of its starting population - a collapse no historical Scandinavia
suffered, and a worse answer than the one we have.

The reason is that the initial condition would become self-contradictory.
`farmland_for_population` sizes the farm so that the implied workforce feeds
the starting population *at quality 1.0*; applying 0.65 afterwards keeps the
farm the same size and removes a third of the food. Nothing in that sequence
resembles a society. A real population on poor ground farms MORE GROUND per
head - which is why Scandinavian population density was low, as an OUTCOME
of thin soil and a short season rather than as an input.

And the room to do exactly that is already in the data. Each civilisation
currently crops a small fraction of the cultivable land its own regions
hold:

    civilisation       farm km2   arable km2   share   true weighted fertility
    rome_100ad          234,616    1,205,170   19.5%                      1.03
    han_china_100ad     209,350    1,247,610   16.8%                      1.30
    mexica_1500          18,047      378,000    4.8%                      0.95
    england_1300         16,243      351,800    4.6%                      0.89
    norse_900ad           5,414       97,600    5.5%                      0.65

Norse crops 5.5% of its arable land. Compensating for a fertility of 0.65
takes 1/0.65 = 1.54 times the hectares, which it has eighteen times over.

So the fix is that the starting endowment must be SELF-CONSISTENT: size the
initial farm from the population AND the soil it actually sits on, so a
civilisation begins able to feed itself on its own ground, and let the
arable land its regions really hold be the ceiling that binds when it cannot.
A civilisation whose population cannot be fed from its own arable land at
its own fertility is then genuinely land-constrained, and that is a result
the model computed rather than a number anybody chose.

That ceiling is the extensive margin `sim/world/agriculture.py`'s own module
docstring already names as missing mechanism (b), and it is the same
quantity `sim/world/land.py` computes rent from - so this is one mechanism
serving two domains that currently disagree about whether land is scarce.

## Why this was invisible

`farmland_for_population`'s docstring defends sizing the farm from
population as an initial condition, and that defence is sound - CLAUDE.md
SS3.1 allows initial conditions, and seeding a civilisation neither land-rich
nor land-starved avoids scripting a feast or a famine. The quality decision
rode along inside that defence without being argued separately, and it is a
different decision: area is an initial condition a modeller may reasonably
choose, and soil fertility is a physical property of a place that the data
file already records.

A note for whoever picks this up: the bit-identical result above is the
cheapest possible detector for this class of bug, and it cost one probe.
When several configurations that ought to differ produce the same number to
nine decimal places, the shared mechanism is not reading its inputs. That is
worth running deliberately rather than stumbling into.
