# Mod system backlog

What a mod can do today is in `mods/README.md`. Evidence and the full
analysis for everything below is in
`Complaints/118-mod-system-cannot-change-rules-or-remove-content.md`.

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
   dependencies, and rejection of unknown keys.

3. **Commands and automatic policies.** A mod cannot add, change or remove a
   player command or an automatic policy (auto-mine, auto-forest, shedding);
   both are Python. A declarative form for policies (a condition on state
   and an action from the existing command set) would cover most needs
   without running mod code.

## Larger work

4. **New kinds of actor and new mechanics** (elves, dragons, magic). By the
   design constraints these cannot be special cases: a new species is an
   actor with calorie needs, growth and diet running through the normal
   production and labour rules, and magic is most naturally an energy or
   material source with recipes. Both depend on the general-actor work the
   project needs anyway for multiplayer and draft animals.

5. **Runnable mod code.** Not supported, and expensive to trust: Python run
   in-process has the player's full permissions. Prefer extending the
   declarative data contract. If code hooks are ever added they need a
   process or WASM boundary, an allowlisted API, per-mod consent, and a
   deterministic random source handed in so saves and fingerprints stay
   reproducible.

## Not required

- **Save-format work.** CLAUDE.md: no save migration, ever.
- **Engine rewrites for new content.** The engine reads data and never
  special-cases content ids.
