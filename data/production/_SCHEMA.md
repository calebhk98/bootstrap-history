# data/production/ - what makes each material, and how much comes out

WHAT MAKES EACH MATERIAL, AND HOW MUCH COMES OUT. The tech tree records what every process CONSUMES and almost never what anything PRODUCES: of the 162 materials its recipes consume, not one has a node declaring a yield. iron_bar_kg is consumed by 590 nodes and nothing makes it. That is why every cost in this engine bottoms out in a book price - there is no production side to compute one from, so a book was the only place a number could come from. This file is the production side.

## Why this is a separate directory from the tech tree

The tech tree answers 'what must exist before I can build this'. That is a different question from 'what does a kilogram of this cost to make', and mixing them into the same node made the merge fight itself: mat_* ids are duplicated across seventeen branch files and treetool keeps the first, so a recipe added to one of them silently loses. Keeping production separate also makes the material-to-producer link EXPLICIT. sim/audit_costs.py currently has to guess it by stripping a unit suffix off the material key and hoping a node id matches, which works for 47 of 162.

One file per material family, merged by material key, exactly like
`data/branches/`. Several people can author at once without colliding.
A key defined twice is an error rather than a silent overwrite -
`sim/validate_production.py` says which files disagree.

## THE RULE THAT GOVERNS EVERY NUMBER HERE

A yield is a physical fact about a process - ore grade times recovery, reduction stoichiometry, kerf and drying loss, extraction rate. It is NEVER derived from what the material sells for, and never tuned so that a computed price matches data/prices.json. Those prices are 91.8% the author's own estimates and this file exists to replace them, so calibrating against them would be arguing in a circle. If you cannot say where a number comes from in physical terms, write what you can defend and mark conf C - an honest C is worth more than a fitted A.

## How the price falls out

Once every material has inputs and a yield, the price of each is the cost of what it consumes plus the labour it takes plus rent on anything nature supplied rather than a process, and every one of those is defined the same way. That is a system of equations, solved for the fixed point where all prices agree. See docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md Part 2.

## Fields

