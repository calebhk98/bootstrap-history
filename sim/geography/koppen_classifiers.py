"""Koppen-Geiger classifiers for the tile generator, one per option of map_data_sources.SOURCES["koppen_class"].

Each factory returns classify(lat, lon) -> class letters, or None when the dataset has nothing there.
"""


def kgcpy_rubel_2016():
    import kgcpy  # generator-only dependency

    def classify(lat, lon):
        # Keep longitude in [-180, 180): the equal-area round trip can return 180.00000003 at the antimeridian.
        lon = ((lon + 180.0) % 360.0) - 180.0
        # The raster marks some coastline pixels "Ocean" where the land mask says land; widen the search to the
        # nearest real classification.
        try:
            climate_zone = kgcpy.lookupCZ(lat, lon)
            if climate_zone != "Ocean":
                return climate_zone
        except Exception:
            pass
        for size in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144):
            try:
                climate_zone, _uncertainty, nearby = kgcpy.nearbyCZ(lat, lon, size=size)
                if climate_zone != "Ocean":
                    return climate_zone
                real_land_nearby = [zone for zone in nearby if zone != "Ocean"]
                if real_land_nearby:
                    return real_land_nearby[0]
            except Exception:
                continue
        return None

    return classify
