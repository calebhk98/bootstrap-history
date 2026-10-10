# Mod hooks plan: land tiles, commands and new actor kinds

Status: commands, policies, actor kinds and mod code (stages 2 to 4) are built, as described in `mods/README.md`; the land-tile readers of section 1.1 are the work that remains outside Complaint 118.

Complaint 118 left three things a mod cannot do: add land tiles, add commands, add actor kinds.
This document says how each is discovered today, where a mod would hook in, what blocks it, the
mechanism proposed, a staged plan with tests, and an audit of other places where adding content
still means editing a list in code. Nothing here changes code.

Governing rules (CLAUDE.md): the engine never special-cases content ids (4.7); dynamic over
enumerated; the owner wants every data source and content type swappable by one option or by
adding files, with nothing so interlinked that swapping is hard. A mod follows `mods/README.md`:
new ids are `<mod_id>:<name>`, dependencies are declared, `"override": true` patches, `"remove":
true` deletes, and a removal that leaves a dangling reference is an error naming both parties.

Measured on 2026-10-06 on branch `mod-hooks-design` (from `structural-dedupe-and-owner-decisions`).
Counts are in the table at the end of section 1; every number comes from the command beside it.

## 1. How each kind is discovered today, and what blocks a mod

### 1.1 Land tiles

Today the map is already a merged set of folders, and a tile add already works. The loader is
`sim/geography/map_source.py` (`merge_folders`, `load_map`, `mod_overlay_folders`); a mod's
`mods/<id>/data/world/geography/tiles/*.json` adds tiles (new id must be `<mod_id>:<name>`),
patches them (`override`) or deletes them (`remove`); `layers/*.json` patches per-tile values; any
other subfolder is a catalogue (regions, climate classes, route modes, resources, deposits). The
engine opens the map once with every installed mod in load order
(`sim/engine/geography_port.py`, `GeographyPortMixin.world_map`), and `load_geography(world_map)`
(`sim/geography/loading.py`) turns it into the older `land_tiles` dict.

A probe overlay with one new tile (not committed; run with `python3 -I` on a scratch folder) showed:
the tile appears in the merged grid, `problems()` reports nothing, `tile_facts` and `food_potential`
answer for it. So the mechanism exists. What blocks real use:

1. **Readers that ignore the mods.** Several modules open the base map directly instead of the
   simulation's map: `sim/geography/tile_names.py` (`_tiles`, `_climate_words`, `_region_names`
   through a bare `load_geography()`), `tile_lookup.py` (nearest tile), `territory.py`
   (`map_source.load_map()` for frontier and roads), `crop_climate.py` (`load_geography()`),
   `sim/engine/agents_port_cast.py` (`load_geography()["land_tiles"]`), `sim/ui/cli_interactive.py`
   (`load_geography()`), and the default arguments in `sim/world/land.py`
   (`load_region_lands`, `load_tile_lands`) and `tile_holdings.py`. A mod tile is therefore
   invisible to place names, territory, the cast's anchors and the interactive map. Counts below.
2. **No tile validation.** `queries.problems` checks parameters, mechanisms, route modes and
   resource rows only (`sim/geography/queries.py`). Nothing checks that a new tile has the fields
   the models read (latitude, longitude, land area, coastal flag, climate class, region), that its
   `borders` name real tiles, that its climate class exists in `climate_classes`, that its region
   exists in `regions`, or that the layers a model needs have a value for it.
3. **Silent zeros.** `tile_layers.number(...)` returns the default when a layer has no value for a
   tile, so a tile without a rain value gets zero crops with no message. The probe tile showed this
   shape: crops zero while pastoral and hunting answered. Routes do the same: `routes_graph.py`
   treats a coastal tile with no `is_port` value as not a port when the layer exists.
4. **One-sided borders.** Land edges are built from the union of every tile's `borders`
   (`_land_and_river_edges`, `routes_graph.py`), so a new tile joins the graph with only its own
   list, but `tile_facts` of the neighbour does not list it, and a removed tile leaves its name in
   other tiles' `borders` (ignored by the edge builder, but a stale reference all the same).
