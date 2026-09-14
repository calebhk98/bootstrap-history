# Open work, verified 2026-09-11

Every claim below was checked by running the code today, not carried forward
from an earlier list. The previous version of this file was mostly stale
within hours, so anything here that is fixed should be deleted rather than
annotated.

## Verified still open

### `why`'s leaf detection does not scan `req_any`

Confirmed: `req_any` appears nowhere in the explain path. A node whose only
dependents reach it through a `req_any` substitution group is reported as a
dead end. Found when three Norse starting technologies were reported as
dead ends and two of them were not.

### Reputation rewards building, not running

Confirmed: the completion reward reads state interest, tier and revenue and
never looks at `operating`. So it can be maximised by building things you
never open. The fix is to make it follow what you run, the way revenue
already does.

### Six pieces of real infrastructure carry no upkeep

`en_transmission_line`, `en_gas_holder`, `en_grid_interconnection`,
`en_thermal_station`, `en_penstock`, `sea_merchant_ships_large`. These are
the opposite of the technique-with-upkeep error already fixed: real plant
with real standing costs, charging nothing.

### The simulator killed its own process during a long step

A play tester lost several minutes of play when `step 3` silently killed the
process at 150+ staff and 220+ technologies. Not reproduced since. Worth
chasing before any long run is trusted, because it undermines every
measurement taken from one.

### `rush` on turn one is still a trap

The hours overcommitment is fixed and it now warns that it is a rule of thumb,
but a tester still watched it spike scandal to within a year of the line that
ends the run. The warning may not be enough.

## Ideas raised and not pursued

### Inflation that emerges rather than being scripted

Tractable, and the pieces exist: a money stock, a debasement event, real
output. `price level = money x velocity / real output` would already behave
correctly, with debasement raising the stock and industrialisation raising
output, and no number multiplied by hand. What no small model captures is
expectations, which is what makes real inflation interesting.

### Whether `commodities.py` should absorb the live throttle

Half done. `propagate_demand`'s chain attribution is wired in, so a shortage
is blamed on the link that actually broke. The rest of `commodities.py`
duplicates `resource_throttle` and `material_price_factor` for four
materials, and folding those together is a real judgement call rather than an
obvious win.

### Depth gap: `atomic_theory`

One node for Dalton to Perrin, about sixty contested years, in a tree that is
otherwise very finely grained. Flagged by the history audit as the single
largest compression.

## Verified fixed today, kept only as a record

The two rulebooks (a player capped at six scholars while auto_hire reached
146); institutions as quantities, which let the capability rule come off the
shelf; whole-number people; the anachronistic goal, now two devices with the
1951 junction transistor as the target; upkeep on techniques; revenue on
techniques, so you can no longer open positional notation as a shop; rubber
produced rather than bought; mine land, depletion and technology yield; the
goods market; the backward-chaining planner; auto_hire going through hire();
fog rewindable by save and reload; the save lost on a closed pipe; the log
not surviving a reload; a dead founder starting projects; the developer's
audit markers shipped in player prose; the test suite going from 425
seconds to 44; and military technology doing nothing (`society.
military_leverage()` now buys faster war recovery, a protection bonus once
you have a patron to hand it to, and a lighter state-funding penalty,
scaled by how much of the 111-node branch you have actually built).
