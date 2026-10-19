# Urbanisation Drivers (bh_urbanisation_w2n6)

Complaints/closed/107 asks for towns that grow from jobs, food reach and mortality, with housing, disease and
water costs and no fixed city maximum. This mod derives that view on the land tiles (not the 21 hand-drawn
regions) from state the engine already holds. It changes nothing in a game unless the player opts in.

## Turning it on

* The command: `python3 sim/simulator.py mod-allow bh_urbanisation_w2n6` (consent for `hooks.py`), then in any
  game `{"cmd":"bh_urbanisation_w2n6:towns"}` (optional `"days"`, the haul that counts as food reach).
* The civilisation: `--civ bh_urbanisation_w2n6:rome_tenements`, Rome 100 AD plus a tenement quarter, an actor
  kind (`bh_urbanisation_w2n6:tenement_dwellers`, data only, no consent needed) that buys food, shelter and water
  at the going prices through the existing need catalogue and dies faster when food or water go unmet.
  The civilisation file is a copy of `rome_100ad.json` with one added cast actor; keep it in step by hand.

## What the `towns` command derives, per held tile

* Food reach: the farm surplus of each tile (food potential minus what its people eat) within a haul of the
  town over the routes the nation's technologies open, shared among the towns that reach it. This is the town's
  ceiling (`food_ceiling_people`).
* Jobs: people in non-farm households (the civilisation's start-date urban share kept in step with the
  population, plus the households of the founder's and firms' non-farm staff) placed on tiles in proportion to the
  food each can assemble (`jobs_pull_people`). The town is the smaller of the two, and `bound_by` says which.
* Water: demand at the WHO basic-access level read from `data/world/needs.json`.
* Housing: wall and roof volume from the tile's climate (`sim/world/climate_needs.py`).
* Disease: an urban mortality premium that rises with crowding and falls to zero as the water and sanitation
  technologies in the engine's disease burden are held; `excess_deaths_per_year` is the premium times the
  baseline adult death rate.

The command only reads the engine and records one number in the mod's own saved state; it changes who lives
where and who dies in no way. To make the tile towns count, see `Complaints/562`.

## Labelled heuristics (CLAUDE.md 4.4)

* `DEFAULT_FOOD_HAUL_DAYS`: replace with the haul at which grain freight eats its value.
* `CROWDING_HALF_POPULATION` and `URBAN_DISEASE_PREMIUM_AT_FULL_CROWDING`: replace with housing density and
  contact rates feeding the demography module's disease burden.
* The tenement kind's headcount, birth, death and famine rates, and its work share: the mod author's own,
  replaced once towns are derived and move households.
* Non-farm households start from the civilisation's `urban_fraction` (a start-date initial condition); only
  growth in hired staff moves it, so towns do not yet grow from industry beyond the founder's and firms' payroll.

## Known limits

* A tile's "town" is all its urban people, many real towns at the map's tile size, so premiums sit near their
  ceiling; a finer settlement grain is needed.
* Nothing shifts households between tiles; the engine's own town estimate (`map` screen, labour market) is
  unchanged.
* With `bh_towns_m8d4` (named towns, not on main) the two would combine by naming the towns this command
  places, and its town table could replace the nominal sizes this command distributes.
