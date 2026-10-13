# Room advice promises places that income then withholds

**Status:** open

The `labour` screen tells a player that, say, `paid_apprentice_staff (+10 places)` is how to get more
room. In a Rome playtest (`play --civ rome_100ad --kit merchant --seed real25`) household places did not
move when it was opened, or when it was shut again. `freedman_staff`, advertised the same way, raised
places by less than it promised.

Cause: `_room_advice` (`sim/labour/labour_capacity.py`) prints each node's flat `room_places`, but the
places those institutions add go through `staff_capacity`. That function scales the institutional ceiling
by what 40% of the household's spare income can pay (`STAFF_BUDGET_SHARE_OF_SPARE`). For a founder with a
small surplus the scale is close to zero, so the node adds almost nothing. Bought housing
(`worker_housing_places`) is not scaled, so `buy housing` was the only lever that worked as described.

Why it matters: the player spent money and an opening charge on a promise the engine never meant to keep
at that income, and nothing on any screen explained why.

What it would take: have `_room_advice` print what the node would add at the current income (the same
`scale` that `staff_capacity` computes), and say that it grows with surplus. Add a test that the advertised
figure equals the change in `household_room()` when the node is opened.
