# The state employs no guards or mine inspectors, so order and land ceilings borrow the collection share

**Status:** open

Complaint 658 replaced typed `state_capacity` with the 620 collectible share (`Sim.state_reach()`, `sim/engine/legitimacy.py`).
Three readers need specific staff, and the state's budget has no line for them, so they read the collection share:

- theft and plunder order (`sim/engine/theft_exposure.py` `order_factor`, `theft_charge.py`): needs a watch or guards,
  paid and placed on tiles;
- the mine land ceiling (`sim/engine/economy_mining.py` `mine_land_ceiling`, `mine_ceiling.py`): needs mine inspectors
  and a registry of claims;
- the forest ceiling (`forest_land_ceiling`, `forest_ceiling.py`): needs foresters or wardens holding tenure.

Why it matters (CLAUDE.md 4.1): the ceilings and theft exposure still carry a labelled-heuristic scale
(`MINE_CEILING_*_SCALE_*`, `FOREST_HA_PER_MILLION_KM2_PER_SC`) per unit of reach rather than following from staff.

What it would take: a `guards` line and an `inspectors` line in `sim/agents/budget.py` (like the `administration` line),
whose employed share and travel time to the tile (the 620 machinery in `sim/agents/collection.py`) replace the
borrowed share; the ceilings then follow the inspectors a state pays rather than a tonnes-per-reach scale.
Tests: more guards or a nearer tile lowers the theft share on that tile; more inspectors raises the mine ceiling.
