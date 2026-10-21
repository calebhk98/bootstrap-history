"""The farm model's answer to the tile food view: what a cropped hectare gives under a farming technique.

The farm model owns the physical yield (crop, tools, rotation, storage loss). A tile's food capacity is the
tile's cropped hectares times this per-hectare answer times the tile's own yield factor (soil, climate, river
water; geography's `crop_site`), so both read one yield rather than keeping two estimates.
"""
from typing import Optional

from sim.geography.api import CropTechnique
from sim.world import agriculture

REFERENCE_HECTARES = 1000.0   # large enough that the harvest-window cap reads as the plain per-hectare rate


def crop_technique(technique, storage_technique: Optional["agriculture.StorageTechnique"] = None) -> CropTechnique:
    """What one cropped reference hectare yields under `technique` (a farming_technique.Technique)."""
    storage_technique = storage_technique or agriculture.DEFAULT_STORAGE_TECHNIQUE
    crop, toolkit, rotation = technique.crop, technique.toolkit, technique.rotation
    hours_per_hectare = crop.base_labour_hours_per_hectare * toolkit.labour_hours_multiplier
    gross_kg = agriculture.gross_harvest_kg(
        agriculture.Land(REFERENCE_HECTARES, quality=1.0), REFERENCE_HECTARES * hours_per_hectare,
        crop=crop, toolkit=toolkit, rotation=rotation,
        worker_count=REFERENCE_HECTARES / agriculture.hectares_cropped_per_farm_worker(crop, toolkit)) / REFERENCE_HECTARES
    return CropTechnique(
        kg_per_cropped_hectare=gross_kg,
        open_field_cropped_share=1.0 - rotation.fallow_share_of_holding,
        seed_kg_per_cropped_hectare=crop.planting_material_kg_per_ha,
        loss_fraction=storage_technique.spoilage_rate_per_year,
        kcal_per_kg=crop.energy_kcal_per_kg,
        tillage_capacity=toolkit.tillage_capacity)
