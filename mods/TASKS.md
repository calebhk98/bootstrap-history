# Mod system backlog

What a mod can do today is in `mods/README.md`. Evidence and the full
analysis for everything below is in
`Complaints/122-mod-system-cannot-change-rules-or-remove-content.md`.

The target: two authors who have never heard of each other can each ship a
mod, a player installs both, and they either work together or fail loudly
with a message naming both mods. And a mod can change the game's content and
rules as far as the design constraints allow (CLAUDE.md section 4), not only
add to it.

Ordered by value per cost.

## Bugs

1. **An override resets every field it does not mention.**
   `load_mod_tree` applies node defaults to the patch before merging it, so
   an override that sets one field wipes prerequisites, risk, traits and the
   rest back to defaults. Apply defaults to new nodes only.

2. **Two mods overriding the same base field is silent last-wins.** Load
   order is dependency, then mod id, so the result depends on alphabetical
   order and neither author is told. Either report the collision naming both
   mods, or require one to declare the other (`load_after` or a dependency).

3. **A malformed node crashes with a bare `KeyError`** instead of a
   `ModError` naming the mod and file.

## Missing capabilities

4. **Removal.** No content type can be deleted. Add `remove` for tech nodes,
   goals, trades and recipes, and fail if any remaining content still names a
   removed id.

5. **Changing base civilisations.** A mod cannot patch or hide a base
   civilisation (for example alter Rome, or make it unplayable); today the
   only route is copying the whole file under a new id. Add an override patch
   and a hidden/unplayable flag.

6. **Overrides for goals and trades**, matching what nodes and recipes have.

7. **World content from mods:** geography, deposits and resources, hazards
   and events, UI and currency strings, strategies. Each is read from base
   paths only.

8. **Manifest hardening:** a minimum game version, compared versions for
   dependencies, rejection of unknown keys, and a check that a mod using
   another mod's ids declares it as a dependency.

## Larger work

9. **New kinds of actor and new mechanics** (elves, dragons, magic). By the
   design constraints these cannot be special cases: a new species is an
   actor with calorie needs, growth and diet running through the normal
   production and labour rules, and magic is most naturally an energy or
   material source with recipes. Both depend on the general-actor work the
   project needs anyway for multiplayer and draft animals.

10. **Runnable mod code.** Not supported, and expensive to trust: Python run
    in-process has the player's full permissions. Prefer extending the
    declarative data contract. If code hooks are ever added they need a
    process or WASM boundary, an allowlisted API, per-mod consent, and a
    deterministic random source handed in so saves and fingerprints stay
    reproducible.

## Not required

- **Save-format work.** CLAUDE.md: no save migration, ever.
- **Engine rewrites for new content.** The engine reads data and never
  special-cases content ids.
