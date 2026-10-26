"""The ledger module: applies the money and goods commands and publishes what each holder has.

Until the founder's purse and tonnes ledger move into the ledger's own state, it reaches them through the engine
bridge's `legacy_*` views; those reads go when the state moves (docs/architecture/MODULE_MIGRATION_TASKS.md)."""
from typing import Any

from sim.agents.api import edges, ledger
from sim.assembly.api import Module

from . import rules

MONEY = "money"
STOCK = "stock"


class Ledger(Module):
	def edge(self, name: str) -> Any:
		return self.needs.legacy_edge_account[name]

	def pay_edge(self, command: Any) -> None:
		ledger.transfer(self.needs.legacy_acting_household(), self.edge(command.edge), command.amount, command.purpose)
		self.bump_seat(MONEY)

	def receive_from_edge(self, command: Any) -> None:
		ledger.transfer(self.edge(command.edge), self.needs.legacy_acting_household(), command.amount, command.purpose)
		self.bump_seat(MONEY)

	def pay_wages(self, command: Any) -> None:
		payer, registry = self.needs.legacy_acting_household(), self.needs.legacy_actor_registry()
		rules.pay_wages(registry, payer, command.amount, command.purpose, self.edge(edges.EDGE_WORKERS))
		self.bump_seat(MONEY)

	def change_stock(self, command: Any) -> None:
		opening = self.needs.legacy_opening_stock()      # first: the year's snapshot is taken before the change
		rules.add_tonnes(self.needs.legacy_stock_ledger(), opening, command.commodity, command.tonnes)
		self.needs.legacy_acting_household()._stock_throttle_sig = None
		self.bump_seat(STOCK)

	def goods_stock(self, commodity: str) -> float:
		return self.needs.legacy_stock_ledger().get(commodity, 0.0)

	def acting_balance(self) -> float:
		return self.needs.legacy_acting_household().capital
