# Committed map layers come from non-commercial or unlicensed datasets

**Status:** closed - owner decided licences do not matter; each layer's dataset is one option in `sim/geography/map_data_sources.py` naming its loader, files and source text, read by both `tools/generate_geography_tiles.py` and `sim.geography.layer_build` (`--source layer=option` on either), Koppen provenance corrected to Rubel et al. via kgcpy, and `data/world/geography/ATTRIBUTION.md` lists each layer's current source. Committed data unchanged; full regeneration not run (needs network and geodata packages)

Several committed files under `data/world/geography/` are derived from datasets whose terms forbid commercial use or redistribution, or state no terms at all. The file-by-file provenance, each provider's licence page and the open replacements are in `Complaints/reports/map-data-licence-audit.md` (not legal advice).

- WorldClim 2.1 (non-commercial; redistribution needs permission): the temperature, precipitation, elevation, elevation spread and ruggedness layers in `data/world/geography/layers/`.
- Oregon State VGPM ocean productivity (no terms found): `layers/ocean_productivity_gc_m2_yr.json`.
- The Koppen class in `tile_grid.json`, and the arable and fertility figures read from it, come from the Rubel et al. maps bundled in the `kgcpy` package (no data terms found), not from Beck 2018 as the tool and docs say.
- `forest_fraction` (ESA WorldCover, CC BY 4.0) is allowed but needs its full attribution line.

What it would take: rebuild the climate layers from CHELSA (CC BY 4.0) or ERA5, elevation from GMTED2010, SRTM or Copernicus DEM, and Koppen from Beck 2023 (CC BY 4.0) with the generator in `tools/`; get written terms for VGPM or replace it; add an attribution file. Rebuilding moves every tile's climate, so food, farming and weather results change.

Related: 411 (food potential reads these layers), 136.
