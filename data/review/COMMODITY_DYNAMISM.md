# Is the commodity model dynamic, or does it only look it?

Audited by running the engine directly (not by reading alone). Every number
below came out of a live `Sim` built with the `sim()` helper from
`rome/sim/test_regressions.py`, run from `rome/sim`. Read-only: nothing in
the engine or the data was changed.

## Verdict, up front

**Partly, and the honest split is narrow.** Two real mechanisms exist and
both genuinely respond to supply and demand — but only for **9 hand-named
commodities** (13 material keys), out of **162 distinct material keys** the
tech tree actually uses. Everything else — **149 material keys, roughly
92% of them**, aluminium and silk and glass and cotton and every dye,
acid, alloy and textile among them — has a price that is a constant, read
once out of `prices.json` at load time, and never revisited for any reason
at all: not scarcity, not surplus, not population, not time.

There is also a *third*, better mechanism — `commodities.py`'s
`CommodityLedger`, a genuinely general elasticity-based price function that
would work correctly for an arbitrary, unanticipated commodity if it were
fed real demand and supply. It is not a lookup table; it is the real thing.
But it is wired into the live game for **zero** commodities' prices. Its
only live call site (`wire_chain_report()`) uses it to produce a diagnostic
report about copper wire, and never touches what anything costs or earns.
`core.py`'s own comment says as much: *"core.py still does not import this
module and Sim still has no inventory."* That remains true today.

And the "market" that goods-producing concerns (looms, print shops,
photography studios) sell into is not a market at all: it is a private
per-node clock. Verified by experiment below.

## The flooding test (iron)

Iron is one of the 9 tracked commodities, so this one genuinely works:

