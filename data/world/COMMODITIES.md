# Commodities: a framework, not a catalogue

This is a design document for treating bulk goods (iron, wool, coffee, copper,
gold...) as first-class things the simulator can be asked about: how much you
have, how much the country has, what makes it, what eats it, who you can trade
it for, and what it is worth this year versus last year. It is deliberately
NOT a populated commodity list. Nine commodities are defined in
`commodities.json` to exercise the mechanism. Read this alongside
`data/world/resources.json` (annual output ceilings), `data/world/
geography.json` (where things are and what reaching them costs) and
`sim/engine/economy.py` (the live material-throttle system this framework was
written next to, and is now partly wired into -- see section 0).

The code lives in `sim/engine/commodities.py`. It is no longer a wholly
standalone module that nothing imports: `economy.py.wire_chain_report()`
calls its `propagate_demand()` directly. See section 0 for exactly what was
taken, what was deliberately left as a separate, already-working system, and
why; "core.py does not import this module" is still true (the per-civ `Sim`
gained a new METHOD, not a new component living inside it).

## 0. What was decided, and why

The question this pass had to answer honestly: is `commodities.py`'s
machinery wired in behind the goods model that now exists in `economy.py`
(`GOODS_CATEGORIES`/`goods_market_factor()`, a price-falls-as-supply-grows
curve for textiles/processing/printing/photography revenue), or folded into
the live path, with the standalone module retired? Neither, exactly, once
the two systems were actually compared:

- **`goods_market_factor()` already answers the brief's headline
  example** (automated looms make cloth cheaper) for the goods it covers,
  with its own calibration (diffusion half-lives, population/reach-adjusted
  saturation) already tested against 621 checks. It solves a DIFFERENT
  question than `commodities.py` does, though: "how has THIS concern's
  revenue moved since it opened," not "how much copper does the country
  have, and what happens to a manufactured good when the raw material
  behind it runs short." Swapping one in for the other was never the right
  frame; they answer different questions and both are worth keeping.
