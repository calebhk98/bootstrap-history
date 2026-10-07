# Map data attribution and provenance

The dataset behind each generated map layer. The registry is `tools/map_data_sources.py`; a layer's dataset is one option there, chosen with `--source layer=option` on `tools/generate_geography_tiles.py`. Layers other than the first three are written by `python3 -m sim.geography.layer_build`. A test checks this registry covers every layer file and tile-grid field.

Terms are recorded as provenance (read from each provider on the audit date, see `Complaints/reports/map-data-licence-audit.md`); the project owner decided licences do not block use here.

| Layer | Source option | Dataset | Provider | Citation | Terms as recorded |
|---|---|---|---|---|---|
| land_mask | natural_earth_50m_land | Natural Earth 1:50m land | Natural Earth | Natural Earth, naturalearthdata.com | public domain |
| country_majority | natural_earth_50m_admin0 | Natural Earth 1:50m admin-0 countries | Natural Earth | Natural Earth, naturalearthdata.com | public domain |
| koppen_class | kgcpy_rubel_2016 | Koppen-Geiger present-day map (Rubel et al. 2016, 100 arc-second) bundled in the kgcpy package | Rubel and colleagues, Vienna (maps); kgcpy package | Rubel, Brugger, Haslinger and Auer 2016; Kottek et al. 2006 | no data terms stated on the data site; package code BSD |
| mean_temperature_c | worldclim_2_1 | WorldClim 2.1 bio1 | WorldClim | Fick and Hijmans 2017, Int. J. Climatol. 37:4302 | non-commercial use; redistribution needs permission |
| annual_precipitation_mm | worldclim_2_1 | WorldClim 2.1 bio12 | WorldClim | Fick and Hijmans 2017, Int. J. Climatol. 37:4302 | non-commercial use; redistribution needs permission |
| coldest_month_temperature_c | worldclim_2_1 | WorldClim 2.1 monthly tavg | WorldClim | Fick and Hijmans 2017, Int. J. Climatol. 37:4302 | non-commercial use; redistribution needs permission |
| warmest_month_temperature_c | worldclim_2_1 | WorldClim 2.1 monthly tavg | WorldClim | Fick and Hijmans 2017, Int. J. Climatol. 37:4302 | non-commercial use; redistribution needs permission |
| elevation_mean_m | worldclim_2_1 | WorldClim 2.1 elevation (SRTM-derived) | WorldClim | Fick and Hijmans 2017, Int. J. Climatol. 37:4302 | non-commercial use; redistribution needs permission |
| elevation_std_m | worldclim_2_1 | WorldClim 2.1 elevation (SRTM-derived) | WorldClim | Fick and Hijmans 2017, Int. J. Climatol. 37:4302 | non-commercial use; redistribution needs permission |
| ruggedness_index | worldclim_2_1 | WorldClim 2.1 elevation (SRTM-derived) | WorldClim | Fick and Hijmans 2017, Int. J. Climatol. 37:4302 | non-commercial use; redistribution needs permission |
| forest_fraction | esa_worldcover_2020 | ESA WorldCover 2020 tree-cover fraction, 30 arc-second, UC Davis geodata mirror | ESA WorldCover consortium | Zanaga et al. 2021; (c) ESA WorldCover project 2020 / Contains modified Copernicus Sentinel data (2020) processed by ESA WorldCover consortium | CC BY 4.0 |
| ocean_productivity_gc_m2_yr | oregon_state_vgpm_modis_2022 | Oregon State VGPM ocean net primary productivity, MODIS r2022 monthly, 2022 | Oregon State University | Behrenfeld and Falkowski 1997 | no terms found |
| coast_km | natural_earth_10m_coastline | Natural Earth 1:10m coastline | Natural Earth | Natural Earth, naturalearthdata.com | public domain |
| river_km_all | natural_earth_10m_rivers | Natural Earth 1:10m rivers_lake_centerlines | Natural Earth | Natural Earth, naturalearthdata.com | public domain |
| river_km_navigable | natural_earth_10m_rivers | Natural Earth 1:10m rivers_lake_centerlines | Natural Earth | Natural Earth, naturalearthdata.com | public domain |
| lake_area_km2 | natural_earth_10m_lakes | Natural Earth 1:10m lakes | Natural Earth | Natural Earth, naturalearthdata.com | public domain |
| shelf_area_km2 | natural_earth_10m_bathymetry | Natural Earth 1:10m bathymetry L_0 and K_200 | Natural Earth | Natural Earth, naturalearthdata.com | public domain |
| is_port | natural_earth_10m_ocean | Natural Earth 1:10m ocean | Natural Earth | Natural Earth, naturalearthdata.com | public domain |

Notes:
- `koppen_class` (and the arable and fertility figures read from it) come from the Rubel et al. 2016 maps bundled in the `kgcpy` package, not from Beck et al. 2018.
- Made with Natural Earth.
- Hand-authored catalogues (deposits, resources, parameters, route modes, regions, climate class fallbacks) carry their own `source` fields and redistribute no external raster or vector dataset.
