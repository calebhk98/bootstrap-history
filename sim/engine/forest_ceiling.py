"""How much standing woodland a civilisation could hold: the ground it holds, not the labels the ground is filed under."""
from sim.geography.api import tile_facts, tiles_held


def held_land_area_km2(civilisation, world_map=None):
    """Total land area of the tiles the civilisation holds; a civilisation holding no tile has none."""
    return sum(float(tile_facts(tile, world_map)["land_area_km2"]) for tile in tiles_held(civilisation, world_map))


def revenue_scale_multiple(revenue, revenue_scale, cap_multiple):
    """1 plus the revenue in units of the scale revenue, the revenue part capped; negative revenue adds nothing."""
    return 1.0 + min(cap_multiple, max(0.0, revenue) / revenue_scale)


def forest_ceiling_hectares(land_area_km2, state_reach, base_per_million_km2, per_million_km2_per_capacity,
                            revenue_multiple):
    """Hectares of woodland per million km2 of land (more for a more capable state), scaled by the revenue multiple."""
    return ((base_per_million_km2 + per_million_km2_per_capacity * state_reach)
            * (land_area_km2 / 1.0e6) * revenue_multiple)
