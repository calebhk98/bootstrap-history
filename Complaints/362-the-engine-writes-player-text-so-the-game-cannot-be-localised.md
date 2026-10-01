# The engine writes player-facing sentences, and numbers are formatted ad hoc, so the game cannot be localised or shown in other units consistently

**Status:** open

The unit layer (`sim/engine/units.py`, `units_text.py`) is used by two screen modules only. About 69 files format numbers themselves, and about 14 simulation modules outside the protocol layer build player sentences (refusals, notes, event text): among them `labour_training.py`, `projects_starting.py`, `core_step_phases.py`, `projects_staffing.py`, `society_hazards.py`, `cash_remedies.py`. There is no message catalogue. The simulation should not care what words or units a player sees.

What it would take: the engine returns structured results (a reason code and its quantities, each with its dimension), and one display layer renders them in the player's language and units (complaint 285 is the units half). Incrementally: a check that fails on new sentence-building in engine modules, then move modules one at a time.
