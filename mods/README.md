# Mods

Every immediate subdirectory containing `mod.json` is active. Remove or move a
folder to disable that mod; no registry or Python edit is required. The loader
orders mods by dependencies and then by id, rejects missing dependencies,
dependency cycles, declared conflicts, and ambiguous duplicate ids.

## Ids and namespaces

A mod id has the form `<author>_<name>_<suffix>`: lowercase letters, digits and
underscores, starting with a letter, ending in a random suffix of four or more
lowercase letters or digits (for example `ana_steamage_k3f9`). The random suffix
is what keeps two authors who never spoke from picking the same id; make one up
rather than choosing a word. The loader rejects any other shape with a message
saying so. A mod id never contains `:`.

Every new technology, recipe, material, civilisation, trade or topic tag a mod
creates is named `<mod_id>:<name>`, for example `ana_steamage_k3f9:boiler`. The
`:` cannot occur in a mod id, so a namespace belongs to exactly one mod and a
mod can never create an id inside another's. The name part is lowercase letters,
digits and underscores, starting with a letter. Players type the full id.
A civilisation's file name writes the `:` as `+`
(`ana_steamage_k3f9+realm.json`), since `:` is not portable in file names.

A mod that uses another mod's ids anywhere in its data files (a prerequisite,
a material, a goal node, a starting technology, a recipe input) must list that
mod in `dependencies`, directly or through a chain of dependencies; otherwise
the load fails with an error naming both mods.

A manifest has this shape:

```json
{
  "id": "ana_example_k3f9",
  "name": "Example Mod",
  "version": "1.0.0",
  "dependencies": [],
  "conflicts": []
}
```

All five keys are required; a manifest missing one is refused with a message naming
it. Any other key (author, credits, a description, a homepage) is the author's own
metadata: the loader ignores it and the mod loads. The game has no version number to compare against, so
there is no minimum-game-version field yet.

A mod may provide:

* `data/branches/*.json`: a list of technology nodes (or an object with a
  `nodes` list).
* `data/goals.json`: `{ "goals": [...] }`, using the base goal catalog shape.
* `data/category_traits.json`: `{ "categories": {category: {"never_abandoned": bool, "practisable": bool}}, "diffusion_traits": [...] }`, merged over `data/world/category_traits.json`. A mod whose nodes use a new `cat` must add its entry; `validate` reports a missing one.
* `data/civilizations/*.json`: civilization files using the base schema, or
  override patches of an existing civilisation.
* `data/production/*.json`: production recipe files using the base schema.
* `data/world/trade_families.json`: additive `trade_families` entries (the
  backwards-compatible shorthand trade registry).
* `data/world/trades.json`: additive `trades` entries with a `family` and
  optional `training`, `note`, and `initially_absent` fields. Availability and
  descriptive metadata belong here; a wage is deliberately not part of trade
  identity.

* `data/world/needs.json`: `needs` (household spending categories, ids
  `<mod_id>:<name>`, each with a `surplus_budget_share` weight) and `goods`
  (`satisfies`: {need: effectiveness per unit}, optional `supply_per_year`).
  A recipe entry may carry `satisfies` and `supply_per_year` for its main
  output instead. Demand for the good, the demand it derives for its inputs
  through recipes, and a scarcity price where its supply is limited follow
  from these; no basket entry is needed. See `sim/world/need_demand.py`.

* `data/world/units.json`: `units` (display units, ids `<mod_id>:<name>`, each with
  `name`, `symbol`, `dimension` of `area`, `mass`, `temperature` or `money`, and a
  `factor` and optional `offset` such that base = value * factor + offset; bases
  are hectare, kilogram, Celsius and labour hour) and optional `field_rules`.
  See `sim/PROTOCOL.md`, "Display units".

* `data/ui/figures.json`: `{ "figures": { "<mod_id>:<name>": {...} } }`, figures for the `figures` / `why`
  inspector. A figure has a string `label`, optional `unit` and integer `digits`, and `value`, a state path:
  dotted names of `Sim` attributes or methods (a method is called with no arguments; a name after a mapping
  looks up its key), for example `population.total`. Optional `components`, `flows` and `drivers` are either a
  path to a mapping of name to number or `{name: path}`. A path reads only: no step starts with `_`, and a
  method is callable only when the engine marks it `@readable` (`sim/engine/readable.py`); anything else is
  refused at load with an error naming the file. The base game's own file shows the shape; a figure
  that needs code (a cause book) stays a `@figure` in `sim/ui`. Ids outside the mod's namespace and ids already
  taken are errors.

New technology, recipe, civilization, and trade ids must be
`<mod_id>:<name>`. A technology or recipe may instead deliberately patch an existing
id with `"override": true`; an override is a deep merge that changes only the
fields it names (defaults apply to new nodes only) and fails if its target does
not exist. Technology nodes may also use `"replaces": "existing_id"`, which is
the same patch aimed at that id. A new technology node must have a string
`name`. Unmarked collisions are errors which name both sources.

