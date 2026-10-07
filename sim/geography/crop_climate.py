"""Where a crop can be grown: the Koppen classes of a territory's tiles against the classes an entry names.

A production entry may carry `grown_in_climate_classes`, a list of Koppen-Geiger classes in which the
crop is grown. A civilisation can grow it when any tile it holds (`tiles_held`) has one of them. An entry that names none grows anywhere. Whether the
civilisation knows how is a separate gate, the entry's `requires_node`.
"""
import functools

from sim.geography.loading import load_geography

CLASSES_FIELD = "grown_in_climate_classes"


@functools.lru_cache(maxsize=None)
def _tiles():
    tiles = load_geography().get("land_tiles") or {}
    return tiles.get("tiles") or {}


@functools.lru_cache(maxsize=None)
def classes_of_tiles(tile_ids):
    """Koppen classes of these tiles (a tuple of tile ids)."""
    tiles = _tiles()
    return frozenset(tiles[tile_id]["koppen_class"] for tile_id in tile_ids if tile_id in tiles)


def territory_classes(tile_ids):
    """Koppen classes of a civilisation's held tiles (any iterable of tile ids)."""
    return classes_of_tiles(tuple(tile_ids or ()))


def territory_suits(entry, classes):
    """Whether a territory holding these classes can grow what the entry makes."""
    wanted = entry.get(CLASSES_FIELD)
    return not wanted or bool(set(wanted) & set(classes))


def entry_grows_in(entry, tile_ids):
    """Whether a territory of these tiles has a climate the entry's crop grows in."""
    return territory_suits(entry, territory_classes(tile_ids))
