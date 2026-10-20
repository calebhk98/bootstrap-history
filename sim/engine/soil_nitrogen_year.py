"""The held cropland's soil nitrogen between years (Complaint 543).

`state.economy.soil_nitrogen` is the saved {tile: share of the native pool left}; a tile with no entry is native.
Each year the cropped hectares' harvest, the rotation's legumes and the manure spread draw the pool down or build it
(sim/world/soil_nutrients.py), and the tile's yield factor reads it back through `soil_nitrogen_factors`.
"""
from sim.geography.api import crop_site, tiles_held
from sim.world import agriculture, agriculture_tile, land, soil_nutrients

DRAUGHT_HERD = "draught_animal_kg"   # the held stock whose dung the transitional manure rule spreads


class SoilNitrogenMixin:

    def _rotation_cropped_share(self):
        return 1.0 - self.labour.farming_technique().rotation.fallow_share_of_holding

    def refresh_farm_territory(self):
        """The farm's ladder, ceiling and cleared ground's quality from the held tiles as they now are: the soil nitrogen
        stock and the society's rotation both move a tile's yield factor and cropped hectares."""
        territory = land.territory_cropland(self.farm_sites())
        self._farm_ladder = territory.ladder
        self._farm_arable_ceiling = territory.cropped_hectares
        self.labour.set_farm_area(self.farm_land.hectares)

    def soil_nitrogen_factors(self):
        """{tile: yield factor of its soil nitrogen stock} for the held tiles below native, under the society's rotation."""
        stock = self.state.economy.soil_nitrogen
        if not stock:
            return {}
        cropped_share = self._rotation_cropped_share()
        reference = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
        manure = self._manure_nitrogen_per_hectare()
        return {tile_id: soil_nutrients.yield_response(stock[tile_id], cropped_share, reference, manure)
                for tile_id in tiles_held(self.civ, self.world_map) if tile_id in stock}

    def _manure_nitrogen_per_hectare(self):
        """Transitional: nitrogen of the draught herd's collected dung over the held cropped hectares, kg per hectare of holding."""
        herd_kg = self.state.economy.society_herds.get(DRAUGHT_HERD, 0.0)
        hectares = sum(site.cropped_hectares for site in self._unworn_sites().values())
        return 0.0 if hectares <= 0.0 else soil_nutrients.herd_manure_nitrogen_kg(herd_kg) / hectares

    def _unworn_sites(self):
        share = self._rotation_cropped_share()
        return {tile_id: crop_site(tile_id, share, self.world_map) for tile_id in tiles_held(self.civ, self.world_map)}

    def step_soil_nitrogen(self):
        """One year of cropping, legumes and manure on every held tile that has cropland."""
        technique = self.labour.farming_technique()
        crop = agriculture_tile.crop_technique(technique)
        rotation = technique.rotation
        reference = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
        stock = self.state.economy.soil_nitrogen
        manure = self._manure_nitrogen_per_hectare()
        for tile_id, site in self._unworn_sites().items():
            if site.arable_hectares <= 0.0 or site.cropped_hectares <= 0.0:
                continue
            cropped_share = min(1.0, site.cropped_hectares / site.arable_hectares)
            share = stock.get(tile_id, 1.0)
            stock[tile_id] = soil_nutrients.next_share(
                share, cropped_share, crop.kg_per_cropped_hectare * site.yield_factor,
                rotation.legume_share_of_holding, manure, reference)
