"""The ledger's module spec (sim/assembly)."""
from sim.assembly.api import KEYED, ModuleSpec, ViewSpec

from .commands import ChangeStock, PayEdge, PayWages, ReceiveFromEdge
from .ledger import MONEY, STOCK, Ledger

LEGACY_READS = ("legacy_acting_household", "legacy_edge_account", "legacy_actor_registry", "legacy_stock_ledger",
                "legacy_opening_stock")

MODULE_SPECS = (ModuleSpec(
	"ledger", Ledger, channels=(MONEY, STOCK),
	publishes=(
		# not cached yet: the purse and the tonnes ledger are still written outside the ledger's commands
		ViewSpec("goods_stock", "goods_stock", kind=KEYED, channels=(STOCK,), seat_scoped=True, cached=False),
		ViewSpec("acting_balance", "acting_balance", channels=(MONEY,), seat_scoped=True, cached=False),
	),
	applies=((PayEdge, "pay_edge"), (ReceiveFromEdge, "receive_from_edge"), (PayWages, "pay_wages"),
	         (ChangeStock, "change_stock")),
	reads=LEGACY_READS,
),)
