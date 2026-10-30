"""The held cropland's soil nitrogen between years (Complaint 543).

The per-tile loop is geography's (soil_nitrogen_factors, soil_nitrogen_after_year); this hands it the society's rotation,
crop and draught herd. `world.soil_nitrogen` is the saved {tile: share of the native pool left}; a tile with no entry is
native. Each year the cropped hectares' harvest, the rotation's legumes and the manure spread draw the pool down or build
it, and the tile's yield factor reads it back through `soil_nitrogen_factors`."""
from sim.living_stock.api import stock_rates
from sim.world import agriculture, agriculture_tile

from . import rules
from .constants import DRAUGHT_HERD, DRAUGHT_HERD_SPECIES_ROW


class Soil:

    def _rotation_cropped_share(self):
        return 1.0 - self.needs.farming_technique().rotation.fallow_share_of_holding

    def soil_nitrogen_factors(self):
        """{tile: yield factor of its soil nitrogen stock} for the held tiles below native, under the society's rotation."""
        stock = self.world.soil_nitrogen
        if not stock:
            return {}
        return self.needs.tile_soil_nitrogen_factors(
            stock, self._rotation_cropped_share(), _reference_cropped_share(), self._draught_manure_kg())

    def _draught_manure_kg(self):
        """Dung and urine a year the draught herd's recipes collect (data/world/living_stock.json, the species row the herd's
        recipes read), kg."""
        return rules.draught_manure_kg(self.needs.society_herds().get(DRAUGHT_HERD, 0.0), stock_rates()[DRAUGHT_HERD_SPECIES_ROW])

    def step_soil_nitrogen(self, seats=None):
        """One year of cropping, legumes and manure on every held tile that has cropland."""
        technique = self.needs.farming_technique()
        self.world.soil_nitrogen = self.needs.soil_nitrogen_after_year(
            self.world.soil_nitrogen, self._rotation_cropped_share(), _reference_cropped_share(),
            agriculture_tile.crop_technique(technique).kg_per_cropped_hectare, technique.rotation.legume_share_of_holding,
            self._draught_manure_kg())


def _reference_cropped_share():
    return 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
