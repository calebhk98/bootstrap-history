# A seat cannot be handed over: its knowledge, holdings and notes are lost when the founder dies

**Status:** done - the handover command moves the seat's fields, its debts and claims, and every store keyed by its id; the replacement must be an empty seat (cash, debts and known techniques merge; works, staff, holdings, institutions and arrears are refused with `replacement_not_empty`)

Part of Complaint 481 (A player cannot play as a country).

Notes keyed to a country (597) should survive a handover the same way.

**What is wrong.** A seat ends when its founder dies and is dropped from the year; nothing passes its knowledge, holdings or notes to another player. The group asked for this so a replacement player inherits what the leaver knew.

**Evidence.** `sim/engine/seat_run.py` (seat ends at death); `sim/engine/year_run.py` (seat dropped from the year).

**Why it matters.** A multiplayer game of any length loses the leaver's work every time a player changes.

**What it would take.** A handover command (and the matching protocol text) that moves a seat's known nodes, holdings and notes to a named replacement seat, for a household seat and, once 594 exists, a country seat.

**Test.** A test hands a seat over and reads the replacement's fields: the same known nodes, holdings and notes, and the old seat is gone from the year.

**What was done.** `hand_over_seat` renames the leaver's id to the replacement's in the actors' book and contract registry (facility draws, term loans as borrower and lender, deposits, bonds, named lenders), the economy record's agent-keyed stores (`AGENT_KEYED_FIELDS` in `sim/economy/record.py`), the other seats' offers, shares, licences and disclosures, the other actors' records and the year's market flows (`sim/engine/seat_handover_rekey.py`, `sim/rekey.py`). Nothing is paid, so no total moves. A loan between the leaver and the replacement ends, since it would be owed to itself.

**Tests.** `sim/tests/test_seat_handover_accounts.py` (debt, claims, goods, stores, refusals), `sim/tests/test_seat_handover_whole_game.py` (slow: debt carried in a real game, the save names the leaver nowhere).
