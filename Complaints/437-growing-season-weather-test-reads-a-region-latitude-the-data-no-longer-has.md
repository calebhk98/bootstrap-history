# The growing-season weather test reads a region latitude the data no longer has

**Status:** open

`python3 -m sim.tests --only growing_season_weather_correlation --slow` errors in "two nearby cells correlate
far more than two distant ones": `KeyError: 'lat'`. The test builds
`Sim._WeatherCell(cell_id="gaul", lat=gaul["lat"], ...)` from a region record that no longer carries
`lat`/`lon`. It fails the same way on main (`bcd8b65`). It is a slow topic, so it runs only with `--slow`.

What it would take: take the cell's position from wherever region coordinates live now (the tile map, or a
region anchor point), or build the two test cells from stated coordinates.
