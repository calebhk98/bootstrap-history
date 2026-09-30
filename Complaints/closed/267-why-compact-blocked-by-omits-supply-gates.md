# `why ... compact` returns `blocked_by` with only missing prerequisites, so items gated on a supply (manganese, nitre beds) look unblocked

**Status:** closed

B: `why ... compact` returns `blocked_by: []` for items gated on "a manganese supply ... any of mat_manganese", so scripts and players following `blocked_by` miss them; A had the same experience with bulk steel ("technology appears research-ready but beginning exposes a missing manganese supply").

Cause: `sim/engine/proto/compact.py` builds `blocked_by` from `out.get("missing_prerequisites")` only; the `req_any` groups (supplies and alternatives resolved by `substitution_quality`, `sim/engine/projects_starting.py`) and the material bill are not included. Checked: `why mat_bulk_steel compact` lists the missing prerequisite ids and no supply.

What it would take: add unmet `req_any` groups and the binding material to `blocked_by` (under fog, only what `why` already reveals), and a `blocked_kind` (knowledge, specialist, material supply, capital, calendar) per entry. Related: 129 (blocked messages do not say which kind), 179 closed, 268.


Found in the final blind playtests of this branch (Rome 100 AD and Mexica 1500 fog runs; B annoyances; A section 5). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`, `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.
