# We priced land and then never charged anybody for it

Found while deciding whether the engine's solved-price switch could finally
be turned on. It is the reason the answer is no, and it is larger than every
other reason combined.

## The finding

    production recipes consuming iugerum_land: NONE

Not one recipe in `data/production/` lists land as an input. And the rent
term in `recipe_cost_and_allocation` only attaches to a recipe whose own
OUTPUT key is a rent-bearing material - the six ores and `iugerum_land`
itself. So rent reaches a crop through neither route.

    wheat_kg       inputs={}   extracted_from="arable land"
    wool_kg        inputs={}   extracted_from="pasture"
    olive_oil_kg   inputs={}   extracted_from="arable land"
    timber_m3      inputs={}   extracted_from="forest"
    linen_kg       inputs={}   extracted_from="arable land"

Every one of them SAYS it comes from land, in prose, in `extracted_from`, and
consumes no land in structure. `wheat_kg` is 150 labourer-hours divided by
577.5 kg of output and nothing else - its price is mathematically guaranteed
to be labour cost alone, whatever an iugerum is worth.

## Why this matters more than it sounds

Two rounds of work built a Ricardian land market: the extensive margin over
regions of differing quality, then the intensive margin for diminishing
returns on the same ground, with per-civilisation territory, ending at
55.779 hours per iugerum for Rome and nonzero for all five civilisations.

None of it reaches a price anybody pays. Land scarcity - the mechanism that
drives rent, Malthusian pressure and urbanisation, and the reason
`Complaints/43` argued land mattered at all - is computed and then discarded.

The number is not unused entirely: three tech-tree nodes consume
`iugerum_land` directly (`charcoal_industrial`, `endowment_land`,
`exp_transplant_botany`), so a founder buying land pays the right price. But
no LOAF OF BREAD is dearer because land is scarce, which is the entire point.

## What it would take

A structured way for a recipe to say how much land a batch needs, for how
long - `data/production/_SCHEMA.md` has no field for it. `extracted_from` is
prose and cannot carry a quantity. The natural shape is the one `capital`
already uses for a furnace: land is a thing a process occupies rather than
consumes, so a crop should hold N iugera for a season the way a smelter
occupies a hearth.

Note what that also fixes: `sim/world/land.py` currently works out how much
land a civilisation needs by dividing population by a calorie figure, which
is a parallel calculation to the one `data/production/` would do if crops
declared their land. Those two can drift. One of them should be derived from
the other.

## Also found, and already fixed

`sim/engine/prices.py`'s `solved_prices` - the function the engine's switch
actually calls - was solving WITHOUT the rent tables, because it never passed
`rent_hours_per_kg_by_material`, which defaults to the old RENT_IS_ZERO
behaviour. So flipping the switch would have silently thrown away every rent
number two rounds of work produced. A second, independent copy of the bug
`Complaints/32` fixed, one file away, never updated to match.

It also cached on gate-nodes-held alone while land rent is per-civilisation,
so two civilisations sharing a technology set would have shared one another's
land prices. Both fixed, and the engine path now reproduces the command-line
figures to five significant figures for all five civilisations.

## And a third: four of the six "fixed" ores still price at zero rent

`iron_ore_kg`, `copper_ore_kg`, `silver_ore_kg` and `cinnabar_kg` compute
exactly zero rent for Rome. Only cassiterite and galena are positive this
era. Of Rome's 103 solved materials, 60 are extracted with rent still at
exactly zero, median disagreement against book 40x. So `Complaints/32`'s
finding is narrower than it looked: rent exists as a mechanism, and for most
extracted materials it still evaluates to nothing.

## The switch: no, and the useful version of no

Not as one global boolean, which was always the wrong shape. Per material:

  - YES now for roughly 40 manufactured materials per civilisation - real
    recipes, modest disagreement, median 3.9x against a book that is 91.8%
    the author's own estimate.
  - YES for `cassiterite_kg` and `galena_kg`, the two ores whose rent is
    real.
  - NO for the ~60 extracted materials still at zero rent.
  - NO, structurally, for everything GROWN, until land has a channel into a
    crop's price. That is this complaint.

"prices.json slowly deleted" wants a per-material graduation list, not a
switch, and the three-state provenance report already supplies the data to
maintain one.
