# The deferred-feature mods predate mod phases, stores and effects

**Status:** open

The six mods built for the "Deferred to mods" list in `mods/TASKS.md` (`bh_orghierarchy_r4k8`, `bh_urbanisation_w2n6`,
`bh_pollution_t9c3`, `bh_religion_h5p1`, `bh_towns_m8d4`, `bh_cashshelter_z6f2`) were written against the mod API as it
stood before main added `api.phase` (a step in the year, `sim/engine/year_phases.py`, Complaint 494), `api.store`
(saved values per tile, actor or actor pair, `sim/engine/mod_stores.py`, 495) and `api.effects` (`pay`, `kill_people`,
`move_people`, `transfer_tile`, `write_store`, `record_event` and others, `sim/engine/mod_effects.py`, 496). They use
none of them, so some of what complaints 633 to 637 say a mod cannot do may now be possible without the engine
branches those complaints name.

Read from the signatures only; none of this has been tried:

- 633 (`bh_orghierarchy_r4k8`): a `seat` phase could run `staff_managers` every year instead of only on command. The
  overhead binding on directed hours has no effect in `api.effects`, so `engine-director-overhead-hook` still looks needed.
- 634 (`bh_urbanisation_w2n6`): `move_people` and `kill_people` may carry the migration and urban mortality the
  complaint lists as having no hook. `kill_people` takes a country and a share, not a tile, so a per-town premium may
  still fall short. The labour market's town size still needs `engine-town-population-provider`.
- 635 (`bh_pollution_t9c3`): a `world` phase plus `kill_people` could apply pollution deaths, by country rather than by
  tile or age band. Land yield has no effect, so `engine-externality-hook` still looks needed for that half.
- 636 (`bh_religion_h5p1`): `transfer_tile` hands a whole tile to an actor, which is coarser than buying hectares;
  whether it can stand in for land holding is a design question. Lending is not covered.
- 637 (`bh_towns_m8d4`): a tile store of town names may show on `map` as a layer with no engine change. Rows of
  `move` would still not name towns.
- 638 (`bh_cashshelter_z6f2`): nothing in the new API counts claims on other actors in confiscation.

Why it matters: each engine branch is a change someone has to review and merge, and a branch that the shipped API
already makes unnecessary is wasted review. The mods also get yearly behaviour (staffing, deaths, migration) that
today waits for the player to type a command.

What it would take: per mod, try the new API; move what works into the mod; then narrow or close 633 to 637 and
drop or trim the matching `engine-*` branch. Prove each against a seeded game with the mod allowed, and that the
shipped game is unchanged without consent (the check in PR #52: `agent --civ X --kit merchant --seed 7
--deterministic` output compared with and without the mods).
