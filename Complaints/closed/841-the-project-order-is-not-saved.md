# The project order is not saved, so a load forgets every priority the player set

**Status:** closed. The projects module owns the order in its saved world state (`ProjectsWorld.order`), opened from the tree's order
at game start and changed only by `PutProjectFirst`, `ReorderProjects` and `RestoreProjectOrder`. Regression tests:
`sim/tests/test_project_order.py` (rules, commands, serialisation) and `sim/tests/test_project_order_save_smoke.py` (a whole
game keeps a moved project first across save and load).

The order in which the household's hours go to its projects (`Sim.order`, built from the tree's order when the game is
made) is changed by play: starting a project puts it first (`sim/projects/starting.py`), `priority` moves projects
(`sim/ui/proto/dispatch_priority.py`), and the ventures screen restores it after a trial
(`sim/ui/proto/dispatch_ventures.py`). It is an attribute of `Sim`, not part of the saved state, so a save and a load
put it back to the tree's order. With `--session`, where every command is a save then a load, a priority the player sets
does not survive to the next command.

Reproduced at the base (`0be2f72`): move the last project to the front, `save_state`, `load_state` into a fresh game: the
front project is the tree's again.

Found while giving the order an owner (phase 6b of the module migration: a module wrote the engine's list through a
view). The fix rides with that move: the projects module owns the order in its saved state and changes it only through
its commands; the regression test is a save and load that keeps a moved project first.
