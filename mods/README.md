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
metadata: the loader ignores it and the mod loads. These keys are optional and read by the loader:

* `min_game_version`: a version such as `0.1` or `1.2.3`. A mod that needs a newer game than
  `GAME_VERSION` (`sim/game_version.py`, printed by `python3 sim/simulator.py --version`) is refused
  with a message naming both versions.
* `dependencies` entries may end in a version range: `"ana_steamage_k3f9>=1.2,<2"`. Versions compare as
  numbers (major, minor, patch; a missing part is zero), never as text. An installed dependency whose
  `version` falls outside the range refuses the load, naming both mods.
* `code` and `permissions`: see "Mod code" below.

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

## Rules and small world data

A mod changes rules and removes content through data, never through engine edits. Every file below follows the
same patch rules: a new entry is named `<mod_id>:<name>`, `"override": true` deep-merges only the fields it
names (a `null` inside a nested map deletes that key), `"remove": true` deletes, a missing target is an error,
and two unrelated mods on one field are an error naming both.

* `data/constants.json`: `{"constants": {"NAME": {"value": ..., "why": "..."}}}` replaces a number the engine
  declares with `declare(...)` (`python3 sim/constants.py` lists them with their kind and unit), including the
  `temporary_heuristic` ones. `why` is required; the value must be the same kind of value; `validate` names a
  `NAME` nothing declares. The registry records which mod set it.
* `data/world/geography/parameters/` (inside a map overlay): the map's own parameters and heuristics.
* `data/civilizations/_TECH_EFFECTS.json`: what a technology does to a society (literacy, values), keyed by
  technology id, with the base file's shape. Add effects for a mod technology, retune or remove shipped ones.
* `data/world/starting_kits.json`: `{"kits": {id: {"labourer_years": ..., "desc": ...}}}`, the starting wealth kits.
* `data/ui/win_condition_labels.json`: `{"labels": {metric: {"text": "...%s..."}}}`, the sentence for a threshold
  goal's metric. A metric name belongs to the engine, so a new label is not namespaced.
* `data/world/foreign_economies.json`: `economies` records keyed by `civilization` (add a partner, `override` to
  enable or retune one, `remove`) and `not_traded_materials` (added to the base list). A mod civilisation becomes
  a trading partner this way.
* `data/strategies/<mod_id>+<name>.json`: a strategy file in the base shape, named `<mod_id>:<name>` on the
  command line.
* Currency words are part of each civilisation file (`currency`, `currency_words`), so a mod civilisation or a
  civilisation patch sets its own.
* Hazards live in the civilisation file. A civilisation patch may carry `"append": {"hazards": [...]}` and
  `"remove_items": {"hazards": ["Hazard name"]}`; any list field works, and a dotted field reaches into a map, for
  example `"append": {"cast.seats": [...]}` or `"remove_items": {"cast.actors": ["actor_id"]}`. An item is
  identified by its `id`, `actor_id` or `name`. Two unrelated mods may both append to a list; appending to a list
  another unrelated mod replaced whole is an error naming both. A hazard is made of the effect fields the engine
  already reads (`staff_loss`, `sack_chance`, `output_factor`, `real_erosion`, `values`, with `years` and `causes`);
  an effect no existing field expresses needs an actor kind or mod code.
* Mineral deposits and every other map catalogue: the map overlay under `data/world/geography/`.

## Commands and automatic policies

`data/ui/commands.json`: `{"commands": {"<mod_id>:<name>": {...}}}`. A declaration has `summary`, `description`,
optional `group`, `usage`, `options`, `aliases` and `fog_hidden`, and a `kind`:

* `read`: `shows`, a list of `{label, path, unit?, digits?}` read from state paths (the same grammar and
  `@readable` gate as figures; a path that is private or calls an unmarked method is refused at load).
* `macro`: `steps`, a list of command objects replayed through the ordinary dispatcher, so fog guards and
  option checks apply. A `"$field"` string takes that field of the typed command (`shape` is `bare`, `text` or
  `tech`); a missing field runs nothing. A step must name an existing command and may not name a macro.
