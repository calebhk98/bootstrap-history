# Ships have no recipe and no shipwright: they are a state budget line paying carpenters and sailors

**Status:** open

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming).

Blocks 629 (vessels as carrier capital).

**What is wrong.** Ships are a state budget line paying `carpenter` and `sailor` hours; there is no ship good.

**Evidence.** `sim/agents/budget_lines.py`.

**Why it matters.** A ship is an object with maintenance (CLAUDE.md 4.3) and the carriage chain needs it (552).

**What it would take.** A shipwright trade and ship goods with recipes and sourced service lives; the state's ship line buys ships rather than hours.

**Test.** `validate` passes; a test: the state's ship line draws shipwright hours and produces ships.
