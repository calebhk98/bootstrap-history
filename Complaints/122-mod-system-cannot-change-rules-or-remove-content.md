# The mod system adds content but cannot change rules or remove content

**Source:** playtester report that mods are "heavily restricted": no runnable
code, no magic or elves, cannot change or hide Rome, cannot really change the
tech tree. **Status:** Confirmed, with two defects found while checking.

## What a mod can do today

Loader: `sim/engine/mods.py`, `sim/engine/catalog.py`; callers in
`sim/engine/data.py`. Every `mods/<dir>/mod.json` is active; no registry.

| Content | Add | Override | Replace | Remove |
|---|---|---|---|---|
| Tech nodes (`data/branches/*.json`) | yes, id must start `<mod_id>_` (mods.py:104, 138) | `"override": true` deep merge (mods.py:145) | `"replaces"` (mods.py:134) | no |
| Goals (`data/goals.json`) | append only (mods.py:147-153) | no | no | no |
| Production recipes (`data/production/*.json`) | yes, prefixed (mods.py:159-173) | `"override": true` | same as override | no |
| Trades (`data/world/trades.json`, `trade_families.json`) | yes, prefixed (catalog.py:113) | duplicate id is an error (catalog.py:115) | no | no |
| Civilisations (`data/civilizations/*.json`) | yes, filename must be prefixed (mods.py:181) | no | no | no |
| Manifest | id, name, version, dependencies, conflicts (mods.py:24-39) | | | |

Materials need no `prices.json` entry (catalog.py:59-70).

## What it cannot do (evidence)

1. **Runnable code.** Nothing imports, execs or otherwise runs a mod file.
   `grep importlib|exec(|__import__` over `sim/engine` finds no plugin
   loader, and the loader only opens `.json` (mods.py:85-89). I put a `.py`
   file printing a marker inside a throwaway mod; `validate` never ran it.
   There is no hook, event or extension-point API.
2. **New species or agents (elves, dragons).** There is one actor,
   `sim/engine/actors/household.py`; population and labour are human-only
   aggregates (`labour_population.py`). A node with extra keys such as
   `mana` or `kind` is accepted silently and ignored (tested: only
   `missing required field 'cat'` is enforced; unknown keys pass). A mod
   node with no `name` crashes `validate` with a bare `KeyError: 'name'`
   instead of a `ModError`.
3. **New mechanics (magic as energy or a resource).** No mod extension point
   exists for state fields, per-year update phases (`core_step_phases.py`),
   or new resource kinds. `w_magic_fear` in civ values (data.py:308) is a
   social attitude, not a mechanic. README states "arbitrary new mechanics
   are not mod extension points yet" (mods/README.md, second-last section).
