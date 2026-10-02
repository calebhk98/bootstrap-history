"""Where a crop can be grown: the Koppen classes of a territory's tiles against the classes an entry names.

A production entry may carry `grown_in_climate_classes`, a list of Koppen-Geiger classes in which the
crop is grown. A civilisation can grow it when any tile of its home regions has one of them
(`data/world/geography.json`, `land_tiles`). An entry that names none grows anywhere. Whether the
civilisation knows how is a separate gate, the entry's `requires_node`.
"""
import functools

from sim.engine.data import load_civ, load_geography

CLASSES_FIELD = "grown_in_climate_classes"


@functools.lru_cache(maxsize=None)
def _tiles():
    tiles = load_geography().get("land_tiles") or {}
    return tiles.get("tiles") or {}, tiles.get("region_to_tiles") or {}


@functools.lru_cache(maxsize=None)
def classes_of_regions(home_regions):
    """Koppen classes of the tiles of these regions (a tuple of region ids)."""
    tiles, region_to_tiles = _tiles()
    return frozenset(tiles[tile_id]["koppen_class"]
                     for region_id in home_regions
                     for tile_id in region_to_tiles.get(region_id, ())
                     if tile_id in tiles)


def territory_classes(civilization_id):
    """Koppen classes of the tiles of a civilisation's home regions, read from its data file."""
    return classes_of_regions(tuple(load_civ(civilization_id).get("home_regions") or ()))


def territory_suits(entry, classes):
    """Whether a territory holding these classes can grow what the entry makes."""
    wanted = entry.get(CLASSES_FIELD)
    return not wanted or bool(set(wanted) & set(classes))


def entry_grows_in(entry, civilization_id, home_regions=None):
    """Whether the civilisation's territory has a climate the entry's crop grows in; `home_regions`, when
    the caller holds the civilisation, is used instead of reading its file."""
    classes = (classes_of_regions(tuple(home_regions)) if home_regions is not None
               else territory_classes(civilization_id))
    return territory_suits(entry, classes)
