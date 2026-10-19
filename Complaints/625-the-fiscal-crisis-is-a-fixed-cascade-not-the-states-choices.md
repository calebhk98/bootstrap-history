# The fiscal crisis is a fixed cascade, not choices of the state actor

**Status:** open

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Depends on 593 and 595; consumes 621 to 624 as options.

**What is wrong.** Short of money, `Government.advance` cuts every line by the same share, books arrears, shrinks the army, debases if it can, raises levies on visible taxpayers, and soldiers mutiny below a loyalty line, all in a fixed order.

**Evidence.** `Government.advance` (`sim/agents/government.py`); `sim/agents/group_servants.py`. Higher tax never drives peasants off the land (486, 538).

**Why it matters.** No ruler chooses among them, and a dated third-century crisis follows (CLAUDE.md 4.2).

**What it would take.** The responses (cut lines, arrears, debase, borrow, levy, kind demand) as choices of the state actor, each with its consequences, so a player state and an AI state face the same menu.

**Test.** A test: two states with different rules pick different responses from the same shortfall; no fixed cascade remains.
