# Mods have no stable way to change the world: a handler edits engine internals directly

**Status:** closed - effect operations on `api.effects`; world hazards use them

A mod command handler receives the whole `sim` (`mods/README.md`, "Mod code"). Reads have a supported
surface (state paths and `@readable` methods), but writes do not: a mod that moves people, transfers a
tile, destroys goods or records an event must reach into `Sim` attributes and package internals, which
change with every refactor and bypass the walls in `docs/architecture/PACKAGE_WALLS.md`.

Why it matters: a mod written against internals breaks on the next merge, and the money and goods
conservation checks (`sim/agents/edges.py`, `sim/engine/invariants.py`) cannot see a write that skips the
ledgers.

What it would take: a small set of effect operations that go through the normal rules: pay or move money
through the ledger with a named edge, add or remove goods at a tile, kill, move or reassign people,
transfer a tile (Complaint 483), set a declared store value (495), and write a world event with a cause
(Complaint 493). Mod code and data hazards would use the same operations, and the base game's new
systems should use them too, so they stay as moddable as a mod.

## Resolution

`sim/engine/mod_effects.py` adds `ModEffects` (reached as `api.effects`): coin through the ledger against a named
edge, goods in and out of the economy's book against a named edge, killing and moving people, tile transfer with a
cause, store writes by the declaring mod only, and world events. Money or goods without a known edge, and any change
without a cause, are refused. `world_hazards` now kills people and writes its events through the same operations
(`BASE_EFFECTS`). Tests: `sim/tests/test_mod_effects.py`. Documented in `mods/README.md`, "Changing the world".
