"""The coin module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_coin.py)
under the name the owner will publish, except the `legacy_*` ones: raw state the module still reads in place."""
from sim.assembly.api import KEYED, QUOTE, TABLE, ModuleSpec, PhaseHook, Provision, ViewSpec
from sim.ledger.api import PayEdge, PayEdgeFrom, TakeGoods

from .commands import ChargeActorsTheft, ChargeHouseholdTheft, ChargeKeeping, PlunderHousehold
from .module import Coin
from .prices import RATIOS
from .state import CoinWorld

READS_BY_OWNER = {
    "knowledge": ("civilisation",),
    "workforce": ("money_per_labour_hour", "opening_money_per_labour_hour", "headcount"),
    "markets": ("opening_population", "goods_quote"),
    "foreign_trade": ("foreign_economies", "foreign_coin_home_units", "foreign_coin_partner_units", "partner_coin_standard",
                      "partner_opening_facts", "partner_route_cost"),
    "reporting": ("coin_value_ratio",),
    "ledger": ("acting_balance", "held_goods", "cast"),
    "finance": ("credit_limit", "lent_share"),
    "polity": ("standing", "eminence", "visible_scale", "order_reach"),
    "agriculture": ("farm_holdings", "farm_land_price"),
    "resources": ("forest_holding",),
    "land": ("home_country", "tile_known", "tile_haul_cost"),
    "actors": ("actor_world",),
}

# not cached: the foreign ledgers, the purse and the stock they read are still written outside their owners' commands
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "coin", Coin, channels=(RATIOS,), world_state=CoinWorld,
    publishes=(
        ViewSpec("home_coin_metal", "home_coin_metal", **_LIVE),
        ViewSpec("home_coin_stock", "home_coin_stock", **_LIVE),
        ViewSpec("home_price_level", "home_price_level", channels=(RATIOS,), **_LIVE),
        ViewSpec("partner_price_level", "partner_price_level", kind=KEYED, channels=(RATIOS,), **_LIVE),
        ViewSpec("partner_coin_opening", "partner_coin_opening", kind=KEYED, **_LIVE),
        ViewSpec("coin_kg_per_unit", "coin_kg_per_unit", **_LIVE),
        ViewSpec("coin_keeping_cost", "coin_keeping_cost", kind=QUOTE),
        ViewSpec("coin_keeping_due", "coin_keeping_due", kind=QUOTE, seat_scoped=True),
        ViewSpec("coin_hoard", "coin_hoard", seat_scoped=True, **_LIVE),
        ViewSpec("coin_hoard_report", "coin_hoard_report", seat_scoped=True, **_LIVE),
        ViewSpec("coin_carriage_units", "coin_carriage_units", kind=QUOTE),
        ViewSpec("household_exposure", "household_exposure", seat_scoped=True, **_LIVE),
        ViewSpec("household_visible_scale", "household_visible_scale", seat_scoped=True, **_LIVE),
    ),
    applies=((ChargeKeeping, "charge_keeping"), (ChargeActorsTheft, "charge_actors_theft"),
             (ChargeHouseholdTheft, "charge_household_theft"), (PlunderHousehold, "plunder_household")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(PayEdge, PayEdgeFrom, TakeGoods),
    phases=(PhaseHook("coin_revaluation", "revalue_coin_metals"),),
    provides=(Provision("transfer_surcharge", "carriage_surcharge", "carriage"),),
),)