* `policy`: `hook` (`year_start` or `year_end`), `when` (a list of `{path, op, value}`) and `do` (commands).
  Each policy is a switch in the seat's `policy` named `<mod_id>:<name>`, on unless `default` says otherwise (off
  for a player who plays by hand when `default` is absent); the `policy` command flips it.

An alias is a bare word that works only while no command, alias or mod claims it; a clash is an error naming both
owners. An entry named after a shipped command with `"override": true` changes its help text, and with
`"remove": true` deletes it (a macro still naming it fails the load). `data/ui/policies.json`,
`{"defaults": {"auto_mine": false}}`, sets the shipped default of an automatic policy switch.

## Mod code

Data is the default and covers most needs. A mod that needs Python lists files in its manifest:

```json
{ "code": ["hooks.py"], "permissions": ["code"] }
```

Each file defines `register(api)`. The `api` object registers commands (`@api.command(name, group=..., summary=...,
usage=[...], description=...)` with a handler `(sim, nodes, cmd, ended) -> dict`), actor kinds (`api.actor_kind`),
policies (`api.policy`) and spawners (`api.spawner`); every name is forced into `<mod_id>:`. A handler keeps its
state only in `api.state(sim.state.interface)`, a plain dict that is saved with the game, and draws random numbers
only from `api.rng(world, ...)`, so saves and the fingerprint stay reproducible.

**Python in a mod is not sandboxed.** It runs in the game's process with the player's full permissions: files,
network, credentials. Nothing inside CPython holds against a hostile author, and the `api` is an interface for
honest mods, not a defence. The protection is consent: code runs only after the player runs
`python3 sim/simulator.py mod-allow <mod_id>`, which prints the files and records their sha256 digests in
`mods/consent.json` (local to the player, not committed). A changed file needs consent again; an unallowed mod's
data still loads but its code does not, and `validate` lists it. Allow code only from an author you trust. A real
boundary needs a separate process or WASM host with an allowlisted message interface; that is not built.

## Actor kinds

An actor kind a mod adds is a species or institution that runs through the ordinary rules. As data, in
`data/world/actor_kinds.json`: `{"kinds": {"<mod_id>:<name>": {"needs": {need_id: floor_multiple}, "trade": ...,
"work_share": ..., "birth_rate": ..., "death_rate": ..., "famine_death_rate": ..., "vital_needs": [...]}}}`. Its
needs name entries of the needs catalogue (`data/world/needs.json`, extended by the mod), so what it eats is
whatever satisfies those needs, bought at the market's prices against everyone else; it earns the pay of its trade;
deaths rise with the share of its vital needs left unmet; all money moves through the ledger. A civilisation puts
one in play with a `cast.actors` entry `{"actor_id": ..., "kind": "<mod_id>:<name>", "params": {"members": ...}}`.
For behaviour the data cannot express, mod code registers a class with `api.actor_kind`. A saved game that holds a
kind whose mod is gone fails to load with a message naming the mod.

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
civilisation file and the years it exists as a trading economy); a mod's copy of that file adds, patches or
removes partners (see "Rules and small world data"); the file's own `_doc` describes its fields. A mod can add cast
members and strata to a game by patching a civilisation's `cast` key (see
`data/civilizations/_SCHEMA.md`).

A mod can ship a map overlay in `mods/<id>/data/world/geography/` (tile edits in `tiles/`, layer
patches in `layers/`, new resources, deposits, route modes or a whole replacement map). It merges
under the same add, override and remove rules as the rest of the mod system, new ids carry the mod's
prefix, and `sim/geography/map_source.py` states the folder layout. The game opens the map once with
every installed mod's overlay in load order (`sim/engine/geography_port.py`), and the agent economy's
tiles and carriage costs come from it. A mineral row may carry `mine_demand_goods`, the goods whose demand a mine of it supplies (the `mines` screen
reads it; a material without it is its own demand good). A mechanic no data field or actor kind expresses is mod code. There is no price table: every price comes from
production data, so a mod prices a good by giving it a production path.

The three installed sample mods use only this public data contract. They add a
slave-ownership goal, Ptolemaic Egypt in 100 BC, and a photovoltaic technology
line with an all-solar goal. The engine contains no checks for their ids.
