# Extreme late-game wealth is not inherently a bug

**Source:** playtest findings document, ECON-003. **Status:** Preserve /
balance principle, filed as a complaint so the reasoning is on the record
rather than only in a player document.

## The player's point

A modern-informed founder introducing better metallurgy, guns, lenses,
printing, improved food production, machinery, medicine, finance and power
into a preindustrial economy should be capable of becoming fantastically
wealthy. The realism gap, per the player, is not that the founder gets rich;
it is that nothing yet captures *who else* gets a share of the gains, and
*what new constraints* appear at that scale. Their explicit recommendation:
do not solve the late-game money problem by crushing venture revenue until
the player stays poor.

## Why this belongs in the complaints folder rather than only the playtest document

Several of the other findings in this same document (`LATE-001` through
`LATE-008`, filed as `Complaints/107` through `Complaints/114`) propose
systems - independent firms, a state fiscal model, capital markets,
political interest groups - that would each, as a side effect, reduce how
much of the gains the founder personally keeps. A future agent implementing
any one of those in isolation could read "founder's monopoly margins fall"
in `LATE-001`'s own text and conclude the goal is to make the founder poorer
overall, then reach for a revenue-nerf as the fastest way to get there. This
complaint exists to say that reading is wrong before anyone acts on it: the
target is redistribution and new constraints on an economy that keeps
growing, not a smaller economy.

## How this sits against CLAUDE.md

This is squarely inside §3.2: "the baseline is allowed to get worse while
the mechanisms that will make it good are being built," but that licence is
for adding real mechanisms (independent firms competing away margin, a state
that taxes and requisitions, political actors that extract concessions), not
for subtracting revenue directly. A blanket revenue cap or multiplier crushed
to keep late-game wealth low would itself be exactly the kind of hardcoded
outcome §3.1 forbids: a historical result (the founder should end up merely
comfortable, not fantastically rich) encoded directly rather than falling
out of lower-level state (competition, taxation, political risk).

## What already exists that bears on this

`sim/engine/society_state_pressure.py` already has *some* mechanism that
responds to extreme wealth: `prominence_hazard()` and `household_scale()`
both read `household.capital` against fixed thresholds
(`EMINENCE_WEALTH_VISIBLE_THRESHOLD` at 250,000 denarii,
`HOUSEHOLD_WEALTH_SATURATES_AT` at 10,000,000 denarii) to drive state
notice and hazard probability. That mechanism is real and already responds
to wealth. Its limitation, that it saturates rather than continuing to
change qualitatively at extreme fortunes, is a separate finding
(`BAL-002`, filed as `Complaints/118`); this complaint is only about not
reaching for revenue suppression as the fix for either problem.

## Cross-references

Read together with `Complaints/107` (LATE-001, independent firms),
`Complaints/109` (LATE-003, state fiscal model), `Complaints/114` (LATE-008,
political interest groups) and `Complaints/118` (BAL-002, wealth/notice
saturation). None of those documents currently say "reduce venture revenue"
either; this complaint exists to make sure that stays true as they are
implemented.
