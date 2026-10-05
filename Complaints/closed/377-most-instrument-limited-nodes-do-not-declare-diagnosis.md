# Most purity and tolerance limited nodes do not declare a diagnosis instrument

**Status:** closed - survey done: the measurement-limited capability ladders (tolerance, purity, vacuum, furnace temperature) and the nodes whose own text names a measured result (zone refining, electrorefining, vacuum pumps and melting, glass-to-metal seal, ruling engine, precision grinding/honing/boring/bearings) declare `diagnosis_instrument`; `sim/tests/test_diagnosis_instrument_survey.py` counts them per family and checks each instrument exists and is not already a prerequisite. Left undeclared: the ultra-high vacuum rung (no ionisation gauge node exists), the 10 micron rung (its instrument, the micrometer, is its own prerequisite), and the 1600 C rung (pyrometry is its prerequisite).

Split from 274. The `diagnosis_instrument` mechanic is in place but only two capability nodes use it. Every other node whose failure depends on purity, tolerance, vacuum or temperature measurement still teaches by brute repetition. `python3 sim/treetool.py judge` (script since removed; recover with `git show 97473f1:sim/treetool.py`) reports nodes that need such a rung; none yet reports a missing diagnosis instrument.

## What it would take

Tag the remaining nodes in `data/branches/` with the instrument that measures their result, derive the reached figure from process quality instead of the placeholder range, and let `why` show whether a failure would be diagnosable. Related: 274, 124, 241.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 274 (`closed/274-failure-without-an-instrument-is-a-cost-not-a-mystery.md`): failure without an instrument is a cost: the mechanic is built, only a few nodes declare it (this issue).
