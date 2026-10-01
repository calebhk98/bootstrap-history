# `compact` output is longer than the normal screen

**Status:** closed - 'compact' is now a short summary built in sim/engine/proto/compact.py (state, step, why, stuck), separate from 'json'; it was larger than the text screen, now smaller than both (test_compact_mode)

`help commands`: "'compact' implies 'json' and ... adds a small shared set of ... fields". At 507 AD `state compact` was 10,747 bytes of JSON and `state` 4,250 bytes of text. For a script or agent trying to read less, compact is worse.

What it would take: make compact a genuinely short summary (the fields a turn needs), separate from full json.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