- **`commodities.py`'s price/national-output/monopoly/trade-partner
  machinery substantially DUPLICATES what `economy.py` already runs live**
  (`resource_throttle()`, `MARKET_SHARE`, `material_price_factor()`,
  `mineral_scale()`/`material_reach()` in `geography.py`) for the materials
  both files track (iron, copper, coal, gold). `commodities.json`'s own
  numbers were already SOURCED from `economy.py` for these four
  specifically (copper's 15,000 t/yr, coal's 0.50 market share, etc. -- see
  section 2's own note), precisely to avoid the drift section 10.1 (below)
  warns a careless merge would cause. Swapping `economy.py`'s own, tested,
  621-check-backed system for a second implementation of the same idea,
  however faithfully sourced, was judged not worth the risk for no gain:
  the numbers would not actually change, only which code computes them.
- **The one piece of `commodities.py` with no analogue anywhere in the
  existing code is `propagate_demand()`** (section 7): a recipe-chain
  demand walk that names WHICH link broke, where `resource_throttle()`
  checks a flat list of material keys, each against its own supply,
  independently. This is the genuinely new capability, and it was real,
  not hypothetical: `copper_wire_kg` and `wire_drawn_kg` are drawn by 36
  real nodes (the whole `el2_` electrical branch, `gp_magnet_wire_
  enamelled`, `hom_piano`, `en_rotary_converter`...) and were not in
  `MATERIAL_CHECKS` at all before this pass -- copper demand for DRAWN WIRE
  was invisible to the throttle entirely, the exact failure mode this
  section describes, sitting live in the tree rather than hypothetical.

**What was taken**: `economy.py.wire_chain_report()` now calls
`CommodityLedger.propagate_demand()` directly, through a new
`supply_override` parameter on `CommodityLedger` that lets a live Sim hand
over ITS OWN reachable-copper figure (`_own_material_supply("mine:copper")
+ _material_market_tonnes("copper")`) instead of `commodities.json`'s
separate national estimate. Rome and the Norse get genuinely different
numbers out of the same call, because they do not share one coastline --
see `demo_commodities.py` section 7 for both printed side by side.
`MATERIAL_CHECKS` also gained `copper_wire_kg`, `wire_drawn_kg` (both ->
copper) and `gold_kg` (a tracked commodity `open_mine("gold", ...)` already
supported, with no material key ever throttling demand for it), and
`resource_throttle()`/`material_price_factor()` were both fixed to group
demand by shared supply before comparing to it, rather than checking each
material key against the WHOLE of its supply independently -- a latent bug
`iron_bar_kg`/`iron_ore_kg` already had, that adding three more copper keys
would have made worse rather than better if left unfixed. See
`economy.py`'s `_demand_by_supply_tag()` for the one mechanism shared by
both.

**What was deliberately NOT taken (as of the pass this section describes)**:
`commodities.py`'s own `price()`, `country_output()`, `market_available()`,
`monopoly_price()` and `trade_partners()` remained exactly what they were --
a standalone, self-consistent demonstration of the mechanism on nine
commodities, not the thing `resource_throttle()`/`material_price_factor()`
computed for the live game. **This changed in the pass section 0.1 below
describes** -- `country_output()` is now a real input to the live price for
four of these nine (cloth, wool, cotton, copper_wire), and the underlying
IDEA (a general, elasticity-shaped supply/demand response, not a hand-listed
one) now covers every material key the tech tree uses, not nine.

## 0.1 Generalised beyond nine: rome/data/review/COMMODITY_DYNAMISM.md

A later audit, run directly against a live `Sim` rather than by reading the
code, measured the gap section 0 above left open precisely: **149 of the
162 distinct material keys the tech tree actually uses (about 92%) had a
price read once from `prices.json` at load time and never revisited for
scarcity, surplus, population or time**, because `MATERIAL_CHECKS`/
`MARKET_SHARE` in `economy.py` only ever named 13 keys (9 commodities) by
hand. Its worked failure was aluminium: "no mine, no supply lever of any
kind... nothing in `economy.py` even contains the string 'aluminium.'
Producing an enormous amount of it via electrolysis tech changes nothing."
The audit's own conclusion was that the gap was not a missing theory --
`CommodityLedger.price()` already was a correct, general elasticity
function -- but missing WIRING and missing per-material data.

**What changed.** Rather than hand-authoring ~150 more `commodities.json`
entries (the audit's own sketch names this as one option but not the only
one), `economy.py` now derives a commodity for ANY material key generically,
in three tiers, cheapest-and-most-specific first:

1. The 9 commodities this file already curates (`MATERIAL_CHECKS`/
   `MARKET_SHARE`, unchanged) -- iron, copper, coal, gold, lead, tin,
   silver, saltpetre, charcoal.
2. A `commodities.json` commodity this file curates but `economy.py` never
   priced against before (cloth, wool, cotton, copper_wire): now read
   through `CommodityLedger.country_output()` for real, so a built power
   loom genuinely raising cloth's national output (`produced_by`'s own
   multiplier) is a real input to a live price, not only to the standalone
   `demo_commodities.py` demonstration section 0 above described.
3. Everything else (silk, glass, aluminium, the acids and dyes and
   alloys of the industrial and chemical ages) -- a generic fallback
   derived from the one number every material already has, its own book
   price in `prices.json`, fitted against the curated seven's own
   capex/opex and national-output figures (see `economy.py`'s own
   `GENERIC_OUTPUT_ANCHOR_T_PER_YR`/`GENERIC_MINE_CAPEX_MULTIPLE` comments
   for the fit and its error against a held-out point, gold).

`open_mine()`/`mine_quote()`/`close_mine()` are generalised the same way:
sinking standing production capacity is no longer limited to the seven
hand-named metals, so "make a mountain of it" is a real, general lever for
whatever a recipe needs, not a rule written per commodity. `resource_
throttle()`, `material_price_factor()` and `material_market_factor()` all
consume this generically now (`_material_tag()`), rather than skipping any
material key outside the original 13.

The goods side (`GOODS_CATEGORIES`/`goods_market_factor()`) also changed:
concerns in the same category now share one total-supply figure instead of
each pricing off its own private per-node age clock (the audit's other
headline finding: two identical looms, same age, priced bit-for-bit
identically, "a time curve wearing a market's clothes"), and the category
list grew to cover the tree's real consumer/entertainment nodes
(fermentation, leisure, sound, media, commerce, luxury/spectacle/law,
personal) with an income effect (`income_factor()`/`essential_price_ratio()`)
coupling a cheaper, saturated essential market to more spending on
discretionary goods. See `economy.py`'s own comments on `GOODS_CATEGORIES`,
`_goods_category_state()` and `income_factor()` for the full reasoning; this
section exists so a reader of this design doc is not left believing the
"nine commodities, one wired capability" picture section 0 painted is still
the whole story.