- With heavy iron demand pinned (one node alone, `mat_bulk_steel`, asks for
  15,000 t/yr against an empire baseline of 82,500 t/yr), the price
  pressure multiplier `material_price_factor("iron")` opened at **3.03x**
  book price (demand was badly outrunning what the market would sell at
  this civilization's standing).
- Opening the largest iron mine the model would allow (geology- and
  standing-capped at **7,863 t/yr** for this Rome start — you cannot sink
  an arbitrarily large mine; `mine_quote` for 1,000,000,000 t/yr politely
  reports "room left before geology stops you: 7,862.8") and letting it
  mature (3-year lead time) dropped the multiplier to **2.77x**.
- A *completely unrelated* iron-consuming project (`ag2_baler`, nothing to
  do with the steel node creating the demand) got **8.4% cheaper**
  (3,631.8 -> 3,326.0 denarii) purely because the mine existed. This is a
  real cross-project price effect, not a special case for the node that
  built the mine.
- Flooding *beyond* what the player needs does nothing further: the
  multiplier floors at 1.0 (book price) once supply clears demand, and the
  mine cannot be sunk past the geological/standing ceiling regardless of
  capital available (confirmed: asking for 5x the ceiling with 50 million
  denarii in hand still only yields the ceiling amount).
- **There is no revenue from selling iron.** Mining in this engine is a
  pure cost center: capital sunk, opex paid every year, and the payoff is
  entirely on the *buying* side (cheaper future purchases, higher
  `resource_throttle`). Nothing credits `revenue()` for tonnes mined; a
  `mine_capacity` entry never appears anywhere in the revenue calculation.
  So "does your revenue from selling iron fall as you saturate the market"
  has no answer in this model — there is no such revenue to begin with.
- Scope caveat: "does anyone else's project get cheaper" is answered inside
  a single civilization's own economy. This is a solo-player economic
  simulation against a static "the empire's market" backdrop, not a
  multi-agent market with other buyers who might also feel the glut.

## The unanticipated-commodity test — the heart of it

**162** distinct material keys appear in `mat` dictionaries across the tech
tree. Of those, **13** (mapping to 9 underlying tracked "tags") get *any*
price response at all, because — and only because — they appear by name in
`economy.py`'s `MATERIAL_CHECKS` / `MARKET_SHARE` dictionaries:

**Dynamic (13 keys / 9 commodities):** `charcoal_kg`, `firewood_kg`,
`iron_bar_kg`, `iron_ore_kg`, `coal_kg`, `copper_kg`, `copper_wire_kg`,
`wire_drawn_kg`, `lead_kg`, `tin_kg`, `silver_kg`, `gold_kg`, `nitre_kg`
(saltpetre).

**Inert (149 keys, ~92%):** everything else, tested directly rather than
assumed — `aluminium_kg`, `silk_kg`, `glass_raw_kg`, `cotton_kg`,
`wool_kg`, `cloth_kg`, `linen_kg`, `cast_iron_kg` (yes — even a
sibling of tracked iron, `cast_iron_kg`, is not itself tracked), plus
`bauxite_kg`, `brass_kg`, `bronze_kg`, `ammonia_kg`, `asbestos_kg`, dozens
of acids, dyes, alloys and textiles — the entire industrial-age and
chemical-age material list.

Experiment, not inference: I pinned each of these to the node that demands
the most of it (e.g. `mt2_duralumin_alloy` for aluminium, 950 kg in one
build), set that node active, and asked `material_market_factor()` for the
project cost multiplier. Result for every single one: **1.0**, to within
floating-point noise (`1.0000000021`), regardless of how large the demand
was set. The function's own code explains why without any ambiguity:
`material_price_factor()` returns `1.0` immediately if the material's tag
`not in self.MARKET_SHARE`, and `material_market_factor()` simply skips
(`continue`) any material key not in `MATERIAL_CHECKS` when computing a
project's weighted price factor. It is not that these commodities respond
weakly — they are not consulted at all.

### The aluminium question, specifically

**No.** Aluminium is a completely ordinary case of the 92%, not a special
one. There is no aluminium mine (`open_mine` only recognizes seven
materials by hardcoded name: coal, iron, copper, lead, tin, silver, gold —
electrolysis is not among them and could not be, since the mechanism is a
literal dictionary of material names, `MINE_CAPEX_PER_T_YR`). There is no
supply-side lever of any kind for it. `prices.json` carries a flat `6.0`
denarii/kg for `aluminium_kg` with a note explaining that *historically*
aluminium was pre-electrolysis a precious metal at ~2,000 den/kg and its
price collapsed after Hall-Héroult — that collapse is **narrative prose in
a comment, not a mechanism**. Nothing in `economy.py` even contains the
string "aluminium." Producing an enormous amount of it via electrolysis
tech changes nothing about what it costs to buy, because nothing ever asks
how much of it exists. Coffee, silk, saltpetre (partially — saltpetre
*is* one of the 9 tracked, via nitre beds) and glass all land in the same
place: coffee_kg does not even appear as a material key anywhere in the
tech tree (its entire existence is one illustrative, explicitly
"do-not-wire-in" entry in `commodities.json`, flagged anachronistic by its
own author); silk and glass are ordinary flat-priced materials with no
production mechanism and no price response, identical in kind to
aluminium.

### The better mechanism that exists but isn't used

`commodities.py`'s `CommodityLedger.price(commodity_id, demand_t, supply_t)`
is a genuine, general constant-elasticity price function — demand equal to
supply gives 1.0x, 5x demand gives 5.0x (bounded by a floor/ceiling),
0.2x demand gives 0.4x, confirmed by calling it directly. It would handle
an arbitrary, never-anticipated commodity correctly *if* given real
numbers. But `commodities.json` only defines **9** commodities total
(iron, copper, copper_wire, coal, gold, wool, cloth, cotton, coffee — the
file's own `_doc` calls itself "A FRAMEWORK, not a catalogue" built to
"exercise every case," not to cover the game), and its own `_doc` states
plainly: `"not_integrated": "sim/engine/core.py's Sim class does not read
this file."` The one live call site, `wire_chain_report()`, hands it a
supply override and gets back a diagnostic tree naming which link in a
copper-wire supply chain would break — useful, but it never feeds into
`project_cost()` or `revenue()`. It changes what a player is *told*, never
what anything actually costs or earns.

## The demand side

Demand for the 9 tracked commodities (`annual_material_demand()`) is real
in the narrow sense that it is computed, not a constant: it sums the
material bill of every node the player currently has under construction
(half-weighted, spread over build years) plus every node they are running
with upkeep (half-weighted again, every year, forever). Verified: with
zero active or done nodes, demand is exactly `{}` — nothing is assumed, it
all has to come from what is actually being built.

But that demand comes from **only one source: the player's own build
list.** It does not come from population "wanting" iron, from a bigger
society needing more copper, or from income/affordability of any kind.
Verified directly: holding a fixed demand load, sweeping population from
6.5M to 650M people changes `material_price_factor("iron")` by exactly
zero (`3.0250` at every population level) — because `mineral_scale()`
(geology and trade reach) is deliberately decoupled from population by
design, per its own comment (*"A coalfield does not care how many people
live near it"*). This is a considered choice, not an oversight, and it is
narrower than "demand comes from anywhere real": there is no independent
population-consumption term at all for the 9 tracked raw materials — no
"more people eat more grain," "more people wear more wool." The only place
population enters the *supply* side of a tracked commodity is charcoal,
which is treated as a local wood market rather than a mined resource
(`_material_market_tonnes` scales charcoal, and only charcoal, by
`pop_scale`, confirmed linear: 50 -> 100 -> 1,000 -> 10,000 t/yr as pop
scale went 0.05 -> 0.1 -> 1.0 -> 10.0).

For the 4 `GOODS_CATEGORIES` (see below), population and "the economy" do
reach the model, but only by stretching *how long a fixed-shape decline
takes*, not by creating any real quantity of demand.

## The population link

There is a real, working population -> plague -> `pop_deficit` ->
`pop_scale` cascade (`core.py`), and it does reach commodity-adjacent
numbers, but through exactly two channels, both indirect:

1. **Charcoal's market tonnage**, linearly, as shown above (this is the
   one tracked raw material population genuinely feeds).
2. **`goods_market_factor()`'s `tau`** (how many years before a goods
   market visibly saturates): `tau = base_tau * pop_scale**0.5 *
   economy**0.25 / reach`. Verified: the identical node, identical age (50
   years), earns a revenue factor of **0.726** at 1/10th population versus
   **0.818** at 10x population — a real, measurable, population-driven
   difference in how fast a concern's earnings decay.

