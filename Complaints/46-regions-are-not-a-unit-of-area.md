# A region is not a unit of area, and land rent is reading the filing system

Raised by the stakeholder, from a simple question: how can China with one
region have more land than Rome with seven?

Because the regions were sized by what they are CALLED, not by how much
ground they cover. Measured, from `data/world/geography.json`:

    americas_north     19,800,000 km2
    americas_south     17,840,000
    siberia_urals      13,000,000
    china               9,597,000
    north_africa        5,750,000
    ...
    hispania              596,000
    italia                301,000
    britannia             230,000

Largest to smallest is 86x. So "Rome holds seven regions and Han China holds
one" says nothing whatever about how much land either has.

## The two empires are the same size, and only one has rent

    rome_100ad   7 regions   9,517,500 km2 raw   1,205,170 km2 arable
    han_china    1 region    9,597,000 km2 raw   1,247,610 km2 arable

Near-identical on both measures, and both feeding roughly 60 million people.
Yet `iugerum_land` prices at 9.141 hours for Rome and 0.0 for Han China.

The entire difference is that Rome's ground is filed under seven labels of
differing stated quality and China's is filed under one. A Ricardian margin
needs something worse to compare against, and China has nothing worse of its
own because nobody drew a line through it.

That is the map's filing system leaking into the economics. It is not a
finding about Roman or Chinese agriculture.

## Two fixes, and they are different sizes

**The intensive margin, which is cheap.** Rent has two sources and
`sim/world/land.py` has one. The extensive margin is better land against
worse. The intensive margin is diminishing returns to more labour on the SAME
ground - the second and third ploughing of one field yielding less than the
first. With it, crowding a single region raises its rent whether or not a
worse region exists anywhere, so China stops being free without anyone
touching the map. `sim/world/deposits.py` already has both margins; its
intensive one is the ore grade falling as a deposit is worked out. This is
recorded in `Complaints/43` too and is the smaller job by far.

**Re-tiling the world, which is not cheap.** The stakeholder's own model is
a region as a fixed quantity of land, roughly 150,000 km2. That is the better
design and it fixes more than rent:

  - rent stops depending on where somebody chose to draw a border;
  - conquest becomes granular - three tiles of North Africa rather than one
    5.75-million-km2 lump that is 96% Sahara and rated 1.35 fertility on the
    strength of the Nile;
  - quality genuinely varies within what is today one block.

The world's land is roughly 149 million km2, so about a thousand tiles. That
is nothing to compute: the price solve is 0.37 seconds and runs a few dozen
times a game, and tiles reach it only through per-civilisation sums.

## The real cost of re-tiling, and why it is not obviously worth doing yet

Each of the 21 regions today carries a hand-written `land.source` explaining
where its area, arable fraction and fertility came from. A thousand tiles
cannot each get that treatment, so they would have to be generated from a
rule - a climate band, a terrain class, a latitude. Done well that is fine
and arguably better, because one stated rule applied a thousand times is more
defensible than a thousand separate judgements. Done badly it replaces 21
defensible numbers with 1,000 invented ones, which is precisely the
hardcoded-outcome failure CLAUDE.md section 3.1 exists to prevent.

So the rule has to be agreed BEFORE anybody writes a thousand numbers, and
the rule is the actual deliverable. The tiles are just its output.

## Recommended order

1. Intensive margin on land. Small, fixes China, makes the map's granularity
   matter much less, and is worth doing whether or not re-tiling ever
   happens.
2. Re-tiling as its own deliberate pass, starting from an agreed generating
   rule rather than from a thousand hand-written entries.

Note that the current regions are ALSO used for freight distance in
`sim/engine/economy.py`, via their centroids, and that use is unharmed by the
size disparity - a centroid is a point and 22 of them give perfectly
reasonable great-circle bands. So re-tiling is a land-rent problem, not a
geography-wide one, and the freight work does not need to wait for it.
