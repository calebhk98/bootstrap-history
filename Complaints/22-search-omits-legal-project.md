# `available find` can omit a legal project

**Type:** Search bug  
**Priority:** High

## Player evidence

After Bayer alumina, `available find "lapping plate"` returned no match, but `why prc_lapping_plate` said `STATUS: CAN START NOW`. It was startable only because the player already knew the ID.

## Impact

A blind player can conclude a legal route is unavailable.

## Suggested check

Index all currently legal projects in `available find`, including normalized names and aliases.
