"""Data build pipeline: per-tile physical layers for the world map.

Rebuild with `python3 -m sim.geography.build`. The game never imports this
package; its dependencies (numpy, shapely, pyproj, rasterio, geopandas,
pyhdf) are imported only inside it.
"""
