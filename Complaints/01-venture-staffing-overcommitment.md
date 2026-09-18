# Venture staffing can appear overcommitted without an explanation

**Type:** UI / rules clarity  
**Priority:** Medium
**Status (project-wide audit, 2026-09-18): PARTLY RESOLVED.** `_staff_fraction_note` (`sim/engine/proto/state.py`) now explains fractional FTE counts generally on `state`/`labour` ("these are continuous full-time-equivalents, not a count of whole people"). The ventures-screen-specific overcommitment breakdown (effective capacity, required FTE, and overcommitment behaviour, spelled out on that one screen) was not separately confirmed. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

At 103 AD, `ventures` reported 1 total craftsman supporting 1.3 craftsman-years across three concerns, while free craftsmen was `0` (not negative) and no concern closed.

## Why it matters

The player cannot tell whether fractional staffing is intentionally soft-overcommitted, rounded, or incorrectly reported.

## Suggested check

Verify the staffing rule and make the screen state the effective capacity, required FTE, and overcommitment behavior explicitly.
