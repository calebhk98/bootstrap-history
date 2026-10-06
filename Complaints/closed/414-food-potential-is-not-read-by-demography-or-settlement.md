# Food potential is not read by demography or settlement

**Status:** closed - folded into 416

Geography now answers how many people a tile's crops, herds, game, wild plants and fish can feed (`api.food_potential`), so a civilisation on steppe, coast or desert river is no longer grain-only (Complaint 138). Nothing reads it yet: `sim/geography/settlement.py` still splits people by arable area times fertility, and demography's food comes from the farming model alone.

What it would take: the engine passes the actor's technique factors (keyed by the food source ids in `data/world/geography/resources/` and the `food_source_crops` parameter) and reads the per-source energy for its held tiles; settlement shares people by total food potential. Then Complaint 138 can close.
