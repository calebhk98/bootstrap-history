# A handover keeps the replacement's held nodes but drops their finish years and what it had heard of

**Status:** open - found while moving the held sets into the knowledge module

`HandOverTechniques` (`sim/knowledge/module.py` `hand_over_techniques`, sent by `sim/engine/seat_move.py` `move_seat`) merges the
replacement's `done` and `granted` into the leaver's knowledge record, and the leaver's record then becomes the replacement's
(`MOVED_FIELDS` in `seat_move.py` carries the whole `modules` slot). The replacement's own `done_year` and `revealed` are
dropped with its old record. A node the replacement held before the handover therefore stays held but has no finish year
(`done_year` answers nothing for it, so `earliest_done_year` and the year-built readers fall back to their default), and what it
had heard of under fog is forgotten (a fogged replacement sees less than before the handover).

The move kept the behaviour. Reproduce on `sim/tests/seat_handover_fixture.py`: give the heir a node in its `KnowledgeSeat.done`
with a `done_year`, hand the leaver's seat to it, and read `techniques_by_seat()` and `done_year()`.
What it would take: merge `done_year` (the earlier year wins, as `earliest_done_year` already reads it) and `revealed` in
`hand_over_techniques`, with a test calling that handler on two `KnowledgeSeat`s.
