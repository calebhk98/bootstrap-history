# Aged tin and gravel asks fall below their labour cost while copper ore sits far above its

**Status:** open

After 511 the cassiterite and tin recipes are consistent with the deposits, but in an aged Rome game
(`YearInputs` stepping loop of `sim/tests/test_economy_tin_dearer_than_copper.py`, eight years) shown tin over
copper falls from about 0.7 in year one to under 0.1 and stays there. Two causes, both outside the recipes:
- The remembered ask of idle gravel sellers (`cassiterite_kg|united_kingdom_01`, `|spain_03`) decays to a fraction
  of the labour that digs a tonne, and tin trades a few tonnes a year at a price below the labour in its gravel.
  This is the unsold-seller family of closed 502 (an ask held near cost times a markup).
- Copper ore shows tens of times the labour of raising it (a scarcity price from capped sites against demand),
  while tin's sites have room far above its demand, so tin never meets a binding site limit.
Whether tin should bind on its sites depends on the working rate of the tin deposits
(`geography.working_rate_tonnes_per_year`) against the demand for bronze, both data to re-measure first.
