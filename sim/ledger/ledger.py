"""The ledger module: applies the money and goods commands and publishes what each holder has.

The seat's tonnes ledger, its cash book and the pool of capacity keys swept out of the ledgers are the ledger's own state
(sim/ledger/state.py). A seat's purse is its account in the actors' book; the ledger moves it through the account it builds for
the length of a command (sim/ledger/seat_account.py)."""
from typing import Any, Optional

from sim.agents.api import EDGE_EXCHANGE, GOVERNMENT_PREFIX, edges, ledger
from sim.assembly.api import Module
from sim.refusal import Refusal

from . import cash_book, rules
from .seat_account import SeatAccount

BANK_CAPITAL_LABEL = "bank capital"   # the cause of the coin a seat puts into a bank it founds
OPENING_LABEL = "opening"   # the label of the posting that opens a joining seat's account
MONEY = "money"
STOCK = "stock"


class Ledger(Module):
	def edge(self, name: str) -> Any:
		return self.needs.cast_state().edge(name)

	def account(self, seat_id: Optional[str] = None) -> SeatAccount:
		"""The seat's purse as this module moves it (the acting seat's unless one is named)."""
		seat_id = self.clock.acting_seat if seat_id is None else seat_id
		return SeatAccount(self.seat_of(seat_id), self.needs.cast_state().purses, seat_id)

	def pay_edge(self, command: Any) -> None:
		ledger.transfer(self.account(), self.edge(command.edge), command.amount, command.purpose)
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
			payee = self.account(command.payee)
		else:
			cast = self.needs.cast()
			payee = cast.get(command.payee) or cast.ensure_government(command.payee[len(GOVERNMENT_PREFIX):])
		ledger.transfer(payer, payee, command.amount, command.purpose)
		self.bump(MONEY)

	def pay_actor_from_household(self, command: Any) -> Any:
		payee = self.needs.cast().get(command.payee)
		if payee is None:
			return Refusal("no_such_actor", "the cast holds no actor %s" % command.payee)
		ledger.transfer(self.account(), payee, command.amount, command.purpose)
		self.bump_seat(MONEY)
		return None

	def take_from_household_purse(self, command: Any) -> Any:
		taker = self.needs.cast().get(command.taker)
		if taker is None:
			return Refusal("no_such_actor", "the cast holds no actor %s" % command.taker)
		ledger.transfer(self.account(), taker, command.amount, command.purpose)
		self.bump_seat(MONEY)
		return None

	def settle_with_edge(self, command: Any) -> None:
		ledger.settle(self.account(), self.edge(command.edge), command.balance, command.purpose)
		self.bump_seat(MONEY)

	def rescale_household_money(self, command: Any) -> None:
		account = self.account()
		account.capital = account.capital * command.ratio
		if self.seat.cash_mark is not None:
			self.seat.cash_mark = self.seat.cash_mark * command.ratio
		self.bump_seat(MONEY)

	def restore_purse(self, command: Any) -> None:
		self.account(command.seat).capital = command.balance
		self.bump_seat(MONEY, command.seat)

	def open_purse(self, command: Any) -> None:
		purses = self.needs.cast_state().purses
		if command.balance and not purses.has_account(command.seat):
			purses.set_net(command.seat, command.balance, OPENING_LABEL)
			self.bump_seat(MONEY, command.seat)

	def open_cash_book(self, command: Any) -> None:
		"""The seat's cash book measures from `command.opening`."""
		self.seat.cash_mark = float(command.opening)

	def close_cash_period(self, command: Any) -> None:
		cash_book.close_period(self.seat, self.account().capital, self.needs.year())

	def credit_seat(self, command: Any) -> None:
		self.account(command.seat).credit(command.amount, command.purpose)
		self.bump_seat(MONEY, command.seat)

	def debit_seat(self, command: Any) -> None:
		self.account(command.seat).debit(command.amount, command.purpose)
		self.bump_seat(MONEY, command.seat)

	def note_seat_cash(self, command: Any) -> None:
		account = self.account(command.seat)
		(account.note_income if command.direction > 0.0 else account.note_outlay)(command.purpose, command.amount)
		self.bump_seat(MONEY, command.seat)

	def note_spend(self, command: Any) -> None:
		self.seat.total_spend += command.amount

	def note_holder_booking(self, command: Any) -> None:
		"""The lender's books record a posting its loan or repayment made: a seat's household, else an actor of the cast."""
		if command.holder in self.needs.seat_list()["joined"]:
			self._note_booking(self.account(command.holder), command)
		else:
			self._note_booking(self.needs.cast().actors.get(command.holder), command)

	def _note_booking(self, holder: Any, command: Any) -> None:
		if holder is not None:
			(holder.note_income if command.signed > 0.0 else holder.note_outlay)(command.label, abs(command.signed))

	def withdraw_household_money(self, command: Any) -> None:
		ledger.transfer(self.account(), self.edge(EDGE_EXCHANGE), command.amount, BANK_CAPITAL_LABEL)
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
		ledger.transfer(self.edge(command.edge), self.account(), command.amount, command.purpose)
		self.bump_seat(MONEY)

	def pay_wages(self, command: Any) -> None:
		registry = self.needs.cast()
		rules.pay_wages(registry, self.account(), command.amount, command.purpose, self.edge(edges.EDGE_WORKERS))
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
		return self.account().capital

	def seat_balance(self, seat_id: str) -> float:
		"""What the seat's purse holds (its account's net position in the actors' book)."""
		return self.account(seat_id).capital

	def cash_book(self) -> Any:
		"""The acting seat's open period of cash by cause, and the closed ones before it."""
		return cash_book.book(self.seat, self.account().capital, self.needs.year())

	def cash_causes_since(self, year: Optional[int]) -> Any:
		"""Cash moved by cause since the snapshot of `year` (every kept period when None)."""
		return cash_book.causes_since(self.seat, year)

	def cash_unaccounted(self) -> float:
		"""Cash in hand less the cash book's opening and entries: zero when nothing bypassed the ledger."""
		return cash_book.unaccounted(self.seat, self.account().capital)

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
