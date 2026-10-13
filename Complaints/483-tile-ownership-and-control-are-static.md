# Tile ownership and political control are static: no owner map, no transfer, no control levels

**Status:** open

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
