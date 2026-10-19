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
