# The save listing's goal year is always empty

**Status:** open - kept as it is in the scenario module move (the listing reads the field where it no longer lives)

`sim/engine/settings.py` (`list_saves`, the row built from each save) fills `goal_year` from the scenario section of the
save: `scenario.get("goal_year")`. The year the goal was reached is the seats module's field (`goal_year` in the acting seat's
`modules.seats` slot, which the same function already reads `founder_alive` and `dead_reason` from), and no scenario section
ever held it since the field moved, so every row says `goal_year: None` whether or not the goal was reached.

Evidence: `grep -n goal_year sim/engine/settings.py`; the equivalence relocation `("/seats/*/modules/seats/goal_year",
"/seats/*/seat_progress/goal_year")` in `sim/tests/equiv_fields.py` shows where it lives.

Fix: read it from `seats_slot` (`seats_slot.get("goal_year")`) and add a test that lists a save whose seat reached its goal.
Kept as it is because the move must not change replies.
