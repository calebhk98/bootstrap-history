# Closed complaints

Twenty-eight complaints whose fix has landed and been verified against the
code rather than against the complaint's own closing paragraph. They were
moved here so `Complaints/` shows what is still open at a glance.

**They are kept, not deleted, and they are not dead weight.** Several are
referenced from live code and data - `sim/engine/core.py`, `sim/engine/
data.py`, `data/tech_tree.json`, three `data/branches/*.json` files and
`data/production/_SCHEMA.md` all cite one by path, because the reason a
mechanism is shaped the way it is usually lives in the complaint that forced
it. Every such reference was rewritten to `Complaints/closed/` when the
files moved; none was left dangling.

Three of them are worth reading even if you never hit the bug:

- **27 (non-deterministic simulation)** - `id()` is an address, not an
  identity, and reusing one as a cache key made the whole simulation
  irreproducible. Includes the hypotheses that were wrong and the probe
  whose own allocations suppressed the effect it was measuring.
- **30 (`treetool.py merge` discards branch edits)** - a tool silently
  dropping the work it was asked to merge.
- **33 (two undefined global reads)** - WITHDRAWN by its own author. The bug
  never existed; it was an artefact of a `git commit` taking the whole index
  in a shared checkout. Kept for the process lesson.

The status line at the top of each file records what closed it and how that
was verified. `docs/architecture/STATE_OF_THE_PROJECT.md` holds the full
table, including the complaints still open next door.

## What is NOT here

Complaints that are partly resolved, pinned on purpose, or unverified stay
in `Complaints/`. Two in particular are parked states rather than open bugs
and should not be closed by someone tidying up:

- **42** is PINNED, not fixed: a regression test holds a known-defect count
  at exactly 17 and fails in both directions, so the number can only move
  deliberately.
- **35** is a playthrough review, not a single bug, and several of its items
  remain entirely unaddressed.
