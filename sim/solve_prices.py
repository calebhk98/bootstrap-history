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
rent there is still not "no answer" - it is the same honest lower bound
this section used to claim for everything: whatever the true price is, it
is at least the labour it takes. Tag: HEURISTIC, not a physical fact,
tracked against Milestone 1's provenance ledger. Forest timber and every
other GROWN or land-limited material used to belong on this list too -
see RENT ON GROWN AND LAND-LIMITED MATERIALS immediately below for why it
no longer does.

RENT ON GROWN AND LAND-LIMITED MATERIALS (Complaints/49 - "land rent
reaches no crop"). `sim/world/land.py` computes a real, per-civilization
Ricardian rent on arable land - both margins of it, extensive (better
land against worse) and intensive (diminishing returns to more labour on
the same ground) - and `land_rent_hours_per_iugerum` above turns that into
`iugerum_land`'s own solved price. Before this round, nothing else in
`data/production/` ever looked that price up: `wheat_kg` had `inputs={}`,
so its price was mathematically guaranteed to be labour cost alone,
whatever an iugerum was worth, and the same was true of wool, timber,
olives, wine and every other material a recipe's own prose said came
"from arable land", "from pasture" or "from forest" without a single
recipe actually consuming any. Two rounds of rent calculation reached no
price anybody paid. This is the fix.

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

ENERGY IS NOW PRICED, AS THREE MARKETS - THERMAL, MECHANICAL AND ELECTRICAL -
CONNECTED BY CONVERSION RECIPES, NOT TWO MARKETS WITH ELECTRICITY GLUED TO
ONE OF THEM (Complaints/32's third gap, then a real defect the stakeholder
found in how that gap was closed - see THE ALUMINIUM DEFECT below). Every
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
                    ELECTRICAL_MJ entry and THE ALUMINIUM DEFECT below
                    answer honestly rather than assume: with this round's
                    `electrical_mj_photovoltaic` included, the motor route
                    currently wins, for reasons that entry explains and
                    flags as resting on an admittedly incomplete cost.

    electrical_mj   electricity - the one carrier with no shaft and no flame
                    required to reach it at all (see THE ALUMINIUM DEFECT).
                    Priced via electrical_mj_dynamo (mechanical energy
                    through a dynamo) or electrical_mj_photovoltaic (photons,
                    directly, through a solar panel's fixed capital and
                    NOTHING ELSE) - whichever the solved prices make
                    cheapest. Also consumed directly, as electrolysis
                    current or as arc/resistance heat, by any recipe whose
                    own `electrical_mj` field says it needs some (aluminium_kg
                    and silicon_kg this round; see WHICH ENTRIES USE
                    ELECTRICAL_mj DIRECTLY below).

THE ALUMINIUM DEFECT (found by the stakeholder, fixed this round). The
previous version of this file carried aluminium's 46,000 MJ/tonne of
Hall-Heroult electrolysis current as `mechanical_mj`, on the reasoning
"electricity is a carrier, not a source, so it must bottom out in whatever
turns the dynamo." That reasoning is right for a waterwheel-and-dynamo
civilisation and wrong in general: a photovoltaic cell makes electricity
from photons with no shaft anywhere in the chain, and so does a
thermoelectric couple, a battery or a fuel cell. Forcing every use of
electricity through `mechanical_mj` made a civilisation with arbitrarily
cheap solar panels structurally unable to ever make cheap aluminium, which
is not a fact about aluminium - it is a fact about a schema that had only
two carriers and picked the wrong one to call "electricity." Fixed by giving
electricity its own carrier (`electrical_mj`) and letting `aluminium_kg`
draw on THAT, with `mechanical_mj` reaching it only through the
`electrical_mj_dynamo` conversion below, exactly like every other route
would.

THE CHECK, RUN HONESTLY RATHER THAN ASSUMED TO PASS. The expectation going
in was that nothing should change except by a dynamo's own conversion loss,
since this file has no combustion engine cheap enough to beat a water
wheel (see mechanical_mj's own note above) and therefore no OTHER route to
electricity worth considering. Excluding `electrical_mj_photovoltaic` and
re-solving confirms exactly that: `electrical_mj` prices at 0.00388 h/MJ via
`electrical_mj_dynamo` (against `mechanical_mj`'s own 0.00258 - a ~50%
premium for the dynamo's conversion loss, its own labour and its own
amortised build, all individually modest and all pointing the same
direction), and aluminium_kg prices at roughly 15-16% more than before the
fix (0.442 h/kg against the old 0.382), squarely "roughly what it is now
plus a dynamo's losses." So the mechanism is right.

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
entirely - exactly the case THE ALUMINIUM DEFECT above says the old schema
could never represent. This is the mechanism doing its job, not a defect,
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

TEMPERATURE, AND WHY A SINGLE SHARED FLOOR WAS ITSELF A BUG (Complaints/44,
then a second defect found by the stakeholder reasoning about the first
fix rather than by running anything - see Complaints/44's own text for the
friction incident this paragraph continues from). A megajoule of heat is
not fungible across temperature: one MJ at 200 C cannot do what one MJ at
1600 C can, which is the whole reason a bloomery cannot melt iron however
much charcoal is fed into it. The first round's fix gave every
thermal_mj-supplying technique a `temperature_reached_c` and computed ONE
shared floor for the whole pool - the LARGER of the pool's own default
(`THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C`) and whatever the single
HOTTEST active consumer stated it needed - and excluded any technique
that fell short of that one number. That correctly kept a warm bearing
out of England's forges, and it was ALSO wrong in a way nothing had yet
exercised: a single global floor means the hottest consumer in the WHOLE
ECONOMY sets the bar for every other use of the carrier, however cool.
Concretely, on the data as it stood, the three `mechanical_mj_heat_
engine_*` entries' own stated 1000 C requirement already raised the
SHARED floor to 1000 C for every thermal_mj consumer in the file, plaster
and rosin (150-160 C, per their own `yield_basis`) included - harmless
today only because charcoal and coal both happen to clear 1100 C anyway,
not because the mechanism was right. Invent a technique that reaches
2500 C anywhere in the economy (a genuinely hot process, nothing to do
with brick-firing) and the SAME shared-floor logic would raise the pool's
floor to 2500 C and lock charcoal and coal - both 1100 C, comfortably hot
enough to fire a brick, glaze a pot or melt glass - out of every thermal_
mj use in the file, brick-firing included. That is the stakeholder's own
example (a fission-hot process should not disqualify existing coal
burning from melting iron) and the mirror image of it (a cheap, merely-
warm source should not stop being usable for the modest jobs it was
already doing, the moment something hotter is invented elsewhere) - both
follow from the same defect: a shared floor conflates "what the hottest
job needs" with "what every job may use."

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
plus each ACTIVE consumer's own `temperature_needed_c`, exactly as
before); `capability_price_for_requirement` then solves, separately, for
the cheapest technique that clears EACH one of those requirements, at
this round's own prices - so a 2500 C requirement gets its own answer
(today: `thermal_mj_electrical_resistance`, the only technique in this
file that reaches it) without disturbing the 1000 C answer the heat
engines get (charcoal or coal, whichever is cheaper - unchanged) or the
700 C answer everything else gets (also charcoal or coal - also
unchanged). A recipe that states no requirement at all still just pays
`thermal_mj`'s own ordinary solved price - the cheapest technique
clearing the universal default floor, which is ALL `capability_floor_
by_carrier` computes now (see its own docstring: it no longer looks at
what any consumer needs, because a consumer's own need is graded
separately). `thermal_mj_friction` is excluded from every one of these
grades it cannot reach (its own 100 C never clears even the 700 C
default), the same physical fact as before - the ONLY behaviour change
this round is that a hot grade existing, or ceasing to exist, no longer
touches a cooler grade's own answer.

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
OTHER entries still carry a genuinely electrical need under the old
`mechanical_mj` name for the same reason aluminium used to - zinc's
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

That pass used to add a recipe's outputs only once every input was already
resolvable, which is a topological ordering and refuses every genuine cycle
- the axe-and-iron example above included, and a material listing itself
among its inputs (seed corn) worst of all, since that took everything
downstream with it too. It now runs that same ordering pass first (it
correctly handles the whole acyclic part of the graph, which is most of it),
then finds the strongly connected components of whatever is left, and tests
each one for PRODUCTIVENESS rather than refusing it outright: a component is
resolvable when every dependency from OUTSIDE it already has a price AND the
damped iteration, run on the component alone, actually contracts to a fixed
point instead of growing without bound (Hawkins-Simon: the input-output
matrix restricted to the component has spectral radius under 1). A component
that grows instead of contracting - consuming more of a good than the cycle
yields - is reported by name, the same way a missing recipe already was; see
`_component_is_productive` and Complaints/31 for the two reproductions this
was built against (the docstring's own axe/iron example, and self-referencing
seed corn) and `sim/tests/test_price_solver_cycles.py` for the pinned tests,
inverted now that the pass accepts what it should.

THE SOLVER NOW HAS A NOTION OF WHEN, AND DID NOT BEFORE. This is the defect
Complaints/39 records, and it was found by reading a run rather than by
reasoning about the code: a 100 AD Roman scenario came back pricing every
one of its three energy carriers off `electrical_mj_photovoltaic`. The data
was right - a panel really is the cheapest source of electricity at solved
prices - and the answer was still nonsense, because nobody in 100 AD has a
panel. Every technique in `data/production/` competed on cost alone, in
every scenario, and cost alone has no date on it.

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
import argparse
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# REPO_ROOT, not just HERE, has to be on sys.path for `from sim.world import
# deposits` below: `sim` is a namespace package rooted at the repository, the
# same one sim/tests/__main__.py's own docstring explains, and this file is
# normally launched as a bare script (`python3 sim/solve_prices.py`), which
# only puts HERE (sim/ itself) on sys.path automatically.
sys.path.insert(0, REPO_ROOT)
import simulator                                # noqa: E402  (see sys.path above)
from validate_production import load_production, materials_the_tree_consumes  # noqa: E402
from sim.world import deposits                  # noqa: E402  (RENT ON EXTRACTED MATERIALS)
from sim.world import land                      # noqa: E402  (RENT ON ARABLE LAND)

NUMERAIRE_TRADE = "labourer"

# The three energy carriers (see ENERGY in this module's docstring). Named
# once here rather than spelled out at each of the three call sites that
# used to hand-write the pair, so that adding `electrical_mj` this round
# could not silently miss one of them - a real risk a bare tuple repeated
# three times invites.
ENERGY_CARRIER_FIELDS = ("thermal_mj", "mechanical_mj", "electrical_mj")

# PHYSICAL CAPABILITY CAPS (Complaints/44 - see TEMPERATURE in this
# module's own docstring for the full defect and the reasoning behind the
# number below). data/tech_tree.json's own `cap_heat_0700` node -
# "Sustained 700 C (pottery kiln)... Already available wherever there is
# an updraught pottery kiln, wood fired. Free starting capability. Glazes,
# bricks, lime, glass working" - carries no prerequisite at all (`pre:
# []`), so it is the lowest sustained-heat capability the tree considers
# universal: every civilisation this file prices for, however primitive,
# is assumed to already have SOME way to fire a pot or a brick. That is
# the genuine physical floor for what this file's own thermal_mj
# techniques already claim to be delivering (thermal_mj_charcoal's own
# yield_basis: "a still, a carbonating tower, a calciner" - real furnace
# apparatus, not ambient warmth), so it is reused here rather than an
# invented number - exactly the tree's own vocabulary, per the task that
# added this mechanism, instead of a parallel scale.
THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C = 700.0

# {carrier_material: (reached_field, needed_field, default_floor)}. A
# technique that OUTPUTS an energy carrier may state, on itself, the
# ceiling of some physical dimension it can reach (`temperature_reached_c`
# today); a recipe that CONSUMES that carrier may state, on itself, the
# floor it needs on the same dimension (`temperature_needed_c`). Both
# fields are optional - an entry that states neither is unconstrained,
# exactly as it was before this mechanism existed (see this file's own
# `solve`, `capability_floor_by_carrier` and `capability_price_for_
# requirement` below, and TEMPERATURE in the module docstring for why
# grading is now PER CONSUMER rather than one shared floor). Keyed by
# carrier rather than hand-written at each call site for the same reason
# ENERGY_CARRIER_FIELDS above is: so a second physical dimension - torque,
# pressure, whatever a future stakeholder names next - slots in as one
# more entry here, read by the same functions, rather than a second,
# parallel, hand-rolled comparison. See the module docstring's TEMPERATURE
# section for the worked example (a torque cap on mechanical_mj) and this
# task's own report for the argument in full.
CAPABILITY_CAP_FIELDS = {
    "thermal_mj": ("temperature_reached_c", "temperature_needed_c",
                   THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C),
}


def capability_floor_by_carrier(production_entries):
    """{carrier_material: the carrier's own UNIVERSAL default floor} - one
    entry per carrier named in CAPABILITY_CAP_FIELDS.

    THIS IS DELIBERATELY NOT "the largest requirement any consumer states"
    any more (see TEMPERATURE in the module docstring for why that WAS
    this function's behaviour, and why it was itself a bug: a single
    shared floor lets the hottest consumer anywhere in the economy lock
    every cooler consumer out of the cheap technique it could already
    use, and lets a newly cheap cold source push a hot consumer's own
    requirement down to nothing it never asked for). A specific
    consumer's own stated requirement is now graded separately by
    `capability_price_for_requirement` below, so this function only has
    to return the one number every technique claiming to supply the
    carrier is checked against regardless of what any consumer needs -
    the free, universal minimum (THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C's
    own citation) - which decides `thermal_mj`'s own ordinary pool price,
    the one every consumer with no stated requirement of its own pays.

    `production_entries` is kept as a parameter, and unused, so every
    existing call site (and `_meets_capability_floor` below, which takes
    this function's own return value) is unaffected by this round's
    change in what the function computes.
    """
    return {carrier: default_floor
            for carrier, (_reached_field, _needed_field, default_floor)
            in CAPABILITY_CAP_FIELDS.items()}


def capability_required_grades(production_entries):
    """{carrier_material: sorted tuple of every distinct requirement this
    era's own (possibly gated) `production_entries` actually states for
    that carrier} - the carrier's own universal default floor, ALWAYS
    included (every civilisation this file prices for already clears
    it), plus each ACTIVE consumer's own `needed_field` value: an entry
    that draws a nonzero amount of the carrier (`entry.get(carrier)` is
    truthy) AND states a requirement on it (`entry.get(needed_field) is
    not None`) - "no stated requirement" still means exactly that, not
    zero, exactly as `capability_floor_by_carrier` used to describe for
    its own single shared number.

    This is the PER-CONSUMER GRADING this round's fix is built on (see
    TEMPERATURE in the module docstring): every distinct value here gets
    its OWN price from `capability_price_for_requirement`, computed
    independently, so a 2500 C requirement existing somewhere in the
    economy neither raises nor lowers the price a 1000 C or a 700 C
    requirement gets - each is simply one more entry in the set this
    function returns.
    """
    required_by_carrier = {}
    for carrier, (_reached_field, needed_field, default_floor) in CAPABILITY_CAP_FIELDS.items():
        required_values = {default_floor}
        for entry in production_entries.values():
            if entry.get(carrier) and entry.get(needed_field) is not None:
                required_values.add(entry[needed_field])
        required_by_carrier[carrier] = tuple(sorted(required_values))
    return required_by_carrier


def capability_price_for_requirement(carrier, required_value, production_entries,
                                     current_prices, wage_by_trade,
                                     rent_hours_per_kg_by_material=None):
    """(price, recipe_id) for the CHEAPEST technique that both supplies
    `carrier` and clears `required_value` on the physical dimension
    CAPABILITY_CAP_FIELDS grades it by, costed at this round's own
    `current_prices` - or None if nothing eligible resolves this round
    (should not happen for any value `capability_required_grades` itself
    produced, since the default floor is always clearable by this file's
    own PRIMARY techniques, but a caller must still handle it the same
    way an ordinary unpriceable material is handled elsewhere in this
    file: propagate the failure rather than guess a price).

    THIS is the mechanism that replaces the single shared floor: called
    once per distinct required value (see `capability_required_grades`),
    not once per carrier, so a hot requirement and a cool one sharing the
    same carrier name get independently the cheapest technique that
    actually clears EACH one, rather than the cheapest technique that
    clears whichever requirement happens to be largest.

    A candidate technique that states no reach at all on this dimension
    is treated as unconstrained (it clears every requirement) - the same
    "no stated value, no new behaviour" rule `_meets_capability_floor`
    already applies; today every PRIMARY thermal_mj technique states one,
    so this only matters for a future carrier or a future technique added
    without one.

    Deliberately does NOT thread a capability-graded price into this
    inner cost calculation for the CANDIDATE techniques themselves (see
    `recipe_cost_and_allocation`'s own `capability_band_price_by_carrier`
    parameter) - a producer of one capped carrier drawing on ANOTHER
    capped carrier with its own stated requirement would need that too,
    but no entry in this file does that today (the only other carrier
    CAPABILITY_CAP_FIELDS could someday grade, `mechanical_mj`, is not
    graded yet - see the module docstring's torque example), so this is
    left as a plain `current_prices` lookup for now rather than solved
    for a case that does not exist. Tag: GAP, not a heuristic, per
    CLAUDE.md 3.4 - the day a second graded carrier feeds a first one,
    this function's own candidate costing needs the same banded lookup
    `recipe_cost_and_allocation` already has.
    """
    reached_field = CAPABILITY_CAP_FIELDS[carrier][0]
    best = None
    for recipe_id, entry in production_entries.items():
        outputs = entry.get("outputs") or {}
        if carrier not in outputs:
            continue
        reached = entry.get(reached_field)
        if reached is not None and reached < required_value:
            continue
        result = recipe_cost_and_allocation(
            recipe_id, entry, current_prices, wage_by_trade,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
        if result is None:
            continue
        _total_cost, output_prices = result
        price = output_prices[carrier]
        if best is None or price < best[0]:
            best = (price, recipe_id)
    return best


def _capability_graded_price(carrier, entry, current_prices,
                             capability_band_price_by_carrier):
    """The price a SPECIFIC consuming `entry` pays for `carrier` this
    round - PER-CONSUMER GRADING (see TEMPERATURE in the module
    docstring). An entry that states its own requirement on the
    dimension CAPABILITY_CAP_FIELDS grades `carrier` by pays whatever the
    cheapest technique clearing THAT requirement costs, read from
    `capability_band_price_by_carrier` (built once per round by `solve`,
    one entry per value `capability_required_grades` found - see
    `capability_price_for_requirement`); an entry that states no
    requirement - the overwhelming majority of every energy carrier's
    consumers - pays the carrier's own ordinary solved price
    (`current_prices[carrier]`), exactly as before this mechanism
    existed. Returns None (propagating an unpriceable recipe, exactly
    like a missing input price elsewhere in this file) only if the
    entry's own stated requirement cannot be met by anything this round -
    never by silently falling back to the wrong grade's price.

    `capability_band_price_by_carrier` is None outside `solve`'s own
    iteration (the one-off ore and wheat base-price calls in
    `rent_hours_per_kg_by_ore_material` and `land_rent_hours_per_iugerum`,
    neither of which ever states a capped-carrier requirement) and for
    any carrier CAPABILITY_CAP_FIELDS does not grade at all, in which
    case this always falls through to the plain, ungraded lookup.
    """
    capped = CAPABILITY_CAP_FIELDS.get(carrier)
    if capped and capability_band_price_by_carrier:
        _reached_field, needed_field, _default_floor = capped
        required_value = entry.get(needed_field)
        if required_value is not None:
            band = capability_band_price_by_carrier.get(carrier) or {}
            graded = band.get(required_value)
            return graded[0] if graded is not None else None
    return current_prices.get(carrier)


def _meets_capability_floor(material, entry, floor_by_carrier):
    """True unless `material` is a capability-capped carrier (see
    CAPABILITY_CAP_FIELDS) and `entry`'s own stated reach on that
    dimension falls short of `floor_by_carrier[material]`. An entry that
    states no reach at all (most entries, including every material that
    is not itself an energy-carrier-supplying technique) is treated as
    unconstrained - the same "no stated value, no new behaviour" rule
    this mechanism applies throughout.

    Used two ways: with `capability_floor_by_carrier`'s own output, to
    decide which technique wins the carrier's ORDINARY pool price (what
    an unlabelled consumer pays); and, inside `capability_price_for_
    requirement`'s own candidate loop in spirit (that function inlines
    the same comparison against a single `required_value` rather than a
    per-carrier dict, since it is testing one specific requirement at a
    time rather than every carrier's own floor at once).
    """
    capped = CAPABILITY_CAP_FIELDS.get(material)
    if capped is None:
        return True
    reached_field, _needed_field, _default_floor = capped
    reached = entry.get(reached_field)
    if reached is None:
        return True
    return reached >= floor_by_carrier[material]


# Damped Jacobi fixed-point iteration: every material's next price is a blend
# of its old price and what the current round's cheapest technique implies,
# so a technique flipping from one iteration to the next (a real possibility
# early on, when every price still carries the same seed guess) nudges the
# price rather than slamming it, which is what "damped" buys over a raw
# reassignment. 0.5 was not tuned against an outcome - it is the textbook
# midpoint - and the run below reports whether it actually converges rather
# than assuming a coefficient this arbitrary must be fine.
DAMPING_FACTOR = 0.5
MAXIMUM_ITERATIONS = 2000
CONVERGENCE_TOLERANCE = 1e-10

# Every price starts equal, in labour-hours, before the first iteration.
# The seed value only matters for how many iterations convergence takes and
# for which technique looks cheapest in round one (see the joint-production
# note above); it does not bias where the fixed point ends up, because a
# fixed point is defined by the equations agreeing with each other, not by
# where the search started.
INITIAL_PRICE_GUESS_HOURS = 1.0

# Used only by the cycle-productiveness test in compute_resolvable_materials:
# a price the restricted iteration crosses only if the component is growing
# without bound rather than converging. Not a plausible real price for
# anything - see _component_is_productive.
GROWTH_BOUND_HOURS = 1e9


def wage_ratios_by_trade(prices_json):
    """{trade: hours of unskilled labour one hour of this trade is worth}.

    `prices.json`'s wage table is denarii per hour, one static number per
    trade with no notion of unskilled labour as a unit. Dividing every rate
    by the unskilled (`labourer`) rate turns it into what the design doc
    calls the numeraire: `wage_of("labourer")` is 1.0 by construction, and
    every other trade is stated as how many labourer-hours it is worth,
    which is a ratio the denarii happen to cancel out of.
    """
    wage_table = prices_json["wage_rates_denarii_per_hour"]
    unskilled_rate = wage_table[NUMERAIRE_TRADE]["rate"]
    return {trade: entry["rate"] / unskilled_rate
            for trade, entry in wage_table.items()
            if not trade.startswith("_")}


def load_starting_technologies(civilization_id):
    """The set of tech-tree node ids a civilization begins the game holding.

    This is read straight from `data/civilizations/<id>.json`'s
    `starting_techs`, which is an INITIAL CONDITION - what this society has
    already worked out by the year it starts in - and so is exactly the kind
    of input CLAUDE.md section 3.1 allows. It is not a schedule of when
    techniques were invented; there is no such table here and there must not
    be one.
    """
    path = os.path.join(HERE, os.pardir, "data", "civilizations",
                        "%s.json" % civilization_id)
    if not os.path.exists(path):
        available = sorted(name[:-len(".json")]
                           for name in os.listdir(os.path.dirname(path))
                           if name.endswith(".json") and not name.startswith("_"))
        raise FileNotFoundError(
            "no civilization %r - have: %s" % (civilization_id, ", ".join(available)))
    with open(path) as handle:
        civilization = json.load(handle)
    return set(civilization.get("starting_techs") or [])


def techniques_available_to(production_entries, reached_nodes):
    """Split the production entries into what this era can run and what it cannot.

    Returns (available, unreached, unclassified) - the first a dict in the
    same shape as `production_entries`, the other two sorted lists of recipe
    ids, kept apart because they mean different things and want different
    responses:

      unreached    - the entry names a node this civilization has not
                     reached. Working as intended. A Roman cannot electrolyse
                     zinc and the solve should not offer to.
      unclassified - the entry carries no `requires_node` at all, so nobody
                     has said when it becomes available. Dropped, because
                     admitting it is precisely how a photovoltaic panel ended
                     up pricing Roman electricity (Complaints/39), and
                     counted, because a silent drop is how that stayed
                     invisible for as long as it did.

    `requires_node: null` is a third, deliberate state: available with no
    technology whatever - gathering firewood, quarrying stone, growing wheat.
    It is admitted to every era, including the earliest.
    """
    available, unreached, unclassified = {}, [], []
    for recipe_id, entry in production_entries.items():
        if "requires_node" not in entry:
            unclassified.append(recipe_id)
            continue
        required = entry["requires_node"]
        if required is None or required in reached_nodes:
            available[recipe_id] = entry
        else:
            unreached.append(recipe_id)
    return available, sorted(unreached), sorted(unclassified)


def build_producers_index(production_entries):
    """{material_key: [recipe_id, ...]} - every recipe that yields it.

    A recipe's id is not always the material it makes: `salt_solar_kg` and
    `salt_brine_kg` both yield `salt_kg`, and `zinc_electrolytic_kg` yields
    `zinc_kg` plus two byproducts that have no recipe of their own. Building
    this index from `outputs` rather than assuming id-equals-output is what
    makes both choice of technique and joint production visible at all - see
    the module docstring.
    """
    producers_of = collections.defaultdict(list)
    for recipe_id, entry in production_entries.items():
        for material_key in (entry.get("outputs") or {}):
            producers_of[material_key].append(recipe_id)
    return dict(producers_of)


def _dependency_materials(entry):
    """Every material one recipe's price computation needs a price FOR:
    its ordinary process `inputs`, plus, now that capital is wired in (see
    the module docstring's CAPITAL section), every capital good's own
    `build_materials`, plus, now that energy is wired in (see ENERGY),
    `thermal_mj` and/or `mechanical_mj` themselves whenever the entry needs
    a nonzero amount of either, plus, now that land is wired in (see RENT ON
    GROWN AND LAND-LIMITED MATERIALS), `iugerum_land` itself whenever the
    entry states a nonzero `land_iugera_years`. Resolvability has to see all
    four, or a capital-only cycle - `iron_bar_kg` priced partly in
    `iron_bar_kg`, via its own finery hammer's iron fittings - or an energy
    or land dependency that happened not to resolve, would never appear in
    the graph that decides whether a price exists at all.
    """
    dependencies = set((entry.get("inputs") or {}).keys())
    for capital_good in (entry.get("capital") or []):
        dependencies.update((capital_good.get("build_materials") or {}).keys())
    for energy_key in ENERGY_CARRIER_FIELDS:
        if entry.get(energy_key):
            dependencies.add(energy_key)
    if entry.get("land_iugera_years"):
        dependencies.add("iugerum_land")
    return dependencies


def _grow_resolvable_by_topological_pass(production_entries, resolvable):
    """Add a recipe's outputs once every dependency is already resolvable,
    repeated until nothing new is added. This is a topological-order
    construction, so it is exactly right for the acyclic part of the graph
    (the great majority of it) and refuses every genuine cycle by
    construction - which is why `compute_resolvable_materials` runs it only
    as a first pass, then hands whatever it could not reach to the
    strongly-connected-component productiveness test below. `resolvable` is
    mutated in place so a cycle accepted by that test can call this again
    and let anything waiting only on it cascade through the same loop.
    """
    added_this_pass = True
    while added_this_pass:
        added_this_pass = False
        for entry in production_entries.values():
            outputs = entry.get("outputs") or {}
            if not outputs or all(output in resolvable for output in outputs):
                continue
            if all(dependency in resolvable for dependency in _dependency_materials(entry)):
                for output in outputs:
                    if output not in resolvable:
                        resolvable.add(output)
                        added_this_pass = True


def _pending_entries(production_entries, resolvable):
    """Entries with at least one output the topological pass above could not
    reach - the residual the strongly-connected-component pass runs over."""
    return {recipe_id: entry for recipe_id, entry in production_entries.items()
            if (entry.get("outputs") or {})
            and not all(output in resolvable for output in entry["outputs"])}


def _build_material_dependency_graph(pending_entries, resolvable):
    """{material: {materials it still depends on}}, over every output any
    pending entry still needs to resolve, restricted to dependencies that
    are not already resolved - a resolved dependency is a boundary
    condition for the productiveness test below, not part of the cycle
    structure, so it is not an edge here.
    """
    graph = collections.defaultdict(set)
    for entry in pending_entries.values():
        outputs = entry.get("outputs") or {}
        still_needed_outputs = [output for output in outputs if output not in resolvable]
        remaining_dependencies = [dependency for dependency in _dependency_materials(entry)
                                  if dependency not in resolvable]
        for output in still_needed_outputs:
            graph[output]  # a node even if this entry alone has no remaining dependency
            graph[output].update(remaining_dependencies)
    return graph


def _strongly_connected_components(graph):
    """Tarjan's algorithm, iterative to avoid a recursion limit on a large
    residual graph. Returns components such that if a component depends on
    another (an edge leaves it and lands somewhere else in the graph), the
    component it depends on is always emitted FIRST - so a single pass over
    the result can decide each component using only what earlier components,
    or the pre-existing resolved set, already settled.
    """
    next_index = [0]
    index_of = {}
    lowlink_of = {}
    on_stack = set()
    stack = []
    components = []

    for start in graph:
        if start in index_of:
            continue
        call_stack = [(start, iter(graph.get(start, ())))]
        index_of[start] = lowlink_of[start] = next_index[0]
        next_index[0] += 1
        stack.append(start)
        on_stack.add(start)

        while call_stack:
            node, neighbours = call_stack[-1]
            descended = False
            for neighbour in neighbours:
                if neighbour not in graph:
                    # Nothing in the residual graph depends on THIS - a
                    # dead end (a missing production entry, reported
                    # separately by the caller), not part of any cycle.
                    continue
                if neighbour not in index_of:
                    index_of[neighbour] = lowlink_of[neighbour] = next_index[0]
                    next_index[0] += 1
                    stack.append(neighbour)
                    on_stack.add(neighbour)
                    call_stack.append((neighbour, iter(graph.get(neighbour, ()))))
                    descended = True
                    break
                elif neighbour in on_stack:
                    lowlink_of[node] = min(lowlink_of[node], index_of[neighbour])
            if descended:
                continue

            call_stack.pop()
            if call_stack:
                parent = call_stack[-1][0]
                lowlink_of[parent] = min(lowlink_of[parent], lowlink_of[node])
            if lowlink_of[node] == index_of[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(component)
    return components


def _entries_relevant_to_component(production_entries, component, resolved_so_far):
    """Recipes usable when testing whether `component` is productive: every
    one of the recipe's outputs must lie inside the component (a recipe that
    also makes something outside it is not part of this cycle), and every
    dependency must already be resolved OR be another member of the same
    component - the only kind of "not yet resolved" a productiveness test is
    allowed to lean on. Anything else is a hole this component cannot paper
    over, and is reported as such by the caller.
    """
    relevant = {}
    for recipe_id, entry in production_entries.items():
        outputs = entry.get("outputs") or {}
        if not outputs or not all(output in component for output in outputs):
            continue
        if all(dependency in component or dependency in resolved_so_far
               for dependency in _dependency_materials(entry)):
            relevant[recipe_id] = entry
    return relevant


def _has_external_anchor(entry, resolved_so_far):
    """True if this recipe's cost includes something that is NOT another
    member of its own cycle: ordinary labour, capital build-labour, a
    material dependency that is already resolved (ultimately an extracted
    good, priced at labour plus zero rent), or land (ultimately priced by
    the Ricardian rent on `iugerum_land`, another extracted good in
    everything but name). A cycle where every relevant recipe fails this
    never bottoms out in labour or an extracted good at all - see the
    module docstring's CYCLES section - so there is nothing to price it
    FROM, independent of whether the arithmetic happens to converge.
    """
    if sum((entry.get("labour_hours") or {}).values()) > 0:
        return True
    if any(dependency in resolved_so_far for dependency in (entry.get("inputs") or {})):
        return True
    for capital_good in (entry.get("capital") or []):
        if sum((capital_good.get("build_labour_hours") or {}).values()) > 0:
            return True
        if any(material in resolved_so_far
               for material in (capital_good.get("build_materials") or {})):
            return True
    if entry.get("land_iugera_years") and "iugerum_land" in resolved_so_far:
        return True
    return False


def _component_is_productive(component, production_entries, resolved_so_far,
                             rent_hours_per_kg_by_material=None):
    """Test the productiveness condition (Hawkins-Simon: the input-output
    matrix restricted to `component` has spectral radius under 1) the same
    way the module docstring says the design should work it out - by
    literally running the damped Jacobi iteration `solve()` uses below,
    restricted to this component, with every material outside it pinned at a
    nominal placeholder price.

    A placeholder is valid here because whether the restricted map CONTRACTS
    does not depend on it: for a single-output recipe the update rule is
    affine in prices (materials cost is linear in input prices; labour and
    rent are constants), so contraction is a property of the coefficients on
    component-internal materials alone. Joint-output recipes add a genuine
    nonlinearity through value-share allocation; this still runs the real
    `recipe_cost_and_allocation` rather than a separate linear
    approximation, so divergence for those is caught empirically, by the
    iteration actually crossing GROWTH_BOUND_HOURS, rather than assumed safe
    by an argument that no longer strictly applies.

    Returns (True, None) if it converges, or (False, explanation) naming the
    component - Complaints/31 asks for a non-contracting cycle to be
    reported by name, as clearly as a missing recipe already is, not
    silently folded into "no path to a price".
    """
    relevant = _entries_relevant_to_component(production_entries, component, resolved_so_far)
    produced = {output for entry in relevant.values() for output in (entry.get("outputs") or {})}
    missing = sorted(component - produced)
    if missing:
        return False, (
            "%s: no admissible recipe even counting the rest of this cycle "
            "(every recipe for it needs something outside {%s} with no "
            "price of its own)"
            % (", ".join(missing), ", ".join(sorted(component))))

    if not any(_has_external_anchor(entry, resolved_so_far) for entry in relevant.values()):
        return False, (
            "{%s}: every recipe in this cycle only consumes other members "
            "of the same cycle - it never bottoms out in labour or an "
            "extracted good, so there is nothing to price it from"
            % ", ".join(sorted(component)))

    dummy_wage_by_trade = collections.defaultdict(lambda: 1.0)
    prices = {material: 1.0 for material in resolved_so_far}
    prices.update({material: INITIAL_PRICE_GUESS_HOURS for material in component})

    for _iteration in range(1, MAXIMUM_ITERATIONS + 1):
        candidates_by_material = collections.defaultdict(list)
        for entry in relevant.values():
            result = recipe_cost_and_allocation(
                "<cycle productiveness test>", entry, prices, dummy_wage_by_trade,
                rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
            if result is None:
                continue
            _total_cost, output_prices = result
            for material, price in output_prices.items():
                if material in component:
                    candidates_by_material[material].append(price)

        max_relative_change = 0.0
        for material in component:
            candidates = candidates_by_material.get(material)
            if not candidates:
                continue
            best_price = min(candidates)
            previous_price = prices[material]
            damped_price = (1.0 - DAMPING_FACTOR) * previous_price + DAMPING_FACTOR * best_price
            if not math.isfinite(damped_price) or abs(damped_price) > GROWTH_BOUND_HOURS:
                return False, (
                    "{%s}: restricted iteration grew without bound instead "
                    "of converging - this cycle consumes more of itself "
                    "than it yields (spectral radius >= 1, Hawkins-Simon "
                    "fails)" % ", ".join(sorted(component)))
            prices[material] = damped_price
            if previous_price > 0:
                max_relative_change = max(
                    max_relative_change, abs(damped_price - previous_price) / previous_price)

        if max_relative_change < CONVERGENCE_TOLERANCE:
            return True, None

    return False, (
        "{%s}: restricted iteration neither converged nor visibly diverged "
        "within %d iterations - treated as unproductive rather than guessed "
        "at" % (", ".join(sorted(component)), MAXIMUM_ITERATIONS))


def compute_resolvable_materials(production_entries, producers_of, diagnostics=None,
                                 rent_hours_per_kg_by_material=None):
    """Which materials can, even in principle, bottom out in labour and rent.

    First, the acyclic part: a material is resolvable once it has at least
    one recipe every one of whose dependencies is itself resolvable
    (vacuously true for an extracted material, which has no inputs at all).
    Grown by `_grow_resolvable_by_topological_pass` until nothing new is
    added - a plain topological reachability computation that is exactly
    right for a DAG and, by construction, refuses every genuine cycle.

    Second, the part that pass cannot see: whatever is left is decomposed
    into strongly connected components (`_strongly_connected_components`),
    and each one is tested for PRODUCTIVENESS rather than refused outright -
    a component is resolvable when every dependency from outside it is
    already resolved AND the iteration restricted to the component actually
    contracts (`_component_is_productive`). This is what makes the
    docstring's own axe/iron example, and a material like seed corn that
    lists itself among its inputs, resolve when the numbers say they should
    - see Complaints/31 and `sim/tests/test_price_solver_cycles.py`.

    This is still deliberately separate from the numeric solve below. A
    material stuck in a genuinely UNPRODUCTIVE cycle (consuming more of a
    good than the cycle yields, or never touching labour or an extracted
    good at all) would otherwise get SOME floating-point price out of a
    damped iteration - fixed-point arithmetic does not know the difference
    between "converged" and "converged to a number that means nothing" -
    and this pass is what tells them apart, and names the cycle responsible
    in `diagnostics` (a list, if the caller wants the messages) rather than
    only reporting the materials downstream of it as having no path.
    """
    resolvable = set()
    _grow_resolvable_by_topological_pass(production_entries, resolvable)

    pending = _pending_entries(production_entries, resolvable)
    graph = _build_material_dependency_graph(pending, resolvable)
    for component in _strongly_connected_components(graph):
        component_set = set(component)
        if component_set <= resolvable:
            continue  # settled already, e.g. absorbed by an earlier component
        is_productive, explanation = _component_is_productive(
            component_set, production_entries, resolvable,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
        if is_productive:
            resolvable |= component_set
            # A newly-productive cycle can unlock ordinary, acyclic recipes
            # that were only waiting on it - let those cascade in before the
            # next component (which may depend on this one) is judged.
            _grow_resolvable_by_topological_pass(production_entries, resolvable)
        elif diagnostics is not None:
            diagnostics.append(explanation)
    return resolvable


def recipe_cost_and_allocation(recipe_id, entry, current_prices, wage_by_trade,
                               rent_hours_per_kg_by_material=None,
                               capability_band_price_by_carrier=None):
    """Cost one recipe's whole batch, then split it across its outputs.

    Returns (total_process_cost_hours, {output_material: price_per_unit}),
    or None if some input has no price yet (should not happen for a
    resolvable recipe fed resolvable inputs, but the caller does not assume
    that - see the module docstring on why most extracted materials still
    price at zero rent, why six ores no longer do, why `thermal_mj`/
    `mechanical_mj` are priced through the energy market in
    data/production/70_energy.json, and why `energy_mj` still is not).

    `capability_band_price_by_carrier` is {carrier: {required_value:
    (price, recipe_id)}}, built once per round by `solve` from
    `capability_required_grades` and `capability_price_for_requirement` -
    see TEMPERATURE in the module docstring and `_capability_graded_price`
    below for PER-CONSUMER GRADING, the mechanism this feeds. Omitted or
    None, every energy carrier this recipe draws on prices at
    `current_prices`'s own flat value for it, exactly the old behaviour -
    this is the default so every caller with no opinion about grading
    (the rent and land one-off calls, which never consume a graded
    carrier) is not forced to pass an empty dict everywhere.

    `rent_hours_per_kg_by_material` is {material_key: hours of rent per kg
    of that material's OWN output} - see RENT ON EXTRACTED MATERIALS in the
    module docstring and `rent_hours_per_kg_by_ore_material` below for how
    it is built. Omitted or None, every material's rent is zero, exactly
    the old RENT_IS_ZERO behaviour; this is the default so that the cycle-
    productiveness test and any other caller that has no opinion about rent
    is not forced to pass an empty dict everywhere.

    The split is net-realisable-value allocation: each output's share of the
    batch's total cost is its own current value (quantity times current
    price) divided by the batch's total value. This is the standard answer
    to "how much of a joint process's cost belongs to this one output" and it
    is why a single-output recipe needs no special case - its one output
    simply holds a 100% share.

    CAPITAL (see the module docstring): each item in `entry["capital"]` adds
    (cost of its build_materials + cost of its build_labour_hours) /
    (service_life_years * annual_output_at_basis) to the cost of ONE UNIT of
    this recipe's basis output, priced through this same `current_prices`
    vector rather than looked up - a furnace built partly from the metal it
    makes is exactly the kind of dependency `compute_resolvable_materials`
    has to see, which is why `_dependency_materials` counts these build
    materials too. Everything else this function sums (`material_cost_hours`,
    `labour_cost_hours`) is a cost for the WHOLE BATCH described by `inputs`
    and `labour_hours` (a batch of `batch_output_quantity` units, below), so
    the per-unit capital charge is scaled up by that same quantity before it
    is added in - otherwise it would silently get divided by the batch size
    a second time when `total_process_cost_hours` is turned back into a
    per-unit price further down.
    """
    inputs = entry.get("inputs") or {}
    labour_hours = entry.get("labour_hours") or {}
    outputs = entry.get("outputs") or {}
    # The batch size `annual_output_at_basis` (and every input/labour_hours
    # quantity above) is implicitly stated against: the recipe's own basis
    # output, always the largest quantity in `outputs` for every entry that
    # carries `capital` today (a byproduct like lead's silver or zinc's
    # germanium is always the tiny quantity, never the one a furnace's
    # annual output is quoted against).
    batch_output_quantity = max(outputs.values()) if outputs else 1.0

    material_cost_hours = 0.0
    for input_material, quantity_per_batch in inputs.items():
        input_price = current_prices.get(input_material)
        if input_price is None:
            return None
        material_cost_hours += quantity_per_batch * input_price

    labour_cost_hours = 0.0
    for trade, hours_per_batch in labour_hours.items():
        labour_cost_hours += hours_per_batch * wage_by_trade[trade]

    # RENT (see RENT ON EXTRACTED MATERIALS in the module docstring). A
    # material not named in `rent_hours_per_kg_by_material` - which is
    # everything except the six ores sim/world/deposits.py covers - still
    # prices at exactly 0.0 rent, the old RENT_IS_ZERO answer. Summed over
    # every output rather than assumed single-output, so a hypothetical
    # future joint-output ore entry would be charged correctly on each of
    # its outputs rather than silently on only one.
    rent_by_kg = rent_hours_per_kg_by_material or {}
    rent_hours = sum(output_quantity * rent_by_kg.get(output_material, 0.0)
                     for output_material, output_quantity in outputs.items())

    # LAND (Complaints/49 - see RENT ON GROWN AND LAND-LIMITED MATERIALS in
    # the module docstring). `land_iugera_years` is a BATCH-level quantity,
    # exactly like `inputs` and `labour_hours` above, of iugera-years this
    # whole batch ties up `iugerum_land` for - priced through this same
    # `current_prices` vector rather than a separate rent table, because
    # `iugerum_land` is an ORDINARY material once its own price is set (by
    # the rent term above, on ITS OWN recipe in data/production/
    # 40_organics.json) and a crop paying for the land it grows on is no
    # different from a furnace paying for the ore it smelts. Kept as its
    # own named term rather than folded into `material_cost_hours` for the
    # same reason CAPITAL's build bill is not hand-added to `inputs`: this
    # is land OCCUPIED for a season, not a material CONSUMED making one
    # batch, and the field name should say so.
    land_iugera_years = entry.get("land_iugera_years") or 0.0
    land_cost_hours = 0.0
    if land_iugera_years:
        land_price = current_prices.get("iugerum_land")
        if land_price is None:
            return None
        land_cost_hours = land_iugera_years * land_price

    capital_cost_hours = 0.0
    for capital_good in (entry.get("capital") or []):
        build_materials = capital_good.get("build_materials") or {}
        build_labour_hours = capital_good.get("build_labour_hours") or {}

        build_cost_hours = 0.0
        for build_material, quantity_per_build in build_materials.items():
            build_material_price = current_prices.get(build_material)
            if build_material_price is None:
                return None
            build_cost_hours += quantity_per_build * build_material_price
        for trade, hours_per_build in build_labour_hours.items():
            build_cost_hours += hours_per_build * wage_by_trade[trade]

        lifetime_output = capital_good["service_life_years"] * capital_good["annual_output_at_basis"]
        capital_cost_hours += build_cost_hours / lifetime_output

    # ENERGY (Complaints/32's third gap, now closed for all THREE carriers -
    # THERMAL, MECHANICAL and ELECTRICAL - see ENERGY in the module
    # docstring). All three are BATCH-level quantities, exactly like
    # `inputs` and `labour_hours` above (the MJ figure is already stated
    # against this same batch's basis output) - NOT a per-unit-of-output
    # charge the way `capital` is, so unlike capital_cost_hours none of
    # these terms gets multiplied by batch_output_quantity. PER-CONSUMER
    # GRADING (Complaints/44, continued - see TEMPERATURE in the module
    # docstring): the price paid is not always `current_prices[energy_key]`
    # any more - `_capability_graded_price` returns THIS recipe's own
    # graded price when it states its own requirement, and falls back to
    # the same flat lookup as before otherwise.
    energy_cost_hours = 0.0
    for energy_key in ENERGY_CARRIER_FIELDS:
        energy_quantity_per_batch = entry.get(energy_key) or 0.0
        if energy_quantity_per_batch:
            energy_price = _capability_graded_price(
                energy_key, entry, current_prices, capability_band_price_by_carrier)
            if energy_price is None:
                return None
            energy_cost_hours += energy_quantity_per_batch * energy_price

    total_process_cost_hours = (material_cost_hours + labour_cost_hours + rent_hours
                                + land_cost_hours
                                + capital_cost_hours * batch_output_quantity
                                + energy_cost_hours)

    total_batch_value = sum(quantity * current_prices.get(material, INITIAL_PRICE_GUESS_HOURS)
                            for material, quantity in outputs.items())

    output_prices = {}
    for output_material, output_quantity in outputs.items():
        if total_batch_value > 0:
            output_value = output_quantity * current_prices.get(
                output_material, INITIAL_PRICE_GUESS_HOURS)
            value_share = output_value / total_batch_value
        else:
            # Every output priced at exactly zero (only possible before the
            # first real iteration, or for a recipe whose every output is
            # otherwise worthless) - split the cost evenly rather than divide
            # by zero, and let the next iteration's real prices take over.
            value_share = 1.0 / len(outputs)
        output_prices[output_material] = (total_process_cost_hours * value_share) / output_quantity

    return total_process_cost_hours, output_prices


# {ore_material_key: (metal_name_in_deposits_METALS, (candidate_recipe_id,
# ...))} - see RENT ON EXTRACTED MATERIALS in the module docstring for what
# this table is, why gold is not in it (gold_kg has no extracted_from ore
# stage of its own for rent to attach to), and why the "dominant" recipe
# matters (it is the one whose own ore-to-metal ratio is used to convert a
# per-kg-of-metal rent into a per-kg-of-ore price, and the one that ratio
# is EXACT for - see rent_hours_per_kg_by_ore_material's own docstring).
# copper, tin, silver and mercury each have exactly one recipe that
# consumes their ore, so there is only one candidate for them. Iron has
# two - pig_iron_kg (blast furnace) and iron_bloom_kg (direct bloomery) -
# at different ore-to-metal ratios, and which of them an era can even RUN
# differs: `--civ rome_100ad` gates pig_iron_kg out entirely (blast_furnace
# is not a Roman technology) while leaving iron_bloom_kg available, so a
# single fixed recipe id here would silently leave iron at zero rent for
# every Roman-era gated solve - exactly the scenario this task's own VERIFY
# step runs. The tuple is tried in order and the first candidate present in
# THIS solve's (possibly gated) production_entries is used, so an ungated
# solve gets the blast-furnace ratio and a Roman-gated one falls back to
# the bloomery ratio - both real recipes, never an invented one.
RENT_BEARING_ORE_MATERIALS = {
    "iron_ore_kg": ("iron", ("pig_iron_kg", "iron_bloom_kg")),
    "copper_ore_kg": ("copper", ("copper_kg",)),
    "cassiterite_kg": ("tin", ("tin_kg",)),
    "galena_kg": ("lead", ("lead_kg",)),
    "silver_ore_kg": ("silver", ("silver_kg",)),
    "cinnabar_kg": ("mercury", ("mercury_kg",)),
}


def rent_hours_per_kg_by_ore_material(production_entries, wage_by_trade):
    """{ore_material_key: hours of rent per kg of that ore's own output},
    for every metal in RENT_BEARING_ORE_MATERIALS whose ore and dominant
    smelting recipe both survive this era's gate - see RENT ON EXTRACTED
    MATERIALS in the module docstring for the mechanism this implements and
    why it is only approximate for a metal with more than one ore-consuming
    recipe.

    THE ALGEBRA. `sim/world/deposits.py`'s `find_marginal_deposit` gives
    `price_at_margin_labour_hours_per_kg` - the Ricardian, rent-inclusive
    price of one kilogram of CONTAINED METAL, at the fixed quantity demanded
    this function reads from `data/world/resources.json`'s own
    `empire_output_100ad` (see the module docstring's own TEMPORARY
    HEURISTIC paragraph on why that quantity is fixed rather than derived
    from price). Call that `metal_price`.

    The dominant recipe's own `inputs[ore] / outputs[metal]` ratio
    (`ore_per_metal`, kg of ore per kg of metal) is what turns a kilogram of
    metal into a kilogram of ore in `data/production/`'s own accounting.
    The ore's own recipe carries no inputs, so its RENT-FREE price
    (`ore_base_price`, labour only, exactly what this file used to compute)
    is fixed and does not depend on the solve's iteration at all - this
    function is therefore called once, before the iteration starts, not
    once per round.

    Setting `existing_extraction_proxy = ore_base_price * ore_per_metal`
    (what the dominant recipe already implies a kilogram of metal's
    extraction costs, with no rent), the rent this function attributes to
    the metal is `max(0, metal_price - existing_extraction_proxy)` - the
    Ricardian gap between the marginal deposit's true price and what the
    zero-rent recipe already charges - and dividing that back by
    `ore_per_metal` gives `rent_per_kg_ore`, the number this function
    returns for that ore. Added onto `ore_base_price` inside
    `recipe_cost_and_allocation` and multiplied back through the dominant
    recipe's own `ore_per_metal`, it reproduces `metal_price` on that
    recipe's output EXACTLY (the division and the later multiplication use
    the same ratio); every OTHER recipe that consumes the same ore at a
    DIFFERENT ratio gets an approximation instead, by design - see the
    module docstring.

    A metal whose marginal deposit is cheap enough that the existing
    zero-rent recipe already prices above it (which can happen: the two
    numbers come from unrelated sources, `data/production/`'s own generic
    grade assumption and `sim/world/deposits.py`'s specific named
    deposits) gets exactly 0.0 rent here, not a negative one - rent is a
    surplus over cost of production, never a discount below it.
    """
    with open(deposits.RESOURCES_FILE) as handle:
        resources_json = json.load(handle)

    rent_by_ore_material = {}
    for ore_material, (metal, candidate_recipe_ids) in RENT_BEARING_ORE_MATERIALS.items():
        ore_entry = production_entries.get(ore_material)
        if ore_entry is None:
            # Gated out of this era (--civ), or (should not happen for a
            # base material the tree already validates) simply absent -
            # either way there is nothing to attach a rent to, so this ore
            # keeps the RENT_IS_ZERO default rather than a guess.
            continue
        dominant_entry = next(
            (production_entries[recipe_id] for recipe_id in candidate_recipe_ids
             if recipe_id in production_entries),
            None)
        if dominant_entry is None:
            # Every candidate recipe is gated out of this era too - iron
            # under an ungated future-tech solve missing BOTH blast furnace
            # and bloomery would land here, which should not happen for
            # this project's own civilizations but is handled the same way
            # as any other missing recipe: zero rent, not a guess.
            continue
        dominant_inputs = dominant_entry.get("inputs") or {}
        dominant_outputs = dominant_entry.get("outputs") or {}
        if ore_material not in dominant_inputs or not dominant_outputs:
            continue
        ore_per_metal = dominant_inputs[ore_material] / max(dominant_outputs.values())
        if ore_per_metal <= 0:
            continue

        ore_outputs = ore_entry.get("outputs") or {}
        if ore_material not in ore_outputs:
            continue
        ore_output_quantity = ore_outputs[ore_material]
        base_cost = recipe_cost_and_allocation(ore_material, ore_entry, {}, wage_by_trade)
        if base_cost is None:
            continue
        ore_base_total_hours, _ = base_cost
        ore_base_price_per_kg = ore_base_total_hours / ore_output_quantity
        existing_extraction_proxy_per_kg_metal = ore_base_price_per_kg * ore_per_metal

        deposits_for_metal = deposits.load_deposits(metal)
        quantity_demanded_tonnes_per_year = (
            resources_json["empire_output_100ad"][metal]["t_per_yr"])
        outcome = deposits.find_marginal_deposit(
            deposits_for_metal, quantity_demanded_tonnes_per_year)
        metal_price_per_kg = outcome.price_at_margin_labour_hours_per_kg

        rent_per_kg_metal = max(
            0.0, metal_price_per_kg - existing_extraction_proxy_per_kg_metal)
        rent_by_ore_material[ore_material] = rent_per_kg_metal / ore_per_metal

    return rent_by_ore_material


# See sim/world/land.py's own module docstring for the mechanism (the
# margin of cultivation over a civilization's own regions, not an ore
# deposit's grade) and for why this defaults to Rome's own territory when
# no --civ is given: mirroring rent_hours_per_kg_by_ore_material's own
# Rome-anchored default (data/world/resources.json's empire_output_100ad
# has no per-civilization breakdown either), even though land's OWN
# mechanism, unlike ore's, is genuinely per-civilization the moment --civ
# names one.
DEFAULT_LAND_CIVILIZATION = "rome_100ad"


def land_rent_hours_per_iugerum(production_entries, wage_by_trade,
                                civilization_id=None):
    """{"iugerum_land": hours of rent per iugerum}, or {} if there is no
    reference crop price or no priceable land to convert into one this
    round - see sim/world/land.py's own module docstring for the mechanism
    (the Ricardian margin of cultivation over a civilization's own held
    regions) and for why a civilization holding only one region prices
    land at exactly zero (a real finding, not a bug: no differential rent
    without at least two regions of different quality to compare).

    THE ALGEBRA. sim/world/land.py's own `margin_outcome_for_civilization`
    returns a supply-weighted average rent in kilograms of grain-equivalent
    per iugerum - a PHYSICAL quantity, not a price (see that module's own
    WHY THE HOURS CONVERSION LIVES IN sim/solve_prices.py, NOT HERE
    section for why the conversion happens here rather than there).
    Multiplying by wheat_kg's own ZERO-LAND-RENT price (labour only, exactly
    like rent_hours_per_kg_by_ore_material's own `ore_base_price_per_kg`)
    turns that physical surplus into the labour-hour unit this file prices
    everything else in. `iugerum_land` itself has no `inputs` and no
    `labour_hours` of its own (data/production/40_organics.json's own
    entry says so directly), so this rent figure becomes its WHOLE solved
    price with nothing else added - see recipe_cost_and_allocation's own
    rent_hours term.

    THE ZERO-LAND-RENT REFERENCE PRICE, AND WHY IT STAYS ZERO-RENT EVEN NOW
    THAT wheat_kg CONSUMES LAND (Complaints/49). Before this round wheat_kg
    truly had no `inputs` at all, so calling `recipe_cost_and_allocation`
    with an empty price dict gave its labour-only price by construction.
    wheat_kg now also states a `land_iugera_years` (see RENT ON GROWN AND
    LAND-LIMITED MATERIALS above), so the SAME call would otherwise return
    None the moment it tries to look up a price for `iugerum_land` that this
    empty dict does not have. The fix is to seed exactly that one price at
    0.0 rather than leave it absent - `{"iugerum_land": 0.0}` - which
    reproduces the pre-Complaints/49 answer exactly (0.0 hours/iugerum times
    any `land_iugera_years` is 0.0, so the land term drops out and only
    labour remains) rather than changing what this reference price MEANS.
    This is deliberately NOT circular: the reference price answers "what
    would wheat cost if land were free", which this function needs as a
    pure UNIT CONVERSION for land.py's physical rent, and it is computed
    once, outside the main iteration, the same way it always was - wheat's
    ACTUAL solved price (what every other recipe that consumes wheat_kg
    pays, and what bread is costed from) is computed by the ordinary
    Jacobi iteration in `solve()` below, WITH land_iugera_years priced in,
    using `iugerum_land`'s price that THIS function's own return value
    fixes beforehand. See WHY NO NEW CYCLE in the module docstring.
    """
    civilization_id = civilization_id or DEFAULT_LAND_CIVILIZATION
    wheat_entry = production_entries.get("wheat_kg")
    if wheat_entry is None:
        # Gated out of this era, or (should not happen - wheat_kg carries
        # requires_node: null, admitted to every era) simply absent. Either
        # way there is no reference crop price to convert the physical rent
        # into hours with, so land keeps the old RENT_IS_ZERO answer.
        return {}
    wheat_cost = recipe_cost_and_allocation(
        "wheat_kg", wheat_entry, {"iugerum_land": 0.0}, wage_by_trade)
    if wheat_cost is None:
        return {}
    _wheat_total_hours, wheat_output_prices = wheat_cost
    wheat_price_per_kg = wheat_output_prices.get("wheat_kg")
    if not wheat_price_per_kg:
        return {}

    try:
        outcome = land.margin_outcome_for_civilization(civilization_id)
    except (FileNotFoundError, KeyError):
        # An unknown civilization id, or one missing a population field -
        # should not happen for this project's own data/civilizations/
        # files, handled the same way a missing ore recipe is: no rent
        # guessed, the old zero-rent answer stands.
        return {}
    if outcome.price_kg_grain_equivalent_per_iugerum <= 0.0:
        return {}
    rent_hours = outcome.price_kg_grain_equivalent_per_iugerum * wheat_price_per_kg
    return {"iugerum_land": rent_hours}


def solve(production_entries, producers_of, resolvable_materials, wage_by_trade,
         damping=DAMPING_FACTOR, max_iterations=MAXIMUM_ITERATIONS,
         tolerance=CONVERGENCE_TOLERANCE, rent_hours_per_kg_by_material=None):
    """Damped Jacobi fixed-point iteration over every resolvable material.

    Every material updates from the SAME round's starting prices (Jacobi,
    not Gauss-Seidel) so that the result does not depend on dict iteration
    order - a determinism concern this repository has been burned by before
    (see CLAUDE.md section 6 on `id()` and stale caches). Each round: cost
    every recipe against the current price vector, take the cheapest
    technique for each material, and blend it into that material's price by
    `damping`. Stop when the largest relative change across all materials
    drops below `tolerance`, or after `max_iterations`.

    Returns (prices, iterations_run, final_residual, chosen_recipe_by_material).

    PHYSICAL CAPABILITY CAPS, PER CONSUMER (Complaints/44, continued; see
    CAPABILITY_CAP_FIELDS and TEMPERATURE in the module docstring). Two
    things are computed once, before the very first round, from THIS
    solve's own `production_entries` alone - exactly like
    `rent_hours_per_kg_by_ore_material` is computed once rather than every
    round, because neither depends on the price vector: `floor_by_carrier`
    (the carrier's own universal default floor, e.g. thermal_mj's
    cap_heat_0700 rung) and `required_grades_by_carrier` (every DISTINCT
    requirement this era's own consumers actually state, the default
    included - see `capability_required_grades`).

    Every round after that, TWO things happen with those, in order:
    `capability_price_for_requirement` is re-solved for each distinct
    required value at THIS round's current prices (a technique's own cost
    moves every round, so which one clears a given requirement most
    cheaply can too) into `band_price_by_carrier`, and THEN every recipe
    is costed with that dict threaded through
    `recipe_cost_and_allocation`, so a consumer that states its own
    requirement pays its own graded price rather than the flat pool
    price. Choice of technique for the carrier MATERIAL itself (`thermal_
    mj`'s own entry in `resolvable_materials`, what an unlabelled consumer
    pays) still uses `_meets_capability_floor` against the plain
    `floor_by_carrier` - the universal default only, exactly as before
    this mechanism existed, and now correctly UNAFFECTED by any other
    consumer's own higher requirement (see TEMPERATURE for why that used
    to be a bug).
    """
    prices = {material: INITIAL_PRICE_GUESS_HOURS for material in resolvable_materials}
    chosen_recipe_by_material = {}
    recipe_ids_in_order = sorted(production_entries)  # stable order; see above
    floor_by_carrier = capability_floor_by_carrier(production_entries)
    required_grades_by_carrier = capability_required_grades(production_entries)

    final_residual = float("inf")
    iterations_run = 0
    for iteration in range(1, max_iterations + 1):
        iterations_run = iteration

        # PER-CONSUMER GRADING: re-solved every round, from THIS round's
        # own (pre-update) `prices`, exactly like every candidate recipe
        # below is costed against those same prices (Jacobi - see this
        # function's own docstring on why every material updates from the
        # same round's starting point).
        band_price_by_carrier = {
            carrier: {
                required_value: capability_price_for_requirement(
                    carrier, required_value, production_entries, prices,
                    wage_by_trade,
                    rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
                for required_value in required_values
            }
            for carrier, required_values in required_grades_by_carrier.items()
        }

        candidates_by_material = collections.defaultdict(list)
        for recipe_id in recipe_ids_in_order:
            entry = production_entries[recipe_id]
            outputs = entry.get("outputs") or {}
            if not outputs or not all(output_material in resolvable_materials for output_material in outputs):
                continue
            result = recipe_cost_and_allocation(
                recipe_id, entry, prices, wage_by_trade,
                rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
                capability_band_price_by_carrier=band_price_by_carrier)
            if result is None:
                continue
            _total_cost, output_prices = result
            for material, price in output_prices.items():
                if not _meets_capability_floor(material, entry, floor_by_carrier):
                    continue
                candidates_by_material[material].append((price, recipe_id))

        new_prices = {}
        max_relative_change = 0.0
        for material in resolvable_materials:
            candidates = candidates_by_material.get(material)
            if not candidates:
                new_prices[material] = prices[material]
                continue
            best_price, best_recipe = min(candidates, key=lambda pair: pair[0])
            chosen_recipe_by_material[material] = best_recipe
            damped_price = (1.0 - damping) * prices[material] + damping * best_price
            new_prices[material] = damped_price
            previous_price = prices[material]
            if previous_price > 0:
                relative_change = abs(damped_price - previous_price) / previous_price
                max_relative_change = max(max_relative_change, relative_change)

        prices = new_prices
        final_residual = max_relative_change
        if max_relative_change < tolerance:
            break

    return prices, iterations_run, final_residual, chosen_recipe_by_material


def minor_joint_byproducts_are_unanchored(production_entries, chosen_recipe_by_material,
                                          prices, wage_by_trade, share_threshold=0.5,
                                          rent_hours_per_kg_by_material=None):
    """{material: value_share} for every material whose CONVERGED, CHOSEN
    recipe is a joint-production recipe in which this material holds under
    `share_threshold` of the batch's value.

    See JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR in the module
    docstring for why this matters: these are not ordinary low-value
    materials, they are materials whose printed price is a mass-split
    artifact rather than an independently derived number, and every caller
    that prints a price must be able to say so next to it.
    """
    unanchored = {}
    for material, recipe_id in chosen_recipe_by_material.items():
        entry = production_entries[recipe_id]
        outputs = entry.get("outputs") or {}
        if len(outputs) <= 1:
            continue
        result = recipe_cost_and_allocation(
            recipe_id, entry, prices, wage_by_trade,
            rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
        if result is None:
            continue
        total_process_cost, _output_prices = result
        if total_process_cost <= 0:
            continue
        value_share = (outputs[material] * prices[material]) / total_process_cost
        if value_share < share_threshold:
            unanchored[material] = value_share
    return unanchored


def format_hours(value):
    if value >= 100:
        return "%.1f" % value
    if value >= 1:
        return "%.3f" % value
    return "%.5f" % value


def _default_capability_band_price_by_carrier(production_entries, prices, wage_by_trade,
                                                rent_hours_per_kg_by_material):
    # The same {carrier: {required_value: (price, recipe_id)}} shape `solve`
    # builds each round - see print_why's own docstring for why this is
    # computed once at the top-level call and threaded through recursion
    # rather than rebuilt at every level.
    return {
        carrier: {
            required_value: capability_price_for_requirement(
                carrier, required_value, production_entries, prices,
                wage_by_trade,
                rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
            for required_value in required_values
        }
        for carrier, required_values in capability_required_grades(production_entries).items()
    }


def _print_extraction_rent_explanation(pad, material, entry, rent_by_kg):
    # Why this material's price does or does not carry a Ricardian rent -
    # see RENT ON EXTRACTED MATERIALS and RENT ON GROWN AND LAND-LIMITED
    # MATERIALS in the module docstring.
    if entry.get("extracted_from"):
        material_rent_per_kg = rent_by_kg.get(material)
        if material_rent_per_kg and material == "iugerum_land":
            print("%s  EXTRACTED from %s - no cost of production, only a "
                  "Ricardian rent of %s h/iugerum from sim/world/land.py's "
                  "margin of cultivation over a civilization's own held "
                  "regions (see RENT ON ARABLE LAND)."
                  % (pad, entry["extracted_from"], format_hours(material_rent_per_kg)))
        elif material_rent_per_kg:
            print("%s  EXTRACTED from %s - labour plus a Ricardian rent of "
                  "%s h/kg from sim/world/deposits.py's marginal-deposit "
                  "supply curve (see RENT ON EXTRACTED MATERIALS)."
                  % (pad, entry["extracted_from"], format_hours(material_rent_per_kg)))
        elif entry.get("land_iugera_years"):
            # GROWN/land-limited (Complaints/49): this material's OWN
            # extracted_from rent term (the ore-style mechanism above) is
            # zero, as it always is for anything that is not one of the six
            # named ores - but that is not the same as "no rent at all" any
            # more, because this recipe also consumes iugerum_land, whose
            # own rent shows up in the LAND line below rather than here.
            print("%s  EXTRACTED from %s - no separate cost of production "
                  "of its own; its land cost is priced through iugerum_land "
                  "(see the LAND line below and RENT ON GROWN AND LAND-"
                  "LIMITED MATERIALS)."
                  % (pad, entry["extracted_from"]))
        else:
            print("%s  EXTRACTED from %s - no cost of production, only "
                  "labour and a rent this round fixed at 0.0 (see RENT ON "
                  "EXTRACTED MATERIALS - this material is not one of the "
                  "six ores sim/world/deposits.py covers, nor a material "
                  "that consumes iugerum_land - see sim/world/land.py)."
                  % (pad, entry["extracted_from"]))


def _print_rejected_techniques(pad, material, recipe_id, production_entries, producers_of):
    # Split rejections by REASON (Complaints/44) - see print_why's call site
    # for why a capability floor and a price comparison are different findings.
    candidates = sorted(set(producers_of.get(material, [])) - {recipe_id})
    if candidates:
        # Split rejections by REASON (Complaints/44) - a technique that
        # cannot physically reach what this material needs is a different
        # finding from one that merely costs more today, and conflating
        # them is exactly how "thermal_mj_friction should never be chosen"
        # stopped being verifiable as anything but a hope. See
        # CAPABILITY_CAP_FIELDS and _meets_capability_floor above.
        floor_by_carrier = capability_floor_by_carrier(production_entries)
        capped = CAPABILITY_CAP_FIELDS.get(material)
        notes = []
        for candidate_id in candidates:
            candidate_entry = production_entries[candidate_id]
            if capped and not _meets_capability_floor(material, candidate_entry, floor_by_carrier):
                reached_field, _needed_field, _default_floor = capped
                notes.append("%s (reaches %s, this era needs >= %s - see "
                             "CAPABILITY_CAP_FIELDS)" % (
                             candidate_id, candidate_entry.get(reached_field),
                             floor_by_carrier[material]))
            else:
                notes.append("%s (more expensive at current prices)" % candidate_id)
        print("%s  other techniques considered and rejected: %s"
              % (pad, ", ".join(notes)))


def _print_joint_output_note(pad, other_outputs, outputs):
    if other_outputs:
        print("%s  joint output of this batch, also yielding: %s - cost "
              "split across outputs by current value share" % (
              pad, ", ".join("%s (%.4g)" % (key, outputs[key]) for key in other_outputs)))


def _print_inputs(pad, inputs, output_quantity, prices, total_process_cost):
    if inputs:
        print("%s  inputs, per %.4g unit(s) of output batch:" % (pad, output_quantity))
        for input_material, quantity_per_batch in sorted(inputs.items()):
            input_price = prices.get(input_material)
            cost = quantity_per_batch * input_price if input_price is not None else None
            share_text = ("%.1f%% of process cost" % (100.0 * cost / total_process_cost)
                         if cost is not None and total_process_cost > 0 else "n/a")
            print("%s    %-24s x %10.4g  @ %10s h/unit = %10s h  (%s)" % (
                pad, input_material, quantity_per_batch,
                format_hours(input_price) if input_price is not None else "NO PRICE",
                format_hours(cost) if cost is not None else "?",
                share_text))


def _print_labour(pad, entry, wage_by_trade, total_process_cost):
    labour_hours = entry.get("labour_hours") or {}
    if labour_hours:
        print("%s  labour:" % pad)
        for trade, hours_per_batch in sorted(labour_hours.items()):
            wage = wage_by_trade[trade]
            cost = hours_per_batch * wage
            share_text = ("%.1f%% of process cost" % (100.0 * cost / total_process_cost)
                         if total_process_cost > 0 else "n/a")
            print("%s    %-24s %10.4g h  @ %6.3fx unskilled wage = %10s h  (%s)" % (
                pad, trade, hours_per_batch, wage, format_hours(cost), share_text))


def _print_rent_this_batch(pad, outputs, rent_by_kg, total_process_cost):
    rent_this_batch = sum(quantity * rent_by_kg.get(output_material, 0.0)
                          for output_material, quantity in outputs.items())
    if rent_this_batch > 0:
        share_text = ("%.1f%% of process cost" % (100.0 * rent_this_batch / total_process_cost)
                     if total_process_cost > 0 else "n/a")
        print("%s  rent (Ricardian, see RENT ON EXTRACTED MATERIALS): "
              "%10s h  (%s)" % (pad, format_hours(rent_this_batch), share_text))


def _print_land(pad, entry, prices, total_process_cost):
    land_iugera_years = entry.get("land_iugera_years") or 0.0
    if land_iugera_years:
        land_price = prices.get("iugerum_land")
        land_cost = land_iugera_years * land_price if land_price is not None else None
        share_text = ("%.1f%% of process cost" % (100.0 * land_cost / total_process_cost)
                     if land_cost is not None and total_process_cost > 0 else "n/a")
        print("%s  land (see RENT ON GROWN AND LAND-LIMITED MATERIALS): "
              "%10.4g iugera-yrs @ %10s h/iugerum-yr = %10s h  (%s)" % (
              pad, land_iugera_years,
              format_hours(land_price) if land_price is not None else "NO PRICE",
              format_hours(land_cost) if land_cost is not None else "?", share_text))
    return land_iugera_years


def _print_capital(pad, entry, prices, wage_by_trade, outputs, total_process_cost):
    capital_goods = entry.get("capital") or []
    if capital_goods:
        print("%s  capital (amortised build cost, see CAPITAL in the module "
              "docstring):" % pad)
        for capital_good in capital_goods:
            build_materials = capital_good.get("build_materials") or {}
            build_labour_hours = capital_good.get("build_labour_hours") or {}
            build_cost = sum(quantity * prices.get(build_material, 0.0)
                             for build_material, quantity in build_materials.items())
            build_cost += sum(hours * wage_by_trade.get(trade, 0.0)
                              for trade, hours in build_labour_hours.items())
            lifetime_output = (capital_good["service_life_years"]
                               * capital_good["annual_output_at_basis"])
            charge = build_cost / lifetime_output
            # `charge` is per unit of OUTPUT (see recipe_cost_and_allocation);
            # total_process_cost is per BATCH, so scale by the batch quantity
            # before comparing them, the same way the real cost sum does.
            batch_output_quantity = max(outputs.values()) if outputs else 1.0
            share_text = ("%.2f%% of process cost"
                         % (100.0 * charge * batch_output_quantity / total_process_cost)
                         if total_process_cost > 0 else "n/a")
            print("%s    %-40s %10s h build / %.4g lifetime units = %10s h/unit  (%s)"
                  % (pad, capital_good.get("good", "?"), format_hours(build_cost),
                     lifetime_output, format_hours(charge), share_text))


def _print_energy(pad, entry, prices, capability_band_price_by_carrier,
                   chosen_recipe_by_material, total_process_cost):
    energy_labels = {"thermal_mj": "thermal (heat) energy",
                     "mechanical_mj": "mechanical (shaft) energy",
                     "electrical_mj": "electrical energy"}
    graded_energy_keys = set()
    for energy_key, label in energy_labels.items():
        energy_quantity = entry.get(energy_key) or 0.0
        if not energy_quantity:
            continue
        # PER-CONSUMER GRADING (see print_why's own docstring and
        # TEMPERATURE in the module docstring): THIS recipe's own graded
        # price if it states a requirement, not necessarily the same as
        # the carrier's flat pool price shown for `--why thermal_mj`
        # itself.
        energy_price = _capability_graded_price(
            energy_key, entry, prices, capability_band_price_by_carrier)
        capped = CAPABILITY_CAP_FIELDS.get(energy_key)
        graded_note = ""
        if capped:
            _reached_field, needed_field, _default_floor = capped
            required_value = entry.get(needed_field)
            if required_value is not None:
                graded_energy_keys.add(energy_key)
                band = (capability_band_price_by_carrier.get(energy_key) or {})
                graded = band.get(required_value)
                graded_recipe_id = graded[1] if graded is not None else "NOTHING THIS ERA"
                pool_recipe_id = chosen_recipe_by_material.get(energy_key, "?")
                graded_note = ("  [graded: this recipe needs >= %s, met by "
                               "%s, vs the shared pool's own choice %s]"
                               % (required_value, graded_recipe_id, pool_recipe_id))
        cost = energy_quantity * energy_price if energy_price is not None else None
        share_text = ("%.1f%% of process cost" % (100.0 * cost / total_process_cost)
                     if cost is not None and total_process_cost > 0 else "n/a")
        print("%s  %-24s x %10.4g MJ @ %10s h/MJ = %10s h  (%s)%s" % (
            pad, label, energy_quantity,
            format_hours(energy_price) if energy_price is not None else "NO PRICE",
            format_hours(cost) if cost is not None else "?", share_text, graded_note))
    return graded_energy_keys


def _print_energy_gap(pad, entry):
    residual_energy_mj = entry.get("energy_mj") or 0.0
    if residual_energy_mj:
        print("%s  ENERGY GAP: this recipe also needs %.4g MJ that neither "
              "the thermal nor the mechanical energy market prices (a "
              "technology this file cannot yet cost - see ENERGY in this "
              "file's module docstring). The price above is a LOWER BOUND "
              "by that much." % (pad, residual_energy_mj))


def _print_value_share_or_total(pad, other_outputs, this_output_value_share, output_prices,
                                 material, output_quantity, total_process_cost, price):
    if other_outputs:
        print("%s  this output's value share of the batch: %.1f%%  ->  "
              "%s h of %s h total process cost, / %.4g unit(s) = %s h/unit"
              % (pad, 100.0 * this_output_value_share,
                 format_hours(output_prices[material] * output_quantity),
                 format_hours(total_process_cost), output_quantity,
                 format_hours(price)))
        if this_output_value_share < 0.5:
            print("%s  (*) MINOR JOINT BYPRODUCT: this share is under half the "
                  "batch's value, and every material in that position converges "
                  "to the SAME price per unit as its dominant co-product - a "
                  "mass-split artifact of net-realisable-value allocation with "
                  "no independent price to anchor it, not a derived number. "
                  "See JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR in this "
                  "file's module docstring." % pad)
    else:
        print("%s  process total: %s h  /  %.4g unit(s) of output = %s h/unit"
              % (pad, format_hours(total_process_cost), output_quantity, format_hours(price)))


def _resolved_recipe_id_or_none(pad, material, resolvable_materials, ancestors,
                                 chosen_recipe_by_material):
    # The three ways print_why has nothing further to print for this
    # material - no path to a price, a cycle back to an ancestor already
    # shown, or (a bug) resolvable but never actually chosen - all end the
    # same way for the caller: print the reason, return None, stop.
    if material not in resolvable_materials:
        print("%s%s: NO PATH TO A PRICE (see the unpriceable-materials list)"
              % (pad, material))
        return None
    if material in ancestors:
        print("%s%s: (cycle back to an ancestor already shown above)" % (pad, material))
        return None
    recipe_id = chosen_recipe_by_material.get(material)
    if recipe_id is None:
        print("%s%s: resolvable but never chosen by any recipe - this should "
              "not happen and is worth reporting as a bug" % (pad, material))
        return None
    return recipe_id


def _next_recursion_targets(inputs, entry, graded_energy_keys, land_iugera_years, material):
    # A GRADED energy dependency (this recipe stated its own requirement)
    # was already shown above, by name and by price, next to the pool's
    # own choice for comparison - recursing into the generic carrier
    # material here would print the POOL's chosen technique instead,
    # which is not necessarily the one this recipe actually pays for (see
    # PER-CONSUMER GRADING) and would be misleading rather than merely
    # redundant, so it is skipped rather than recursed into.
    energy_dependencies = [energy_key for energy_key in ENERGY_CARRIER_FIELDS
                          if entry.get(energy_key) and energy_key not in graded_energy_keys]
    land_dependencies = ["iugerum_land"] if land_iugera_years and material != "iugerum_land" else []
    return sorted(inputs) + energy_dependencies + land_dependencies


def print_why(material, production_entries, producers_of, resolvable_materials,
              prices, wage_by_trade, chosen_recipe_by_material, indent=0, ancestors=(),
              rent_hours_per_kg_by_material=None, capability_band_price_by_carrier=None):
    """Recursive cost breakdown for one material: how much of its price is
    which input, which labour, which rent - recursing into every priced
    input in turn, with a cycle guard so a recipe graph that legitimately
    loops (iron needs charcoal needs an axe needs iron) prints once per
    branch and then says so, rather than recursing forever.

    `capability_band_price_by_carrier` is the same {carrier: {required_
    value: (price, recipe_id)}} shape `solve` builds each round (see
    PER-CONSUMER GRADING there and `_capability_graded_price`) - computed
    ONCE here, at the top-level call, from the final converged `prices`,
    and threaded through every recursive call rather than rebuilt at each
    level, so a recipe that states its own energy requirement (a heat
    engine's `temperature_needed_c`, say) is costed and displayed at ITS
    OWN graded price rather than the carrier's flat pool price - the same
    distinction `solve` itself now makes, shown here rather than hidden
    behind a single scalar `prices[carrier]`.
    """
    if capability_band_price_by_carrier is None:
        capability_band_price_by_carrier = _default_capability_band_price_by_carrier(
            production_entries, prices, wage_by_trade, rent_hours_per_kg_by_material)
    pad = "  " * indent
    recipe_id = _resolved_recipe_id_or_none(pad, material, resolvable_materials, ancestors,
                                            chosen_recipe_by_material)
    if recipe_id is None:
        return
    entry = production_entries[recipe_id]
    price = prices[material]
    outputs = entry.get("outputs") or {}
    other_outputs = [key for key in outputs if key != material]

    header = "%s%s = %s labour-hours" % (pad, material, format_hours(price))
    if recipe_id != material:
        header += "   [technique: %s]" % recipe_id
    conf = entry.get("conf", "?")
    header += "   (conf %s)" % conf
    print(header)

    rent_by_kg = rent_hours_per_kg_by_material or {}
    _print_extraction_rent_explanation(pad, material, entry, rent_by_kg)

    candidates = sorted(set(producers_of.get(material, [])) - {recipe_id})
    if candidates:
        _print_rejected_techniques(pad, material, recipe_id, production_entries, producers_of)

    _print_joint_output_note(pad, other_outputs, outputs)

    result = recipe_cost_and_allocation(
        recipe_id, entry, prices, wage_by_trade,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
        capability_band_price_by_carrier=capability_band_price_by_carrier)
    total_process_cost, output_prices = result
    output_quantity = outputs[material]
    this_output_value_share = (output_prices[material] * output_quantity) / total_process_cost \
        if total_process_cost > 0 else 0.0

    inputs = entry.get("inputs") or {}
    if inputs:
        _print_inputs(pad, inputs, output_quantity, prices, total_process_cost)

    _print_labour(pad, entry, wage_by_trade, total_process_cost)

    _print_rent_this_batch(pad, outputs, rent_by_kg, total_process_cost)

    land_iugera_years = _print_land(pad, entry, prices, total_process_cost)

    _print_capital(pad, entry, prices, wage_by_trade, outputs, total_process_cost)

    graded_energy_keys = _print_energy(pad, entry, prices, capability_band_price_by_carrier,
                                        chosen_recipe_by_material, total_process_cost)

    _print_energy_gap(pad, entry)

    _print_value_share_or_total(pad, other_outputs, this_output_value_share, output_prices,
                                 material, output_quantity, total_process_cost, price)

    next_ancestors = ancestors + (material,)
    for input_material in _next_recursion_targets(inputs, entry, graded_energy_keys,
                                                  land_iugera_years, material):
        print()
        print_why(input_material, production_entries, producers_of, resolvable_materials,
                  prices, wage_by_trade, chosen_recipe_by_material,
                  indent=indent + 1, ancestors=next_ancestors,
                  rent_hours_per_kg_by_material=rent_hours_per_kg_by_material,
                  capability_band_price_by_carrier=capability_band_price_by_carrier)


def _apply_era_gate(arguments, production_entries):
    """Restricts production_entries to the techniques `arguments.civ` can
    actually run, before anything else looks at them - see THE ERA GATE
    comment this replaces below. Returns (all_production_entries,
    production_entries, unreached_techniques, unclassified_techniques) on
    success, or None if arguments.civ names an unknown civilization (the
    message is already printed).
    """
    # THE ERA GATE. Applied before anything else looks at the entries, so
    # that resolvability, the fixed point, choice of technique, --why and
    # --compare all see the same, single set of techniques. Filtering later
    # - say, only inside `solve` - would leave the resolvability pass
    # reporting materials as priceable that this era has no way to make.
    unreached_techniques, unclassified_techniques = [], []
    all_production_entries = production_entries
    if arguments.civ:
        try:
            reached_nodes = load_starting_technologies(arguments.civ)
        except FileNotFoundError as problem:
            # A CLI typo deserves the list of real names, not a traceback.
            print(problem)
            return None
        entries_before_gate = len(production_entries)
        (production_entries, unreached_techniques,
         unclassified_techniques) = techniques_available_to(
            production_entries, reached_nodes)
        print("ERA GATE: %s holds %d technologies; %d of %d techniques are "
              "available to it (%d need a node it has not reached, %d carry "
              "no requires_node and are dropped unclassified)."
              % (arguments.civ, len(reached_nodes), len(production_entries),
                 entries_before_gate, len(unreached_techniques),
                 len(unclassified_techniques)))
        if unclassified_techniques:
            print("       An unclassified technique is an unanswered "
                  "question, not a universal one - see WHEN A TECHNIQUE "
                  "BECOMES AVAILABLE in data/production/_SCHEMA.md.")
        print()
    return (all_production_entries, production_entries, unreached_techniques,
            unclassified_techniques)


def _run_why_report(material, all_referenced_materials, production_entries, producers_of,
                     resolvable_materials, prices, wage_by_trade, chosen_recipe_by_material,
                     rent_hours_per_kg_by_material):
    if material not in all_referenced_materials:
        print("%r is not a material this tree consumes, nor one "
              "data/production/ produces or references. Typo?" % material)
        return 1
    print_why(material, production_entries, producers_of, resolvable_materials,
              prices, wage_by_trade, chosen_recipe_by_material,
              rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)
    return 0


def _run_compare_report(prices_json, resolvable_materials, prices, unanchored_byproducts):
    book_prices = {material: entry["p"] for material, entry in prices_json["purchase_prices_denarii"].items()
                   if not material.startswith("_")}
    unskilled_wage_denarii_per_hour = \
        prices_json["wage_rates_denarii_per_hour"][NUMERAIRE_TRADE]["rate"]
    rows = []
    for material in sorted(resolvable_materials):
        if material not in book_prices:
            continue
        computed_hours = prices[material]
        book_hours = book_prices[material] / unskilled_wage_denarii_per_hour
        if book_hours <= 0 or computed_hours <= 0:
            continue
        disagreement = (computed_hours / book_hours if computed_hours >= book_hours
                       else book_hours / computed_hours)
        higher = "book" if book_hours > computed_hours else "computed"
        rows.append((disagreement, material, computed_hours, book_hours, higher))
    rows.sort(reverse=True)
    print("computed price (labour-hours) vs data/prices.json book price "
          "(converted to labour-hours via the labourer wage), sorted by "
          "disagreement - THIS IS A VALIDATION READ, NOT A CALIBRATION "
          "TARGET. The book is 91.8%% author estimate; this exists to "
          "replace it, so a big ratio is a finding about one of the two "
          "numbers, not automatically a bug in the computed one. Rows "
          "marked (*) are minor joint byproducts whose computed price is "
          "a mass-split artifact, not an independent number - see "
          "JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR above; for "
          "those the book is the more informative number this round.")
    print()
    print("%-26s %14s %14s %16s" % ("material", "computed h", "book h", "disagreement"))
    for disagreement, material, computed_hours, book_hours, higher in rows:
        flag = " (*)" if material in unanchored_byproducts else ""
        print("%-26s %14s %14s %12sx %s higher%s" % (
            material, format_hours(computed_hours), format_hours(book_hours),
            format_hours(disagreement), higher, flag))
    return 0


def _print_default_report_header(arguments):
    print("PRICE SOLVER - numeraire is one hour of unskilled (%r trade) "
          "labour. Rent on the ore of iron, copper, tin, lead, silver and "
          "mercury is now priced from sim/world/deposits.py's Ricardian "
          "marginal-deposit supply curve (see RENT ON EXTRACTED MATERIALS "
          "in the module docstring); rent on iugerum_land is now priced "
          "from sim/world/land.py's margin of cultivation over %s's own "
          "held regions (pass --civ to price another civilization's "
          "territory instead); every other extracted material (forest, "
          "quarry, salt pan, gold's placer-and-amalgamation step) still "
          "prices at zero rent. thermal_mj, mechanical_mj and electrical_mj "
          "are all priced via the three-way energy market and its "
          "conversion recipes in data/production/70_energy.json; energy_mj "
          "is still not priced (see module docstring)."
          % (NUMERAIRE_TRADE, arguments.civ or DEFAULT_LAND_CIVILIZATION))
    print()


def _print_rent_summary(arguments, rent_hours_per_kg_by_material):
    if rent_hours_per_kg_by_material:
        ore_rent = {material: rent_hours for material, rent_hours in rent_hours_per_kg_by_material.items()
                   if material in RENT_BEARING_ORE_MATERIALS}
        land_rent = {material: rent_hours for material, rent_hours in rent_hours_per_kg_by_material.items()
                    if material not in RENT_BEARING_ORE_MATERIALS}
        print("RENT NOW PRICED for %d of the %d ore materials named in "
              "RENT_BEARING_ORE_MATERIALS this era's gate leaves reachable "
              "(the rest fell out of the gate along with every recipe that "
              "would have consumed them):"
              % (len(ore_rent), len(RENT_BEARING_ORE_MATERIALS)))
        for ore_material in sorted(ore_rent):
            print("   %-26s %10s h/kg rent"
                  % (ore_material, format_hours(ore_rent[ore_material])))
        if land_rent:
            print("RENT NOW PRICED on land, for %s (%d region(s) held):"
                  % (arguments.civ or DEFAULT_LAND_CIVILIZATION,
                     len(land.cultivable_land_for_civilization(
                         arguments.civ or DEFAULT_LAND_CIVILIZATION))))
            for land_material in sorted(land_rent):
                print("   %-26s %10s h/iugerum rent"
                      % (land_material, format_hours(land_rent[land_material])))
        elif "iugerum_land" not in rent_hours_per_kg_by_material:
            civilization_for_land = arguments.civ or DEFAULT_LAND_CIVILIZATION
            region_count = len(land.cultivable_land_for_civilization(civilization_for_land))
            print("iugerum_land priced at zero rent this run - %s holds "
                  "%d region(s), and none of its worse ones are needed to "
                  "feed its own stated population, so nothing better-than-"
                  "the-margin is actually being worked yet (see sim/world/"
                  "land.py's own module docstring - a single held region "
                  "always lands here too, since it has no worse region of "
                  "its own to earn a differential rent over)."
                  % (civilization_for_land, region_count))
        print()


def _print_convergence_summary(converged, iterations_run, residual, arguments,
                                resolvable_materials, all_referenced_materials, unpriceable):
    print("convergence: %s after %d iteration(s), final max relative change "
          "%.3e (tolerance %.0e, damping %.2f)"
          % ("CONVERGED" if converged else "DID NOT CONVERGE",
             iterations_run, residual, CONVERGENCE_TOLERANCE, arguments.damping))
    print("%d of %d referenced materials have a path to a price (%d resolved "
          "via data/production/, %d with NO path)"
          % (len(resolvable_materials), len(all_referenced_materials),
             len(resolvable_materials), len(unpriceable)))


def _print_unpriceable_materials(unpriceable, unreached_techniques, unclassified_techniques,
                                  all_production_entries, producers_of, tree_consumed):
    if unpriceable:
        print()
        print("MATERIALS WITH NO PATH TO A PRICE - a missing input entry, or "
              "a cycle with no extracted/labour-only material to bottom out "
              "at:")
        # UNDER A GATE, "no production entry at all" would be a lie: the
        # entry exists and this era simply cannot run it, which is a
        # completely different finding and wants a different response
        # (nothing, if the gate is right). Separate the two so a gated run
        # does not read as a hole in the data.
        # AND "GATED OUT" IS NOT "UNLABELLED", WHICH THIS CONFLATED. A
        # technique this era cannot reach is a correct answer and wants no
        # action. A technique nobody has classified yet is an unanswered
        # question that happens to LOOK the same from here, and calling it
        # "correctly gated out" told the reader the opposite of the truth -
        # copper_kg read as correctly unavailable to Rome when in fact its
        # file had not been labelled.
        unreached_materials, unclassified_materials = set(), set()
        for recipe_id in unreached_techniques:
            unreached_materials |= set(
                (all_production_entries[recipe_id].get("outputs") or {}))
        for recipe_id in unclassified_techniques:
            unclassified_materials |= set(
                (all_production_entries[recipe_id].get("outputs") or {}))
        # A material with both an unreached and an unlabelled recipe is an
        # open question, so the weaker claim wins.
        unreached_materials -= unclassified_materials
        for material in unpriceable:
            if material not in producers_of and material in unclassified_materials:
                reason = ("something makes it, but no recipe for it says when "
                          "it becomes available - UNLABELLED, not gated out")
            elif material not in producers_of and material in unreached_materials:
                reason = ("something makes it, but nothing this era can run "
                          "- correctly gated out, not a missing entry")
            elif material not in producers_of:
                reason = "no production entry at all"
            else:
                reason = "every producing recipe needs an input with no path of its own"
            print("   %-26s consumed by %4d tree node(s) - %s"
                  % (material, tree_consumed.get(material, 0), reason))


def _print_unproductive_cycles(unproductive_cycles):
    if unproductive_cycles:
        print()
        print("UNPRODUCTIVE CYCLES (Complaints/31) - a material with a path "
              "back to itself that consumes more of a good than the cycle "
              "yields, or that never bottoms out in labour or an extracted "
              "good, named rather than only reported through the materials "
              "it takes down with it:")
        for message in unproductive_cycles:
            print("   %s" % message)


def _print_energy_summaries(production_entries, resolvable_materials):
    # A set, not a list: a CONVERSION recipe's own output can be one of the
    # three carrier names themselves (mechanical_mj_motor outputs
    # mechanical_mj while consuming electrical_mj to do it), and several
    # conversion techniques compete for the same carrier, so without
    # deduping this would print "mechanical_mj" once per competing
    # technique rather than once.
    energy_priced = sorted(set(
        material for recipe_id, entry in production_entries.items()
        for material in (entry.get("outputs") or {})
        if any(entry.get(energy_key) for energy_key in ENERGY_CARRIER_FIELDS)
        and material in resolvable_materials))
    if energy_priced:
        print()
        print("%d material(s) draw on the energy market (thermal_mj, "
              "mechanical_mj and/or electrical_mj, priced via "
              "data/production/70_energy.json - see ENERGY in the module "
              "docstring) - their price above already includes it: %s"
              % (len(energy_priced), ", ".join(energy_priced)))

    energy_affected = sorted(
        material for recipe_id, entry in production_entries.items()
        for material in (entry.get("outputs") or {})
        if entry.get("energy_mj") and material in resolvable_materials)
    if energy_affected:
        print()
        print("%d material(s) are still UNDERPRICED because their recipe "
              "needs energy_mj that none of the three energy markets can "
              "supply - a technology this script cannot yet cost, not the general gap "
              "the other %d materials above just closed (a real lower "
              "bound, not a wrong answer - see ENERGY in the module "
              "docstring): %s"
              % (len(energy_affected), len(energy_priced), ", ".join(energy_affected)))


def _print_unanchored_byproducts_summary(unanchored_byproducts):
    if unanchored_byproducts:
        print()
        print("%d material(s) marked (*) below are MINOR JOINT BYPRODUCTS "
              "whose printed price is a mass-split artifact of joint-cost "
              "allocation, not an independently derived number - see JOINT "
              "BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR in this file's "
              "module docstring, and run --why on one of them:"
              % len(unanchored_byproducts))
        for material in sorted(unanchored_byproducts):
            print("   %-26s value share of its batch: %5.1f%%"
                  % (material, 100.0 * unanchored_byproducts[material]))


def _print_price_table(resolvable_materials, chosen_recipe_by_material, unanchored_byproducts, prices):
    print()
    print("%-30s %16s  %s" % ("material", "price (hours)", ""))
    for material in sorted(resolvable_materials):
        recipe_id = chosen_recipe_by_material.get(material, "?")
        technique_note = "" if recipe_id == material else ("  [%s]" % recipe_id)
        flag = " (*)" if material in unanchored_byproducts else ""
        print("%-30s %16s%s%s" % (
            material, format_hours(prices[material]), flag, technique_note))


def _run_default_report(arguments, rent_hours_per_kg_by_material, converged, iterations_run,
                         residual, resolvable_materials, all_referenced_materials, unpriceable,
                         unreached_techniques, unclassified_techniques, all_production_entries,
                         producers_of, tree_consumed, unproductive_cycles, production_entries,
                         unanchored_byproducts, chosen_recipe_by_material, prices):
    _print_default_report_header(arguments)
    _print_rent_summary(arguments, rent_hours_per_kg_by_material)
    _print_convergence_summary(converged, iterations_run, residual, arguments,
                                resolvable_materials, all_referenced_materials, unpriceable)
    _print_unpriceable_materials(unpriceable, unreached_techniques, unclassified_techniques,
                                  all_production_entries, producers_of, tree_consumed)
    _print_unproductive_cycles(unproductive_cycles)
    _print_energy_summaries(production_entries, resolvable_materials)
    _print_unanchored_byproducts_summary(unanchored_byproducts)
    _print_price_table(resolvable_materials, chosen_recipe_by_material, unanchored_byproducts, prices)
    return 0 if converged else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--why", metavar="MATERIAL",
                        help="full recursive cost breakdown for one material")
    parser.add_argument("--compare", action="store_true",
                        help="computed price vs prices.json book price, as a "
                             "ratio, worst disagreement first")
    parser.add_argument("--damping", type=float, default=DAMPING_FACTOR,
                        help="fixed-point damping factor (default %.1f)" % DAMPING_FACTOR)
    parser.add_argument("--civ", metavar="CIVILIZATION",
                        help="solve using only the techniques this civilization "
                             "can actually run, from its starting_techs (e.g. "
                             "rome_100ad). Without this the solve is UNDATED and "
                             "will happily price Roman electricity off a "
                             "photovoltaic panel - see THE SOLVER NOW HAS A "
                             "NOTION OF WHEN, above, and Complaints/39")
    arguments = parser.parse_args(argv)

    _tree, prices_json, nodes, _wages_unused, _goods_unused = simulator.load()
    if not isinstance(nodes, dict):
        nodes = {node["id"]: node for node in nodes}

    production_entries, duplicates = load_production()
    if duplicates:
        print("REFUSING TO SOLVE: data/production/ has duplicate material "
              "keys, which validate_production.py should never let through:")
        for duplicate in duplicates:
            print("  %s" % duplicate)
        return 1

    era_gate_result = _apply_era_gate(arguments, production_entries)
    if era_gate_result is None:
        return 1
    (all_production_entries, production_entries, unreached_techniques,
     unclassified_techniques) = era_gate_result

    wage_by_trade = wage_ratios_by_trade(prices_json)
    producers_of = build_producers_index(production_entries)

    # RENT ON EXTRACTED MATERIALS (see the module docstring). Computed once,
    # against this solve's own (possibly era-gated) production_entries and
    # wage table, before the iteration starts - see
    # rent_hours_per_kg_by_ore_material's own docstring for why it does not
    # need to be recomputed every round.
    rent_hours_per_kg_by_material = rent_hours_per_kg_by_ore_material(
        production_entries, wage_by_trade)

    # RENT ON ARABLE LAND (see sim/world/land.py's own module docstring).
    # A separate mechanism from ore's - the margin of cultivation over a
    # civilization's own held regions, not a deposit's grade - but wired in
    # the SAME dict, because recipe_cost_and_allocation does not care which
    # mechanism produced a material's rent, only that one exists. Uses
    # `arguments.civ` when given (land, unlike ore, is genuinely per-
    # civilization) and Rome's own territory otherwise - see
    # land_rent_hours_per_iugerum's own docstring for why.
    rent_hours_per_kg_by_material.update(
        land_rent_hours_per_iugerum(production_entries, wage_by_trade,
                                    civilization_id=arguments.civ))

    unproductive_cycles = []
    resolvable_materials = compute_resolvable_materials(
        production_entries, producers_of, diagnostics=unproductive_cycles,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)

    tree_consumed = materials_the_tree_consumes(nodes)
    all_referenced_materials = set(tree_consumed) | set(producers_of)
    for entry in production_entries.values():
        all_referenced_materials |= set((entry.get("inputs") or {}).keys())
    unpriceable = sorted(all_referenced_materials - resolvable_materials)

    prices, iterations_run, residual, chosen_recipe_by_material = solve(
        production_entries, producers_of, resolvable_materials, wage_by_trade,
        damping=arguments.damping,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)

    converged = residual < CONVERGENCE_TOLERANCE
    unanchored_byproducts = minor_joint_byproducts_are_unanchored(
        production_entries, chosen_recipe_by_material, prices, wage_by_trade,
        rent_hours_per_kg_by_material=rent_hours_per_kg_by_material)

    if arguments.why:
        return _run_why_report(arguments.why, all_referenced_materials, production_entries,
                                producers_of, resolvable_materials, prices, wage_by_trade,
                                chosen_recipe_by_material, rent_hours_per_kg_by_material)

    if arguments.compare:
        return _run_compare_report(prices_json, resolvable_materials, prices, unanchored_byproducts)

    # Default: every material's price, in labour-hours.
    return _run_default_report(arguments, rent_hours_per_kg_by_material, converged, iterations_run,
                                residual, resolvable_materials, all_referenced_materials, unpriceable,
                                unreached_techniques, unclassified_techniques, all_production_entries,
                                producers_of, tree_consumed, unproductive_cycles, production_entries,
                                unanchored_byproducts, chosen_recipe_by_material, prices)


if __name__ == "__main__":
    sys.exit(main())