For the other 8 tracked raw materials (iron, copper, lead, tin, silver,
gold, coal, saltpetre) population has **no effect whatsoever** on price —
confirmed identical `material_price_factor` (3.0250) across a 100x
population sweep with demand held fixed. This is not a bug; it is a
deliberate, well-reasoned modelling decision (geology, not demography,
caps a mine), but it does mean "does a bigger society want more iron"
is answered **no**, on purpose, in this model.

## The goods side — a real market, or a clock wearing its clothes?

A clock. Tested directly, not inferred from reading:

- One textile concern (`hom_clothes_dryer_electric`), operating alone,
  age 20 years: revenue factor **0.7840**.
- The *same* concern, same age, with a second textile concern
  (`hom_mangle_wringer`) *also* operating in the same category, same age:
  revenue factor **0.7840** — bit-for-bit identical. The second concern's
  factor was also 0.7840. Neither affected the other at all.
- Ten identical concerns of the same category, all operating, all the same
  age: the first one's factor is still exactly **0.7840** — indistinguishable
  from being alone in the market.

`goods_market_factor(k)`'s only inputs are: this node's own category
config, this node's own `age` (years since *this specific node* opened),
and the civilization-wide `pop_scale` / `economy` / `reach` scalars — none
of which are affected by what any other concern, in the same category or
not, is doing. There is no shared "how much supply of this category
already exists" state anywhere; "supply" in the formula (`supply = 1.0 +
age/tau`) is a synthetic stand-in for "the rest of the world," not a count
of anything the player or any other agent has actually built. Two players
opening the same kind of concern in the same year would, in this model,
each independently earn as if they had the market to themselves, forever.
This spans **118 nodes** (50 textiles, 31 processing, 19 printing, 18
photography) — every one of them declines on a private per-node clock with
zero cross-elasticity to any other concern, including its own twin.

## Counts, stated exactly

| | count |
|---|---|
| distinct material keys used anywhere in the tech tree | 162 |
| material keys with ANY price response to supply/demand | 13 (-> 9 commodities: charcoal, iron, coal, copper, lead, tin, silver, gold, saltpetre) |
| material keys that are a flat, never-revisited price | 149 (~92%) |
| commodities with a *correct, general* elasticity price function available | 9 defined in `commodities.json`, of which 0 are wired to affect what anything actually costs or earns in a live game |
| goods-producing nodes whose revenue follows a real market (cross-elastic with competitors) | 0 |
| goods-producing nodes whose revenue follows a private per-node age clock | 118 (all of GOODS_CATEGORIES) |
| mined materials with a production lever at all (a mine you can sink) | 7 (coal, iron, copper, lead, tin, silver, gold) — out of 162 |

## What would it take to make it general?

The smallest change is not a new pricing formula — `CommodityLedger.price()`
already IS a correct, general one; it was built, tested, and then never
connected. The gap is entirely about wiring and missing per-commodity data,
not about inventing new economics:

1. **Give every material key a commodity id and a supply model, not just
   9 of them.** `commodities.json`'s schema (`base_price`, `elasticity`,
   `national_output_t_per_yr` or a production route, `market_share`) is
   already the right shape — it just needs an entry for the other ~150
   keys instead of three flat-file replacements to imagine per commodity.
   Missing data specifically: a national-output ceiling (or "trade only,
   import_capacity") and *some* production route (a mine, a farm, a
   manufacturing recipe, or explicitly "trade only, no domestic route")
   for every one of the 149 currently-inert keys. Aluminium in particular
   needs a `recipe` (bauxite + electricity, gated behind the electrolysis
   tech the tree already has) rather than a hardcoded pre/post price note.
2. **Replace the hand-maintained `MATERIAL_CHECKS`/`MARKET_SHARE`
   dictionaries with a lookup into that general commodity table**, so
   `project_cost()` and `material_market_factor()` ask "does this material
   key belong to a tracked commodity" by table membership, not by a
   maintainer having remembered to add a new line for every new material
   the tree grows.
3. **Compute real demand from the tree once, generically**, the way
   `annual_material_demand()` already does — it is generic over material
   keys today; only the *price response on top of it* is hand-listed. So
   step 2 mostly subsumes this: once every material key resolves to a
   commodity, the existing demand summation needs no changes at all.
4. **Replace `goods_market_factor()`'s per-node age clock with the same
   `CommodityLedger` machinery**: track cumulative built capacity per
   *category* (or better, per underlying manufactured commodity) across
   every concern that sells into it, and price off that shared total the
   same way `CommodityLedger.price()` already prices copper wire off
   national copper supply. That single change is what would make two
   concerns in the same market actually compete.
5. **Give `Sim` the inventory `commodities.py`'s `Ledger` class already
   sketches** — a running stock, not just an annual flow — so "I flooded
   the market this year" can be felt as a multi-year glut rather than
   resetting every step.

None of this requires new theory. The elasticity function, the recipe
graph, the demand summation and even a stock-ledger class all already
exist in the codebase, proven correct in isolation by `commodities.py`'s
own tests. What is missing is (a) data — a commodity entry for the other
~150 materials — and (b) actually importing `commodities.py` into `core.py`
and routing `project_cost()` / `revenue()` through it instead of around it.
