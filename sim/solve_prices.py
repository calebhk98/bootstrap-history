#!/usr/bin/env python3
"""Solve for the price of every material from physical structure, not a book.

    python3 sim/solve_prices.py                        every price, in labour-hours
    python3 sim/solve_prices.py --why iron_bar_kg       full recursive cost breakdown
    python3 sim/solve_prices.py --compare               computed price vs prices.json,
                                                         as a ratio, worst disagreement first

STANDALONE AND READ-ONLY. This tool computes prices; nothing in `sim/engine/`
reads them yet. `data/prices.json` still runs the game. That wiring is a
separate, later change - this file only has to prove the calculation works
and say honestly where it does not.

THE MECHANISM, from docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md Part 2:
a material's price is what it costs to make one unit of it -

    price_of(material) =  sum over inputs of
                              quantity_per_unit(material, input) * price_of(input)
                        +  sum over trades of
                              hours_per_unit(material, trade) * wage_of(trade)
                        +  rent_per_unit(material)

Every input price on the right is defined by the same equation, so this is a
system of equations rather than a lookup, solved for the fixed point where
every price is consistent with every other. `data/production/` supplies
`quantity_per_unit` (its `inputs`) and `hours_per_unit` (its `labour_hours`)
for 182 materials once byproducts are counted; `data/prices.json`
`wage_rates_denarii_per_hour` supplies the wage ratios. Nothing here is a
lookup of a finished price - only of the physical recipe and the relative
wage, which is what the mechanism is allowed to take as given.

NUMERAIRE: one hour of UNSKILLED labour, per the design doc's Part 2.1. The
`labourer` trade is the unskilled one - it is the cheapest trade in the wage
table, and entries in data/production/ that need generic unskilled effort
(spinning thread, moving ore) already book it to `labourer` rather than to a
craft. Every wage is expressed as a ratio against `labourer`'s rate, so
`wage_of("labourer") == 1.0` by construction and every price this script
prints is "how many hours of unskilled labour", never denarii.

RENT ON EXTRACTED MATERIALS (Complaints/32, fixed this round for six of
seven metals). Extracted materials (ore at the pit head, timber in the
forest, salt in the pan) have no cost of production - nature made them,
nobody's labour did - so their price should be their labour cost plus a
RENT on the deposit or field, set by the quality of the worst source still
worth working (the extensive margin). That margin needs geography
(competing sites of different quality) and demand (something bidding for
the marginal one). `data/production/` still cannot supply either - it is a
flat recipe list with no notion of "this ore body" versus "that poorer
one" - but `sim/world/deposits.py` now can: it carries a named-deposit
supply curve (ore grade, hardness, depth, sinking cost) for iron, copper,
tin, lead, silver, gold and mercury, and finds the marginal deposit for a
given quantity demanded exactly the way Ricardian rent theory says to.
This file now uses it for the six of those seven metals that
`data/production/` represents as an EXTRACTED ore material
(`iron_ore_kg`, `copper_ore_kg`, `cassiterite_kg`, `galena_kg`,
`silver_ore_kg`, `cinnabar_kg` - see RENT_BEARING_ORE_MATERIALS below).
Gold is the exception: `gold_kg` folds placer extraction and mercury
amalgamation into one recipe with no separate `extracted_from` ore stage
of its own (see WHAT THIS DOES NOT REACH below), so it is left at zero
rent, unchanged, rather than forced into a mechanism the data does not
carry for it.

THE DEMAND-DETERMINES-THE-MARGIN LOOP, AND HOW IT WAS ACTUALLY CLOSED.
Ricardian rent is circular by construction: which deposit is marginal
depends on how much is demanded, and (in a fully closed model) how much is
demanded depends on the price that same margin sets. This project has no
demand system yet (`sim/world/demand.py` prices HOUSEHOLD demand, not a
metal market's quantity response to its own price), so the loop is NOT
closed here - it is cut, deliberately and visibly, at the same place
`sim/world/deposits.py`'s own docstring already cuts it: quantity demanded
is fixed at `data/world/resources.json`'s `empire_output_100ad` figure for
each metal, a real historical OUTPUT level (an initial condition, per
CLAUDE.md 3.1) rather than a quantity derived from the price this file
computes. TAG: TEMPORARY HEURISTIC (CLAUDE.md 3.4) - the day a real supply-
and-demand system exists for these metals, `rent_hours_per_kg_by_ore_
material` is the one function that changes, and everything downstream of
it (the rent term in `recipe_cost_and_allocation`, choice of technique
between the ore-route and byproduct-route for silver, and so on) is
already wired to take whatever number it produces.

HOW THE PER-KG-OF-METAL RENT BECOMES A PER-KG-OF-ORE PRICE, AND THE
APPROXIMATION THIS INTRODUCES. `sim/world/deposits.py` prices a metal per
kilogram of CONTAINED METAL raised, pre-smelting; `data/production/` prices
its ore materials per kilogram of ORE (rock or gravel), and lets the
smelting recipe that consumes the ore state its OWN, separate, generic
ore-to-metal ratio (`copper_kg` assumes 50 kg ore/kg metal; no particular
named deposit in `deposits.json` need actually run at that grade). Folding
a per-kg-metal rent into a per-kg-ore price therefore needs a ratio to
convert with, and this file uses each metal's DOMINANT smelting recipe's
own ratio for that conversion (RENT_BEARING_ORE_MATERIALS names it), which
makes the rent embedded in THAT recipe's own final price exactly right by
construction (see `rent_hours_per_kg_by_ore_material`'s own docstring for
the algebra) but is only APPROXIMATE for any OTHER recipe that consumes
the same ore at a different ratio: `iron_ore_kg` feeds both `pig_iron_kg`
(2.2 t ore/t metal, the ratio used here) and `iron_bloom_kg` (4.0 t
ore/t metal, the bloomery route) - `iron_bloom_kg`'s own share of iron's
rent comes out about 1.8x too large as a result. `galena_kg` has the
opposite, harmless case: it also feeds `bismuth_kg` and `selenium_kg` at
enormously higher ore-per-unit ratios, and those materials picking up a
proportionally large share of lead's rent is the CORRECT answer (a trace
byproduct that needs three million kg of galena per kg recovered should
carry three million kg worth of that galena's rent), not an artifact.
Tag: TEMPORARY HEURISTIC (CLAUDE.md 3.4) for the `iron_bloom_kg` case
specifically; fixing it needs `data/production/` to record the actual
deposit or grade each recipe draws on, which is out of this file's scope
and out of this task's ownership (`data/production/` is owned elsewhere
right now).

WHAT THIS DOES NOT REACH. Quarried stone, salt, gold's placer-and-
amalgamation step, and every metal `sim/world/deposits.py` has no named-
deposit list for still price at exactly zero rent, unconditionally - a
mine's grade-based margin is not a fact this file has for them yet. Zero
rent there is still not "no answer" - it is an honest lower bound:
whatever the true price is, it is at least the labour it takes. Tag:
HEURISTIC, not a physical fact, tracked against Milestone 1's provenance
ledger. Forest timber and every other GROWN or land-limited material get a
real rent instead of this zero-rent treatment - see RENT ON GROWN AND
LAND-LIMITED MATERIALS immediately below.

RENT ON GROWN AND LAND-LIMITED MATERIALS (Complaints/49 - "land rent
reaches no crop"). `sim/world/land.py` computes a real, per-civilization
Ricardian rent on arable land - both margins of it, extensive (better
land against worse) and intensive (diminishing returns to more labour on
the same ground) - and `land_rent_hours_per_iugerum` above turns that into
`iugerum_land`'s own solved price. Without this section, nothing else in
`data/production/` looks that price up: `wheat_kg` has `inputs={}`, so its
price is mathematically guaranteed to be labour cost alone, whatever an
iugerum is worth, and the same is true of wool, timber, olives, wine and
every other material a recipe's own prose says comes "from arable land",
"from pasture" or "from forest" without a single recipe actually consuming
any - a real rent computed on the land side that reaches no price anybody
pays on the crop side. This section is the fix.

A FIELD IS NOT A MINE (see sim/world/land.py's own module docstring), so
this needed its own route into a recipe's cost rather than reusing
RENT_BEARING_ORE_MATERIALS' ore-grade mechanism above: a crop is not the
material that earns a rent, the LAND it grows on is, and the crop merely
OCCUPIES that land for a season rather than consuming it the way a
smelter consumes ore. `land_iugera_years` (data/production/_SCHEMA.md) is
the field that says so - a BATCH-level quantity, exactly like
`labour_hours` or a capital good's `build_materials` above, of how many
land-area-YEARS this recipe's whole batch ties up on `iugerum_land`.
LAND-AREA-YEARS, not bare area, because land held for two years costs
twice what the same land held for one year does - the same reasoning
`capital`'s own `service_life_years` already applies to a furnace, and
the natural unit once yield (kg per iugerum per YEAR) and rent (hours per
iugerum per YEAR) are both already flows: multiplying a flow by however
long it is drawn on is what turns it into a cost, exactly as an hourly
wage times hours worked is what turns it into a wage bill.

HOW IT IS WIRED. `recipe_cost_and_allocation` reads `land_iugera_years`
and multiplies it by `current_prices["iugerum_land"]` exactly the way it
already prices an ordinary `inputs` entry - a NEW term
(`land_cost_hours`), not folded into `material_cost_hours` itself, for
the same reason CAPITAL's build bill gets its own term rather than being
hand-added to `inputs`: naming what a cost IS matters as much as
computing it right. `_dependency_materials` and `_has_external_anchor`
both now see `iugerum_land` as a dependency whenever `land_iugera_years`
is nonzero, so the resolvability and cycle-productiveness passes above
treat a land-consuming recipe exactly like one that consumes any other
extracted material - no separate code path, because land-as-an-input and
ore-as-an-input are the same shape once `iugerum_land` has a price.

WHY THIS DOES NOT CLOSE A CYCLE BACK ON ITSELF. `iugerum_land`'s own price
never depends on the crop prices `land_iugera_years` feeds into:
`land_rent_hours_per_iugerum` fixes it, once, before the main iteration
starts, from land.py's PHYSICAL rent and wheat_kg's ZERO-LAND-RENT
reference price (see that function's own docstring for why seeding
`{"iugerum_land": 0.0}` into that ONE reference call keeps it that way
even though wheat_kg now states a `land_iugera_years` of its own). wheat's
ACTUAL solved price - what bread, and every other consumer of wheat, pays
- does include land rent, computed by the ordinary Jacobi iteration below;
it is only the one-off unit-conversion call that stays rent-free, and it
runs once, not every round. So the arrow runs one way: land.py's physical
inputs (population, territory, fertility - no price anywhere in them) ->
`iugerum_land`'s hours price (fixed) -> every land-consuming material's
own solved price (iterated) - never back around to land.py itself or to
wheat's own reference price.

WHICH MATERIALS GOT IT, AND WHICH DID NOT. See data/production/_SCHEMA.md's
own LAND section for the full considered list and the reasoning on each -
every material whose `extracted_from` names arable land, pasture or
forest and whose own `yield_basis` already states (or straightforwardly
implies, for `dye_kg`'s already-computed hectare-years and `timber_m3`'s
mean annual increment) a land requirement now carries it; livestock
byproducts with no independent land claim of their own, and the apiary
and marsh entries whose OWN yield_basis says land is not their binding
constraint, do not.

PASTURE AND FOREST PAY ARABLE LAND'S OWN RENT, AND THAT IS A HEURISTIC.
sim/world/land.py computes ONE rent, from the margin of cultivation over
ARABLE cropland; wool, milk, timber and every forest good above pay that
SAME rent for their own pasture or woodland, because this project tracks
only one `iugerum_land` material and one margin. Real pasture and
woodland were commonly land unfit for the plough and would earn a lower
rent of their own at their own margin, so this overstates their true land
cost. Tag: TEMPORARY HEURISTIC (CLAUDE.md 3.4), tracked against the same
provenance ledger as the ore-rent approximations above; fixing it needs
sim/world/land.py to carry a separate margin for pasture and forest,
which is out of this round's scope.

ENERGY IS PRICED AS THREE MARKETS - THERMAL, MECHANICAL AND ELECTRICAL -
CONNECTED BY CONVERSION RECIPES, NOT TWO MARKETS WITH ELECTRICITY GLUED TO
ONE OF THEM (Complaints/32's third gap; see WHY ELECTRICITY HAS ITS OWN
CARRIER below for why electricity needs the third market). Every
entry that needs process heat or shaft work beyond what a fuel already
listed in its `inputs` supplies draws on one of `thermal_mj`, `mechanical_mj`
or `electrical_mj`, and all three are real inputs this script prices through
`data/production/70_energy.json` - a handful of PRIMARY techniques (burn a
fuel, turn a water wheel, catch photons) plus CONVERSION techniques that
turn one carrier into another, priced and chosen exactly like any other
multi-recipe material (see CHOICE OF TECHNIQUE below). The three-way split
is still the physics, not a modelling convenience: a kilogram of charcoal, a
turning shaft and a flow of electrons are three different things a process
can be handed, and collapsing any two of them into one undifferentiated
number would let whichever was cheaper silently stand in for the other,
hiding exactly the constraint - which technology can reach which
TEMPERATURE, and which can deliver which kind of WORK - that this file's own
instructions from CLAUDE.md name as the point of the exercise.

    thermal_mj      heat, from burning an ordinary solid fuel, OR from
                    converting mechanical or electrical energy into heat
                    (see CONVERSIONS below). Priced via whichever of
                    thermal_mj_charcoal, thermal_mj_coal,
                    thermal_mj_electrical_resistance or thermal_mj_friction
                    the solved prices make cheapest - a real choice of
                    technique, not an assumption about which fuel a process
                    "should" use. The two combustion techniques are costed
                    the same way: a fuel's calorific value (taken at ~29
                    MJ/kg for both charcoal and coal, deliberately the SAME
                    figure for both, since real values for the two overlap -
                    the choice between them here turns on which is cheaper
                    to PRODUCE, not on an invented energy-density gap) times
                    a furnace efficiency (25%, bracketed by this file's own
                    lime-kiln 20% and brine-boiling-pan 30% figures) sets how
                    much fuel one usable megajoule needs.

    mechanical_mj   shaft work - a turning axle, nothing else. Priced via
                    mechanical_mj_waterwheel (a water wheel's amortised
                    build, using the `capital` mechanism below, at the
                    typical output data/world/resources.json's water_power
                    constraint gives), mechanical_mj_human_muscle (a
                    labourer's own sustained output, from that same file's
                    human_power constraint), mechanical_mj_motor (electrical
                    energy through a motor - see CONVERSIONS) or one of the
                    three mechanical_mj_heat_engine_* techniques (thermal
                    energy through a heat engine) - whichever the solved
                    prices make cheapest. Water beats muscle by roughly
                    three orders of magnitude (a few kilowatts continuous
                    beats 75 W every time) and every heat-engine technique
                    too (see CONVERSIONS - a heat engine at efficiency e
                    costs thermal_mj's own price divided by e per MJ of
                    mechanical output, so even the 40%-efficient modern one
                    needs a thermal_mj price under 40% of water's own
                    mechanical_mj price to compete, and coal is nowhere
                    near that cheap relative to water) - THAT part is the
                    supply curve, not an
                    assumption. Whether water also beats mechanical_mj_motor
                    depends entirely on how electrical_mj itself resolves,
                    which is a separate question this docstring's
                    ELECTRICAL_MJ entry and WHY ELECTRICITY HAS ITS OWN
                    CARRIER below answer honestly rather than assume: with
                    `electrical_mj_photovoltaic` included, the motor route
                    currently wins, for reasons that entry explains and
                    flags as resting on an admittedly incomplete cost.

    electrical_mj   electricity - the one carrier with no shaft and no flame
                    required to reach it at all (see WHY ELECTRICITY HAS
                    ITS OWN CARRIER).
                    Priced via electrical_mj_dynamo (mechanical energy
                    through a dynamo) or electrical_mj_photovoltaic (photons,
                    directly, through a solar panel's fixed capital and
                    NOTHING ELSE) - whichever the solved prices make
                    cheapest. Also consumed directly, as electrolysis
                    current or as arc/resistance heat, by any recipe whose
                    own `electrical_mj` field says it needs some (aluminium_kg
                    and silicon_kg this round; see WHICH ENTRIES USE
                    ELECTRICAL_mj DIRECTLY below).

WHY ELECTRICITY HAS ITS OWN CARRIER RATHER THAN BOTTOMING OUT IN
`mechanical_mj`. "Electricity is a carrier, not a source, so it must bottom
out in whatever turns the dynamo" is right for a waterwheel-and-dynamo
civilisation and wrong in general: a photovoltaic cell makes electricity
from photons with no shaft anywhere in the chain, and so does a
thermoelectric couple, a battery or a fuel cell. Forcing every use of
electricity through `mechanical_mj` would make a civilisation with
arbitrarily cheap solar panels structurally unable to ever make cheap
aluminium, which is not a fact about aluminium - it would be a fact about a
schema with only two carriers that picked the wrong one to call
"electricity." Electricity therefore has its own carrier (`electrical_mj`),
and `aluminium_kg` draws on THAT, with `mechanical_mj` reaching it only
through the `electrical_mj_dynamo` conversion below, exactly like every
other route does.

THE CHECK, RUN HONESTLY RATHER THAN ASSUMED TO PASS. The expectation going
in was that nothing should change except by a dynamo's own conversion loss,
since this file has no combustion engine cheap enough to beat a water
wheel (see mechanical_mj's own note above) and therefore no OTHER route to
electricity worth considering. Excluding `electrical_mj_photovoltaic` and
re-solving confirms exactly that: `electrical_mj` prices at 0.00388 h/MJ via
`electrical_mj_dynamo` (against `mechanical_mj`'s own 0.00258 - a ~50%
premium for the dynamo's conversion loss, its own labour and its own
amortised build, all individually modest and all pointing the same
direction), and aluminium_kg prices at roughly 15-16% more than the
labour-only mechanical route gives (0.442 h/kg against 0.382 h/kg),
squarely "roughly the mechanical-route figure plus a dynamo's losses." So
the mechanism is right.

But that is NOT what the DEFAULT solve above reports, and saying so is the
point of this paragraph rather than something to quietly fix. With
`electrical_mj_photovoltaic` included - which it should be, since removing
it again would just be re-hiding the case this whole fix exists to show -
the solver finds PHOTOVOLTAIC cheaper than the water-wheel-and-dynamo route
for `electrical_mj`, and that cheap electricity then cascades: the solved
`thermal_mj` and even `mechanical_mj` end up routed through
`thermal_mj_electrical_resistance` and `mechanical_mj_motor` respectively,
both ultimately rooted in the same panel. Aluminium's price actually FALLS
relative to the old book-mechanical figure (0.319 h/kg, not up by a dynamo's
loss), because the cheapest path skips the dynamo's conversion loss
entirely - exactly the case WHY ELECTRICITY HAS ITS OWN CARRIER above says
a mechanical-only schema could never represent. This is the mechanism doing
its job, not a defect,
but the specific NUMBER behind it should not be over-read: `silicon_kg`'s
own yield_basis is explicit that its cost omits crystal growth, wafer
sawing, cell processing and module lamination - real, individually
significant steps - so the panel's amortised cost, and therefore this
entire cascade, is a LOWER BOUND that most likely understates real
photovoltaic-grade silicon's true cost by a margin this file cannot yet
quantify. Until that gap closes, treat "the solver's default technique for
mechanical and thermal energy is now photovoltaic" as a demonstration that
the mechanism CAN reach that conclusion, not as a settled claim that it
should - see `--why aluminium_kg` for the worked numbers behind both
figures (no Complaints/ entry was filed for this fix - that directory is
outside this change's scope).

CONVERSIONS - the graph that makes the three carriers into one connected
market instead of three separate ones, each a TECHNIQUE exactly like a
fuel-burning or water-wheel entry, living in `data/production/70_energy.json`
and chosen by the same cheapest-technique rule as everything else:

    thermal    -> mechanical   heat engine, Carnot-limited. THIS is the
                                conversion whose improvement IS the
                                industrial revolution, so it is not one
                                number but three genuinely competing
                                techniques spanning the historical range:
                                mechanical_mj_heat_engine_atmospheric (~1%,
                                a Newcomen-class atmospheric engine),
                                mechanical_mj_heat_engine_compound (~10%, a
                                good 19th-century compound engine) and
                                mechanical_mj_heat_engine_modern_steam (~40%,
                                a modern reheat steam cycle). None of the
                                three ever wins the mechanical_mj comparison
                                in this file - not against a water wheel,
                                and not against mechanical_mj_motor either
                                (see mechanical_mj above) - which is a
                                finding the arithmetic produces, not a rule
                                this file enforces.
    mechanical -> electrical   electrical_mj_dynamo, ~92.5% (the stated
                                90-95% range's midpoint).
    electrical -> mechanical   mechanical_mj_motor, ~92.5% - the same
                                machine as the dynamo above, run in reverse,
                                and priced with the same build bill for
                                exactly that reason.
    electrical -> thermal      thermal_mj_electrical_resistance, ~98%.
                                Resistance or arc heating reaches ANY
                                temperature - there is no furnace-wall or
                                flue loss the way a combustion route has,
                                which is the whole reason arc furnaces exist
                                - but it feeds the same UNDIFFERENTIATED
                                `thermal_mj` pool as charcoal and coal do,
                                so this technique only ever wins the generic
                                pool's price on ordinary running cost, never
                                on reaching a temperature the other two
                                cannot: see TEMPERATURE, NOT MODELLED THIS
                                ROUND below for why that matters and what it
                                means for quartz_tube_kg.
    mechanical -> thermal      thermal_mj_friction, ~98% efficient and
                                MODELLED ANYWAY, because the stakeholder
                                asked about this one specifically rather
                                than take "obviously pointless" on faith.
                                It is real (this is literally how a brake
                                works) and it is never chosen: turning
                                mechanical_mj into heat this way costs
                                mechanical_mj's own price divided by 0.98,
                                and mechanical_mj is already pricier per MJ
                                than coal, so thermal_mj_friction can never
                                undercut thermal_mj_coal for any material in
                                this file. That "always loses" claim is the
                                solver's own choice-of-technique output
                                (`chosen_recipe_by_material["thermal_mj"]`),
                                not an assumption baked in by leaving the
                                technique out.
    photons    -> electrical   electrical_mj_photovoltaic. No fuel, no
                                shaft, no water wheel anywhere in the
                                chain - a fixed panel (glass, an aluminium
                                frame, copper wiring and a silicon cell,
                                priced via the new `silicon_kg` entry) that
                                turns sunlight into current for free running
                                cost, for as long as the panel lasts. THE
                                CASE THAT PROVES THE OLD MODEL WRONG: nothing
                                about this technique can be expressed as
                                shaft work at any efficiency, so a schema
                                with only `thermal_mj` and `mechanical_mj`
                                had no honest place to put it at all.
                                `silicon_kg`'s own yield_basis is explicit
                                that its electrical_mj figure covers only
                                carbothermic reduction and Siemens-process
                                purification - real crystal growth, wafer
                                sawing, cell doping and module lamination are
                                each individually energy-intensive and NONE
                                of them are modelled here, so this
                                technique's price is a LOWER BOUND by a
                                margin this file cannot yet quantify. Tag:
                                GAP, not a heuristic, per CLAUDE.md 3.4.

TEMPERATURE, AND WHY A SINGLE SHARED FLOOR IS ITSELF A BUG (Complaints/44).
A megajoule of heat is not fungible across temperature: one MJ at 200 C
cannot do what one MJ at 1600 C can, which is the whole reason a bloomery
cannot melt iron however much charcoal is fed into it. Every
thermal_mj-supplying technique states its own `temperature_reached_c`, and
a technique that falls short of what a use needs is excluded from it - but
computing ONE shared floor for the whole pool - the LARGER of the pool's
own default (`THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C`) and whatever the
single HOTTEST active consumer states it needs - is wrong, even though it
correctly keeps a warm bearing out of England's forges: a single global
floor means the hottest consumer in the WHOLE ECONOMY sets the bar for
every other use of the carrier, however cool. Concretely, on the data as it
stands, the three `mechanical_mj_heat_engine_*` entries' own stated 1000 C
requirement would raise a SHARED floor to 1000 C for every thermal_mj
consumer in the file, plaster and rosin (150-160 C, per their own
`yield_basis`) included - harmless today only because charcoal and coal
both happen to clear 1100 C anyway, not because the mechanism is right.
Invent a technique that reaches 2500 C anywhere in the economy (a genuinely
hot process, nothing to do with brick-firing) and the SAME shared-floor
logic would raise the pool's floor to 2500 C and lock charcoal and coal -
both 1100 C, comfortably hot enough to fire a brick, glaze a pot or melt
glass - out of every thermal_mj use in the file, brick-firing included.
That is the stakeholder's own example (a fission-hot process should not
disqualify existing coal burning from melting iron) and the mirror image of
it (a cheap, merely-warm source should not stop being usable for the modest
jobs it is already doing, the moment something hotter is invented
elsewhere) - both follow from the same defect: a shared floor conflates
"what the hottest job needs" with "what every job may use."

THE FIX IS PER-CONSUMER GRADING, not a second global number and not
several separate carrier materials. `thermal_mj` stays ONE named carrier
- so every entry outside this round's ownership that already draws on it
(`petroleum_refined_kg`, `sodium_carbonate_solvay_kg`, `plaster_kg`,
`rosin_kg`, `ammonium_nitrate_kg`, none of which state their own
`temperature_needed_c`) keeps reading exactly the same field name and
needs no edit - but the PRICE a given consuming recipe pays for it is no
longer one shared number. `capability_required_grades` collects the set
of distinct requirements THIS era's own entries actually state (the
carrier's own universal default, `THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C`,
plus each ACTIVE consumer's own `temperature_needed_c`);
`capability_price_for_requirement` then solves, separately, for
the cheapest technique that clears EACH one of those requirements, at
this round's own prices - so a 2500 C requirement gets its own answer
(today: `thermal_mj_electrical_resistance`, the only technique in this
file that reaches it) without disturbing the 1000 C answer the heat
engines get (charcoal or coal, whichever is cheaper - unchanged) or the
700 C answer everything else gets (also charcoal or coal - also
unchanged). A recipe that states no requirement at all still just pays
`thermal_mj`'s own ordinary solved price - the cheapest technique
clearing the universal default floor, which is ALL `capability_floor_
by_carrier` computes (see its own docstring: it looks only at the
carrier's own universal default, not at what any consumer needs, because a
consumer's own need is graded separately). `thermal_mj_friction` is
excluded from every one of these grades it cannot reach (its own 100 C
never clears even the 700 C default) - grades are independent of each
other, so a hot grade existing, or ceasing to exist, never touches a
cooler grade's own answer.

This is a real fix, not the bloomery-melts-iron mistake restated: it does
not claim charcoal and coal can do what only an arc furnace can (see
`quartz_tube_kg` below, still bypassing the pool entirely and unaffected
by this round's change), and it does not single out friction by name -
`thermal_mj_friction` loses every grade it competes for because its OWN
stated reach (100 C - the ordinary, sourced ceiling of a sustained,
unpressurised mechanical friction heater; see that entry's own
yield_basis for the citation) falls short of every one of them, the same
way `thermal_mj_electrical_resistance` (3000 C) and `thermal_mj_charcoal`/
`thermal_mj_coal` (1100 C each) clear the 700 C and 1000 C grades easily
and only resistance clears a hypothetical 2500 C one.

`thermal_mj` STILL stays a single NAMED carrier rather than being split
into several materials (`thermal_mj_at_1100`, and so on) - the two
candidate shapes this task's own report weighs are "separate carrier
materials, using the tree's own `cap_heat_0700/1100/1300/2000/3000` rungs
as band edges" against "one carrier, priced per consumer", and the second
is what is built here, for a reason specific to this round's ownership
rather than a claim that it is better in general: the five consuming
entries in the paragraph above live in files this task does not own, and
every one of them names the field `thermal_mj`, not a banded name - a
separate-materials scheme would need each of THEIR OWN entries rewritten
to say which band they draw from, which is exactly the edit this task is
fenced off from making. Per-consumer grading needs no such rewrite: it
reads the SAME `thermal_mj` field and the SAME (optional)
`temperature_needed_c` field every entry already has the vocabulary for,
and grades the price behind the name rather than the name itself. If a
future round DOES own every consumer (or the split is judged worth a
coordinated rewrite anyway), separate band materials remain available
and would give each band its own resolvable price for `--why` and
`--compare` to show directly, rather than the graded price computed on
demand the way this round shows it (see print_why's own ENERGY section
below) - a real trade-off, not a decision this round claims to have
closed.

A SECOND PHYSICAL LIMIT SLOTS IN THE SAME WAY, WITHOUT REDESIGN (the
stakeholder's own example: a water wheel should not be able to deliver a
torque of millions) - add a second entry to `CAPABILITY_CAP_FIELDS` keyed
on `mechanical_mj`, e.g. `("torque_reached_nm", "torque_needed_nm",
0.0)`, give `mechanical_mj_waterwheel` and friends their own `torque_
reached_nm` (a real figure: a wheel's torque is its power divided by its
shaft's angular speed, both already physical facts this file or
`data/world/resources.json` states), and give whichever recipe needs a
torque floor its own `torque_needed_nm`. Nothing else changes:
`capability_required_grades`, `capability_price_for_requirement` and
`_meets_capability_floor` all key off `CAPABILITY_CAP_FIELDS` rather than
naming `thermal_mj` or `temperature_reached_c` anywhere in their own
bodies, so a torque-needing forge press and a temperature-needing kiln
would be graded side by side, on two independent dimensions of the SAME
`mechanical_mj`/`thermal_mj` carriers, by the same two functions that
grade temperature today. See this task's own report for the worked
argument.

WHICH ENTRIES USE ELECTRICAL_MJ DIRECTLY, RATHER THAN THROUGH A CONVERSION.
`aluminium_kg` (Hall-Heroult electrolysis current), `silicon_kg` (arc-furnace
reduction and Siemens-process purification current) and `quartz_tube_kg`
(arc/resistance heat reaching a temperature no combustion route in this file
reaches) all carry a nonzero `electrical_mj` field of their own, exactly the
way a handful of pre-industrial entries carry a nonzero `thermal_mj` or
`mechanical_mj` today. This is deliberate, not a shortcut: for all three,
the physical requirement is specifically ELECTRICAL (a current, or heat
above what any fuel reaches) rather than a level of energy that happens to
be supplied electrically today, so pricing them straight off `electrical_mj`
lets the CHOICE OF TECHNIQUE mechanism pick whichever route to that
carrier - water wheel and a dynamo, or a solar panel, or (once one exists)
something else - without the entry itself ever deciding. Found but left
alone this round, flagged per CLAUDE.md 3.4 rather than silently fixed: several
OTHER entries still carry a genuinely electrical need under the
`mechanical_mj` name, the same misclassification WHY ELECTRICITY HAS ITS
OWN CARRIER above describes for aluminium: zinc's
electrolysis (`zinc_electrolytic_kg`), tungsten's induction/resistance
sintering (`tungsten_kg`) and calcium carbide's electric-arc furnace
(`calcium_carbide_kg`, whose own yield_basis already says outright "the arc
furnace must reach roughly 2000 C, well above anything a combustion furnace
reaches" while still being carried as `mechanical_mj`). `barium_kg`'s small
`mechanical_mj` figure, by contrast, is a genuine vacuum pump - real shaft
work - and is correctly named already. Reclassifying the three electrical
ones is the same fix as aluminium's, done three more times; it is out of
this round's scope (which named aluminium specifically) and is recorded here
so it is not lost.

WHAT THIS DOES NOT MODEL, LABELLED RATHER THAN HIDDEN. The water-wheel
technique assumes continuous year-round operation (a real wheel is idled by
drought, ice and repair) and treats the SITE - the head and flow of a
particular stretch of river - as free, under the same zero-rent rule that
still covers every extracted material `sim/world/deposits.py` has no named-
deposit list for (see RENT ON EXTRACTED MATERIALS above); a genuine
site-scarcity rent, the way `sim/world/deposits.py` now derives one for the
six ores it covers, would raise this price at
large scale and is future work, not this round's. Ox-muscle mechanical work
is omitted entirely: this file has no priced fodder material (only
wheat_kg, a poor stand-in for a working animal's mostly-hay ration), and
since water already beats human muscle by three orders of magnitude for
every material this round touches, an ox at roughly five times a human's
sustained output would not change which source sets the margin for any of
them - it would only add a segment of the curve nothing here currently
needs. The photovoltaic technique's own insolation figure (a representative
Mediterranean ~5 kWh/m2/day) belongs beside `water_power` and `human_power`
in `data/world/resources.json`'s own constraints block for the same reason
those two live there rather than being invented inline - that file is out
of this round's scope, so the figure is cited directly in
`electrical_mj_photovoltaic`'s own capital_basis instead, flagged there as
where it should eventually move.

CAPITAL IS NOW PRICED (Complaints/32). `data/production/_SCHEMA.md`'s
`capital` field lists the fixed plant a process runs IN - a furnace, a mill,
a chamber - as a build bill in the same physical units this file already
prices: `build_materials`, `build_labour_hours`, a `service_life_years` and
an `annual_output_at_basis`. Amortised cost per unit of output is

    (cost of build_materials + cost of build_labour_hours)
    / (service_life_years * annual_output_at_basis)

summed over every item in the list (a furnace stack and its hearth lining
wear at different rates and are separate items on purpose - see CAPITAL in
the schema) and added to the recipe's cost alongside its ordinary inputs,
labour and rent. It is priced, not looked up: the build bill is costed
through the same solved price vector as everything else, so a capital charge
falls when the materials it is built from get cheaper, exactly like every
other term here. Measured effect on the committed data: a few tenths of a
percent to a few percent of prime cost (pig_iron_kg +1.7%, iron_bar_kg
+0.25%, glass_raw_kg +6.4%) - physical depreciation of long-lived,
high-throughput plant really is a small unit cost, which is a finding, not a
bug to chase; see Complaints/32 for the reasoning and CLAUDE.md 3.1 on not
tuning a number until it looks more familiar.

Capital also introduces the two real cycles Complaints/31 is about:
`iron_bar_kg`'s own hammer fittings are 800 kg of `iron_bar_kg`, and
`pig_iron_kg`'s hearth lining is 3,000 kg of `iron_bar_kg` while `iron_bar_kg`
is made from `pig_iron_kg`. Both are correct physics - real plant is built
partly from its own product - and both only work because
`compute_resolvable_materials` below treats a capital good's
`build_materials` as a dependency for resolvability purposes exactly like an
ordinary input (see `_dependency_materials`), so these cycles are visible to
the same productiveness test as any other.

CHOICE OF TECHNIQUE AND JOINT PRODUCTION, handled by the same rule. Several
materials have more than one recipe (salt from brine or from solar pans;
zinc by direct smelting or by electrolysis) and several recipes yield more
than one material (smelting galena yields lead AND silver; roasting coal
yields carbon AND coal tar). Both are the same underlying question - how much
of a process's cost belongs to a given unit of a given output - and this
script answers both with one mechanism: cost the whole process, then split
that cost across its outputs in proportion to each output's own current price
times its quantity (net-realisable-value allocation, the standard treatment
of joint cost in cost accounting). A single-output recipe is just the case
where one output holds 100% of the value share. Where a material has several
candidate recipes, its price is the CHEAPEST of what each recipe implies for
it - the solver picks the technique a rational producer would pick at current
prices, and because prices move as the solve iterates, technique choice
iterates alongside it exactly as the design doc's Part 2.1 says it must.

JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR ARE NOT REALLY PRICED, AND
THIS SCRIPT SAYS SO RATHER THAN PRINTING THE NUMBER AS IF THEY WERE. Running
the solve and inspecting every joint-production recipe shows the same thing
every time: a MINOR co-product (silver from lead smelting, platinum from
nickel refining, germanium and indium from zinc electrolysis, coal tar from
coke-making) converges to EXACTLY the same price per physical unit as its
DOMINANT co-product, no matter how the price search is seeded. That is not a
finding about silver and platinum being cheap - it is `recipe_cost_and_
allocation`'s net-realisable-value split degenerating to a plain mass split
whenever nothing else in the system independently prices the minor output.
The algebra: at a fixed point, value_i = quantity_i * price_i for every
output of one recipe, and the value split is itself computed FROM those same
prices, so "every output priced identically per unit" is a self-consistent
answer whenever no other equation constrains it - and for these five
materials, nothing else does, because their only OTHER recipe (if any, like
silver's direct patio-amalgamation route) turns out more expensive at the
degenerate price and is never selected. This is the textbook joint-production
result from classical price theory: a system with one process and two goods
has one equation short of pinning down both prices, and closing the gap needs
demand, or a second independent process that actually binds - this dataset
has neither yet. `minor_joint_byproducts_are_unanchored` finds exactly this
set by checking, on the CONVERGED, CHOSEN recipe for each material, whether
it is a joint recipe where this material holds under half the batch's value.
Flagged materials print with a `(*)` and a named warning, in every mode -
their number is a real lower bound on cost (the batch really did cost that
much to run) but not a real relative price, and treating it as one would be
worse than saying plainly that this round cannot separate it out.

CYCLES ARE EXPECTED BY THE ITERATION, AND NOW ACCEPTED BY THE PASS IN FRONT
OF IT TOO (Complaints/31, fixed). Iron needs charcoal; charcoal needs timber
and labour; an axe needs an iron edge. The damped fixed-point iteration below
handles that the same way it handles everything else, by converging to the
prices where the equations agree rather than requiring an acyclic graph. What
the iteration CANNOT do is resolve a material whose every path back through
its own inputs never bottoms out at something with no inputs (an extracted
material, ultimately just labour and zero rent) - a genuine hole in the data,
or a cycle that consumes more of a good than it yields - and
`compute_resolvable_materials` below is the separate graph pass that finds
those before any numeric work starts.

`compute_resolvable_materials` runs a topological-ordering pass first,
adding a recipe's outputs only once every input is already resolvable -
which correctly handles the whole acyclic part of the graph, which is most
of it, but by itself would refuse every genuine cycle (the axe-and-iron
example above included, and a material listing itself among its inputs
(seed corn) worst of all, since that would take everything downstream with
it too). It then finds the strongly connected components of whatever is
left, and tests each one for PRODUCTIVENESS rather than refusing it
outright: a component is resolvable when every dependency from OUTSIDE it
already has a price AND the damped iteration, run on the component alone,
actually contracts to a fixed point instead of growing without bound
(Hawkins-Simon: the input-output matrix restricted to the component has
spectral radius under 1). A component that grows instead of contracting -
consuming more of a good than the cycle yields - is reported by name, the
same way a missing recipe already is; see `_component_is_productive` and
Complaints/31 for the two cases this was built against (the docstring's own
axe/iron example, and self-referencing seed corn) and
`sim/tests/test_price_solver_cycles.py` for the pinned tests.

THE SOLVER NEEDS A NOTION OF WHEN, NOT ONLY OF COST. This is the defect
Complaints/39 records: pricing every technique in `data/production/` on
cost alone, in every scenario, gives cost no date - a 100 AD Roman scenario
prices every one of its three energy carriers off
`electrical_mj_photovoltaic`, and the DATA is right (a panel really is the
cheapest source of electricity at solved prices), but the answer is
nonsense, because nobody in 100 AD has a panel.

The fix is a gate, not a deletion. Each entry may carry `requires_node`: the
tech-tree node that has to be reached before anyone can run that technique
(see WHEN A TECHNIQUE BECOMES AVAILABLE in `data/production/_SCHEMA.md`).
A civilisation's `starting_techs` is a set of exactly those ids, so

    python3 sim/solve_prices.py --civ rome_100ad

filters the entries down to what Rome can actually do and then solves that
smaller system. The whole rest of the mechanism is unchanged: the same
resolvability pass, the same fixed point, the same choice of technique -
choosing now among the techniques that exist rather than among all of them,
which is what choice of technique was always supposed to mean.

Three things this deliberately does NOT do, each because doing it would
hide something:

  - It does not delete the photovoltaic entry. The panel is correct data.
    Removing it would make the Roman answer look right while the tool went
    on silently using Hall-Heroult and the compound steam engine for
    everything else.
  - It does not treat an unclassified entry as universally available. An
    entry with no `requires_node` is DROPPED from a gated solve and counted,
    because the alternative - admitting it - is exactly how the photovoltaic
    panel got into a Roman answer in the first place. An unlabelled entry
    is an unanswered question, and the honest handling of an unanswered
    question is to say how many there are.
  - It does not date anything by year. There is no table mapping techniques
    to centuries anywhere in this file, and there must not be: that would be
    a hardcoded outcome (CLAUDE.md section 3.1). Availability comes from the
    tree's own prerequisite structure and the civilisation's own starting
    set, both of which are initial conditions rather than results.

HOW EXPENSIVE IS THIS, ACTUALLY - MEASURED, BECAUSE IT DECIDES THE WIRING.
The question that matters for putting this in the engine is not how long one
solve takes but how OFTEN one is needed, and the answer is: far less often
than "every turn", because almost nothing in the tree is a gate.

    full ungated solve      0.673 s   1076 iterations   183 materials
    gated solve (rome)      0.371 s   1076 iterations   107 materials
    distinct nodes used as a gate   82 of 2864 in the tree, 2.9%

Only 82 nodes can change the answer. Unlocking a node has about a 97% chance
of not being a gate at all, so a year in which a hundred nodes complete will
usually need NO re-solve, and can need at most as many as there are newly
unlocked gates. Over an entire game the number of distinct solves is bounded
by 82 and in practice is far below it.

So the engine should key a cached price vector on the set of GATE nodes held
- not on the full technology set, which changes constantly and would defeat
the cache - and re-solve only when that set changes. Under that scheme the
per-turn cost is a set comparison, and the 0.37 s is paid a few dozen times
across a whole game rather than once a turn.

The 1076 iterations are a separate matter and are not currently a problem.
Damping is 0.5 against a 1e-10 tolerance, which is conservative; if the solve
ever does become hot, that is the knob, not the architecture.

WHAT A GATED SOLVE COSTS. Fewer techniques means fewer materials have any
path to a price at all, so a gated run resolves strictly fewer materials
than an ungated one and reports the difference. That is the correct answer
rather than a regression: a material no Roman could make does not have a
Roman price, and printing one for it was the bug.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from sim.validate_production import load_production, materials_the_tree_consumes  # noqa: E402

# THIS FILE IS A PURE COMPOSITION POINT over two sibling modules - the same
# shape sim/engine/society.py and sim/engine/economy.py already use for the
# same reason (see either one's own module docstring): every name below is
# defined in one of the two sibling modules, not here, so that
# `python3 sim/solve_prices.py ...`, `from sim import solve_prices`, and
# every existing `solve_prices.<name>` call site keep working unmodified.
#
#     sim/solve_prices_core.py     the price algebra: resolvability, the
#                                   ore and land rent mechanisms, capital
#                                   and energy cost, choice of technique,
#                                   and the damped fixed-point `solve` loop
#     sim/solve_prices_report.py   the reporting front end: `print_why`,
#                                   the default price table, the `--compare`
#                                   report, and the CLI's own `main`
#
# This docstring above - THE mechanism essay - lives here rather than with
# either sibling: every "see the module docstring" comment in both sibling
# files means THIS docstring, and splitting it apart by topic would break
# every one of those cross references for no benefit.
from sim.solve_prices_core import (                  # noqa: E402
    CAPABILITY_CAP_FIELDS,
    CONVERGENCE_TOLERANCE,
    DAMPING_FACTOR,
    DEFAULT_LAND_CIVILIZATION,
    ENERGY_CARRIER_FIELDS,
    GROWTH_BOUND_HOURS,
    INITIAL_PRICE_GUESS_HOURS,
    MAXIMUM_ITERATIONS,
    NUMERAIRE_TRADE,
    RENT_BEARING_ORE_MATERIALS,
    THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C,
    _build_material_dependency_graph,
    _capability_graded_price,
    _component_is_productive,
    _dependency_materials,
    _entries_relevant_to_component,
    _grow_resolvable_by_topological_pass,
    _has_external_anchor,
    _meets_capability_floor,
    _pending_entries,
    _strongly_connected_components,
    build_producers_index,
    capability_floor_by_carrier,
    capability_price_for_requirement,
    capability_required_grades,
    compute_resolvable_materials,
    land_rent_hours_per_iugerum,
    load_starting_technologies,
    minor_joint_byproducts_are_unanchored,
    recipe_cost_and_allocation,
    rent_hours_per_kg_by_ore_material,
    solve,
    techniques_available_to,
    wage_ratios_by_trade,
)
from sim.solve_prices_report import (                # noqa: E402
    _apply_era_gate,
    _default_capability_band_price_by_carrier,
    _next_recursion_targets,
    _print_capital,
    _print_convergence_summary,
    _print_default_report_header,
    _print_energy,
    _print_energy_gap,
    _print_energy_summaries,
    _print_extraction_rent_explanation,
    _print_inputs,
    _print_joint_output_note,
    _print_labour,
    _print_land,
    _print_price_table,
    _print_rejected_techniques,
    _print_rent_summary,
    _print_rent_this_batch,
    _print_unanchored_byproducts_summary,
    _print_unproductive_cycles,
    _print_unpriceable_materials,
    _print_value_share_or_total,
    _resolved_recipe_id_or_none,
    _run_compare_report,
    _run_default_report,
    _run_why_report,
    format_hours,
    main,
    print_why,
)

if __name__ == "__main__":
    sys.exit(main())
