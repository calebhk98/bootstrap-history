# The automation audit test wraps methods the labour wall moved

**Status:** open

`python3 -m sim.tests --only automation_audit` crashes before any check runs:
`AttributeError: 'Sim' object has no attribute 'hire'`. The test wraps `hire`,
`auto_open_ventures`, `reopen_restaffed_ventures` and `auto_commission_for_blocked` on the `Sim`
(`sim/tests/test_automation_audit.py` around line 29). The labour wall moved `hire` and
`auto_commission_for_blocked` onto `sim.labour`. It fails the same way on main (`bcd8b65`).

Why it matters: the audit of what automation does each year is not checked at all while the topic crashes.

What it would take: wrap each method on the object that now holds it (`sim.labour.hire`,
`sim.labour.auto_commission_for_blocked`), and the engine ones where they still live.
