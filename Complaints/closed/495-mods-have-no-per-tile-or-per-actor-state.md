# Mod state is one dict: there is no saved per-tile, per-actor or per-pair store a mod can declare

**Status:** closed - declared tile, actor and actor-pair stores, saved and readable; tile control moved onto them

`ModCodeApi.state` (`sim/engine/mod_code.py`) gives each mod one JSON dict inside the save. A mod that
models anything spatial or relational has to invent its own keys, and nothing else in the game can read
them: figures and `read` commands reach state paths marked `@readable` (`sim/engine/readable.py`),
which a mod's dict is not.

Why it matters: the systems in Complaints 481 to 493 hang values on tiles (owner, control, unrest, disease
load), on actors (army, loyalty, beliefs) and on pairs of actors (treaty, trust, tariff). A fantasy mod
needs the same shape (mana on a tile, a hero's renown, a feud between houses).

What it would take: declared stores, in data or through `api`, keyed by tile, actor or actor pair, each
with a namespaced name, a default and a unit; saved with the game by the existing automatic save
detection; readable by figures, `read` commands and the map screen. Build the base game's own new
per-tile and per-actor values on the same stores.

## Resolution

`sim/engine/mod_stores.py` holds declared stores: named `<mod_id>:<name>`, keyed by tile, actor or ordered actor
pair, each with a default and a unit, declared in a mod's `data/stores.json` or by `api.store`. Values that
differ from the default live in `state.stores`, so the automatic save carries them. `sim.stores.<name>.<key>` is
an ordinary state path, so figures and `read` commands reach it, and `map layer <store>` shows a tile store on the
map screen. A duplicate declaration, an undeclared write and a write to another mod's store are errors naming the
mod. The base game's tile control level (Complaint 483) now lives in the base-declared `control` store
(`data/world/stores.json`) instead of the owner map. Held by `sim/tests/test_mod_stores.py`; use is in
`mods/README.md`.
