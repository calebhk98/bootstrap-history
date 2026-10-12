# No firm ever enters a founder's concern in a default game

**Status:** open

Entrants see a concern only within an observation range of where their country sits, and a country's
government is placed at its central tile (Rome's lies in Africa), well out of range of the founder's seat.
Exposure stays far below the entry threshold, so no firm copies a founder concern in a default Rome.
The firm tests work around it with `ready_for_entry` in `sim/tests/harness.py`, which moves the home
government to the founder's seat. Measure: a default `harness.sim()` stepped a few years, then count firms
whose node is one the founder runs.
