"""What the land module answers about places on the map: a tile's record and climate, the names and regions on it, and the
endemic disease of the ground. Mixed into `Land`."""
from typing import Any, Dict, Iterable, List

from sim.geography.api import endemic_people_loss, layer_value, regions_of_tiles, tile_facts, tile_names

CLIMATE_LAYERS = ("lat", "koppen_class", "koppen_sample_mix")


class MapPlaces:
    """Mixed into `Land`."""

    world_map: Any

    def tile_description(self, tile: str) -> Dict[str, Any]:
        """{id, lat, lon, land_area_km2, coastal, neighbours, climate_class, region} of a tile on the map."""
        return tile_facts(tile, self.world_map)

    def land_area_of(self, tiles: Iterable[str]) -> float:
        """Total land area in km2 of these tiles, summed in the order given."""
        return sum(float(tile_facts(tile, self.world_map)["land_area_km2"]) for tile in tiles)

    def tile_climates(self, tiles: Iterable[str]) -> List[Dict[str, Any]]:
        """[{lat, koppen_class, koppen_sample_mix}] for each of these tiles, in the order given."""
        return [{layer: layer_value(tile, layer, self.world_map) for layer in CLIMATE_LAYERS} for tile in tiles]

    def tile_places(self, tile: str) -> List[str]:
        """Names of the places the map puts on a tile, highest rank first; empty when it names none."""
        return tile_names.places_on(self.world_map, tile)

    def regions_of(self, tiles: Iterable[str]) -> List[str]:
        """Sorted region labels the tiles carry."""
        return regions_of_tiles(tiles, self.world_map)

    def endemic_people_loss(self, tiles: Iterable[str]) -> Dict[str, float]:
        """{population band: excess death rate a year} from the endemic disease of these tiles, averaged over them."""
        return endemic_people_loss(tiles, self.world_map)