## 1. What a commodity is, here

A commodity is a bulk, fungible good that:

1. is **produced** by something (geology, land, or another commodity plus a
   process),
2. is **consumed** by something (a technology's `mat` dict, ultimately, or a
   person's stomach or back),
3. has a **national quantity** (the country produces X tonnes a year of it,
   whether or not you personally touch any of it), and a **personal
   quantity** (what you, specifically, hold or can lay hands on), and
4. has a **price** that moves against how hard demand leans on supply, in
   BOTH directions: scarcity should raise it, and a glut should lower it.

That last point is the one thing the existing `economy.py` genuinely lacks
(see 4.4 below), and it is the specific mechanism the balloon example in the
brief needs: automated looms do not just make more cloth, they must make
cloth **cheaper**, and that price has to be visible to whatever buys cloth
next.

A commodity is not a technology. `tex_power_loom` is a technology; "cloth" is
a commodity it produces more of, more cheaply, than `tex_horizontal_loom`
does. Keeping these separate is why one commodity can have several producing
technologies (a loom lineage) and several consuming technologies (a balloon
envelope, a sailcloth order, a toga), all changing independently.

## 2. Fields, and what each one is for

One entry in `commodities.json`'s `commodities` object, with every field
explained:

```jsonc
"copper": {
  "name": "Copper",
  "unit": "kg",
  "category": "ore_metal",                 // ore_metal | agricultural | manufactured | luxury_import
  "material_keys": ["copper_kg", "copper_ore_kg"],   // prices.json keys this commodity subsumes
  "base_price_denarii_per_kg": 4.0,
  "price_conf": "C",
  "price_source": "data/prices.json:copper_kg",
  "national_output_t_per_yr": 15000,
  "output_conf": "C",
  "output_source": "data/world/resources.json:empire_output_100ad.copper",
  "market_share": 0.03,                    // fraction of national output an ordinary buyer can actually purchase, see economy.py MARKET_SHARE
  "elasticity": 1.0,                       // how hard price reacts to demand/supply imbalance
  "price_floor_factor": 0.35,              // price never falls below this fraction of base, however large the glut
  "price_ceiling_factor": 8.0,             // ...or rises above this multiple, however large the shortage
  "regions": ["hispania", "britannia", "gaul_germania", "greece_anatolia", "italia"],
  "trade_only": false,                     // true if there is no domestic production route at all
  "monopoly_possible": false,
  "recipe": null,                          // {commodity_id: units of input per unit of output}, for manufactured goods
  "produced_by": [
    {"node": "mine:copper", "kind": "mine", "note": "generic capacity via Sim.open_mine('copper', ...)"}
  ],
  "notes": "..."
}
```

- **`material_keys`** is the bridge to the existing tech tree: every node's
  `mat` dict is keyed by strings like `copper_kg`, and this list says which
  of those keys this commodity answers for. This is deliberately the same
  idea as `economy.py`'s `MATERIAL_CHECKS`, generalised: one commodity can
  answer for several material keys (`copper_wire_kg` AND `wire_drawn_kg` are
  both "copper wire"), and a material key answers for at most one commodity.
- **`national_output_t_per_yr`** is a FLOW (tonnes per year), not a stock.
  So is everything else about production and consumption in this framework.
  See section 8 for why a flow model and not a stockpile model.
- **`market_share`** and the mine-cost tables are read from `economy.py`
  where they already exist (copper, iron, coal, lead, tin, silver, gold),
  rather than re-guessed, specifically so the two do not drift apart. Where
  a commodity has no existing entry (cloth, wool, coffee, cotton, copper
  wire) a number is estimated here and marked `[C]`, same as the rest of
  this project's convention.
- **`produced_by`** is a list of technologies (or the sentinel `mine:X`,
  meaning "however much of X you personally choose to sink capital into
  mining, via the existing `open_mine` mechanism") that either establish a
  commodity's production (`kind: "mine"` or `"farm"`) or multiply an
  existing production route's output (`kind: "multiplier"`, with an
  `output_multiplier`). Multiple `kind: "manufacture"` entries on the same
  commodity are read as alternatives, and the model picks whichever built
  one has the highest multiplier -- exactly `economy.py`'s `chosen_fuel()`
  pattern, generalised.
- **`recipe`** is what turns this into a chain. `copper_wire`'s recipe is
  `{"copper": 1.05}`: one kilogram of drawn wire needs 1.05 kg of copper
  (a 5% drawing loss, `[C]` estimate). A commodity with a recipe is
  manufactured FROM other commodities, and its available supply is capped
  by whichever upstream commodity runs short -- this is the mechanism
  section 6 is about.
- **`price_floor_factor` / `price_ceiling_factor`** exist because an
  unbounded elasticity curve is not credible at either extreme: a total
  glut does not make copper worthless (there is always a floor use and a
  floor cost of digging it), and a total shortage does not make it
  infinitely expensive (people substitute, or simply stop buying, before
  that happens). These bound the curve in section 4.

## 3. Attaching production and consumption to technologies

**Consumption already exists.** Every one of the tech tree's 2,831 nodes
carries a `mat` dict of material keys to kilograms. `commodity_demand()` in
`commodities.py` sums those, converts to tonnes/year the same way
`economy.py`'s `annual_material_demand()` does (kilograms of a project's bill
of materials spread over its `build_yrs`, plus half that again forever for
anything built and still standing with upkeep), and rolls them up by
commodity via `material_keys`. Nothing new had to be invented here; this is
mostly `annual_material_demand()` read through a coarser lens.

