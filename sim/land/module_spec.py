"""The land module's spec (sim/assembly).

The owner map, the ways and works and the colonies are saved in the world and seat slots. The installed mods' map overlays are
the engine's, published by sim/engine/bridge_land.py. No view is cached: the owner map is seeded by its first read, and the
geography views follow the held technologies and the people, which are written outside any command of this module."""
from sim.actors.api import FollowTileTransfer
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.demography.api import SendSettlers
from sim.hazards.api import RecordWorldEvent
from sim.ledger.api import PayEdge
from sim.reporting.api import RecordEvent
from sim.stores.api import WriteStore

from .commands import AdvanceColonies, BuildWay, BuildWork, FinishWays, FoundColony, LoseWork, TransferTile
from .module import Land
from .state import LandSeat, LandWorld

READS_BY_OWNER = {
    "core": ("civilisation", "civilisation_record", "year", "map_overlays", "money_text", "plain_number"),
    "knowledge": ("techniques_held", "techniques_version", "techniques_granted", "tree_nodes"),
    "ventures": ("operating_version",),
    "projects": ("project_cost_now",),
    "markets": ("purchase_quote",),
    "workforce": ("labour_market", "settlement_tiles", "money_per_labour_hour"),
    "finance": ("can_pay", "afford_means", "spending_power"),
    "mechanics": ("mechanic",),
    "production": ("is_venture", "running", "institution_expansion_convexity"),
    "foreign_trade": ("partners_in_agent_economy",),
    "stores": ("store",),
    "seats": ("seat_list",),
    "demography": ("pop_scale", "working_age"),
    "disease": ("disease_burden", "regional_disease_loss"),
    "agriculture": ("wild_stock",),
}