| field | meaning |
|---|---|
| `outputs` | {material_key: quantity}. Usually one key. More than one means genuine joint production - smelting galena yields lead AND silver, and pretending otherwise misprices both. |
| `inputs` | {material_key: quantity} consumed to produce that output. Keys must be material keys the tree already uses, or new ones you also define an entry for. A material with no inputs is EXTRACTED rather than made: say so in extracted_from. |
| `labour_hours` | {trade: hours} to produce one basis unit. Trades must exist in data/prices.json wage_rates_denarii_per_hour. |
| `thermal_mj` | Process HEAT not already accounted for by a fuel listed in `inputs` - obtainable by burning an ordinary solid fuel, OR by converting mechanical or electrical energy into heat. Priced by `sim/solve_prices.py` through the thermal energy market in `data/production/70_energy.json` (charcoal, coal, electrical resistance/arc, or mechanical friction - whichever is cheaper at solved prices; the last of these is real but never wins, see ENERGY in that file's module docstring). Usually 0 for pre-industrial processes, where the fuel IS the energy. Left UNDIFFERENTIATED by temperature this round - a decision, not an oversight; see TEMPERATURE in `sim/solve_prices.py`'s module docstring before pointing a high-temperature need at this field. |
| `mechanical_mj` | Shaft work not already accounted for by `inputs` - a turning axle, nothing else. Priced through the same file's mechanical energy market (a water wheel's amortised build, human muscle, a heat engine converting thermal energy, or a motor converting electrical energy - whichever is cheaper). Electricity is NOT automatically shaft work (see ENERGY in `sim/solve_prices.py`'s module docstring, and THE ALUMINIUM DEFECT there for the bug this used to be) - a process that specifically needs a CURRENT, not a shaft, belongs in `electrical_mj` instead even where the current happens to come from a dynamo today. |
| `electrical_mj` | Electrical energy not already accounted for by `inputs` - a current, or heat/work reached only because electricity supplies it (electrolysis; arc or resistance heating, which alone reaches temperatures no fuel here does; a motor). Priced through the same file's electrical energy market (a water wheel through a dynamo, a heat engine through a dynamo, or a photovoltaic panel with no shaft at all - whichever is cheaper). Use this, not `mechanical_mj`, for any process whose PHYSICAL requirement is electricity itself, so the choice-of-technique mechanism can pick photovoltaic over hydro-plus-dynamo once that route is actually cheaper, rather than that choice being foreclosed by which field an entry happened to use. |
| `energy_mj` | The residual: process heat or work needing a technology none of the three energy markets above can supply. Left deliberately uncosted - see ENERGY in `sim/solve_prices.py`'s module docstring for why. Do not reach for this field first; it should be rare. As of this round nothing in this directory uses it - `quartz_tube_kg`, the last entry that did, now draws on `electrical_mj` directly (arc/resistance heating genuinely reaches its 1700-2000 C; see that entry's own yield_basis and TEMPERATURE in the solver's module docstring for why it does not go through the shared `thermal_mj` pool instead). |
| `extracted_from` | For materials nature supplies: 'ore deposit', 'forest', 'quarry', 'arable land', 'seawater'. These earn a rent set by the worst source still worth working, rather than a cost of production. Omit for manufactured materials. |
| `basis` | The quantity the whole entry is quoted per. Say it in words. |
| `yield_basis` | WHY these numbers, in physical terms. This is the most important field in the entry. An entry whose yield_basis does not survive a metallurgist reading it is a guess wearing a lab coat. |
| `capital` | Optional. A list of the fixed capital goods this process runs IN rather than consumes making one batch - a furnace, a mill, a chamber, a pan. See CAPITAL below. Omit entirely for a process where capital is not worth separating from labour - see WHICH MATERIALS GOT CAPITAL below for which and why. |
| `conf` | A well attested, B probable, C the author's estimate. Be honest; C is fine and common. |

## CAPITAL

`inputs` and `labour_hours` say what a batch eats. Neither says what it is
made IN. A blast furnace does not appear in iron's `inputs` - nothing about
the furnace is consumed making one tonne of pig iron - but the furnace cost
something to build and it wears out, and both of those are real costs that
belong in the price of what comes out of it.

Each item in the `capital` list is one capital good:

```
{
 "good": "blast furnace stack, structural masonry",
 "build_materials": {"stone_kg": 400000.0},
 "build_labour_hours": {"mason": 3000.0, "labourer": 1500.0},
 "service_life_years": 40,
 "annual_output_at_basis": 400000.0,
 "capital_basis": "why these four numbers, in physical terms",
 "conf": "C"
}
```

`build_materials` and `build_labour_hours` are the physical bill to build ONE
such capital good, given in exactly the same shape as this file's own
`inputs` and `labour_hours` - not a lump of currency. This is the whole
design: a furnace is so much brick, so much iron and so much mason's labour,
each of which this file already knows how to price, so capitalising it stays
inside the same solved system instead of reintroducing a book number wearing
a new field's name. A furnace priced in bricks is a furnace whose cost falls
when bricks get cheaper, and a lump-sum "cap_cost_denarii" field would not do
that - it would just be `prices.json` again, one field over.

`service_life_years` and `annual_output_at_basis` turn a build bill into a
cost per basis-unit: `(cost of build_materials + cost of build_labour_hours)
/ (service_life_years * annual_output_at_basis)`. Both are PHYSICAL FACTS
about the thing - how many years before the lining spalls apart or the
timbering rots, how many tonnes a campaign actually turns out in a year -
never a financial depreciation convention (there is no straight-line vs.
declining-balance choice to make here, because nothing here is amortising a
purchase price; it is amortising a build bill that is itself computed from
physical quantities). If you would have to look up an accounting standard to
answer either field, you are answering the wrong question.

`capital` is a LIST rather than one object because a real plant is not one
lifetime. A blast furnace's stone stack stands for decades; the firebrick
lining inside it spalls from thermal shock and slag attack and gets rebuilt
every few years; a water-wheel's timber frame rots faster than either. Averaging
those into a single blended service life would hide exactly the fact that
matters - that the lining is rebuilt many times over the stack's one lifetime
- so an entry with parts that wear at different rates gets one list item per
part, each with its own build bill and its own life, rather than one number
that quietly assumes they wear together.

`capital_basis` is `yield_basis`'s counterpart, held to the same 50-character
floor by the validator: say where the build bill, the service life and the
annual output come from, in terms a millwright or a mason would recognise,
not in terms a banker would.

**This is now wired in.** `sim/solve_prices.py` reads `capital` and adds the
amortisation formula above to a recipe's cost alongside its ordinary inputs,
labour and rent - see the CAPITAL section of that file's module docstring
and `recipe_cost_and_allocation`. It was deliberately never hand-added to
`inputs` instead, which would have hidden the capital cost as an ordinary
material flow rather than naming it. Two of the entries above are genuine
recipe cycles once this is read - `iron_bar_kg`'s own hammer fittings are
800 kg of `iron_bar_kg`, and `pig_iron_kg`'s hearth lining is 3,000 kg of
`iron_bar_kg` while `iron_bar_kg` is made from `pig_iron_kg` - and both
resolve correctly because `sim/solve_prices.py`'s resolvability pass now
tests cycles for productiveness instead of refusing every one outright; see
Complaints/31 and Complaints/32.

## ENERGY

`thermal_mj`, `mechanical_mj` and `electrical_mj` are the THREE carriers a
process can draw on for heat, work or current beyond what a fuel already in
its `inputs` supplies - never interchangeable by fiat: a kilogram of
charcoal cannot turn a shaft, a water wheel cannot run an electrolysis cell,
and (this round's fix) a shaft is not the only way to get a current either.
All three are priced, not looked up: see `data/production/70_energy.json`,
which defines each carrier as a MATERIAL with several TECHNIQUES for
supplying it, exactly like `salt_kg` has a solar-pan technique and a
brine-boiling one - `sim/solve_prices.py` picks whichever technique is
cheaper at the solved prices, so the choice of fuel, motive power or
generating route is an OUTPUT of the solve, never a fact stated in advance.

THE THREE CARRIERS ARE CONNECTED, NOT THREE SEPARATE MARKETS. Alongside the
PRIMARY techniques (burn a fuel for thermal; a water wheel or human muscle
for mechanical; a photovoltaic panel for electrical, with no shaft anywhere
in that one's chain), `70_energy.json` also has CONVERSION techniques that
turn one carrier into another - a heat engine (thermal to mechanical,
Carnot-limited, modelled as a genuine historical RANGE of techniques rather
than one number, because this is the conversion the industrial revolution
actually is), a dynamo (mechanical to electrical) and a motor (electrical to
mechanical, the same machine run the other way), resistance/arc heating
(electrical to thermal - the only route here that reaches an arbitrary
temperature), and friction (mechanical to thermal - real, and modelled, and
never the market's cheapest route, which the solver's own choice-of-technique
output demonstrates rather than assumes). A recipe that needs one carrier
can therefore end up paying for a DIFFERENT one under the hood, through
whichever chain of conversions is cheapest - see ENERGY in
`sim/solve_prices.py`'s module docstring for the physics of each link
(calorific values, furnace and conversion efficiencies, a water wheel's
typical kilowatts from `data/world/resources.json`) and for what is
deliberately NOT modelled yet (a site-scarcity rent on the best mill sites;
an ox as well as a labourer turning the crank; TEMPERATURE GRADING within
`thermal_mj` itself - see TEMPERATURE in that docstring for why that is a
named, deferred decision rather than a silent gap).

USE `electrical_mj`, NOT `mechanical_mj`, FOR A GENUINELY ELECTRICAL NEED.
The previous version of this schema described `mechanical_mj` as including
"work delivered as electricity... a carrier for shaft work rather than a
source of its own" - reasoning that is right for a waterwheel-and-dynamo
civilisation and wrong in general, since a photovoltaic cell or a fuel cell
makes electricity with no shaft anywhere in the chain (see THE ALUMINIUM
DEFECT in `sim/solve_prices.py`'s module docstring for the full story and
`aluminium_kg`'s own yield_basis for the fix). A process that needs
electrolysis current, or heat/work that is available ONLY because
electricity supplies it (arc heating reaching a temperature no fuel here
does; induction sintering), belongs in `electrical_mj`, letting the
choice-of-technique mechanism decide whether that current comes from a
dynamo or a solar panel rather than that choice being foreclosed by which
field the entry happened to use. `mechanical_mj` is for a turning axle and
nothing else now.

`energy_mj` still exists for the rare case none of the three carriers
reaches - a technology this file cannot yet price a path for. As of this
round nothing in this directory uses it: `quartz_tube_kg`, the one entry
that used to (its 1700-2000 C need is hotter than any charcoal or coal fire
reaches), now draws on `electrical_mj` directly, because resistance/arc
heating genuinely reaches that temperature - see that entry's own
`yield_basis`, and TEMPERATURE in `sim/solve_prices.py`'s module docstring
for why it draws on `electrical_mj` directly rather than through the shared,
temperature-blind `thermal_mj` pool (routing it through that pool would let
it silently pay coal's price while claiming coal's ~1000-1200 C fire can do
what only the arc route can - the very mistake TEMPERATURE warns about).

## WHICH MATERIALS GOT CAPITAL, AND WHICH WERE LEFT CAPITAL-LIGHT ON PURPOSE

Capital was added where it plausibly dominates - heavy, campaign-run
apparatus that stands for years and is expensive to build - not everywhere.
Judgement, not coverage, is the point; see the milestone note in
`docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md`.

**Given capital:** `pig_iron_kg` (blast furnace stack, separately from its
shorter-lived hearth lining and bellows drive), `iron_bar_kg` (finery hearth
and water-powered hammer), `tool_steel_kg` and `steel_plate_kg` (cementation
furnace; `steel_plate_kg` also a rolling mill), `wire_drawn_kg` (water-powered
draw-bench and dies), `copper_kg` (a small shaft furnace, added to
`00_examples.json` as the worked example of the field's shape), `lead_kg`
(smelting hearth and cupellation furnace), `zinc_electrolytic_kg` and
`aluminium_kg` (the reduction cell itself only - the generating plant behind
their electricity need, `mechanical_mj` for zinc and `electrical_mj` for
aluminium as of this round's fix, is excluded from THIS capital list, but is
no longer uncosted: it is priced separately, through the energy market in
`data/production/70_energy.json` - see ENERGY above), `glass_raw_kg`
(pot furnace, relined nearly every campaign), `coal_kg` (shaft timbering and
winding gear - real capital that is easy to forget because extraction entries
otherwise carry only labour), `sulfuric_acid_kg` (the lead chamber itself -
sheet lead is not cheap and the chamber's whole cost is lead and labour, which
this file already prices), and `salt_solar_kg` (pan levees and sluices - added
specifically because it is the CHEAP case: a saltern's works are real but
modest, unlike a furnace, and showing that contrast is worth more than only
showing the expensive examples).

**Left capital-light on purpose**, meaning judged genuinely small relative to
labour and materials rather than merely not-yet-done: `charcoal_kg` and
`brick_1000` (an earth clamp or a brick scove kiln is built from the very
material being fired and a day's digging - there is no separate lasting
structure to amortise); `lime_kg` (same reasoning - a simple stone-lined pit
kiln); bloomery-route steel (`iron_bloom_kg`, `steel_noric_kg`) and
`cast_iron_kg` (a small clay-and-turf bloomery shaft was historically rebuilt
for each smelt or every few smelts, so its build cost is already closer to a
per-batch material than a multi-year asset, and `cast_iron_kg`'s own furnace
cost is already carried by the `pig_iron_kg` it is cast from); ore and quarry
extraction generally (hand tools, not a structure); `ammonia_kg` (its
capital - a coking plant - is already flagged in its own `yield_basis` as an
unresolved joint-costing problem; capitalising it now would bury that problem
rather than fix it); and the remaining crucible-scale nonferrous alloys
(`bronze_kg`, `brass_kg`, `tin_kg`, `silver_kg`'s patio process) and modern
electric-furnace minor metals (`tungsten_kg`, `chromium_kg`, `manganese_kg`,
`nickel_kg`, `molybdenum_kg`), which are real gaps rather than considered
zeroes - they were simply lower priority than the entries above by
consumption count and are left for the next pass rather than guessed at here.

## WHAT THIS SCHEMA DOES NOT MODEL, AND THE SIZE OF THE HOLE

Found by building `sim/solve_prices.py` and reading the answer, which is the
only way these things get found.

The solver computes, for every material, the cost of its inputs plus the cost
of its labour. That is **prime cost**. It is not a price, and the gap is
structural rather than a matter of precision:

| missing | status |
|---|---|
| **capital** | field exists now (see CAPITAL above), populated for the ~13 materials where it plausibly dominates, and read by `sim/solve_prices.py` |
| rent | `extracted_from` marks it; the solver fixes it at zero this round |
| energy | **priced now, as three connected carriers.** `thermal_mj`, `mechanical_mj` and `electrical_mj` are all read by `sim/solve_prices.py` through the energy market in `data/production/70_energy.json`, linked by conversion techniques (heat engine, dynamo, motor, resistance/arc, friction, photovoltaic - see ENERGY in that file's module docstring); `energy_mj` remains for the rare case none of the three carriers reaches, currently used by no entry in this directory. TEMPERATURE within `thermal_mj` is a separately named, deliberately deferred gap - see TEMPERATURE in the solver's module docstring |
| transport | not modelled anywhere |
| margin, risk, failed batches | not modelled anywhere |

Capital was the big one and the only one with no field at all - it has one
now, and it is read. Every entry here still says what a process eats and,
for most of them, nothing about what it is done *in*; the `capital` field
says that for the materials where it was judged to matter. The tech tree
carries the whole thing as `cap`, which is 23.5% of its whole cost base, and
only the ~13 entries listed under WHICH MATERIALS GOT CAPITAL above have any
of it reflected here yet - most of the tree's `cap` share still has not
crossed into this directory, though what has crossed now feeds the solver.

The size of the hole, measured rather than guessed: a kilogram of iron bar
comes out at **0.96 labour-hours** with capital counted (0.95 without it -
see Complaints/32 on how small the capital charge turns out to be), which at
the book unskilled wage is about 72 denarii a tonne against a book price of
1,000 - still nearly fourteen times. Put the other way round, the computed
number says an unskilled labourer could buy a kilo of iron with about an
hour's work - which is roughly true today and was nowhere near true in Rome,
where iron was dear. Capital was not the gap; see Complaints/32 for what is
(rent on extracted materials, fixed at zero, is the largest single term).

So the solver's numbers are an **honest lower bound**, and knowing precisely
which things are missing is worth more than a closer number would be. Do not
add a fudge factor to close the gap. Capital is now read; rent and energy are
next, in the order Complaints/32 sets out.

## Confidence, and what it is actually measuring

`conf` grades **how well the numbers are evidenced**, not how sure you feel.
It is a provenance scale inherited from `data/prices.json`, and it is about
where a figure came from.

There is a fourth grade, `D`, because the first round of authoring needed one
and did not have it. Three agents independently used `C` for two
incompatible things: "this is my estimate of a real quantity" and "this entry
should not exist, the thing it describes is not a material." A reader cannot
tell those apart, and they call for opposite responses - refine the first,
delete the second.

- **A** - well attested. A measured figure, or one that follows from
  stoichiometry and physical constants with nothing assumed.
- **B** - probable. Scholarly consensus, contested in the detail. Or derived,
  but resting on one stated assumption a reasonable person might set
  differently - a kiln efficiency, an ore grade.
- **C** - the author's estimate or inference. Order of magnitude. Honest, and
  common; most of this data is C and should be.
- **D** - **placeholder. The entry is wrong in KIND, not merely uncertain in
  degree.** The thing it describes is not a material, or has no mass, or is a
  person. The numbers are there to hold the slot and must not be trusted or
  refined - the entry wants deleting once whatever consumes it is fixed. See
  `Complaints/28-material-keys-that-are-not-materials.md`.

A `D` is not a worse `C`. It is a different statement: a `C` says *I do not
know this number well*, a `D` says *this number should not exist*. Refining a
`D` is wasted work.

## Worked examples

`00_examples.json` holds one entry of each shape - extracted,
smelted, harvested - plus `copper_kg` now also carrying a `capital` entry, as
the worked example of that field's shape. Copy the shape, not the numbers.

Run `python3 sim/validate_production.py` after every edit, and
`--todo` to see what is still missing, worst first.
