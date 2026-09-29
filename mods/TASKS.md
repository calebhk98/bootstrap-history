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

## Missing capabilities

1. **World content from mods:** geography, deposits and resources, hazards
   and events, UI and currency strings, strategies. Each is read from base
   paths only.

2. **Manifest hardening:** a minimum game version, compared versions for
   dependencies, rejection of unknown keys, and a check that a mod using
   another mod's ids declares it as a dependency.

3. **Namespaces that cannot overlap.** A content id only has to start with
   `<mod_id>_`, so a mod `steam` can create `steam_power_engine` inside
   another mod `steam_power`'s space. Use a separator a mod id cannot contain
   (for example `steam:engine`), or forbid a mod id that is a prefix of
   another installed mod's id.

4. **Mod ids that are unique without coordination.** Two authors who never
   talk can pick the same id, and then their mods cannot be installed
   together. Recommend an author prefix plus a short random suffix in the
   id (for example `ana_steamage_k3f9`), check the format at load, and
   document it in `mods/README.md`.

5. **Commands and automatic policies.** A mod cannot add, change or remove a
   player command or an automatic policy (auto-mine, auto-forest, shedding);
   both are Python. A declarative form for policies (a condition on state
   and an action from the existing command set) would cover most needs
   without running mod code.

## Larger work

6. **New kinds of actor and new mechanics** (elves, dragons, magic). By the
   design constraints these cannot be special cases: a new species is an
   actor with calorie needs, growth and diet running through the normal
   production and labour rules, and magic is most naturally an energy or
   material source with recipes. Both depend on the general-actor work the
   project needs anyway for multiplayer and draft animals.

7. **Runnable mod code.** Not supported, and expensive to trust: Python run
   in-process has the player's full permissions. Prefer extending the
   declarative data contract. If code hooks are ever added they need a
   process or WASM boundary, an allowlisted API, per-mod consent, and a
   deterministic random source handed in so saves and fingerprints stay
   reproducible.

## Not required

- **Save-format work.** CLAUDE.md: no save migration, ever.
- **Engine rewrites for new content.** The engine reads data and never
  special-cases content ids.
