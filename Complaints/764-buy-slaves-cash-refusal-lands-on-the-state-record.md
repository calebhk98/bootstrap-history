# The cash refusal of buying slaves is written to the saved household record, where nothing reads it

**Status:** open

`Labour.buy_slaves` (sim/labour/labour_bondage.py) sets `_last_buy_refusal` twice. The room refusal goes to the household actor
(`self._world.household`), which is what the screens read back (`Sim._last_buy_refusal`, sim/engine/core_properties.py). The cash
refusal ("cannot afford N slaves") is set on `self._world.state.household`, the saved `HouseholdState`, which has no such field and
is never read, so a player who cannot pay is told the generic message instead of the figures. Found while moving the staff fields
to the workforce module; the move kept the behaviour.

Fix: set it on the household actor in both places (one line), with a regression test that a cash-short `buy slaves` reply carries
the refusal text.