**Production had to be invented**, because nothing in the tech tree currently
says "this node makes N tonnes of commodity Y a year." The tree encodes
capability (you now know how to build a power loom) and price/revenue
abstractly (`rev`, sold in the market via `workshop_output()`), not physical
throughput of a tracked bulk good. So `commodities.json`'s `produced_by` is
new data, in two shapes:

- **Extractive/agricultural** (iron, copper, coal, gold, wool): a baseline
  national output (from `resources.json` where one exists, estimated and
  marked `[C]` where it does not, e.g. wool) times a **multiplier** from
  whichever of a short list of technology nodes is built. `met_mine_pumping`
  and `mt2_cyanidation` multiply gold; `fud_livestock_selective_sheep`
  multiplies wool. Nothing multiplies iron or coal in this pass, which is
  honest: it means the six-to-ten commodities chosen do not happen to cover
  a metallurgy throughput node, not that none exist in the tree.
- **Manufactured** (cloth, copper wire): a baseline national
  manufacturing-throughput ceiling (weaver-hours available, smith-hours
  available; estimated, `[C]`) times a multiplier from the best built
  production technology (loom lineage; wire-drawing bench), CAPPED by
  however much of the upstream commodity (wool, copper) is actually
  available once its own recipe ratio is applied. This cap is what makes
  the copper-wire failure case fail: wire-drawing capacity is not the
  constraint, copper is.

`trade_only` commodities (coffee, cotton in this pass) have no `produced_by`
that is a domestic technology at all: their supply is purely an import
figure, discussed in section 6.

## 4. Price versus supply and demand

`commodity_price()` computes:

```
ratio  = demand_t / max(supply_t, epsilon)
factor = clamp(ratio ** elasticity, price_floor_factor, price_ceiling_factor)
price  = base_price_denarii_per_kg * factor
```

This is deliberately symmetric where `economy.py`'s
`material_price_factor()` is not:

### 4.1 Why the existing version only goes up

`economy.py`'s premium is `1.0 + 0.9 * min(1.5, need/supply)^2`, floored at
`1.0`. It cannot go below 1.0 because in that model MORE of your own supply
just relieves a premium down to the flat catalogue price; the catalogue
price is never itself represented as something that falls. That was
sufficient for its purpose (what does buying more of something scarce cost
you specifically), but it cannot represent "automated looms make cloth
cheaper for everyone," because there the BASE PRICE has to move, not a
premium on top of it.

### 4.2 The worked example: looms and cloth

`cloth`'s `produced_by` lists the loom lineage with multipliers (`[C]`
estimates, methodology in `commodities.json`'s notes; order of magnitude
only, per this project's stated convention that ratios matter more than
absolute figures):

