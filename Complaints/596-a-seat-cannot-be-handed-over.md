# A seat cannot be handed over: its knowledge, holdings and notes are lost when the founder dies

**Status:** open

Part of Complaint 481 (A player cannot play as a country).

Notes keyed to a country (597) should survive a handover the same way.

**What is wrong.** A seat ends when its founder dies and is dropped from the year; nothing passes its knowledge, holdings or notes to another player. The group asked for this so a replacement player inherits what the leaver knew.

**Evidence.** `sim/engine/seat_run.py` (seat ends at death); `sim/engine/year_run.py` (seat dropped from the year).

**Why it matters.** A multiplayer game of any length loses the leaver's work every time a player changes.

**What it would take.** A handover command (and the matching protocol text) that moves a seat's known nodes, holdings and notes to a named replacement seat, for a household seat and, once 594 exists, a country seat.

**Test.** A test hands a seat over and reads the replacement's fields: the same known nodes, holdings and notes, and the old seat is gone from the year.
