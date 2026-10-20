"""A state's bonds: it sells claims for a fixed coupon, and the market pays what they are worth at the rate it asks.

A bond promises a yearly coupon and its face at the end of its term. The market (the lending pool's depositors)
buys it for the present value of those payments at the yield it asks of the issuer: the going rate plus the
issuer's own premium, which rises with a default on its record. An issuer in good standing sells at about face; one
with a record of default sells the same coupon for less, so it must promise more face to raise the same cash. The
bonds outstanding are the issuer's debt at face and the market's claim at what it paid; a default writes off what
the market paid.
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Mapping, Optional, Tuple

from sim.constants import declare

BOND_TERM_YEARS = declare(
	"BOND_TERM_YEARS", 10.0, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	retire="Complaints/106: an issuer chooses the term of each bond against what it can bear and what the market will take",
	why="The life of every bond a state sells. Stands in for the issuer's choice of maturity and the market's "
		"appetite for long claims, which are not modelled.")
EPSILON = 1e-9


def bond_price(face: float, coupon_rate: float, years: float, yield_rate: float) -> float:
	"""What the market pays for a bond: its coupons and face discounted at the yield it asks. At the coupon rate
	a bond is worth its face; a higher yield (a dearer market, a worse record) cuts the price."""
	if face <= 0.0:
		return 0.0
	years = max(1, int(round(years)))
	growth = 1.0 + max(-0.99, yield_rate)
	coupons = sum(coupon_rate * face / growth ** year for year in range(1, years + 1))
	return coupons + face / growth ** years


@dataclass
class Bond:
	face: float           # what the issuer owes at the end
	coupon: float         # yearly rate on the face
	years_left: float
	paid: float           # what the market paid for it: the loss it bears in a default


class BondBook:
	"""The terms each issuer sells at this year and the bonds outstanding."""

	def __init__(self) -> None:
		self.terms: Dict[str, Tuple[float, float]] = {}      # issuer -> (coupon rate, yield the market asks)
		self.held: Dict[str, List[Bond]] = {}

	def set_terms(self, issuer: str, coupon_rate: float, yield_rate: float) -> None:
		"""From now on the issuer raises cash by bonds at this coupon, sold at the price this yield gives."""
		self.terms[issuer] = (max(0.0, coupon_rate), max(0.0, yield_rate))

	def issues(self, issuer: str) -> bool:
		return issuer in self.terms

	def price_per_face(self, issuer: str) -> float:
		coupon, yield_rate = self.terms[issuer]
		return bond_price(1.0, coupon, BOND_TERM_YEARS, yield_rate)

	def sell(self, issuer: str, cash: float) -> Optional[Bond]:
		"""A bond that raises `cash` at today's price: its face is the cash over the price per unit of face."""
		if cash <= 0.0:
			return None
		bond = Bond(cash / self.price_per_face(issuer), self.terms[issuer][0], BOND_TERM_YEARS, cash)
		self.held.setdefault(issuer, []).append(bond)
		return bond

	def debt(self, issuer: str) -> float:
		return sum(bond.face for bond in self.held.get(issuer, ()))

	def paid_in(self, issuer: str) -> float:
		return sum(bond.paid for bond in self.held.get(issuer, ()))

	def total_paid(self) -> float:
		"""What the market paid for every bond outstanding."""
		return sum(bond.paid for bonds in self.held.values() for bond in bonds)

	def coupons_due(self, issuer: str) -> float:
		return sum(bond.face * bond.coupon for bond in self.held.get(issuer, ()))

	def age(self, issuer: str) -> float:
		"""A year passes: bonds at their term fall due and are returned; their face is what the issuer must repay."""
		due = 0.0
		kept = []
		for bond in self.held.get(issuer, ()):
			bond.years_left -= 1.0
			if bond.years_left <= EPSILON:
				due += bond.face
			else:
				kept.append(bond)
		if kept:
			self.held[issuer] = kept
		else:
			self.held.pop(issuer, None)
		return due

	def write_off(self, issuer: str) -> float:
		"""The issuer defaults: its bonds end and the market loses what it paid for them."""
		lost = self.paid_in(issuer)
		self.held.pop(issuer, None)
		return lost

	def to_canon_dict(self) -> Dict[str, Any]:
		return {"terms": {issuer: list(terms) for issuer, terms in sorted(self.terms.items())},
				"held": {issuer: [asdict(bond) for bond in bonds] for issuer, bonds in sorted(self.held.items())}}

	@classmethod
	def from_record(cls, record: Mapping[str, Any]) -> "BondBook":
		book = cls()
		book.terms = {issuer: (terms[0], terms[1]) for issuer, terms in (record.get("terms") or {}).items()}
		book.held = {issuer: [Bond(**bond) for bond in bonds] for issuer, bonds in (record.get("held") or {}).items()}
		return book