| node | multiplier | note |
|---|---|---|
| `tex_warp_weighted_loom` | 1.0 | baseline, attested Roman standard |
| `tex_two_beam_loom` | 1.2 | |
| `tex_horizontal_loom` | 1.5 | |
| `tex_treadle_loom` | 2.5 | frees both hands |
| `tex_power_loom` | 20.0 | order-of-magnitude figure for the shift from a single hand-weaver to a power-loom operator minding several machines through the early Industrial Revolution; not pinned to one citation |

With no loom built, `national_capacity` defaults to the baseline (1.0x) and
demand for cloth (from every node whose `mat` includes `cloth_kg` or
`linen_kg`, see the note on lumping fibres in section 9) sits well above it,
so `commodity_price("cloth", ...)` returns something above the 3.0
den/kg catalogue figure. Build `tex_power_loom` and the SAME demand is now a
small fraction of a twenty-times-larger national capacity, so the ratio
drops, and price falls toward (and can hit) `price_floor_factor`. That fall
is then visible to `hot_air_balloon`, which needs 400 kg of `linen_kg`
(lumped into `cloth` here): its material cost genuinely falls. This is
proven in `sim/test_regressions.py` and in `sim/demo_commodities.py`.

### 4.3 Fluctuation

The brief asks for "+/- fluctuation," not just a deterministic curve. A
second function, `price_with_noise()`, multiplies the fundamental price by
`exp(rng.gauss(0, sigma))`, `sigma` defaulting to 0.08 (an 8% typical annual
swing, `[C]`, chosen to be visible without swamping the supply/demand
signal), clamped to the same floor/ceiling. `price_series()` chains years of
this with light mean reversion, so a market not under sustained pressure
still wobbles year to year the way an actual pre-modern market did, instead
of sitting on a single number forever. This is decoration on top of the
supply/demand mechanism, not a replacement for it: the fundamental (from
demand and supply) sets where the noise centres.

### 4.4 What "fluctuation" is NOT modelled as here

Seasonal variation (a harvest commodity is cheap at harvest and dear before
the next one), and genuine shock events (a mine flooding, a plague year
cutting demand) are both real and both absent. `price_series()`'s noise is a
crude stand-in for both. See section 10.

## 5. Monopoly

"You know where coffee grows and how to process it, so you hold a monopoly
and sell it at a margin" is a pricing regime, not a different price formula:
a monopolist does not sell at the market-clearing price, they sell at
whatever a buyer with no alternative will pay, bounded above by the cost of
the buyer's next-best alternative (smuggling, a rival route, doing without).

`monopoly_price()` takes a marginal cost (what it actually costs you to grow
and process a kilogram) and an alternative price (what a buyer could get it
for elsewhere, possibly `None`, meaning no alternative exists at all) and
returns:

```
ceiling = alternative_price if alternative_price is not None else marginal_cost * max_margin
price   = max(marginal_cost * min_margin, ceiling)
```

`max_margin` defaults to 6.0 (a sixfold markup with no competition at all;
`[C]`, chosen to be dramatic without being absurd -- the historic spice and
silk trades ran retail markups in roughly this range across a WHOLE chain of
middlemen, and a single-owner monopoly is one link, not a chain, so 6x is
already generous rather than conservative). `commodities.json` marks
`monopoly_possible: true` on `coffee`; the flag is advisory, not enforced:
the framework does not currently know whether any OTHER actor could also
supply the commodity, because it has no model of other actors at all (see
section 9).

**Coffee is deliberately anachronistic and is marked as such in the data
file.** Coffea arabica cultivation and coffee drinking are not attested
before roughly the 9th to 15th centuries CE, in Ethiopia and then Yemen; a
Roman of 100 AD has no coffee to hold a monopoly over. It is included purely
to exercise the monopoly mechanic end to end (a good with a `regions` list
of exactly one place, `arabia_horn`, a `cost_multiplier` of 15 already
present in `geography.json`, and nobody else able to reach it), and the
document and the code both say so. Do not wire it into the Rome 100 AD game
state; a later-era civilization file is the honest place for it.

## 6. Trade between regions

This framework does not reinvent `geography.json`; it reads it.
`geography.json.located_materials` already gives, per material, which
regions have it and a `cost_multiplier` calibrated against Roman
`reach_from_italia`; `geography.json.regions[*].minerals` already gives each
region's share of a mined material's output. `commodities.json`'s `regions`
field for an ore/agricultural commodity is that same region list, copied so
the commodity entry is self-describing, not re-derived.

