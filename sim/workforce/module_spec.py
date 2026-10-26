"""The workforce module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_workforce.py and
the other bridge files) under the name the owner will publish, or a view of a module that has moved. Every view the module
publishes is uncached: the staff and hour fields are still on the household record, which the engine, the actors and the
screens write directly, so no channel can say when they changed."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.demography.api import SetClearedFarmland, SetFarmHoursNeeded
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.polity.api import AddReputation, ScaleFamiliarity, ScaleProtection
from sim.reporting.api import DiscardEventsAfter, RecordEvent

from .commands import (AllocateFarmWorkforce, ApplyLandClearing, BuildHousing, NoteTradeSpread, PressLabour, ReportStaffReduction,
                       ScaleDeputies, SetEmployed, SurviveStaff, UpdateWages)
from .module import Workforce

READS_BY_OWNER = {
    "core": ("civilisation", "game_config", "opening_wage_index", "legacy_state", "legacy_game", "legacy_order", "legacy_tree",
             "legacy_dice", "legacy_act_as", "starting_wages", "trades_absent", "trade_notes", "trade_records", "trade_family",
             "wage_schedule_for", "plain_number", "money_text", "legacy_acting_household", "legacy_household_actor"),
    "seats": ("founder", "acting_country"),
    "polity": ("standing", "rep_factor"),
    "reporting": ("event_log", "last_market_price_ratio", "real_output_per_head", "agent_prices", "agent_wage"),
    "demography": ("population", "pop_scale", "people_by_tile", "urban_fraction", "farm_holdings"),
    "agriculture": ("farm_land", "farm_technique_this_year", "farm_ladder", "farm_arable_ceiling"),
    "land": ("home_tiles_held", "home_tiles_held_version", "coverage", "coverage_share"),
    "knowledge": ("techniques_held", "held_techniques", "visibility", "tree_closure"),
    "mechanics": ("mechanic", "effect_factor", "effect_holds", "effect_sum", "effect_terms", "effect_value",
                  "labour_productivity_sources", "room_sources", "staff_capacity_sources"),
    "diffusion": ("literacy", "research_productivity", "staff_hire_advice", "staff_sources"),
    "production": ("running", "institution_units", "upkeep", "revenue_estimate", "is_venture"),
    "projects": ("start_check", "reopen_units", "exclusion_reason", "active_hours_still_wanted", "staff_closure_age",
                 "staffing_draw", "staffing_held_totals", "staffing_shortfalls", "concerns_to_close_for_staffing",
                 "venture_foreman", "venture_foremen_used", "venture_staff_free", "shared_answer"),
    "materials": ("material_price_factor",),
    "finance": ("living_cost", "spending_power", "can_pay", "purchase_refusal", "price_index", "home_price_level",
                "housing_price_per_place", "trade_school_price_per_seat", "concern_rows_stopped"),
    "actors": ("actor_staff_fte", "actor_staff_nationwide", "actor_staff_total", "teaching_knowledge", "harvest_share_taken",
               "director_overhead_hours", "agent_people_by_trade", "agent_people_by_tile_and_trade", "agent_country",
               "agent_unskilled_wage"),
}

_LIVE = dict(cached=False)
_SEAT = dict(cached=False, seat_scoped=True)

MODULE_SPECS = (ModuleSpec(
    "workforce", Workforce,
    publishes=(
        ViewSpec("staff", "staff", **_SEAT),
        ViewSpec("staff_snapshot", "staff_snapshot", **_SEAT),
        ViewSpec("headcount", "headcount", **_SEAT),
        ViewSpec("hours_available", "hours_available", kind=KEYED, **_SEAT),
        ViewSpec("literacy_references", "literacy_references", **_LIVE),
        ViewSpec("literacy_capacity", "literacy_capacity", kind=KEYED, **_SEAT),
        ViewSpec("farm_share_of_hours", "farm_share_of_hours", **_SEAT),
        ViewSpec("trade_spread", "trade_spread", **_SEAT),
        ViewSpec("staff_advice", "staff_advice", kind=QUOTE, **_LIVE),
        ViewSpec("project_staffing_shortfall", "project_staffing_shortfall", kind=QUOTE, **_LIVE),
        ViewSpec("seat_base_tile", "seat_base_tile", kind=KEYED, **_LIVE),
        ViewSpec("market_supply", "market_supply", kind=KEYED, **_LIVE),
        ViewSpec("trade_available", "trade_available", kind=KEYED, **_LIVE),
        ViewSpec("labour_quote", "labour_quote", kind=QUOTE, **_LIVE),
        ViewSpec("hour_wage", "hour_wage", kind=KEYED, **_LIVE),
        ViewSpec("wage", "wage", kind=KEYED, **_LIVE),
        ViewSpec("base_annual_wage", "base_annual_wage", kind=KEYED, **_LIVE),
        ViewSpec("trade_population", "trade_population", kind=KEYED, **_LIVE),
        ViewSpec("money_per_labour_hour", "money_per_labour_hour", **_LIVE),
        ViewSpec("opening_money_per_labour_hour", "opening_money_per_labour_hour", **_LIVE),
        ViewSpec("labour_state_weights", "labour_state_weights", **_LIVE),
        ViewSpec("town_mortality_premium_by_tile", "town_mortality_premium_by_tile", **_LIVE),
        ViewSpec("wage_index_terms", "wage_index_terms", **_LIVE),
        ViewSpec("wage_index", "wage_index", **_LIVE),
        ViewSpec("wage_materials", "wage_materials", **_LIVE),
        ViewSpec("trade_registry", "trade_registry", **_LIVE),
        ViewSpec("society_labour_hours", "society_labour_hours", **_LIVE),
        ViewSpec("farming_technique", "farming_technique", **_LIVE),
        ViewSpec("farm_land_hectares", "farm_land_hectares", **_LIVE),
        ViewSpec("hours_per_person_year", "hours_per_person_year", **_LIVE),
    ),
    applies=((SetEmployed, "set_employed"), (NoteTradeSpread, "note_trade_spread"), (PressLabour, "press_labour"),
             (SurviveStaff, "survive_staff"), (ScaleDeputies, "scale_deputies"), (ReportStaffReduction, "report_staff_reduction"),
             (AllocateFarmWorkforce, "allocate_farm_workforce"), (ApplyLandClearing, "apply_land_clearing"),
             (UpdateWages, "update_wages")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(PayEdge, ReceiveFromEdge, RecordEvent, DiscardEventsAfter, AddReputation, ScaleFamiliarity, ScaleProtection,
           SetClearedFarmland, SetFarmHoursNeeded, BuildHousing),
),)
