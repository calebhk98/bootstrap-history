"""The resources module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_resources.py and
the files it names) under the name the owner will publish, except the `legacy_*` ones: raw state used in place."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, PhaseHook, ViewSpec
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.materials.api import ApplyThrottle
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent

from .channels import FOREST, MINES, NITRE, TIMBER
from .commands import (AutoMothballMines, BuyForest, CloseMine, DrawDeposit, FellTimber, LayNitreBeds, MothballMines, NoteMineCostPaid, OpenMine,
                       Prospect, RegrowTimber)
from .module import Resources
from .state import ResourcesSeat, ResourcesWorld

READS_BY_OWNER = {
    "knowledge": ("year", "start_year", "civilisation"),
    "prices": ("price_index", "material_price"),
    "workforce": ("wage", "labour_quote", "money_per_labour_hour"),
    "materials": ("normalized_material", "material_demand", "material_checks", "charcoal_per_hectare", "material_shortfall",
                  "material_market_tonnes", "material_unsupplied_sentence", "material_binding"),
    "ledger": ("goods_stock", "acting_balance"),
    "finance": ("can_pay", "purchase_budget", "spending_power", "affordable_units", "afford_means"),
    "polity": ("inspection_reach", "forest_reach"),
    "production": ("revenue_estimate", "running", "running_stamp"),
    "mechanics": ("effect_best", "effect_terms"),
    "land": ("mineral_scale", "legacy_world_map"),
    "agriculture": ("weather_seed",),
    "seats": ("automatic_policy", "founder"),
    "reporting": ("money_text", "mass_text", "area_text", "mass_rate_text", "mass_per_area_text"),
}

# not cached: they read prices, wages, the state's reach or the map, which legacy code still writes outside any command
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "resources", Resources, channels=(MINES, FOREST, NITRE, TIMBER), world_state=ResourcesWorld, seat_state=ResourcesSeat,
    publishes=(
        # cached: every write to the seat's workings, woodland, nitre beds and the felled ledger is a command or phase of this module
        ViewSpec("mine_workings", "mine_workings", channels=(MINES,), seat_scoped=True),
        ViewSpec("mine_capacity", "mine_capacity", channels=(MINES,), seat_scoped=True),
        ViewSpec("mines_being_sunk", "mines_being_sunk", channels=(MINES,), seat_scoped=True),
        ViewSpec("mine_depletion", "mine_depletion", kind=KEYED, channels=(MINES,), seat_scoped=True),
        ViewSpec("forest_hectares", "forest_hectares", channels=(FOREST,), seat_scoped=True),
        ViewSpec("nitre_beds", "nitre_beds", channels=(NITRE,), seat_scoped=True),
        ViewSpec("timber_felled", "timber_felled", channels=(TIMBER,)),
        ViewSpec("mine_operating_cost", "mine_operating_cost", seat_scoped=True, **_LIVE),
        ViewSpec("mine_working_cost", "operating_cost_of", kind=QUOTE, **_LIVE),
        ViewSpec("mine_working_report", "working_report", kind=QUOTE, **_LIVE),
        ViewSpec("mine_quote", "mine_quote", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("mine_land_ceiling", "mine_land_ceiling", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("mineable", "mineable", kind=KEYED, **_LIVE),
        ViewSpec("mine_catalog_hint", "mine_catalog_hint", **_LIVE),
        ViewSpec("mine_works_materials", "works_materials", **_LIVE),
        ViewSpec("mine_demand_goods", "mine_demand_goods", kind=KEYED, **_LIVE),
        ViewSpec("mine_yield", "mine_yield", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("mine_depletion_note", "mine_depletion_note", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("empire_output", "empire_output"),
        ViewSpec("found_deposits", "found_deposits", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("partner_deposits", "partner_deposits", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("deposit_remaining", "deposit_remaining_tonnes", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("mine_room_in_deposits", "mine_room_in_deposits", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("forest_holding", "forest_holding", seat_scoped=True, **_LIVE),
        ViewSpec("forest_price", "forest_price_per_hectare", **_LIVE),
        ViewSpec("forest_ceiling", "forest_land_ceiling", seat_scoped=True, **_LIVE),
        ViewSpec("nitre_price", "nitre_base_cost", **_LIVE),
        ViewSpec("shortage_remedy_plan", "shortage_remedy_plan", kind=QUOTE, seat_scoped=True, **_LIVE),
    ),
    applies=((OpenMine, "open_mine"), (CloseMine, "close_mine"), (MothballMines, "mothball_mines"), (AutoMothballMines, "auto_mothball_mines"),
             (DrawDeposit, "draw_deposit"), (Prospect, "prospect"), (BuyForest, "buy_forest"), (LayNitreBeds, "lay_nitre"),
             (NoteMineCostPaid, "note_mine_cost_paid"), (FellTimber, "fell_timber"), (RegrowTimber, "regrow_timber")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(ApplyThrottle, PayEdge, ReceiveFromEdge, RecordEvent, RecordAutomation, RecordAutomationSkip),
    phases=(PhaseHook("materials", "step_materials"),),
),)
