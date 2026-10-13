# Mod state is one dict: there is no saved per-tile, per-actor or per-pair store a mod can declare

**Status:** open

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
