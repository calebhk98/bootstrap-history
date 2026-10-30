# The cash refusal of buying slaves is written to the saved household record, where nothing reads it

**Status:** closed - already fixed by the workforce module move: both refusals go through `note_buy_refusal`, kept per acting seat and read by `last_buy_refusal`. Tests: `sim/tests/test_workforce_commands.py` `test_a_refusal_to_buy_people_is_kept_for_the_acting_seat_until_it_is_cleared` and `sim/tests/test_bondage_training_lag.py` `test_a_purchase_the_purse_cannot_cover_notes_the_refusal_with_the_figures`.

`Labour.buy_slaves` (sim/labour/labour_bondage.py) sets `_last_buy_refusal` twice. The room refusal goes to the household actor
(`self._world.household`), which is what the screens read back (`Sim._last_buy_refusal`, sim/engine/core_properties.py). The cash
refusal ("cannot afford N slaves") is set on `self._world.state.household`, the saved `HouseholdState`, which has no such field and
is never read, so a player who cannot pay is told the generic message instead of the figures. Found while moving the staff fields
to the workforce module; the move kept the behaviour.

Fix: set it on the household actor in both places (one line), with a regression test that a cash-short `buy slaves` reply carries
the refusal text.
