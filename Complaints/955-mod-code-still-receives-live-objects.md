# Mod code still receives live objects beside its declared access

**Status:** partly - commands, phases, figures and the four providers get a declared `ModAccess`; four hand-outs remain

A code mod declares the views it reads and the commands it sends (`ModCodeApi.reads`, `ModCodeApi.sends`) and is handed a
`ModAccess` (`sim/assembly/mod_access.py`) that refuses anything else, naming the mod. What is left, each a live object or an
unchecked door:

- Actor kinds, spawners and player commands (`api.actor_kind`, `api.spawner`, `api.player_command`) are classes and functions the
  actors module calls with its own `world` (`sim/actors/world*.py`) and registry: `bh_cashshelter_z6f2` (`Holder.advance`) and
  `bh_religion_h5p1` (`ReligiousHouse.collections`, `invest_surplus`) call `world.rng_for`, `world.edge`, `world.land_rent_per_hectare`
  and the like. Those methods are the actors module's world, not the mod's declared reads. Fix: the actors module hands such code
  a world of declared views, the way a mod's commands get an access.
- `ModEffects` (`api.effects`, `api.write_store`, a mod store's handle) act through `FrameworkDoor`, which sends and reads without
  the mod's declaration (the effect checks its own arguments: a named edge, a cause, the mod's own store). The effects need no
  declaration by design; it is a door to narrow if mods should list them too.
- `api.adjust_view` still hands its function a `Needs` (attributes per view named in `reads`), not a `ModAccess`; `kernel` takes plain
  functions. They declare their reads at the call, so they are checked, but through a second mechanism.
- Command handlers are still called `(access, nodes, cmd, ended)`: `nodes` is the tech tree's node table the UI passes.

Found on the way and fixed: the workforce module sent `NoteSpend` (in `Labour.move_base`) without declaring it, so `move_base` and the
Towns mod's `go` raised `AssemblyError` in any built game; the spec now lists it. No test reached `move_base` in a built game
before `test_towns_mod_smoke`.

Check: `bash tools/done_check.sh` (mods importing `sim.engine` outside mod_code; mods importing `sim` beyond `sim.mod_api`).
