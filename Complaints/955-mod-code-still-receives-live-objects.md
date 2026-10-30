# Mod code still receives live objects beside its declared access

**Status:** partly - every hand-out is a declared `ModAccess` or a narrowed surface except one: command handlers still receive `nodes`

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

What is left:

- Command handlers are still called `(access, nodes, cmd, ended)`: `nodes` is the tech tree's node table the UI passes. It needs the
  interface module to publish the table as a view the handler reads (`tree_nodes`) and the registry's call to drop the argument,
  which changes every shipped and test handler; not part of this pass.
- The `cast` view a mod may declare answers the actors module's live registry (a `legacy_` view, counted by
  `tools/measure/module_graph.py`); a mod that declares it reads a live object, and the effects `pay`, `pay_edge` and
  `receive_from_edge` check their actors through it. Retiring it belongs to the actors module's views, not to the mod door.
- `api.kernel` takes plain functions: a kernel reads nothing of the game (it is checked against the reference's stored samples).

Check: `bash tools/done_check.sh` (mods importing `sim.engine` outside mod_code; mods importing `sim` beyond `sim.mod_api`).
