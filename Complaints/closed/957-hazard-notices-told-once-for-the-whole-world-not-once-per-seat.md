# Hazard notices are told once for the whole world, so a later seat is never told

**Status:** closed - the already-told memo (`said_condition`) moved from the hazards world state to its seat state; `sim/tests/test_hazard_telling_per_seat.py` holds it

`say_once` (sim/hazards/events.py) kept its memo in `world.said_condition`, keyed on the hazard name only. The "causes fail" and
condition tellings (sim/hazards/shocks.py) and the concern levy notice (sim/polity/transfers.py) all use it, so with two seats only
the first seat to reach the line was told; every later seat got none. Reproduced by calling `say_once` under two seats: the second
call answered False. The memo is now `HazardsSeat.said_condition`, so each seat is told once.
