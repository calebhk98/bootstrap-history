"""What a borrower does when it cannot pay its interest: the unpaid part is arrears, and arrears that last too long
are a default. One rule for every actor; the actor decides only what closing means for it."""
from typing import Tuple

from sim.constants import declare

ARREARS_YEARS_BEFORE_DEFAULT = declare(
	"ARREARS_YEARS_BEFORE_DEFAULT", 3, kind="temporary_heuristic",
	unit="consecutive years", source=None, confidence="D",
	retire="Complaints/588: a lender's assessment of the borrower's assets and income replaces the fixed wait",
	why="Years a borrower may go without paying its interest in full before its lenders write the claim off. "
		"Stands in for lenders weighing what the borrower's assets and income can still carry.")


def settle_year(owed: float, spare_credit: float) -> Tuple[float, float]:
	"""(paid, unpaid) of `owed` interest: it is paid by drawing on the facility, and only within the room the
	facility has left under the ceiling; a borrower past its ceiling pays nothing."""
	paid = min(owed, max(0.0, spare_credit))
	return paid, owed - paid


def in_default(years_in_arrears: int) -> bool:
	return years_in_arrears >= ARREARS_YEARS_BEFORE_DEFAULT


DEFAULT_RECORD_PREMIUM = declare(
	"DEFAULT_RECORD_PREMIUM", 0.1, kind="temporary_heuristic",
	unit="rate added when the remembered loss is all the borrower owes and has lost", source=None, confidence="D",
	retire="Complaints/588: a lender's assessment of the borrower's record replaces the fixed premium",
	why="What a borrower that defaulted pays over the rate of one that did not. Stands in for lenders pricing a "
		"borrower's record.")
DEFAULT_RECORD_FADE_PER_YEAR = declare(
	"DEFAULT_RECORD_FADE_PER_YEAR", 0.1, kind="temporary_heuristic",
	unit="share of the remembered loss forgotten each year", source=None, confidence="D",
	retire="Complaints/588: a lender's assessment of the borrower's record replaces the fixed premium",
	why="How fast lenders forgive a default. Stands in for lenders' memory of a borrower.")


def record_premium(remembered_loss: float, debt_after: float) -> float:
	"""Rate added to what a borrower with a default on its record pays: the share of its remembered loss in the loss
	and the debt it would then owe, times the declared premium."""
	remembered_loss = max(0.0, remembered_loss)
	total = remembered_loss + max(0.0, debt_after)
	return DEFAULT_RECORD_PREMIUM * remembered_loss / total if total > 0.0 else 0.0


def faded(remembered_loss: float) -> float:
	return remembered_loss * (1.0 - DEFAULT_RECORD_FADE_PER_YEAR)
