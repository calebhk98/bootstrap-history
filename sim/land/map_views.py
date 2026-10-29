"""The map and the geography of the game, and the facts about the land other modules read.

`Geography` (sim/geography) reads the civilisation, its population scale, the technologies it holds and the ways built
through `GeographyInputs`, which asks the views the module declared. Each view below answers from the map or from the
geography handle."""
from typing import Any, Dict, List, Optional

from sim.geography.api import (Geography, endemic_people_loss, food_potential, layer_value, load_geography, open_map, reach,
                               route, tiles_held, usable_modes)


class GeographyInputs:
    """What one game's geography reads from it, as the views the land module declared."""

    def __init__(self, module: Any):
        self._module = module

    @property
    def civ(self) -> Any:
        return self._module.needs.civilisation()

    @property
    def pop_scale(self) -> float:
        return self._module.needs.pop_scale()

    @property
    def world_map(self) -> Any:
        return self._module.world_map

    @property
    def held_nodes(self) -> Any:
        """The technologies the civilisation holds and keeps in service, and what its actions returned."""
        return self._module.needs.held_techniques(True)

    @property
    def improvements(self) -> Any:
        """The roads and track built, {edge key: {way: true}}."""
        return self._module.needs.built_ways()

    def civilisation(self, civilisation_id: str) -> Optional[Dict[str, Any]]:
        """A civilisation's record, or None when there is none by that id."""
        try:
            return self._module.needs.civilisation_record[civilisation_id]
        except (OSError, ValueError, KeyError):
            return None


