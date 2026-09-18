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
| `thermal_mj` | Process HEAT not already accounted for by a fuel listed in `inputs` - obtainable by burning an ordinary solid fuel, OR by converting mechanical or electrical energy into heat. Priced by `sim/solve_prices.py` through the thermal energy market in `data/production/70_energy.json` (charcoal, coal, electrical resistance/arc, or mechanical friction - whichever is cheaper AND CAPABLE ENOUGH at solved prices; see `temperature_needed_c`/`temperature_reached_c` immediately below - friction is real but essentially never wins, see ENERGY in that file's module docstring). Usually 0 for pre-industrial processes, where the fuel IS the energy. STILL ONE NAMED CARRIER, but no longer one shared PRICE: PER-CONSUMER GRADING (Complaints/44, continued) now solves a separate price for every distinct `temperature_needed_c` this era's entries actually state, so a cool use and a hot use of the same `thermal_mj` field get the cheapest technique that clears EACH one's own requirement, at the same time, rather than one technique chosen for the era's single hottest requirement - see TEMPERATURE in `sim/solve_prices.py`'s module docstring for the full mechanism and why a materials-per-band split was rejected in favour of this. |
| `temperature_reached_c` | Optional, on a TECHNIQUE that supplies `thermal_mj` (or, in the future, another capped carrier) - the sustained temperature (Celsius) that technique can physically deliver, a real physical fact with a stated basis (CLAUDE.md 3.1), never tuned to make it win or lose. Prefer the tech tree's own `cap_heat_0700`/`1100`/`1300`/`1600`/`2000`/`3000` rungs as reference values over an invented number - see the worked entries in `data/production/70_energy.json`. Omit for anything that is not itself an energy-carrier-supplying technique. See CAPABILITY_CAP_FIELDS in `sim/solve_prices.py`'s module docstring for the mechanism this feeds. |
| `temperature_needed_c` | Optional, on a recipe (of ANY kind, not only an energy-carrier technique) that draws a nonzero `thermal_mj` - the temperature its own process genuinely needs. Omitting it is not the same as stating a low number: an entry with no stated requirement pays the shared pool's ordinary price (the cheapest technique clearing only the universal default floor, `sim/solve_prices.py`'s `THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C`), exactly as before this field existed. An entry that DOES state a requirement is graded SEPARATELY from that shared pool and from every other entry's own stated requirement (see PER-CONSUMER GRADING in `thermal_mj`'s own description above) - stating a high requirement here no longer raises what any other entry, including the generic pool, has to pay. See WHEN TO ADD A TEMPERATURE REQUIREMENT below for which entries are worth annotating first. |
| `mechanical_mj` | Shaft work not already accounted for by `inputs` - a turning axle, nothing else. Priced through the same file's mechanical energy market (a water wheel's amortised build, human muscle, a heat engine converting thermal energy, or a motor converting electrical energy - whichever is cheaper). Electricity is NOT automatically shaft work (see ENERGY in `sim/solve_prices.py`'s module docstring, and THE ALUMINIUM DEFECT there for the bug this used to be) - a process that specifically needs a CURRENT, not a shaft, belongs in `electrical_mj` instead even where the current happens to come from a dynamo today. |
| `electrical_mj` | Electrical energy not already accounted for by `inputs` - a current, or heat/work reached only because electricity supplies it (electrolysis; arc or resistance heating, which alone reaches temperatures no fuel here does; a motor). Priced through the same file's electrical energy market (a water wheel through a dynamo, a heat engine through a dynamo, or a photovoltaic panel with no shaft at all - whichever is cheaper). Use this, not `mechanical_mj`, for any process whose PHYSICAL requirement is electricity itself, so the choice-of-technique mechanism can pick photovoltaic over hydro-plus-dynamo once that route is actually cheaper, rather than that choice being foreclosed by which field an entry happened to use. |
| `energy_mj` | The residual: process heat or work needing a technology none of the three energy markets above can supply. Left deliberately uncosted - see ENERGY in `sim/solve_prices.py`'s module docstring for why. Do not reach for this field first; it should be rare. As of this round nothing in this directory uses it - `quartz_tube_kg`, the last entry that did, now draws on `electrical_mj` directly (arc/resistance heating genuinely reaches its 1700-2000 C; see that entry's own yield_basis and TEMPERATURE in the solver's module docstring for why it does not go through the shared `thermal_mj` pool instead). |
| `extracted_from` | For materials nature supplies: 'ore deposit', 'forest', 'quarry', 'arable land', 'seawater'. These earn a rent set by the worst source still worth working, rather than a cost of production. Omit for manufactured materials. |
| `land_iugera_years` | Optional. For a material whose real constraint is GROUND rather than a process (a crop, a fleece, a felled tree) - how many iugerum-years of `iugerum_land` this recipe's WHOLE BATCH ties up, priced against `iugerum_land`'s own solved rent exactly like an ordinary `inputs` entry. See LAND below for the unit, the mechanism, and which materials got it. |
| `basis` | The quantity the whole entry is quoted per. Say it in words. |
| `yield_basis` | WHY these numbers, in physical terms. This is the most important field in the entry. An entry whose yield_basis does not survive a metallurgist reading it is a guess wearing a lab coat. |
| `capital` | Optional. A list of the fixed capital goods this process runs IN rather than consumes making one batch - a furnace, a mill, a chamber, a pan. See CAPITAL below. Omit entirely for a process where capital is not worth separating from labour - see WHICH MATERIALS GOT CAPITAL below for which and why. |
| `requires_node` | WHEN this technique becomes available: the id of the tech-tree node that has to be reached before anyone can run it, or `null` for a technique that needs no technology at all. See WHEN A TECHNIQUE BECOMES AVAILABLE below. Omitting the field is not the same as `null` - it means nobody has classified this entry, and a gated solve drops it. |
| `conf` | A well attested, B probable, C the author's estimate. Be honest; C is fine and common. |

## WHEN A TECHNIQUE BECOMES AVAILABLE

The solver used to have no notion of time. Every technique in this directory
competed on cost alone, in every scenario, so a 100 AD Roman question got its
electricity from a photovoltaic panel and its aluminium from Hall-Heroult -
the cheapest routes, and correct as data, but not available to anyone alive
in 100 AD. `Complaints/39` records the defect. `requires_node` is the fix.

Three states, and the difference between them is the whole point:

| value | meaning |
|---|---|
| field absent | Nobody has classified this entry. It competes in an ungated solve and is DROPPED from a gated one. `validate_production.py` counts these so the gap is a number rather than a silence. |
| `null` | Available to anyone, anywhere, with no technology whatever: gathering firewood, quarrying stone, digging clay, growing wheat. A deliberate statement. |
| a node id | Available once that node is reached. The id is checked against `data/tech_tree.json`; a typo silently means "never available", so it is verified rather than trusted. |

Pick the node that is the REAL gate, not the earliest node the process
touches. Electrolytic zinc needs electrolysis, so its gate is whatever node
supplies an industrial current, not the node that first roasts an ore -
someone who can roast but cannot electrolyse still cannot run this recipe.
When two nodes are both genuinely necessary, name the LATER one, because
that is the one that decides the date; the tree's own `pre` chain carries
the earlier ones.

When the honest answer is that no single node gates it, say so in
`yield_basis` and leave the field absent. An absent field costs coverage,
which is visible and fixable. A wrong node id is invisible and prices a
whole material out of existence in every gated scenario that should have
had it.

A civilisation's `starting_techs` (`data/civilizations/*.json`) is the era
set a gated solve is run against - 223 node ids for `rome_100ad`. So the
test of a label is concrete: with this id, does this technique come out
available to Rome in 100 AD, and is that right?

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

## LAND

`Complaints/49` found that two rounds of work built a real, per-civilisation
Ricardian rent on arable land in `sim/world/land.py` - both margins of it,
extensive (better land against worse) and intensive (diminishing returns to
more labour on the same ground) - and that NOTHING in this directory ever
consumed `iugerum_land`: `wheat_kg` had `inputs={}`, `wool_kg` had
`inputs={}`, and so on for every material whose own prose already said it
came "from arable land" or "from pasture" or "from forest". The rent was
computed and then discarded; no loaf of bread was ever dearer for it.
`land_iugera_years` is the fix.

WHY A NEW FIELD RATHER THAN AN `inputs` ENTRY. Land is not consumed the way
ore or fuel is - the same iugerum grows wheat again next year - so folding
it into `inputs` (which this schema's own rule reads as "consumed making
one batch") would misdescribe what is actually happening: a crop OCCUPIES
land for a season, the way `capital` above already says a smelting recipe
OCCUPIES a furnace rather than consuming it batch by batch. `land_iugera_years`
gets its own field for exactly the reason `capital`'s build bill does not
get hand-added to `inputs` either: naming what a cost IS matters as much as
computing it right.

WHY THE UNIT IS IUGERA-YEARS, NOT BARE IUGERA. `sim/world/land.py`'s own
`margin_outcome_for_civilization` returns a rent that is a FLOW - kilograms
of grain-equivalent per iugerum PER YEAR, exactly the way `data/production/
40_organics.json`'s own `wheat_kg` states its yield as kg per hectare PER
YEAR, not kg per hectare full stop. A flow only becomes a cost once
multiplied by how long the land is drawn on, the same way an hourly wage
only becomes a wage bill once multiplied by hours worked. Land held for two
years costs twice what the same land held for one year does - `capital`'s
own `service_life_years` makes the identical point for a furnace above -
so the natural field is IUGERA TIMES YEARS, stated once per recipe as a
single number rather than as an area and a duration that would have to be
multiplied out downstream every time the price is used.

WHAT THE NUMBER MEANS, CONCRETELY. `land_iugera_years` is a BATCH-level
quantity, exactly like `labour_hours` or a capital good's `build_materials`
- stated against the SAME batch `basis` already describes, not against one
unit of output. For every entry in this file whose `basis` is already "per
hectare ... per year" (`wheat_kg`, `wool_kg`, `milk_kg`, `olive_oil_kg`,
`wine_common_kg`, `cotton_kg`, `hemp_fiber_kg`, `linen_kg`, `silk_kg`,
`rose_petals_kg`, `cork_kg`, `oak_bark_kg`, `shellac_kg`, `rubber_kg`), the
whole batch already IS one hectare-year, so `land_iugera_years` is simply
that one hectare converted into `iugerum_land`'s own unit: 1 ha /
0.2523 ha/iugerum (this directory's own `iugerum_land` entry, the standard
Roman conversion) = 3.9635 iugera-years, THE SAME CONSTANT for every one of
those entries - not a new area estimate per material, only a unit
conversion of the yield each entry already states. `timber_m3` (basis: per
finished cubic metre, not per hectare-year) needs an actual conversion
instead: 1.5 standing m3 per finished m3 (its own stated felling loss) /
4 m3/ha/yr (the midpoint of its own stated 3-5 m3/ha/yr mean annual
increment) = 0.375 ha-years/m3 = 1.4863 iugera-years, and `wood_kg`/
`firewood_kg` (basis: per tonne) reuse that SAME forest's mean annual
increment against their own stated density to get 1.6515 iugera-years/
tonne. `dye_kg`'s own `yield_basis` already computes 1.39 ha-years of
cultivation per tonne directly, so its `land_iugera_years` is just that
figure converted (5.5093). `ox` and `mule` (draft animals, not crops) use
their own already-stated "roughly 3-5 hectares of grazing for the whole
[~4-year] rearing period" - midpoint 4 ha x 4 yr = 16 ha-years = 63.417
iugera-years - closing a gap those two entries' own `yield_basis` used to
flag explicitly ("this land-tenure cost is a genuine rent on grazing land
... but this file's rent mechanism is fixed at zero this round"). Every
entry's own `yield_basis` states its derivation and cites the physical
figure (a mean annual increment, a stocking density, a stated ha-years
figure) it came from - see each entry's own LAND paragraph rather than
re-deriving it here.

HOW IT IS PRICED. `sim/solve_prices.py`'s `recipe_cost_and_allocation`
multiplies `land_iugera_years` by `iugerum_land`'s own solved price (set,
as it always was, by `land_rent_hours_per_iugerum` from `sim/world/land.py`'s
Ricardian margin for the civilisation being solved) and adds the result to
the recipe's cost, exactly the way an `inputs` entry is priced - see RENT ON
GROWN AND LAND-LIMITED MATERIALS in that file's module docstring for the
full mechanism, including why this does NOT create a new cycle (the
reference price used to convert land.py's physical rent into hours is
computed rent-free, once, before land-consuming recipes are priced at all).

WHICH MATERIALS GOT IT, AND WHICH DID NOT. Every material considered:

**Given `land_iugera_years`:** the food and fibre crops (`wheat_kg`,
`olive_oil_kg`, `wine_common_kg`, `cotton_kg`, `hemp_fiber_kg`, `linen_kg`,
`silk_kg`, `rose_petals_kg`, `dye_kg`), the pasture products (`wool_kg`,
`milk_kg`), the forest products (`timber_m3`, `wood_kg`, `firewood_kg`,
`cork_kg`, `oak_bark_kg`, `shellac_kg`, `rubber_kg`), and the two draft
animals (`ox`, `mule`) - every one of them a material whose `extracted_from`
already named arable land, pasture or forest and whose own `yield_basis`
already stated (or, for `dye_kg` and `timber_m3`, straightforwardly
implied) a land requirement in physical terms.

**Considered and excluded, with reasons:**

- Livestock byproducts (`hide_kg`, `bone_kg`, `bristles_kg`, `horsehair_kg`,
  `fat_kg`, `manure_kg`) - each one's own `yield_basis` already says the
  animal's land/feed cost belongs to whatever eventually prices meat, not to
  the byproduct, and explicitly declines to charge it to avoid double-
  counting once a meat entry exists. Adding land here would either double-
  count (if a share of the animal's own grazing were charged to hide AND to
  a future meat entry) or need a `cattle_kg`/`meat_kg` material this
  directory does not have to divide the joint cost against - out of this
  round's scope, and reported as a gap rather than closed. `milk_kg` is
  different: it is extracted DIRECTLY from pasture in its own right (not a
  slaughter byproduct of another priced good), so it got the field.
- `beeswax_kg` - its own `yield_basis` states directly that an apiary is
  NOT land-limited ("bees forage over several kilometres of surrounding
  countryside well beyond any land the beekeeper holds... what limits it is
  the number of hives someone can build and tend"). Taking its own stated
  physical reasoning at face value means no field, not a guessed one.
- `papyrus_sheet` - its own `yield_basis` states directly that the marsh
  reed bed is not the bottleneck ("a stand of papyrus vastly outproduces
  what a small workshop can slice, lay and press in a day"). Same reasoning
  as `beeswax_kg`: the entry's own text says land is not binding.
- Every ORE, QUARRY, SALT-PAN and other MINERAL extraction (`iron_ore_kg`,
  `stone_kg`, `salt_kg`, `clay_kg`, and the rest of `20_nonferrous.json` and
  `30_fuel_stone.json`'s deposit entries) - a mine or a quarry is not a
  field (see `sim/world/land.py`'s own module docstring for why: a
  deposit's margin is set by GRADE, which falls as it is worked, while a
  field's margin is set by location and fertility, fixed and not consumed
  by use). These already have their OWN rent mechanism, `sim/world/
  deposits.py`'s marginal-deposit supply curve for the six named ores, or
  price at zero rent pending one - see RENT ON EXTRACTED MATERIALS in
  `sim/solve_prices.py`'s module docstring. Mixing the two mechanisms would
  misprice both.
- Every MANUFACTURED, downstream material that consumes one of the entries
  above (`leather_kg`, `thread_kg`, `fabric_kg`, `cloth_kg`, `paper_kg`,
  `ink_kg`, `essential_oil_kg`, and the rest of the textile and byproduct
  chain) - these already inherit their land cost through the price of the
  land-carrying material they consume (`leather_kg` pays for land through
  `oak_bark_kg`'s price, `essential_oil_kg` through `rose_petals_kg`'s), the
  same way a smelted metal inherits its ore's rent without a `capital` or
  rent term of its own. Giving them a SECOND `land_iugera_years` on top
  would double-count.

PASTURE AND FOREST PAY ARABLE LAND'S OWN RENT, AND THAT IS A HEURISTIC.
`sim/world/land.py` computes ONE rent, from the margin of cultivation over
ARABLE cropland, because this project tracks only one `iugerum_land`
material. Every pasture and forest entry above pays that SAME rent for its
own grazing or woodland, when real pasture and woodland were commonly land
unfit for the plough and would earn a lower rent of their own at their own
margin - this overstates wool's, milk's, timber's and every forest
product's true land cost. Tag: TEMPORARY HEURISTIC (CLAUDE.md 3.4); fixing
it needs `sim/world/land.py` to carry a separate margin for pasture and
forest, out of this round's scope. The AREA figures themselves (a mean
annual increment, a stocking density) are physical facts, not part of this
heuristic - only the RENT PER IUGERUM they get multiplied by is borrowed
from arable land's own margin.

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
temperature), and friction (mechanical to thermal - real, and modelled;
economically pointless whenever mechanical_mj is priced off human muscle,
but genuinely CHOSEN for one solved round once England 1300's water wheel
made mechanical_mj cheap enough - Complaints/44 - until `temperature_
reached_c`/`temperature_needed_c` gave the choice-of-technique mechanism a
way to rule it out on physical grounds rather than on cost alone). A
recipe that needs one carrier can therefore end up paying for a DIFFERENT
one under the hood, through whichever chain of conversions is cheapest AND
capable enough - see ENERGY in `sim/solve_prices.py`'s module docstring
for the physics of each link (calorific values, furnace and conversion
efficiencies, a water wheel's typical kilowatts from
`data/world/resources.json`) and for what is deliberately NOT modelled
yet (a site-scarcity rent on the best mill sites; an ox as well as a
labourer turning the crank; a second graded dimension alongside
temperature - torque, pressure - which TEMPERATURE in that docstring
gives the worked example for).

TEMPERATURE WITHIN `thermal_mj` IS NOW GRADED PER CONSUMER, NOT ONE SHARED
FLOOR (Complaints/44, continued). The first round's fix computed a SINGLE
floor for the whole `thermal_mj` pool - the largest requirement any active
consumer stated - and that was itself found to be a bug: it let the era's
single hottest requirement lock every cooler use out of a technique that
could obviously still do its (cooler) job, and let a newly cheap cold
source undercut a hot use's own requirement rather than merely the generic
pool's. `thermal_mj` stays ONE named carrier - no `thermal_mj_below_X`
split, and no rewrite of any consuming entry outside this round's ownership
- but the PRICE behind that name is now solved separately for every
distinct `temperature_needed_c` this era's own entries state, so a cool
job and a hot job sharing the same carrier name each get the cheapest
technique that clears THEIR OWN requirement, at the same time. See
TEMPERATURE in `sim/solve_prices.py`'s module docstring for the mechanism
in full and why a materials-per-band split was considered and rejected.

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

## WHEN TO ADD A TEMPERATURE REQUIREMENT

`temperature_needed_c` exists so a specific recipe can say its own process
genuinely needs more heat than the shared `thermal_mj` pool's default floor
(`sim/solve_prices.py`'s `THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C`) already
guarantees - see CAPABILITY_CAP_FIELDS in that file's module docstring for
the mechanism this feeds and Complaints/44 for the defect it closes. Stating
one here grades THIS recipe's own price separately from everything else
(PER-CONSUMER GRADING) - it never raises what any other entry, including
the generic pool, pays, so adding one is safe to do in isolation and does
not need coordinating with any other entry that also draws on `thermal_mj`.

Add it where the temperature genuinely DECIDES which technique wins, the
same test `requires_node` already asks: smelting, forging, glass, pottery
and cement kilns are the obvious candidates in the tree at large, because a
low-grade heat source cannot do any of them - but check first whether the
recipe already burns a specific fuel through its own `inputs` (as every
smelting entry in this directory currently does: `pig_iron_kg`,
`iron_bloom_kg`, `iron_bar_kg` and `tool_steel_kg` all charge `charcoal_kg`
directly rather than drawing on the shared `thermal_mj` carrier at all -
see `thermal_mj`'s own field description above, "usually 0 for
pre-industrial processes, where the fuel IS the energy"). A
`temperature_needed_c` on such an entry would do nothing: the field only
matters for a recipe that actually draws a nonzero `thermal_mj`, which
today is a short, mostly-industrial list (the three `mechanical_mj_
heat_engine_*` entries in `data/production/70_energy.json`, annotated this
round as the worked example, plus a handful of 19th-century chemical
entries in files outside this round's ownership - `petroleum_refined_kg`,
`sodium_carbonate_solvay_kg`, `plaster_kg`, `rosin_kg`,
`ammonium_nitrate_kg` - whose own already-published `yield_basis` text
already states real operating temperatures, none of them close to
challenging the default floor, so leaving them unannotated for now costs
nothing in practice; see this task's own report for the reasoning).

Do NOT try to annotate every thermal_mj-consuming entry in one pass - an
entry with no stated `temperature_needed_c` keeps working exactly as it
did before this field existed (it pays the shared pool's price, gated only
by the pool's own default floor), so leaving one unannotated is a true,
honest "nobody needed more than the default here yet", not a silent wrong
answer the way an unclassified `requires_node` is.

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
| rent | `extracted_from` marks it. **Priced now for two of its three routes.** Ore: `sim/world/deposits.py`'s marginal-deposit supply curve prices `cassiterite_kg` and `galena_kg` (the other four named ores still solve to zero rent this era - Complaints/32). Land: `land_iugera_years` (see LAND above) now lets a GROWN or land-limited material pay `sim/world/land.py`'s Ricardian rent on `iugerum_land` through the ordinary price solve - Complaints/49. Every OTHER extracted material (quarry, salt pan, gold's placer-and-amalgamation step, most metals) still solves at exactly zero rent, unconditionally |
| energy | **priced now, as three connected carriers.** `thermal_mj`, `mechanical_mj` and `electrical_mj` are all read by `sim/solve_prices.py` through the energy market in `data/production/70_energy.json`, linked by conversion techniques (heat engine, dynamo, motor, resistance/arc, friction, photovoltaic - see ENERGY in that file's module docstring); `energy_mj` remains for the rare case none of the three carriers reaches, currently used by no entry in this directory. TEMPERATURE within `thermal_mj` is now graded PER CONSUMER (Complaints/44, continued) - every thermal_mj-supplying technique states what it can reach, and every distinct requirement this era's own consumers actually state gets its OWN separately solved price, rather than one shared floor across every consumer of the carrier; the carrier stays ONE NAME (no `thermal_mj_below_X` split - that would need every other consuming entry, most outside this directory's per-file ownership, rewritten to name a band), which is a considered trade-off rather than a deferred gap; see TEMPERATURE in the solver's module docstring for the mechanism and the trade-off in full |
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
  `Complaints/closed/28-material-keys-that-are-not-materials.md`.

A `D` is not a worse `C`. It is a different statement: a `C` says *I do not
know this number well*, a `D` says *this number should not exist*. Refining a
`D` is wasted work.

## Worked examples

`00_examples.json` holds one entry of each shape - extracted,
smelted, harvested - plus `copper_kg` now also carrying a `capital` entry and
`timber_m3` now also carrying a `land_iugera_years` entry, as the worked
examples of those fields' shapes. Copy the shape, not the numbers.

Run `python3 sim/validate_production.py` after every edit, and
`--todo` to see what is still missing, worst first.
