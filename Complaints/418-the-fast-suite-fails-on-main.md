# The fast suite fails on main

**Status:** open

On main at the merge of pull request 30, `python3 -m sim.tests --only automation_audit,capital_charge` fails before any geography change:

- `automation_audit`: the module patches `Sim.hire`, which no longer exists (`AttributeError: 'Sim' object has no attribute 'hire'`), so the whole topic crashes at import.
- `capital_charge`: three checks raise `KeyError: 'lab'`.

A third check, "a cached price-table lookup costs well under rebuilding the done set", is a wall-clock comparison that failed once under load in a full run and passes alone; a timing ratio is not a stable assertion.

What it would take: point the automation audit at wherever hiring lives now (`sim/labour/`), find what the `lab` key became for the capital charge, and make the price-table timing check measure work rather than seconds.
