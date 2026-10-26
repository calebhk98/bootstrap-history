"""The held cropland's soil nitrogen between years (Complaint 543).

The per-tile loop lives in sim/geography/soil_nitrogen.py, reached as `sim.geography`; this mixin hands it the society's
rotation, crop and draught herd. `state.economy.soil_nitrogen` is the saved {tile: share of the native pool left}; a tile
with no entry is native.
Each year the cropped hectares' harvest, the rotation's legumes and the manure spread draw the pool down or build it
(sim/geography/soil_nutrients.py), and the tile's yield factor reads it back through `soil_nitrogen_factors`.
"""
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR
from sim.world import agriculture, agriculture_tile, land

from sim.living_stock.api import stock_rates

DRAUGHT_HERD = "draught_animal_kg"   # the held stock whose dung the transitional manure rule spreads
DRAUGHT_HERD_SPECIES_ROW = "cattle_kg"   # the draught recipe's dung and fodder factors are the cattle row's (95_herds.json)


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
        return self.geography.soil_nitrogen_factors(
            stock, self._rotation_cropped_share(), _reference_cropped_share(), self._draught_manure_kg())

    def _draught_manure_kg(self):
        """Dung and urine a year the draught herd's recipes collect (data/world/living_stock.json, the species row the herd's
        recipes read), kg."""
        row = stock_rates()[DRAUGHT_HERD_SPECIES_ROW]
        return (self.view("society_herds")().get(DRAUGHT_HERD, 0.0) * row["manure_share_of_live_weight_per_day"]
                * CIVIL_DAYS_PER_YEAR * row["manure_collected_share"])

    def step_soil_nitrogen(self):
        """One year of cropping, legumes and manure on every held tile that has cropland."""
        technique = self.labour.farming_technique()
        self.geography.step_soil_nitrogen(
            self.state.economy.soil_nitrogen, self._rotation_cropped_share(), _reference_cropped_share(),
            agriculture_tile.crop_technique(technique).kg_per_cropped_hectare, technique.rotation.legume_share_of_holding,
            self._draught_manure_kg())


def _reference_cropped_share():
    return 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