5. **No dependency check on map ids.** `mods_ids.check_declared_dependencies` scans tech, recipe and
   civilisation data; it does not scan geography files, so a mod that places a tile in another mod's
   region does not need to declare that mod.
6. **Civilisation start data names tiles.** Shipped civilisation files list `home_tiles`; a mod
   civilisation may list `home_regions` labels instead (the tiles carrying them). A mod tile joins a
   shipped civilisation by a patch that replaces its `home_tiles`, or a mod civilisation listing a mod region. That is workable; it only needs validation (a region with no
   tiles, a tile naming no region).

### 1.2 Commands

Two separate command systems exist and a mod needs both to be reachable.

**Protocol commands** (what a player or agent types, `sim/PROTOCOL.md`). Registry:
`sim/ui/proto/command_registry.py`, a module-level `COMMANDS` dict filled by `@command(...)` or
`register_command(...)`, which asserts that a name is not registered twice. Discovery: every
`sim/ui/proto/dispatch_*.py` module is found by name with `pkgutil.iter_modules` and imported by
`sim/ui/proto/dispatch.py` (lines near the top), so a new in-repo command needs no list edit; the
same trick finds `parse_*.py` (`typed.py`, `_load_parser_modules`) and `render_*.py`
(`render_typed.py`). Snapshots taken once at import: `_AGENT_DISPATCH_TABLE` and `KNOWN_COMMANDS`
(`dispatch.py`), `TYPED_ALIASES` (`typed.py`). `unregister(name)` exists and tests use it.
The typed parser reads each command's `shape` ("bare", "tech", "tech_done", "file", "word", "text")
from the registry, so a command with a plain shape needs no parser. Help pages, the "did you mean"
list and the group listing are all read from the registry; an unknown group is shown after the
listed ones (`GROUP_ORDER`).

**Player order commands** (what a queued order of a second player or AI runs):
`sim/agents/player_commands.py`, `COMMANDS` plus `register_command(name, handler)`, which replaces
silently on a repeat name. It is exported through `sim/agents/api.py`.

What blocks a mod:

1. **No loader runs code or reads command data from a mod.** `mods.py` opens only JSON
   (`json_files`); nothing in `sim/engine` uses `importlib` on a mod path (the complaint's grep still
   holds). The `dispatch_*` discovery scans the repository's own package directory only.
2. **Import-time snapshots.** `KNOWN_COMMANDS`, `_AGENT_DISPATCH_TABLE` and `TYPED_ALIASES` are
   frozen when `dispatch.py` and `typed.py` load; a command registered later is missing from them
   (`dispatch.py` line near 565 calls `handlers()` live, the others do not).
3. **Name collisions are asserts, not mod errors**, and a typed command word is one flat namespace
   shared with aliases, so two mods choosing `survey` collide with no message naming either mod.
4. **No fog or fuzz contract for a mod handler.** `fog_hidden` exists on the entry, but a handler
   that prints a tech id leaks under fog; the scanner test `test_scanners_and_scheduling.py` checks
   the repository's own commands only.
5. **Declarative precedent exists but only for figures.** `data/ui/figures.json` (and each mod's
   copy) is read by `sim/engine/ui_data.py`: figures name state paths, a path may call a method only
   if it carries `@readable` (`sim/engine/readable.py`), and a bad path is refused at load naming
   the file. Commands have no equivalent.

### 1.3 Actor kinds

