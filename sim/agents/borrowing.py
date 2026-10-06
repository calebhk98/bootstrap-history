"""How any actor borrows: one rule for a firm, a state and (through the same pure functions) the founder.

An actor's debt is its purse below zero. What it will be lent is the smaller of what its standing earning
can carry at the market rate and what lenders still hold after everyone else's loans. What it pays is the
market rate plus a premium for the share of that ceiling it has used, less a discount for its standing.
"""
from typing import Any

from sim.constants import declare
from sim.world import capital_market

from . import ledger
from .edges import EDGE_INTEREST

STANDING_DISCOUNT_CAP = declare(
	"STANDING_DISCOUNT_CAP", 0.03, kind="temporary_heuristic",
	unit="fraction off the annual rate (maximum)", source=None, confidence="D",
	why="The most a fully trusted borrower's standing can cheapen its credit; the same ceiling the "
		"founder's reputation has. Stands in for lenders' knowledge of a borrower.")
TRACK_RECORD_YEARS = declare(
	"TRACK_RECORD_YEARS", 10.0, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="Years of existence after which lenders trust a firm's record in full; its standing grows "
		"linearly until then. Stands in for lenders learning a borrower's reliability.")


class Borrower:
	"""Mixed into `Actor`: debt, ceiling, rate and interest, read from the world's market."""

	def debt(self) -> float:
		return max(0.0, -self.money)  # type: ignore[attr-defined]

	def credit_earning(self, world: Any) -> float:
		"""Standing yearly earning lenders count on to carry its debt."""
		return 0.0

	def credit_standing(self, world: Any) -> float:
		"""How far lenders trust the actor, 0..1, from what they can see of it."""
		return 0.0

	def standing_discount(self, world: Any) -> float:
		return STANDING_DISCOUNT_CAP * max(0.0, min(1.0, self.credit_standing(world)))

	def credit_ceiling(self, world: Any) -> float:
		"""The most this actor may owe in all: what its earning can carry at the market rate, and no
		more than lenders hold after the others' loans."""
		carried = capital_market.serviceable_debt(
			self.credit_earning(world), max(world.market_rate(), world.starting_rate()), world.debt_service_share_of_surplus())
		room = world.credit_headroom(self.identity())  # type: ignore[attr-defined]
		return carried if room is None else min(carried, room)

	def spare_credit(self, world: Any) -> float:
		"""What the actor may still borrow: its ceiling less what it already owes."""
		return max(0.0, self.credit_ceiling(world) - self.debt())

	# Whether the actor pays for copies on credit; a firm does, a state and a household keep to their purse.
	borrows_for_copies = False

	def spendable(self, world: Any) -> float:
		"""The purse above zero, and what may still be borrowed if the actor borrows for copies."""
		purse = max(0.0, self.money)  # type: ignore[attr-defined]
		return purse + self.spare_credit(world) if self.borrows_for_copies else purse

	def rate_on_loan(self, world: Any, amount: float) -> float:
		"""The rate on `amount` borrowed on top of what the actor owes, by the share of the ceiling it then uses."""
		ceiling = self.credit_ceiling(world)
		used = (self.debt() + amount) / ceiling if ceiling > 0.0 else 1.0
		return capital_market.borrower_rate(world.market_rate(), self.standing_discount(world), used)

	def borrowing_rate(self, world: Any) -> float:
		debt = self.debt()
		used = 0.0
		if debt > 0.0:
			ceiling = self.credit_ceiling(world)
			used = debt / ceiling if ceiling > 0.0 else 1.0
		return capital_market.borrower_rate(world.market_rate(), self.standing_discount(world), used)

	def pay_interest(self, world: Any) -> float:
		"""Interest on the debt is added to it, booked as an outlay; the amount."""
		debt = self.debt()
		if debt <= 0.0:
			return 0.0
		owed = debt * self.borrowing_rate(world)
		ledger.transfer(self, world.edge(EDGE_INTEREST), owed, "interest")
		world.note_interest_paid(owed)
		return owed
