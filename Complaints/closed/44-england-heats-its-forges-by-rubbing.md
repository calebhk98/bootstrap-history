# Medieval England makes process heat by friction, and the data predicted it would not

Emergent, correct by the model's own rules, and wrong. Found immediately
after the waterwheel's iron gate was fixed, which is the point: this was
invisible while no civilisation could build a waterwheel at all.

## What happened

    england_1300   mechanical_mj  0.00275  [mechanical_mj_waterwheel]
                   thermal_mj     0.00281  [thermal_mj_friction]

    rome_100ad     mechanical_mj  3.704    [mechanical_mj_human_muscle]
                   thermal_mj     0.00855  [thermal_mj_charcoal]

England can build a waterwheel, so its mechanical power costs 0.00275 hours
a megajoule instead of the 3.704 that human muscle costs - a factor of 1,347,
which is not a bug and is the whole reason Domesday counts 5,624 mills.
Converting that shaft work to heat by friction is nearly lossless, so heat
via friction lands at 0.00281, undercutting charcoal's 0.00855 by three
times. The solver then does exactly what choice of technique means and picks
it.

`data/production/70_energy.json`'s own `thermal_mj_friction` entry predicts
in writing that this should never be chosen. It is now chosen. The entry's
author was right about the history and the model disagrees with them.

## Why the model is wrong and the author is right

`sim/solve_prices.py`'s docstring says it outright, under TEMPERATURE, NOT
MODELLED THIS ROUND - A DECISION, NOT AN OVERSIGHT: a megajoule of heat is a
megajoule of heat, with no notion of what temperature it arrives at.

That is exactly the distinction this result needs. A friction brake on a
mill shaft delivers low-grade warmth spread over a large surface. A charcoal
fire delivers a small, intense, high-temperature zone. They are both "heat"
in joules and they are not interchangeable for any of the things process heat
is actually FOR in 1300 - you cannot smelt, forge, fire pottery or melt glass
with a warm bearing, and those are most of the thermal demand in the tree.

So this is not a new defect. It is the known temperature gap, which was
harmless while it was only a note in a docstring, becoming a wrong answer the
moment cheap mechanical power existed to feed it. Rumford's cannon-boring
observation is the reason the physics is real; the absence of any medieval
friction furnace is the reason the economics is not.

## What it would take

Not a special case for friction, and not deleting the entry - the same
mistake `Complaints/39` warned against for the photovoltaic panel. Deleting
it would make this answer look right while leaving the model unable to tell
a forge from a warm room, and the next cheap low-grade heat source would
walk straight back in.

The real fix is to give heat a temperature, so a process states the
temperature it needs and a technique states the temperature it can reach.
The tech tree ALREADY has the vocabulary for this - `cap_heat_0700`,
`cap_heat_1100`, `cap_heat_1300`, `cap_heat_2000`, `cap_heat_3000` are nodes
in it, and two of them are already used as `requires_node` gates. So the
concept exists in the data and only the energy market is blind to it.

That is a real piece of work and should not be bolted on in the middle of a
wiring round. Recorded here so the next person does not rediscover it by
watching a medieval forge run on a mill brake.

## Also worth keeping

Rome is unaffected and correctly so: it still burns charcoal, because its
`starting_techs` lack `cap_power_water` regardless of the iron gate. The two
civilisations diverging here - one on water, one on muscle and charcoal - is
the first time the era gate has produced a genuinely different ECONOMY rather
than just a different list of available techniques.

## Fixed, by giving heat a temperature rather than by deleting friction

    england_1300  thermal_mj  0.00281 [friction]  ->  0.00855 [charcoal]
    rome_100ad    thermal_mj  0.00855 [charcoal]  ->  unchanged

And the reason is general rather than a special case naming friction, which
is the part that matters. `--why thermal_mj --civ england_1300` prints:

    other techniques considered and rejected:
      thermal_mj_coal      (more expensive at current prices)
      thermal_mj_friction  (reaches 100.0, this era needs >= 700.0)

Coal loses on cost, friction loses on physics, from one rule.

A technique now states the temperature it reaches and a process the
temperature it needs, and `solve()` never even offers a technique that falls
short - so choice of technique picks the cheapest one THAT WORKS. Every
number comes from the tree's own `cap_heat_*` rungs rather than a new scale
invented beside them: charcoal and coal at 1100 C from `cap_heat_1100` ("a
man on a bellows tops out near here"), electrical resistance at 3000 C from
`cap_heat_3000` ("no chemical flame reaches here"), and the pool's default
floor at 700 C from `cap_heat_0700`, the tree's lowest rung and a free
universal capability.

Friction's own 100 C is Rumford's 1798 cannon-boring experiment: a
horse-driven borer brought a box of water to a rolling boil and no hotter,
because past boiling the heat drives evaporation rather than temperature.
The entry's own "warm bearing" character, given a real number.

### Two things worth keeping from how this was done

The friction entry was NOT deleted, which was the explicit warning in this
complaint and in `Complaints/39` before it. It is still there, still
correct, still the cheapest heat per megajoule - and now simply unable to
reach a forge. The next cheap low-grade heat source will meet the same rule
instead of walking in unopposed.

And the mechanism is dimension-agnostic on purpose. The stakeholder asked for
a torque cap in the same breath as temperature; adding one is a single entry
in `CAPABILITY_CAP_FIELDS` plus a `torque_reached_nm` on the waterwheel,
because the comparison code does not know or care which physical quantity it
is comparing. Pressure would go in the same way.

### What is deliberately left

Four real `thermal_mj` consumers in files another agent owned were left
unannotated - refined petroleum, Solvay soda, plaster and rosin. Their own
`yield_basis` already states operating temperatures (plaster about 150 C,
rosin about 160 C) comfortably inside what charcoal reaches, so annotating
them changes no outcome today. Recorded in `_SCHEMA.md` as the next thing to
touch.

And a finding that saves the next person the trip: the iron entries
(`pig_iron_kg`, `iron_bloom_kg`, `iron_bar_kg`, `tool_steel_kg`) do not draw
on the shared `thermal_mj` pool at all. They charge `charcoal_kg` through
`inputs` directly, which is the schema's own "usually 0 for pre-industrial
processes, where the fuel IS the energy". A temperature requirement on them
would be a no-op.
