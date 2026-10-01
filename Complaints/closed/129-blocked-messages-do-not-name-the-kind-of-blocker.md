# Blocked-project messages do not say which kind of blocker they are

**Status:** closed

The kind is classified in one place (`start_blockers`, `sim/engine/blockers.py`) and read by the start refusal, `why`, `why compact`, `stuck`, `path` and the heard-of rows of `available`. Remaining: the "calendar" kind (a floor still to serve) is not a blocker entry, and the `stuck` sentences for work in hand, raw materials and shut ventures are still their own text without a kind label.

**Source:** `reports/TOP_PROBLEMS.md` item 8 (finished knowledge versus active supply or capability, inconsistently surfaced).

## What is wrong

The game's best distinction is between knowing a thing and having it running
(closed concern, missing material supply, missing staff). A blocked project's
message does not consistently say which of these it is. The report's examples:
sulfuric-acid chemistry known but no supply, a completed plant that must be
open for downstream supply, a concern that auto-closed from attrition. Only
some paths say "you have built it already, so `open X`".

## Evidence

- `sim/engine/projects_starting.py` - `_START_REASON_CHECKS` returns free-form
  strings, one per check; there is no structured blocker kind, and only
  `_patron_advice` (same file) distinguishes "built but closed".
- `python3 sim/simulator.py why <node>` for a node behind a closed concern, a
  node behind a missing material, and a node behind missing knowledge: compare
  how each blocker is worded.

## Why it matters

A player who reads "knowledge missing" when the truth is "concern closed" (or
the reverse) spends years on the wrong fix. Overlaps `Complaints/86` (completion
wording) but this is about the refusal side.

## What it would take

Have each check return a kind (`knowledge`, `closed`, `material`, `staff`,
`political`, `funds`) alongside its text, render the kind as a fixed leading
label in `why`, `start` refusals and `stuck`, and expose it in the JSON
protocol. Test: one node per kind, asserting the label.

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): asks that a blocked technology show the kind of block separately: KNOWLEDGE, SPECIALISTS, MATERIAL SUPPLY, CAPITAL, CALENDAR each READY or not, and that the capacity-report suggestions sit next to the blocked project (complaint 267 is the compact-output half: `blocked_by` omits supply gates).

**Also left:** `BlockersMixin._BLOCKER_KIND_BY_CHECK` (`sim/engine/blockers.py`) maps each start check to its kind by the check function's name, and an unlisted check falls back to "unavailable". A new check added to `_START_REASON_CHECKS` without an entry is therefore mislabelled silently. Each check should declare its own kind, or a test should fail when a check has no kind.

**Also done:** every start check declares its kind through `blocker_kind`, a test fails when one does not; `stuck` rows carry a kind (including calendar per project) and show it as a label.
