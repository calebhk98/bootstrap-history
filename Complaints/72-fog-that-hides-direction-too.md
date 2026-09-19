# Fog messages become repetitive without giving directional information

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
