"""The ledger's module spec (sim/assembly)."""
from sim.assembly.api import KEYED, LIST, QUOTE, ExtensionPoint, ModuleSpec, ViewSpec

from .commands import (BankStock, ChangeStock, CloseCashPeriod, CreditSeat, DebitSeat, DrawDownStock, NoteSeatCash, NoteSpend, OpenCashBook, OpenPurse, PayActor, PayActorFromEdge, PayActorFromHousehold, PayEdge, PayEdgeFrom, PayExchange, PayWages,
                       NoteHolderBooking, ReceiveFromEdge, ReceiveFromExchange, RescaleHouseholdMoney, RestorePurse, SettleHouseholdInterest, SettleWithEdge, TakeFromHouseholdPurse, WithdrawHouseholdMoney)
from .ledger import MONEY, STOCK, Ledger
from .state import LedgerSeat, LedgerWorld

LEGACY_READS = ("legacy_household_actor", "legacy_edge_account", "cast", "cast_state", "seat_list", "year", "actor_world")

MODULE_SPECS = (ModuleSpec(
	"ledger", Ledger, channels=(MONEY, STOCK), world_state=LedgerWorld, seat_state=LedgerSeat,
	publishes=(
		# not cached: the purse is an account in the actors' book, which its own owner moves too, and the opening snapshot and the
		# cash book answer by the year, which the ledger's channels do not carry
		ViewSpec("goods_stock", "goods_stock", kind=KEYED, channels=(STOCK,), seat_scoped=True, cached=False),
		ViewSpec("acting_balance", "acting_balance", channels=(MONEY,), seat_scoped=True, cached=False),
		ViewSpec("seat_balance", "seat_balance", kind=KEYED, channels=(MONEY,), cached=False),
		ViewSpec("cash_book", "cash_book", channels=(MONEY,), seat_scoped=True, cached=False),
		ViewSpec("cash_causes_since", "cash_causes_since", kind=QUOTE, seat_scoped=True),
		ViewSpec("cash_unaccounted", "cash_unaccounted", channels=(MONEY,), seat_scoped=True, cached=False),
		ViewSpec("held_goods", "held_goods", channels=(STOCK,), seat_scoped=True, cached=False),
		ViewSpec("goods_stock_opening", "goods_stock_opening", channels=(STOCK,), seat_scoped=True, cached=False),
		ViewSpec("transfer_listening", "transfer_listening", kind=QUOTE),
	),
	extension_points=(ExtensionPoint("transfer_surcharge", LIST),),   # (payer, payee, amount, purpose) -> (edge, amount, cause) or None
	applies=((PayEdge, "pay_edge"), (PayEdgeFrom, "pay_edge_from"), (PayActorFromEdge, "pay_actor_from_edge"), (PayActor, "pay_actor"),
	         (PayActorFromHousehold, "pay_actor_from_household"), (TakeFromHouseholdPurse, "take_from_household_purse"),
	         (SettleWithEdge, "settle_with_edge"), (RescaleHouseholdMoney, "rescale_household_money"), (RestorePurse, "restore_purse"),
	         (SettleHouseholdInterest, "settle_household_interest"), (NoteHolderBooking, "note_holder_booking"),
	         (WithdrawHouseholdMoney, "withdraw_household_money"), (DrawDownStock, "draw_down_stock"), (PayExchange, "pay_exchange"), (ReceiveFromExchange, "receive_from_exchange"), (ReceiveFromEdge, "receive_from_edge"), (PayWages, "pay_wages"),
	         (ChangeStock, "change_stock"), (BankStock, "bank_stock"), (CreditSeat, "credit_seat"), (DebitSeat, "debit_seat"),
	         (NoteSeatCash, "note_seat_cash"), (OpenCashBook, "open_cash_book"), (OpenPurse, "open_purse"), (CloseCashPeriod, "close_cash_period"), (NoteSpend, "note_spend")),
	reads=LEGACY_READS,
),)
