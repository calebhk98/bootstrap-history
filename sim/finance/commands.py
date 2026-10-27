"""Commands to the owner of debt and the capital market: the lenders' year, the money phase's debt steps and a seat's bank."""
from dataclasses import dataclass
from typing import Any

from sim.assembly.api import Command


@dataclass(frozen=True)
class RefreshLenderOffers(Command):
	"""The year's meeting of lenders: the pool pays the interest it holds, then who offers what is fixed."""


@dataclass(frozen=True)
class DefaultOnDebt(Command):
	"""The acting seat's household defaults on its debt in `year`."""
	year: int


@dataclass(frozen=True)
class ChargeInterest(Command):
	"""The acting seat's household pays the year's interest on its debt by the shared arrears rule. Answers the interest owed."""
	year: int


@dataclass(frozen=True)
class ShedLossMakers(Command):
	"""The acting seat's household shuts the plants that keep losing money."""
	year: int


@dataclass(frozen=True)
class WarnNearLimit(Command):
	"""The acting seat's household is told, once, that it is close to its credit limit."""
	year: int


@dataclass(frozen=True)
class EnforceCreditLimit(Command):
	"""The acting seat's household makes the responses to exhausted credit if it is past its limit."""
	year: int


@dataclass(frozen=True)
class JudgeInsolvency(Command):
	"""The year's count of the acting seat's insolvent years, and the staff an insolvent household can no longer pay."""


@dataclass(frozen=True)
class ServeBondageYear(Command):
	"""A year of the acting seat's debt service: the hours owed go to the creditor and the debt falls."""


@dataclass(frozen=True)
class NoteLenderPosting(Command):
	"""A lender's cash moved by `signed` (a loan it made, or was repaid), under `label`: entered in the lender's own books."""
	account: str
	signed: float
	label: Any


@dataclass(frozen=True)
class FoundBank(Command):
	"""The acting seat puts `capital` of its money into a new bank. Answers {ok, bank, capital, note}, or {ok: False, error, cause}."""
	capital: Any
