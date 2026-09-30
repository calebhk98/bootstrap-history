# Fog messages become repetitive without giving directional information

**Status:** open

Repeated queries could return effectively the same "one prerequisite you have not heard of" for years. This is technically fog-safe but eventually provides no decision support.

## WHAT THE PLAYER SAW

The school remained blocked after legal status, teachers, university, paper, textbooks, endowment, etc. The missing item eventually turned out to be positional/place-value arithmetic. There was little way to infer that category from the blocker.

## WHY IT MATTERS

Without semantic hints about why something is blocked, the player cannot strategically work around the obstacle or redirect effort. The same repetitive message year after year creates noise rather than guidance.

## WHAT WOULD RESOLVE IT

Fog should hide identity, not necessarily semantic category. Examples:

- "missing a teachable quantitative curriculum foundation"
- "missing a way to reproduce texts at scale"
- "missing high-temperature measurement"
- "missing a source of traction animals"
- "missing a precision-machining foundation"

Only improve the hint when the player has discovered enough nearby knowledge to justify it.

## WHERE IT LIVES

`sim/engine/fog.py::fog_scrub()` and related fog rendering logic. Also affects `sim/engine/proto/techtree.py` where capability reasons are constructed.

## Confidence

Design recommendation

## Cross-references

Related to BUG-006 (fog scrubbing can leak hidden IDs). UX-004 also addresses incomplete search discoverability under fog.

Also reported (England 1300 fog playtest): `case_hardening` stayed blocked by one completely unheard prerequisite for years, and epidemiology likewise; searches around metallurgy, steel, furnace, charcoal and temperature gave no clue, so the tester drifted into "adjacent-branch fishing". The missing step turned out to be a workshop and laboratory culture, found only by browsing wider name sets. The tester suggests thematic hints that keep the identity hidden ("you are missing a heat-treatment control idea", "this depends on a better way to judge temperature") and, separately, a related-names search (see 196). They also note that reasoning from visible names worked well and made fog feel fair, so hints should stay coarse. Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`.
