# Mods

Every immediate subdirectory containing `mod.json` is active. Remove or move a
folder to disable that mod; no registry or Python edit is required. The loader
orders mods by dependencies and then by id, rejects missing dependencies,
dependency cycles, declared conflicts, and ambiguous duplicate ids.

A manifest has this shape:

```json
{
  "id": "example_mod",
  "name": "Example Mod",
  "version": "1.0.0",
  "dependencies": [],
  "conflicts": []
}
```

A mod may provide:

* `data/branches/*.json`: a list of technology nodes (or an object with a
  `nodes` list).
* `data/goals.json`: `{ "goals": [...] }`, using the base goal catalog shape.
* `data/civilizations/*.json`: civilization files using the base schema.
* `data/production/*.json`: production recipe files using the base schema.
* `data/world/trade_families.json`: additive `trade_families` entries (the
  backwards-compatible shorthand trade registry).
* `data/world/trades.json`: additive `trades` entries with a `family` and
  optional `training`, `note`, and `initially_absent` fields. Availability and
  descriptive metadata belong here; a wage is deliberately not part of trade
  identity.

New technology, recipe, civilization, and trade ids must start with
`<mod_id>_`. A technology or recipe may instead deliberately patch an existing
id with `"override": true`; overrides are deep merges and fail if their target
does not exist. Technology nodes may also use `"replaces": "existing_id"`.
Unmarked collisions are errors which name both sources.

## Economic content

Production is loaded once as a dependency-ordered catalogue and that same
catalogue is used by validation, the price solver, demand, and the labour
market. Materials are discovered from recipe keys, inputs, outputs, capital
build materials, and technology requirements; adding one does **not** require
an entry in `data/prices.json`. A technology may therefore consume a mod
material when a production path produces it. Resolvable paths are costed in
labour-hours and added to the runtime goods table even when the old price book
has never heard of them. A missing path is an authoring error; a path gated by
technology is reported as unavailable rather than assigned an invented price.

New professions belong in `data/world/trades.json` (or the family shorthand)
and production recipes may use them immediately. Wages are not yet a complete
general-equilibrium solve: existing trades still receive temporary legacy
rates and a new trade receives the median rate of its family through the
wage-provider seam. These are compatibility inputs scheduled for replacement,
not calibration targets. Labour allocation itself remains dynamic.

World geography/resources, hazards, UI, and arbitrary new mechanics are not
mod extension points yet. `data/prices.json` is scheduled for deletion but is
still read for the temporary labour-hour/denarius conversion, legacy wage
inputs, and goods whose production economics are incomplete. It is no longer
the material namespace or a mod authoring interface.

The three installed sample mods use only this public data contract. They add a
slave-ownership goal, Ptolemaic Egypt in 100 BC, and a photovoltaic technology
line with an all-solar goal. The engine contains no checks for their ids.
