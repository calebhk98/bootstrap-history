"""The ledger module: applies the money and goods commands and publishes what each holder has.

The seat's tonnes ledger and the pool of capacity keys swept out of it are the ledger's own state (sim/ledger/state.py). The
founder's purse is still the household's, reached through the engine bridge's `legacy_*` views until it moves
(docs/architecture/MODULE_MIGRATION_TASKS.md)."""
from typing import Any

from sim.agents.api import EDGE_EXCHANGE, GOVERNMENT_PREFIX, edges, ledger
from sim.assembly.api import Module
from sim.refusal import Refusal

from . import rules

MONEY = "money"
STOCK = "stock"


class Ledger(Module):
	def edge(self, name: str) -> Any:
		return self.needs.legacy_edge_account[name]

	def pay_edge(self, command: Any) -> None:
		ledger.transfer(self.needs.legacy_acting_household(), self.edge(command.edge), command.amount, command.purpose)
		self.bump_seat(MONEY)

	def pay_edge_from(self, command: Any) -> None:
		actor = self.needs.cast().actors[command.actor]
		ledger.transfer(actor, self.edge(command.edge), command.amount, command.purpose)
		self.bump(MONEY)

	def pay_actor_from_edge(self, command: Any) -> Any:
		payee = self.needs.cast().get(command.payee)
		if payee is None:
			return Refusal("no_such_actor", "the cast holds no actor %s" % command.payee)
		ledger.transfer(self.edge(command.edge), payee, command.amount, command.purpose)
		self.bump(MONEY)
		return None

	def pay_actor(self, command: Any) -> None:
		payer = self.needs.cast().get(command.payer)
		if command.payee in self.needs.seat_list()["joined"]:
			payee = self.needs.seat_party[command.payee]
		else:
			cast = self.needs.cast()
			payee = cast.get(command.payee) or cast.ensure_government(command.payee[len(GOVERNMENT_PREFIX):])
		ledger.transfer(payer, payee, command.amount, command.purpose)
		self.bump(MONEY)

	def pay_actor_from_household(self, command: Any) -> Any:
		payee = self.needs.cast().get(command.payee)
		if payee is None:
			return Refusal("no_such_actor", "the cast holds no actor %s" % command.payee)
		ledger.transfer(self.needs.legacy_household_actor(), payee, command.amount, command.purpose)
		self.bump_seat(MONEY)
		return None

	def take_from_household_purse(self, command: Any) -> Any:
		taker = self.needs.cast().get(command.taker)
		if taker is None:
			return Refusal("no_such_actor", "the cast holds no actor %s" % command.taker)
		ledger.transfer(self.needs.legacy_acting_household(), taker, command.amount, command.purpose)
		self.bump_seat(MONEY)
		return None

	def settle_with_edge(self, command: Any) -> None:
		ledger.settle(self.needs.legacy_household_actor(), self.edge(command.edge), command.balance, command.purpose)
		self.bump_seat(MONEY)

	def rescale_household_money(self, command: Any) -> None:
		household = self.needs.legacy_acting_household()
		household.capital = household.capital * command.ratio
		if household.cash_mark is not None:
			household.cash_mark = household.cash_mark * command.ratio
		self.bump_seat(MONEY)

	def restore_purse(self, command: Any) -> None:
		self.needs.legacy_acting_household().capital = command.balance
		self.bump_seat(MONEY)

	def settle_household_interest(self, command: Any) -> Any:
		settled = self.needs.legacy_household_actor().settle_interest(self.needs.actor_world())
		self.bump_seat(MONEY)
		return settled

	def note_holder_booking(self, command: Any) -> None:
		"""The lender's books record a posting its loan or repayment made: a seat's household, else an actor of the cast."""
		if command.holder in self.needs.seat_list()["joined"]:
			with self.needs.acting_as(command.holder):
				self._note_booking(self.needs.legacy_acting_household(), command)
		else:
			self._note_booking(self.needs.cast().actors.get(command.holder), command)

	def _note_booking(self, holder: Any, command: Any) -> None:
		if holder is not None:
			(holder.note_income if command.signed > 0.0 else holder.note_outlay)(command.label, abs(command.signed))

	def withdraw_household_money(self, command: Any) -> None:
		household = self.needs.legacy_household_actor()
		household.money = household.money - command.amount
		self.bump_seat(MONEY)

	def pay_exchange(self, command: Any) -> None:
		cast = self.needs.cast()
		cast.state.purses.transfer(command.actor, EDGE_EXCHANGE, command.coin, "exchange")
		cast.actors[command.actor].note_outlay(command.label, command.coin)
		self.bump(MONEY)

	def receive_from_exchange(self, command: Any) -> None:
		cast = self.needs.cast()
		cast.state.purses.transfer(EDGE_EXCHANGE, command.actor, command.coin, "exchange")
		cast.actors[command.actor].note_income(command.label, command.coin)
		self.bump(MONEY)

	def receive_from_edge(self, command: Any) -> None:
		ledger.transfer(self.edge(command.edge), self.needs.legacy_acting_household(), command.amount, command.purpose)
		self.bump_seat(MONEY)

	def pay_wages(self, command: Any) -> None:
		payer, registry = self.needs.legacy_acting_household(), self.needs.cast()
		rules.pay_wages(registry, payer, command.amount, command.purpose, self.edge(edges.EDGE_WORKERS))
		self.bump_seat(MONEY)

	def stock_ledger(self) -> Any:
		"""The seat's tonnes ledger, made on first use, with the capacity keys swept into the world's capacity pool."""
		self.seat._material_stock_ledger = rules.settled_stock(self.seat._material_stock_ledger, self.world.capacity_pool)
		return self.seat._material_stock_ledger

	def opening_stock(self) -> Any:
		"""The tonnes as the year's accounting began; the snapshot is taken here if this year has none."""
		self.seat._material_stock_opening = rules.year_opening_record(
			self.seat._material_stock_opening, self.needs.year(), self.stock_ledger())
		return self.seat._material_stock_opening["tonnes"]

	def change_stock(self, command: Any) -> None:
		stock = self.stock_ledger()
		if command.legacy_snapshot_after_change:
			stock[command.commodity] += command.tonnes
			opening = self.opening_stock()
			opening[command.commodity] = opening.get(command.commodity, 0.0) + command.tonnes
		else:
			opening = self.opening_stock()      # first: the year's snapshot is taken before the change
			rules.add_tonnes(stock, opening, command.commodity, command.tonnes)
		stock.writes += 1
		self.bump_seat(STOCK)

	def bank_stock(self, command: Any) -> None:
		self.opening_stock()      # first: the year's snapshot is taken before the change
		stock = self.stock_ledger()
		for commodity, tonnes in command.tonnes:
			stock[commodity] = tonnes
		stock.writes += 1
		self.bump_seat(STOCK)

	def draw_down_stock(self, command: Any) -> None:
		stock = self.stock_ledger()
		stock[command.commodity] = max(0.0, stock[command.commodity] - command.tonnes)
		self.bump_seat(STOCK)

	def goods_stock_opening(self) -> Any:
		"""The acting seat's tonnes by commodity key as they stood when this year's accounting began, as the books stand now:
		read it, never write it. Nothing is recorded by asking."""
		return rules.year_opening_record(self.seat._material_stock_opening, self.needs.year(), self.held_goods())["tonnes"]

	def goods_stock(self, commodity: str) -> float:
		return self.stock_ledger().get(commodity, 0.0)

	def acting_balance(self) -> float:
		return self.needs.legacy_acting_household().capital

	def held_goods(self) -> Any:
		"""The acting seat's tonnes ledger by commodity key: read it, never write it."""
		return self.stock_ledger()

	def transfer_listening(self) -> Any:
		"""A context in which every transfer between two parties asks the `transfer_surcharge` providers what moving
		the money costs, and the payer pays each answer to the edge it names. The surcharge's own postings are not
		charged again (sim/agents/ledger.py switches the hook off while it runs)."""
		return ledger.listening(self.after_transfer)

	def after_transfer(self, payer: Any, payee: Any, amount: float, purpose: Any) -> None:
		for charge in self.needs.transfer_surcharge(payer, payee, amount, purpose):
			if charge is not None:
				edge_name, charged, cause = charge
				ledger.transfer(payer, self.edge(edge_name), charged, cause)