4. **Change or hide Rome or any base civ.** `load_civ` reads the base file
   first and only falls back to a mod (data.py:279-281); a mod civ needs a
   prefixed name, so it cannot shadow a base id (tested: a mod file named
   `rome_100ad.json` is rejected at mods.py:106). There is no override,
   patch or "hidden/unplayable" flag: `civilization_ids()` (data.py:322)
   lists every non-underscore file in `data/civilizations`. Egypt's mod is a
   full copy of the Rome file (it still carries Rome's opening text), the
   only way to "change Rome".
5. **Remove or restructure base tech nodes.** No `delete`/`remove` key
   exists. `override` can only deep-merge. Because `_node_defaults`
   (mods.py:110-119) runs on the patch before merging, see defect A below.
   Rewiring prerequisites is possible only by replacing the whole `pre`
   list; deleting a node other nodes depend on is impossible.
6. **World geography, resources, deposits.** `RESFILE`, `GEOFILE`
   (data.py:110-111) and `sim/world/deposits.py` (`DEPOSITS_FILE`, line 282)
   read base files only; `mods/*/data/world/geography.json` is never opened
   (tested: a mod region did not appear in `load_geography()`).
7. **Hazards and events.** Hazards live only inside each civilisation file
   (`society_hazards.py:606`). A mod cannot add a hazard to a base civ; a
   mod civ can carry its own. Hazard kinds are a closed set of
   Python methods (`_shock_staff_loss`, `_shock_sack_chance`,
   `_shock_output_factor`, `_shock_real_erosion`, `_shock_values`), so a new
   kind needs engine code.
8. **UI text and currency.** `MONEY_WORDS`, `MONEY_SHORT_WORDS`
   (data.py:244-260), `STARTING_KITS`, `WIN_CONDITION_LABELS` are Python
   dicts in `data.py`; the protocol/renderers in `sim/engine/proto/` have no
   mod hooks. `money_short` falls back to "den" for any unknown currency, so
   a mod currency displays wrongly. Strategies load from `sim/strategies`
   only (`STRATS`).
9. **Other.** Goals cannot be removed or reordered; `data/prices.json`,
   wages (`WAGES`) and `TRADE_FAMILY` are still base-owned, with new trades
   getting a family-median wage (catalog.py:143-159); capabilities
   (`00_capabilities.json`) are not a mod surface.

## Defects in what does exist

**A. An override silently resets every field it does not mention.**
`load_mod_tree` fills defaults into the patch (`_node_defaults`, mods.py:144)
and then deep-merges it over the base node (mods.py:145). Lists and scalars
are replaced. Tested with a mod containing only
`{"id":"mat_copper","override":true,"cap":222}`: `pre` went from
`[blast_furnace, cap_heat_1100]` to `[]`, and risk, conf, kb, traits, up, ph
all reverted to defaults. A "retune one cost" override therefore deletes the
node's prerequisites, which is the opposite of a patch. the mod contract
describes an override as a deliberate replacement, but README calls it a
"deep merge"; the code is neither.

**B. Two mods overriding the same base node are silent last-wins.** Mods are
ordered by dependency then id (mods.py:80-81). Two unrelated mods both
overriding `mat_copper` are applied in id order with no diagnostic
(tested: mod `a` set `cap` 111 and `pre` to add `a_x`; mod `b` set `cap` 222;
result was 222, and `a`'s prerequisite was wiped, which is defect A). The
outcome depends on alphabetical mod ids.

## Third-party compatibility (two authors who have never met)

- **New ids:** safe. The mandatory `<mod_id>_` prefix for nodes, recipes,
  trades and civs (mods.py:104-107, catalog.py:113) means two mods cannot
  collide on new ids unless they pick the same mod id, which is an error
  (mods.py:52).
- **Overrides of one base node:** silent last-wins by id order, and each
  override also resets unmentioned fields (defects A and B). No error, no
  merge report.
- **Goals:** appended to one list with no duplicate check, so two mods can
  add goals for the same node (mods.py:153).
- **Trades:** a shared base trade can not be extended, only prefixed new
  ones added; a duplicate is an error (catalog.py:115).
- **Production overrides:** duplicate id is an error, but a same-id override
  from two mods is last-wins (mods.py:166-172).
- **Declared compatibility:** `dependencies` and `conflicts` exist and are
  enforced, but `conflicts` fails the whole game if both installed
  (mods.py:60-63): it is an install-time hard error, not a per-mod
  ordering. There is no `load_after`, version range, or minimum game
  version. The `version` field is never compared.
- **Cross-mod references:** a mod may reference another mod's ids only by
  declaring a dependency; nothing checks that it did (only the material
  producer check at catalog.py:73).
- **Error blame:** most errors name the file; the `KeyError` cases do not.

## Why it matters

The sample mods are data packs. A new setting, species, resource or rule, or
removing or rewriting the base game, needs engine edits, so mod authors fork
the repo, which loses the compatibility the manifest was meant to give. The
override defect makes even legitimate data retuning unsafe.

## What it would take (highest value per cost first)

1. **Fix defect A.** Merge the raw patch, then apply defaults only to new
   nodes. Add a regression test. Small.
2. **Detect override conflicts (defect B).** Track which mod last patched
   each id and field; error (or require `load_after`) when two unrelated
   mods patch the same field. Small.
3. **`remove` for nodes, goals, trades, recipes, and `hidden`/`playable:
   false` for civs.** Loader-side, with a check that no remaining node
   still names a removed id. Follows the existing "explicit, and fails if the
   target is missing" override rule. Small to medium.
4. **Data-driven world layers:** geography regions, deposits, hazards and
   money/UI strings loaded from mods with the same prefix and override
   rules. Medium; each needs its base loader taken off a hard-coded path.
   Civ patching (base civ plus a mod's overlay) belongs here.
5. **Manifest hardening:** minimum game version, `load_after`, unknown-key
   rejection in node schema, `ModError` in place of `KeyError`. Small.
6. **Data-defined resources and species.** Hard, and constrained by
   CLAUDE.md §4.1 and §4.3: elves or dragons must not get a bespoke branch
   with a hand-set outcome. They need an actor type with calorie needs,
   growth and diet that competes with humans, run through the same
   production and labour rules. That is the shared draft-animal/actor
   generalisation the project wants anyway (CLAUDE.md §2 and §5 on
   general and multiplayer actors). Magic-as-energy is easiest if modelled as a
   material or energy source with a production recipe (as electricity
   already is in `economy_electricity.py`) rather than a new mechanic;
   that rides on step 4 plus recipe-driven energy.
7. **Runnable code.** Easy to build, expensive to trust. Prefer a
   declarative expression or rule language over Python. If Python hooks are
   ever allowed: they need named hook points (start of year, hazard kind,
   renderer), a deterministic RNG handed in (saves and the fingerprint
   depend on draw order, see `society_hazards.py` `_shocks` docstring), and
   state kept in the auto-detected save fields.

**Security:** mods run today with no code, so a downloaded mod is data only
(the worst case is a crash or a nonsense economy). Any Python plugin runs
with the player's full user permissions: file, network, credentials. There
is no in-process sandbox for CPython that holds; a "sandboxed" mod needs a
subprocess or WASM boundary with an allowlisted API, an explicit
"this mod runs code" consent per mod, and a manifest permission list. Until
then, keeping mods data-only is a feature worth stating in the README.
