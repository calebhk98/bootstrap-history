# The engine writes player-facing sentences, and numbers are formatted ad hoc, so the game cannot be localised or shown in other units consistently

**Status:** open - owner direction (2026-10-06): everything that prints belongs in sim/ui/; unblocked, scheduled after the structural work

The unit layer (`sim/engine/units.py`, `units_prose.py`, `units_summary.py`) is imported across `sim/ui/` and `sim/engine/`, not by two screen modules (the file `units_text.py` is gone). About 69 files format numbers themselves, and about 14 simulation modules outside the protocol layer build player sentences (refusals, notes, event text): among them `sim/labour/labour_training.py` and `sim/finance/cash_remedies.py` (the other modules named when this was filed, `projects_starting`, `core_step_phases`, `projects_staffing` and `society_hazards`, no longer exist under those names; the counts were not re-measured, and `sim/refusal.py` causes already give refusals a structured reason). There is no message catalogue. The simulation should not care what words or units a player sees.

What it would take: the engine returns structured results (a reason code and its quantities, each with its dimension), and one display layer renders them in the player's language and units (complaint 285 is the units half). Incrementally: a check that fails on new sentence-building in engine modules, then move modules one at a time.

Owner decision (2026-10-02): wait until more of the other work is done; do not drive it with a burndown test.
