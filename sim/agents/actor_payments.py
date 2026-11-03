"""`ActorPayments`: how money reaches and leaves an actor's purse, entered with the purpose it moved for. Reached as `party.payments`.

The default moves the actor's `money` and notes it; `RecordedPayments` posts through the actor's purses book and keeps the
actor's income and outlay by purpose on its record.
"""
from typing import Any

from . import ledger
from .ledger import Purpose
from .purses import EDGE_OUTSIDE


class ActorPayments:

	def __init__(self, actor: Any) -> None:
		self.actor = actor

	def credit(self, amount: float, purpose: Purpose) -> None:
		"""Money in, with the purpose it came for."""
		self.actor.money += amount
		self.note_income(purpose, amount)

	def debit(self, amount: float, purpose: Purpose) -> None:
		"""Money out, with the purpose it went for."""
		self.actor.money -= amount
		self.note_outlay(purpose, amount)

	def note_income(self, purpose: Purpose, amount: float) -> None:
		"""Hook: an actor with books records what came in."""

	def note_outlay(self, purpose: Purpose, amount: float) -> None:
		"""Hook: an actor with books records what went out."""


class RecordedPayments(ActorPayments):

	def credit(self, amount: float, purpose: Purpose) -> None:
		self.actor.purses.transfer(EDGE_OUTSIDE, self.actor.actor_id, amount, ledger.purposes_label(purpose))
		self.note_income(purpose, amount)

	def debit(self, amount: float, purpose: Purpose) -> None:
		self.actor.purses.transfer(self.actor.actor_id, EDGE_OUTSIDE, amount, ledger.purposes_label(purpose))
		self.note_outlay(purpose, amount)

	def note_income(self, purpose: Purpose, amount: float) -> None:
		income = self.actor.record.income
		for label, part in ledger.parts(purpose, amount).items():
			income[label] = income.get(label, 0.0) + part

	def note_outlay(self, purpose: Purpose, amount: float) -> None:
		outlays = self.actor.record.outlays
		for label, part in ledger.parts(purpose, amount).items():
			outlays[label] = outlays.get(label, 0.0) + part
