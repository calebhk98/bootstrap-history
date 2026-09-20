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
* `data/world/trade_families.json`: additive `trade_families` entries.

New technology, recipe, civilization, and trade ids must start with
`<mod_id>_`. A technology or recipe may instead deliberately patch an existing
id with `"override": true`; overrides are deep merges and fail if their target
does not exist. Technology nodes may also use `"replaces": "existing_id"`.
Unmarked collisions are errors which name both sources.

The three installed sample mods use only this public data contract. They add a
slave-ownership goal, Ptolemaic Egypt in 100 BC, and a photovoltaic technology
line with an all-solar goal. The engine contains no checks for their ids.