_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "land", Land, world_state=LandWorld, seat_state=LandSeat,
    publishes=(
        ViewSpec("tile_owner", "tile_owner", kind=KEYED, **_LIVE),
        ViewSpec("tile_control", "tile_control", kind=KEYED, **_LIVE),
        ViewSpec("tiles_owned_by", "tiles_owned_by", kind=KEYED, **_LIVE),
        ViewSpec("tile_owner_map", "tile_owner_map", **_LIVE),
        ViewSpec("home_tiles_held", "home_tiles_held", **_LIVE),
        ViewSpec("tiles_listed_by", "tiles_listed_by", kind=QUOTE),
        ViewSpec("home_tiles_held_version", "home_tiles_held_version", **_LIVE),
        ViewSpec("tile_ownership_problems", "tile_ownership_problems", **_LIVE),
        ViewSpec("settlement_spec", "settlement_spec", kind=QUOTE),
        ViewSpec("settlement_candidates", "settlement_candidates", kind=QUOTE),
        ViewSpec("settlement_outfit_cost", "settlement_outfit_cost", kind=QUOTE),
        ViewSpec("colonies", "colony_rows", seat_scoped=True, **_LIVE),
        ViewSpec("map_for_agent_economy", "map_for_agent_economy", **_LIVE),
        ViewSpec("geography_data", "geography_data", **_LIVE),
        ViewSpec("legacy_geography", "legacy_geography", **_LIVE),
        ViewSpec("built_ways", "built_ways", **_LIVE),
        ViewSpec("built_way_km", "built_way_km", kind=QUOTE),
        ViewSpec("way_quote", "way_quote", kind=QUOTE),
        ViewSpec("way_refusal", "way_refusal", kind=QUOTE),
        ViewSpec("works_at", "works_at", kind=KEYED, **_LIVE),
        ViewSpec("work_capacity", "work_capacity", kind=KEYED, **_LIVE),
        ViewSpec("work_quote", "work_quote", kind=QUOTE),
        ViewSpec("held_techniques", "held_techniques", kind=QUOTE),
        ViewSpec("partner_gate_refusal", "partner_gate_refusal", kind=QUOTE),
        ViewSpec("techniques_with_results", "techniques_with_results", kind=QUOTE),
        ViewSpec("tile_description", "tile_description", kind=QUOTE),
        ViewSpec("land_area_of", "land_area_of", kind=QUOTE),
        ViewSpec("tile_climates", "tile_climates", kind=QUOTE),
        ViewSpec("tile_places", "tile_places", kind=QUOTE),
        ViewSpec("map_catalogue", "map_catalogue", kind=QUOTE),
        ViewSpec("regions_of", "regions_of", kind=QUOTE),
        ViewSpec("endemic_people_loss", "endemic_people_loss", kind=QUOTE),
        ViewSpec("modes_usable", "modes_usable", kind=QUOTE),
        ViewSpec("modes_carrying", "modes_carrying", kind=QUOTE),
        ViewSpec("carriage_facts", "carriage_facts", **_LIVE),
        ViewSpec("mode_carrier", "mode_carrier", kind=QUOTE),
        ViewSpec("mode_crews", "mode_crews", kind=QUOTE),
        ViewSpec("cheapest_route", "cheapest_route", kind=QUOTE),
        ViewSpec("reach_days", "reach_days", kind=QUOTE),
        ViewSpec("forest_increment", "forest_increment", kind=QUOTE),
        ViewSpec("felled_after_cuts", "felled_after_cuts", kind=QUOTE),
        ViewSpec("felled_after_regrowth", "felled_after_regrowth", kind=QUOTE),
        ViewSpec("timber_on_tile", "timber_on_tile", kind=QUOTE),
        ViewSpec("deposit_catalogue", "deposit_catalogue", **_LIVE),
        ViewSpec("deposits_listed", "deposits_listed", kind=QUOTE),
        ViewSpec("deposits_worked_before", "deposits_worked_before", kind=QUOTE),
        ViewSpec("deposit_working_rate", "deposit_working_rate", kind=QUOTE),
        ViewSpec("prospect_finds", "prospect_finds", kind=QUOTE),
        ViewSpec("tile_endowment", "tile_endowment", kind=QUOTE),
        ViewSpec("tile_known", "tile_known", kind=KEYED, **_LIVE),
        ViewSpec("borders_among", "borders_among", kind=QUOTE),
        ViewSpec("tile_facts", "tile_facts", kind=KEYED, **_LIVE),
        ViewSpec("home_modes", "home_modes", **_LIVE),
        ViewSpec("route_between", "route_between", kind=QUOTE),
        ViewSpec("reach_from", "reach_from", kind=QUOTE),
        ViewSpec("held_tile_geometry", "held_tile_geometry", **_LIVE),
        ViewSpec("crop_sites", "crop_sites", kind=QUOTE),
        ViewSpec("food_kcal_by_source", "food_kcal_by_source", kind=QUOTE),
        ViewSpec("game_food_sources", "game_food_sources", **_LIVE),
        ViewSpec("huntable_kcal", "huntable_kcal", kind=QUOTE),
        ViewSpec("take_hunt", "take_hunt", kind=QUOTE),
        ViewSpec("regrow_wild_stock", "regrow_wild_stock", kind=QUOTE),
        ViewSpec("tile_soil_nitrogen_factors", "tile_soil_nitrogen_factors", kind=QUOTE),
        ViewSpec("soil_nitrogen_after_year", "soil_nitrogen_after_year", kind=QUOTE),
        ViewSpec("tracked_materials", "tracked_materials", **_LIVE),
        ViewSpec("mineral_share_of_tiles", "mineral_share_of_tiles", kind=QUOTE),
        ViewSpec("material_source_tiles", "material_source_tiles", kind=KEYED, **_LIVE),
        ViewSpec("route_km_to", "route_km_to", kind=QUOTE),
        ViewSpec("mineral_scale", "mineral_scale", kind=KEYED, **_LIVE),
        ViewSpec("material_cost_factor", "material_cost_factor", kind=QUOTE),
        ViewSpec("stock_land", "stock_land", **_LIVE),
        ViewSpec("endemic_stock_loss", "endemic_stock_loss", kind=QUOTE),
        ViewSpec("nursery_room_units", "nursery_room_units", kind=QUOTE),
    ),
    applies=((TransferTile, "transfer_tile"), (AdvanceColonies, "advance_colonies"), (FoundColony, "found_colony"),
             (BuildWay, "build_way"), (FinishWays, "finish_ways"), (BuildWork, "build_work"), (LoseWork, "lose_work")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(FollowTileTransfer, PayEdge, RecordEvent, RecordWorldEvent, SendSettlers, WriteStore),
),)
