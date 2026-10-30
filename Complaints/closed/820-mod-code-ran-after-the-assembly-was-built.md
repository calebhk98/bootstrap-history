# Mod code ran after the assembly was built, so a mod's modules, replacements and layers missed the first game

**Status:** closed - the game's assembly now runs and applies its mods' code (`game_assembly.build`), covered by `sim/tests/test_mod_set_per_game_smoke.py`

`Sim.__init__` built the assembly with `game_assembly.build(MODS_DIR, ...)`, which applied the operations of mod code that had
already run (`mod_code.MOD_OPERATIONS`). Nothing ran mod code before that: the first call was `register_mod_actor_kinds()`, reached from
the actors module's first `cast()`, after the assembly existed. So `api.add_module`, `replace_module`, `remove_module`, `extend_module`,
`adjust_view`, `provide` and `withdraw` of a consented mod took effect only in a game built after something else had run the code
(the protocol's mod loader did, the command line did not), and the mods' process-global registrations (`register_*`) took effect in
every game of the process whatever its mod set.

Found while making the registries per-assembly (`docs/architecture/MODULE_REGISTRY_PLAN.md` section 4.6). Fixed by the same change:
`build` runs each allowed mod's `register(api)` once per process, keeps the `Operations` per (mods directory, mod id), and applies the
ones of its own mods directory; a bad year-phase constraint is an error of building the game. No shipped mod ships consent, so the
baseline games do not change.
