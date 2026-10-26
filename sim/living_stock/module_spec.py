"""Living stock's module spec (sim/assembly)."""
from sim.assembly.api import KEYED, QUOTE, TABLE, ModuleSpec, PhaseHook, ViewSpec
from sim.foreign_trade.api import CloseMarketsTo, RecordStockTaken, SettleFlow
from sim.ledger.api import ChangeStock, PayEdge
from sim.polity.api import RaiseScandal
from sim.workforce.api import PressLabour

from .commands import BuyStock, ChangeHeld, GrantOpeningHerds, GrantOpeningStock, SmuggleStock
from .holding import HERDS
from .module import LivingStock
from .state import LivingStockWorld

# not cached: the held tonnes are read from the ledger, whose tonnes are still written outside its commands
_HELD = dict(seat_scoped=True, cached=False)

MODULE_SPECS = (ModuleSpec(
    "living_stock", LivingStock, channels=(HERDS,), world_state=LivingStockWorld,
    publishes=(
        ViewSpec("stock_held", "stock_held", kind=KEYED, inputs=("goods_stock",), **_HELD),
        ViewSpec("held_living_stock", "held_living_stock", inputs=("goods_stock",), **_HELD),
        ViewSpec("stock_status", "stock_status", kind=KEYED, inputs=("goods_stock",), **_HELD),
        ViewSpec("stock_holds_met", "stock_holds_met", kind=QUOTE, inputs=("goods_stock",), **_HELD),
        ViewSpec("stock_purchase_quote", "stock_purchase_quote", kind=QUOTE, seat_scoped=True),
        ViewSpec("stock_smuggle_quote", "stock_smuggle_quote", kind=QUOTE, seat_scoped=True),
        ViewSpec("society_herds", "society_herds", kind=TABLE, channels=(HERDS,)),
    ),
    applies=((ChangeHeld, "change_held"), (GrantOpeningStock, "grant_opening_stock"),
             (GrantOpeningHerds, "grant_opening_herds"), (BuyStock, "buy_stock"), (SmuggleStock, "smuggle_stock")),
    reads=("goods_stock", "acting_balance", "material_commodity", "tree", "civilisation", "year", "stock_land",
           "endemic_stock_loss", "nursery_room_units", "producer_capacities", "hour_wage", "can_pay", "partners",
           "partner", "partner_refusal", "partner_gate", "partner_landed_price", "partner_carry",
           "partner_catch_chance"),
    sends=(ChangeStock, PayEdge, PressLabour, SettleFlow, RecordStockTaken, CloseMarketsTo, RaiseScandal),
    phases=(PhaseHook("living_stock", "step_living_stock"),),
),)
