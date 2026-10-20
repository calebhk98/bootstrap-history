"""Who lent what to a borrower that names its lenders: a ledger beside the pool's single claim.

The pool lends on its depositors' funds, so a draw on a borrower's facility is funded by the depositors in proportion
to what each has placed. A borrower that names its lenders (a state) keeps that attribution: each lender's claim
rises with a draw it funded, falls with a repayment in proportion, and is written down by a default, so the loss
falls on the lenders that lent and not on those who placed funds afterwards.
"""
from typing import Any, Dict, Mapping, Set


class NamedLenders:
	"""For each naming borrower, its claims by lender and what each lender has lost on it."""

	def __init__(self) -> None:
		self.borrowers: Set[str] = set()
		self.held: Dict[str, Dict[str, float]] = {}
		self.written_down: Dict[str, Dict[str, float]] = {}

	def name(self, borrower: str) -> None:
		self.borrowers.add(borrower)

	def names(self, borrower: str) -> bool:
		return borrower in self.borrowers

	def claims(self, borrower: str) -> Dict[str, float]:
		return dict(self.held.get(borrower, {}))

	def lost(self, borrower: str) -> Dict[str, float]:
		return dict(self.written_down.get(borrower, {}))

	def drew(self, borrower: str, amount: float, deposits: Mapping[str, float]) -> None:
		"""A draw of `amount`, funded by the depositors in proportion to their deposits."""
		total = sum(deposits.values())
		if amount <= 0.0 or total <= 0.0:
			return
		held = self.held.setdefault(borrower, {})
		for lender, deposit in sorted(deposits.items()):
			held[lender] = held.get(lender, 0.0) + amount * deposit / total

	def repaid(self, borrower: str, share: float) -> None:
		"""The borrower repaid `share` of its debt: every claim falls by it."""
		held = self.held.get(borrower)
		if held:
			for lender in held:
				held[lender] *= max(0.0, 1.0 - share)

	def settle_default(self, borrower: str, lost: float, deposits: Mapping[str, float]) -> Dict[str, float]:
		"""The borrower defaults owing `lost`: each lender's claim is written down, no more than it still holds on
		deposit; returns the write-down by lender (the rest of the loss is the pool's)."""
		held = self.held.pop(borrower, {})
		total = sum(held.values())
		taken: Dict[str, float] = {}
		if total > 0.0 and lost > 0.0:
			for lender, claim in sorted(held.items()):
				part = min(lost * claim / total, claim, deposits.get(lender, 0.0))
				if part > 0.0:
					taken[lender] = part
					record = self.written_down.setdefault(borrower, {})
					record[lender] = record.get(lender, 0.0) + part
		return taken

	def to_canon_dict(self) -> Dict[str, Any]:
		return {"borrowers": sorted(self.borrowers), "held": {b: dict(sorted(h.items())) for b, h in sorted(self.held.items())},
				"written_down": {b: dict(sorted(w.items())) for b, w in sorted(self.written_down.items())}}

	@classmethod
	def from_record(cls, record: Mapping[str, Any]) -> "NamedLenders":
		named = cls()
		named.borrowers = set(record.get("borrowers") or ())
		named.held = {b: dict(h) for b, h in (record.get("held") or {}).items()}
		named.written_down = {b: dict(w) for b, w in (record.get("written_down") or {}).items()}
		return named