class MapViews:
    """Mixed into `Land`."""

    needs: Any
    _map_cache: Optional[Any] = None
    _geography_cache: Optional[Geography] = None

    @property
    def world_map(self) -> Any:
        """The base map with every installed mod's map overlay merged, in the mods' load order."""
        if self._map_cache is None:
            self._map_cache = open_map(list(self.needs.map_overlays()))
        return self._map_cache

    @property
    def geography(self) -> Geography:
        if self._geography_cache is None:
            self._geography_cache = Geography(GeographyInputs(self))
        return self._geography_cache

    def tiles_listed_by(self, civilisation: Any) -> List[str]:
        """The tiles a civilisation's file lists as its own (its `home_tiles`, else those its `home_regions` name), on this map."""
        return tiles_held(civilisation, self.world_map)

    def map_for_agent_economy(self) -> Any:
        """The map the agent economy's setup holds for its tile builds and route searches (its `EconomySetup.world_map`)."""
        return self.world_map

    def geography_data(self) -> Any:
        """The geography data the map describes, for the `Geography` handle to open on."""
        return load_geography(self.world_map)

    def legacy_geography(self) -> Geography:
        return self.geography

    def tile_known(self, tile: str) -> bool:
        return tile in self.world_map.tiles

    def borders_among(self, tiles: Any) -> Dict[str, Any]:
        """{tile: the tiles it borders} for each of the tiles on the map."""
        return self.geography.borders_among(tiles)

    def tile_facts(self, tile: str) -> Optional[Dict[str, float]]:
        """What a tile gives an army, from the map: the food it can feed, the working-age people its endemic disease takes in a
        year, and its ruggedness; None for a tile not on the map. Static, so kept per tile."""
        world_map = self.world_map
        if tile not in world_map.tiles:
            return None
        if tile not in self._tile_facts:
            self._tile_facts[tile] = (float(food_potential(tile, world_map=world_map)["total_kcal_per_year"]),
                                      float(endemic_people_loss([tile], world_map).get("working_age", 0.0)),
                                      float(layer_value(tile, "ruggedness_index", world_map) or 0.0))
        food, disease, ruggedness = self._tile_facts[tile]
        return {"food_kcal_per_year": food, "working_age_endemic_loss": disease, "ruggedness": ruggedness}

    def home_modes(self) -> List[str]:
        """The ways the home country's goods can travel: what its built ways and ports allow."""
        return list(usable_modes([self.needs.held_techniques(True)], self.world_map))

    def route_between(self, origin: str, target: str, modes: Any) -> Any:
        """The fastest route from one tile to another by these modes over the built ways, or None."""
        return route([origin], [target], modes, self.world.improvements, held_nodes=self.needs.held_techniques(True),
                     world_map=self.world_map, fastest=True)

    def reach_from(self, tile: str, modes: Any, range_days: float) -> Dict[str, float]:
        """{tile: days} reachable from a tile by these modes within `range_days`."""
        return reach([tile], modes, range_days, self.world.improvements, world_map=self.world_map)

    def held_tile_geometry(self) -> List[tuple]:
        """[(tile id, lat, lon, land area km2, arable fraction)] for each held tile the land map describes, in held order."""
        tiles_by_id = (load_geography(self.world_map).get("land_tiles") or {}).get("tiles") or {}
        rows = []
        for tile_id in tiles_held(self.needs.civilisation(), self.world_map):
            tile = tiles_by_id.get(tile_id)
            if not tile:
                continue
            rows.append((tile_id, tile["lat"], tile["lon"], tile.get("land_area_km2", 0.0), tile.get("arable_fraction", 0.0)))
        return rows

    def crop_sites(self, cropped_share: float, nutrient_factors: Any, tillage_capacity: float) -> Any:
        """{tile: crop site} over the held tiles under a rotation that crops `cropped_share`."""
        return self.geography.crop_sites(cropped_share, nutrient_factors, tillage_capacity)

    def food_kcal_by_source(self, wild_stock: Any, crop_technique: Any, nutrient_factors: Any) -> Any:
        return self.geography.food_kcal_by_source(wild_stock, crop_technique, nutrient_factors)

    def game_food_sources(self) -> Any:
        return self.geography.game_food_sources()

    def huntable_kcal(self, wild_stock: Any) -> Any:
        return self.geography.huntable_kcal(wild_stock)

    def take_hunt(self, wild_stock: Any, available: Any, share: float) -> Any:
        return self.geography.take_hunt(wild_stock, available, share)

    def regrow_wild_stock(self, wild_stock: Any) -> Any:
        return self.geography.regrow_wild_stock(wild_stock)

    def tile_soil_nitrogen_factors(self, stock: Any, cropped_share: float, reference_cropped_share: float, manure_kg: float) -> Any:
        return self.geography.soil_nitrogen_factors(stock, cropped_share, reference_cropped_share, manure_kg)

    def soil_nitrogen_after_year(self, stock: Any, cropped_share: float, reference_cropped_share: float,
                                 kg_per_cropped_hectare: float, legume_share: float, manure_kg: float) -> Dict[str, float]:
        """The soil nitrogen stock a year of cropping, legumes and manure on the held tiles leaves; `stock` is not changed."""
        after = dict(stock)
        self.geography.step_soil_nitrogen(after, cropped_share, reference_cropped_share, kg_per_cropped_hectare, legume_share,
                                          manure_kg)
        return after

    def tracked_materials(self) -> Any:
        return self.geography.tracked_materials()

    def mineral_share_of_tiles(self, tiles: Any, commodity: str) -> float:
        """Share of a mined commodity on the given tiles."""
        return self.geography.held_share(tiles, commodity)

    def material_source_tiles(self, material: str) -> Any:
        return self.geography.source_tiles(material)

    def route_km_to(self, tiles: Any) -> Any:
        return self.geography.route_km_to(tiles)

    def mineral_scale(self, material: str) -> float:
        return self.geography.mineral_scale(material)

    def material_cost_factor(self, node_id: str) -> float:
        """What the geography multiplies a project's material bill by (distance from the sources)."""
        return self.geography.material_cost_factor(node_id)

    def stock_land(self) -> Dict[str, Any]:
        """{place: the tile the held stock stands on, pasture_kg: live weight the held tiles' grass carries}."""
        return {"place": self.geography.stock_place(), "pasture_kg": self.geography.held_pasture_kg(self.needs.wild_stock())}

    def endemic_stock_loss(self, place: Optional[str], species: Any) -> float:
        return self.geography.endemic_stock_loss(place, species)

    def nursery_room_units(self, place: Optional[str], output_per_batch: float, hectare_years_per_batch: float) -> Any:
        return self.geography.nursery_room_units(place, output_per_batch, hectare_years_per_batch)
