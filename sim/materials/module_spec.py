"""The materials module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_materials.py and
the files it names) under the name the owner will publish, except the `legacy_*` ones: raw state used in place. No view of
the module is cached: the stock, the projects and the market behind them are written outside any command of the owners."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, PhaseHook, ViewSpec
from sim.ledger.api import BankStock, ChangeStock, PayEdge
from sim.markets.api import NoteDraw, NotePurchase, ResetDraws
from sim.reporting.api import RecordEvent

from .channels import READING
from .commands import ApplyThrottle, CaptureReadings, ForgetReadings, RestoreReadings, SettleProjectMaterials
from .module import Materials
from .state import MaterialsSeat

READS_BY_OWNER = {
    "knowledge": ("year", "civilisation", "tree", "tree_nodes", "techniques_held", "visibility", "hard_prerequisites",
                  "legacy_projects", "project_versions", "operating", "default_population", "pop_scale"),
    "mechanics": ("mechanic", "effect_best", "running_stamp", "running"),
    "ledger": ("goods_stock", "held_goods", "goods_stock_opening"),
    "markets": ("goods_quote", "can_be_bought", "purchase_quote", "partner_import", "agent_producer_capacity",
                "material_freight_factor"),
    "prices": ("material_prices", "material_commodity_map", "commodity_record", "commodity_country_output", "price_epoch",
               "producers_stamp"),
    "foreign_trade": ("foreign_supply_tonnes",),
    "resources": ("empire_output", "mine_capacity", "mine_depletion", "forest_hectares", "nitre_beds", "found_deposits", "mine_works_materials",
                  "shortage_remedy_plan"),
    "land": ("legacy_world_map", "mineral_scale", "material_cost_factor"),
    "projects": ("project_cost", "project_cost_now", "opposition_factor", "cost_money_factor",
                             "rebuild_work_factor", "failure_reset_share", "shared_bill"),
    "diffusion": ("civ_cost_factor",),
    "finance": ("can_pay", "purchase_refusal"),
}

# not cached: the tonnes ledger, the projects and the market are still written by code outside the owners' commands
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "materials", Materials, channels=(READING,), seat_state=MaterialsSeat,
    publishes=(
        ViewSpec("material_pool", "material_pool", kind=KEYED, **_LIVE),
        ViewSpec("material_commodity", "material_commodity", kind=KEYED, **_LIVE),
        ViewSpec("normalized_material", "normalized_material", kind=KEYED, **_LIVE),
        ViewSpec("material_checks", "material_checks", **_LIVE),
        ViewSpec("charcoal_per_hectare", "charcoal_per_hectare", **_LIVE),
        ViewSpec("material_demand", "annual_material_demand", seat_scoped=True, **_LIVE),
        ViewSpec("material_demand_held", "demand_held", seat_scoped=True, **_LIVE),
        ViewSpec("demand_by_supply_tag", "demand_by_supply_tag", kind=QUOTE, **_LIVE),
        ViewSpec("own_supply_by_commodity", "own_supply_by_commodity", kind=QUOTE, **_LIVE),
        ViewSpec("material_own_supply", "own_material_supply", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("material_market_tonnes", "market_tonnes", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("society_output", "society_output_tonnes", kind=KEYED, **_LIVE),
        ViewSpec("national_output", "national_output", kind=KEYED, **_LIVE),
        ViewSpec("own_production_tags", "own_production_tags", seat_scoped=True, **_LIVE),
        ViewSpec("material_shortfall", "material_shortfall", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("material_price_factor", "material_price_factor", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("material_market_summary", "material_market_summary", seat_scoped=True, **_LIVE),
        ViewSpec("material_supply_route", "material_supply_route", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("material_unsupplied_sentence", "material_unsupplied_sentence", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("materials_report", "materials_report", seat_scoped=True, **_LIVE),
        ViewSpec("resource_throttle", "throttle_quote", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("material_binding", "binding", channels=(READING,), seat_scoped=True, **_LIVE),
        ViewSpec("material_throttle", "last_throttle", channels=(READING,), seat_scoped=True, **_LIVE),
        ViewSpec("material_shortages", "shortages", channels=(READING,), seat_scoped=True, **_LIVE),
        ViewSpec("shortage_conditions", "shortage_conditions", seat_scoped=True, **_LIVE),
        ViewSpec("generation", "generation_capacity_kw", seat_scoped=True, **_LIVE),
        ViewSpec("generation_breakdown", "generation_breakdown_kw", seat_scoped=True, **_LIVE),
        ViewSpec("generation_by_tier", "installed_generation_kw_by_tier", seat_scoped=True, **_LIVE),
        ViewSpec("electricity_demand", "electricity_demand_kw", seat_scoped=True, **_LIVE),
        ViewSpec("project_material_needs", "project_material_needs", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("project_material_bill", "project_material_bill", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("project_material_parts", "project_material_parts", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("project_cost_without_materials", "project_cost_without_materials", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("own_output_claim", "project_own_output_claim", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("bounty_price", "bounty_price", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("material_upfront_refusal", "material_upfront_refusal", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("failure_bill", "failure_bill", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("failure_loss", "failure_loss", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("materials_without_a_seller", "materials_without_a_seller", kind=QUOTE, seat_scoped=True, **_LIVE),
        ViewSpec("start_gate_material_seller", "start_gate_material_seller", kind=QUOTE, seat_scoped=True, **_LIVE),
    ),
    applies=((ApplyThrottle, "apply_throttle"), (SettleProjectMaterials, "settle_project_materials"),
             (ForgetReadings, "forget_readings"), (RestoreReadings, "restore_readings"),
             (CaptureReadings, "capture_readings")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(BankStock, ChangeStock, PayEdge, ResetDraws, NoteDraw, NotePurchase, RecordEvent),
    phases=(PhaseHook("material_shortage_notes", "step_shortage_notes"),),
),)