What `commodities.py` does NOT do is recompute `region_reach()`: that
function depends on a specific civilization's home centroid and travel
habits (`Sim._compute_home_centroid`, `Sim.region_reach`,
`GeographyMixin.material_reach`), which only exist on a live `Sim`. A
commodity's "who can we trade it for" answer is therefore two-tiered by
design:

1. **Without a `Sim`** (this framework standalone): `commodities.py` reports
   which regions hold the commodity and the flat `cost_multiplier` from
   `geography.json`, i.e. "Roman-calibrated, unadjusted for who is asking."
2. **With a `Sim`** (a second pass, not built here): the SAME regions list
   would be handed to `Sim.material_reach()` to get a civilization-specific
   multiplier, exactly the way `material_cost_factor()` already does for
   `located_materials` entries that have an `unlocks` node. This is the
   cleanest seam in the whole design for a second pass to extend, because
   the region data and the reach mathematics already exist and already do
   the right thing; only the commodity layer needs to call them.

`trade_partners(commodity_id)` in `commodities.py` gives tier 1 only, and
says so in its return value (`"reach_adjusted": false`).

## 7. Demand propagating down a chain, and failing partway

This is the scenario the brief calls the real test, and it is the one piece
of this framework that had no analogue anywhere in the existing code:
`resource_throttle()` checks a FLAT list of material keys against supply,
each independently; it has no concept of one material being manufactured
from another, so it cannot represent "wire-drawing capacity is fine, copper
is not, so wire is short despite nobody being short of the ability to draw
it."

`propagate_demand(commodity_id, quantity_t, ...)` walks the `recipe` graph
recursively, bottom-up:

1. At a leaf commodity (no `recipe`, e.g. `copper`), the deliverable amount
   is simply `min(requested, national_supply_you_can_reach)`.
2. At a manufactured commodity (has a `recipe`, e.g. `copper_wire`), the
   function first asks each input commodity to deliver `requested * ratio`,
   recursively, THEN takes the smaller of (a) its own production capacity
   (wire-drawing throughput) and (b) what its inputs actually delivered,
   translated back through the recipe ratio.
3. The **bottleneck** is attributed to whichever node's own capacity, not
   its inputs' delivery, is the binding constraint -- so a copper shortage
   is reported as `copper`, not as `copper_wire`, even though `copper_wire`
   is also short.

### 7.1 The worked failure

`el2_three_wire_distribution_system` needs 5,000 kg (5 t) of `copper_wire_kg`
in one build. `copper_wire`'s recipe is `{"copper": 1.05}`, so the request
propagates up as "5.25 t of copper, please." Roman copper output is 15,000
t/yr (`resources.json`, `[C]`), and an ordinary buyer's market share of that
is 3% (`economy.py.MARKET_SHARE["copper"]`, reused, not re-derived) --
450 t/yr reachable, which comfortably covers 5.25 t on its own. So the demo
in `sim/demo_commodities.py` and the regression check both ALSO simulate a
much larger ask (kilometres of wire at industrial scale, tens of tonnes,
against a buyer with no elevated standing and no mine of their own) to
produce the actual shortfall the brief describes, and shows:

- `copper`'s node in the report has `met_fraction < 1`, `bottleneck: "copper"`.
- `copper_wire`'s node ALSO has `met_fraction < 1` (it necessarily inherits
  the shortfall) but `bottleneck: null`, because the shortfall did not
  originate in wire-drawing capacity.

That distinction (who is short vs who merely inherited a shortage) is the
thing a flat throttle cannot say and a chained one can.

### 7.1 This is now wired in, against the real worked example

