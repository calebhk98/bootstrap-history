# The energy file builds machines that nothing else can buy

Raised by the stakeholder, who put it as: the electricity file should not
care about the costs of materials, that belongs to the pricing side.

The literal version of that is wrong and worth saying why before the part
that is right, because the two are easy to confuse.

## What the energy file does NOT do

It does not calculate a cost. `data/production/70_energy.json` holds
physical facts only - a square metre of photovoltaic panel intercepts
sunlight and yields 1180 MJ a year for 25 years, and building it takes 10 kg
of glass, 1.8 kg of aluminium, 0.15 kg of copper, 0.5 kg of silicon and 4.5
hours of skilled labour. Not one price appears anywhere in the file.
`sim/solve_prices.py` turns that structure into a price. The separation the
complaint asks for is already the design.

Nor was anything tuned. The suspicion was that someone had raised the price
of solar because it came out too good. The opposite happened: every number
in the entry is sourced (1000 W/m2 at AM1.5, about 5 kWh/m2/day of real
insolation, 18% conversion, a 25-year service life), and the entry states in
its own words that its price is a LOWER BOUND, because `silicon_kg` omits
crystal growth, wafer sawing, doping, metallisation and lamination. The
honest response to "this comes out too cheap" is to say so and leave the
number alone, and that is what was done.

## And the economics cannot be separated, either

A panel costs aluminium. Aluminium needs electricity. Electricity can come
from a panel. That circle is real, and it is not a modelling failure - it is
what an economy IS. The solver's whole cycle machinery exists for it: see
`_component_is_productive` and `Complaints/31`. Severing energy from
material prices would not make the model cleaner, it would make it wrong,
because there is no order in which you can price these things one at a time.

## What IS wrong

Six of the twelve energy entries carry a bill of materials for a MACHINE:

    mechanical_mj_waterwheel                 timber, iron bar, stone
    mechanical_mj_heat_engine_atmospheric    iron bar, timber, stone
    mechanical_mj_heat_engine_compound       iron bar, copper, stone
    mechanical_mj_heat_engine_modern_steam   iron bar, copper, stone
    electrical_mj_dynamo                     iron bar, copper wire
    mechanical_mj_motor                      iron bar, copper wire
    electrical_mj_photovoltaic               glass, aluminium, copper, silicon

A waterwheel is not a kind of energy. It is a manufactured good that happens
to produce energy, and its construction is a recipe like any other recipe in
this directory. Right now that recipe exists ONLY as an inline sub-object
inside an energy-conversion entry, which has three consequences:

**Nothing else can buy one.** There is no `waterwheel` or
`photovoltaic_panel_m2` material key anywhere. A founder who wants to build
a mill, or a second actor who wants to buy one, has nothing to name. That
runs straight into CLAUDE.md section 4: make the founder's mechanisms
general enough that other actors can use them. A machine that can only be
amortised, never owned, is not general.

**The same machine cannot be shared between uses.** A waterwheel drives a
mill, a trip hammer, a bellows and a dynamo. Four uses, and the current
shape would need the build bill written four times, drifting apart as
authors edit one and not the others.

**A machine cannot be improved.** Better bearings or a better wheel should
change every process that runs on one. Inline bills make that four edits
that nobody will remember to make together.

## The shape of the fix

Promote each machine to its own production entry with a material key, and
let the energy entry consume it - `N square metres of panel per 1000 MJ per
year` rather than a copy of the panel's build bill. That is the same move
`capital` already makes for a blast furnace, taken one step further: the
furnace, too, is a thing somebody builds.

This is NOT urgent and should not pre-empt wiring the solver into the
engine. It is a data reshape with no behavioural consequence for the price
solve - the same materials and labour go in either way, so the computed
price of energy should come out unchanged, and that invariance is the test
of whether the reshape was done right. The before-prices, recorded on the
ungated solve at the commit that raises this:

    electrical_mj   0.00122   via electrical_mj_photovoltaic
    mechanical_mj   0.00201   via mechanical_mj_motor
    thermal_mj      0.00125   via thermal_mj_electrical_resistance

Reshape, then require those three to come back identical. If they move, the
reshape changed physics rather than layout, and something was lost.

(Those three chosen techniques are themselves the subject of Complaints/39 -
this is an undated solve, so every carrier roots in a panel. The invariance
test holds regardless of which technique wins, which is why it is the right
test to use before the gate is finished.)

## What this is not

Not a case for a separate energy domain that knows nothing about costs.
Energy has to know what a panel is made of, because that IS its cost. The
complaint is about WHERE the panel's recipe lives, not about whether energy
is allowed to depend on it.
