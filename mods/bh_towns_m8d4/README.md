# Town Table (bh_towns_m8d4)

Names towns. The base map's tiles are anonymous 150 thousand square kilometre cells (`China 10`); this mod adds a
catalogue of named towns, each placed on a real tile, with a cited size at the start date of each shipped
civilisation. It answers Complaints/289 (closed, deferred to mods).

## What it adds

- `data/world/geography/towns/<civilisation>.json`: a `towns` catalogue of the mod's map overlay, loaded the way the
  deposits catalogue is. Each entry has `name`, `also_called`, `tile`, `lat`, `lon` and `sizes`, a list of dated
  snapshots `{year, people, low, high, source, conf}`. `conf` uses the map's letters (A checked, B coordinate checked
  and size approximate, C from memory of a secondary compilation, D weak). The tile is the equal-area grid cell that
  contains the coordinates (the cell rule of `tools/generate_geography_tiles.py`), so a tile can hold several towns.
- Coverage: Rome 100 AD, Han China 100 AD, Mexica 1500, England 1300 and Norse 900 AD. Every town's tile is held by
  its civilisation, except Hedeby (Danish; not in the Norse tiles, listed for the map only).
- Two commands (mod code, `hooks.py`):
  - `bh_towns_m8d4:towns` lists the towns on your tiles with size, range, source, confidence and days from your
    base. `bh_towns_m8d4:towns <name or tile>` finds a town by part of its name (or an alternative name) or lists a
    tile's towns, including towns outside your nation.
  - `bh_towns_m8d4:go <town>` resolves the name to its tile and runs the ordinary `move_base`; costs and refusals
    are the shipped ones.

## Turning it on

The data loads with the mod and changes nothing: no shipped command reads the catalogue. The commands are code, so
run `python3 sim/simulator.py mod-allow bh_towns_m8d4` once, then in a game use
`{"cmd":"bh_towns_m8d4:towns"}` and `{"cmd":"bh_towns_m8d4:go","text":"Luoyang"}`.

## What it models and does not

Sizes are start-date initial conditions (CLAUDE.md 4.1 allows them); nothing reads them as a model input. They are
entered from memory of Chandler (1987), Modelski (2003), Bairoch (1988), Smith (2012) and similar compilations,
marked C or D, and each carries the literature's range; check them against the books before relying on one. Where
the ranges differ by a factor of two or more (Rome, Tenochtitlan, Luoyang) both ends are shown.

The simulation's own estimate of the town you work in (shown by `move`) is unrelated and much smaller than a cited
capital's size; the gap is a finding about the settlement model, not an error here.

## Limits

- Shipped `map` and `move` cannot name towns; a mod may only change their help text. Naming towns inside those
  screens needs an engine hook (a map-catalogue hook for the tile name and place rows); see Complaints/637.
- A town exists from its earliest snapshot on; the command uses the latest snapshot at or before the game year and
  shows `size_year` and `years_old`. Figures older than `STALE_AFTER_YEARS` in `hooks.py` carry `stale: true`
  (a labelled heuristic, retired by adding later snapshots to `sizes`). London and Londinium are one entry whose
  snapshots carry their own names. `python3 mods/bh_towns_m8d4/check.py` checks the table without a game.
- Tile granularity: Tenochtitlan, Texcoco, Cholula, Tlaxcala and Zempoala share one tile, so `go` moves to the tile.
- No labelled heuristics: no number here is derived or tuned.
