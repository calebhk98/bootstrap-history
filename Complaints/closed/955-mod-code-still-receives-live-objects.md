# Mod code still receives live objects beside its declared access

**Status:** closed - every hand-out to mod code is a declared `ModAccess` or a narrowed surface; command handlers read the tree through `tree_nodes`, and the live `cast` view is refused to mods

A code mod declares the views it reads and the commands it sends (`ModCodeApi.reads`, `ModCodeApi.sends`) and is handed a
`ModAccess` (`sim/assembly/mod_access.py`) that refuses anything else with `UndeclaredRead` or `UndeclaredSend`, naming the mod and the
name. Done:

- Commands, phases, figures and the four providers receive the mod's `ModAccess`.
- View adjusters (`api.adjust_view`) receive a `ModAccess` over the views listed in `reads` (and no sends), not a `Needs`; the one
  mechanism is shared with every other hand-out.
- Effects (`api.effects`) take the mod's `ModAccess` and send each owner's command, so the mod declares what an effect uses:
  `api.uses_effects("pay", ...)` adds the views and commands of `EFFECT_NEEDS` (`sim/engine/mod_effects.py`), and an effect used
  without it is refused naming the mod. Goods move by the markets module's `MoveGoods`, people by the actors module's
  `MoveStratumPeople`; the unchecked `FrameworkDoor` and `door_of` are gone, and a mod store's handle reads and writes through the
  access too.
- Command handlers (`api.command`) are called `(access, cmd, ended)`; the tech tree's node table is the `tree_nodes` view the
  mod declares with `api.reads` (the shipped hierarchy command does).
- Spawners (`api.spawner`) are called `function(access)` and found an actor by sending `AddActor`; player commands
  (`api.player_command`) are called `handler(access, actor_id, order)`. Neither sees the registry, the player object or the world.
  `api.provide` refuses the three points whose answers carry the actors module's own objects (`actor_kinds`, `actor_spawners`,
  `player_commands`), so the typed calls are the only way in.
- Actor kinds (`api.actor_kind`): the class runs inside the agents package and its base classes (the shipped `Church`, `Business`)
  ask the world for everything in `sim/agents/protocols.py`, so a per-mod list of declared views cannot be built without breaking
  the `super()` calls. The actors module therefore keeps handing the agents package its world, narrowed for a mod's classes: each
  method of the mod's own classes that takes `world` receives `NarrowedWorld` (`sim/agents/narrowed_world.py`), which answers the
  members of the `World` protocol and refuses any other (the actors module, its registry, its needs) with
  `UndeclaredWorldMember`, an `UndeclaredRead` naming the mod and the member. The world it answers from is the actors module's, built
  from the views the actors module declares; it holds no `Sim`.

- The `cast` view (the actors module's live registry) cannot be declared by a mod: `api.reads("cast")` is refused naming the mod. A
  mod reads `actor_exists(actor_id)` and `actor_sheet(actor_id)` (id, kind, purse, headcount, prominence, cause note: plain data,
  `sim/actors/actor_sheets.py`); the effects `pay`, `pay_edge` and `receive_from_edge` check their actors through `actor_exists`, and
  the shipped cash shelter reads its holders through `actor_sheet`. A wealth-claims seizer is given the taker's id, not the actor.
- `api.kernel` takes plain functions: a kernel reads nothing of the game (it is checked against the reference's stored samples); this
  is a statement, not a todo.

Check: `bash tools/done_check.sh` (mods importing `sim.engine` outside mod_code; mods importing `sim` beyond `sim.mod_api`).
