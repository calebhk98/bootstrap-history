# A project that needs a measuring instrument you lack fails as a cost, not as lost information

**Status:** partly - the `diagnosis_instrument` mechanic exists and is pinned by sim/tests/test_failure_needs_instrument.py; only two nodes carry it, the rest is 377

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 6 (the tacit supply chain and the purity trap).

## What is wrong

A very pure material or process can be attempted with no instrument able to tell why a batch failed. The game treats the failure like any other: money is lost and the odds are the node's `risk`. The review's sharper point is that when you cannot measure the cause, a failure should teach nothing, and the player should know it. Compare 241 (failures are generic) and 124 (no lever against failure risk); neither covers diagnosability.

## Why it matters

Without it the retry learning curve (`_retry_risk_multiplier` in `sim/engine/projects_progress.py`) rewards every failure equally, so an unmeasurable process gets easier by brute repetition, which the history of purity-limited technologies contradicts.

## What it would take

Tag the nodes whose failure modes need an instrument (data on the node, for example a required measurement capability), and let the retry multiplier improve only when a held instrument could have identified the cause; otherwise report the failure as uninformative. Must be data-driven (`CLAUDE.md` 4.7). Test: the same node fails twice with and without the instrument and the second-attempt risk differs.

Owner decision (2026-10-02): important to get right.

Done: a node may declare `diagnosis_instrument` (see `data/branches/MECHANICS.md`). Without the named instrument its failures add no retry learning (`ProjectsState.uninformed_failures`) and the report names the missing instrument and the figure needed; with it the report gives the figure reached against the figure needed. The reached figure is a labelled placeholder (`SHORTFALL_FACTOR_RANGE`), not yet derived from process quality. Remaining: 377.
