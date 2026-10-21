# Slow-suite checks that are red on main

**Status:** open

A red slow suite on the default branch means every branch's slow run starts red and its own regressions are read against
noise. This file is the current list: one section per failing topic, naming the complaint that owns the fix. Where the subject
is an open design issue, that complaint pins the check or leaves it failing on purpose; it is never loosened to go green.
Older entries (the three topics this file first named, and the later regressions bisected on integration branches) are in
`Complaints/reports/558-history.md`; their topics have moved on.

Filled from the full slow run on 3cb9c9a0 (orchestrator).

Command: `python3 -m sim.tests --slow --timing` (cold: see 557 for the time cost; one process at a time).

## Failing topics

One section per topic, in this form:

### `<topic>`

- Failing check, as the runner prints it.
- Owning complaint.
- What would turn it green (fix, or pinned status with the test kept honest).

(No topics listed until the orchestrator's run fills this in.)
