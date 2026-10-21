# The deferred-feature mods predate mod phases, stores and effects

**Status:** open

**What is wrong.** The six mods built for the "Deferred to mods" list in `mods/TASKS.md` (`bh_orghierarchy_r4k8`,
`bh_urbanisation_w2n6`, `bh_pollution_t9c3`, `bh_religion_h5p1`, `bh_towns_m8d4`, `bh_cashshelter_z6f2`) were written
against the mod API before main added `api.phase` (a step in the year, `sim/engine/year_phases.py`, Complaint 494),
`api.store` (saved values per tile, actor or actor pair, `sim/engine/mod_stores.py`, 495) and `api.effects` (`pay`,
`kill_people`, `move_people`, `transfer_tile`, `write_store`, `record_event` and others, `sim/engine/mod_effects.py`, 496).
They use none of them (check: `grep -ln "api.phase\|api.store\|api.effects" mods/bh_*/*.py`), so some of what complaints
633 to 636 say a mod cannot do may now be possible without the engine branches those complaints name. Complaints 637
(place names) and 638 (confiscation of claims) were done in the engine and are closed.

Read from the signatures only; none of this has been tried:

- 633 (`bh_orghierarchy_r4k8`): a phase can run `staff_managers` every year instead of only on command. Charging the
  overhead against directed hours has no effect in `api.effects`, so the hook of 633 is still needed.
- 634 (`bh_urbanisation_w2n6`): `move_people` and `kill_people` may carry migration and urban mortality. `kill_people`
  takes a country and a share, not a tile, so a per-town premium may fall short. The mod still has to register its town
  derivation through `api.town_provider`.
- 635 (`bh_pollution_t9c3`): the externality hook is in main and the mod registers it; deaths by band and a yield factor
  per tile do not need effects.
- 636 (`bh_religion_h5p1`): `transfer_tile` hands a whole tile, which is not land holding (see 636: land holding is the
  titles of 538). Lending is not covered by any effect.
- 638 (`bh_cashshelter_z6f2`): done through `register_wealth_claims` in the engine; the mod already registers claims.

**Why it matters.** The mods get yearly behaviour (staffing, deaths, migration) that today waits for the player to type a
command, and an engine change that the shipped API already makes unnecessary is wasted review.

**What it would take.** Per mod, try the new API; move what works into the mod; narrow or close 633 to 636 for what it
covers. Prove each against a seeded game with the mod allowed, and that the shipped game is unchanged without consent (the
check in PR #52: `agent --civ X --kit merchant --seed 7 --deterministic` output compared with and without the mods).
