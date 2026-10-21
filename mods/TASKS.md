# Mod system backlog

What a mod can do today is in `mods/README.md`. Evidence and the full
analysis for everything below is in
`Complaints/closed/118-mod-system-cannot-change-rules-or-remove-content.md`;
the design the later items followed is `docs/architecture/MOD_HOOKS_PLAN.md`.

The target: two authors who have never heard of each other can each ship a
mod, a player installs both, and they either work together or fail loudly
with a message naming both mods. And a mod can change the game's content and
rules as far as the design constraints allow (CLAUDE.md section 4), not only
add to it.

## Done

1. **World content from mods:** map overlays (geography, deposits, resources,
   routes), needs, display units, foreign economies, starting kits,
   win-condition sentences, strategies, civilisation hazards and cast through
   list edits, declared numbers (`data/constants.json`) and technology effects.
2. **Manifest hardening:** required keys, extra keys kept as the author's own
   metadata (owner decision), `min_game_version` against `GAME_VERSION`
   (`sim/game_version.py`, `simulator.py --version`), dependency version ranges
   compared as semantic versions.
3. **Commands and automatic policies:** declarative `read`, `macro` and `policy`
   entries in `data/ui/commands.json`, plus default switches in
   `data/ui/policies.json`.
4. **New kinds of actor:** a declared species (`data/world/actor_kinds.json`)
   running through the needs catalogue, the labour market and the ledger, and
   code-registered kinds.
5. **Runnable mod code:** owner decision 2026-10-09, built as consented and
   hashed Python (`mod-allow`, `mods/consent.json`) with the safety boundary
   stated in the README: it is not a sandbox.

## Open

- **A process or WASM boundary for mod code.** Consent is the only protection
  today; an allowlisted message interface would let a player run an author they
  do not trust. Not started; the declarative contract covers most needs.
- **Swappable implementations of engine computations** (speed mods, for example numpy): `Complaints/661`.
- **Hazard effects beyond the shipped fields.** A hazard is made of the effect
  fields the engine reads; a new effect needs an actor kind or mod code.

## Not required

- **Save-format work.** CLAUDE.md: no save migration, ever.
- **Engine rewrites for new content.** The engine reads data and never
  special-cases content ids.

## Deferred to mods (owner decisions)

Features the owner decided should be mods. Each closed complaint keeps the design notes. Each is built as an opt-in mod
(its `README.md` says how to turn it on) on the hooks of `mods/README.md`; what remains is listed per mod.

- Organisational hierarchy for directed hours at scale (span of control, overhead, technologies that widen it). (`Complaints/closed/104-directed-hours-need-organisational-hierarchy.md`) Mod `bh_orghierarchy_r4k8`; the overhead binds on directed hours through `api.director_overhead` (`Complaints/closed/633`). Hiring managers stays a command.
- Urbanisation as a system: towns grow from jobs, food reach and mortality, with housing, disease and water costs. (`Complaints/closed/107-urbanisation-should-become-first-class.md`) Mod `bh_urbanisation_w2n6`; a yearly phase stores the derived towns and the town provider hands them, and the urban mortality premium, to the labour market and `Population.step` (`Complaints/closed/634`). Households move by the engine's one migration rule; a jobs-driven pull would change that rule.
- Industrial pollution and externalities derived from physical throughput (smoke, runoff, occupational disease, cleanup technology). (`Complaints/closed/108-add-industrial-pollution-and-externalities.md`) Mod `bh_pollution_t9c3`; deaths and yield factors reach mortality, the harvest producers work and the pooled harvest the people eat (`Complaints/closed/635`).
- Religious institutions as an actor kind holding land, mills and credit, with data per civilisation. (`Complaints/closed/269-religious-institutions-absent-as-economic-actors.md`) Mod `bh_religion_h5p1`; the house's purse is lent through `lends_from_purse` and its civilisations are `variant_of` patches (`Complaints/closed/636`). Land holding waits for `Complaints/538`.
- A town table (name, tile, size at the start date with a source) so `map` and `move` can name places. (`Complaints/closed/289-tiles-have-no-place-names-and-no-towns.md`) Mod `bh_towns_m8d4`; names on the shipped `map` and `move`: `Complaints/637`, branch `engine-map-place-names`.
- Religion as a household need (rites, offerings, priests and diviners): owner decision 2026-10-20, out of the base game; temples' own consumption can build on `bh_religion_h5p1`. (`Complaints/530`)
- Sheltering cash from disasters and confiscation (deposits elsewhere, letters of credit); the display part is done. (`Complaints/closed/165-disasters-take-cash.md`) Mod `bh_cashshelter_z6f2`; confiscation counting lodged coin: `Complaints/638`, branch `engine-confiscation-counts-claims`.

A mod civilisation that varies a shipped one names it with `variant_of` and holds only what differs, so it follows its base.
