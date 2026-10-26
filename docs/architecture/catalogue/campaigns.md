# Module `campaigns`

Armies, campaigns, conquest, captives and revolts.

**Status:** moved, on branch `mr/campaigns` (package `sim/campaigns/`, bridge `sim/engine/bridge_campaigns.py`, forwarders
`sim/engine/forward_campaigns.py`). The draft of task 1.5 (a read-only analysis of `e8b004c`) is kept below as corrected by the
move; "What the move changed in this draft" lists each correction.

## What the move changed in this draft

- **Views: one, not three.** Only the army screens read the module from outside; they ask for an owner's armies and free soldiers,
  both answered by `armies[owner]` (`{"armies": [Army...], "free_soldiers": float}`). `campaign_sites` and `stability` had no reader
  outside the module (the draft already marked all three under the caller floor), so they are not published; the module's own
  site, column and garrison readings are methods.
- **Commands: four, not five.** `RaiseArmy`, `OrderArmy`, `RecallArmy`, `DisbandArmy` (the draft folded recall and disband into
  `OrderArmy`; they have different refusal causes and the screens send them separately). `ResolveCampaigns` and `ResolveRevolts`
  are the phases `campaigns` and `revolts` (`PhaseHook`), not commands. `TakeCaptives` is not a command: the module takes
  captives itself and sends `AddCaptives` to the owner of the people.
- **State: four fields, not one.** `state.economy.campaigns` (a dict made by `setdefault` on every read) is `CampaignsWorld`:
  `armies`, `drawn`, `held_since`, `next_id`, with relocations in `sim/tests/equiv_fields.py`.
- **It sends fourteen commands to other owners**, not one (`TransferTile`): the draft listed only the command it found by name.
  Every other write the old code made into someone else's fact is now a command of that owner (table below).
- **`acting_owner` was dead** (nothing called it) and is gone.
- **The draft's "0 callers from mixins" was right**; the only outside callers were `sim/ui/proto/dispatch_armies.py` (six names,
  now forwarders) and `year_phases.py` (two names, now module phases).

## Mixin classes and files absorbed

| Old class | Old file | Now |
|---|---|---|
| `CampaignActorsMixin` | `sim/engine/campaign_actors.py` | `sim/campaigns/armies.py` (`Armies`) |
| `CampaignYearMixin` | `sim/engine/campaign_year.py` | `sim/campaigns/campaign_year.py` (the phase), `contest.py` (siege, storm, tile taken and held) |
| `RevoltYearMixin` | `sim/engine/revolt_year.py` | `sim/campaigns/stability.py` |
| `CaptivesMixin` | `sim/engine/captives.py` | `sim/campaigns/captives.py` |

The rules that are plain functions of plain values are in `sim/campaigns/rules.py` (orders, recall, keeping armies within the
force, the state grievance); the world rules stay in `sim/world/campaign_*.py`, `battle.py` and `sim/agents/{army_raising,unrest,
revolt,authority,ruler}.py`.

## State owned

`CampaignsWorld` (world scope, no per-seat state): `armies` (army id to the `Army` as a dict), `drawn` (tile to the food energy
armies took from it this year), `held_since` (tile to `{year, by, from}` for tiles taken by an army), `next_id`.

## Views published

| View | Kind | Answers | Cached |
|---|---|---|---|
| `armies` | keyed by owner | the owner's armies and the soldiers of its force that are in none | no: the free soldiers come from the state's army line, which polity code still writes outside its commands |

## Commands applied

| Command | Fields | Refusal causes |
|---|---|---|
| `RaiseArmy` | owner, soldiers, tile (optional) | `army_size_not_positive`, `unknown_tile`, `tile_not_yours`, `not_enough_soldiers` |
| `OrderArmy` | owner, army_id, tile | `unknown_army`, `not_your_army`, `unknown_tile` |
| `RecallArmy` | owner, army_id | `unknown_army`, `not_your_army`, `no_tile_to_return_to` |
| `DisbandArmy` | owner, army_id | `unknown_army`, `not_your_army` |

## Commands sent to other owners (the owner's package holds the class; the engine bridge applies it until the owner moves)

| Command | Package | What the bridge does (as the old code wrote it) |
|---|---|---|
| `TransferTile(tile, to_actor, cause, control)` | `sim/land/` | `Sim.transfer_tile`; also sent by `mod_effects.transfer_tile` |
| `RecordWorldEvent(kind, actors, tiles, cause, facts)` | `sim/hazards/` | `world_events.record`; also sent by `mod_effects.kill_people`, `move_people`, `record_event` |
| `WriteStore(store, key, value, owner)` | `sim/stores/` | `sim.stores.write`; also sent by `mod_effects.write_store` |
| `RecordConquestContact(conqueror, previous, tile)` | `sim/actors/` | `contact_events.after_conquest` |
| `AddCaptives(winner, people)` | `sim/demography/` | `agents.add_captives` on the winner's bonded stratum |
| `StrikeFromForce(owner, killed)` | `sim/polity/` | the state's army line less its field dead |
| `SetLandTakenMemory`, `RegisterPeople`, `SetGrievanceReference`, `ResetStateUnrest`, `SetTileReading`, `RecordRising`, `ReplaceRuler`, `CloseSuccessionDispute` | `sim/polity/` | the matching writes on the state's government record in the stability phase |

## Reads (views of owners that have not moved, published by the bridge)

| Owner | Views |
|---|---|
| land | `tile_owner`, `tiles_owned_by` (in `bridge_shared.py`), `tile_owner_map`, `tile_facts`, `home_modes`, `route_between` (quote), `reach_from` (quote) |
| actors | `has_state`, `country_world`, `countries` |
| polity | `organised_factions` |
| seats | `played_countries` |
| demography | `food_eaten` |
| stores | `store` |
| core | `civilisation`, `year` |

`country_world[owner]` is the agents' world adapter for the owner's state (the shared one for the home country, else its country's
scope); the module reads rule inputs off it (`soldiers_under_arms`, `equipment_kg_per_soldier`, `pay_per_person_year`,
`collection_people_by_tile`, `rng_for`, the government's record). The record is read as an object and written only by the polity
commands above. This is the module's one debt of the `legacy_` kind, under the name of an actor view.

## Year phases

`campaigns` and `revolts` (world phases, in that order). Neither shares a phase with another module.

## Forwarders left in `Sim`

`raise_army`, `order_army`, `recall_army`, `disband_army` (commands), `armies_of`, `free_soldiers` (the `armies` view): all called
by `sim/ui/proto/dispatch_armies.py`. They go when that screen sends and reads itself.

## Hard spots

- Campaign resolution iterates armies in id order with random draws keyed by tile, army and year; the commands to land, polity and
  the log are sent in the order the old code wrote them, and the micro equivalence tier and a scripted conquest year were identical
  to the base.
- The stability phase's writes to the state's record are sent in the old order, because the later reads in the same loop (the free
  soldiers behind each tile's garrison) see them.
- `tile_facts` keeps the static food, endemic loss and ruggedness of a tile in a cache on the game (`_campaign_sites`), because
  the geography queries behind it are slow; it is static data keyed by tile.
- The `store` view answers a snapshot of a store (`{default, values}`); reading it creates the store's saved entry, as the old
  `stores.view` did.