`el2_three_wire_distribution_system`'s 5,000 kg (5 t) of `copper_wire_kg`
above is not hypothetical: it, and 35 other real nodes (the whole `el2_`
electrical branch, `gp_magnet_wire_enamelled`, `hom_piano`, `en_rotary_
converter`), draw `copper_wire_kg` or `wire_drawn_kg` in the actual tech
tree, and before this pass neither material key was in `economy.py.
MATERIAL_CHECKS`: demand for drawn copper wire was invisible to
`resource_throttle()` entirely, exactly the gap this section describes, not
a constructed example. `economy.py.wire_chain_report(wire_t_per_yr)` now
answers the real question -- would a given wire shortfall actually be
copper running short, or the wire-drawing bench itself -- by calling THIS
file's `propagate_demand()` with `supply_override={"copper": <this Sim's
own reachable copper>}` rather than trusting `commodities.json`'s separate
national estimate. See section 0 for why this, and not a wholesale swap of
`resource_throttle()` itself, was the right amount of wiring.

## 8. Flow, not stock, and what "how much you have" means

Every production and consumption number in this framework, and in
`resources.json` before it, is an annual FLOW: tonnes per year. That is a
deliberate inheritance from the existing model, not a new choice, and it is
worth being honest about its limits. "How much you have" is better answered
two ways, and the framework keeps them separate rather than pretending a
flow model tracks a warehouse:

- **Your production rate**: what you personally mine, grow or manufacture a
  year, from `produced_by` entries you have built plus mine/farm capacity
  you have sunk capital into (the existing `Sim.mine_capacity`,
  `Sim.forest_ha` idea, generalised).
- **Your stock on hand**: a running balance of what you have produced or
  bought minus what you have consumed or sold. `commodities.py` provides a
  minimal `Ledger` class for this (`add`, `remove`, `on_hand`), used by the
  demo, but nothing in the existing `Sim` currently calls it: `Sim` has
  never modelled an inventory, only annual flows netted against each other
  within the same year. Wiring a real stockpile into `Sim` (so unsold cloth
  carries over, so a mine's output that exceeds this year's building
  programme accumulates rather than evaporating) is second-pass work; see
  section 10.

"How much the country has" is answered as a flow throughout this document
(`country_output`), for the same reason `resources.json` answers it that
way: nobody has ever tried to estimate the STANDING STOCK of iron in the
Roman Empire, only its annual production, and flow is the number that
actually binds a plan.

## 9. What is deliberately left out of this pass

- **Only nine commodities are defined.** The brief was explicit: prove the
  machinery, do not populate the tree. `commodities.json` covers something
  mined (iron, copper, coal, gold), something grown (wool), something
  manufactured from another commodity (cloth from wool and flax lumped
  together, copper wire from copper), and something obtainable only by
  trade (coffee, cotton). The other roughly 170 priced materials in
  `prices.json` have no commodity entry and `commodity_demand()` silently
  ignores material keys it does not recognise, exactly like
  `economy.py.MATERIAL_CHECKS` does today.
- **Fibres are lumped.** `cloth` answers for both `cloth_kg` (wool cloth)
  and `linen_kg` (flax cloth), and its `recipe` only checks against wool.
  This is wrong in detail (a linen shortage should not be masked by a wool
  surplus) and was a deliberate simplification to keep the demonstration to
  one clean chain rather than two nearly-identical ones. A second pass
  should split them.
- **No labour throughput ceiling on manufacturing.** `copper_wire`'s supply
  is capped by copper availability and by a flat technology multiplier, not
  by how many smiths exist to draw it. The wage/labour-market machinery in
  `sim/engine/labour.py` is a whole parallel system this framework does not
  touch. A finished good that is short on LABOUR rather than material is a
  real and common failure mode this pass cannot represent.
- **No competing buyers.** `national_supply` minus `market_share` is "what
  you personally could get," not "what is left after the army, the mint and
  every other workshop in the empire have already bought theirs this year."
  There is exactly one demand source in this model: you.
- **No FULL integration into the running game, and that is now a deliberate
  choice rather than unfinished business.** `economy.py` calls
  `propagate_demand()` (section 7.1) for the one capability
  `resource_throttle()` lacked; it does not call this file's `price()`,
  `country_output()`, `market_available()`, `monopoly_price()` or
  `trade_partners()`, because those would duplicate, not improve on, the
  live, already-tested `resource_throttle()`/`material_price_factor()`/
  `mineral_scale()` system for the materials both track. See section 0.
- **Fluctuation is noise, not simulated cause.** Section 4.4 already says
  this; repeating it here because it is the single most visible gap between
  "+/- fluctuation" as asked for and what is actually modelled.

## 10. The hard problems a second pass will hit

1. **Merging with `economy.py` without breaking the regression suite --
   DONE for the one mechanism that needed it, deliberately not attempted
   for the rest.** `economy.py.MATERIAL_CHECKS`, `MARKET_SHARE`,
   `material_price_factor()` and `resource_throttle()` are load-bearing for
   the entire running simulation, including debt, credit limits and mine
   mothballing, all of which have their own regression tests keyed to exact
   numbers. A wholesale swap of those for `commodities.py`'s OWN
   price/national-output machinery would have to reproduce every one of
   those numbers exactly while extending correctly to the materials that
   are not yet tracked -- a careful, mechanical migration for no actual
   gain, since the numbers were already cross-sourced to agree (section 2's
   own note). What this pass did instead: added `copper_wire_kg`,
   `wire_drawn_kg` and `gold_kg` to `MATERIAL_CHECKS` directly (real
   material keys, 36+ live nodes, previously untracked entirely), fixed a
   latent aggregation bug in `resource_throttle()`/`material_price_factor()`
   that checking three copper-drawing keys against one copper supply would
   otherwise have made worse, and wired `propagate_demand()` itself in via
   `supply_override` for the one question (chained-shortage attribution)
   neither function can answer. The regression suite's count grew rather
   than shrank, and stayed green throughout.

   **UPDATE (see section 0.1): a later pass went considerably further.**
   Rather than migrating `economy.py`'s hand-listed 9/13 to `commodities.
   json`'s own (separately-sourced) machinery -- the swap this item argued
   against, and still correctly argues against for the reason given above
   -- the later pass made `economy.py`'s OWN price-response mechanism
   generic over every material key the tech tree uses, with a fallback
   derived from each material's own book price where no curated entry
   exists. This is not the migration this item describes; it is the
   smaller, load-bearing-preserving move the item's own reasoning already
   pointed at ("the numbers were already cross-sourced to agree") extended
   to materials nobody had cross-sourced anything for yet.
2. **Recipe cycles and multi-input recipes.** The demonstration chain
   (copper -> copper wire) is linear. A real recipe graph is not: steel
   needs iron AND coal (as coke) AND limestone flux; gunpowder needs three
   separate commodities in fixed ratios. `propagate_demand()`'s recursion
   handles a DAG with multiple inputs per node fine in principle (it
   already loops over `recipe.items()`), but nothing has tested it against
   a real multi-input node, and nothing detects a cycle (a genuine risk
   once by-products are added, e.g. slag reused as flux).
3. **By-products and joint production.** A copper mine also raises silver
   and arsenic; a bloomery's slag has its own secondary market in some
   periods. Nothing here represents one extraction process yielding several
   commodities at once, which real mining and smelting always do.
4. **Whose demand you are competing against.** Section 9's "no competing
   buyers" gap is the one most likely to produce a silently wrong number at
   scale: the Empire itself buys iron for the army, mints coin from silver,
   and none of that is subtracted from what is "available" before you get
   to it. `resource_throttle()` has the same gap today; it is not new to
   this framework, but this framework makes it easier to notice because it
   is now phrased as "the country's output" explicitly.
5. **Price history and genuine shocks.** A currency debasement, a mine
   flooding, a war closing a trade route: each is a real, dateable price
   event in this simulator's own period (the model already has `SHOCKS` in
   `data.py` for plagues and debasement). None of them currently move a
   commodity price. Wiring `SHOCKS` into `price_with_noise()`'s mean is
   straightforward in principle and untouched here.
6. **Regional trade needs a live `Sim`, and this framework deliberately
   does not have one.** Section 6 already names the seam; taking it means
   deciding whether `commodities.py` becomes a mixin on `Sim` (tight
   coupling, full access to `region_reach`) or stays standalone and is
   handed a small interface (`reach_fn: Callable[[str], int]`) so it can be
   tested without a `Sim` at all. This document has an opinion (the second
   one, for testability) but has not built it.
7. **What counts as "processed" for a monopoly.** `monopoly_price()` takes
   the monopoly as a given boolean. Nothing computes it from first
   principles (do you actually hold every node in the chain that a rival
   would need? Has anyone else researched the same nodes?). The brief's
   coffee example works because coffee is deliberately the only place in
   this data file anyone could grow and process it; a real monopoly check
   needs to reason about OTHER technologies, which this framework has no
   model of at all (see point 4).
