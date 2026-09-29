# Elite literacy can be pushed past its own stated ceiling by the mechanism that never checks it

## What the player saw

The Mexica run reported elite literacy around 99.8% while the same state
reported an elite-literacy ceiling of 97%.

## Verified against current code

Confirmed, and quantifiable without running the full scenario.

`literacy_ceiling_elite()` moved to `sim/engine/society_adoption.py:353-354`,
still a flat return of `LITERACY_CEILING_ELITE` (declared 0.97,
`society_adoption.py:343-351`).

`_advance_literacy()` (`society_adoption.py:436-496`), the schooling-driven
growth path, respects it correctly:

    eli_ceil = self.literacy_ceiling_elite()
    if eli < eli_ceil - 1e-6:
        eli_new = min(eli_ceil, eli + self.LITERACY_GROWTH_RATE_ELITE
                      * flow * (eli_ceil - eli))

`apply_tech_effects()` (`society_adoption.py:96-168`), the direct
tech-effect path, does not:

    elif field in ("literacy_general", "literacy_elite", "state_capacity"):
        before = float(self.civ.get(field, 0.0))
        self.civ[field] = max(0.0, min(1.0, before + delta))

This clamps to `[0.0, 1.0]` only - `literacy_ceiling_elite()` is never
consulted on this path at all. Any technology whose `_TECH_EFFECTS.json`
entry carries a `literacy_elite` delta can push `literacy_elite` straight
past 0.97, all the way to 1.0 if enough of them complete.

Quantified directly against the shipped data:

    python3 -c "
    import json
    d = json.load(open('data/civilizations/_TECH_EFFECTS.json'))
    total = 0
    for k, eff in d.items():
        if isinstance(eff, dict) and isinstance(eff.get('literacy_elite'), (int,float)):
            print(k, eff['literacy_elite']); total += eff['literacy_elite']
    print('sum:', total)
    "
    rag_paper 0.05
    printing_press 0.2
    if_movable_type 0.1
    school_founded 0.06
    academy_network 0.08
    corpus_written 0.04
    fin_lending_library 0.04
    arithmetic_positional 0.03
    sum: 0.6000000000000001

Eight technologies carry a direct `literacy_elite` delta summing to 0.60.
Mexica's own civ file starts `literacy_elite` at 0.4
(`data/civilizations/mexica_1500.json:303`). If all eight complete, the
direct-effect path alone takes `literacy_elite` from 0.4 to
`min(1.0, 0.4 + 0.6) = 1.0` - a full 0.10 past the "ceiling" - entirely
independent of whatever `_advance_literacy`'s own, correctly-clamped
schooling growth contributes on top. The player's observed 99.8% (rather
than exactly 1.0) is consistent with not every one of the eight having
completed, or with the run being read mid-transition.

Status: **confirmed in current code**, and quantified directly against
`_TECH_EFFECTS.json` and Mexica's starting value without needing to run the
scenario - the two code paths' inconsistency is visible from static
inspection, and the shipped data confirms the delta is large enough to
matter in an ordinary run, not only in a constructed edge case.

## Cross-references

No open complaint names this. `literacy_ceiling_elite()`'s sibling,
`literacy_ceiling_general()`, was not checked this session for the identical
defect - worth a follow-up check, since `apply_tech_effects()`'s clamp is
written once and applies to `literacy_general` on the identical code path
(`field in ("literacy_general", "literacy_elite", "state_capacity")`), and
`state_capacity` is a third value that may have the same "ceiling" framing
elsewhere in the engine and the same gap here. Not independently checked
this session; flagged as a likely-identical sibling bug rather than
confirmed.

## What would resolve it

The player states the two legitimate resolutions correctly, and both are
compatible with CLAUDE.md SS3.1/SS3.2 (this is an internal-consistency
question about what a displayed number means, not a hardcoded-outcome
question):

1. **If 0.97 is meant as a real hard ceiling**, clamp `apply_tech_effects()`'s
   `literacy_elite`/`literacy_general` branch to
   `min(self.literacy_ceiling_elite(), before + delta)` (and the equivalent
   general-literacy ceiling function) instead of the flat `min(1.0, ...)`.
2. **If technology is meant to be able to raise or bypass the ceiling**
   (arguably defensible: `printing_press` and `if_movable_type` carrying the
   two largest deltas here is a real claim about what movable type does to a
   literate elite, and a ceiling that cannot move at all as a civilisation's
   information technology changes is its own kind of unrealism, closer to
   what CLAUDE.md SS3.1 warns against for the *opposite* reason - a fixed
   number standing in for a mechanism), rename the "ceiling" language on the
   `literacy` screen to something that admits the exception, such as
   "schooling-driven ceiling," and state explicitly that direct technology
   effects can move past it. Silently exceeding a number the game itself
   calls a ceiling, with no reader ever able to tell which of the two this
   is, is the actual defect - not the raw fact that literacy can go past
   0.97.

## The invariant

    if a number is called a ceiling: literacy_elite <= literacy_ceiling_elite()

The player's own ARCH-002 phrasing, directly testable: complete the eight
`literacy_elite`-bearing technologies (or a synthetic subset summing past
`1.0 - starting_literacy_elite`) on a fresh `Sim` and assert
`s.civ["literacy_elite"] <= s.literacy_ceiling_elite()` afterward. Given the
sum above (0.60) already exceeds the room most starting civilisations have
under 0.97, this should fail immediately against current code without
needing a long run.
