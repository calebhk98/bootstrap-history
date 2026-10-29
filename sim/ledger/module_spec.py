"""The ledger's module spec (sim/assembly)."""
from sim.assembly.api import KEYED, LIST, QUOTE, ExtensionPoint, ModuleSpec, ViewSpec

from .commands import (BankStock, ChangeStock, DrawDownStock, PayActor, PayActorFromEdge, PayActorFromHousehold, PayEdge, PayEdgeFrom, PayExchange, PayWages,
                       ReceiveFromEdge, ReceiveFromExchange, RescaleHouseholdMoney, RestorePurse, SettleWithEdge, TakeFromHouseholdPurse, WithdrawHouseholdMoney)
from .ledger import MONEY, STOCK, Ledger
from .state import LedgerSeat, LedgerWorld

LEGACY_READS = ("legacy_acting_household", "legacy_household_actor", "legacy_edge_account", "cast", "legacy_seats", "seat_party",
                "year")

MODULE_SPECS = (ModuleSpec(
	"ledger", Ledger, channels=(MONEY, STOCK), world_state=LedgerWorld, seat_state=LedgerSeat,
	publishes=(
		# not cached: the purse is still written outside the ledger's commands (HouseholdState.capital), and the opening snapshot
		# answers by the year, which the ledger's channels do not carry
		ViewSpec("goods_stock", "goods_stock", kind=KEYED, channels=(STOCK,), seat_scoped=True, cached=False),
		ViewSpec("acting_balance", "acting_balance", channels=(MONEY,), seat_scoped=True, cached=False),
		ViewSpec("held_goods", "held_goods", channels=(STOCK,), seat_scoped=True, cached=False),
		ViewSpec("goods_stock_opening", "goods_stock_opening", channels=(STOCK,), seat_scoped=True, cached=False),
		ViewSpec("transfer_listening", "transfer_listening", kind=QUOTE),
	),
	extension_points=(ExtensionPoint("transfer_surcharge", LIST),),   # (payer, payee, amount, purpose) -> (edge, amount, cause) or None
	applies=((PayEdge, "pay_edge"), (PayEdgeFrom, "pay_edge_from"), (PayActorFromEdge, "pay_actor_from_edge"), (PayActor, "pay_actor"),
	         (PayActorFromHousehold, "pay_actor_from_household"), (TakeFromHouseholdPurse, "take_from_household_purse"),
	         (SettleWithEdge, "settle_with_edge"), (RescaleHouseholdMoney, "rescale_household_money"), (RestorePurse, "restore_purse"),
	         (WithdrawHouseholdMoney, "withdraw_household_money"), (DrawDownStock, "draw_down_stock"), (PayExchange, "pay_exchange"), (ReceiveFromExchange, "receive_from_exchange"), (ReceiveFromEdge, "receive_from_edge"), (PayWages, "pay_wages"),
	         (ChangeStock, "change_stock"), (BankStock, "bank_stock")),
	reads=LEGACY_READS,
),)
