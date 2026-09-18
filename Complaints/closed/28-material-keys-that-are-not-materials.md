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

## Resolved: the three fixed, `argon_or_h2_m3` left as recorded above

`monochromatic_light_kg`, `steam_kg` and `slave_skilled` are gone from every
node's `mat` list, and their `conf: D` entries in `data/production/` are
deleted (per this file's own instruction to delete rather than refine them).
`argon_or_h2_m3` is untouched, as the section above says to leave it until
something actually needs the argon/hydrogen distinction.

**`prc_optical_flat`** (`data/branches/20_precision.json`) - `mat` no longer
carries `monochromatic_light`. Nothing needed inventing: the node's own `pre`
already named `cap_measure_light` (interferometric length by wavelengths of
light) and `arc_light_lamp` (the light source it runs), so whoever wrote
those had already done the capability half of this fix and simply left the
stale material key behind. The removed quantity was priced at 0 denarii, so
this is a pure schema correction with no cost effect at all.

**`chm_activated_carbon`** (`data/branches/18_chemicals.json`) - `mat` no
longer carries `steam_kg`; `coal_kg` rises from 200 to 245 to cover it,
derived the way `data/production/`'s own fuel-estimate entries are: sensible
heat plus the ~2.26 MJ/kg latent heat of vaporisation for the 100 kg of
steam, at a ~20% furnace efficiency (the same figure `lime_kg`'s kiln entry
in `data/production/30_fuel_stone.json` uses) and coal's ~29 MJ/kg calorific
value, giving about 45 kg of extra coal. The node also carries a `req_any`
"steam_supply" gate (any of `cap_power_steam`, `steam_atmospheric`,
`steam_high_pressure`, `steam_watt`) that turned out to exist ONLY in
`data/tech_tree.json`, not in the branch file - an earlier, undocumented
partial attempt at this same fix, addressing "can you raise steam at all"
while leaving the double-counted fuel key in place. Left it as the answer to
that question; `coal_kg` answers the separate question of how much fuel this
one batch burns.

**`freedman_staff`** - `mat` no longer carries `slave_skilled`; the same
valuation (8 people at the 1000 denarii/head `data/prices.json` already
carried) now sits in `cap` (2000 to 10000) instead, since acquiring people is
a one-time capital outlay, not a material - exactly how `buy_slaves()` in
`sim/engine/labour.py` already treats the identical transaction (a straight
`household.capital` deduction, no `lab` hours). This node has NO branch
source at all - it is a `"_src": "core"` node, one of the ones that predate
`data/branches/` - so the edit went into `data/tech_tree.json` directly,
which for this node is the only place the definition lives. The link the
"what is missing" line above asked for is still missing: building this node
still does not touch `self.household.slaves` or `self.household.freedmen`,
only `hired_cap()`. It remains a parallel, unlinked way of modelling the same
thing `buy_slaves()`/`manumit()` do with real market depth and a training
lag. Wiring the two together is an engine change, not a data fix, and is not
done here.

**A mechanical finding worth recording alongside the fix itself:**
`sim/treetool.py`'s `cmd_merge` seeds its working node table from the
CURRENT `data/tech_tree.json`, and a branch file's node whose id is already
in that table is skipped ("duplicate id, keeping the first") rather than
overwriting it. Editing only the branch files for `chm_activated_carbon` and
`prc_optical_flat` and re-running `merge` left the old `mat` untouched in the
merged output - the branch edits were silently discarded. So "edit the
branch, then merge" only ever applies to a brand-new node id; changing an
existing one requires editing `data/tech_tree.json` itself (keeping the
branch file in sync as documentation of record). All three nodes were edited
in both places here, and a second `merge` run afterwards is a no-op (verified
node-by-node), confirming the fix is stable under the tool.

**Fingerprint:** `perf_fingerprint.py check` against a baseline recorded
before this change reports 8 of 9 scenarios diverging - every Rome, Han,
Norse and England scenario, and the 400-year Rome run - each at its own year
(20 to 110), and only `mexica_1500/seed1` unchanged (Mexica's own tech order
apparently never reaches any of these three nodes within 200 years). Three
node costs changing was always going to move affordability broadly across
civilisations that reach `freedman_staff` and `chm_activated_carbon` early;
what matters is that no scenario diverges at year 0 or collapses into
chaos - each is a specific, dated point consistent with one of these three
projects becoming affordable a little earlier or later than before.
`sim/simulator.py validate` and `sim/test_regressions.py` (1623 checks) both
pass unchanged; no regression test had baked in any of the three old costs.