A technology's engine behaviour (standing, credit, staffing, hedges, power tiers and so
on) is declared in its `mechanics` object, documented in `data/branches/MECHANICS.md`.
A mod that adds a node gives it those behaviours by declaring mechanics; an
override that names a mechanic changes or, with `null`, removes it.

Goals (in `data/goals.json`, identified by their `node`) and trades (in
`data/world/trades.json`, with `family`, `training`, `note`, `initially_absent`)
take `"override": true` with the same meaning: a deep merge of only the named
fields, a `null` inside a nested map deletes that key, and an override of a
missing goal or trade is an error.

Two mods that override the same field of the same technology, recipe, goal or
trade are an error naming both mods, the id and the field, unless the later mod declares the
other as a dependency (directly or transitively), in which case the dependent
mod wins. Overrides of different fields merge.

## Removing content

An entry marked `"remove": true` deletes a base (or earlier mod) item by its
id: a technology node in `data/branches`, a recipe in `data/production`, a
trade in `data/world/trades.json`, or a goal in `data/goals.json` (identified
by its `node`). Removing an id that does not exist is an error. After all mods
load, any remaining technology prerequisite or `req_any` option, goal, recipe
input or output, technology material, labour trade, or civilisation starting
technology that still names a removed id is an error naming the referencing
item and the removing mod. The trade check includes technology labour, and
every base and mod civilisation is checked once at mod load, picked or not. Patch the reference away with an override (in the
same mod or a mod that depends on the remover). Inside a nested map of an
override, a `null` value deletes that key, for example
`"inputs": {"removed_material": null}`.

A mod that removes an id another unrelated mod overrides (in either order) is
an error naming both mods; declare a dependency to choose a winner.

## Civilisations

A file `data/civilizations/<id>.json` is a new civilisation (namespaced with the mod id) unless it carries `"override": true`, in which case it patches the
existing civilisation of that id (base or from another mod; write `:` as `+` in the file name) by deep merge,
changing only the named fields; lists such as `starting_techs` are replaced
whole. Unrelated mods patching the same field are an error naming both. A
patch with `"hidden": true` keeps the civilisation out of the new-game menu and
`civilization_ids()`; it still loads by name.

A civilisation holds the tiles its `home_tiles` list names (shipped civilisations list nothing else). To give a shipped
civilisation a mod's new tile, a patch replaces `home_tiles` whole; a new mod civilisation may instead list `home_regions`,
region labels that resolve to the tiles carrying them, and `home_tiles` wins when both are present.

## Economic content

Production is loaded once as a dependency-ordered catalogue and that same
catalogue is used by validation, the price solver, demand, and the labour
market. Materials are discovered from recipe keys, inputs, outputs, capital
build materials, and technology requirements. A technology may therefore consume a mod
material when a production path produces it. Resolvable paths are costed in
labour-hours and added to the runtime goods table. A missing path is an authoring error; a path gated by
technology is reported as unavailable rather than assigned an invented price.

New professions belong in `data/world/trades.json` (or the family shorthand)
and production recipes may use them immediately. Wages are not yet a complete
general-equilibrium solve: existing trades still receive temporary legacy
rates and a new trade receives the median rate of its family through the
wage-provider seam. These are compatibility inputs scheduled for replacement,
not calibration targets. Labour allocation itself remains dynamic.

Trading partners are listed in `data/world/foreign_economies.json` (each names a
civilisation file and the years it exists as a trading economy). The loader does not
read a mod's copy of that file yet, so a mod can add the civilisation but not enable
it as a partner; the file's own `_doc` describes its fields. A mod can add cast
members and strata to a game by patching a civilisation's `cast` key (see
`data/civilizations/_SCHEMA.md`).

A mod can ship a map overlay in `mods/<id>/data/world/geography/` (tile edits in `tiles/`, layer
patches in `layers/`, new resources, deposits, route modes or a whole replacement map). It merges
under the same add, override and remove rules as the rest of the mod system, new ids carry the mod's
prefix, and `sim/geography/map_source.py` states the folder layout. The game opens the map once with
every installed mod's overlay in load order (`sim/engine/geography_port.py`), and the agent economy's
tiles and carriage costs come from it. A mineral row may carry `mine_demand_goods`, the goods whose demand a mine of it supplies (the `mines` screen
reads it; a material without it is its own demand good). Hazards and arbitrary new mechanics are not mod
extension points yet. There is no price table: every price comes from
production data, so a mod prices a good by giving it a production path.

The three installed sample mods use only this public data contract. They add a
slave-ownership goal, Ptolemaic Egypt in 100 BC, and a photovoltaic technology
line with an all-solar goal. The engine contains no checks for their ids.
