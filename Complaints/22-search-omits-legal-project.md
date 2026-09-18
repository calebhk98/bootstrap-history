# `available find` can omit a legal project

**Type:** Search bug  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `matches_find()` (`sim/engine/proto/techtree.py`) now matches every query word against id, name, doc anchor and aliases. Checked directly: `prc_lapping_plate`'s name ("Lapping with cast-iron plate and abrasive compound") now matches a `"lapping plate"` query. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

After Bayer alumina, `available find "lapping plate"` returned no match, but `why prc_lapping_plate` said `STATUS: CAN START NOW`. It was startable only because the player already knew the ID.

## Impact

A blind player can conclude a legal route is unavailable.

## Suggested check

Index all currently legal projects in `available find`, including normalized names and aliases.
