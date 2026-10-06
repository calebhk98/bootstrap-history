# Map data licence audit

This is a research note, not legal advice. Licence statements below were read from each provider's own pages on the audit date and are summarised, not interpreted. Anything that matters commercially should be confirmed with the provider or a lawyer.

Scope: every committed file under `data/world/geography/`, plus a grep of `data/`, `docs/`, `tools/` and `sim/` for external geodata names. No other `data/` file derives from external geodata (the only other hits are unrelated uses of the words "natural earth" for pigment, USGS cited as a figure in deposit notes, and Koppen as a label).

## 1. File-by-file provenance

Build tools: `sim/geography/layer_build/` (module `python3 -m sim.geography.layer_build`; source names in `catalog.py`, download URLs in `layers_raster.py`, `layers_ocean.py`, `layers_vector.py`) and `tools/generate_geography_tiles.py`.

Transformation common to all measured layers: the source raster or vector is reduced to one number per roughly 150,000 km2 equal-area tile (EPSG:6933 grid, clipped to Natural Earth 1:50m land, cos(latitude) weighted pixel means). Values are heavily aggregated (one number per tile, 1139 tiles).

| File | Source dataset(s) | Tool and transformation | Provenance recorded in file? |
|---|---|---|---|
| layers/mean_temperature_c.json | WorldClim 2.1, bio1, 10 arc-minute | layer_build, tile land mean | yes (`source`) |
| layers/annual_precipitation_mm.json | WorldClim 2.1, bio12 | layer_build, tile land mean | yes |
| layers/coldest_month_temperature_c.json | WorldClim 2.1 monthly tavg | per pixel min of 12 months, then tile mean | yes |
| layers/warmest_month_temperature_c.json | WorldClim 2.1 monthly tavg | per pixel max of 12 months, then tile mean | yes |
| layers/elevation_mean_m.json | WorldClim 2.1 elevation (SRTM-derived) | tile land mean | yes |
| layers/elevation_std_m.json | WorldClim 2.1 elevation (SRTM-derived) | weighted standard deviation per tile | yes |
| layers/ruggedness_index.json | WorldClim 2.1 elevation (SRTM-derived) | mean absolute neighbour difference per pixel, tile mean | yes |
| layers/forest_fraction.json | ESA WorldCover 2020 tree cover, 30 arc-second, fetched from the geodata.ucdavis.edu mirror (Zanaga et al. 2021) | averaged to about 5 arc-minutes, tile land mean | yes |
| layers/ocean_productivity_gc_m2_yr.json | Oregon State VGPM (Behrenfeld and Falkowski 1997), MODIS r2022 monthly, 2022 | 11 published months averaged (April absent upstream), scaled to a year, mean over shelf-zone sea pixels | yes |
| layers/coast_km.json | Natural Earth 1:10m coastline | line length clipped to tile | yes |
| layers/river_km_all.json | Natural Earth 1:10m rivers_lake_centerlines | line length clipped to tile | yes |
| layers/river_km_navigable.json | Natural Earth 1:10m rivers_lake_centerlines (scalerank <= 6) | line length clipped to tile | yes |
| layers/lake_area_km2.json | Natural Earth 1:10m lakes | polygon area clipped to tile | yes |
| layers/shelf_area_km2.json | Natural Earth 1:10m bathymetry_L_0 and K_200 | ocean zone area minus deeper than 200 m | yes |
| layers/is_port.json | Natural Earth 1:10m ocean polygon | rasterised on 0.1 degree grid, port flag | yes |
| tile_grid.json | Natural Earth 1:50m land and admin-0 countries (geometry, country majority); Koppen-Geiger class sampled via the `kgcpy` PyPI package | grid, clip, 25x25 sample points per tile classified; class mix mapped to arable fraction and fertility by a hand-set table | yes (`generation_rule_summary`, per-tile `source`) |
| climate_classes/koppen_food_fallbacks.json | Koppen class labels with class-typical climate numbers | authored by hand, "from memory" style fallback values; class names only, no raster | no external dataset recorded |
| climate_groups/koppen.json | Koppen class letters | hand-authored words | not external data |
| derived_layers/climate.json, derived_layers/food.json | none (rules over other layers; De Martonne 1926 formula cited) | rule definitions | n/a |
| sea_links/links.json | Natural Earth ocean raster | water routes between port tiles, built by `layer_build/sea_links.py` | partial (`_doc` says "ocean raster"; Natural Earth inferred from `is_port` and the tool) |
| deposits/*.json, located_materials/, resources/*.json, parameters/*.json, sea_lanes/, route_modes/, reach_levels/, regions/, map.json, geography_notes.json | authored content; deposit coordinates "from Wikipedia", reserve figures "from memory" citing USGS; food coefficients cite Lieth 1975 and others | hand-authored | cited in `source` fields; no raster or vector dataset redistributed |

Notes on mismatches in the record:
- `tools/generate_geography_tiles.py` and `docs/architecture/MAP_AND_WEATHER.md` describe the Koppen source as Beck et al. 2018. The `kgcpy` package metadata (PyPI) says it bundles the Rubel et al. 2016 100 arc-second maps, so the real source of `koppen_class` is Rubel and colleagues, not Beck. This should be corrected in the docstring.
- `forest_fraction` is labelled "ESA WorldCover 2020 ... via geodata" in the file; the upstream product is ESA's, the mirror is UC Davis.
- GAEZ: no committed file references it (grep found no hit). The fact-check's GAEZ concern does not apply to the files in this branch.

## 2. Per-source licence table

| Source | Licence | Redistribution of derived data | Attribution | Commercial use | Link |
|---|---|---|---|---|---|
| WorldClim 2.1 | Custom terms: "freely available for academic use and other non-commercial use" | "Redistribution or commercial use is not allowed without prior permission." Maps and figures for academic publication are allowed. The page does not say whether tile-aggregated derived values count as redistribution. | No explicit requirement; citing Fick and Hijmans 2017 is normal practice | Needs permission; contact info@worldclim.org | https://worldclim.org/about.html |
| Natural Earth | Public domain | Allowed, no permission needed | Not required; "Made with Natural Earth" suggested | Allowed | https://www.naturalearthdata.com/about/terms-of-use/ |
| ESA WorldCover 2020 | CC BY 4.0 | Allowed with attribution | Required: "(c) ESA WorldCover project 2020 / Contains modified Copernicus Sentinel data (2020) processed by ESA WorldCover consortium"; cite Zanaga et al. 2021 | Allowed | https://esa-worldcover.org/en/data-access |
| Oregon State VGPM / ocean productivity | No licence or terms found on the site (the old URL redirects to orca.science.oregonstate.edu) | Unstated | Citation of Behrenfeld and Falkowski 1997 is customary; no stated requirement | Unstated | http://orca.science.oregonstate.edu/index.php |
| MODIS (VGPM input) | NASA data are generally open; not separately fetched here, so unverified in this audit | not verified | not verified | not verified | n/a |
| kgcpy package code | BSD (PyPI metadata) | Code licence only; it does not cover the bundled data | n/a | n/a | https://pypi.org/project/kgcpy/ |
| Koppen-Geiger maps bundled in kgcpy (Rubel et al. 2016, from koeppen-geiger.vu-wien.ac.at) | No licence or terms stated on the data site; only a citation request (Kottek et al. 2006) | Unstated | Citation requested | Unstated | http://koeppen-geiger.vu-wien.ac.at/present.htm |
| SRTM (upstream of WorldClim elevation) | US government work, public domain per USGS EROS page | Allowed | Citation expected | Allowed | https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1-arc |
| GAEZ | Not used by any committed file | n/a | n/a | n/a | n/a |

Whether heavily aggregated values are treated differently: only WorldClim's page speaks to derived products, and only for academic maps and figures. Nothing found says tile means are exempt. A cautious reading treats the six temperature, precipitation and elevation-family layers as derived from WorldClim data and therefore covered until the provider says otherwise.

## 3. Files that may need a replacement source or permission

Restricted (WorldClim, non-commercial and no redistribution without permission). Seven committed layers:
1. layers/mean_temperature_c.json
2. layers/annual_precipitation_mm.json
3. layers/coldest_month_temperature_c.json
4. layers/warmest_month_temperature_c.json
5. layers/elevation_mean_m.json
6. layers/elevation_std_m.json
7. layers/ruggedness_index.json

Also read at run time from these: derived_layers/climate.json (aridity index from precipitation and temperature) and the food model fallbacks that consume them. These carry no WorldClim values themselves.

Unlicensed or unstated terms:
- layers/ocean_productivity_gc_m2_yr.json (Oregon State VGPM; no terms found).
- tile_grid.json `koppen_class`, `koppen_sample_mix`, and the arable and fertility numbers derived from them (Rubel et al. maps via kgcpy; data site states no terms). The grid geometry itself is Natural Earth and is clean.

Clean: all Natural Earth layers (coast, rivers, lakes, shelf, is_port, sea_links geometry) and forest_fraction (CC BY 4.0, needs the attribution line, which the file does not yet carry in the full wording).

## 4. Recommended replacements

Climate (temperature, precipitation, coldest and warmest month):

| Option | Licence | Note |
|---|---|---|
| CHELSA V2.1 climatologies | CC BY 4.0 (CHELSA site) | Closest match: 1981-2010 means at 30 arc-seconds, same bioclim variables. First choice. |
| ERA5 / ERA5-Land (Copernicus) | CC BY 4.0 per the CDS dataset page | Reanalysis, coarser fit to station data; precipitation is weaker in mountains. Usable fallback. |
| CRU TS | Open Database Licence with attribution and share-alike (CRU data page) | Share-alike is a stronger condition than CC BY; check compatibility before use. |
| TerraClimate | No terms on its web page; licence unverified | Do not rely on it until the terms are confirmed with the lab. |

Elevation and ruggedness:

| Option | Licence | Note |
|---|---|---|
| SRTM (USGS) | Public domain | Direct source of the WorldClim elevation; ends at 60N and 56S. Would need a high-latitude fill. |
| GMTED2010 (USGS) | USGS product, generally public domain; not separately fetched here, confirm | Global coverage including high latitudes; 7.5 arc-second to 30 arc-second. Best single replacement. |
| Copernicus DEM GLO-90 / GLO-30 | Free, attribution required, commercial use and redistribution allowed (Copernicus Data Space page) | Needs the DLR and Airbus attribution wording in distributed derivatives. |

Koppen class: Beck et al. 2023 (gloh2o.org/koppen) is CC BY 4.0, commercial use allowed, attribution required. Replace the kgcpy raster with it, which also makes the docstring true. Alternatively compute classes from the CHELSA layers with the published Koppen rules.

Ocean productivity: ask the Oregon State group for written terms, or substitute a licensed product, for example Copernicus Marine or NASA Ocean Color VGPM or CbPM products after confirming their terms. Not verified here.

Also: write the ESA WorldCover attribution string into `forest_fraction.json` and into any credits file, and add a "Made with Natural Earth" credit.

## 5. Open points for the owner

- Ask info@worldclim.org whether tile-aggregated derived values may be committed and published. A written yes would avoid regenerating seven layers.
- Regenerating needs network access and the `layer_build` cache; the cell values will change, so the fingerprint and any tests that pin layer values will move. Not run in this audit.
- Licence pages can change; re-read them before acting.
