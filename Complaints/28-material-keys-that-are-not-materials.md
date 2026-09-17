# Three keys in the tree's material lists are not materials

**Type:** Data defect / schema
**Priority:** Low, but it will not fix itself

Found while authoring `data/production/`. Giving every material a producing
process with a yield turned out to be a good way of finding the entries that
cannot have one, because a recipe for a thing that has no mass is impossible
to write honestly and three agents independently refused to write one.

## `monochromatic_light_kg`

Consumed by one node, in kilograms.

Light does not weigh anything. This is an instrument capability - a
monochromator, a sodium lamp, a spectroscope - written into a node's `mat`
list as though it were a purchased consumable. What the node actually needs
is a piece of equipment it can use repeatedly, not a stock it draws down.

The entry in `data/production/50_chemicals.json` says so in its own
`yield_basis` rather than inventing a recipe, and is marked conf C. The fix
is to remove the key from that node's `mat` and express the requirement as
the capability it is: this is what `cap_*` rungs exist for, and a
measurement rung is exactly the shape of the thing.

## `steam_kg`

Consumed by one node, in kilograms.

Steam is water in a state, produced on the spot by burning something under a
boiler. It is not procured, stored or traded, and pricing a kilogram of it as
a material double-counts the fuel that the same node already pays for.

What the node means is that it needs a boiler and the fuel to run one.

## `slave_skilled`

Consumed by one node.

This is a person. `data/production/40_organics.json` has an entry that
refuses to give it a recipe and says plainly that it belongs in a
labour-supply model - wages, coercion, manumission, manumission rates - and
not in a materials file. Its conf C marks an entry that should not exist in
this form rather than a number that needs refining.

The engine already models slaves and freedmen as household state, so the
machinery to do this properly is closer than it looks. What is missing is the
link between that state and a node saying it needs one.

## A softer case, recorded here rather than in its own complaint

`argon_or_h2_m3` conflates two chemically unrelated gases under one key.
Argon is inert; hydrogen is reducing. A node that needs an inert atmosphere
because its workpiece would otherwise burn is not satisfied by a reducing
one, and this key cannot express the difference. It is currently priced by
the cheaper hydrogen route, which is the right call for now and the wrong one
the first time a node genuinely needs argon.

Split it when something needs the distinction, not before.

## Why this is worth a complaint rather than a silent fix

Each of these is one node. The cost of leaving them is small, and the cost of
fixing them wrongly is not: removing a key from a node's `mat` changes that
node's cost, which changes what a run can afford, which the fingerprint will
correctly flag as a behaviour change. That is a real edit to the simulation
and deserves its own commit with its own justification, not a drive-by while
authoring data.

The production entries for all four are written to be honest in the meantime:
they say what the thing actually is, and their confidence marks say the entry
is wrong in kind rather than merely uncertain in degree.