Registry: `sim/agents/registry.py` holds `ACTOR_CLASSES` (kind to class), `SPAWNERS` (rules that
found actors after the year's turns) and `WORLD_SCOPE`; `register_actor_kind(kind, class)`,
`register_spawner(name, fn)` and `sim/agents/policy.py` `register_policy(kind, factory)` /
`make_policy` add to them, and `sim/agents/api.py` exports all four. The cast
(`sim/agents/cast.py`, `seed_cast`) creates actors from a civilisation's `cast.actors` entries by
`kind` and deliberately skips a kind that is not registered yet, creating it on a later call. The
shipped kinds register themselves at import (`trader.py`, `stratum.py`, `player.py`,
`government_foreign.py`); `api.py` imports each of those modules by name so the registration
happens.

So the registry is real and keyed by kind, and `MULTIPLAYER.md` says "a mod can add a kind of
actor". In practice a mod cannot, because:

1. **No loader**, as for commands: nothing imports mod Python, and the engine's mod loader never
   reads a kind declaration from data.
2. **A kind class needs a large implicit interface.** It is built as
   `ACTOR_CLASSES[kind](actor_id, record, make_policy(policy_kind))` (`registry._wrap`), is run by
   `ActorRegistry.advance`, and the registry probes it with `hasattr` for `rivals_of`,
   `on_capacity_change`, `find_actor`. The interface is a base class (`RecordedActor`,
   `sim/agents/base.py`) plus duck-typed extras, written nowhere as a contract.
3. **One flat record.** `ActorRecord` (`sim/agents/records.py`) carries the union of firm,
   government, stratum and group fields; a new kind with its own state has nowhere to put it except
   by editing that dataclass.
4. **Enumerated kind names in engine code.** `society_disclosure.py` lists `("firm", "government")`
   for a report, `licence.py` and `society_disclosure.py` compare to `"firm"` and
   `"interest_group"`. A mod kind is invisible to those, which is correct for a report about firms
   but must be a stated choice, not an accident.
5. **A save made with a mod kind fails with `KeyError`** when the mod is later removed
   (`registry._wrap`); there is no message naming the mod. No migration is wanted (CLAUDE.md 4.6),
   only a clear error.
6. **A "species" needs data, not just a class.** CLAUDE.md 4.3 says dragons are agents with calorie
   needs, not a branch. The needs catalogue (`data/world/needs.json`, `sim/world/need_demand.py`)
   already lets a mod declare needs and goods; a kind has no data way to say "consumes these needs".

### 1.4 Counts (2026-10-06)

| What | Count | Command |
|---|---|---|
| Protocol commands registered | 76 | `grep -rn '^@command(\|register_command(' sim/ui --include='*.py' \| wc -l` |
| `dispatch_*.py` modules found by name | 27 | `ls sim/ui/proto \| grep -c '^dispatch_'` |
| Actor kinds registered by the shipped code | 4 beyond the three built in | `grep -rn 'register_actor_kind(' sim --include='*.py' \| grep -v 'def \|tests\|api.py' \| wc -l` |
| Readers of the base map only, `map_source.load_map()` | 7 | `grep -rn 'load_map()' sim --include='*.py' \| grep -v tests \| wc -l` |
| Calls of `load_geography()` with no map | 11 | `grep -rn 'load_geography()' sim --include='*.py' \| grep -v tests \| wc -l` |
| Mod test topics | 6 | `ls sim/tests/test_mod_*.py \| wc -l` |

The goal for both map counts is zero outside the geography package's own default-argument seam.

## 2. Proposed mechanisms

All three follow one shape: **data first, code only where data cannot say it, nothing implicit.**
Every mod item is named `<mod_id>:<name>`; every cross-mod reference needs a declared dependency;
`override` patches and `remove` deletes with the existing claim checks (`mods_base.claim_fields`,
`claim_removal`, `check_not_removed`); a removal that leaves a reference dangling is an error
naming the remover and the referrer.

### 2.1 Land tiles: data merged into the tile grid, with validation

No new loader. The change is to make the existing overlay complete.

1. **Every reader takes the simulation's map.** Replace each base-map read in section 1.1 with a
   `world_map` argument (as `load_geography(world_map)` and `queries` already do), threaded from
   `sim.world_map`. A static-analysis test fails if `map_source.load_map()` or a bare
   `load_geography()` appears outside the geography package's one defaulting function.
2. **Tile validation inside `queries.problems`** (new module `sim/geography/map_validate.py`, so the
   file stays short). For every tile, in the merged map: required fields present and typed
   (`lat`, `lon` in range, `land_area_km2` positive, `coastal` boolean); `koppen_class` in the
   `climate_classes` catalogue; the region label in `regions`; every `borders` entry a tile in the
   merged map; and every layer a model declares as required has a value for the tile. Required
   layers are declared in data, not code: a `required_layers` list on each parameter or mechanism
   row that reads layers (food mechanisms, `is_port` for coastal tiles when a port layer exists), so
   a mod mechanism declares its own. A message names the file that added the tile (the merge already
   knows each file; keep an `origin` per entry, `_internal`, not a player field).
3. **Reciprocal borders at merge time.** After merging, the loader makes `borders` symmetric in
   memory for tiles a mod adds (a tile that lists a neighbour adds itself to that neighbour's list)
   and prunes names of removed tiles. A mod therefore never has to override base tiles just to
   connect.
4. **Removal is checked.** Removing a tile errors if a civilisation start (`home_regions` becoming
   empty), a located material, a deposit or another mod's tile still names it. Removal of a tile
   also drops its layer values and its edges.
5. **Routes, climate and food pick tiles up with no further code**, because they read layers and
   `borders` through `tile_layers` and `routes_graph`: land edges from `borders`, river and sea
   edges from layer values (`river_km_navigable`, `is_port`, `coastal`), climate from
   `koppen_class` through the `derived_layers` rules, food from the climate and elevation layers
   through the food mechanisms. What a mod must supply is exactly what validation lists as missing;
   a mod author gets a message, not a zero. A mod may also add a whole new climate class, derived
   rule or route mode in its own catalogue files (already supported).
6. **Map dependency check.** Extend `mods_ids.check_declared_dependencies` to read ids from
   geography files (tile `old_region`, catalogue references, layer ids) so using another mod's
   region requires its declaration.
7. **Cache safety.** `load_map` is cached by the overlay tuple, and `tile_layers` caches per map
   object, so a changed mod set builds a new map; nothing else to do, but a test pins it.

Safety boundary: pure data, so a bad mod can crash or build a nonsense map but cannot run code.

### 2.2 Commands: data plus a Python module the loader imports into the registry

Two tiers, so most mods never need code.

**Tier A, declarative (no code, no consent).** `mods/<id>/data/ui/commands.json`, beside the
existing `figures.json`, merged in mod load order by a new `sim/engine/ui_data` sibling
(`ui_commands.py`):

- `kind: "read"`: name, group, summary, usage, description, `shape` (one of the existing plain
  shapes), and `shows`: a list of `{label, path, unit?, digits?}` using the same state-path grammar
  and the same `@readable` gate as figures (`check_state_path`). The reply is a plain table. No
  state change.
- `kind: "macro"`: a template of existing commands with argument substitution, replayed through
  the normal dispatch so fog guards, option checks and money localisation apply. A macro may not
  name a macro (no recursion), and every command it names must exist at load or the mod fails
  naming the file.
- `kind: "policy"` (from `mods/TASKS.md` item 3): a condition on readable paths and an action from
  the existing command set, run at a named hook (start of year, after year). Same safety as a macro.

**Tier B, Python (consent required).** The manifest gains an optional `code` object:
`{"commands": ["commands.py"], "actors": [...]}` and `"permissions": ["code"]`. The loader imports
each listed file by path (`importlib.util.spec_from_file_location`, module name
`sim_mod.<mod_id>.<file>`) after Tier A, only for mods the player has consented to. The module
calls one function, `mod_api.command(name, group=..., summary=..., ...)`, a decorator with the same
fields as `@command` that registers the entry in `command_registry`.

Rules for both tiers:

- **Names.** The canonical name is `<mod_id>:<name>`. A bare word works as an alias only while it is
  unique among all commands, aliases and mods; a clash is a load error naming both mods (not an
  assert), and the player can always type the full id. Collision with a base command is an error
  unless the mod uses `"override": true` (a command override replaces the entry, with the same
  claim check as other overrides) or `"remove": true` (delete a base command; the check that no
  macro, help topic or alias still names it applies).
- **Registration timing.** Mod commands are registered in one function,
  `load_mod_commands(mods)`, called at the end of the `dispatch.py` module-level discovery loop,
  before `KNOWN_COMMANDS`, `_AGENT_DISPATCH_TABLE` and `TYPED_ALIASES` are built, so the snapshots
  include them. A test asserts the three agree with `COMMANDS` after mods load.
- **Typed parsing.** A mod command declares one of the existing shapes; a new shape is engine code.
- **Fog and fuzz.** A mod command sets `fog_hidden` or declares that it names no technology; a
  scanner test runs the existing fog scan over mod commands the same way it does base commands.
- **State.** A handler may keep state only in `sim.mod_state[mod_id]` (a plain dict that the save
  file detects automatically, as all `Sim` fields are), never in module globals, so saves round-trip
  and the fingerprint stays honest. Randomness comes from the world's keyed generator
  (`world.rng_for(...)`), never `random`.
- **Player order commands** (`sim/agents/player_commands.py`) take the same two tiers: a manifest
  list registered through `register_command`, names namespaced, a repeat name an error rather than a
  silent replace.

**Safety boundary, stated plainly.** Tier A is data: the worst case is a crash or a nonsense
reply. Tier B is Python run in the player's process with the player's full permissions (files,
network, credentials); no in-process sandbox for CPython holds, and a restricted facade is an
interface for honest mods, not a defence. So Tier B is off by default; a mod that ships code is
listed by `simulator.py validate` and refused to load unless the player has consented to that mod
id and the sha256 of its code files (`mods/consent.json`, written by an explicit
`simulator.py mod-allow <id>` subcommand that prints the files it hashes); a changed file needs
consent again. A real boundary (subprocess with an allowlisted message API, or WASM) is the only
safe way to run code from an unknown author and is out of scope here; this plan states that rather
than implying the facade protects anyone. This matches `Complaints/118` and `mods/TASKS.md` item 5.

### 2.3 Actor kinds: a registry keyed by kind with a policy interface

The registry already exists; the work is to make it a contract, give a kind data to run on, and
connect mods.

1. **Write the kind contract** as a `typing.Protocol` in `sim/agents/kind_contract.py` (exported
   from `api.py`): constructor `(actor_id, record, policy)`, `kind`, `identity()`, `year(world)`,
   plus optional capabilities declared as named flags rather than `hasattr` probes
   (`runs_concerns`, `has_staff`, `borrows`). `registry._wrap` reads the flags. The existing kinds
   adopt it without behaviour change (fingerprint check).
2. **A policy interface for every kind.** `Policy.choose(actor, decision)` already is the seam
   (`ValuePolicy`, `CallbackPolicy`, `IdlePolicy`, `register_policy`). The contract states that a
   kind asks its policy for every choice with a `Decision(kind, options, budget)`, so a human, an AI
   or a mod can drive it; a kind may name which decision kinds it raises
   (`decision_kinds`) so a policy can be validated against it.
3. **Per-kind state.** Add `ActorRecord.extra: Dict[str, Any]` (plain JSON data, auto-saved) for
   state outside the shared fields; a kind reads and writes only its own keys. No change to the
   shared fields.
4. **Data-declared kinds** (`mods/<id>/data/world/actor_kinds.json`): an entry
   `{id: "<mod_id>:<name>", base: <registered kind or "generic">, needs: {...}, policy: "value",
   behaviours: [...], spawner: {...}}`. `generic` is one shipped class whose behaviours are chosen
   from a small registered list of behaviour functions (consume needs from the needs catalogue,
   grow or shrink, work a trade, hold land, pay or receive through `ledger.transfer`). A species is
   then data: calorie needs and diet through the existing needs and recipe catalogue, growth rate,
   the trade it works, and the spawner rule as a condition on readable paths. This follows
   CLAUDE.md 4.3: no bespoke branch, no hand-set outcome; the species competes for the same food
   and labour through the ordinary markets. Money moves only through `ledger.transfer`, so the
   conservation test covers it.
5. **Python kinds (Tier B, same consent as commands).** The module calls `register_actor_kind`,
   `register_policy` and `register_spawner` from `sim.agents.api` (the only door of the walled
   package). The loader prefixes names: kind and spawner names must start with `<mod_id>:`,
   checked at registration, so two mods cannot register the same kind.
6. **Clear failure on a missing mod.** `registry._wrap` raises an error naming the kind and, because
   the save records the mod ids it was made with, the missing mod. No migration, only the message.
7. **Engine enumerations stated.** The three kind-name comparisons in section 1.3 item 4 get a
   comment-free fix: the reports read a `report_as` capability on the class (`firm`, `government`,
   none) so a mod kind opts in explicitly.
8. **Cast.** A civilisation's `cast.actors` entry naming a mod kind needs the mod declared as a
   dependency; `seed_cast` already waits for an unregistered kind, so load order does not matter.
   A mod can also patch `cast` on an existing civilisation (already supported).

Safety boundary: data kinds are data. Python kinds share Tier B consent and the same caveat.

## 3. Audit: other places where adding content means editing a list in code

Method: search for module-level tuples, sets and dicts of quoted ids, for `if kind ==` and `elif`
chains, and for literal ids in non-test code. Ranked by how often content changes there (most
often first). Frequency is the author's judgement from how branches and mods add content; the
counts are measured.

| Rank | Place | What is enumerated | Why it matters | Fix direction |
|---|---|---|---|---|
| 1 | Done: per-category traits (`never_abandoned`, `practisable`) and the ordered `diffusion_traits` live in `data/world/category_traits.json`, read through `sim/engine/category_traits.py`; a mod overlays its own `data/category_traits.json`; `validate` reports a node category with no entry | Technology categories and trait names | Was: every new branch domain needed an engine edit | The literal trait name `medical` is still read by `sim/engine/hazard_relief.py` |
| 2 | `sim/engine/mods.py` `_node_defaults`; `sim/engine/tree_merge.py` `DEFAULTS` and the second list near line 50 | Node field defaults, written in more than one place | A new node field is a multi-place edit; a mod and the base can disagree | One defaults table in data, read by both loaders |
| 3 | `sim/labour/legacy_trade_defaults.py` `GENERIC_STAFF_TRADES`; literal trade ids in engine code (see counts) | Trade names such as the labourer, artisan, scholar | Trades are data (`data/world/trades.json`), the engine names a few | A `role` attribute on a trade record (`general_labour`, `skilled`, `learned`) read by the engine |
| 4 | Base-map-only readers (section 1.4) | Which map is open | Blocks land tiles | Section 2.1 |
| 5 | `sim/engine/data.py` `STARTING_KITS`, `WIN_CONDITION_LABELS` | Starting kits and win metric labels | A new scenario or goal type edits Python | Move to `data/world/starting_kits.json` and the metric catalogue, mod-mergeable |
| 6 | Hazard kinds: `HAZARD_KINDS` in `sim/ui/figures_headline.py` and `sim/engine/hazard_relief.py`, the `_shock_*` methods in `sim/engine/society_hazards.py`, `sim/ui/proto/hazard_words.py`, `sim/engine/fog.py` loops | Four hazard kinds | A new hazard kind is a code change in five files (the complaint's point 7) | One hazard-kind registry (name, shock function, words, fog rule); data rows for ordinary hazards of an existing kind are already civilisation data |
| 7 | `sim/agents/api.py` import list | Which agent modules register their kinds, spawners and commands | An in-repo kind needs an edit to the door; the dispatch modules show the better pattern | Discover by name, as `dispatch.py` does, or by a manifest |
| 8 | `sim/engine/core.py` `class Sim(...)` base list (mixins) | Engine mechanisms | Each mechanism adds a base class; low churn, but it is the largest enumeration | Mixin discovery by name is risky for ordering; leave, but record the order as data if mods ever hook the year |
| 9 | `sim/geography/mechanisms.py` `OWNER_OF_MECHANISM`, `resources_catalogue.py` `DEPOSIT_MECHANISMS`, `sim/world/deposits.py` `DEPTH_CLASSES`, `HARDNESS_CLASSES` | Resource and deposit mechanisms and classes | Mechanisms are code by design; the classes are content | Move the classes to the catalogue; keep mechanisms as the stated code boundary |
| 10 | `sim/agents/stratum_year.py` `TIERS`, `sim/agents/cast.py` `CONSUMED_CAST_KEYS`, `sim/agents/exchange.py` `SIDE_KEYS`, `sim/economy/currency.py` `REGIMES`, `state_policy.py` `STATE_FINANCING_ORDER` | Need tiers, cast keys, exchange sides, currency regimes, financing order | Low churn; some are mechanisms, some content (tiers) | Tiers into the needs catalogue; leave the rest |
| 11 | Display-order lists in `sim/ui/proto` (`GROUP_ORDER`, `TIER_NAMES`, `KIND_ORDER`, `_SCORE_COMPONENT_ORDER`, `WAITING_KIND_ORDER`) | Presentation order | A new item falls to the end, which is safe | Leave |
| 12 | `data/world/foreign_economies.json` read from base only (`mods/README.md`) | Trading partners | A mod can add a civilisation but not enable it as a partner | Merge the mod's copy under the usual rules |
| 13 | Physical lists: `ENERGY_CARRIERS` (copies in `energy_prices.py`, `solve_prices_core.py`, `economy/recipes.py`, plus `validate_production.py`) | Energy carrier fields | Physical, rarely changes, but one list is copied into several modules | One definition imported by all |

Already good, to copy: `dispatch_*`, `parse_*` and `render_*` discovery by name; the command
registry; `figures.json` plus `@readable`; geography catalogues merged by folder; the `mechanics`
index (`sim/engine/mechanics.py`) that reads node data; the actor, spawner and policy registries.

Literal content ids in non-test code, measured 2026-10-06 by
a scratch script that counts lines holding the quoted id in `sim/` outside the tests (not kept; a
measurement worth keeping becomes a `simulator.py` subcommand, see the audit command below): the labour trades appear on many lines (labourer, scholar, artisan), the materials a few
(iron, copper, silver, gold, wheat), a currency name twice, civilisation names in one file
(`sim/default_civilisation.py`). The complaint's `MONEY_WORDS` no longer exists in `data.py` (no
match for it in `sim/`); treat the complaint's point 8 as partly stale.

How to check the owner's rule after each stage: the end-to-end test cannot prove that no engine file changed, so the guard is the audit itself.
Add `simulator.py validate --audit-enumerations`, which lists module-level collections of quoted
ids against a checked-in allowlist (mechanisms and physical constants are allowed with a reason),
so a new enumeration is reported when it is added. Until it exists, the grep patterns above are the
check.

## 4. Staged plan

Each stage lists the files it touches. "Waits" means the stage edits a directory another branch is
changing; do not start it until that branch merges.

Branches in flight to respect (from `git branch`, measured 2026-10-06): the geography work
(`civilisations-hold-tiles-and-roads` touches `sim/geography/tile_holdings.py`, the engine's use of
routes; `map-data-licence-audit` touches `data/world/geography/`) and the counterparty work
(`every-posting-names-a-counterparty` touches `sim/agents/`, the ledger and every posting). Check
`git log <branch>` before starting a stage that waits.

**Stage 0: fixtures and a mod test harness. Does not wait.**
- New `sim/tests/mod_fixtures/ana_hooks_test_k3f9/` (the "hooks test mod"): `mod.json`, one tile
  file, one commands file (one read command, one macro), one actor kind file, and a small Python
  commands module held back until Stage 4. Reuse `ModTestBase.add_mod` from
  `sim/tests/test_mod_removal_and_civs.py` for temporary mods.
- New `sim/tests/test_mod_hooks_end_to_end.py`: installs the fixture mod, opens a game, and asserts
  the three things in later stages. It starts as a list of expected failures, one per hook.
- Touches: `sim/tests/` only.

**Stage 1: land tiles. Waits for the geography branches.**
- 1a. Failing tests: a mod tile is visible to `tile_names`, `territory`, `land.load_tile_lands`,
  `agents_port_cast`; `problems()` reports a tile with a dangling border, unknown class, unknown
  region, missing required layer; reciprocal borders; tile removal pruning; a route from a base
  tile to the mod tile; food potential for it; fingerprint unchanged for the base map.
- 1b. Thread `world_map` through the readers in section 1.1 and add the static test.
  Touches `sim/geography/tile_names.py`, `tile_lookup.py`, `territory.py`, `crop_climate.py`,
  `tile_holdings.py`, `sim/world/land.py`, `sim/engine/agents_port_cast.py`,
  `sim/ui/cli_interactive.py`.
- 1c. Validation and merge-time borders: new `sim/geography/map_validate.py`, edits to
  `map_source.py` (origin per entry, reciprocal borders), `queries.py` (`problems`), data rows
  `required_layers` under `data/world/geography/parameters/` (**data/world/geography waits**).
- 1d. Map ids in `check_declared_dependencies`: `sim/engine/mods_ids.py`.
- Docs: `mods/README.md` map paragraph, `sim/geography/INTERFACE.md` (`problems`).

**Stage 2: declarative commands (Tier A). Does not wait** (touches `sim/ui/proto`, `sim/engine`).
- Tests: a read command and a macro from a mod appear in `help`, `KNOWN_COMMANDS`, the typed
  parser and a protocol reply; a name clash names both mods; a macro naming a missing command fails
  at load naming the file; an override and a removal with the dangling-reference check; fog scan
  covers them.
- Files: new `sim/engine/ui_commands.py` (load and validate), new `sim/ui/proto/mod_commands.py`
  (turn a declaration into a registry entry and a handler), edit `sim/ui/proto/dispatch.py` (call it
  before the snapshots), `command_registry.py` (an `owner` field, a clash error naming mods
  instead of an assert), `typed.py` only if the alias snapshot needs to move.
- Docs: `mods/README.md`, `sim/PROTOCOL.md`.

**Stage 3: the actor kind contract and data kinds. Waits for the counterparty branch** (edits
`sim/agents/registry.py`, `records.py`, `base.py`, which that branch is changing).
- Tests: the existing kinds satisfy the contract (flags replace `hasattr`); a data-declared kind from
  the fixture mod is created from a civilisation's cast, consumes a need, spawns by its rule, pays
  through the ledger, and the conservation test still holds; removing the mod gives the clear error;
  fingerprint unchanged for base play.
- Files: new `sim/agents/kind_contract.py`, `sim/agents/generic_kind.py`,
  `sim/agents/kind_data.py` (load `actor_kinds.json`); edit `registry.py` (`_wrap`, flags, error),
  `records.py` (`extra`), `api.py`, `society_disclosure.py` and `licence.py` (`report_as`).
  Engine side: `sim/engine/agents_port*.py` hands the loader the mod list.
- Docs: `sim/agents/MULTIPLAYER.md`, `docs/architecture/ACTORS.md`.

**Stage 4: Python hooks (Tier B) for commands and kinds. After 2 and 3.**
- Tests: a mod without consent does not run (a marker file is not written); with consent it
  registers a command and a kind; a changed file needs consent again; names must carry the
  prefix; a handler's state lives in `mod_state` and survives save and load.
- Files: new `sim/engine/mod_code.py` (consent file, hash, import), `sim/simulator.py` (a
  `mod-allow` and a `validate` report), manifest keys in `sim/engine/mods.py`, `sim/engine/mods_ids.py`
  (`code`, `permissions`), `sim/ui/proto/mod_commands.py` (decorator).
- Docs: `mods/README.md` security paragraph, `mods/TASKS.md`.

**Stage 5: the audit follow-ups, in rank order, one small change each. Each waits only if its
files are in a directory under change.**
- Ranks 1 and 2 first (categories and node defaults: `economy_production.py`, `fog.py`,
  `society_diffusion.py`, `mods.py`, `tree_merge.py`, `data/branches`), then 3, 5, 6, 7, 13.
  Rank 4 is Stage 1b. Each change keeps the fingerprint identical.

**Order and dependencies.** 0, then 2 (independent of both waiting branches) while the geography
and counterparty branches land; then 1 and 3 in either order; then 4; 5 throughout.

Record the result by moving Complaint 118 to `Complaints/closed/` when Stages 1 to 4 pass, and by
turning `mods/TASKS.md` items 3 and 4 into links to this plan. Open question for the owner: whether
Stage 4 ships at all, given the safety boundary in section 2.2; Stages 1 to 3 are useful without it.
