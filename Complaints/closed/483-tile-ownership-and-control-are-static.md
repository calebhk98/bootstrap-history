# Tile ownership and political control are static: no owner map, no transfer, no control levels

**Status:** closed - owner map with control levels, one transfer, colonies and ways read it, invariant added

- A civilisation holds the tiles its file lists (`home_tiles`, else `home_regions`;
  `sim/geography/tile_holdings.py`, `tiles_held`). The agent economy fixes each tile's country at setup
  (`sim/economy/setup.py`, `country_of`).
- The only way to gain a tile is `found_colony` for a seat, on unclaimed neighbours
  (`sim/engine/colonies.py`). Nothing transfers a tile between countries, and nothing stops two
  civilisation files listing the same tile.
- There is no control state: no core, integrated, garrisoned, tributary, port enclave, claimed-only or
  ungoverned level (`grep -rni "tributary\|control_level\|garrison" sim` finds only defence-store
  manpower).
- Built ways live in one global dict, `state.economy.improvements` (`sim/engine/ways.py`), with no owner.

Why it matters: the group's first requirement is "a region can only have one owner", used to catch
contradictions in their timeline. Conquest (485), authority (484) and tolls (487) all need an owner
that can change.

What it would take: a saved tile-to-actor owner map with a control level, read by `country_of`,
`tiles_held` and the ways record; a transfer operation; and an invariant that every tile has at most one
owner (493).

## Resolution

- `sim/geography/tile_owners.py` holds the owner map ({tile: owner, control}), seeding with conflict reports, the one `transfer` (a country or seat; `None` releases), `way_owner` and `problems`. Control levels are data in `data/world/control_levels.json`.
- The map is saved as `state.economy.tile_owners`, seeded on first read from the home and agent-economy partner civilisation files (`sim/engine/tile_ownership.py`); a tile claimed by two files goes to the first and is recorded in `tile_claim_conflicts`.
- `tiles_held(..., owners=)`, `EconomySetup.country_of`, the labour market held tiles, colonies (founding transfers the tile to the seat, dying out releases it) and the ways record (`way_owners`, read from the owners of the tiles a way stands on, so a conquered tile takes its ways) all read it.
- `check_tile_owner_invariants` runs with the step invariants.
- Held by `sim/tests/test_tile_owners.py`.
